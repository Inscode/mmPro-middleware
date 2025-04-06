import os
import requests
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import random
from diskcache import Cache

# Initialize cache and load environment variables
cache = Cache('otp_cache')
load_dotenv()

# Configuration from environment variables
REDMINE_URL = os.getenv("REDMINE_URL")
API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
VERIFY_SERVICE_SID = os.getenv("VERIFY_SERVICE_SID")

# Initialize Twilio client if credentials are available
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN]) else None

class GeneralPublicService:
    # Constants based on your Redmine configuration
    TRACKER_TPL = 8          # TPL License tracker
    TRACKER_COMPLAINT = 26   # Complaints tracker
    CUSTOM_FIELD_LORRY = 53  # Lorry Number field
    CUSTOM_FIELD_PHONE = 66  # Mobile Number field
    CUSTOM_FIELD_ROLE = 67   # Role field
    PROJECT_ADMIN = 14       # Admin project ID
    STATUS_NEW = 11          # New status ID

    @staticmethod
    def is_lorry_number_valid(lorry_number):
        """
        Check if a lorry number exists in the TPL license records
        """
        try:
            if not REDMINE_URL or not API_KEY:
                return None, "Redmine configuration missing"

            headers = {"X-Redmine-API-Key": API_KEY}
            params = {
                "tracker_id": GeneralPublicService.TRACKER_TPL,
                "limit": 100  # Adjust based on expected number of records
            }

            response = requests.get(
                f"{REDMINE_URL}/issues.json",
                params=params,
                headers=headers
            )

            if response.status_code != 200:
                return None, f"Redmine API error: {response.status_code}"

            issues = response.json().get("issues", [])
            lorry_number_lower = lorry_number.lower().strip()

            for issue in issues:
                for field in issue.get("custom_fields", []):
                    if field.get("id") == GeneralPublicService.CUSTOM_FIELD_LORRY:
                        if str(field.get("value", "")).lower() == lorry_number_lower:
                            return True, None

            return False, None

        except requests.RequestException as e:
            return None, f"Network error: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"

    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))

    @staticmethod
    def send_verification_code(phone):
        """
        Send OTP to the provided phone number
        Returns tuple: (success: bool, message: str)
        """
        try:
            # Clean phone number and validate
            phone = phone.strip()
            if not phone.startswith('+'):
                phone = f"+94{phone.lstrip('0')}"  # Assuming Sri Lankan numbers
            
            otp = GeneralPublicService.generate_otp()
            cache.set(phone, otp, expire=600)  # 10 minute expiration

            # Using Textware SMS gateway
            response = requests.get(
                "https://message.textware.lk:5001/sms/send_sms.php",
                params={
                    "username": "aasait",
                    "password": "Aasait@textware132",
                    "src": "AASAIT",
                    "dst": phone,
                    "msg": f"Your AASA verification code is: {otp}"
                },
                timeout=10
            )

            if response.status_code == 200 and "success" in response.text.lower():
                return True, "OTP sent successfully"
            return False, f"SMS gateway error: {response.text}"

        except requests.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def verify_code(phone, code):
        """
        Verify the OTP code for a phone number
        Returns tuple: (success: bool, message: str)
        """
        stored_otp = cache.get(phone.strip())
        if not stored_otp:
            return False, "OTP expired or not found"
        if stored_otp == code.strip():
            cache.delete(phone)
            return True, "Verification successful"
        return False, "Invalid OTP code"

    @staticmethod
    def create_complaint(phone_number, vehicle_number, description=None):
        """
        Create a new complaint ticket in Redmine
        Returns tuple: (success: bool, issue_id/error_message: str)
        """
        try:
            issue_data = {
                'issue': {
                    'project_id': GeneralPublicService.PROJECT_ADMIN,
                    'tracker_id': GeneralPublicService.TRACKER_COMPLAINT,
                    'subject': f"Vehicle Complaint: {vehicle_number}",
                    'description': description or "No additional details provided",
                    'status_id': GeneralPublicService.STATUS_NEW,
                    'priority_id': 2,  # Normal priority
                    'custom_fields': [
                        {
                            'id': GeneralPublicService.CUSTOM_FIELD_PHONE,
                            'value': phone_number
                        },
                        {
                            'id': GeneralPublicService.CUSTOM_FIELD_LORRY,
                            'value': vehicle_number
                        },
                        {
                            'id': GeneralPublicService.CUSTOM_FIELD_ROLE,
                            'value': "Public"
                        }
                    ]
                }
            }

            response = requests.post(
                f'{REDMINE_URL}/issues.json',
                json=issue_data,
                headers={
                    'X-Redmine-API-Key': API_KEY,
                    'Content-Type': 'application/json'
                },
                timeout=30
            )

            if response.status_code == 201:
                issue_id = response.json().get('issue', {}).get('id')
                return True, str(issue_id) if issue_id else "Complaint created"
            else:
                error = response.json().get('errors', ['Failed to create complaint'])[0]
                return False, f"Redmine error: {error}"

        except requests.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"