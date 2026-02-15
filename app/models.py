from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum

class ReminderStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    DISMISSED = "dismissed"

class Reminder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    due_at: Optional[datetime] = None
    status: ReminderStatus = ReminderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class FoodLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    meal_type: Optional[str] = None
    logged_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class TrainingLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    activity: str
    duration_minutes: Optional[int] = None
    intensity: Optional[str] = None
    logged_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class MentalLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    mood: Optional[str] = None
    tags: Optional[str] = None
    logged_at: datetime = Field(default_factory=datetime.utcnow)

class DailySummary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: date = Field(unique=True)
    highlight: Optional[str] = None
    challenge: Optional[str] = None
    energy_level: Optional[int] = None
    sleep_quality: Optional[int] = None
    gratitude: Optional[str] = None
    tomorrow_focus: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
