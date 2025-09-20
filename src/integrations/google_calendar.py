"""Google Calendar integration for appointment booking"""

import os
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from dotenv import load_dotenv

load_dotenv()

# Scopes for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarIntegration:
    """Google Calendar integration for appointment management"""
    
    def __init__(self, calendar_id: str = "primary", credentials_file: str = None):
        self.calendar_id = calendar_id
        self.credentials_file = credentials_file or os.getenv('GOOGLE_CREDENTIALS_FILE')
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        token_file = 'token.pickle'
        
        # Load existing token
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_file or not os.path.exists(self.credentials_file):
                    raise ValueError(
                        "Google credentials file not found. "
                        "Please download credentials.json from Google Cloud Console "
                        "and set GOOGLE_CREDENTIALS_FILE in .env"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=8080)
            
            # Save credentials for next run
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
        print("✅ Google Calendar authenticated successfully")
    
    def get_available_slots(self, date: str, working_hours: str, duration_minutes: int, timezone: str = "America/New_York") -> List[str]:
        """
        Get available appointment slots for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
            working_hours: "HH:MM-HH:MM" format
            duration_minutes: Appointment duration
            timezone: Timezone string
            
        Returns:
            List of available slots in "HH:MM-HH:MM" format
        """
        try:
            if not working_hours:
                return []
            
            # Parse working hours
            start_hour, end_hour = working_hours.split('-')
            tz = pytz.timezone(timezone)
            
            # Create start and end datetime objects
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            start_time = tz.localize(datetime.combine(
                date_obj.date(),
                datetime.strptime(start_hour, '%H:%M').time()
            ))
            end_time = tz.localize(datetime.combine(
                date_obj.date(), 
                datetime.strptime(end_hour, '%H:%M').time()
            ))
            
            # Get existing events for the day
            events = self._get_events_for_date(date, timezone)
            
            # Generate available slots
            available_slots = []
            current_time = start_time
            
            while current_time + timedelta(minutes=duration_minutes) <= end_time:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Check if slot conflicts with existing events
                is_available = True
                for event in events:
                    event_start = event['start']
                    event_end = event['end']
                    
                    # Check for overlap
                    if (current_time < event_end and slot_end > event_start):
                        is_available = False
                        break
                
                if is_available:
                    slot_str = f"{current_time.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}"
                    available_slots.append(slot_str)
                
                current_time += timedelta(minutes=duration_minutes)
            
            return available_slots
            
        except Exception as e:
            print(f"Error getting available slots: {e}")
            return []
    
    def _get_events_for_date(self, date: str, timezone: str) -> List[Dict]:
        """Get all events for a specific date"""
        try:
            tz = pytz.timezone(timezone)
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            
            # Start and end of the day
            day_start = tz.localize(datetime.combine(date_obj.date(), datetime.min.time()))
            day_end = tz.localize(datetime.combine(date_obj.date(), datetime.max.time()))
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=day_start.isoformat(),
                timeMax=day_end.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Convert events to our format
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Convert to datetime objects
                if 'T' in start:  # dateTime format
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    
                    # Convert to local timezone
                    start_dt = start_dt.astimezone(tz)
                    end_dt = end_dt.astimezone(tz)
                    
                    formatted_events.append({
                        'start': start_dt,
                        'end': end_dt,
                        'summary': event.get('summary', 'Busy')
                    })
            
            return formatted_events
            
        except HttpError as e:
            print(f"Error fetching calendar events: {e}")
            return []
    
    def book_appointment(self, date: str, time_slot: str, customer_info: Dict, 
                        timezone: str = "America/New_York", 
                        summary: str = None) -> Dict:
        """
        Book an appointment in Google Calendar
        
        Args:
            date: Date in YYYY-MM-DD format
            time_slot: Time slot in "HH:MM-HH:MM" format
            customer_info: Dictionary with customer details
            timezone: Timezone string
            summary: Event summary (optional)
            
        Returns:
            Dictionary with booking result
        """
        try:
            # Parse time slot
            start_time_str, end_time_str = time_slot.split('-')
            
            tz = pytz.timezone(timezone)
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            
            # Create datetime objects
            start_dt = tz.localize(datetime.combine(
                date_obj.date(),
                datetime.strptime(start_time_str, '%H:%M').time()
            ))
            end_dt = tz.localize(datetime.combine(
                date_obj.date(),
                datetime.strptime(end_time_str, '%H:%M').time()
            ))
            
            # Create event summary
            customer_name = customer_info.get('name', 'Unknown')
            if not summary:
                summary = f"Appointment - {customer_name}"
            
            # Create event description
            description_parts = []
            for key, value in customer_info.items():
                if value and key != 'name':
                    description_parts.append(f"{key.replace('_', ' ').title()}: {value}")
            
            description = "\n".join(description_parts)
            
            # Create event
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_dt.isoformat(), 
                    'timeZone': timezone,
                },
                'attendees': [
                    {'email': customer_info.get('email', '')},
                ] if customer_info.get('email') else [],
            }
            
            # Insert event into calendar
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            return {
                'success': True,
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink', ''),
                'message': f"Appointment booked successfully for {customer_name}",
                'details': {
                    'date': date,
                    'time': time_slot,
                    'customer': customer_name,
                    'summary': summary
                }
            }
            
        except HttpError as e:
            return {
                'success': False,
                'error': f"Google Calendar error: {e}",
                'message': "Failed to book appointment"
            }
        except Exception as e:
            return {
                'success': False, 
                'error': f"Booking error: {e}",
                'message': "Failed to book appointment"
            }
    
    def cancel_appointment(self, event_id: str) -> Dict:
        """Cancel an appointment by event ID"""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            return {
                'success': True,
                'message': "Appointment cancelled successfully"
            }
            
        except HttpError as e:
            return {
                'success': False,
                'error': f"Failed to cancel appointment: {e}"
            }
    
    def get_appointment_details(self, event_id: str) -> Dict:
        """Get appointment details by event ID"""
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            return {
                'success': True,
                'event': {
                    'id': event['id'],
                    'summary': event.get('summary', ''),
                    'description': event.get('description', ''),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'link': event.get('htmlLink', '')
                }
            }
            
        except HttpError as e:
            return {
                'success': False,
                'error': f"Failed to get appointment: {e}"
            }