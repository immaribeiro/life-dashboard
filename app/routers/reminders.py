from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime
from app.database import get_session
from app.models import Reminder, ReminderStatus
from app.auth import require_api_key

router = APIRouter(prefix="/reminders", tags=["reminders"])

@router.post("", dependencies=[Depends(require_api_key)])
def create_reminder(reminder: Reminder, session: Session = Depends(get_session)):
    session.add(reminder)
    session.commit()
    session.refresh(reminder)
    return reminder

@router.get("")
def list_reminders(status: Optional[str] = None, session: Session = Depends(get_session)):
    query = select(Reminder)
    if status:
        query = query.where(Reminder.status == status)
    return session.exec(query).all()

@router.patch("/{id}", dependencies=[Depends(require_api_key)])
def update_reminder(id: int, data: dict, session: Session = Depends(get_session)):
    reminder = session.get(Reminder, id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.items():
        setattr(reminder, k, v)
    if data.get("status") == "done" and not reminder.completed_at:
        reminder.completed_at = datetime.utcnow()
    session.commit()
    session.refresh(reminder)
    return reminder

@router.delete("/{id}", dependencies=[Depends(require_api_key)])
def delete_reminder(id: int, session: Session = Depends(get_session)):
    reminder = session.get(Reminder, id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Not found")
    session.delete(reminder)
    session.commit()
    return {"ok": True}
