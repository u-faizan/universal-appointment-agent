# Universal Appointment Agent - MCP Server

## Quick Start

### 1. Run the MCP Server
```bash
python mcp_server.py
```

### 2. Available MCP Tools

#### Configure Business
```json
{
  "tool": "configure_business",
  "arguments": {
    "business_type": "dentist",
    "business_name": "My Dental Clinic",
    "assistant_name": "Emily",
    "services": ["Cleanings", "Checkups", "Procedures"],
    "working_hours": {
      "monday": "09:00-17:00",
      "tuesday": "09:00-17:00",
      "wednesday": "09:00-17:00",
      "thursday": "09:00-17:00",
      "friday": "09:00-16:00",
      "saturday": "",
      "sunday": ""
    }
  }
}
```

#### Chat with Agent
```json
{
  "tool": "chat_with_agent",
  "arguments": {
    "message": "Hi, I need an appointment tomorrow",
    "session_id": "user123"
  }
}
```

#### Check Availability
```json
{
  "tool": "check_availability",
  "arguments": {
    "date": "2024-09-21"
  }
}
```

#### Direct Booking
```json
{
  "tool": "book_appointment_direct",
  "arguments": {
    "date": "2024-09-21",
    "time_slot": "14:00-15:00",
    "customer_info": {
      "name": "John Smith",
      "phone": "555-1234",
      "date_of_birth": "1990-01-01"
    }
  }
}
```

## Features

* **Universal Business Support**: Dentist, salon, doctor, spa, lawyer, generic
* **Natural Conversations**: AI-powered chat via Mistral
* **Real Calendar Integration**: Google Calendar booking
* **Customer Data Storage**: Google Sheets integration
* **Session Management**: Multiple concurrent conversations
* **Coral Protocol Ready**: Standard MCP interface

## Integration

This agent is designed for Coral Protocol. Once running, it can be discovered and used by other agents or applications in the Coral ecosystem.

## Phase 4 Instructions

### 1. **Copy all files** to your project:
- `src/mcp/tools_definitions.py`
- `src/mcp/server.py`
- `mcp_server.py` (root level)
- `test_phase4.py`
- `README_MCP.md`

### 2. **Make sure** you have empty `__init__.py` in `src/mcp/`:
```bash
touch src/mcp/__init__.py
```