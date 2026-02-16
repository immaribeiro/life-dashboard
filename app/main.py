from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import reminders, food, training, mental, summary, dashboard, ui, weight, stats, calendar, subscriptions, suggestions

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Life Dashboard", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(reminders.router, prefix="/api")
app.include_router(food.router, prefix="/api")
app.include_router(training.router, prefix="/api")
app.include_router(mental.router, prefix="/api")
app.include_router(summary.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(weight.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(subscriptions.router)  # prefix already in router
app.include_router(suggestions.router)    # prefix already in router
app.include_router(ui.router)

@app.get("/health")
def health():
    return {"status": "ok"}
