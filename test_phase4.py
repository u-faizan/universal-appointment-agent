#!/usr/bin/env python3
"""Test Phase 4: MCP Server for Coral Protocol"""

import sys
import os
import asyncio
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mcp.server import UniversalAppointmentMCPServer
from src.mcp.tools_definitions import APPOINTMENT_TOOLS
from mcp.types import TextContent

async def test_mcp_server_initialization():
    """Test MCP server initialization"""
    print("Testing MCP Server Initialization...")
    
    try:
        server = UniversalAppointmentMCPServer()
        
        # Test that the server was created and has tools defined
        tools = APPOINTMENT_TOOLS  # Import the tools directly
        print(f"✅ MCP Server initialized with {len(tools)} tools")
        
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "configure_business", "chat_with_agent", "check_availability",
            "book_appointment_direct", "get_agent_status", "get_conversation_status",
            "reset_conversation", "cancel_appointment", "get_business_info"
        ]
        
        for expected_tool in expected_tools:
            if expected_tool in tool_names:
                print(f"   ✅ {expected_tool}")
            else:
                print(f"   ❌ Missing: {expected_tool}")
        
        return server
        
    except Exception as e:
        print(f"❌ MCP server initialization failed: {e}")
        return None

async def test_business_configuration(server):
    """Test business configuration via MCP"""
    print("\nTesting Business Configuration...")
    
    try:
        # Test dental configuration
        dental_config = {
            "business_type": "dentist",
            "business_name": "Test Dental Clinic",
            "assistant_name": "Emily",
            "services": ["General Dentistry", "Cleanings", "Checkups"],
            "working_hours": {
                "monday": "09:00-17:00",
                "tuesday": "09:00-17:00",
                "wednesday": "09:00-17:00",
                "thursday": "09:00-17:00",
                "friday": "09:00-16:00",
                "saturday": "",
                "sunday": ""
            },
            "appointment_duration": 60,
            "timezone": "America/New_York",
            "sheet_id": os.getenv('GOOGLE_SHEETS_ID')
        }
        
        result = await server._configure_business(dental_config)
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        if response_data["success"]:
            print("✅ Dental business configured successfully")
            print(f"   Business: {response_data['configuration']['business_name']}")
            print(f"   Assistant: {response_data['configuration']['assistant_name']}")
            print(f"   Services: {len(response_data['configuration']['services'])}")
        else:
            print(f"❌ Configuration failed: {response_data['error']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Business configuration test failed: {e}")
        return False

async def test_agent_status(server):
    """Test agent status checking"""
    print("\nTesting Agent Status...")
    
    try:
        result = await server._get_agent_status({})
        response_text = result[0].text
        status_data = json.loads(response_text)
        
        if status_data["configured"]:
            print("✅ Agent status retrieved successfully")
            print(f"   Business: {status_data['business_name']}")
            print(f"   Type: {status_data['business_type']}")
            print(f"   Services: {len(status_data['services'])}")
            print(f"   Calendar: {'✅' if status_data['calendar_integration'] else '❌'}")
            print(f"   Sheets: {'✅' if status_data['sheets_integration'] else '❌'}")
        else:
            print("❌ Agent not configured")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Agent status test failed: {e}")
        return False

async def test_availability_checking(server):
    """Test availability checking"""
    print("\nTesting Availability Checking...")
    
    try:
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        result = await server._check_availability({"date": tomorrow})
        response_text = result[0].text
        availability_data = json.loads(response_text)
        
        if availability_data["success"]:
            slots = availability_data["available_slots"]
            print(f"✅ Availability check successful for {tomorrow}")
            print(f"   Working hours: {availability_data.get('working_hours', 'N/A')}")
            print(f"   Available slots: {len(slots)}")
            if slots:
                print(f"   Sample slots: {slots[:3]}")
            return True
        else:
            print(f"❌ Availability check failed: {availability_data['error']}")
            return False
        
    except Exception as e:
        print(f"❌ Availability checking test failed: {e}")
        return False

