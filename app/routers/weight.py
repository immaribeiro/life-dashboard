from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from datetime import date as date_type
from app.database import get_session
from app.models import WeightLog
from app.auth import require_api_key

router = APIRouter(prefix="/weight", tags=["weight"])

@router.post("", dependencies=[Depends(require_api_key)])
def create_weight(entry: WeightLog, session: Session = Depends(get_session)):
    # Upsert: if weight for this date exists, update it
    existing = session.exec(select(WeightLog).where(WeightLog.logged_at == entry.logged_at)).first()
    if existing:
        existing.weight_kg = entry.weight_kg
        existing.notes = entry.notes
        session.commit()
        session.refresh(existing)
        return existing
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry

@router.get("")
def list_weight(days: Optional[int] = 30, session: Session = Depends(get_session)):
    """Get weight entries for the last N days"""
    from datetime import timedelta
    cutoff = date_type.today() - timedelta(days=days)
    entries = session.exec(
        select(WeightLog)
        .where(WeightLog.logged_at >= cutoff)
        .order_by(WeightLog.logged_at.asc())
    ).all()
    return entries

@router.get("/latest")
def get_latest_weight(session: Session = Depends(get_session)):
    """Get the most recent weight entry"""
    entry = session.exec(select(WeightLog).order_by(WeightLog.logged_at.desc())).first()
    if not entry:
        raise HTTPException(status_code=404, detail="No weight entries")
    return entry

@router.delete("/{id}", dependencies=[Depends(require_api_key)])
def delete_weight(id: int, session: Session = Depends(get_session)):
    entry = session.get(WeightLog, id)
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    session.delete(entry)
    session.commit()
    return {"ok": True}
