from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from datetime import date as date_type, datetime, time
from app.database import get_session
from app.models import MentalLog
from app.auth import require_api_key

router = APIRouter(prefix="/mental", tags=["mental"])

@router.post("", dependencies=[Depends(require_api_key)])
def create_mental(entry: MentalLog, session: Session = Depends(get_session)):
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry

@router.get("")
def list_mental(date: Optional[str] = None, session: Session = Depends(get_session)):
    query = select(MentalLog)
    if date:
        d = date_type.fromisoformat(date)
        start = datetime.combine(d, time.min)
        end = datetime.combine(d, time.max)
        query = query.where(MentalLog.logged_at >= start).where(MentalLog.logged_at <= end)
    return session.exec(query.order_by(MentalLog.logged_at.desc())).all()

@router.delete("/{id}", dependencies=[Depends(require_api_key)])
def delete_mental(id: int, session: Session = Depends(get_session)):
    entry = session.get(MentalLog, id)
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    session.delete(entry)
    session.commit()
    return {"ok": True}
