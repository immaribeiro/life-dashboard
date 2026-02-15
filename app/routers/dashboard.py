from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from datetime import date, datetime
from app.database import get_session
from app.models import Reminder, ReminderStatus, FoodLog, TrainingLog, MentalLog, DailySummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/today")
def get_today(session: Session = Depends(get_session)):
    today = date.today()
    today_start = f"{today}T00:00:00"
    today_end = f"{today}T23:59:59"

    reminders = session.exec(select(Reminder).where(Reminder.status == ReminderStatus.PENDING)).all()
    food = session.exec(select(FoodLog).where(FoodLog.logged_at >= today_start).where(FoodLog.logged_at <= today_end)).all()
    training = session.exec(select(TrainingLog).where(TrainingLog.logged_at >= today_start).where(TrainingLog.logged_at <= today_end)).all()
    mental = session.exec(select(MentalLog).where(MentalLog.logged_at >= today_start).where(MentalLog.logged_at <= today_end)).all()
    summary = session.exec(select(DailySummary).where(DailySummary.date == today)).first()

    return {
        "date": str(today),
        "reminders": reminders,
        "food": food,
        "training": training,
        "mental": mental,
        "summary": summary,
    }
