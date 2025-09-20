"""Main Universal Appointment Agent"""

import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pytz

from ..config.business_config import BusinessConfig
from ..config.ai_config import mistral_config
from ..config.prompts.base_prompts import get_base_system_prompt
from ..config.prompts.dentist import get_dental_system_prompt
from ..integrations.google_calendar import GoogleCalendarIntegration
from ..integrations.google_sheets import GoogleSheetsIntegration
from ..utils.datetime_parser import DateTimeParser
from .conversation_manager import ConversationManager, ConversationContext

class UniversalAppointmentAgent:
    """Main appointment booking agent with natural conversation"""
    
    def __init__(self, config: BusinessConfig):
        self.config = config
        self.conversation_manager = ConversationManager()
        self.datetime_parser = DateTimeParser(config.timezone)
        
        # Initialize integrations
        self.calendar = GoogleCalendarIntegration(
            calendar_id=config.calendar_id
        )
        
        self.sheets = None
        if config.sheet_id:
            try:
                self.sheets = GoogleSheetsIntegration(sheet_id=config.sheet_id)
                self.sheets.setup_customer_sheet(config.business_type)
            except Exception as e:
                print(f"⚠️ Sheets integration failed: {e}")
                self.sheets = None
        
        print(f"✅ Agent initialized for {config.business_name} ({config.business_type})")
    
    async def process_message(self, message: str, session_id: str = "default") -> str:
        """
        Process user message and return agent response
        
        Args:
            message: User's message
            session_id: Session identifier
            
        Returns:
            Agent's response
        """
        try:
            # Get or create conversation context
            context = self.conversation_manager.get_or_create_context(
                session_id, 
                self.config.business_type,
                self.config.required_fields
            )
            
            # Add user message to context
            context.add_message('user', message)
            
            # Classify intent and update context
            intent = self.conversation_manager.classify_intent(message)
            context.current_intent = intent
            
            # Extract customer information
            extracted_info = self.conversation_manager.extract_customer_info(message, context)
            for field, value in extracted_info.items():
                context.update_customer_info(field, value)
            
            # Extract datetime information
            datetime_info = self.datetime_parser.extract_datetime_info(message)
            if datetime_info['date']:
                context.requested_date = datetime_info['date']
            if datetime_info['time']:
                context.requested_time = datetime_info['time']
            
            # Process based on conversation stage and intent
            response = await self._generate_contextual_response(context, message)
            
            # Handle any actions (booking, availability checking)
            response = await self._handle_actions(context, response)
            
            # Add response to context
            context.add_message('assistant', response)
            
            return response
            
        except Exception as e:
            error_response = "I apologize, but I encountered an error. Could you please try again?"
            print(f"Agent error: {e}")
            return error_response
    
    async def _generate_contextual_response(self, context: ConversationContext, message: str) -> str:
        """Generate contextual response using Mistral"""
        
        if not mistral_config:
            return "I'm sorry, but the AI service is currently unavailable. Please try again later."
        
        try:
            # Get business-specific system prompt
            if context.business_type == 'dentist':
                system_prompt = get_dental_system_prompt(self.config)
            else:
                system_prompt = get_base_system_prompt(self.config)
            
            # Build contextual user message
            context_info = self.conversation_manager.get_context_for_prompt(context.session_id)
            
            user_prompt = f"""
{context_info}

Current user message: {message}

Instructions:
- Respond naturally and professionally
- If booking appointment, check availability first
- Collect required information: {', '.join(self.config.required_fields)}
- Confirm details before final booking
- Be helpful and conversational
"""
            
            # Create messages for Mistral
            messages = [
                mistral_config.create_system_message(system_prompt),
                mistral_config.create_user_message(user_prompt)
            ]
            
            # Get response from Mistral
            response = mistral_config.create_chat_completion(messages)
            response_text = response.choices[0].message.content
            
            return response_text
            
        except Exception as e:
            print(f"AI generation error: {e}")
            return "I apologize for the technical difficulty. How can I help you with your appointment?"
    
    async def _handle_actions(self, context: ConversationContext, response: str) -> str:
        """Handle actions based on conversation context and response"""
        
        # Check if we need to get availability
        if (context.requested_date and not context.available_slots and 
            context.current_intent == 'book_appointment'):
            
            await self._check_and_update_availability(context)
        
        # Check if we should book appointment
        if self._should_book_appointment(context, response):
            booking_result = await self._book_appointment(context)
            
            if booking_result['success']:
                context.appointment_booked = True
                context.event_id = booking_result['event_id']
                context.booking_confirmed = True
                context.conversation_stage = 'completed'
                
                return f"{response}\n\n{booking_result['message']}"
            else:
                return f"I apologize, there was an issue booking your appointment: {booking_result.get('error', 'Unknown error')}. Let me help you find another time."
        
        # Update conversation stage based on context
        self._update_conversation_stage(context)
        
        return response
    
    async def _check_and_update_availability(self, context: ConversationContext):
        """Check availability and update context"""
        try:
            working_hours = self.config.get_working_hours_for_date(
                datetime.strptime(context.requested_date, '%Y-%m-%d')
            )
            
            if working_hours:
                slots = self.calendar.get_available_slots(
                    context.requested_date,
                    working_hours,
                    self.config.appointment_duration,
                    self.config.timezone
                )
                context.available_slots = slots
                
                # Auto-select slot if specific time was requested
                if context.requested_time and slots:
                    for slot in slots:
                        if slot.startswith(context.requested_time):
                            context.selected_slot = slot
                            break
        except Exception as e:
            print(f"Availability check error: {e}")
    
    def _should_book_appointment(self, context: ConversationContext, response: str) -> bool:
        """Determine if appointment should be booked"""
        
        # Check all conditions for booking
        has_slot = context.selected_slot is not None
        has_all_info = context.is_info_complete()
        not_already_booked = not context.appointment_booked
        
        # Look for confirmation in recent messages or response
        recent_messages = [msg['content'].lower() for msg in context.messages[-2:] if msg['role'] == 'user']
        confirmation_words = ['yes', 'correct', 'confirm', 'book it', 'sounds good', 'perfect', 'right']
        has_confirmation = any(word in ' '.join(recent_messages + [response.lower()]) 
                              for word in confirmation_words)
        
        # Must be in appropriate conversation stage
        appropriate_stage = context.conversation_stage in ['info_collection', 'confirmation']
        
        return (has_slot and has_all_info and not_already_booked and 
                has_confirmation and appropriate_stage)
    
    async def _book_appointment(self, context: ConversationContext) -> Dict:
        """Book the appointment"""
        try:
            if not context.selected_slot or not context.requested_date:
                return {
                    'success': False,
                    'error': 'Missing appointment details'
                }
            
            # Book in calendar
            booking_result = self.calendar.book_appointment(
                date=context.requested_date,
                time_slot=context.selected_slot,
                customer_info=context.customer_info,
                timezone=self.config.timezone,
                summary=f"{self.config.business_name} - {context.customer_info.get('name', 'Customer')}"
            )
            
            if booking_result['success']:
                # Store customer data in sheets
                if self.sheets:
                    self.sheets.store_customer_data(
                        context.customer_info,
                        {
                            'date': context.requested_date,
                            'time': context.selected_slot
                        }
                    )
                
                return {
                    'success': True,
                    'event_id': booking_result['event_id'],
                    'message': f"Your appointment is confirmed for {context.requested_date} from {context.selected_slot}. Thank you for choosing {self.config.business_name}!"
                }
            else:
                return booking_result
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_conversation_stage(self, context: ConversationContext):
        """Update conversation stage based on context"""
        
        if context.appointment_booked:
            context.conversation_stage = 'completed'
        elif context.selected_slot and context.is_info_complete():
            context.conversation_stage = 'confirmation'
        elif context.requested_date or context.available_slots:
            context.conversation_stage = 'scheduling'
        elif context.current_intent == 'book_appointment':
            context.conversation_stage = 'info_collection'
        elif context.messages:
            context.conversation_stage = 'active'
        else:
            context.conversation_stage = 'greeting'
    
    def get_greeting(self) -> str:
        """Get business-appropriate greeting"""
        return self.config.get_greeting()
    
    def reset_conversation(self, session_id: str = "default"):
        """Reset conversation context"""
        self.conversation_manager.reset_context(session_id)
    
    def get_conversation_status(self, session_id: str = "default") -> Dict:
        """Get current conversation status"""
        if session_id not in self.conversation_manager.contexts:
            return {'status': 'new', 'context': None}
        
        context = self.conversation_manager.contexts[session_id]
        return {
            'status': context.conversation_stage,
            'context': context.get_context_summary(),
            'appointment_booked': context.appointment_booked,
            'required_fields': context.required_fields,
            'collected_fields': context.collected_fields,
            'missing_fields': context.get_missing_fields()
        }