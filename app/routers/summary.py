from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from app.database import get_session
from app.models import DailySummary
from app.auth import require_api_key
from datetime import date as date_type

router = APIRouter(prefix="/summary", tags=["summary"])

from datetime import date as date_type

@router.post("", dependencies=[Depends(require_api_key)])
def upsert_summary(entry: DailySummary, session: Session = Depends(get_session)):
    # Ensure summary_date is a date object
    if isinstance(entry.summary_date, str):
        entry.summary_date = date_type.fromisoformat(entry.summary_date)
    
    existing = session.exec(select(DailySummary).where(DailySummary.summary_date == entry.summary_date)).first()
    if existing:
        for field in ["highlight", "challenge", "energy_level", "sleep_quality", "gratitude", "tomorrow_focus"]:
            val = getattr(entry, field)
            if val is not None:
                setattr(existing, field, val)
        session.commit()
        session.refresh(existing)
        return existing
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry

@router.get("/{date}")
def get_summary(date: str, session: Session = Depends(get_session)):
    from datetime import date as date_type
    d = date_type.fromisoformat(date)
    entry = session.exec(select(DailySummary).where(DailySummary.summary_date == d)).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    return entry

@router.get("")
def list_summaries(session: Session = Depends(get_session)):
    return session.exec(select(DailySummary).order_by(DailySummary.date.desc())).all()
