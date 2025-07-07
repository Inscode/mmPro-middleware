import os
from dotenv import load_dotenv
import requests
from utils.MLOUtils import MLOUtils
from utils.jwt_utils import JWTUtils
from utils.limit_utils import LimitUtils
from utils.jwt_utils import JWTUtils
from werkzeug.utils import secure_filename 
import json


load_dotenv()

class MiningEnginerService:

    ORS_API_KEY = os.getenv("ORS_API_KEY")
    
    @staticmethod
    def update_miningOwner_appointment(token,issue_id,update_data):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"
            
            payload = {
            "issue": {
                "status_id": update_data.get("status_id", 31),  # Default status ID
                #"description": appointment_data.get("description", ""),
                "due_date": update_data.get("due_date" ), 
                }
            }

            headers = {
            "Content-Type": "application/json",
            "X-Redmine-API-Key": API_KEY
            }

            response = requests.put(
            f"{REDMINE_URL}/issues/{issue_id}.json",
            json=payload,
            headers=headers
            )

            if response.status_code == 201:
                return response.json(), None
            else:
                error_msg = f"Failed to create appointment. Status: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f", Error: {error_data.get('errors', 'Unknown error')}"
                except:
                    error_msg += f", Response: {response.text}"
                return None, error_msg

        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"
        
     
    @staticmethod
    def get_me_pending_licenses(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            headers = {"X-Redmine-API-Key": API_KEY}
            
            # --- Constants ---
            TRACKER_ID = 4  # Mining License tracker
            STATUS_ID = 26  # ME Appointment Pending
            LIMIT = 100

            offset = 0
            all_issues = []

            # --- Paginated fetch ---
            while True:
                params = {
                    "tracker_id": TRACKER_ID,
                    "status_id": STATUS_ID,
                    "offset": offset,
                    "limit": LIMIT
                }

                response = requests.get(
                    f"{REDMINE_URL}/projects/mmpro-gsmb/issues.json",
                    params=params,
                    headers=headers
                )

                if response.status_code != 200:
                    return None, f"Redmine API error: {response.status_code} - {response.text[:200]}"

                data = response.json()
                issues = data.get("issues", [])
                all_issues.extend(issues)

                if len(issues) < LIMIT:
                    break

                offset += LIMIT

            # --- Process issues ---
            processed_issues = []
            for issue in all_issues:
                custom_fields = {
                    field['id']: field['value']
                    for field in issue.get('custom_fields', [])
                    if str(field.get('value', '')).strip()
                }

                processed_issues.append({
                    "id": issue.get("id"),
                    "assigned_to": issue.get("assigned_to", {}).get("name"),
                    "Google_location": custom_fields.get(92),
                    "mining_number": custom_fields.get(101),
                })

            return processed_issues, None

        except Exception as e:
            return None, f"Server error: {str(e)}"


    
    # @staticmethod
    # def get_attachment_urls(api_key, redmine_url, custom_fields):
    #     try:
    #         # Define the mapping of custom field names to their attachment IDs
    #         file_fields = {
    #             "Detailed Mine Restoration Plan": None,
    #             "Deed and Survey Plan": None,
    #             "Payment Receipt": None     
    #         }

    #         # Extract attachment IDs from custom fields
    #         for field in custom_fields:
    #             field_name = field.get("name")
    #             attachment_id = field.get("value")

    #             if field_name in file_fields and attachment_id.isdigit():
    #                 file_fields[field_name] = attachment_id

    #         # Fetch URLs for valid attachment IDs
    #         file_urls = {}
    #         for field_name, attachment_id in file_fields.items():
    #             if attachment_id:
    #                 attachment_url = f"{redmine_url}/attachments/{attachment_id}.json"
    #                 response = requests.get(
    #                     attachment_url,
    #                     headers={"X-Redmine-API-Key": api_key, "Content-Type": "application/json"}
    #                 )

    #                 if response.status_code == 200:
    #                     attachment_data = response.json().get("attachment", {})
    #                     file_urls[field_name] = attachment_data.get("content_url", "")

    #         return file_urls

    #     except Exception as e:
    #         return {}


    @staticmethod
    def get_attachment_urls(custom_fields):
        try:
            upload_field_names = {
                "Economic Viability Report",
                "Detailed Mine Restoration Plan",
                "Professional",
                "Deed and Survey Plan",
                "License Boundary Survey",
                "Payment Receipt"
            }

            file_urls = {}

            for field in custom_fields:
                field_name = field.get("name")
                raw_value = field.get("value")

                if field_name not in upload_field_names:
                    continue

                if not raw_value:
                    file_urls[field_name] = None
                    continue

                attachment_id = str(raw_value).strip()
                file_urls[field_name] = int(attachment_id) if attachment_id.isdigit() else None

            return file_urls

        except Exception as e:
            print(f"[ERROR] Failed to get attachment IDs: {str(e)}")
            return {}
        
    @staticmethod
    def miningEngineer_approve(token, ml_id, me_appointment_id, update_data, attachments=None):   
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"
            
            headers = {
                "Content-Type": "application/json",
                "X-Redmine-API-Key": API_KEY
            }

            # Step 1: Update ML Issue
            payload = {
                "issue": {
                    "status_id": update_data.get("status_id", 32),    
                    "start_date": update_data.get("start_date", ""),  # Optional
                    "due_date": update_data.get("due_date", ""),      # Optional
                    "custom_fields": [
                        {
                            "id": 34,  # Capacity
                            "value": update_data.get("Capacity", "")
                        },
                        {
                            "id": 99,  # Month capacity
                            "value": update_data.get("month_capacity", "")
                        },
                        {
                            "id": 96,  # ME Comment
                            "value": update_data.get("me_comment", "")
                        },
                        {
                            "id": 94,  # ME Report
                            "value": update_data.get("me_report")
                        },
                        {
                            "id": 64,  
                            "value": update_data.get("Remaining")
                        },
                        {
                            "id": 63, 
                            "value": update_data.get("Used")
                        },
                         {
                            "id": 18,  # ME Report
                            "value": update_data.get("royalty", "")
                        }
                    ]              
                }
            }

            response = requests.put(
                f"{REDMINE_URL}/issues/{ml_id}.json",
                json=payload,
                headers=headers
            )

            if response.status_code not in (200, 204):
                return None, f"Redmine API error: {response.status_code} - {response.text}"

            # Step 2: Close ME Appointment Issue
            me_payload = {
                "issue": {
                    "status_id": 5  # Assuming 5 means 'closed'
                }
            }

            me_response = requests.put(
                f"{REDMINE_URL}/issues/{me_appointment_id}.json",
                json=me_payload,
                headers=headers
            )

            if me_response.status_code not in (200, 204):
                return None, f"Failed to close ME Appointment: {me_response.status_code} - {me_response.text}"

            # Final response
            try:
                return (response.json(), None) if response.content else ({"status": "success"}, None)
            except ValueError:
                return {"status": "success"}, None

        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"


    @staticmethod
    def miningEngineer_reject(token, ml_id, me_appointment_id, update_data):   
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"
            
            # Prepare payload for rejection
            payload = {
                "issue": {
                    "status_id": update_data.get("status_id", 6),  # Rejected
                    "custom_fields": [
                        {
                            "id": 97,  # MeComment(F)
                            "value": update_data.get("me_comment", "")
                        },
                        {
                            "id": 98,  # MeReport(F)
                            "value": update_data.get("me_report")
                        }
                    ]
                }
            }

            headers = {
                "Content-Type": "application/json",
                "X-Redmine-API-Key": API_KEY
            }

            # Send update to Redmine
            ml_response = requests.put(
                f"{REDMINE_URL}/issues/{ml_id}.json",
                json=payload,
                headers=headers
            )
            
            if ml_response.status_code not in (200, 204):
                return None, f"Redmine API error (ML ID : {ml_id}):{ml_response.text}"
            
            me_payload = {
                "issue": {
                    "status_id": 5  # Assuming 5 means 'closed'
                }
            }

            me_response = requests.put(
                f"{REDMINE_URL}/issues/{me_appointment_id}.json",
                json=me_payload,
                headers=headers
            )

            if me_response.status_code not in (200, 204):
                return None, f"Failed to close ME Appointment: {me_response.status_code} - {me_response.text}"

            # Final response
            try:
                return (ml_response.json(), None) if ml_response.content else ({"status": "success"}, None)
            except ValueError:
                return {"status": "success"}, None
            
        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"

    @staticmethod
    def create_ml_appointment(token, start_date,mining_license_number,Google_location):
        """
        Creates a Mining Engineer appointment in Redmine.
        
        Args:
            token: JWT token for authentication
            start_date: Appointment date (YYYY-MM-DD)
            mining_license_number: License number to associate
            
        Returns:
            Tuple (created_issue_data, error_message)
        """
        try:
            # 1. Get Redmine configuration
            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Redmine URL not configured"

            # 2. Extract API key and user info from token
            api_key = JWTUtils.get_api_key_from_token(token)
            if not api_key:
                return None, "Invalid API token"

            user_Id, error = MLOUtils.get_user_info_from_token(token)
            if not user_Id:
                return None, f"User info error: {error}"

            # 3. Extract ML issue ID from license number (format: LLL/100/206)
            try:
                ml_issue_id = int(mining_license_number.split('/')[-1])
            except (IndexError, ValueError):
                return None, "Invalid mining license number format. Expected LLL/100/ID"

            # 4. Prepare and create appointment
            payload = {
                "issue": {
                    "project_id": 1,
                    "tracker_id": 12,  # MeAppointment tracker
                    "status_id": 31,   # ME Appointment Scheduled
                    "subject": f"Site Visit for Mining License {mining_license_number}",
                    "start_date": start_date,
                    "assigned_to_id": user_Id,
                    "custom_fields": [
                        {
                            "id": 101,  # Mining License Number field
                            "value": mining_license_number
                        },
                        {
                            "id": 92,  # Mining License Number field
                            "value": Google_location,
                        }
                    ]
                }
            }

            # Create the appointment
            response = requests.post(
                f"{REDMINE_URL}/issues.json",
                headers={
                    "X-Redmine-API-Key": api_key,
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )

            if response.status_code != 201:
                error_msg = f"Redmine error creating appointment ({response.status_code}): {response.text[:200]}"
                return None, error_msg

            # 5. Update the original ML issue status
            success, status_error = MiningEnginerService.change_issue_status(
                token=token,
                issue_id=ml_issue_id,
                new_status_id=31  # ME Appointment Scheduled
            )

            if not success:
                # Log but don't fail the whole operation
                print(f"Warning: Created appointment but failed to update ML status: {status_error}")
                # You might want to implement retry logic here

            return response.json(), None

        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"


    @staticmethod
    def change_issue_status(token, issue_id, new_status_id):
        try:
            user_api_key = JWTUtils.get_api_key_from_token(token)

            if not user_api_key:
                return None, "Invalid or missing API key"

            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Environment variable 'REDMINE_URL' is not set"

            update_payload = {
                "issue": {
                    "status_id": new_status_id
                }
            }

            response = requests.put(
                f"{REDMINE_URL}/issues/{issue_id}.json",
                headers={
                    "X-Redmine-API-Key": user_api_key,
                    "Content-Type": "application/json"
                },
                data=json.dumps(update_payload)
            )

            if response.status_code != 204:
                return None, f"Failed to update issue status: {response.status_code} - {response.text}"

            return True, None

        except Exception as e:
            return None, f"Server error: {str(e)}"
        
    # @staticmethod
    # def get_me_meetingeShedule_licenses(token):  
    #     try:
    #         REDMINE_URL = os.getenv("REDMINE_URL")
    #         API_KEY = JWTUtils.get_api_key_from_token(token)

    #         if not REDMINE_URL or not API_KEY:
    #             return None, "Redmine URL or API Key is missing"

    #         # Step 2: Define query parameters for project_id=1 and tracker_id=4 (ML)
    #         params = {
    #             "project_id": 1,
    #             "tracker_id": 4,  # ML tracker ID
    #             "status_id": 31 
    #         }

    #         headers = {
    #             "X-Redmine-API-Key": API_KEY
    #         }

    #         # Make the Redmine request
    #         limit = LimitUtils.get_limit()
    #         response = requests.get(
    #             f"{REDMINE_URL}/projects/mmpro-gsmb/issues.json?offset=0&limit={limit}",
    #             params=params,
    #             headers=headers
    #         )

    #         # Check if the request was successful
    #         if response.status_code != 200:
    #             error_msg = f"Redmine API error: {response.status_code}"
    #             if response.text:
    #                 error_msg += f" - {response.text[:200]}"  # Truncate long error messages
    #             return None, error_msg

    #         data = response.json()
    #         issues = data.get("issues", [])

    #         processed_issues = []
    #         for issue in issues:
    #             # Process custom fields using IDs
    #             custom_fields = {field['id']: field['value']
    #                             for field in issue.get('custom_fields', [])
    #                             if field.get('value') and str(field.get('value')).strip()}

    #             attachment_urls = MiningEnginerService.get_attachment_urls(API_KEY, REDMINE_URL, issue.get("custom_fields", []))

    #             processed_issues.append({
    #                 "id": issue.get("id"),
    #                 "subject": issue.get("subject"),
    #                 "status": issue.get("status", {}).get("name"),
    #                 "assigned_to": issue.get("assigned_to", {}).get("name"),
    #                 "exploration_license_no": custom_fields.get(19),  # ID for "Exploration Licence No"
    #                 "Land_Name": custom_fields.get(28),  # ID for "Land Name(Licence Details)"
    #                 "Land_owner_name": custom_fields.get(29),  # ID for "Land owner name"
    #                 "Name_of_village": custom_fields.get(30),  # ID for "Name of village"
    #                 "Grama_Niladhari": custom_fields.get(31),  # ID for "Grama Niladhari Division"
    #                 "Divisional_Secretary_Division": custom_fields.get(32),  # ID for "Divisional Secretary Division"
    #                 "administrative_district": custom_fields.get(33),  # ID for "Administrative District"
    #                 "Capacity": custom_fields.get(34),  # ID for "Capacity"
    #                 "Mobile_Numbe": custom_fields.get(66),  # ID for "Mobile Number"
    #                 "Google_location": custom_fields.get(92),  # ID for "Google location"
    #                 "Detailed_Plan": attachment_urls.get("Detailed Mine Restoration Plan") or custom_fields.get(72),  # ID for "Detailed Mine Restoration Plan"
    #                 "Payment_Receipt": attachment_urls.get("Payment Receipt") or custom_fields.get(80),  # ID for "Payment Receipt"
    #                 "Deed_Plan": attachment_urls.get("Deed and Survey Plan") or custom_fields.get(90),  # ID for "Deed and Survey Plan"
    #             })

    #         return processed_issues, None

    #     except Exception as e:
    #         return None, f"Server error: {str(e)}"
    
    @staticmethod
    def get_me_meetingeShedule_licenses(token):  
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            # Step 1: Define query parameters
            params = {
                "project_id": 1,
                "tracker_id": 4,  # ML tracker ID
                "status_id": 31 
            }

            headers = {
                "X-Redmine-API-Key": API_KEY
            }

            # ✅ Use a fixed default limit
            limit = 100

            # Step 2: Make the Redmine request
            response = requests.get(
                f"{REDMINE_URL}/projects/mmpro-gsmb/issues.json",
                params={**params, "offset": 0, "limit": limit},
                headers=headers
            )

            # Step 3: Check response
            if response.status_code != 200:
                error_msg = f"Redmine API error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text[:200]}"  # Truncate long error messages
                return None, error_msg

            data = response.json()
            issues = data.get("issues", [])

            processed_issues = []
            for issue in issues:
                # Extract custom fields by ID
                custom_fields = {
                    field['id']: field['value']
                    for field in issue.get('custom_fields', [])
                    if field.get('value') and str(field.get('value')).strip()
                }

                attachment_urls = MiningEnginerService.get_attachment_urls(
                    API_KEY, REDMINE_URL, issue.get("custom_fields", [])
                )

                processed_issues.append({
                    "id": issue.get("id"),
                    "subject": issue.get("subject"),
                    "status": issue.get("status", {}).get("name"),
                    "assigned_to": issue.get("assigned_to", {}).get("name"),
                    "exploration_license_no": custom_fields.get(19),
                    "Land_Name": custom_fields.get(28),
                    "Land_owner_name": custom_fields.get(29),
                    "Name_of_village": custom_fields.get(30),
                    "Grama_Niladhari": custom_fields.get(31),
                    "Divisional_Secretary_Division": custom_fields.get(32),
                    "administrative_district": custom_fields.get(33),
                    "Capacity": custom_fields.get(34),
                    "Mobile_Numbe": custom_fields.get(66),
                    "Google_location": custom_fields.get(92),
                    "Detailed_Plan": attachment_urls.get("Detailed Mine Restoration Plan") or custom_fields.get(72),
                    "Payment_Receipt": attachment_urls.get("Payment Receipt") or custom_fields.get(80),
                    "Deed_Plan": attachment_urls.get("Deed and Survey Plan") or custom_fields.get(90),
                })

            return processed_issues, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def get_me_appointments(token):
        """Get all ME Appointments for the current mining engineer"""
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return {"error": "Redmine URL not configured"}

            api_key = JWTUtils.get_api_key_from_token(token)
            if not api_key:
                return {"error": "Invalid API token"}

            # user_info = MLOUtils.get_user_info_from_token(token)
            # if not user_info:
            #     return {"error": "Failed to get user info"}

            params = {
                "project_id": 1,
                "tracker_id": 12,  # ME Appointment tracker
                # "assigned_to_id": user_info["user_id"],
                "status_id": "open",  # Only show open appointments
                "limit": 100
            }

            response = requests.get(
                f"{REDMINE_URL}/issues.json",
                headers={"X-Redmine-API-Key": api_key},
                params=params,
                timeout=30
            )

            if response.status_code != 200:
                return {"error": f"Redmine API error: {response.status_code}"}

            appointments = []
            for issue in response.json().get("issues", []):
                appointments.append({
                    "id": issue.get("id"),
                    "subject": issue.get("subject"),
                    "start_date": issue.get("start_date"),
                    "status": issue.get("status", {}).get("name"),
                    "assigned_to": issue.get("assigned_to", {}).get("name"),
                    "Google_location": next(
                        (cf["value"] for cf in issue.get("custom_fields", []) 
                        if cf.get("id") == 92),
                        None
                    ),
                    "mining_number": next(
                        (cf["value"] for cf in issue.get("custom_fields", []) 
                        if cf.get("id") == 101),
                        None
                    )
                })

            return {"appointments": appointments}

        except Exception as e:
            return {"error": f"Server error: {str(e)}"}
        


    @staticmethod
    def get_me_approve_license(token):  
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            user_id, error = MLOUtils.get_user_info_from_token(token)
            if not user_id:
                return None, error

            headers = {
                "X-Redmine-API-Key": API_KEY
            }

            offset = 0
            processed_issues = []
            total_count = None

            while True:
                params = {
                    "project_id": 1,
                    "tracker_id": 4,  # ML tracker ID
                    "status_id": 32,  # Approved status
                    "offset": offset
                    # No limit specified → Redmine defaults to 25
                }

                response = requests.get(
                    f"{REDMINE_URL}/projects/mmpro-gsmb/issues.json",
                    params=params,
                    headers=headers
                )

                if response.status_code != 200:
                    error_msg = f"Redmine API error: {response.status_code}"
                    if response.text:
                        error_msg += f" - {response.text[:200]}"
                    return None, error_msg

                data = response.json()
                issues = data.get("issues", [])
                if total_count is None:
                    total_count = data.get("total_count", 0)

                for issue in issues:
                    custom_fields = {
                        field['id']: field['value']
                        for field in issue.get('custom_fields', [])
                        if field.get('value') and str(field.get('value')).strip()
                    }

                    attachment_urls = MiningEnginerService.get_attachment_urls(issue.get("custom_fields", []))

                    processed_issues.append({
                        "id": issue.get("id"),
                        "subject": issue.get("subject"),
                        "status": issue.get("status", {}).get("name"),
                        "assigned_to": issue.get("assigned_to", {}).get("name"),
                        "exploration_license_no": custom_fields.get(19),
                        "Land_Name": custom_fields.get(28),
                        "Land_owner_name": custom_fields.get(29),
                        "Name_of_village": custom_fields.get(30),
                        "Grama_Niladhari": custom_fields.get(31),
                        "Divisional_Secretary_Division": custom_fields.get(32),
                        "administrative_district": custom_fields.get(33),
                        "Capacity": custom_fields.get(34),
                        "Mobile_Numbe": custom_fields.get(66),
                        "Google_location": custom_fields.get(92),
                        "Detailed_Plan": attachment_urls.get("Detailed Mine Restoration Plan") or custom_fields.get(72),
                        "Payment_Receipt": attachment_urls.get("Payment Receipt") or custom_fields.get(80),
                        "Deed_Plan": attachment_urls.get("Deed and Survey Plan") or custom_fields.get(90),
                        "mining_license_number": custom_fields.get(101),
                    })

                offset += len(issues)
                if offset >= total_count or not issues:
                    break

            return processed_issues, None

        except Exception as e:
            return None, f"Server error: {str(e)}"


    @staticmethod
    def get_me_approve_single_license(token, issue_id):  
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return {"error": "Redmine URL or API Key is missing"}

        
            user_id, error = MLOUtils.get_user_info_from_token(token)
            if not user_id:
                return {"error": error}

            headers = {
                "X-Redmine-API-Key": API_KEY
            }


            response = requests.get(
                f"{REDMINE_URL}/issues/{issue_id}.json",
                headers=headers
            )


            if response.status_code != 200:
                error_msg = f"Redmine API error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text[:200]}"  # Truncate long error messages
                return {"error": error_msg}

            data = response.json()
            issue = data.get("issue", {})

       
            if issue.get("tracker", {}).get("id") != 4 or issue.get("project", {}).get("id") != 1:
                return {"error": "Issue not found or not a valid mining license"}

        
            custom_fields = {field['id']: field['value']
                            for field in issue.get('custom_fields', [])
                            if field.get('value') and str(field.get('value')).strip()}

            attachment_urls = MiningEnginerService.get_attachment_urls(API_KEY, REDMINE_URL, issue.get("custom_fields", []))

            processed_issue = {
                "id": issue.get("id"),
                "subject": issue.get("subject"),
                "status": issue.get("status", {}).get("name"),
                "assigned_to": issue.get("assigned_to", {}).get("name"),
                "exploration_license_no": custom_fields.get(19),
                "Land_Name": custom_fields.get(28),
                "Land_owner_name": custom_fields.get(29),
                "Name_of_village": custom_fields.get(30),
                "Grama_Niladhari": custom_fields.get(31),
                "Divisional_Secretary_Division": custom_fields.get(32),
                "administrative_district": custom_fields.get(33),
                "Capacity": custom_fields.get(34),
                "Mobile_Numbe": custom_fields.get(66),
                "Google_location": custom_fields.get(92),
                "Detailed_Plan": attachment_urls.get("Detailed Mine Restoration Plan") or custom_fields.get(72),
                "Payment_Receipt": attachment_urls.get("Payment Receipt") or custom_fields.get(80),
                "Deed_Plan": attachment_urls.get("Deed and Survey Plan") or custom_fields.get(90),
                "mining_license_number": custom_fields.get(101),
            }

            return processed_issue

        except Exception as e:

            return {"error": f"Server error: {str(e)}"}
        


    @staticmethod
    def get_me_licenses_count(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            # Step 1: Extract user_id from the token
            user_id, error = MLOUtils.get_user_info_from_token(token)
            if not user_id:
                return None, error

            # Step 2: Define query parameters for project_id=1 and tracker_id=4 (ML)
            params = {
                "project_id": 1,
                "tracker_id": 4,  # ML tracker ID
            }

            headers = {
                "X-Redmine-API-Key": API_KEY
            }

            # Pagination variables
            offset = 0
            limit = 100
            all_issues = []

            while True:
                paged_params = params.copy()
                paged_params.update({"offset": offset, "limit": limit})

                response = requests.get(
                    f"{REDMINE_URL}/projects/mmpro-gsmb/issues.json",
                    params=paged_params,
                    headers=headers
                )

                if response.status_code != 200:
                    error_msg = f"Redmine API error: {response.status_code}"
                    if response.text:
                        error_msg += f" - {response.text[:200]}"
                    return None, error_msg

                data = response.json()
                issues = data.get("issues", [])
                all_issues.extend(issues)

                if len(issues) < limit:
                    break

                offset += limit

            # Status ID to Name mapping
            status_map = {
                6: "Rejected",
                26: "Awaiting ME Scheduling",
                31: "ME Appointment Scheduled",
                32: "ME Approved"
            }
            valid_status_ids = set(status_map.keys())
            status_counts = {status_map[status_id]: 0 for status_id in valid_status_ids}

            for issue in all_issues:
                status_id = issue.get("status", {}).get("id")
                if status_id in valid_status_ids:
                    status_counts[status_map[status_id]] += 1

            return status_counts, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

            return {"error": f"Server error: {str(e)}"}         
        

    # @staticmethod
    # def set_license_hold(issue_id, reason_for_hold, token):
    #     try:
    #         user_api_key = JWTUtils.get_api_key_from_token(token)
    #         if not user_api_key:
    #             return False, "Invalid or missing API key in token"

    #         REDMINE_URL = os.getenv("REDMINE_URL")
    #         if not REDMINE_URL:
    #             return False, "Environment variable 'REDMINE_URL' is not set"

    #         # 1. Get the "Hold" status ID (assuming fixed or fetch dynamically)
    #         # You can hardcode the Hold status ID if fixed, here example 39 as per your data
    #         hold_status_id = 39

    #         # 2. Update the issue status to "Hold" and set the "Reason For Hold" custom field
    #         update_payload = {
    #             "issue": {
    #                 "status_id": hold_status_id,
    #                 "custom_fields": [
    #                     {
    #                         "id":106,
    #                         "value": reason_for_hold
    #                     }
    #                 ]
    #             }
    #         }

    #         response = requests.put(
    #             f"{REDMINE_URL}/issues/{issue_id}.json",
    #             json=update_payload,
    #             headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
    #         )

    #         if response.status_code not in [200, 204]:
    #             return False, f"Failed to update issue: {response.status_code} - {response.text}"

    #         return True, None

    #     except Exception as e:
    #         return False, f"Server error: {str(e)}"


    @staticmethod
    def set_license_hold(issue_id, reason_for_hold, token):
        try:
            user_api_key = JWTUtils.get_api_key_from_token(token)
            if not user_api_key:
                return False, "Invalid or missing API key in token"

            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return False, "Environment variable 'REDMINE_URL' is not set"

            # 1. Set current issue to Hold
            hold_status_id = 39
            update_payload = {
                "issue": {
                    "status_id": hold_status_id,
                    "custom_fields": [
                        {
                            "id": 106,  # Reason for hold
                            "value": reason_for_hold
                        }
                    ]
                }
            }

            response = requests.put(
                f"{REDMINE_URL}/issues/{issue_id}.json",
                json=update_payload,
                headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
            )

            if response.status_code not in [200, 204]:
                return False, f"Failed to update license issue: {response.status_code} - {response.text}"

            # 2. Construct the matching value used in MeAppointment
            license_ref_string = f"ML Request LLL/100/{issue_id}"

            # 3. Search MeAppointment issues with custom field "Mining License Number" = license_ref_string
            search_params = {
                "project_id": 1,
                "tracker_id": 12,  # MeAppointment tracker ID
                "status_id": "*",  # Get all statuses
                "cf_101": license_ref_string  # Custom field ID 101 = "Mining License Number"
            }

            search_response = requests.get(
                f"{REDMINE_URL}/issues.json",
                params=search_params,
                headers={"X-Redmine-API-Key": user_api_key}
            )

            if search_response.status_code != 200:
                return False, f"Failed to search MeAppointment: {search_response.status_code} - {search_response.text}"

            me_issues = search_response.json().get("issues", [])
            if not me_issues:
                return False, f"No MeAppointment issue found for license {license_ref_string}"

            # 4. Close the first matched MeAppointment (assumes one-to-one)
            me_appointment_id = me_issues[0]["id"]
            close_payload = {
                "issue": {
                    "status_id": 5  # Closed
                }
            }

            close_response = requests.put(
                f"{REDMINE_URL}/issues/{me_appointment_id}.json",
                json=close_payload,
                headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
            )

            if close_response.status_code not in [200, 204]:
                return False, f"Failed to close MeAppointment: {close_response.status_code} - {close_response.text}"

            return True, None

        except Exception as e:
            return False, f"Server error: {str(e)}"

    
    @staticmethod
    def get_me_hold_licenses(token):  
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            # user_id, error = MLOUtils.get_user_info_from_token(token)
            # if not user_id:
            #     return None, error

            headers = {
                "X-Redmine-API-Key": API_KEY
            }

            offset = 0
            processed_issues = []
            total_count = None  # unknown at first

            while True:
                params = {
                    "project_id": 1,
                    "tracker_id": 4,
                    "status_id": 39,
                    "offset": offset
                    # No limit → Redmine defaults to 25
                }

                response = requests.get(
                    f"{REDMINE_URL}/projects/mmpro-gsmb/issues.json",
                    params=params,
                    headers=headers
                )

                if response.status_code != 200:
                    error_msg = f"Redmine API error: {response.status_code}"
                    if response.text:
                        error_msg += f" - {response.text[:200]}"
                    return None, error_msg

                data = response.json()
                issues = data.get("issues", [])
                if total_count is None:
                    total_count = data.get("total_count", 0)

                for issue in issues:
                    custom_fields = {
                        field['id']: field['value']
                        for field in issue.get('custom_fields', [])
                        if field.get('value') and str(field.get('value')).strip()
                    }

                    attachment_urls = MiningEnginerService.get_attachment_urls(issue.get("custom_fields", []))

                    processed_issues.append({
                        "id": issue.get("id"),
                        "subject": issue.get("subject"),
                        "status": issue.get("status", {}).get("name"),
                        "assigned_to": issue.get("assigned_to", {}).get("name"),
                        "exploration_license_no": custom_fields.get(19),
                        "Land_Name": custom_fields.get(28),
                        "Land_owner_name": custom_fields.get(29),
                        "Name_of_village": custom_fields.get(30),
                        "Grama_Niladhari": custom_fields.get(31),
                        "Divisional_Secretary_Division": custom_fields.get(32),
                        "administrative_district": custom_fields.get(33),
                        "Capacity": custom_fields.get(34),
                        "Mobile_Numbe": custom_fields.get(66),
                        "Google_location": custom_fields.get(92),
                        "Mining_license_Number": custom_fields.get(101),
                        "hold": custom_fields.get(106),
                        "Detailed_Plan": attachment_urls.get("Detailed Mine Restoration Plan") or custom_fields.get(72),
                        "Payment_Receipt": attachment_urls.get("Payment Receipt") or custom_fields.get(80),
                        "Deed_Plan": attachment_urls.get("Deed and Survey Plan") or custom_fields.get(90),
                    })

                offset += len(issues)  # move to next page
                if offset >= total_count or not issues:
                    break

            return processed_issues, None

        except Exception as e:
            return None, f"Server error: {str(e)}"


    @staticmethod
    def get_miningLicense_view_button(token, issue_id):
        try:
            
            api_key = JWTUtils.get_api_key_from_token(token)
            if not api_key:
                return None, "Invalid or missing API key"

            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "REDMINE_URL environment variable not set"

            issue_url = f"{REDMINE_URL}/issues/{issue_id}.json?include=attachments"
            response = requests.get(
                issue_url,
                headers={"X-Redmine-API-Key": api_key, "Content-Type": "application/json"}
            )

            if response.status_code != 200:
                return None, f"Failed to fetch issue: {response.status_code} - {response.text}"

            issue = response.json().get("issue")
            if not issue:
                return None, "Issue data not found"

            custom_fields = issue.get("custom_fields", [])
            custom_field_map = {field["name"]: field.get("value") for field in custom_fields}

            attachments = MiningEnginerService.get_attachment_urls(custom_fields)   

            print("custom_field_map:", custom_field_map)

            formatted_issue = {
                "id": issue.get("id"),
                "subject": issue.get("subject"),
                "start_date": issue.get("start_date"),
                "due_date": issue.get("due_date"),
                "status": issue.get("status", {}).get("name"),
                "assigned_to": issue.get("assigned_to", {}).get("name"),
                "land_name": custom_field_map.get("Land Name(Licence Details)"),
                "land_owner_name": custom_field_map.get("Land owner name"),
                "village_name": custom_field_map.get("Name of village "),
                "google_location": custom_field_map.get("Google location "),
                "grama_niladhari_division": custom_field_map.get("Grama Niladhari Division"),
                "capacity": custom_field_map.get("Capacity"),
                "used": custom_field_map.get("Used"),
                "remaining": custom_field_map.get("Remaining"),
                "exploration_licence_no": custom_field_map.get("Exploration Licence No"),
                "royalty": custom_field_map.get("Royalty"),
                "divisional_secretary_division": custom_field_map.get("Divisional Secretary Division"),
                "administrative_district": custom_field_map.get("Administrative District"),
                "mining_license_number": custom_field_map.get("Mining License Number"),
                "mobile_number": custom_field_map.get("Mobile Number"),
                "economic_viability_report": attachments.get("Economic Viability Report"),
                "license_fee_receipt": attachments.get("License fee receipt"),
                "detailed_mine_restoration_plan": attachments.get("Detailed Mine Restoration Plan"),
                "deed_and_survey_plan": attachments.get("Deed and Survey Plan"),
                "payment_receipt": attachments.get("Payment Receipt"),
                "license_boundary_survey": attachments.get("License Boundary Survey")
            }

            return formatted_issue, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def get_attachment_urls(custom_fields):
        try:
            upload_field_names = {
                "Economic Viability Report",
                "Detailed Mine Restoration Plan",
                "Professional",
                "Deed and Survey Plan",
                "License Boundary Survey",
                "Payment Receipt"
            }

            file_urls = {}

            for field in custom_fields:
                field_name = field.get("name")
                raw_value = field.get("value")

                if field_name not in upload_field_names:
                    continue

                if not raw_value:
                    file_urls[field_name] = None
                    continue

                attachment_id = str(raw_value).strip()
                file_urls[field_name] = int(attachment_id) if attachment_id.isdigit() else None

            return file_urls

        except Exception as e:
            print(f"[ERROR] Failed to get attachment IDs: {str(e)}")
            return {}
        

    @staticmethod
    def get_me_reject_licenses(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            headers = {"X-Redmine-API-Key": API_KEY}
            params = {"project_id": 1, "tracker_id": 4, "offset": 0, "limit": 100}
            all_issues = []

            while True:
                response = requests.get(
                    f"{REDMINE_URL}/projects/mmpro-gsmb/issues.json",
                    params=params,
                    headers=headers
                )

                if response.status_code != 200:
                    return None, f"Redmine API error: {response.status_code} - {response.text[:200]}"

                data = response.json()
                issues = data.get("issues", [])
                all_issues.extend(issues)

                if len(issues) < params["limit"]:
                    break

                params["offset"] += params["limit"]

            processed_issues = []
            for issue in all_issues:
                if issue.get("status", {}).get("id") != 6:
                    continue

                custom_fields = {
                    field['id']: field['value']
                    for field in issue.get('custom_fields', [])
                    if str(field.get('value', '')).strip()
                }

                attachment_urls = MiningEnginerService.get_attachment_urls(
                     issue.get("custom_fields", [])
                )

                processed_issues.append({
                    "id": issue.get("id"),
                    # "subject": issue.get("subject"),
                    "status": issue.get("status", {}).get("name"),
                    "assigned_to": issue.get("assigned_to", {}).get("name"),
                    # "exploration_license_no": custom_fields.get(19),
                    # "Land_Name": custom_fields.get(28),
                    # "Land_owner_name": custom_fields.get(29),
                    # "Name_of_village": custom_fields.get(30),
                    # "Grama_Niladhari": custom_fields.get(31),
                    # "Divisional_Secretary_Division": custom_fields.get(32),
                    # "administrative_district": custom_fields.get(33),
                    # "Capacity": custom_fields.get(34),
                    # "Mobile_Numbe": custom_fields.get(66),
                    "Google_location": custom_fields.get(92),
                    # "Detailed_Plan": int(custom_fields.get(72)),
                    # "Payment_Receipt":int(custom_fields.get(80)),
                    # "Deed_Plan": int(custom_fields.get(90)),
                    # "License Boundary Survey":int(custom_fields.get(105)),
                    # "Economic Viability Report":int(custom_fields.get(100)),
                    "mining_number": custom_fields.get(101),
                })

            return processed_issues, None

        except Exception as e:
            return None, f"Server error: {str(e)}"
    