from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime, date
from app.database import get_session
from app.models import FoodLog, TrainingLog, MentalLog, Reminder, ReminderStatus

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")

# --- Page routes ---

@router.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/history")
async def history(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@router.get("/reminders")
async def reminders_page(request: Request):
    return templates.TemplateResponse("reminders.html", {"request": request})

@router.get("/settings")
async def settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

# --- HTMX partial routes ---

def _render_food(items):
    if not items:
        return '<p class="text-slate-500 text-sm">Nothing logged yet.</p>'
    rows = "".join(f'<li class="text-sm text-slate-300 py-1 border-b border-slate-700">{i.description}{" · <span class=\'text-slate-500\'>" + i.meal_type + "</span>" if i.meal_type else ""}</li>' for i in items)
    return f"<ul>{rows}</ul>"

def _render_training(items):
    if not items:
        return '<p class="text-slate-500 text-sm">No training logged yet.</p>'
    rows = "".join(f'<li class="text-sm text-slate-300 py-1 border-b border-slate-700">{i.activity}{" · " + str(i.duration_minutes) + "min" if i.duration_minutes else ""}</li>' for i in items)
    return f"<ul>{rows}</ul>"

def _render_mental(items):
    if not items:
        return '<p class="text-slate-500 text-sm">No notes yet.</p>'
    rows = "".join(f'<li class="text-sm text-slate-300 py-1 border-b border-slate-700">{i.content}</li>' for i in items)
    return f"<ul>{rows}</ul>"

def _render_reminders(items):
    if not items:
        return '<p class="text-slate-500 text-sm">No reminders.</p>'
    rows = "".join(
        f'<li class="text-sm text-slate-300 py-1 border-b border-slate-700 flex justify-between">'
        f'<span>{r.text}</span>'
        f'<button hx-patch="/partials/reminders/{r.id}/done" hx-target="#reminder-list" hx-swap="innerHTML" class="text-xs text-green-500 hover:text-green-300">✓</button>'
        f'</li>'
        for r in items if r.status == ReminderStatus.PENDING
    )
    return f"<ul>{rows}</ul>" if rows else '<p class="text-slate-500 text-sm">All done! ✓</p>'

@router.get("/partials/food", response_class=HTMLResponse)
async def partial_food(session: Session = Depends(get_session)):
    today = date.today()
    items = session.exec(select(FoodLog).where(FoodLog.logged_at >= f"{today}T00:00:00")).all()
    return _render_food(items)

@router.post("/partials/food", response_class=HTMLResponse)
async def partial_food_add(description: str = Form(...), meal_type: str = Form(default=None), session: Session = Depends(get_session)):
    entry = FoodLog(description=description, meal_type=meal_type or None)
    session.add(entry)
    session.commit()
    today = date.today()
    items = session.exec(select(FoodLog).where(FoodLog.logged_at >= f"{today}T00:00:00")).all()
    return _render_food(items)

@router.get("/partials/training", response_class=HTMLResponse)
async def partial_training(session: Session = Depends(get_session)):
    today = date.today()
    items = session.exec(select(TrainingLog).where(TrainingLog.logged_at >= f"{today}T00:00:00")).all()
    return _render_training(items)

@router.post("/partials/training", response_class=HTMLResponse)
async def partial_training_add(activity: str = Form(...), duration_minutes: Optional[int] = Form(default=None), session: Session = Depends(get_session)):
    entry = TrainingLog(activity=activity, duration_minutes=duration_minutes)
    session.add(entry)
    session.commit()
    today = date.today()
    items = session.exec(select(TrainingLog).where(TrainingLog.logged_at >= f"{today}T00:00:00")).all()
    return _render_training(items)

@router.get("/partials/mental", response_class=HTMLResponse)
async def partial_mental(session: Session = Depends(get_session)):
    today = date.today()
    items = session.exec(select(MentalLog).where(MentalLog.logged_at >= f"{today}T00:00:00")).all()
    return _render_mental(items)

@router.post("/partials/mental", response_class=HTMLResponse)
async def partial_mental_add(content: str = Form(...), session: Session = Depends(get_session)):
    entry = MentalLog(content=content)
    session.add(entry)
    session.commit()
    today = date.today()
    items = session.exec(select(MentalLog).where(MentalLog.logged_at >= f"{today}T00:00:00")).all()
    return _render_mental(items)

@router.get("/partials/reminders", response_class=HTMLResponse)
async def partial_reminders(session: Session = Depends(get_session)):
    items = session.exec(select(Reminder).where(Reminder.status == ReminderStatus.PENDING)).all()
    return _render_reminders(items)

@router.post("/partials/reminders", response_class=HTMLResponse)
async def partial_reminders_add(text: str = Form(...), due_at: Optional[str] = Form(default=None), session: Session = Depends(get_session)):
    due = datetime.fromisoformat(due_at) if due_at else None
    entry = Reminder(text=text, due_at=due)
    session.add(entry)
    session.commit()
    items = session.exec(select(Reminder).where(Reminder.status == ReminderStatus.PENDING)).all()
    return _render_reminders(items)

@router.patch("/partials/reminders/{id}/done", response_class=HTMLResponse)
async def partial_reminders_done(id: int, session: Session = Depends(get_session)):
    r = session.get(Reminder, id)
    if r:
        r.status = ReminderStatus.DONE
        r.completed_at = datetime.utcnow()
        session.commit()
    items = session.exec(select(Reminder).where(Reminder.status == ReminderStatus.PENDING)).all()
    return _render_reminders(items)

@router.get("/partials/history", response_class=HTMLResponse)
async def partial_history(session: Session = Depends(get_session)):
    food = session.exec(select(FoodLog).order_by(FoodLog.logged_at.desc()).limit(20)).all()
    training = session.exec(select(TrainingLog).order_by(TrainingLog.logged_at.desc()).limit(10)).all()
    parts = []
    if food:
        rows = "".join(f'<li class="text-sm text-slate-300 py-1">{i.logged_at.strftime("%d/%m %H:%M")} — {i.description}</li>' for i in food)
        parts.append(f'<h3 class="text-green-400 font-semibold mb-2 mt-4">🍽️ Food</h3><ul>{rows}</ul>')
    if training:
        rows = "".join(f'<li class="text-sm text-slate-300 py-1">{i.logged_at.strftime("%d/%m %H:%M")} — {i.activity}{" (" + str(i.duration_minutes) + "min)" if i.duration_minutes else ""}</li>' for i in training)
        parts.append(f'<h3 class="text-blue-400 font-semibold mb-2 mt-4">💪 Training</h3><ul>{rows}</ul>')
    return "".join(parts) if parts else '<p class="text-slate-500 text-sm">No history yet.</p>'
