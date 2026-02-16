from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum

class ReminderStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    DISMISSED = "dismissed"

class BillingCycle(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"

class SubscriptionCategory(str, Enum):
    ENTERTAINMENT = "entertainment"
    PRODUCTIVITY = "productivity"
    HEALTH = "health"
    FINANCE = "finance"
    EDUCATION = "education"
    CLOUD = "cloud"
    AI = "ai"
    OTHER = "other"

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
    summary_date: date = Field(unique=True)
    highlight: Optional[str] = None
    challenge: Optional[str] = None
    energy_level: Optional[int] = None
    sleep_quality: Optional[int] = None
    gratitude: Optional[str] = None
    tomorrow_focus: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WeightLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    weight_kg: float
    logged_at: date = Field(default_factory=date.today)
    notes: Optional[str] = None

class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    full_price: float  # Full subscription price
    my_price: Optional[float] = None  # What I actually pay (for shared)
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    category: SubscriptionCategory = SubscriptionCategory.OTHER
    is_shared: bool = False
    shared_with: Optional[str] = None  # "Maria, João" or "family"
    next_billing: Optional[date] = None
    notes: Optional[str] = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Suggestion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category: str  # "subscriptions", "training", "food", "money", "general"
    content: str
    priority: int = 0  # Higher = more important
    dismissed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    dismissed_at: Optional[datetime] = None
