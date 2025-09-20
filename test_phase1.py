#!/usr/bin/env python3
"""Test Phase 1: Business Configuration with Mistral"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.business_config import create_dental_config, create_salon_config, create_doctor_config
from src.config.prompts.dentist import get_dental_system_prompt
from src.config.prompts.base_prompts import get_base_system_prompt

def test_mistral_connection():
    """Test Mistral AI connection"""
    print("Testing Mistral AI Connection...")
    
    try:
        from src.config.ai_config import mistral_config
        
        # Test simple completion
        messages = [
            mistral_config.create_system_message("You are a helpful assistant."),
            mistral_config.create_user_message("Say 'Hello, I am working!' in exactly those words.")
        ]
        
        response = mistral_config.create_chat_completion(messages)
        response_text = response.choices[0].message.content
        
        print(f"✅ Mistral AI connected successfully")
        print(f"   Model: {mistral_config.model}")
        print(f"   Response: {response_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mistral AI connection failed: {e}")
        print("   Make sure MISTRAL_API_KEY is set in .env file")
        return False

def test_business_configs():
    """Test business configuration creation"""
    print("\nTesting Business Configurations...")
    
    # Test dental config
    dental = create_dental_config("Test Dental Clinic", "Emily")
    print(f"✅ Dental Config: {dental.business_name} with {len(dental.services)} services")
    print(f"   Required fields: {dental.required_fields}")
    print(f"   Working hours: {len([h for h in dental.working_hours.values() if h])} days")
    
    # Test salon config  
    salon = create_salon_config("Test Beauty Salon", "Sarah")
    print(f"✅ Salon Config: {salon.business_name} with {len(salon.services)} services")
    print(f"   Required fields: {salon.required_fields}")
    print(f"   Appointment duration: {salon.appointment_duration} minutes")
    
    # Test doctor config
    doctor = create_doctor_config("Test Medical Clinic", "Alex") 
    print(f"✅ Doctor Config: {doctor.business_name} with {len(doctor.services)} services")
    print(f"   Required fields: {doctor.required_fields}")
    print(f"   Appointment duration: {doctor.appointment_duration} minutes")
    
    print("\n" + "="*50)

def test_prompts():
    """Test prompt generation"""
    print("Testing Prompt Generation...")
    
    dental_config = create_dental_config()
    
    # Test base prompt
    base_prompt = get_base_system_prompt(dental_config)
    print(f"✅ Base prompt generated: {len(base_prompt)} characters")
    
    # Test dental-specific prompt
    dental_prompt = get_dental_system_prompt(dental_config)  
    print(f"✅ Dental prompt generated: {len(dental_prompt)} characters")
    print(f"   Contains business name: {'Test' in dental_prompt or dental_config.business_name in dental_prompt}")
    print(f"   Contains assistant name: {dental_config.assistant_name in dental_prompt}")
    
    print("\n" + "="*50)

def main():
    print("Phase 1 Testing: Business Configuration & Prompts (Mistral Edition)")
    print("="*70)
    
    try:
        # Test Mistral connection first
        if not test_mistral_connection():
            print("\n⚠️  Mistral AI not configured, but continuing with other tests...")
        
        test_business_configs()
        test_prompts()
        
        print("🎉 Phase 1 Complete (Mistral Ready)!")
        print("\nNext: Run Phase 2 to add Google integrations")
        
    except Exception as e:
        print(f"❌ Phase 1 Failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)