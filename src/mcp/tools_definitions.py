"""MCP tool definitions for the Universal Appointment Agent"""

from mcp.types import Tool

# MCP Tools for Coral Protocol integration
APPOINTMENT_TOOLS = [
    Tool(
        name="configure_business",
        description="Configure the appointment agent for a specific business type and settings",
        inputSchema={
            "type": "object",
            "properties": {
                "business_type": {
                    "type": "string",
                    "enum": ["dentist", "salon", "doctor", "spa", "lawyer", "generic"],
                    "description": "Type of business for the appointment agent"
                },
                "business_name": {
                    "type": "string",
                    "description": "Name of the business"
                },
                "assistant_name": {
                    "type": "string",
                    "description": "Name of the AI assistant"
                },
                "services": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of services offered by the business"
                },
                "working_hours": {
                    "type": "object",
                    "properties": {
                        "monday": {"type": "string", "description": "Hours in HH:MM-HH:MM format or empty for closed"},
                        "tuesday": {"type": "string", "description": "Hours in HH:MM-HH:MM format or empty for closed"},
                        "wednesday": {"type": "string", "description": "Hours in HH:MM-HH:MM format or empty for closed"},
                        "thursday": {"type": "string", "description": "Hours in HH:MM-HH:MM format or empty for closed"},
                        "friday": {"type": "string", "description": "Hours in HH:MM-HH:MM format or empty for closed"},
                        "saturday": {"type": "string", "description": "Hours in HH:MM-HH:MM format or empty for closed"},
                        "sunday": {"type": "string", "description": "Hours in HH:MM-HH:MM format or empty for closed"}
                    },
                    "required": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                    "description": "Working hours for each day of the week"
                },
                "appointment_duration": {
                    "type": "integer",
                    "default": 60,
                    "description": "Default appointment duration in minutes"
                },
                "timezone": {
                    "type": "string",
                    "default": "America/New_York",
                    "description": "Business timezone"
                },
                "calendar_id": {
                    "type": "string",
                    "default": "primary",
                    "description": "Google Calendar ID"
                },
                "sheet_id": {
                    "type": "string",
                    "description": "Google Sheets ID for customer data storage (optional)"
                }
            },
            "required": ["business_type", "business_name", "assistant_name", "services", "working_hours"]
        }
    ),
    
    Tool(
        name="chat_with_agent",
        description="Have a natural conversation with the appointment agent for booking appointments",
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The user's message to the appointment agent"
                },
                "session_id": {
                    "type": "string",
                    "default": "default",
                    "description": "Session ID to maintain conversation context across messages"
                }
            },
            "required": ["message"]
        }
    ),
    
    Tool(
        name="check_availability",
        description="Check available appointment slots for a specific date",
        inputSchema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date to check availability (YYYY-MM-DD format)"
                },
                "duration": {
                    "type": "integer",
                    "default": 60,
                    "description": "Appointment duration in minutes"
                }
            },
            "required": ["date"]
        }
    ),
    
    Tool(
        name="book_appointment_direct",
        description="Directly book an appointment with confirmed details (bypass conversation)",
        inputSchema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Appointment date (YYYY-MM-DD format)"
                },
                "time_slot": {
                    "type": "string",
                    "description": "Time slot in HH:MM-HH:MM format"
                },
                "customer_info": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Customer's full name"},
                        "phone": {"type": "string", "description": "Customer's phone number"},
                        "email": {"type": "string", "description": "Customer's email (optional)"},
                        "date_of_birth": {"type": "string", "description": "Date of birth (for medical/dental)"},
                        "reason_for_visit": {"type": "string", "description": "Reason for appointment (for medical)"},
                        "preferred_service": {"type": "string", "description": "Preferred service (for salon/spa)"},
                        "notes": {"type": "string", "description": "Additional notes"}
                    },
                    "required": ["name", "phone"]
                },
                "summary": {
                    "type": "string",
                    "description": "Custom appointment summary (optional)"
                }
            },
            "required": ["date", "time_slot", "customer_info"]
        }
    ),
    
    Tool(
        name="get_agent_status",
        description="Get current agent configuration and status",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    
    Tool(
        name="get_conversation_status",
        description="Get the status of a specific conversation session",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "default": "default",
                    "description": "Session ID to check"
                }
            }
        }
    ),
    
    Tool(
        name="reset_conversation",
        description="Reset a conversation session (clear context and start fresh)",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "default": "default",
                    "description": "Session ID to reset"
                }
            }
        }
    ),
    
    Tool(
        name="cancel_appointment",
        description="Cancel an existing appointment by event ID",
        inputSchema={
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Google Calendar event ID of the appointment to cancel"
                }
            },
            "required": ["event_id"]
        }
    ),
    
    Tool(
        name="get_business_info",
        description="Get information about the currently configured business",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
]