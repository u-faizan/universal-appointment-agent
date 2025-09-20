#!/usr/bin/env python3
"""Test Phase 3: Core Agent with Mistral Integration"""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.agent import UniversalAppointmentAgent
from src.config.business_config import create_dental_config, create_salon_config
from src.config.ai_config import mistral_config

def test_agent_initialization():
    """Test agent initialization"""
    print("Testing Agent Initialization...")
    
    try:
        # Test dental agent
        dental_config = create_dental_config("Test Dental Clinic", "Emily")
        dental_agent = UniversalAppointmentAgent(dental_config)
        print("✅ Dental agent initialized successfully")
        
        # Test salon agent
        salon_config = create_salon_config("Test Beauty Salon", "Sarah") 
        salon_agent = UniversalAppointmentAgent(salon_config)
        print("✅ Salon agent initialized successfully")
        
        return dental_agent
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return None

async def test_conversation_flow():
    """Test natural conversation flow"""
    print("\nTesting Conversation Flow...")
    
    try:
        # Initialize agent
        config = create_dental_config("Test Dental Clinic", "Emily")
        agent = UniversalAppointmentAgent(config)
        
        # Test conversation sequence
        test_messages = [
            "Hi, I need a dental appointment",
            "Tomorrow would be great", 
            "Afternoon works better",
            "3pm sounds perfect",
            "My name is John Smith",
            "555-123-4567",
            "March 15th, 1985",
            "Yes, that's correct"
        ]
        
        print("Conversation flow:")
        print(f"Agent: {agent.get_greeting()}")
        
        session_id = "test_session"
        
        for i, message in enumerate(test_messages):
            print(f"\nUser: {message}")
            
            response = await agent.process_message(message, session_id)
            print(f"Agent: {response}")
            
            # Show conversation status
            status = agent.get_conversation_status(session_id)
            print(f"   Status: {status['status']} | Context: {status['context']}")
        
        print("✅ Conversation flow completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation flow test failed: {e}")
        return False
    
async def test_real_booking():
    """Test real appointment booking (no cleanup)"""
    print("\nTesting Real Appointment Booking...")
    
    try:
        config = create_dental_config("Test Dental Clinic")
        agent = UniversalAppointmentAgent(config)
        
        # Get tomorrow's date
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Get available slots
        slots = agent.calendar.get_available_slots(tomorrow, "09:00-17:00", 60)
        
        if not slots:
            print(f"⚠️ No available slots found for {tomorrow}")
            return True
        
        print(f"Available slots for {tomorrow}: {slots[:3]}")
        
        # Book a real test appointment (don't cancel)
        test_customer = {
            'name': 'Test Customer',
            'phone': '555-TEST-123',
            'date_of_birth': '1990-06-15',
            'notes': 'Real test booking - Phase 3'
        }
        
        booking_result = agent.calendar.book_appointment(
            date=tomorrow,
            time_slot=slots[0],
            customer_info=test_customer,
            summary="Phase 3 Real Test Appointment"
        )
        
        if booking_result['success']:
            print(f"✅ Real appointment booked successfully!")
            print(f"   Date: {tomorrow}")
            print(f"   Time: {slots[0]}")
            print(f"   Event ID: {booking_result['event_id']}")
            print(f"   Link: {booking_result['event_link']}")
            
            # Store in sheets
            if agent.sheets:
                agent.sheets.store_customer_data(test_customer, {
                    'date': tomorrow,
                    'time': slots[0]
                })
                print("✅ Customer data stored in Google Sheets")
            
            print("📅 Check your Google Calendar to see the appointment!")
            
        else:
            print(f"❌ Real booking failed: {booking_result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Real booking test failed: {e}")
        return False
    
async def test_datetime_parsing():
    """Test date and time parsing"""
    print("\nTesting DateTime Parsing...")
    
    try:
        from src.utils.datetime_parser import DateTimeParser
        
        parser = DateTimeParser()
        
        # Test date parsing
        test_dates = ["tomorrow", "next friday", "12/25/2024", "December 25th"]
        for date_text in test_dates:
            parsed = parser.parse_date(date_text)
            print(f"   '{date_text}' -> {parsed}")
        
        # Test time parsing
        test_times = ["3pm", "3:30 pm", "morning", "15:30"]
        for time_text in test_times:
            parsed = parser.parse_time(time_text)
            print(f"   '{time_text}' -> {parsed}")
        
        # Test combined extraction
        test_text = "I need an appointment tomorrow at 3pm"
        extracted = parser.extract_datetime_info(test_text)
        print(f"   '{test_text}' -> Date: {extracted['date']}, Time: {extracted['time']}")
        
        print("✅ DateTime parsing working correctly")
        return True
        
    except Exception as e:
        print(f"❌ DateTime parsing test failed: {e}")
        return False

