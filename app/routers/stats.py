from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from datetime import date, datetime, timedelta
from app.database import get_session
from app.models import TrainingLog, WeightLog, FoodLog, MentalLog

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("")
def get_stats(session: Session = Depends(get_session)):
    """Get aggregated statistics for dashboard"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    month_start = today.replace(day=1)
    
    # Training counts
    week_start_dt = datetime.combine(week_start, datetime.min.time())
    month_start_dt = datetime.combine(month_start, datetime.min.time())
    
    trainings_this_week = session.exec(
        select(func.count(TrainingLog.id))
        .where(TrainingLog.logged_at >= week_start_dt)
    ).one()
    
    trainings_this_month = session.exec(
        select(func.count(TrainingLog.id))
        .where(TrainingLog.logged_at >= month_start_dt)
    ).one()
    
    # Weight trend (last 30 days)
    weight_cutoff = today - timedelta(days=30)
    weight_entries = session.exec(
        select(WeightLog)
        .where(WeightLog.logged_at >= weight_cutoff)
        .order_by(WeightLog.logged_at.asc())
    ).all()
    
    weight_data = [{"date": str(w.logged_at), "weight": w.weight_kg} for w in weight_entries]
    
    # Calculate weight change
    weight_change = None
    if len(weight_entries) >= 2:
        weight_change = round(weight_entries[-1].weight_kg - weight_entries[0].weight_kg, 1)
    
    # Training history for chart (last 4 weeks, grouped by week)
    four_weeks_ago = today - timedelta(days=28)
    four_weeks_dt = datetime.combine(four_weeks_ago, datetime.min.time())
    
    trainings = session.exec(
        select(TrainingLog)
        .where(TrainingLog.logged_at >= four_weeks_dt)
        .order_by(TrainingLog.logged_at.asc())
    ).all()
    
    # Group by week
    weekly_training = {}
    for t in trainings:
        week_num = t.logged_at.isocalendar()[1]
        weekly_training[week_num] = weekly_training.get(week_num, 0) + 1
    
    return {
        "training": {
            "this_week": trainings_this_week,
            "this_month": trainings_this_month,
            "weekly_breakdown": weekly_training
        },
        "weight": {
            "entries": weight_data,
            "change_30d": weight_change,
            "latest": weight_entries[-1].weight_kg if weight_entries else None
        }
    }
