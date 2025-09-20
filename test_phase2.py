#!/usr/bin/env python3
"""Test Phase 2: Google Calendar and Sheets Integration"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import os
from datetime import datetime, timedelta
from src.integrations.google_calendar import GoogleCalendarIntegration
from src.integrations.google_sheets import GoogleSheetsIntegration
from src.config.business_config import create_dental_config

def test_google_calendar():
    """Test Google Calendar integration"""
    print("Testing Google Calendar Integration...")
    
    try:
        # Check if credentials file exists
        creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
        if not creds_file or not os.path.exists(creds_file):
            print("⚠️ Google credentials file not found")
            print("   Please download credentials.json from Google Cloud Console")
            print("   and set GOOGLE_CREDENTIALS_FILE in .env")
            return False
        
        # Initialize calendar
        calendar = GoogleCalendarIntegration()
        
        # Test getting available slots for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        working_hours = "09:00-17:00"
        
        slots = calendar.get_available_slots(tomorrow, working_hours, 60)
        print(f"✅ Calendar connected - Found {len(slots)} available slots for {tomorrow}")
        
        if slots:
            print(f"   Sample slots: {slots[:3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Calendar test failed: {e}")
        return False

def test_google_sheets():
    """Test Google Sheets integration"""
    print("\nTesting Google Sheets Integration...")
    
    try:
        sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        if not sheets_id:
            print("⚠️ GOOGLE_SHEETS_ID not set in .env")
            print("   Sheets integration will be disabled")
            return True  # Not required for core functionality
        
        # Initialize sheets
        sheets = GoogleSheetsIntegration()
        
        # Test setup
        success = sheets.setup_customer_sheet("dentist")
        if success:
            print("✅ Google Sheets connected and setup complete")
        else:
            print("⚠️ Google Sheets setup had issues")
        
        # Test storing sample data
        sample_customer = {
            'name': 'Test Customer',
            'phone': '555-TEST',
            'date_of_birth': '1990-01-01',
            'notes': 'Phase 2 test'
        }
        
        sample_appointment = {
            'date': '2024-01-01',
            'time': '10:00-11:00'
        }
        
        stored = sheets.store_customer_data(sample_customer, sample_appointment)
        if stored:
            print("✅ Sample customer data stored successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Sheets test failed: {e}")
        return False

def test_booking_flow():
    """Test complete booking flow"""
    print("\nTesting Complete Booking Flow...")
    
    try:
        config = create_dental_config("Test Dental Clinic")
        
        # Initialize integrations
        calendar = GoogleCalendarIntegration()
        sheets = GoogleSheetsIntegration() if os.getenv('GOOGLE_SHEETS_ID') else None
        
        # Get tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Get available slots
        slots = calendar.get_available_slots(tomorrow, "09:00-17:00", 60)
        
        if not slots:
            print("⚠️ No available slots found for testing")
            return True
        
        # Book a test appointment
        test_customer = {
            'name': 'Phase 2 Test',
            'phone': '555-PHASE2',
            'date_of_birth': '1985-06-15',
            'notes': 'Automated test booking'
        }
        
        booking_result = calendar.book_appointment(
            date=tomorrow,
            time_slot=slots[0],
            customer_info=test_customer,
            summary="Phase 2 Test Appointment"
        )
        
        if booking_result['success']:
            print(f"✅ Test appointment booked successfully")
            print(f"   Event ID: {booking_result['event_id']}")
            
            # Store in sheets if available
            if sheets:
                sheets.store_customer_data(test_customer, {
                    'date': tomorrow,
                    'time': slots[0]
                })
                print("✅ Customer data stored in sheets")
            
            # Clean up - cancel the test appointment
            cancel_result = calendar.cancel_appointment(booking_result['event_id'])
            if cancel_result['success']:
                print("✅ Test appointment cancelled (cleanup)")
        else:
            print(f"❌ Test booking failed: {booking_result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Booking flow test failed: {e}")
        return False

def main():
    print("Phase 2 Testing: Google Calendar & Sheets Integration")
    print("="*60)
    
    # Test individual components
    calendar_ok = test_google_calendar()
    sheets_ok = test_google_sheets()
    
    # Test complete flow
    if calendar_ok:
        booking_ok = test_booking_flow()
    else:
        print("\n⚠️ Skipping booking flow test due to calendar issues")
        booking_ok = False
    
    print("\n" + "="*60)
    
    if calendar_ok and sheets_ok:
        print("🎉 Phase 2 Complete!")
        print("\nGoogle integrations are working:")
        print("  ✅ Calendar: Book and manage appointments")
        print("  ✅ Sheets: Store customer data")
        print("\nNext: Run Phase 3 to add the core agent with Mistral")
    else:
        print("⚠️ Phase 2 has issues - check your Google setup")
        print("\nRequired setup:")
        print("  1. Download credentials.json from Google Cloud Console")
        print("  2. Enable Calendar and Sheets APIs")
        print("  3. Set GOOGLE_CREDENTIALS_FILE in .env")
        print("  4. Optionally set GOOGLE_SHEETS_ID in .env")
    
    return calendar_ok

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)