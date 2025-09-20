"""Conversation context and state management"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class ConversationContext:
    """Tracks conversation state and customer information"""
    session_id: str
    business_type: str
    
    # Conversation tracking
    messages: List[Dict[str, str]] = field(default_factory=list)
    current_intent: Optional[str] = None
    conversation_stage: str = "greeting"  # greeting, scheduling, info_collection, confirmation, completed
    
    # Appointment details
    requested_date: Optional[str] = None
    requested_time: Optional[str] = None
    available_slots: List[str] = field(default_factory=list)
    selected_slot: Optional[str] = None
    
    # Customer information
    customer_info: Dict[str, str] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)
    collected_fields: List[str] = field(default_factory=list)
    
    # Booking status
    appointment_booked: bool = False
    event_id: Optional[str] = None
    booking_confirmed: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        self.last_updated = datetime.now()
    
    def update_customer_info(self, field: str, value: str):
        """Update customer information"""
        if value and value.strip():
            self.customer_info[field] = value.strip()
            if field not in self.collected_fields:
                self.collected_fields.append(field)
            self.last_updated = datetime.now()
    
    def get_missing_fields(self) -> List[str]:
        """Get list of required fields that haven't been collected"""
        return [field for field in self.required_fields 
                if field not in self.collected_fields or not self.customer_info.get(field)]
    
    def is_info_complete(self) -> bool:
        """Check if all required information has been collected"""
        return len(self.get_missing_fields()) == 0
    
    def get_context_summary(self) -> str:
        """Get a summary of the current conversation context"""
        summary_parts = []
        
        if self.current_intent:
            summary_parts.append(f"Intent: {self.current_intent}")
        
        if self.requested_date:
            summary_parts.append(f"Date: {self.requested_date}")
        
        if self.requested_time:
            summary_parts.append(f"Time: {self.requested_time}")
        
        if self.selected_slot:
            summary_parts.append(f"Selected: {self.selected_slot}")
        
        if self.customer_info:
            info_summary = ', '.join([f"{k}: {v}" for k, v in self.customer_info.items() if v])
            summary_parts.append(f"Customer: {info_summary}")
        
        summary_parts.append(f"Stage: {self.conversation_stage}")
        
        return " | ".join(summary_parts) if summary_parts else "New conversation"

class ConversationManager:
    """Manages multiple conversation contexts"""
    
    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
    
    def get_or_create_context(self, session_id: str, business_type: str, 
                            required_fields: List[str]) -> ConversationContext:
        """Get existing context or create new one"""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(
                session_id=session_id,
                business_type=business_type,
                required_fields=required_fields
            )
        
        return self.contexts[session_id]
    
    def update_context_stage(self, session_id: str, stage: str):
        """Update conversation stage"""
        if session_id in self.contexts:
            self.contexts[session_id].conversation_stage = stage
            self.contexts[session_id].last_updated = datetime.now()
    
    def classify_intent(self, message: str) -> str:
        """Classify user intent from message"""
        message_lower = message.lower()
        
        # Appointment booking intents
        if any(word in message_lower for word in ['appointment', 'book', 'schedule', 'reserve']):
            return 'book_appointment'
        
        # Modification intents
        if any(word in message_lower for word in ['cancel', 'reschedule', 'change', 'modify']):
            return 'modify_appointment'
        
        # Information requests
        if any(word in message_lower for word in ['hours', 'open', 'closed', 'when', 'time']):
            return 'hours_inquiry'
        
        if any(word in message_lower for word in ['services', 'what do you', 'offer', 'treatments']):
            return 'services_inquiry'
        
        if any(word in message_lower for word in ['price', 'cost', 'how much', 'payment']):
            return 'pricing_inquiry'
        
        # Confirmation responses
        if any(word in message_lower for word in ['yes', 'correct', 'right', 'confirm', 'sounds good', 'perfect']):
            return 'confirmation'
        
        if any(word in message_lower for word in ['no', 'not right', 'wrong', 'incorrect']):
            return 'rejection'
        
        # Greetings
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return 'greeting'
        
        return 'general_inquiry'
    
    def extract_customer_info(self, message: str, context: ConversationContext) -> Dict[str, str]:
        """Extract customer information from message"""
        import re
        
        extracted = {}
        message_lower = message.lower()
        
        # Extract phone numbers
        phone_patterns = [
            r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',  # US format
            r'(\d{10})',  # 10 digits
            r'(\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4})'  # International
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, message.replace(' ', ''))
            if match and 'phone' not in context.customer_info:
                extracted['phone'] = match.group(1)
                break
        
        # Extract names (when explicitly mentioned)
        name_patterns = [
            r'my name is ([a-zA-Z\s]+)',
            r'i\'m ([a-zA-Z\s]+)',
            r'this is ([a-zA-Z\s]+)',
            r'call me ([a-zA-Z\s]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match and 'name' not in context.customer_info:
                name = match.group(1).strip()
                if len(name.split()) <= 3 and name.replace(' ', '').isalpha():
                    extracted['name'] = name.title()
                break
        
        # Extract date of birth
        dob_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',
            r'(\d{1,2}[a-z]{0,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})'
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, message_lower)
            if match and 'date_of_birth' not in context.customer_info:
                extracted['date_of_birth'] = match.group(1)
                break
        
        return extracted
    
    def reset_context(self, session_id: str):
        """Reset conversation context"""
        if session_id in self.contexts:
            del self.contexts[session_id]
    
    def get_context_for_prompt(self, session_id: str) -> str:
        """Get formatted context for AI prompt"""
        if session_id not in self.contexts:
            return "New conversation"
        
        context = self.contexts[session_id]
        
        prompt_parts = []
        
        # Recent conversation history
        if context.messages:
            prompt_parts.append("Recent conversation:")
            for msg in context.messages[-4:]:  # Last 4 messages
                prompt_parts.append(f"{msg['role']}: {msg['content']}")
            prompt_parts.append("")
        
        # Current context
        summary = context.get_context_summary()
        if summary != "New conversation":
            prompt_parts.append(f"Current context: {summary}")
            prompt_parts.append("")
        
        # Available slots if relevant
        if context.available_slots and not context.selected_slot:
            morning_slots = [s for s in context.available_slots if int(s.split(':')[0]) < 12]
            afternoon_slots = [s for s in context.available_slots if int(s.split(':')[0]) >= 12]
            
            if morning_slots:
                prompt_parts.append(f"Morning slots: {', '.join(morning_slots[:3])}")
            if afternoon_slots:
                prompt_parts.append(f"Afternoon slots: {', '.join(afternoon_slots[:3])}")
            prompt_parts.append("")
        
        # Missing information
        missing_fields = context.get_missing_fields()
        if missing_fields and context.conversation_stage == 'info_collection':
            prompt_parts.append(f"Still need: {', '.join(missing_fields)}")
            prompt_parts.append("")
        
        return "\n".join(prompt_parts)