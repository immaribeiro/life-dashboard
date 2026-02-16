from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import os
import json
from pathlib import Path

# Google Calendar imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

router = APIRouter(prefix="/calendar", tags=["calendar"])

# OAuth config - these should be set via environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://life.immas.org/api/calendar/oauth/callback")

SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_PATH = Path("/data/google_calendar_token.json")

class EventCreate(BaseModel):
    summary: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    all_day: bool = False

def get_credentials() -> Optional[Credentials]:
    """Load stored credentials if they exist and are valid."""
    if not TOKEN_PATH.exists():
        return None
    
    with open(TOKEN_PATH, 'r') as f:
        token_data = json.load(f)
    
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        save_credentials(creds)
    
    return creds if creds and creds.valid else None

def save_credentials(creds: Credentials):
    """Save credentials to file."""
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_PATH, 'w') as f:
        f.write(creds.to_json())

def get_calendar_service():
    """Get authenticated Google Calendar service."""
    creds = get_credentials()
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated with Google Calendar. Visit /api/calendar/auth to connect.")
    return build('calendar', 'v3', credentials=creds)

@router.get("/status")
def calendar_status():
    """Check if Google Calendar is connected."""
    creds = get_credentials()
    if creds and creds.valid:
        return {"connected": True, "message": "Google Calendar is connected"}
    return {"connected": False, "message": "Google Calendar not connected. Visit /api/calendar/auth to connect."}

@router.get("/auth")
def calendar_auth():
    """Start OAuth flow to connect Google Calendar."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth credentials not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return RedirectResponse(auth_url)

@router.get("/oauth/callback")
def calendar_oauth_callback(code: str, request: Request):
    """Handle OAuth callback from Google."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth credentials not configured")
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    
    flow.fetch_token(code=code)
    save_credentials(flow.credentials)
    
    return RedirectResponse("/settings?calendar=connected")

@router.get("/events")
def list_events(days: int = 7):
    """List upcoming calendar events."""
    try:
        service = get_calendar_service()
        now = datetime.utcnow().isoformat() + 'Z'
        end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=end,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return {
            "count": len(events),
            "events": [
                {
                    "id": e.get('id'),
                    "summary": e.get('summary', '(No title)'),
                    "start": e.get('start', {}).get('dateTime', e.get('start', {}).get('date')),
                    "end": e.get('end', {}).get('dateTime', e.get('end', {}).get('date')),
                    "description": e.get('description'),
                    "location": e.get('location')
                }
                for e in events
            ]
        }
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"Google Calendar API error: {str(e)}")

@router.post("/events")
def create_event(event: EventCreate):
    """Create a new calendar event."""
    try:
        service = get_calendar_service()
        
        if event.all_day:
            event_body = {
                'summary': event.summary,
                'description': event.description,
                'start': {'date': event.start_time.strftime('%Y-%m-%d')},
                'end': {'date': (event.end_time or event.start_time).strftime('%Y-%m-%d')}
            }
        else:
            end_time = event.end_time or (event.start_time + timedelta(hours=1))
            event_body = {
                'summary': event.summary,
                'description': event.description,
                'start': {'dateTime': event.start_time.isoformat(), 'timeZone': 'Europe/Lisbon'},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Europe/Lisbon'}
            }
        
        created = service.events().insert(calendarId='primary', body=event_body).execute()
        
        return {
            "ok": True,
            "event_id": created.get('id'),
            "link": created.get('htmlLink'),
            "summary": created.get('summary'),
            "start": created.get('start')
        }
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"Google Calendar API error: {str(e)}")

@router.delete("/events/{event_id}")
def delete_event(event_id: str):
    """Delete a calendar event."""
    try:
        service = get_calendar_service()
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return {"ok": True, "deleted": event_id}
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"Google Calendar API error: {str(e)}")
