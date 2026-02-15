from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from app.database import get_session
from app.models import TrainingLog
from app.auth import require_api_key

router = APIRouter(prefix="/training", tags=["training"])

@router.post("", dependencies=[Depends(require_api_key)])
def create_training(entry: TrainingLog, session: Session = Depends(get_session)):
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry

@router.get("")
def list_training(date: Optional[str] = None, session: Session = Depends(get_session)):
    query = select(TrainingLog)
    if date:
        query = query.where(TrainingLog.logged_at >= f"{date}T00:00:00").where(TrainingLog.logged_at <= f"{date}T23:59:59")
    return session.exec(query.order_by(TrainingLog.logged_at.desc())).all()

@router.delete("/{id}", dependencies=[Depends(require_api_key)])
def delete_training(id: int, session: Session = Depends(get_session)):
    entry = session.get(TrainingLog, id)
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    session.delete(entry)
    session.commit()
    return {"ok": True}
