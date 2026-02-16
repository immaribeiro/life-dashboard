from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_session
from app.models import Suggestion

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])

class SuggestionCreate(BaseModel):
    category: str
    content: str
    priority: int = 0

class SuggestionUpdate(BaseModel):
    content: Optional[str] = None
    priority: Optional[int] = None
    dismissed: Optional[bool] = None

@router.get("")
def list_suggestions(
    category: Optional[str] = None,
    include_dismissed: bool = False,
    session: Session = Depends(get_session)
):
    """List suggestions with optional filters"""
    query = select(Suggestion)
    
    if not include_dismissed:
        query = query.where(Suggestion.dismissed == False)
    
    if category:
        query = query.where(Suggestion.category == category)
    
    query = query.order_by(Suggestion.priority.desc(), Suggestion.created_at.desc())
    suggestions = session.exec(query).all()
    
    return {
        "suggestions": [
            {
                "id": s.id,
                "category": s.category,
                "content": s.content,
                "priority": s.priority,
                "dismissed": s.dismissed,
                "created_at": s.created_at.isoformat(),
            }
            for s in suggestions
        ],
        "count": len(suggestions),
    }

@router.post("")
def create_suggestion(data: SuggestionCreate, session: Session = Depends(get_session)):
    """Create a new suggestion (typically called by Smith)"""
    suggestion = Suggestion(
        category=data.category,
        content=data.content,
        priority=data.priority,
    )
    
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)
    
    return {"ok": True, "id": suggestion.id}

@router.post("/bulk")
def create_suggestions_bulk(suggestions: list[SuggestionCreate], session: Session = Depends(get_session)):
    """Create multiple suggestions at once"""
    created = []
    for data in suggestions:
        suggestion = Suggestion(
            category=data.category,
            content=data.content,
            priority=data.priority,
        )
        session.add(suggestion)
        created.append(suggestion)
    
    session.commit()
    
    return {"ok": True, "count": len(created)}

@router.put("/{suggestion_id}")
def update_suggestion(suggestion_id: int, data: SuggestionUpdate, session: Session = Depends(get_session)):
    """Update a suggestion"""
    suggestion = session.get(Suggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    if data.content is not None:
        suggestion.content = data.content
    if data.priority is not None:
        suggestion.priority = data.priority
    if data.dismissed is not None:
        suggestion.dismissed = data.dismissed
        if data.dismissed:
            suggestion.dismissed_at = datetime.utcnow()
    
    session.add(suggestion)
    session.commit()
    
    return {"ok": True, "id": suggestion_id}

@router.post("/{suggestion_id}/dismiss")
def dismiss_suggestion(suggestion_id: int, session: Session = Depends(get_session)):
    """Dismiss a suggestion"""
    suggestion = session.get(Suggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    suggestion.dismissed = True
    suggestion.dismissed_at = datetime.utcnow()
    session.add(suggestion)
    session.commit()
    
    return {"ok": True, "id": suggestion_id}

@router.delete("/{suggestion_id}")
def delete_suggestion(suggestion_id: int, session: Session = Depends(get_session)):
    """Delete a suggestion permanently"""
    suggestion = session.get(Suggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    session.delete(suggestion)
    session.commit()
    
    return {"ok": True, "id": suggestion_id}

@router.delete("/clear/{category}")
def clear_suggestions(category: str, session: Session = Depends(get_session)):
    """Clear all suggestions in a category (for refresh)"""
    suggestions = session.exec(
        select(Suggestion).where(Suggestion.category == category)
    ).all()
    
    for s in suggestions:
        session.delete(s)
    
    session.commit()
    
    return {"ok": True, "cleared": len(suggestions)}
