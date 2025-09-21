"""MCP Server implementation for Universal Appointment Agent"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

from ..core.agent import UniversalAppointmentAgent
from ..config.business_config import BusinessConfig, create_dental_config, create_salon_config, create_doctor_config
from .tools_definitions import APPOINTMENT_TOOLS

class UniversalAppointmentMCPServer:
    """MCP Server for Universal Appointment Agent"""
    
    def __init__(self):
        self.server = Server("universal-appointment-agent")
        self.agent: Optional[UniversalAppointmentAgent] = None
        self.setup_handlers()
        print("Universal Appointment Agent MCP Server initialized")
    
    def setup_handlers(self):
        """Setup MCP server request handlers"""
        
        # Store reference to self for handlers
        server_instance = self
        
        async def handle_list_tools() -> List[Tool]:
            """Return available MCP tools"""
            return APPOINTMENT_TOOLS
        
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle MCP tool calls"""
            
            try:
                print(f"Handling tool call: {name}")
                
                if name == "configure_business":
                    return await server_instance._configure_business(arguments)
                elif name == "chat_with_agent":
                    return await server_instance._chat_with_agent(arguments)
                elif name == "check_availability":
                    return await server_instance._check_availability(arguments)
                elif name == "book_appointment_direct":
                    return await server_instance._book_appointment_direct(arguments)
                elif name == "get_agent_status":
                    return await server_instance._get_agent_status(arguments)
                elif name == "get_conversation_status":
                    return await server_instance._get_conversation_status(arguments)
                elif name == "reset_conversation":
                    return await server_instance._reset_conversation(arguments)
                elif name == "cancel_appointment":
                    return await server_instance._cancel_appointment(arguments)
                elif name == "get_business_info":
                    return await server_instance._get_business_info(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
                    
            except Exception as e:
                error_msg = f"Error executing tool '{name}': {str(e)}"
                print(f"Tool execution error: {error_msg}")
                return [TextContent(type="text", text=error_msg)]
        
        # Store handlers for the server to use
        self._handle_list_tools = handle_list_tools
        self._handle_call_tool = handle_call_tool
    
    async def _configure_business(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Configure the appointment agent for a specific business"""
        try:
            # Create business configuration
            config = BusinessConfig(
                business_type=arguments["business_type"],
                business_name=arguments["business_name"],
                assistant_name=arguments["assistant_name"],
                services=arguments["services"],
                working_hours=arguments["working_hours"],
                appointment_duration=arguments.get("appointment_duration", 60),
                timezone=arguments.get("timezone", "America/New_York"),
                calendar_id=arguments.get("calendar_id", "primary"),
                sheet_id=arguments.get("sheet_id")
            )
            
            # Initialize the agent
            self.agent = UniversalAppointmentAgent(config)
            
            result = {
                "success": True,
                "message": f"Agent configured successfully for {config.business_name}",
                "configuration": {
                    "business_type": config.business_type,
                    "business_name": config.business_name,
                    "assistant_name": config.assistant_name,
                    "services": config.services,
                    "appointment_duration": config.appointment_duration,
                    "timezone": config.timezone
                }
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "message": "Failed to configure agent"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]
    
    async def _chat_with_agent(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Have a conversation with the appointment agent"""
        if not self.agent:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "Agent not configured. Please configure business first using 'configure_business' tool."
                })
            )]
        
        try:
            message = arguments["message"]
            session_id = arguments.get("session_id", "default")
            
            # Process message through the agent
            response = await self.agent.process_message(message, session_id)
            
            # Get conversation status for additional context
            status = self.agent.get_conversation_status(session_id)
            
            result = {
                "success": True,
                "response": response,
                "conversation_status": {
                    "stage": status["status"],
                    "context": status["context"],
                    "appointment_booked": status["appointment_booked"],
                    "missing_fields": status.get("missing_fields", [])
                },
                "session_id": session_id
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "message": "Failed to process conversation"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]
    
    async def _check_availability(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Check available appointment slots"""
        if not self.agent:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "Agent not configured"
                })
            )]
        
        try:
            date = arguments["date"]
            duration = arguments.get("duration", self.agent.config.appointment_duration)
            
            # Get working hours for the date
            from datetime import datetime
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            working_hours = self.agent.config.get_working_hours_for_date(date_obj)
            
            if not working_hours:
                result = {
                    "success": True,
                    "date": date,
                    "available_slots": [],
                    "message": f"Business is closed on {date}"
                }
            else:
                slots = self.agent.calendar.get_available_slots(
                    date, working_hours, duration, self.agent.config.timezone
                )
                
                result = {
                    "success": True,
                    "date": date,
                    "working_hours": working_hours,
                    "available_slots": slots,
                    "message": f"Found {len(slots)} available slots for {date}"
                }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "message": "Failed to check availability"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]
    
    async def _book_appointment_direct(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Book appointment directly without conversation"""
        if not self.agent:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "Agent not configured"
                })
            )]
        
        try:
            date = arguments["date"]
            time_slot = arguments["time_slot"]
            customer_info = arguments["customer_info"]
            summary = arguments.get("summary")
            
            # Book the appointment
            booking_result = self.agent.calendar.book_appointment(
                date=date,
                time_slot=time_slot,
                customer_info=customer_info,
                timezone=self.agent.config.timezone,
                summary=summary
            )
            
            if booking_result["success"]:
                # Store customer data if sheets is configured
                if self.agent.sheets:
                    self.agent.sheets.store_customer_data(
                        customer_info,
                        {"date": date, "time": time_slot}
                    )
            
            return [TextContent(
                type="text",
                text=json.dumps(booking_result, indent=2)
            )]
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "message": "Failed to book appointment"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]
    
    async def _get_agent_status(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get current agent status and configuration"""
        if not self.agent:
            result = {
                "configured": False,
                "message": "Agent not configured"
            }
        else:
            result = {
                "configured": True,
                "business_type": self.agent.config.business_type,
                "business_name": self.agent.config.business_name,
                "assistant_name": self.agent.config.assistant_name,
                "services": self.agent.config.services,
                "working_hours": self.agent.config.working_hours,
                "appointment_duration": self.agent.config.appointment_duration,
                "timezone": self.agent.config.timezone,
                "calendar_integration": True,
                "sheets_integration": self.agent.sheets is not None,
                "active_conversations": len(self.agent.conversation_manager.contexts)
            }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _get_conversation_status(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get conversation status for a session"""
        if not self.agent:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "Agent not configured"
                })
            )]
        
        session_id = arguments.get("session_id", "default")
        status = self.agent.get_conversation_status(session_id)
        
        return [TextContent(
            type="text",
            text=json.dumps(status, indent=2)
        )]
    
    async def _reset_conversation(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Reset conversation session"""
        if not self.agent:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "Agent not configured"
                })
            )]
        
        session_id = arguments.get("session_id", "default")
        self.agent.reset_conversation(session_id)
        
        result = {
            "success": True,
            "message": f"Conversation reset for session: {session_id}"
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _cancel_appointment(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Cancel an appointment"""
        if not self.agent:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "Agent not configured"
                })
            )]
        
        try:
            event_id = arguments["event_id"]
            result = self.agent.calendar.cancel_appointment(event_id)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "message": "Failed to cancel appointment"
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]
    
    async def _get_business_info(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get business information"""
        if not self.agent:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "configured": False,
                    "message": "No business configured"
                })
            )]
        
        config = self.agent.config
        info = {
            "business_type": config.business_type,
            "business_name": config.business_name,
            "assistant_name": config.assistant_name,
            "services": config.services,
            "working_hours": config.working_hours,
            "appointment_duration": config.appointment_duration,
            "timezone": config.timezone,
            "greeting": config.get_greeting()
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(info, indent=2)
        )]
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="universal-appointment-agent",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

# Entry point for running the server
async def main():
    """Main entry point for MCP server"""
    print("🚀 Starting Universal Appointment Agent MCP Server...")
    print("Ready for Coral Protocol integration!")
    
    server = UniversalAppointmentMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())