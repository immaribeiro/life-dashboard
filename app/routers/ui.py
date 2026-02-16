from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime, date, time
from app.database import get_session
from app.models import FoodLog, TrainingLog, MentalLog, Reminder, ReminderStatus, WeightLog, Subscription, BillingCycle, Suggestion

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

@router.get("/analytics")
async def analytics(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

@router.get("/subscriptions")
async def subscriptions_page(request: Request):
    return templates.TemplateResponse("subscriptions.html", {"request": request})

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
    today_start = datetime.combine(date.today(), time.min)
    items = session.exec(select(FoodLog).where(FoodLog.logged_at >= today_start)).all()
    return _render_food(items)

@router.post("/partials/food", response_class=HTMLResponse)
async def partial_food_add(description: str = Form(...), meal_type: str = Form(default=None), session: Session = Depends(get_session)):
    entry = FoodLog(description=description, meal_type=meal_type or None)
    session.add(entry)
    session.commit()
    today_start = datetime.combine(date.today(), time.min)
    items = session.exec(select(FoodLog).where(FoodLog.logged_at >= today_start)).all()
    return _render_food(items)

@router.get("/partials/training", response_class=HTMLResponse)
async def partial_training(session: Session = Depends(get_session)):
    today_start = datetime.combine(date.today(), time.min)
    items = session.exec(select(TrainingLog).where(TrainingLog.logged_at >= today_start)).all()
    return _render_training(items)

@router.post("/partials/training", response_class=HTMLResponse)
async def partial_training_add(activity: str = Form(...), duration_minutes: Optional[int] = Form(default=None), session: Session = Depends(get_session)):
    entry = TrainingLog(activity=activity, duration_minutes=duration_minutes)
    session.add(entry)
    session.commit()
    today_start = datetime.combine(date.today(), time.min)
    items = session.exec(select(TrainingLog).where(TrainingLog.logged_at >= today_start)).all()
    return _render_training(items)

@router.get("/partials/mental", response_class=HTMLResponse)
async def partial_mental(session: Session = Depends(get_session)):
    today_start = datetime.combine(date.today(), time.min)
    items = session.exec(select(MentalLog).where(MentalLog.logged_at >= today_start)).all()
    return _render_mental(items)

@router.post("/partials/mental", response_class=HTMLResponse)
async def partial_mental_add(content: str = Form(...), session: Session = Depends(get_session)):
    entry = MentalLog(content=content)
    session.add(entry)
    session.commit()
    today_start = datetime.combine(date.today(), time.min)
    items = session.exec(select(MentalLog).where(MentalLog.logged_at >= today_start)).all()
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

@router.get("/partials/calendar-today", response_class=HTMLResponse)
async def partial_calendar_today():
    """Get today's calendar events (legacy, redirects to calendar-day)"""
    return await partial_calendar_day(0)

@router.get("/partials/calendar-day", response_class=HTMLResponse)
async def partial_calendar_day(offset: int = 0):
    """Get calendar events for a specific day (0=today, 1=tomorrow, etc.)"""
    try:
        from app.routers.calendar import get_credentials
        from googleapiclient.discovery import build
        from datetime import timedelta
        
        creds = get_credentials()
        if not creds:
            return '<p class="text-slate-500 text-sm">Calendar not connected. <a href="/api/calendar/auth" class="text-cyan-400 hover:underline">Connect Google Calendar</a></p>'
        
        service = build('calendar', 'v3', credentials=creds)
        target_date = date.today() + timedelta(days=offset)
        next_date = target_date + timedelta(days=1)
        
        # Date label
        if offset == 0:
            date_label = "Today"
        elif offset == 1:
            date_label = "Tomorrow"
        else:
            date_label = target_date.strftime('%A, %d %b')
        
        # Get events for target date
        day_start = datetime.combine(target_date, time.min).isoformat() + 'Z'
        day_end = datetime.combine(next_date, time.min).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=day_start,
            timeMax=day_end,
            maxResults=20,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        header = f'<p class="text-slate-400 text-xs mb-2">{date_label} — {target_date.strftime("%d/%m/%Y")}</p>'
        
        if not events:
            return header + f'<p class="text-slate-500 text-sm">No events scheduled ✨</p>'
        
        rows = []
        for e in events:
            start = e.get('start', {})
            start_time = start.get('dateTime', start.get('date', ''))
            
            # Format time
            if 'T' in start_time:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M')
            else:
                time_str = 'All day'
            
            summary = e.get('summary', '(No title)')
            location = e.get('location', '')
            
            loc_html = f'<span class="text-slate-500 text-xs ml-2">📍 {location[:30]}</span>' if location else ''
            
            rows.append(f'''
                <li class="flex items-center gap-3 py-2 border-b border-slate-700 last:border-0">
                    <span class="text-cyan-400 font-mono text-sm w-14">{time_str}</span>
                    <span class="text-slate-200 text-sm flex-1">{summary}</span>
                    {loc_html}
                </li>
            ''')
        
        return header + f'<ul>{"".join(rows)}</ul>'
        
    except Exception as ex:
        return f'<p class="text-red-400 text-sm">Error loading calendar: {str(ex)[:100]}</p>'

@router.get("/partials/stats-cards", response_class=HTMLResponse)
async def partial_stats_cards(session: Session = Depends(get_session)):
    from datetime import timedelta
    from sqlmodel import func
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    week_start_dt = datetime.combine(week_start, time.min)
    month_start_dt = datetime.combine(month_start, time.min)
    
    trainings_week = session.exec(select(func.count(TrainingLog.id)).where(TrainingLog.logged_at >= week_start_dt)).one()
    trainings_month = session.exec(select(func.count(TrainingLog.id)).where(TrainingLog.logged_at >= month_start_dt)).one()
    
    latest_weight = session.exec(select(WeightLog).order_by(WeightLog.logged_at.desc())).first()
    weight_30d_ago = session.exec(select(WeightLog).where(WeightLog.logged_at <= today - timedelta(days=30)).order_by(WeightLog.logged_at.desc())).first()
    
    weight_change = ""
    if latest_weight and weight_30d_ago:
        diff = latest_weight.weight_kg - weight_30d_ago.weight_kg
        sign = "+" if diff > 0 else ""
        weight_change = f'<span class="text-xs {"text-red-400" if diff > 0 else "text-green-400"}">{sign}{diff:.1f} kg</span>'
    
    return f'''
    <div class="bg-slate-800 rounded-lg p-4 text-center">
        <div class="text-3xl font-bold text-blue-400">{trainings_week}</div>
        <div class="text-slate-400 text-sm">Trainings this week</div>
    </div>
    <div class="bg-slate-800 rounded-lg p-4 text-center">
        <div class="text-3xl font-bold text-green-400">{trainings_month}</div>
        <div class="text-slate-400 text-sm">Trainings this month</div>
    </div>
    <div class="bg-slate-800 rounded-lg p-4 text-center">
        <div class="text-3xl font-bold text-purple-400">{latest_weight.weight_kg if latest_weight else "—"}</div>
        <div class="text-slate-400 text-sm">Latest weight (kg) {weight_change}</div>
    </div>
    <div class="bg-slate-800 rounded-lg p-4 text-center">
        <div class="text-3xl font-bold text-amber-400">{today.strftime("%d %b")}</div>
        <div class="text-slate-400 text-sm">Today</div>
    </div>
    '''

@router.post("/partials/weight", response_class=HTMLResponse)
async def partial_weight_add(weight_kg: float = Form(...), notes: Optional[str] = Form(default=None), session: Session = Depends(get_session)):
    today = date.today()
    existing = session.exec(select(WeightLog).where(WeightLog.logged_at == today)).first()
    if existing:
        existing.weight_kg = weight_kg
        existing.notes = notes
        session.commit()
    else:
        entry = WeightLog(weight_kg=weight_kg, logged_at=today, notes=notes)
        session.add(entry)
        session.commit()
    # Return updated stats cards
    return await partial_stats_cards(session)

# --- Subscriptions partials ---

@router.get("/partials/subscriptions-list", response_class=HTMLResponse)
async def partial_subscriptions_list(session: Session = Depends(get_session)):
    subs = session.exec(
        select(Subscription).where(Subscription.active == True).order_by(Subscription.category, Subscription.name)
    ).all()
    
    if not subs:
        return '<p class="text-slate-500 text-sm">No subscriptions yet. Add your first one!</p>'
    
    # Calculate totals
    monthly_total = 0.0
    for sub in subs:
        price = sub.my_price if sub.my_price is not None else sub.full_price
        if sub.billing_cycle == BillingCycle.MONTHLY:
            monthly_total += price
        elif sub.billing_cycle == BillingCycle.YEARLY:
            monthly_total += price / 12
        elif sub.billing_cycle == BillingCycle.WEEKLY:
            monthly_total += price * 4.33
    
    rows = []
    for sub in subs:
        price = sub.my_price if sub.my_price is not None else sub.full_price
        shared_badge = f'<span class="text-xs bg-blue-900 text-blue-300 px-1.5 py-0.5 rounded ml-2">shared</span>' if sub.is_shared else ''
        shared_with = f'<span class="text-slate-500 text-xs ml-1">w/ {sub.shared_with}</span>' if sub.shared_with else ''
        cycle_text = sub.billing_cycle.value[:3] if sub.billing_cycle else 'mo'
        
        rows.append(f'''
            <tr class="border-b border-slate-700 hover:bg-slate-800">
                <td class="py-3 px-2">
                    <span class="text-slate-200">{sub.name}</span>
                    {shared_badge}{shared_with}
                </td>
                <td class="py-3 px-2 text-right">
                    <span class="text-cyan-400 font-mono">€{price:.2f}</span>
                    <span class="text-slate-500 text-xs">/{cycle_text}</span>
                </td>
                <td class="py-3 px-2 text-center">
                    <span class="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded">{sub.category.value if sub.category else 'other'}</span>
                </td>
                <td class="py-3 px-2 text-right">
                    <button hx-delete="/api/subscriptions/{sub.id}" hx-target="#subscriptions-list" hx-swap="innerHTML"
                            hx-confirm="Cancel {sub.name}?" 
                            class="text-red-400 hover:text-red-300 text-sm">✕</button>
                </td>
            </tr>
        ''')
    
    return f'''
        <div class="mb-4 text-right">
            <span class="text-slate-400">Monthly total:</span>
            <span class="text-2xl font-bold text-cyan-400 ml-2">€{monthly_total:.2f}</span>
        </div>
        <table class="w-full">
            <thead>
                <tr class="text-left text-slate-400 text-sm border-b border-slate-600">
                    <th class="pb-2 px-2">Service</th>
                    <th class="pb-2 px-2 text-right">Cost</th>
                    <th class="pb-2 px-2 text-center">Category</th>
                    <th class="pb-2 px-2"></th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
    '''

@router.get("/partials/suggestions-box", response_class=HTMLResponse)
async def partial_suggestions_box(category: str = "subscriptions", session: Session = Depends(get_session)):
    suggestions = session.exec(
        select(Suggestion)
        .where(Suggestion.category == category)
        .where(Suggestion.dismissed == False)
        .order_by(Suggestion.priority.desc(), Suggestion.created_at.desc())
        .limit(5)
    ).all()
    
    if not suggestions:
        return '''
            <p class="text-slate-500 text-sm">No suggestions right now.</p>
            <p class="text-slate-600 text-xs mt-2">Ask Smith to analyze your subscriptions for savings tips!</p>
        '''
    
    items = []
    for s in suggestions:
        items.append(f'''
            <li class="flex items-start gap-2 py-2 border-b border-slate-700 last:border-0">
                <span class="text-slate-300 text-sm flex-1">{s.content}</span>
                <button hx-post="/api/suggestions/{s.id}/dismiss" hx-target="#suggestions-box" hx-swap="innerHTML"
                        class="text-slate-500 hover:text-slate-300 text-xs">✕</button>
            </li>
        ''')
    
    return f'<ul>{"".join(items)}</ul>'
