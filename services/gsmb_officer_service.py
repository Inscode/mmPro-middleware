import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from utils.jwt_utils import JWTUtils
from utils.MLOUtils import MLOUtils
from flask import request

from utils.limit_utils import LimitUtils

load_dotenv()

class GsmbOfficerService:

    ORS_API_KEY = os.getenv("ORS_API_KEY")
    
    @staticmethod
    def get_mlowners(token):
        try:
            # 🔑 Extract user's API key from token for memberships request
            user_api_key = JWTUtils.get_api_key_from_token(token)
            print(user_api_key)
            if not user_api_key:
                return None, "Invalid or missing API key in the token"

            # 🔑 Get Redmine Admin API key for user details request
            admin_api_key = os.getenv("REDMINE_ADMIN_API_KEY")
            if not admin_api_key:
                return None, "Environment variable 'REDMINE_ADMIN_API_KEY' is not set"

            # 🌐 Get Redmine URL
            REDMINE_URL = os.getenv("REDMINE_URL")

            if not REDMINE_URL:
                return None, "Environment variable 'REDMINE_URL' is not set"

            # 1️⃣ Fetch memberships using the **user's API key**
            memberships_url = f"{REDMINE_URL}/projects/mmpro-gsmb/memberships.json"
            memberships_response = requests.get(
                memberships_url, 
                headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
            )

            if memberships_response.status_code != 200:
                return None, f"Failed to fetch memberships: {memberships_response.status_code} - {memberships_response.text}"

            memberships = memberships_response.json().get("memberships", [])

            # 2️⃣ Filter users who have the role "MLOwner"
            ml_owner_ids = [
                membership['user']['id'] for membership in memberships
                if any(role["name"] == "MLOwner" for role in membership.get("roles", []))
            ]

            if not ml_owner_ids:
                return [], None  # No MLOwner users found

            # 3️⃣ Fetch user details using the **admin API key** (for broader access)
            users_url = f"{REDMINE_URL}/users.json?status=1&limit=100"
            users_response = requests.get(
                users_url, 
                headers={"X-Redmine-API-Key": admin_api_key, "Content-Type": "application/json"}
            )

            if users_response.status_code != 200:
                return None, f"Failed to fetch user details: {users_response.status_code} - {users_response.text}"

            all_users = users_response.json().get("users", [])

            # 4️⃣ Filter users who match MLOwner IDs
            ml_owners_details = [
                user for user in all_users if user["id"] in ml_owner_ids
            ]

            # Fetch the mining license counts for all users
            license_counts, license_error = GsmbOfficerService.get_mining_license_counts(token)
            if license_error:
                return None, license_error

            # 5️⃣ Map license count to each MLOwner
            formatted_ml_owners = []
            for ml_owner in ml_owners_details:
                owner_name = f"{ml_owner.get('firstname', '')} {ml_owner.get('lastname', '')}"
                ml_owner_name = owner_name.strip()
                license_count = license_counts.get(ml_owner_name, 0)

                # Prepare formatted output
                formatted_owner = {
                    "id": ml_owner["id"],
                    "ownerName": ml_owner_name,
                    "NIC": next((field["value"] for field in ml_owner.get("custom_fields", []) if field["name"] == "National Identity Card"), ""),
                    "email": ml_owner.get("mail", ""),
                    "phoneNumber": next((field["value"] for field in ml_owner.get("custom_fields", []) if field["name"] == "Mobile Number"), ""),
                    "totalLicenses": license_count
                }
                
                formatted_ml_owners.append(formatted_owner)

            return formatted_ml_owners, None  # ✅ Return the formatted user details with license count

        except Exception as e:
            return None, f"Server error: {str(e)}"
        

#         @staticmethod
# def get_mlowners(token):
#     try:
#         # 🔑 Extract user's API key from token for memberships request
#         user_api_key = JWTUtils.get_api_key_from_token(token)
#         print(user_api_key)
#         if not user_api_key:
#             return None, "Invalid or missing API key in the token"