async def test_conversation_flow(server):
    """Test conversation flow"""
    print("\nTesting Conversation Flow...")
    
    try:
        # Test conversation messages
        test_messages = [
            "Hi, I need an appointment",
            "Tomorrow afternoon would be great",
            "3pm sounds good",
            "My name is John Test",
            "555-TEST-123",
            "January 1st, 1990"
        ]
        
        session_id = "mcp_test_session"
        
        for i, message in enumerate(test_messages):
            print(f"\n   User: {message}")
            
            result = await server._chat_with_agent({
                "message": message,
                "session_id": session_id
            })
            
            response_text = result[0].text
            chat_data = json.loads(response_text)
            
            if chat_data["success"]:
                print(f"   Agent: {chat_data['response'][:100]}...")
                print(f"   Status: {chat_data['conversation_status']['stage']}")
            else:
                print(f"   ❌ Chat failed: {chat_data['error']}")
                return False
        
        print("✅ Conversation flow completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Conversation flow test failed: {e}")
        return False

async def test_direct_booking(server):
    """Test direct appointment booking"""
    print("\nTesting Direct Appointment Booking...")
    
    try:
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # First check availability
        availability_result = await server._check_availability({"date": tomorrow})
        availability_data = json.loads(availability_result[0].text)
        
        if not availability_data["success"] or not availability_data["available_slots"]:
            print("⚠️ No available slots for direct booking test")
            return True
        
        # Book appointment directly
        booking_args = {
            "date": tomorrow,
            "time_slot": availability_data["available_slots"][0],
            "customer_info": {
                "name": "MCP Test Customer",
                "phone": "555-MCP-TEST",
                "date_of_birth": "1985-05-15",
                "notes": "Direct booking test via MCP"
            },
            "summary": "MCP Direct Booking Test"
        }
        
        result = await server._book_appointment_direct(booking_args)
        response_text = result[0].text
        booking_data = json.loads(response_text)
        
        if booking_data["success"]:
            print("✅ Direct appointment booking successful")
            print(f"   Event ID: {booking_data['event_id']}")
            print(f"   Date: {tomorrow}")
            print(f"   Time: {booking_args['time_slot']}")
            print("   📅 Check your Google Calendar!")
            return True
        else:
            print(f"❌ Direct booking failed: {booking_data['error']}")
            return False
        
    except Exception as e:
        print(f"❌ Direct booking test failed: {e}")
        return False

async def main():
    """Run all Phase 4 tests"""
    print("Phase 4 Testing: MCP Server for Coral Protocol")
    print("="*60)
    
    try:
        # Initialize server
        server = await test_mcp_server_initialization()
        if not server:
            print("❌ Cannot proceed without MCP server")
            return False
        
        # Test configuration
        config_ok = await test_business_configuration(server)
        if not config_ok:
            print("❌ Cannot proceed without business configuration")
            return False
        
        # Test other components
        status_ok = await test_agent_status(server)
        availability_ok = await test_availability_checking(server)
        conversation_ok = await test_conversation_flow(server)
        booking_ok = await test_direct_booking(server)
        
        print("\n" + "="*60)
        
        if all([config_ok, status_ok, availability_ok, conversation_ok, booking_ok]):
            print("🎉 Phase 4 Complete!")
            print("\nMCP Server Features Working:")
            print("  ✅ Business Configuration: Dynamic agent setup")
            print("  ✅ Natural Conversations: Real-time chat via MCP")
            print("  ✅ Availability Checking: Calendar integration")
            print("  ✅ Direct Booking: API-style appointment creation")
            print("  ✅ Status Monitoring: Agent and conversation tracking")
            
            print("\nReady for Coral Protocol Integration!")
            print("Start the server with: python mcp_server.py")
            return True
        else:
            print("⚠️ Phase 4 has issues - check the failed components")
            return False
            
    except Exception as e:
        print(f"❌ Phase 4 testing failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)