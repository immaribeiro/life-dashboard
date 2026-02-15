from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from datetime import date
from app.database import get_session
from app.models import FoodLog
from app.auth import require_api_key

router = APIRouter(prefix="/food", tags=["food"])

@router.post("", dependencies=[Depends(require_api_key)])
def create_food(entry: FoodLog, session: Session = Depends(get_session)):
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry

@router.get("")
def list_food(date: Optional[str] = None, session: Session = Depends(get_session)):
    query = select(FoodLog)
    if date:
        query = query.where(FoodLog.logged_at >= f"{date}T00:00:00").where(FoodLog.logged_at <= f"{date}T23:59:59")
    return session.exec(query.order_by(FoodLog.logged_at.desc())).all()

@router.delete("/{id}", dependencies=[Depends(require_api_key)])
def delete_food(id: int, session: Session = Depends(get_session)):
    entry = session.get(FoodLog, id)
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    session.delete(entry)
    session.commit()
    return {"ok": True}
