from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pytz
from datetime import datetime

@dataclass
class BusinessConfig:
    """Configuration for different business types"""
    business_type: str  # dentist, salon, doctor, spa, lawyer
    business_name: str
    assistant_name: str
    services: List[str]
    working_hours: Dict[str, str]  # {"monday": "08:00-17:00"}
    timezone: str = "America/New_York"
    appointment_duration: int = 60  # minutes
    buffer_time: int = 0  # minutes between appointments
    
    # Business-specific data collection
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    
    # Google integration
    calendar_id: str = "primary"
    sheet_id: Optional[str] = None
    
    def __post_init__(self):
        """Set business-specific defaults"""
        if not self.required_fields:
            self.required_fields = self._get_default_required_fields()
        if not self.optional_fields:
            self.optional_fields = self._get_default_optional_fields()
    
    def _get_default_required_fields(self) -> List[str]:
        """Get default required fields based on business type"""
        defaults = {
            "dentist": ["name", "phone", "date_of_birth"],
            "doctor": ["name", "phone", "date_of_birth", "reason_for_visit"],
            "salon": ["name", "phone", "preferred_service"],
            "spa": ["name", "phone", "preferred_service"],
            "lawyer": ["name", "phone", "case_type"],
            "generic": ["name", "phone"]
        }
        return defaults.get(self.business_type, defaults["generic"])
    
    def _get_default_optional_fields(self) -> List[str]:
        """Get default optional fields based on business type"""
        defaults = {
            "dentist": ["insurance_provider", "emergency_contact", "notes"],
            "doctor": ["insurance_provider", "emergency_contact", "medications", "allergies"],
            "salon": ["hair_type", "previous_services", "allergies", "notes"],
            "spa": ["health_conditions", "allergies", "preferences", "notes"],
            "lawyer": ["case_details", "urgency", "preferred_contact_method"],
            "generic": ["notes"]
        }
        return defaults.get(self.business_type, defaults["generic"])
    
    def get_working_hours_for_date(self, date: datetime) -> Optional[str]:
        """Get working hours for a specific date"""
        day_name = date.strftime("%A").lower()
        return self.working_hours.get(day_name, "")
    
    def is_business_day(self, date: datetime) -> bool:
        """Check if the business is open on a given date"""
        return bool(self.get_working_hours_for_date(date))
    
    def get_timezone_obj(self):
        """Get pytz timezone object"""
        return pytz.timezone(self.timezone)

# Predefined business configurations
def create_dental_config(
    business_name: str = "Dental Clinic",
    assistant_name: str = "Emily",
    calendar_id: str = "primary",
    sheet_id: Optional[str] = None
) -> BusinessConfig:
    return BusinessConfig(
        business_type="dentist",
        business_name=business_name,
        assistant_name=assistant_name,
        services=[
            "General Dentistry", "Preventive Care", "Cosmetic Dentistry", 
            "Dental Cleanings", "Fillings", "Root Canals", "Crowns"
        ],
        working_hours={
            "monday": "08:00-17:00",
            "tuesday": "08:00-17:00", 
            "wednesday": "08:00-17:00",
            "thursday": "08:00-17:00",
            "friday": "08:00-16:00",
            "saturday": "",
            "sunday": ""
        },
        appointment_duration=60,
        calendar_id=calendar_id,
        sheet_id=sheet_id
    )

def create_salon_config(
    business_name: str = "Beauty Salon",
    assistant_name: str = "Sarah", 
    calendar_id: str = "primary",
    sheet_id: Optional[str] = None
) -> BusinessConfig:
    return BusinessConfig(
        business_type="salon",
        business_name=business_name,
        assistant_name=assistant_name,
        services=[
            "Haircuts", "Hair Styling", "Hair Coloring", "Highlights",
            "Hair Treatments", "Blowouts", "Updos", "Hair Extensions"
        ],
        working_hours={
            "monday": "09:00-19:00",
            "tuesday": "09:00-19:00",
            "wednesday": "09:00-19:00", 
            "thursday": "09:00-19:00",
            "friday": "09:00-19:00",
            "saturday": "09:00-17:00",
            "sunday": "10:00-16:00"
        },
        appointment_duration=90,
        calendar_id=calendar_id,
        sheet_id=sheet_id
    )

def create_doctor_config(
    business_name: str = "Medical Clinic",
    assistant_name: str = "Alex",
    calendar_id: str = "primary", 
    sheet_id: Optional[str] = None
) -> BusinessConfig:
    return BusinessConfig(
        business_type="doctor",
        business_name=business_name,
        assistant_name=assistant_name,
        services=[
            "General Consultation", "Health Checkups", "Preventive Care",
            "Chronic Disease Management", "Vaccinations", "Health Screenings"
        ],
        working_hours={
            "monday": "08:00-18:00",
            "tuesday": "08:00-18:00",
            "wednesday": "08:00-18:00",
            "thursday": "08:00-18:00", 
            "friday": "08:00-17:00",
            "saturday": "09:00-13:00",
            "sunday": ""
        },
        appointment_duration=30,
        calendar_id=calendar_id,
        sheet_id=sheet_id
    )