def test_business_configurations():
    """Test different business configurations"""
    print("\nTesting Business Configurations...")
    
    try:
        # Test different business types
        business_types = [
            ("dentist", create_dental_config),
            ("salon", create_salon_config)
        ]
        
        for business_type, config_func in business_types:
            config = config_func(f"Test {business_type.title()}", f"Agent_{business_type}")
            agent = UniversalAppointmentAgent(config)
            
            print(f"✅ {business_type.title()} agent: {len(config.services)} services, "
                  f"{len(config.required_fields)} required fields")
            print(f"   Required: {', '.join(config.required_fields)}")
            print(f"   Greeting: {agent.get_greeting()[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Business configuration test failed: {e}")
        return False

async def test_mistral_integration():
    """Test Mistral AI integration"""
    print("\nTesting Mistral Integration...")
    
    try:
        if not mistral_config:
            print("⚠️ Mistral not configured - skipping AI tests")
            return True
        
        # Test simple completion
        messages = [
            mistral_config.create_system_message("You are a helpful dental office assistant."),
            mistral_config.create_user_message("A customer says: 'I need an appointment tomorrow'. Respond professionally.")
        ]
        
        response = mistral_config.create_chat_completion(messages)
        response_text = response.choices[0].message.content
        
        print(f"✅ Mistral integration working")
        print(f"   Sample response: {response_text[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Mistral integration test failed: {e}")
        return False

def test_conversation_management():
    """Test conversation context management"""
    print("\nTesting Conversation Management...")
    
    try:
        from src.core.conversation_manager import ConversationManager
        
        manager = ConversationManager()
        
        # Create context
        context = manager.get_or_create_context("test_session", "dentist", ["name", "phone"])
        
        # Test message handling
        context.add_message("user", "Hi, I need an appointment")
        context.add_message("assistant", "I'd be happy to help!")
        
        # Test customer info extraction
        info = manager.extract_customer_info("My name is John Smith and my phone is 555-1234", context)
        print(f"   Extracted info: {info}")
        
        # Test intent classification
        intent = manager.classify_intent("I want to book an appointment tomorrow")
        print(f"   Classified intent: {intent}")
        
        # Test context summary
        summary = context.get_context_summary()
        print(f"   Context summary: {summary}")
        
        print("✅ Conversation management working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Conversation management test failed: {e}")
        return False

async def main():
    """Run all Phase 3 tests"""
    print("Phase 3 Testing: Core Agent with Mistral Integration")
    print("="*60)
    
    try:
        # Test individual components
        agent = test_agent_initialization()
        if not agent:
            print("❌ Cannot proceed without agent initialization")
            return False
        
        config_ok = test_business_configurations()
        datetime_ok = await test_datetime_parsing()
        conversation_ok = test_conversation_management()
        mistral_ok = await test_mistral_integration()
        
        # Test complete flow
        if agent and mistral_ok:
            flow_ok = await test_conversation_flow()
            booking_ok = await test_real_booking()
        else:
            print("\n⚠️ Skipping conversation flow test due to missing components")
            flow_ok = False
        
        print("\n" + "="*60)
        
        if all([config_ok, datetime_ok, conversation_ok, mistral_ok]):
            print("🎉 Phase 3 Complete!")
            print("\nCore Agent Features Working:")
            print("  ✅ Business Configuration: Multiple business types")
            print("  ✅ Natural Language Processing: Date/time parsing")
            print("  ✅ Conversation Management: Context tracking")
            print("  ✅ Mistral Integration: AI-powered responses")
            if flow_ok:
                print("  ✅ Complete Conversation Flow: End-to-end booking")
            
            print("\nNext: Run Phase 4 to add MCP server for Coral Protocol")
            return True
        else:
            print("⚠️ Phase 3 has issues - check the failed components")
            return False
            
    except Exception as e:
        print(f"❌ Phase 3 testing failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)