#         # 🔑 Get Redmine Admin API key for user details request
#         admin_api_key = os.getenv("REDMINE_ADMIN_API_KEY")
#         if not admin_api_key:
#             return None, "Environment variable 'REDMINE_ADMIN_API_KEY' is not set"

#         # 🌐 Get Redmine URL
#         REDMINE_URL = os.getenv("REDMINE_URL")
#         print(REDMINE_URL)
#         if not REDMINE_URL:
#             return None, "Environment variable 'REDMINE_URL' is not set"

#         # 1️⃣ Fetch memberships using the **user's API key**
#         memberships_url = f"{REDMINE_URL}/projects/mmpro-gsmb/memberships.json"
#         memberships_response = requests.get(
#             memberships_url, 
#             headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
#         )

#         if memberships_response.status_code != 200:
#             return None, f"Failed to fetch memberships: {memberships_response.status_code} - {memberships_response.text}"

#         memberships = memberships_response.json().get("memberships", [])

#         # 2️⃣ Filter users who have the role "MLOwner"
#         ml_owner_ids = [
#             membership['user']['id'] for membership in memberships
#             if any(role["name"] == "MLOwner" for role in membership.get("roles", []))
#         ]

#         if not ml_owner_ids:
#             return [], None  # No MLOwner users found

#         # 3️⃣ Fetch user details using the **admin API key** (for broader access)
#         users_url = f"{REDMINE_URL}/users.json?status=1&limit=100"
#         users_response = requests.get(
#             users_url, 
#             headers={"X-Redmine-API-Key": admin_api_key, "Content-Type": "application/json"}
#         )

#         if users_response.status_code != 200:
#             return None, f"Failed to fetch user details: {users_response.status_code} - {users_response.text}"

#         all_users = users_response.json().get("users", [])

#         # 4️⃣ Filter users who match MLOwner IDs AND have User Type = mlOwner
#         ml_owners_details = [
#             user for user in all_users 
#             if user["id"] in ml_owner_ids and 
#                any(field["name"] == "User Type" and field["value"] == "mlOwner" 
#                    for field in user.get("custom_fields", []))
#         ]

#         # Fetch the mining license counts for all users
#         license_counts, license_error = GsmbOfficerService.get_mining_license_counts(token)
#         if license_error:
#             return None, license_error

#         # 5️⃣ Map license count to each MLOwner
#         formatted_ml_owners = []
#         for ml_owner in ml_owners_details:
#             owner_name = f"{ml_owner.get('firstname', '')} {ml_owner.get('lastname', '')}"
#             ml_owner_name = owner_name.strip()
#             license_count = license_counts.get(ml_owner_name, 0)

#             # Prepare formatted output
#             formatted_owner = {
#                 "id": ml_owner["id"],
#                 "ownerName": ml_owner_name,
#                 "NIC": next((field["value"] for field in ml_owner.get("custom_fields", []) if field["name"] == "National Identity Card"), ""),
#                 "email": ml_owner.get("mail", ""),
#                 "phoneNumber": next((field["value"] for field in ml_owner.get("custom_fields", []) if field["name"] == "Mobile Number"), ""),
#                 "totalLicenses": license_count
#             }
            
#             formatted_ml_owners.append(formatted_owner)
#             print(formatted_owner["totalLicenses"])

#         return formatted_ml_owners, None  # ✅ Return the formatted user details with license count

