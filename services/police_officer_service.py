from datetime import datetime, timedelta, timezone
import os
import requests
from dotenv import load_dotenv
from utils.jwt_utils import JWTUtils
from utils.user_utils import UserUtils
from utils.constants import CONTENT_TYPE_JSON, REDMINE_API_ERROR_MSG

load_dotenv()

REDMINE_URL = os.getenv("REDMINE_URL")

class PoliceOfficerService:
    @staticmethod
    def check_lorry_number(lorry_number, token):
        try:
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None,  REDMINE_API_ERROR_MSG

            headers = {"X-Redmine-API-Key": API_KEY}
            current_time_utc = datetime.now(timezone.utc)

            # Fetch all TPL licenses (tracker_id = 5)
            tpl_params = {"tracker_id": 5}
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

            # Extract TPL data
            tpl_data = {
                "LicenseNumber": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 59), None),
                "Cubes": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 58), None),
                "Destination": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 68), None),
                "ValidUntil": (created_on_sl + timedelta(hours=estimated_hours)).strftime("%A, %B %d, %Y at %I:%M %p"),
                "Route_01": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 55), None),
                "Route_02": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 56), None),
                "Route_03": next((cf["value"] for cf in valid_tpl_license["custom_fields"] if cf["id"] == 57), None),
                "IsValid": is_valid,
                "Assignee": valid_tpl_license["assigned_to"]["name"] if isinstance(valid_tpl_license.get("assigned_to"), dict) else str(valid_tpl_license.get("assigned_to")),

                
            }

            # Fetch corresponding Mining License (tracker_id = 4)
            ml_number = tpl_data["LicenseNumber"]
            if ml_number:
                # First get all mining license issues (tracker_id=4)
                ml_params = {
                    "tracker_id": 4,
                    "status_id": "*"  # Include all statuses or specify if needed
                }
                ml_response = requests.get(f"{REDMINE_URL}/issues.json", params=ml_params, headers=headers)

                if ml_response.status_code == 200:
                    ml_issues = ml_response.json().get("issues", [])
                    
                    # Find the issue where custom field 101 matches our license number
                    matching_license = None
                    for issue in ml_issues:
                        # Search through custom fields for field ID 101 with matching value
                        for cf in issue.get("custom_fields", []):
                            if cf.get("id") == 101 and str(cf.get("value")) == str(ml_number):
                                matching_license = issue
                                break
                        if matching_license:
                            break

                    if matching_license:
                        mining_data = {
                            "owner": matching_license["assigned_to"]["name"] if isinstance(matching_license["assigned_to"], dict) else str(matching_license["assigned_to"]),
                            "License Start Date": matching_license["start_date"],
                            "License End Date": matching_license["due_date"],
                            "License Owner Contact Number": next((cf["value"] for cf in matching_license["custom_fields"] if cf.get("id") == 66), None),
                            "Grama Niladhari Division": next((cf["value"] for cf in matching_license["custom_fields"] if cf.get("id") == 31), None),
                        }
                        tpl_data.update(mining_data)

            return tpl_data, None


        except Exception as e:
            return None, f"Server error: {str(e)}"    

    @staticmethod
    def create_complaint(vehicleNumber, userID, token):
       
        phone_number  = UserUtils.get_user_phone(userID)
       

        issue_data = {
                'issue': {
                    'project_id': 1,  
                    'tracker_id': 6,  
                    'subject': "New Complaint",  
                    'status_id': 1, 
                    'priority_id': 2,  
                    'assigned_to_id': 8,
                    'custom_fields': [
                        {'id':66, 'name': "Mobile Number", 'value': phone_number },
                        {'id':53, 'name': "Lorry Number", 'value': vehicleNumber},
                        {'id':67, 'name': "Role", 'value': "PoliceOfficer"}
                    ]
                }
            }

        api_key = JWTUtils.get_api_key_from_token(token)

        response = requests.post(
            f'{REDMINE_URL}/issues.json',
            json=issue_data,
            headers={'X-Redmine-API-Key': api_key, 'Content-Type': CONTENT_TYPE_JSON}
        )

        if response.status_code == 201:
            issue_id = response.json()['issue']['id']
            return True, issue_id
        else:
            return False, 'Failed to create complaint'
        