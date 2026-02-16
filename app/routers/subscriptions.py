from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_session
from app.models import Subscription, BillingCycle, SubscriptionCategory

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

class SubscriptionCreate(BaseModel):
    name: str
    full_price: float
    my_price: Optional[float] = None
    billing_cycle: str = "monthly"
    category: str = "other"
    is_shared: bool = False
    shared_with: Optional[str] = None
    next_billing: Optional[str] = None
    notes: Optional[str] = None
    active: bool = True

class SubscriptionUpdate(BaseModel):
    name: Optional[str] = None
    full_price: Optional[float] = None
    my_price: Optional[float] = None
    billing_cycle: Optional[str] = None
    category: Optional[str] = None
    is_shared: Optional[bool] = None
    shared_with: Optional[str] = None
    next_billing: Optional[str] = None
    notes: Optional[str] = None
    active: Optional[bool] = None

@router.get("")
def list_subscriptions(
    active_only: bool = True,
    category: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """List all subscriptions with optional filters"""
    query = select(Subscription)
    
    if active_only:
        query = query.where(Subscription.active == True)
    
    if category:
        query = query.where(Subscription.category == category)
    
    query = query.order_by(Subscription.name)
    subs = session.exec(query).all()
    
    # Calculate totals
    monthly_total = 0.0
    yearly_total = 0.0
    
    for sub in subs:
        if not sub.active:
            continue
        price = sub.my_price if sub.my_price is not None else sub.full_price
        if sub.billing_cycle == BillingCycle.MONTHLY:
            monthly_total += price
            yearly_total += price * 12
        elif sub.billing_cycle == BillingCycle.YEARLY:
            monthly_total += price / 12
            yearly_total += price
        elif sub.billing_cycle == BillingCycle.WEEKLY:
            monthly_total += price * 4.33
            yearly_total += price * 52
    
    return {
        "subscriptions": [
            {
                "id": s.id,
                "name": s.name,
                "full_price": s.full_price,
                "my_price": s.my_price,
                "effective_price": s.my_price if s.my_price is not None else s.full_price,
                "billing_cycle": s.billing_cycle,
                "category": s.category,
                "is_shared": s.is_shared,
                "shared_with": s.shared_with,
                "next_billing": s.next_billing.isoformat() if s.next_billing else None,
                "notes": s.notes,
                "active": s.active,
            }
            for s in subs
        ],
        "totals": {
            "monthly": round(monthly_total, 2),
            "yearly": round(yearly_total, 2),
            "count": len([s for s in subs if s.active]),
        }
    }

@router.post("")
def create_subscription(data: SubscriptionCreate, session: Session = Depends(get_session)):
    """Create a new subscription"""
    from datetime import date
    
    sub = Subscription(
        name=data.name,
        full_price=data.full_price,
        my_price=data.my_price,
        billing_cycle=BillingCycle(data.billing_cycle),
        category=SubscriptionCategory(data.category),
        is_shared=data.is_shared,
        shared_with=data.shared_with,
        next_billing=date.fromisoformat(data.next_billing) if data.next_billing else None,
        notes=data.notes,
        active=data.active,
    )
    
    session.add(sub)
    session.commit()
    session.refresh(sub)
    
    return {"ok": True, "id": sub.id, "name": sub.name}

@router.get("/{sub_id}")
def get_subscription(sub_id: int, session: Session = Depends(get_session)):
    """Get a single subscription"""
    sub = session.get(Subscription, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return {
        "id": sub.id,
        "name": sub.name,
        "full_price": sub.full_price,
        "my_price": sub.my_price,
        "effective_price": sub.my_price if sub.my_price is not None else sub.full_price,
        "billing_cycle": sub.billing_cycle,
        "category": sub.category,
        "is_shared": sub.is_shared,
        "shared_with": sub.shared_with,
        "next_billing": sub.next_billing.isoformat() if sub.next_billing else None,
        "notes": sub.notes,
        "active": sub.active,
    }

@router.put("/{sub_id}")
def update_subscription(sub_id: int, data: SubscriptionUpdate, session: Session = Depends(get_session)):
    """Update a subscription"""
    from datetime import date
    
    sub = session.get(Subscription, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if data.name is not None:
        sub.name = data.name
    if data.full_price is not None:
        sub.full_price = data.full_price
    if data.my_price is not None:
        sub.my_price = data.my_price
    if data.billing_cycle is not None:
        sub.billing_cycle = BillingCycle(data.billing_cycle)
    if data.category is not None:
        sub.category = SubscriptionCategory(data.category)
    if data.is_shared is not None:
        sub.is_shared = data.is_shared
    if data.shared_with is not None:
        sub.shared_with = data.shared_with
    if data.next_billing is not None:
        sub.next_billing = date.fromisoformat(data.next_billing)
    if data.notes is not None:
        sub.notes = data.notes
    if data.active is not None:
        sub.active = data.active
    
    session.add(sub)
    session.commit()
    session.refresh(sub)
    
    return {"ok": True, "id": sub.id}

@router.delete("/{sub_id}")
def delete_subscription(sub_id: int, session: Session = Depends(get_session)):
    """Delete a subscription (or set inactive)"""
    sub = session.get(Subscription, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Soft delete - just mark inactive
    sub.active = False
    session.add(sub)
    session.commit()
    
    return {"ok": True, "id": sub_id}

@router.get("/stats/summary")
def subscription_stats(session: Session = Depends(get_session)):
    """Get subscription statistics by category"""
    subs = session.exec(
        select(Subscription).where(Subscription.active == True)
    ).all()
    
    by_category = {}
    for sub in subs:
        cat = sub.category.value if sub.category else "other"
        if cat not in by_category:
            by_category[cat] = {"count": 0, "monthly": 0.0}
        
        price = sub.my_price if sub.my_price is not None else sub.full_price
        monthly = price
        if sub.billing_cycle == BillingCycle.YEARLY:
            monthly = price / 12
        elif sub.billing_cycle == BillingCycle.WEEKLY:
            monthly = price * 4.33
        
        by_category[cat]["count"] += 1
        by_category[cat]["monthly"] += monthly
    
    # Round values
    for cat in by_category:
        by_category[cat]["monthly"] = round(by_category[cat]["monthly"], 2)
    
    return {
        "by_category": by_category,
        "total_subscriptions": len(subs),
    }
