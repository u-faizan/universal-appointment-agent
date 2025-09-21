#!/usr/bin/env python3
"""
Universal Appointment Agent MCP Server Entry Point
For Coral Protocol Integration
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run the MCP server
from src.mcp.server import main

if __name__ == "__main__":
    print("Universal Appointment Agent - MCP Server")
    print("=" * 50)
    print("Starting server for Coral Protocol integration...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"\nServer error: {e}")
        sys.exit(1)