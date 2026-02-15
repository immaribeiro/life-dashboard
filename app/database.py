from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

engine = None

def get_engine():
    global engine
    if engine is None:
        engine = create_engine(f"sqlite:///{settings.database_path}", connect_args={"check_same_thread": False})
    return engine

def init_db():
    SQLModel.metadata.create_all(get_engine())

def get_session():
    with Session(get_engine()) as session:
        yield session
