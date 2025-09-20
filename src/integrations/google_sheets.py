"""Google Sheets integration for customer data storage"""

import os
import pickle
from datetime import datetime
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

# Scopes for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GoogleSheetsIntegration:
    """Google Sheets integration for customer data management"""
    
    def __init__(self, sheet_id: str = None, credentials_file: str = None):
        self.sheet_id = sheet_id or os.getenv('GOOGLE_SHEETS_ID')
        self.credentials_file = credentials_file or os.getenv('GOOGLE_CREDENTIALS_FILE')
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        creds = None
        token_file = 'sheets_token.pickle'
        
        # Load existing token
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_file or not os.path.exists(self.credentials_file):
                    raise ValueError(
                        "Google credentials file not found. "
                        "Please download credentials.json from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=8080)
            
            # Save credentials for next run
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('sheets', 'v4', credentials=creds)
        print("✅ Google Sheets authenticated successfully")
    
    def setup_customer_sheet(self, business_type: str = "generic") -> bool:
        """Setup customer data sheet with appropriate headers"""
        try:
            if not self.sheet_id:
                print("⚠️ No Google Sheets ID provided")
                return False
            
            # Define headers based on business type
            headers = self._get_headers_for_business_type(business_type)
            
            # Clear existing data and add headers
            range_name = 'A1:Z1'
            
            body = {
                'values': [headers]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"✅ Customer sheet setup complete for {business_type}")
            return True
            
        except HttpError as e:
            print(f"❌ Failed to setup sheet: {e}")
            return False
    
    def _get_headers_for_business_type(self, business_type: str) -> List[str]:
        """Get appropriate headers based on business type"""
        base_headers = ['Timestamp', 'Name', 'Phone', 'Appointment Date', 'Appointment Time']
        
        business_headers = {
            'dentist': base_headers + ['Date of Birth', 'Insurance Provider', 'Emergency Contact', 'Notes'],
            'doctor': base_headers + ['Date of Birth', 'Reason for Visit', 'Insurance Provider', 'Medications', 'Allergies', 'Emergency Contact'],
            'salon': base_headers + ['Preferred Service', 'Hair Type', 'Previous Services', 'Allergies', 'Notes'],
            'spa': base_headers + ['Preferred Service', 'Health Conditions', 'Allergies', 'Preferences', 'Notes'],
            'lawyer': base_headers + ['Case Type', 'Case Details', 'Urgency', 'Preferred Contact Method'],
            'generic': base_headers + ['Service Type', 'Notes']
        }
        
        return business_headers.get(business_type, business_headers['generic'])
    
    def store_customer_data(self, customer_info: Dict, appointment_details: Dict = None) -> bool:
        """Store customer information in Google Sheets"""
        try:
            if not self.sheet_id:
                print("⚠️ No Google Sheets ID provided - customer data not stored")
                return True  # Don't fail the booking
            
            # Get current timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Prepare row data
            row_data = [
                timestamp,
                customer_info.get('name', ''),
                customer_info.get('phone', ''),
                appointment_details.get('date', '') if appointment_details else '',
                appointment_details.get('time', '') if appointment_details else '',
            ]
            
            # Add business-specific fields
            additional_fields = [
                'date_of_birth', 'insurance_provider', 'emergency_contact', 'notes',
                'reason_for_visit', 'medications', 'allergies', 'preferred_service',
                'hair_type', 'previous_services', 'health_conditions', 'preferences',
                'case_type', 'case_details', 'urgency', 'preferred_contact_method',
                'service_type'
            ]
            
            for field in additional_fields:
                row_data.append(customer_info.get(field, ''))
            
            # Append to sheet
            body = {
                'values': [row_data]
            }
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range='A:Z',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            print("✅ Customer data stored in Google Sheets")
            return True
            
        except HttpError as e:
            print(f"⚠️ Failed to store customer data: {e}")
            return True  # Don't fail the booking if sheets fails
    
    def get_customer_history(self, phone: str = None, name: str = None) -> List[Dict]:
        """Get customer history from sheets"""
        try:
            if not self.sheet_id:
                return []
            
            # Read all data
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='A:Z'
            ).execute()
            
            values = result.get('values', [])
            if not values or len(values) < 2:
                return []
            
            headers = values[0]
            rows = values[1:]
            
            # Filter by phone or name
            matching_records = []
            for row in rows:
                if len(row) < len(headers):
                    row.extend([''] * (len(headers) - len(row)))
                
                record = dict(zip(headers, row))
                
                if phone and record.get('Phone', '').strip() == phone.strip():
                    matching_records.append(record)
                elif name and record.get('Name', '').lower().strip() == name.lower().strip():
                    matching_records.append(record)
            
            return matching_records
            
        except HttpError as e:
            print(f"Error getting customer history: {e}")
            return []