#     except Exception as e:
#         return None, f"Server error: {str(e)}"

    @staticmethod
    def get_tpls(token):
        try:
            # 🔑 Extract user's API key from token
            user_api_key = JWTUtils.get_api_key_from_token(token)
            if not user_api_key:
                return None, "Invalid or missing API key in the token"

            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Environment variable 'REDMINE_URL' is not set"

            # 🚀 Fetch TPL issues from Redmine
            tpl_issues_url = f"{REDMINE_URL}/issues.json?tracker_id=5&project_id=1"
            response = requests.get(
                tpl_issues_url,
                headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
            )

            if response.status_code != 200:
                return None, f"Failed to fetch TPL issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])
            formatted_tpls = []

            for issue in issues:
                formatted_tpl = {
                    "id": issue.get("id"),
                    "subject": issue.get("subject"),
                    "status": issue.get("status", {}).get("name"),
                    "author": issue.get("author", {}).get("name"),
                    "tracker": issue.get("tracker", {}).get("name"),
                    "assigned_to": issue.get("assigned_to", {}).get("name") if issue.get("assigned_to") else None,
                    "start_date": issue.get("start_date"),
                    "due_date": issue.get("due_date"),
                    "lorry_number": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Lorry Number"),
                    "driver_contact": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Driver Contact"),
                    "cubes": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Cubes"),
                    "mining_license_number": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Mining License Number"),
                    "destination": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Destination"),
                    "lorry_driver_name": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Lorry Driver Name"),
                
                }
                formatted_tpls.append(formatted_tpl)

            return formatted_tpls, None

        except Exception as e:
            return None, f"Server error: {str(e)}"
        
    @staticmethod
    def get_mining_licenses(token):
        try:
            # 🔑 Extract user's API key from token
            user_api_key = JWTUtils.get_api_key_from_token(token)
            if not user_api_key:
                return None, "Invalid or missing API key in the token"

            # 🌐 Get Redmine URL
            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Environment variable 'REDMINE_URL' is not set"

            # 🚀 Fetch all ML issues from Redmine
            ml_issues_url = f"{REDMINE_URL}/issues.json?tracker_id=4&project_id=1&status_id=7"
            response = requests.get(
                ml_issues_url,
                headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
            )

            if response.status_code != 200:
                return None, f"Failed to fetch ML issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])
            formatted_mls = []

            for issue in issues:
                issue_id = issue.get("id")
                
                # Fetching attachments separately
                custom_fields = issue.get("custom_fields", [])  # Extract custom fields
                attachment_urls = GsmbOfficerService.get_attachment_urls(user_api_key, REDMINE_URL, custom_fields)


                formatted_ml = {
                    "id": issue_id,
                    "subject": issue.get("subject"),
                    "status": issue.get("status", {}).get("name"),
                    "author": issue.get("author", {}).get("name"),
                    "assigned_to": issue.get("assigned_to", {}).get("name") if issue.get("assigned_to") else None,
                    "start_date": issue.get("start_date"),
                    "due_date": issue.get("due_date"),
                    "exploration_licence_no": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Exploration Licence No"),
                    "applicant_or_company_name": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Name of Applicant OR Company"),
                    "land_name": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Land Name(Licence Details) "),
                    "land_owner_name": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Land owners’ name"),
                    "village_name": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Name of village "),
                    "grama_niladhari_division": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Grama Niladhari Division"),
                    "divisional_secretary_division": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Divisional Secretary Division"),
                    "administrative_district": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Administrative District"),
                    "capacity": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Capacity"),
                    "used": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Used"),
                    "remaining": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Remaining"),
                    "mobile_number": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Mobile Number"),
                    "royalty": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Royalty"),
                    
                    # Fetching File URLs from Attachments API
                    "economic_viability_report": attachment_urls.get("Economic Viability Report"),
                    "license_fee_receipt": attachment_urls.get("License fee receipt"),
                    "detailed_mine_restoration_plan": attachment_urls.get("Detailed Mine Restoration Plan"),
                    "professional": attachment_urls.get("Professional"),
                    "deed and survey plan": attachment_urls.get("Deed and Survey Plan"),
                    "payment_receipt": attachment_urls.get("Payment Receipt"),
                }

                formatted_mls.append(formatted_ml)
 
            return formatted_mls, None

        except Exception as e:
            return None, f"Server error: {str(e)}"


    @staticmethod
    def get_mining_license_requests(token):
        try:
            user_api_key = JWTUtils.get_api_key_from_token(token)
            if not user_api_key:
                return None, "Invalid or missing API key in the token"

            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Environment variable 'REDMINE_URL' is not set"

            ml_issues_url = f"{REDMINE_URL}/issues.json?tracker_id=4&project_id=1"
            response = requests.get(
                ml_issues_url,
                headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
            )

            if response.status_code != 200:
                return None, f"Failed to fetch ML issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])

            formatted_mls = []

            for issue in issues:
                custom_fields = issue.get("custom_fields", [])
                attachment_urls = GsmbOfficerService.get_attachment_urls(user_api_key, REDMINE_URL, custom_fields)

                # Fetch assigned_to user details
                assigned_to = issue.get("assigned_to", {})
                assigned_to_id = assigned_to.get("id")
                assigned_to_details = None

                if assigned_to_id:
                    user_response = requests.get(
                        f"{REDMINE_URL}/users/{assigned_to_id}.json",
                        headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
                    )
                    if user_response.status_code == 200:
                        assigned_to_details = user_response.json().get("user", {})

                ml_data = {
                    "id": issue.get("id"),
                    "subject": issue.get("subject"),
                    "status": issue.get("status", {}).get("name"),
                    "assigned_to": assigned_to.get("name"),
                    "created_on": issue.get("created_on"),
                    "assigned_to_details": {
                        "id": assigned_to_details.get("id"),
                        "name": f"{assigned_to_details.get('firstname', '')} {assigned_to_details.get('lastname', '')}".strip(),
                        "email": assigned_to_details.get("mail"),
                        "custom_fields": assigned_to_details.get("custom_fields", [])
                    } if assigned_to_details else None,
                    "exploration_licence_no": GsmbOfficerService.get_custom_field_value(custom_fields, "Exploration Licence No"),
                    "land_name": GsmbOfficerService.get_custom_field_value(custom_fields, "Land Name(Licence Details)"),
                    "land_owner_name": GsmbOfficerService.get_custom_field_value(custom_fields, "Land owner name"),
                    "village_name": GsmbOfficerService.get_custom_field_value(custom_fields, "Name of village "),
                    "grama_niladhari_division": GsmbOfficerService.get_custom_field_value(custom_fields, "Grama Niladhari Division"),
                    "divisional_secretary_division": GsmbOfficerService.get_custom_field_value(custom_fields, "Divisional Secretary Division"),
                    "administrative_district": GsmbOfficerService.get_custom_field_value(custom_fields, "Administrative District"),
                    "google_location": GsmbOfficerService.get_custom_field_value(custom_fields, "Google location "),
                    "mobile_number": GsmbOfficerService.get_custom_field_value(custom_fields, "Mobile Number"),
                   # "economic_viability_report": attachment_urls.get("Economic Viability Report"),
                    "detailed_mine_restoration_plan": attachment_urls.get("Detailed Mine Restoration Plan"),
                    "deed_and_survey_plan": attachment_urls.get("Deed and Survey Plan"),
                    "payment_receipt": attachment_urls.get("Payment Receipt"),
                }

                # Remove keys with None values
                formatted_mls.append(ml_data)

            return formatted_mls, None

        except Exception as e:
            return None, f"Server error: {str(e)}"


    @staticmethod
    def get_complaints(token):
        try:
            # 🔑 Extract user's API key from token
            user_api_key = JWTUtils.get_api_key_from_token(token)
            if not user_api_key:
                return None, "Invalid or missing API key in the token"

            # 🌐 Get Redmine URL
            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Environment variable 'REDMINE_URL' is not set"

            # 🚀 Fetch Complaint issues
            complaints_url = f"{REDMINE_URL}/issues.json?tracker_id=6&project_id=1"
            response = requests.get(
                complaints_url,
                headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
            )

            if response.status_code != 200:
                return None, f"Failed to fetch complaint issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])
            formatted_complaints = []

            for issue in issues:
                custom_fields = issue.get("custom_fields", [])

                # Extract Lorry Number and Mobile Number from custom fields
                lorry_number = None
                mobile_number = None

                for field in custom_fields:
                    if field.get("name") == "Lorry Number":
                        lorry_number = field.get("value")
                    elif field.get("name") == "Mobile Number":
                        mobile_number = field.get("value")

                # 🛠️ Format complaint_date
                created_on = issue.get("created_on")
                complaint_date = None
                if created_on:
                    try:
                        # Parse ISO datetime and format it
                        dt = datetime.strptime(created_on, "%Y-%m-%dT%H:%M:%SZ")
                        complaint_date = dt.strftime("%Y-%m-%d %H:%M:%S")  # 👈 this adds the space
                    except Exception as e:
                        complaint_date = created_on  # fallback if parsing fails

                formatted_complaint = {
                    "id": issue.get("id"), 
                    "lorry_number": lorry_number,
                    "mobile_number": mobile_number,
                    "complaint_date": complaint_date,
                }
                formatted_complaints.append(formatted_complaint)

            return formatted_complaints, None

        except Exception as e:
            return None, str(e)


    @staticmethod
    def get_attachment_urls(api_key, redmine_url, custom_fields):
        try:
            # Define the mapping of custom field names to their attachment IDs
            file_fields = {
                "Economic Viability Report": None,
                "License fee receipt": None,
                "Detailed Mine Restoration Plan": None,
                "Professional": None,
                "Deed and Survey Plan": None,
                "Payment Receipt": None
            }

            # Extract attachment IDs from custom fields
            for field in custom_fields:
                field_name = field.get("name")
                attachment_id = field.get("value")

                if field_name in file_fields and attachment_id.isdigit():
                    file_fields[field_name] = attachment_id

            # Fetch URLs for valid attachment IDs
            file_urls = {}
            for field_name, attachment_id in file_fields.items():
                if attachment_id:
                    attachment_url = f"{redmine_url}/attachments/{attachment_id}.json"
                    response = requests.get(
                        attachment_url,
                        headers={"X-Redmine-API-Key": api_key, "Content-Type": "application/json"}
                    )

                    if response.status_code == 200:
                        attachment_data = response.json().get("attachment", {})
                        file_urls[field_name] = attachment_data.get("content_url", "")

            return file_urls

        except Exception as e:
            return {}


    @staticmethod
    def get_custom_field_value(custom_fields, field_name):
        """Helper function to extract custom field value by name."""
        for field in custom_fields:
            if field.get("name") == field_name:
                return field.get("value")
        return None
    
    @staticmethod
    def get_mining_license_counts(token):
        try:
            # 🔑 Extract user's API key from token
            user_api_key = JWTUtils.get_api_key_from_token(token)
            if not user_api_key:
                return None, "Invalid or missing API key in the token"

            # 🌐 Get Redmine URL
            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Environment variable 'REDMINE_URL' is not set"

            # 🚀 Fetch ML issues from Redmine
            ml_issues_url = f"{REDMINE_URL}/issues.json?tracker_id=4&project_id=1"
            response = requests.get(
                ml_issues_url,
                headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
            )

            if response.status_code != 200:
                return None, f"Failed to fetch ML issues: {response.status_code} - {response.text}"

            # 🛠️ Process the response
            issues = response.json().get("issues", [])
            license_counts = {}

            for issue in issues:
                assigned_to = issue.get("assigned_to", {}).get("name", "Unassigned")  # Handle unassigned cases
                license_counts[assigned_to] = license_counts.get(assigned_to, 0) + 1

            return license_counts, None

        except Exception as e:
            return None, f"Server error: {str(e)}"
        
    @staticmethod
    def upload_file_to_redmine(file):
        print("inside file upload")
        """
        Uploads a file to Redmine and returns the attachment ID.
        """
        REDMINE_URL = os.getenv("REDMINE_URL")
        admin_api_key = os.getenv("REDMINE_ADMIN_API_KEY")
        

        url = f"{REDMINE_URL}/uploads.json?filename={file.filename}"

        headers = {
            "X-Redmine-API-Key": admin_api_key,
            "Content-Type":"application/octet-stream",
            "Accept": "application/json"
        }


        response = requests.post(url, headers=headers, data=file.stream)

        if response.status_code == 201:
             return response.json().get("upload", {}).get("id")   # Attachment ID
        else:
            return None  # Handle failed upload


    @staticmethod
    def upload_mining_license(token, data):
        try:
            # Map custom field IDs from your tracker
            custom_fields = [
                        {"id": 19, "value": data.get("exploration_licence_no")},
                        {"id": 28, "value": data.get("land_name")},
                        {"id": 30, "value": data.get("village_name")},
                        {"id": 31, "value": data.get("grama_niladhari_division")},
                        {"id": 32, "value": data.get("divisional_secretary_division")},
                        {"id": 33, "value": data.get("administrative_district")},
                        {"id": 66, "value": data.get("mobile_number")},
                        {"id": 29, "value": data.get("land_owner_name")},
                        {"id": 18, "value": data.get("royalty")},
                        {"id": 34, "value": data.get("capacity")},
                        {"id": 63, "value": data.get("used")},
                        {"id": 64, "value": data.get("remaining")},
                        {"id": 92, "value": data.get("google_location")},
                        {"id": 101, "value": data.get("mining_license_number")},
                        {"id": 99, "value": data.get("month_capacity")},
                    ]
            # Attachments (file tokens if present)
            file_field_ids = {
                "economic_viability_report": 70,
                "detailed_mine_restoration_plan": 72,
                "deed_and_survey_plan":90,
                "payment_receipt": 80,
                # "license_fee_receipt": 81  # example if you've added this to tracker
            }

            for key, field_id in file_field_ids.items():
                if data.get(key):
                    custom_fields.append({
                        "id": field_id,
                        "value": data[key]
                    })

            assignee_id = int(data["assignee_id"]) if data.get("assignee_id") else None

            # Prepare issue payload
            issue_payload = {
                "issue": {
                    "project_id": 1,
                    "tracker_id": 4,
                    "subject": data["subject"],
                    "start_date": data["start_date"],
                    "due_date": data["due_date"],
                    "status_id": 7,  
                    "description": f"Mining license submitted by {data.get('author', 'GSMB Officer')}",
                    "assigned_to_id":assignee_id,
                    "custom_fields": custom_fields
                }
            }

            user_api_key = JWTUtils.get_api_key_from_token(token)

            headers = {
                "X-Redmine-API-Key": user_api_key,
                "Content-Type": "application/json"
            }

            REDMINE_URL = os.getenv("REDMINE_URL")
            
            response = requests.post(
                f"{REDMINE_URL}/issues.json",  # Use formatted string
                headers=headers,
                json=issue_payload
            )

            if response.status_code == 201:
                issue_id = response.json()["issue"]["id"]

                # Now, update the Mining License Number field with LLL/100/{issue_id}
                update_payload = {
                    "issue": {
                        "custom_fields": [
                            {
                                "id": 101,  # Mining License Number field ID
                                "value": f"LLL/100/{issue_id}"
                            }
                        ]
                    }
                }

                update_response = requests.put(
                    f"{REDMINE_URL}/issues/{issue_id}.json",
                    headers=headers,
                    json=update_payload
                )

                if update_response.status_code == 204:
                    return True, None
                else:
                    return False, f"Failed to update Mining License Number: {update_response.status_code} - {update_response.text}"

            else:
                return False, f"Redmine issue creation failed: {response.status_code} - {response.text}"

        except Exception as e:
            return False, str(e)

    @staticmethod    
    def get_mlownersDetails(token):
        try:
            user_api_key = JWTUtils.get_api_key_from_token(token)
            if not user_api_key:
                return None, "Invalid or missing API key in the token"

            admin_api_key = os.getenv("REDMINE_ADMIN_API_KEY")
            if not admin_api_key:
                return None, "Environment variable 'REDMINE_ADMIN_API_KEY' is not set"

            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Environment variable 'REDMINE_URL' is not set"

            memberships_url = f"{REDMINE_URL}/projects/mmpro-gsmb/memberships.json"
            memberships_response = requests.get(
                memberships_url,
                headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
            )

            if memberships_response.status_code != 200:
                return None, f"Failed to fetch memberships: {memberships_response.status_code} - {memberships_response.text}"

            memberships = memberships_response.json().get("memberships", [])
            ml_owner_ids = [
                membership['user']['id'] for membership in memberships
                if any(role["name"] == "MLOwner" for role in membership.get("roles", []))
            ]

            if not ml_owner_ids:
                return [], None

            users_url = f"{REDMINE_URL}/users.json?status=1&limit=100"
            users_response = requests.get(
                users_url,
                headers={"X-Redmine-API-Key": admin_api_key, "Content-Type": "application/json"}
            )

            if users_response.status_code != 200:
                return None, f"Failed to fetch user details: {users_response.status_code} - {users_response.text}"

            all_users = users_response.json().get("users", [])

            ml_owners_details = [
                user for user in all_users if user["id"] in ml_owner_ids
            ]

            formatted_ml_owners = []
            for ml_owner in ml_owners_details:
                owner_name = f"{ml_owner.get('firstname', '')} {ml_owner.get('lastname', '')}".strip()
                nic = next(
                    (field["value"] for field in ml_owner.get("custom_fields", [])
                    if field["name"] == "National Identity Card"),
                    ""
                )

                formatted_owner = {
                    "id": ml_owner["id"],
                    "ownerName": owner_name,
                    "NIC": nic
                }

                formatted_ml_owners.append(formatted_owner)

            return formatted_ml_owners, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def get_appointments(token):
        try:
            user_api_key = JWTUtils.get_api_key_from_token(token)
            if not user_api_key:
                return None, "Invalid or missing API key in the token"

            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Environment variable 'REDMINE_URL' is not set"

            # 🔁 Tracker ID for Appointment = 11
            appointment_issues_url = f"{REDMINE_URL}/issues.json?tracker_id=11&project_id=1"
            response = requests.get(
                appointment_issues_url,
                headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
            )

            if response.status_code != 200:
                return None, f"Failed to fetch appointment issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])
            formatted_appointments = []

            for issue in issues:
                formatted_appointment = {
                    "id": issue.get("id"),
                    "subject": issue.get("subject"),
                    "status": issue.get("status", {}).get("name"),
                    "author": issue.get("author", {}).get("name"),
                    "tracker": issue.get("tracker", {}).get("name"),
                    "assigned_to": issue.get("assigned_to", {}).get("name") if issue.get("assigned_to") else None,
                    "start_date": issue.get("start_date"),
                    "due_date": issue.get("due_date"),
                    "description": issue.get("description"),
                    "mining_license_number": GsmbOfficerService.get_custom_field_value(issue.get("custom_fields", []), "Mining License Number")
                }
                formatted_appointments.append(formatted_appointment)

            return formatted_appointments, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

 
    @staticmethod
    def create_appointment(token, assigned_to_id, physical_meeting_location, start_date, description):
        try:
            user_api_key = JWTUtils.get_api_key_from_token(token)
            author_id = JWTUtils.decode_jwt_and_get_user_id(token)

            if not user_api_key or not author_id:
                return None, "Invalid or missing API key or user ID"

            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Environment variable 'REDMINE_URL' is not set"

            issue_payload = {
                "issue": {
                    "project_id": 1,
                    "tracker_id": 11,  # Appointment tracker
                    "status_id": 34,    # Default to 'New' or use your desired status ID
                    "assigned_to_id": int(assigned_to_id),
                    "author_id": author_id,
                    "subject": "Appointment",
                    "description": description,
                    "start_date": start_date,
                    "custom_fields": [
                        {
                            "id": 102,  # Replace with actual ID for "Mining License Number"
                            "value": physical_meeting_location,
                        }
                    ]
                }
            }

            response = requests.post(
                f"{REDMINE_URL}/issues.json",
                headers={
                    "X-Redmine-API-Key": user_api_key,
                    "Content-Type": "application/json"
                },
                data=json.dumps(issue_payload)
            )

            if response.status_code != 201:
                return None, f"Failed to create appointment: {response.status_code} - {response.text}"

            issue_id = response.json().get("issue", {}).get("id")
            return issue_id, None

        except Exception as e:
            return None, f"Server error: {str(e)}"
        
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
