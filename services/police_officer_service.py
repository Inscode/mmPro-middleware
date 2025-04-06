from datetime import datetime, timedelta, timezone
import os
import requests
from dotenv import load_dotenv
from utils.jwt_utils import JWTUtils
from utils.user_utils import UserUtils

load_dotenv()

REDMINE_URL = os.getenv("REDMINE_URL")

class PoliceOfficerService:
    @staticmethod
    def check_lorry_number(lorry_number, token):
        try:
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            headers = {"X-Redmine-API-Key": API_KEY}
            current_time_utc = datetime.utcnow().replace(tzinfo=timezone.utc)

            # Fetch all TPL licenses (tracker_id = 5)
            tpl_params = {"tracker_id": 8}
            tpl_response = requests.get(f"{REDMINE_URL}/issues.json", params=tpl_params, headers=headers)

            if tpl_response.status_code != 200:
                return None, f"Failed to fetch TPL issues: {tpl_response.status_code} - {tpl_response.text}"

            tpl_issues = tpl_response.json().get("issues", [])
            lorry_number_lower = lorry_number.lower()

            # Find valid TPL license (not expired)
            valid_tpl_license = None
            for issue in tpl_issues:
                # Check lorry number match (custom field 53)
                lorry_match = any(
                    cf["id"] == 53 and cf.get("value") and str(cf["value"]).lower() == lorry_number_lower
                    for cf in issue.get("custom_fields", [])
                )
            
                if lorry_match:
                    # Check license validity
                    created_on_str = issue.get("created_on")
                    if not created_on_str:
                        continue
                
                    try:
                        created_on_utc = datetime.strptime(created_on_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        estimated_hours = float(issue.get("estimated_hours", 0))
                    
                        # Calculate expiration time
                        expiration_time_utc  = created_on_utc + timedelta(hours=estimated_hours)
                    
                        # Check if license is still valid
                        if current_time_utc  < expiration_time_utc :
                            valid_tpl_license = issue
                            is_valid = True
                            break  
                        else:
                            valid_tpl_license = issue  # Keep reference even if expired
                            is_valid = False
                          
                    except Exception as e:
                        print(f"Error processing issue {issue.get('id')}: {str(e)}")
                        continue

            if not valid_tpl_license:
                return None, "No valid (non-expired) TPL with this lorry number"
            
            # Convert times to Sri Lanka time (UTC+5:30)
            sri_lanka_offset = timedelta(hours=5, minutes=30)
            created_on_sl = created_on_utc + sri_lanka_offset
            valid_until_sl = created_on_sl + timedelta(hours=estimated_hours)

            # Extract TPL data
            tpl_data = {
                "LicenseNumber": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 8), None),
                "Cubes": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 15), None),
                "Destination": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 12), None),
                "ValidUntil": (created_on_sl + timedelta(hours=estimated_hours)).strftime("%A, %B %d, %Y at %I:%M %p"),
                "Route_01": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 55), None),
                "Route_02": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 56), None),
                "Route_03": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 57), None),
                "IsValid": is_valid,
                
            }

            # Fetch corresponding Mining License (tracker_id = 4)
            ml_number = tpl_data["LicenseNumber"]
            if ml_number:
                ml_params = {"tracker_id": 8, "subject": ml_number}
                ml_response = requests.get(f"{REDMINE_URL}/issues.json", params=ml_params, headers=headers)

                if ml_response.status_code == 200:
                    ml_issues = ml_response.json().get("issues", [])
                    if ml_issues:
                        mining_license = ml_issues[0]
                        mining_data = {
                           # "licenseNumber": mining_license["subject"],
                            "owner": mining_license["assigned_to"]["name"] if isinstance(mining_license["assigned_to"], dict) else str(mining_license["assigned_to"]),
                            "License Start Date": mining_license["start_date"],
                            "License End Date": mining_license["due_date"],
                            "License Owner Contact Number": next((cf["value"] for cf in mining_license["custom_fields"] if cf["id"] == 3), None),
                            "Grama Niladhari Division": next((cf["value"] for cf in mining_license["custom_fields"] if cf["id"] == 31), None),
                        }
                        tpl_data.update(mining_data)

            return tpl_data, None

        except Exception as e:
            return None, f"Server error: {str(e)}"    

    @staticmethod
    def create_complaint(vehicleNumber, userID, token):

        phoneNumber = UserUtils.get_user_phone(userID)
        print(phoneNumber)

        issue_data = {
                'issue': {
                    'project_id': 31,  
                    'tracker_id': 26,  
                    'subject': "New Complaint",  
                    'status_id': 29, 
                    'priority_id': 2,  
                    'assigned_to_id': 59,
                    'custom_fields': [
                        {'id': 3, 'name': "Mobile Number", 'value': phoneNumber},
                        {'id': 13, 'name': "Lorry Number", 'value': vehicleNumber},
                        {'id': 8, 'name': "Role", 'value': "PoliceOfficer"}
                    ]
                }
            }

        api_key = JWTUtils.get_api_key_from_token(token)

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