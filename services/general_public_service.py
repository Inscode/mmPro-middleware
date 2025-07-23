import os
import requests
from dotenv import load_dotenv
from twilio.rest import Client
from services.cache import cache
from datetime import datetime, timedelta, timezone
import secrets


load_dotenv()

TWILIO_ACCOUNT_SID = 'AC99293cf8d316875de7dfd3c164e90cbb'
TWILIO_AUTH_TOKEN = 'f848dae98a365e367fa4f08056c871c2'  
VERIFY_SERVICE_SID = 'VA8e0fb628c45e51612bf3e2dd68ef1efe'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

REDMINE_URL = os.getenv("REDMINE_URL")
API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")

class GeneralPublicService:
   
    @staticmethod
    def is_lorry_number_valid(lorry_number):
        try:
            # Extract the user-specific API key from the token
            api_key = API_KEY

            if not REDMINE_URL or not api_key:
                return None, "Redmine URL or API Key is missing"

            headers = {"X-Redmine-API-Key": api_key}

            # Fetch all TPL licenses (tracker_id = 5)
            tpl_params = {"tracker_id": 5}
            tpl_response = requests.get(f"{REDMINE_URL}/issues.json", params=tpl_params, headers=headers)

            if tpl_response.status_code != 200:
                return None, f"Failed to fetch TPL issues: {tpl_response.status_code} - {tpl_response.text}"

            tpl_issues = tpl_response.json().get("issues", [])
            lorry_number_lower = lorry_number.lower()
            current_time = datetime.now(timezone.utc)


            # Check if any TPL license matches the given lorry number (cf_13)
            for issue in tpl_issues:
            # Check lorry number match
                lorry_match = any(
                    cf["id"] == 53 and cf["value"] and cf["value"].lower() == lorry_number_lower 
                    for cf in issue.get("custom_fields", [])
                )
            
                if lorry_match:
                    # Check license validity
                    created_on_str = issue.get("created_on")
                    if not created_on_str:
                        continue  # Skip if no creation date
                
                    try:
                        created_on = datetime.strptime(created_on_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        estimated_hours = issue.get("estimated_hours", 0)
                    
                        # Calculate expiration time
                        expiration_time = created_on + timedelta(hours=estimated_hours)
                    
                        # Check if license is still valid
                        if current_time < expiration_time:
                            return True, None  # Valid license found
                        else:
                            continue  # License expired, check next one
                    except Exception as e:
                        print(f"Error processing issue {issue.get('id')}: {str(e)}")
                        continue

            # If we get here, no valid license was found
            return False, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def generate_otp():
        return str(secrets.randbelow(900000) + 100000)  # Generate a 6-digit OTP

    @staticmethod
    def send_verification_code(phone):
        otp = GeneralPublicService.generate_otp()  # Generate OTP
        cache.set(phone, otp, expire=600)  # Store OTP in cache for 10 minutes

        try:
            url = "https://message.textware.lk:5001/sms/send_sms.php"
            params = {
                "username": os.getenv("TEXTWARE_USERNAME"),
                "password": os.getenv("TEXTWARE_PASSWORD"),
                "src": "TWTEST",
                "dst": phone,
                "msg": f"Your OTP code is {otp}"
            }
            response = requests.get(url, params=params)

            if response.status_code == 200:
                return True, "Message sent successfully"
            else:
                return False, f"Failed to send message: {response.text}"

        except requests.RequestException as e:
            return False, str(e)

    @staticmethod
    def verify_code(phone, code):
        stored_otp = cache.get(phone)  # Retrieve stored OTP

        if stored_otp is None:
            return False, "OTP expired or not found"

        if stored_otp == code:
            cache.delete(phone)  # Remove OTP after successful verification
            return True, None
        else:
            return False, "Invalid OTP"

    @staticmethod
    def create_complaint(phoneNumber, vehicleNumber):
        issue_data = {
                'issue': {
                    'project_id': 1,  
                    'tracker_id': 6,  
                    'subject': "New Complaint",  
                    'status_id': 1, 
                    'priority_id': 2,  
                    'custom_fields': [
                        {'id': 66, 'name': "Mobile Number", 'value': phoneNumber},
                        {'id': 53, 'name': "Lorry Number", 'value': vehicleNumber},
                        {'id': 67, 'name': "Role", 'value': "Public"}
                    ]
                }
            }
        
        api_key = API_KEY

        response = requests.post(
            f'{REDMINE_URL}/issues.json',
            json=issue_data,
            headers={'X-Redmine-API-Key': api_key, 'Content-Type': 'application/json'}
        )

        if response.status_code == 201:
            issue_id = response.json()['issue']['id']
            return True, issue_id
        else:
            return False, 'Failed to create complaint'