"""Natural language date and time parsing utilities"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from dateutil import parser as date_parser
import pytz

class DateTimeParser:
    """Parse natural language dates and times"""
    
    def __init__(self, timezone: str = "America/New_York"):
        self.timezone = timezone
        self.tz = pytz.timezone(timezone)
    
    def parse_date(self, text: str, reference_date: datetime = None) -> Optional[str]:
        """
        Parse natural language date to YYYY-MM-DD format
        
        Args:
            text: Natural language date text
            reference_date: Reference date for relative parsing
            
        Returns:
            Date string in YYYY-MM-DD format or None
        """
        if not text:
            return None
            
        text = text.lower().strip()
        
        if reference_date is None:
            reference_date = datetime.now(self.tz)
        
        # Handle relative dates
        if text in ["today"]:
            return reference_date.strftime("%Y-%m-%d")
        elif text in ["tomorrow"]:
            return (reference_date + timedelta(days=1)).strftime("%Y-%m-%d")
        elif text in ["yesterday"]:
            return (reference_date - timedelta(days=1)).strftime("%Y-%m-%d")
        elif "next week" in text:
            return (reference_date + timedelta(weeks=1)).strftime("%Y-%m-%d")
        
        # Handle day names (this week or next week)
        days = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6, "mon": 0, "tue": 1, 
            "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6
        }
        
        for day_name, day_num in days.items():
            if day_name in text:
                days_ahead = day_num - reference_date.weekday()
                if days_ahead <= 0 or "next" in text:
                    days_ahead += 7
                target_date = reference_date + timedelta(days=days_ahead)
                return target_date.strftime("%Y-%m-%d")
        
        # Try to parse with dateutil
        try:
            # Handle common formats
            if re.match(r'\d{1,2}/\d{1,2}(/\d{4})?', text):
                parsed_date = date_parser.parse(text)
                if parsed_date.year == 1900:  # Default year from dateutil
                    parsed_date = parsed_date.replace(year=reference_date.year)
                    if parsed_date < reference_date:
                        parsed_date = parsed_date.replace(year=reference_date.year + 1)
                return parsed_date.strftime("%Y-%m-%d")
            else:
                parsed_date = date_parser.parse(text, fuzzy=True)
                return parsed_date.strftime("%Y-%m-%d")
        except:
            pass
        
        return None
    
    def parse_time(self, text: str) -> Optional[str]:
        """
        Parse natural language time to HH:MM format
        
        Args:
            text: Natural language time text
            
        Returns:
            Time string in HH:MM format or None
        """
        if not text:
            return None
            
        text = text.lower().strip()
        
        # Handle relative times
        time_mappings = {
            "morning": "09:00",
            "afternoon": "14:00", 
            "evening": "18:00",
            "noon": "12:00",
            "midnight": "00:00"
        }
        
        for keyword, time_value in time_mappings.items():
            if keyword in text:
                return time_value
        
        # Handle specific times with regex patterns
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)?',  # 3:30pm, 15:30
            r'(\d{1,2})\s*(am|pm)',          # 3pm, 3am
            r'(\d{1,2}):(\d{2})',            # 24-hour format
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                
                if len(groups) == 3 and groups[2]:  # HH:MM am/pm
                    hour, minute, period = groups
                    hour = int(hour)
                    minute = int(minute)
                    
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                    
                    return f"{hour:02d}:{minute:02d}"
                
                elif len(groups) == 2 and groups[1] in ['am', 'pm']:  # H am/pm
                    hour = int(groups[0])
                    period = groups[1]
                    
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                    
                    return f"{hour:02d}:00"
                
                elif len(groups) == 2 and groups[1].isdigit():  # HH:MM 24-hour
                    hour, minute = int(groups[0]), int(groups[1])
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return f"{hour:02d}:{minute:02d}"
        
        return None
    
    def extract_datetime_info(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract date and time information from natural language text
        
        Args:
            text: Natural language text containing date/time info
            
        Returns:
            Dictionary with 'date', 'time', and 'original_text'
        """
        result = {
            'date': None,
            'time': None,
            'original_text': text
        }
        
        # Look for dates in the text
        words = text.split()
        for i in range(len(words)):
            # Try single words and combinations
            for length in [1, 2, 3]:
                if i + length <= len(words):
                    candidate = ' '.join(words[i:i+length])
                    parsed_date = self.parse_date(candidate)
                    if parsed_date:
                        result['date'] = parsed_date
                        break
            if result['date']:
                break
        
        # Look for times in the text
        for i in range(len(words)):
            for length in [1, 2, 3]:
                if i + length <= len(words):
                    candidate = ' '.join(words[i:i+length])
                    parsed_time = self.parse_time(candidate)
                    if parsed_time:
                        result['time'] = parsed_time
                        break
            if result['time']:
                break
        
        return result