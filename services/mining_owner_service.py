# from typing import Dict, List, Optional, Tuple
# import requests
# import os
# from dotenv import load_dotenv
# import json
# from datetime import date, timedelta , datetime 
# from services.general_public_service import GeneralPublicService
# from utils.jwt_utils import JWTUtils
# from utils.MLOUtils import MLOUtils
# from flask import request
# from utils.limit_utils import LimitUtils
# from werkzeug.utils import secure_filename
# import time
# from hashlib import md5

# load_dotenv()

# class MLOwnerService:

#     ORS_API_KEY = os.getenv("ORS_API_KEY")
    

#     @staticmethod
#     def mining_licenses(token):
#         try:
#             REDMINE_URL = os.getenv("REDMINE_URL")
#             API_KEY = JWTUtils.get_api_key_from_token(token)

#             if not REDMINE_URL or not API_KEY:
#                 return None, "Redmine URL or API Key is missing"

#             result = JWTUtils.decode_jwt_and_get_user_id(token)
#             if not result['success']:
#                 return None, result['message']

#             user_id = result['user_id']

#             headers = {
#                 "X-Redmine-API-Key": API_KEY,
#                 "Content-Type": "application/json"
#             }

#             offset = 0
#             relevant_issues = []
#             total_count = None

#             while True:
#                 params = {
#                     "project_id": 1,
#                     "tracker_id": 4,
#                     "status_id": 7,
#                     "assigned_to_id": user_id,
#                     "offset": offset
#                     # No limit → Redmine defaults to 25
#                 }

#                 response = requests.get(f"{REDMINE_URL}/issues.json", headers=headers, params=params)

#                 if response.status_code != 200:
#                     return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

#                 data = response.json()
#                 issues = data.get("issues", [])
#                 if total_count is None:
#                     total_count = data.get("total_count", 0)

#                 for issue in issues:
#                     assigned_to = issue.get("assigned_to", {})
#                     custom_fields = issue.get("custom_fields", [])
#                     custom_fields_dict = {field["name"]: field["value"] for field in custom_fields}

#                     owner_name = assigned_to.get("name", "N/A")
#                     license_number = custom_fields_dict.get("Mining License Number", "N/A")
#                     divisional_secretary = custom_fields_dict.get("Divisional Secretary Division", "N/A")
#                     location = custom_fields_dict.get("Name of village ", "N/A")
#                     start_date = issue.get("start_date", "N/A")
#                     due_date = issue.get("due_date", "N/A")

#                     remaining_str = custom_fields_dict.get("Remaining", "0")
#                     try:
#                         remaining_cubes = int(remaining_str.strip()) if remaining_str.strip() else 0
#                     except ValueError:
#                         remaining_cubes = 0

#                     royalty = custom_fields_dict.get("Royalty", "N/A")
#                     status = issue.get("status", {}).get("name", "Unknown")

#                     relevant_issues.append({
#                         "License Number": license_number,
#                         "Divisional Secretary Division": divisional_secretary,
#                         "Owner Name": owner_name,
#                         "Location": location,
#                         "Start Date": start_date,
#                         "Due Date": due_date,
#                         "Remaining Cubes": remaining_cubes,
#                         "Royalty": royalty,
#                         "Status": status
#                     })

#                 offset += len(issues)
#                 if offset >= total_count or not issues:
#                     break

#             return relevant_issues, None

#         except Exception as e:
#             return None, f"Server error: {str(e)}"


#     # @staticmethod
#     # def mining_homeLicenses(token):
#     #     try:
#     #         REDMINE_URL = os.getenv("REDMINE_URL")
#     #         API_KEY = JWTUtils.get_api_key_from_token(token)

#     #         if not REDMINE_URL or not API_KEY:
#     #             return None, "Redmine URL or API Key is missing"

#     #         # Step 1: Extract user_id from the token
#     #         user_id, error = MLOUtils.get_user_info_from_token(token)
#     #         if not user_id:
#     #             return None, error

#     #         # Step 2: Define query parameters for project_id=1 and tracker_id=4 (ML)
#     #         params = {
#     #             "project_id": 1,
#     #             "tracker_id": 4,  # ML tracker ID
#     #             "status_id": 7
#     #         }

#     #         headers = {
#     #             "X-Redmine-API-Key": API_KEY
#     #         }

#     #         # Make the Redmine request
#     #         limit = LimitUtils.get_limit()
#     #         response = requests.get(
#     #             f"{REDMINE_URL}/projects/mmpro-gsmb/issues.json?offset=0&limit={limit}",
#     #             params=params,
#     #             headers=headers
#     #         )

#     #         # Check if the request was successful
#     #         if response.status_code != 200:
#     #             return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

#     #         issues = response.json().get("issues", [])

#     #         relevant_issues = []
#     #         current_date = datetime.now().date()

#     #         for issue in issues:
#     #             assigned_to = issue.get("assigned_to", {})
#     #             assigned_user_id = assigned_to.get("id", None)
#     #             due_date = issue.get("due_date", "N/A")
                
#     #             # Combined filter for assigned user and due date existence
#     #             if assigned_user_id == user_id and due_date != "N/A":
#     #                 due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
                    
#     #                 # Check due date is after current date
#     #                 if due_date_obj > current_date:
#     #                     # Extract fields
#     #                     custom_fields = issue.get("custom_fields", [])
#     #                     custom_fields_dict = {field["name"]: field["value"] for field in custom_fields}

#     #                     owner_name = assigned_to.get("name", "N/A")
#     #                     license_number = custom_fields_dict.get("Mining License Number", "N/A")
#     #                     divisional_secretary = custom_fields_dict.get("Divisional Secretary Division", "N/A")
#     #                     location = custom_fields_dict.get("Name of village ", "N/A")
#     #                     start_date = issue.get("start_date", "N/A")

#     #                     remaining_str = custom_fields_dict.get("Remaining", "0")
#     #                     try:
#     #                         remaining_cubes = int(remaining_str) if remaining_str.strip() else 0
#     #                     except ValueError:
#     #                         remaining_cubes = 0

#     #                     royalty = custom_fields_dict.get("Royalty", "N/A")

#     #                     relevant_issues.append({
#     #                         "Issue ID": issue.get("id", "N/A"),
#     #                         "License Number": license_number,
#     #                         "Divisional Secretary Division": divisional_secretary,
#     #                         "Owner Name": owner_name,
#     #                         "Location": location,
#     #                         "Start Date": start_date,
#     #                         "Due Date": due_date,
#     #                         "Remaining Cubes": remaining_cubes,
#     #                         "Royalty": royalty
#     #                     })


#     #         return relevant_issues, None

#     #     except Exception as e:
#     #         return None, f"Server error: {str(e)}"

#     @staticmethod
#     def mining_homeLicenses(token):
#         try:
#             REDMINE_URL = os.getenv("REDMINE_URL")
#             API_KEY = JWTUtils.get_api_key_from_token(token)

#             if not REDMINE_URL or not API_KEY:
#                 return None, "Redmine URL or API Key is missing"

#             result = JWTUtils.decode_jwt_and_get_user_id(token)
#             if not result['success']:
#                 return None, result['message']

#             user_id = result['user_id']

#             headers = {
#                 "X-Redmine-API-Key": API_KEY,
#                 "Content-Type": "application/json"
#             }

#             offset = 0
#             relevant_issues = []
#             total_count = None
#             current_date = datetime.now().date()

#             while True:
#                 params = {
#                     "project_id": 1,
#                     "tracker_id": 4,
#                     "status_id": 7,
#                     "assigned_to_id": user_id,
#                     "offset": offset
#                     # No limit — Redmine will default to 25 per page
#                 }

#                 response = requests.get(
#                     f"{REDMINE_URL}/issues.json",
#                     headers=headers,
#                     params=params
#                 )

#                 if response.status_code != 200:
#                     return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

#                 data = response.json()
#                 issues = data.get("issues", [])
#                 if total_count is None:
#                     total_count = data.get("total_count", 0)

#                 for issue in issues:
#                     due_date = issue.get("due_date", "N/A")
#                     if due_date != "N/A":
#                         due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
#                         if due_date_obj > current_date:
#                             assigned_to = issue.get("assigned_to", {})
#                             custom_fields = issue.get("custom_fields", [])
#                             custom_fields_dict = {
#                                 field["name"]: field["value"] for field in custom_fields
#                             }

#                             owner_name = assigned_to.get("name", "N/A")
#                             license_number = custom_fields_dict.get("Mining License Number", "N/A")
#                             divisional_secretary = custom_fields_dict.get("Divisional Secretary Division", "N/A")
#                             location = custom_fields_dict.get("Name of village ", "N/A")
#                             start_date = issue.get("start_date", "N/A")

#                             remaining_str = custom_fields_dict.get("Remaining", "0")
#                             try:
#                                 remaining_cubes = int(remaining_str.strip()) if remaining_str.strip() else 0
#                             except ValueError:
#                                 remaining_cubes = 0

#                             royalty = custom_fields_dict.get("Royalty", "N/A")

#                             relevant_issues.append({
#                                 "Issue ID": issue.get("id", "N/A"),
#                                 "License Number": license_number,
#                                 "Divisional Secretary Division": divisional_secretary,
#                                 "Owner Name": owner_name,
#                                 "Location": location,
#                                 "Start Date": start_date,
#                                 "Due Date": due_date,
#                                 "Remaining Cubes": remaining_cubes,
#                                 "Royalty": royalty
#                             })

#                 offset += len(issues)
#                 if offset >= total_count or not issues:
#                     break

#             return relevant_issues, None

#         except Exception as e:
#             return None, f"Server error: {str(e)}"


#     @staticmethod
#     def create_tpl(data, token):
#         try:
#             # Get the Redmine URL from environment variables
#             REDMINE_URL = os.getenv("REDMINE_URL")
#             if not REDMINE_URL:
#                 return None, "Redmine URL is not configured"


#             # Get the API key from the token
#             API_KEY = JWTUtils.get_api_key_from_token(token)
#             if not API_KEY:
#                 return None, "Invalid or missing API key"


#             # Fetch the current mining license issue to get Used and Remaining values
#             mining_license_number = data.get("mining_license_number")
#             if not mining_license_number:
#                 return None, "Mining license number is required"

#             try:
#                 # Extract the issue ID from the license number
#                 mining_issue_id = mining_license_number.strip().split('/')[-1]
#                 mining_issue_id = int(mining_issue_id)  # Make sure it's an integer
#             except (IndexError, ValueError):
#                 return None, "Invalid mining license number format"

#             # Define the Redmine API endpoint to fetch the mining license issue directly
#             mining_issue_url = f"{REDMINE_URL}/issues/{mining_issue_id}.json"
#             headers = {
#                 "Content-Type": "application/json",
#                 "X-Redmine-API-Key": API_KEY
#             }

#             # Fetch the mining license issue
#             mining_issue_response = requests.get(mining_issue_url, headers=headers)
#             if mining_issue_response.status_code != 200:
#                 return None, f"Failed to fetch mining license issue: {mining_issue_response.status_code} - {mining_issue_response.text}"

#             # Log the Redmine API response for debugging
#             mining_issue_data = mining_issue_response.json()
            
#             # Get the issue details
#             mining_issue = mining_issue_data.get("issue")
#             if not mining_issue:
#                 return None, "Mining license issue not found"

#             # Extract current Used, Remaining, Royalty values
#             custom_fields = mining_issue.get("custom_fields", [])
#             used_field = next((field for field in custom_fields if field.get("name") == "Used"), None)
#             remaining_field = next((field for field in custom_fields if field.get("name") == "Remaining"), None)
#             royalty_field = next((field for field in custom_fields if field.get("name") == "Royalty"), None)

#             if not used_field or not remaining_field or not royalty_field:
#                 return None, "Required fields (Used, Remaining, or Royalty) not found in the mining license issue"
            
#             def safe_int(val, default=0):
#                 try:
#                     return int(val)
#                 except (TypeError, ValueError):
#                     return default

#             current_used = safe_int(used_field.get("value"))
#             current_remaining = safe_int(remaining_field.get("value"))
#             current_royalty = safe_int(royalty_field.get("value"))
#             cubes = safe_int(data.get("cubes"))

#             # Calculate TPL cost (500 per cube)
#             tpl_cost = cubes * 500

#             if current_royalty < tpl_cost:
#                 return None, f"Insufficient royalty balance. Required: {tpl_cost}, Available: {current_royalty}"
#             # Update Used and Remaining values
#             new_used = current_used + cubes
#             new_remaining = current_remaining - cubes
#             new_royalty = current_royalty - tpl_cost

#             if new_remaining < 0:
#                 return None, "Insufficient remaining cubes"

#             # Prepare payload to update the mining license issue
#             update_payload = {
#                 "issue": {
#                     "custom_fields": [
#                         {"id": used_field.get("id"), "value": str(new_used)},
#                         {"id": remaining_field.get("id"), "value": str(new_remaining)},
#                         {"id": royalty_field.get("id"), "value": str(new_royalty)}
#                     ]
#                 }
#             }

#             # Send a PUT request to update the mining license issue
#             update_url = f"{REDMINE_URL}/issues/{mining_issue_id}.json"
#             update_response = requests.put(update_url, json=update_payload, headers=headers)
            
#             if update_response.status_code != 204:
#                 return None, "Failed to update mining license issue"

#             # Define the Redmine API endpoint for creating the TPL issue
#             REDMINE_API_URL = f"{REDMINE_URL}/issues.json"

#                     # Extract route_01 and destination for time calculation
#             route_01 = data.get("route_01", "")
#             destination = data.get("destination", "")

#             # Calculate estimated time between route_01 and destination
#             time_result = MLOwnerService.calculate_time(route_01, destination)
          
#             if not time_result.get("success"):
#                 return None, time_result.get("error")

#             time_hours = time_result.get("time_hours", 0)

#             result = JWTUtils.decode_jwt_and_get_user_id(token)

#             user_id = result['user_id']
            
#             payload = {
#                 "issue": {
#                     "project_id": 1,  # Replace with actual project ID
#                     "tracker_id": 5,  # TPL tracker ID
#                     "status_id": 8,   # Active status
#                     "priority_id": 2,
#                     "subject": "TPL",
#                     "start_date": data.get("start_date", date.today().isoformat()),
#                     "assigned_to_id": user_id,
#                    # "due_date": (datetime.now() + timedelta(hours=time_hours)).strftime("%Y-%m-%d"),
#                     "estimated_hours" :time_hours,
#                     "custom_fields": [
#                         {"id": 53, "name": "Lorry Number", "value": data.get("lorry_number", "")},
#                         {"id": 54, "name": "Driver Contact", "value": data.get("driver_contact", "")},
#                         {"id": 55, "name": "Route 01", "value": data.get("route_01", "")},
#                         {"id": 56, "name": "Route 02", "value": data.get("route_02", "")},
#                         {"id": 57, "name": "Route 03", "value": data.get("route_03", "")},
#                         {"id": 58, "name": "Cubes", "value": str(cubes)},
#                         {"id": 59, "name": "Mining License Number", "value": mining_license_number},
#                         {"id": 68, "name": "Destination", "value": data.get("destination", "")}
#                     ]
#                 }
#             }

#             response = requests.post(REDMINE_API_URL, json=payload, headers=headers)


#             # Check if the response is empty before parsing as JSON
#             if response.status_code == 201:
#                 if response.text.strip():  # Ensure there is a response body
#                     return response.json(), None
#                 else:
#                     return {"message": "TPL issue created, but Redmine returned an empty response"}, None
#             else:
#                 return None, response.text or "Failed to create TPL issue"


#         except Exception as e:
#             return None, str(e)
        
#     @staticmethod
#     def calculate_time(city1, city2):
#         """
#         Calculate the distance between two cities using OpenRouteService API and return the time in hours.

#         Args:
#             city1 (str): Name of the first city.
#             city2 (str): Name of the second city.

#         Returns:
#             dict: A dictionary containing the time in hours or an error message.
#         """
#         try:
#             # Step 1: Geocode cities to get coordinates
#             def geocode_location(city_name): 
#                 url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json"
#                 headers = {
#                     "User-Agent": "MiningLicenseTPL/1.0 (it-support@miningcompany.com)"  # <-- important for Nominatim usage policy
#                 }
#                 response_first = requests.get(url, headers=headers, timeout=1)
                
#                 if response_first.status_code != 200:
#                     raise ValueError(f"Geocoding failed with status code {response_first.status_code}, body: {response_first.text}")

#                 try:
#                     response = response_first.json()
#                 except ValueError:
#                     raise ValueError(f"Invalid JSON response: {response_first.text}")  
                
#                 if response:
#                     lat = float(response[0]['lat'])
#                     lon = float(response[0]['lon'])
#                     return lon, lat  # Return as [longitude, latitude]
#                 else:
#                     raise ValueError(f"Location '{city_name}' not found")

#             # Geocode both cities
#             coord1 = geocode_location(city1)
#             time.sleep(1)
#             coord2 = geocode_location(city2)


#             # Step 2: Calculate distance using OpenRouteService
#             url = "https://api.openrouteservice.org/v2/directions/driving-car"
#             headers = {
#                 "Authorization": MLOwnerService.ORS_API_KEY,
#                 "Content-Type": "application/json"
#             }
#             body = {
#                 "coordinates": [coord1, coord2],
#                 "units": "km"
#             }
#             response = requests.post(url, headers=headers, json=body).json()

#             # Extract distance from the response
#             distance_km = response['routes'][0]['summary']['distance']

#             # Calculate the time in hours: (distance / 30 km/h) + 2 hours
#             time_hours = (distance_km / 30) + 2

#             # Return the time in hours
#             return {
#                 "success": True,
#                 "city1": city1,
#                 "city2": city2,
#                 "time_hours": int(round(time_hours))
#             }
#         except Exception as e:
#             return {"success": False, "error": str(e)}


   
#     def update_issue(issue_id, data):
#         try:
#             REDMINE_URL = os.getenv("REDMINE_URL")
#             API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")

#             if not REDMINE_URL or not API_KEY:
#                 return None, "Redmine URL or API Key is missing"
#             headers = {
#                 "X-Redmine-API-Key": API_KEY,  # Include the token for authorization
#                 "Content-Type": "application/json"
#             }
#             update_data = {"issue": data}  # Ensure "issue" is wrapped correctly

#             url = f"{REDMINE_URL}/issues/{issue_id}.json"
           
#             response = requests.put(
#                 url,
#                 json = data,  # Ensure correct JSON structure
#                 headers=headers
#             )


#             # Check if response is empty (204 No Content)
#             if response.status_code == 204:
#                 return {"message": "Issue updated successfully, but no content returned"}, None

#             # If status is not OK, return the error message
#             if response.status_code != 200:
#                 return None, f"Failed to update issue: {response.status_code} - {response.text}"

#             # Attempt to parse the JSON response
#             try:
#                 issue = response.json().get("issue", {})
#                 return issue, None
#             except json.JSONDecodeError:
#                 return None, "Invalid JSON response from server"

#         except Exception as e:
#             return None, f"Server error: {str(e)}"


#     # @staticmethod
#     # def ml_detail(l_number, token):
#     #     api_key = JWTUtils.get_api_key_from_token(token)
#     #     try:
#     #         REDMINE_URL = os.getenv("REDMINE_URL")
#     #         if not REDMINE_URL or not api_key:
#     #             return None, "Redmine URL or API Key is missing"

#     #         headers = {
#     #             "X-Redmine-API-Key": api_key,
#     #             "Content-Type": "application/json"
#     #         }
#     #         limit = LimitUtils.get_limit()
#     #         limit = limit[0] if isinstance(limit, tuple) else limit
#     #         offset = 0

#     #         while True:
#     #             url = f"{REDMINE_URL}/projects/mmpro-gsmb/issues.json?offset={offset}&limit={limit}"
#     #             response = requests.get(url, headers=headers)
#     #             if response.status_code != 200:
#     #                 return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

#     #             issues = response.json().get("issues", [])
#     #             for issue in issues:
#     #                 for field in issue.get("custom_fields", []):
#     #                      if (field.get("id") == 101 and 
#     #                     str(field.get("value", "")).strip().lower() == str(l_number).strip().lower()):
                       
#     #                         custom_fields_dict = {f["name"]: f["value"] for f in issue.get("custom_fields", [])}
#     #                         assigned_to = issue.get("assigned_to", {})
#     #                         result = {
#     #                             "id": issue.get("id"),
#     #                             "assigned_to": {
#     #                                 "id": assigned_to.get("id"),
#     #                                 "name": assigned_to.get("name")
#     #                             },
#     #                             "custom_fields": custom_fields_dict,
#     #                         }
#     #                         return result, None

#     #                 if len(issues) < limit:
#     #                     break
#     #                 offset += limit

#     #             return None, None

#     #     except Exception as e:
#     #         return None, f"Server error: {str(e)}"
        

#     # @staticmethod
#     # def ml_detail(l_number, token):
#     #     try:
#     #         REDMINE_URL = os.getenv("REDMINE_URL")
#     #         API_KEY = JWTUtils.get_api_key_from_token(token)
#     #         if not REDMINE_URL or not API_KEY:
#     #             return None, "Redmine URL or API Key is missing"

#     #         headers = {
#     #             "X-Redmine-API-Key": API_KEY,
#     #             "Content-Type": "application/json"
#     #         }
#     #         limit = LimitUtils.get_limit()
#     #         limit = limit[0] if isinstance(limit, tuple) else limit
#     #         offset = 0

#     #         # Search all issues for the matching Mining License Number
#     #         while True:
#     #             url = f"{REDMINE_URL}/projects/mmpro-gsmb/issues.json?offset={offset}&limit={limit}"
#     #             response = requests.get(url, headers=headers)
#     #             if response.status_code != 200:
#     #                 return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

#     #             issues = response.json().get("issues", [])
#     #             for issue in issues:
#     #                 for field in issue.get("custom_fields", []):
#     #                     if field.get("id") == 101 and str(field.get("value", "")).strip().lower() == str(l_number).strip().lower():
#     #                         # Found the issue, now fetch full details by ID
#     #                         issue_id = issue.get("id")
#     #                         detail_url = f"{REDMINE_URL}/issues/{issue_id}.json"
#     #                         detail_resp = requests.get(detail_url, headers=headers)
#     #                         if detail_resp.status_code != 200:
#     #                             return None, f"Failed to fetch issue details: {detail_resp.status_code} - {detail_resp.text}"
#     #                         issue_data = detail_resp.json().get("issue", {})

#     #                         # Convert custom fields to dict for easy access
#     #                         custom_fields = issue_data.get("custom_fields", [])
#     #                         cf = {f["name"]: f.get("value") for f in custom_fields}

#     #                         # Build the response structure
#     #                         result = {
#     #                             "id": issue_data.get("id"),
#     #                             "subject": issue_data.get("subject"),
#     #                             "status": issue_data.get("status", {}).get("name"),
#     #                             "author": issue_data.get("author", {}).get("name"),
#     #                             "assigned_to": issue_data.get("assigned_to", {}).get("name"),
#     #                             "start_date": issue_data.get("start_date"),
#     #                             "due_date": issue_data.get("due_date"),
#     #                             "created_on": issue_data.get("created_on"),
#     #                             "updated_on": issue_data.get("updated_on"),
#     #                             "royalty": cf.get("Royalty"),
#     #                             "exploration_licence_no": cf.get("Exploration Licence No"),
#     #                             "land_name": cf.get("Land Name(Licence Details)"),
#     #                             "land_owner_name": cf.get("Land owner name"),
#     #                             "village_name": cf.get("Name of village "),
#     #                             "grama_niladhari_division": cf.get("Grama Niladhari Division"),
#     #                             "divisional_secretary_division": cf.get("Divisional Secretary Division"),
#     #                             "administrative_district": cf.get("Administrative District"),
#     #                             "capacity": cf.get("Capacity"),
#     #                             "used": cf.get("Used"),
#     #                             "remaining": cf.get("Remaining"),
#     #                             "mobile_number": cf.get("Mobile Number"),
#     #                             "google_location": cf.get("Google location "),
#     #                             "reason_for_hold": cf.get("Reason For Hold"),
#     #                             "economic_viability_report": cf.get("Economic Viability Report"),
#     #                             "detailed_mine_restoration_plan": cf.get("Detailed Mine Restoration Plan"),
#     #                             "deed_and_survey_plan": cf.get("Deed and Survey Plan"),
#     #                             "payment_receipt": cf.get("Payment Receipt"),
#     #                             "license_boundary_survey": cf.get("License Boundary Survey"),
#     #                             "mining_license_number": cf.get("Mining License Number"),
#     #                         }
#     #                         return result, None

#     #             if len(issues) < limit:
#     #                 break
#     #             offset += limit

#     #         return None, "No mining license found for the given number."

#     #     except Exception as e:
#     #         return None, f"Server error: {str(e)}"
      

#     @staticmethod
#     def ml_detail(l_number: str, token: str) -> Tuple[Optional[Dict], Optional[str]]:
#         try:
#             REDMINE_URL = os.getenv("REDMINE_URL")
#             API_KEY    = JWTUtils.get_api_key_from_token(token)
#             if not REDMINE_URL or not API_KEY:
#                 return None, "Redmine URL or API Key is missing"

#             # Decode token to get user ID
#             result = JWTUtils.decode_jwt_and_get_user_id(token)
#             if not result['success']:
#                 return None, result['message']
#             user_id = result['user_id']

#             headers = {
#                 "X-Redmine-API-Key": API_KEY,
#                 "Content-Type": "application/json"
#             }

#             # Defaults
#             default_limit = 100
#             offset        = 0

#             # Loop through pages of issues
#             while True:
#                 issues_url = (
#                     f"{REDMINE_URL}/issues.json?"
#                     f"project_id=1&tracker_id=4&status_id=7"
#                     f"&assigned_to_id={user_id}"
#                     f"&limit={default_limit}&offset={offset}"
#                 )
#                 resp = requests.get(issues_url, headers=headers, timeout=30)
#                 if resp.status_code != 200:
#                     return None, f"Failed to fetch issues: {resp.status_code} - {resp.text}"

#                 issues = resp.json().get("issues", [])
#                 for issue in issues:
#                     # Look for custom field with id=101 matching l_number
#                     for cf in issue.get("custom_fields", []):
#                         if cf.get("id") == 101 and str(cf.get("value", "")).strip().lower() == str(l_number).strip().lower():
#                             # Found — fetch full details
#                             issue_id  = issue["id"]
#                             detail_url = f"{REDMINE_URL}/issues/{issue_id}.json"
#                             detail_resp = requests.get(detail_url, headers=headers, timeout=30)
#                             if detail_resp.status_code != 200:
#                                 return None, f"Failed to fetch issue details: {detail_resp.status_code} - {detail_resp.text}"

#                             issue_data = detail_resp.json().get("issue", {})
#                             cf_dict    = {f["name"]: f.get("value") for f in issue_data.get("custom_fields", [])}

#                             # Build and return the detail dict
#                             return {
#                                 "id": issue_data.get("id"),
#                                 "subject": issue_data.get("subject"),
#                                 "status": issue_data.get("status", {}).get("name"),
#                                 "author": issue_data.get("author", {}).get("name"),
#                                 "assigned_to": issue_data.get("assigned_to", {}).get("name"),
#                                 "start_date": issue_data.get("start_date"),
#                                 "due_date": issue_data.get("due_date"),
#                                 "created_on": issue_data.get("created_on"),
#                                 "updated_on": issue_data.get("updated_on"),
#                                 # all your custom fields:
#                                 "royalty": cf_dict.get("Royalty"),
#                                 "exploration_licence_no": cf_dict.get("Exploration Licence No"),
#                                 "land_name": cf_dict.get("Land Name(Licence Details)"),
#                                 "land_owner_name": cf_dict.get("Land owner name"),
#                                 "village_name": cf_dict.get("Name of village "),
#                                 "grama_niladhari_division": cf_dict.get("Grama Niladhari Division"),
#                                 "divisional_secretary_division": cf_dict.get("Divisional Secretary Division"),
#                                 "administrative_district": cf_dict.get("Administrative District"),
#                                 "capacity": cf_dict.get("Capacity"),
#                                 "used": cf_dict.get("Used"),
#                                 "remaining": cf_dict.get("Remaining"),
#                                 "mobile_number": cf_dict.get("Mobile Number"),
#                                 "google_location": cf_dict.get("Google location "),
#                                 "reason_for_hold": cf_dict.get("Reason For Hold"),
#                                 "economic_viability_report": cf_dict.get("Economic Viability Report"),
#                                 "detailed_mine_restoration_plan": cf_dict.get("Detailed Mine Restoration Plan"),
#                                 "deed_and_survey_plan": cf_dict.get("Deed and Survey Plan"),
#                                 "payment_receipt": cf_dict.get("Payment Receipt"),
#                                 "license_boundary_survey": cf_dict.get("License Boundary Survey"),
#                                 "mining_license_number": cf_dict.get("Mining License Number"),
#                             }, None

#                 # If fewer issues than limit, we've reached the last page
#                 if len(issues) < default_limit:
#                     break

#                 offset += default_limit

#             return None, "No mining license found for the given number."

#         except requests.exceptions.RequestException as e:
#             return None, f"Network error connecting to Redmine: {str(e)}"
#         except Exception as e:
#             return None, f"Server error: {str(e)}"

        
        
#     @staticmethod
#     def user_detail(user_id, token):
#         api_key = JWTUtils.get_api_key_from_token(token)
#         try:
#             REDMINE_URL = os.getenv("REDMINE_URL")

#             if not REDMINE_URL or not api_key:
#                 return None, "Redmine URL or API Key is missing"
#             headers = {
#                 "X-Redmine-API-Key": api_key,  # Include the token for authorization
#                 "Content-Type": "application/json"
#             }
#             url = f"{REDMINE_URL}/users/{user_id}.json"
           
#             response = requests.get(
#                 url,  # Ensure correct JSON structure
#                 headers=headers
#             )

#             if response.status_code != 200:
#                 return None, f"Failed to fetch issue: {response.status_code} - {response.text}"

#             user_detail = response.json().get("user", {})


#             return user_detail, None  # Returning filtered issues and no error

#         except Exception as e:
#             return None, f"Server error: {str(e)}"
     

#     # @staticmethod
#     # def view_tpls(token: str, mining_license_number: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
#     #     try:
        

#     #         if not mining_license_number or not mining_license_number.strip():
#     #             return None, "Valid mining license number is required"

#     #         mining_license_number = mining_license_number.strip() # Strip once upfront

#     #         # --- Configuration ---
#     #         REDMINE_URL = os.getenv("REDMINE_URL")

#     #         API_KEY = JWTUtils.get_api_key_from_token(token)


#     #         if not REDMINE_URL or not API_KEY:
#     #             return None, "System configuration error - missing Redmine URL or API Key"

#     #         # --- Authentication/User Info (Optional but kept from original) ---
#     #         # Assuming MLOUtils has a method like this
#     #         result = JWTUtils.decode_jwt_and_get_user_id(token)
#     #         if not result['success']:
#     #             return None, result['message']

#     #         user_id = result['user_id']

#     #         # Get all TPL issues (tracker_id=5) without filtering by custom field in params
#     #         params = {
#     #             "project_id": 1,
#     #             "tracker_id": 5,
#     #         }

#     #         headers = {
#     #             "Content-Type": "application/json",
#     #             "X-Redmine-API-Key": API_KEY
#     #         }

#     #         # Assuming LimitUtils has a method like this
#     #         limit = LimitUtils.get_limit() if LimitUtils.get_limit() else 100 # Use a default if needed
            
#     #         api_url = f"{REDMINE_URL}/issues.json" # Simplified URL, project filter is in params
           

#     #         response = requests.get(
#     #             api_url,
#     #             params={**params, "limit": limit, "offset": 0}, # Combine params
#     #             headers=headers,
#     #             timeout=30 # Add a timeout
#     #         )

            

#     #         if response.status_code != 200:
#     #             error_msg = f"Redmine API error ({response.status_code}): {response.text}"
             
#     #             return None, error_msg

#     #         # --- Process Results ---
#     #         try:
#     #             response_data = response.json()
#     #             issues = response_data.get("issues", [])
                
#     #         except ValueError: # Handle cases where response is not valid JSON
#     #              error_msg = f"Redmine API error: Invalid JSON response. Status: {response.status_code}, Body: {response.text}"
                 
#     #              return None, "Failed to parse response from Redmine"


#     #         tpl_list = []
#     #         current_datetime = datetime.now() # Consider timezone if needed

#     #         for issue in issues:
#     #             try:
#     #                 # Get all custom fields for this issue
#     #                 custom_fields = issue.get("custom_fields", [])
                    
#     #                 # Find the Mining issue id (custom field 59)
#     #                 mining_issue_id = None
#     #                 for field in custom_fields:
#     #                     if field.get("id") == 59:
#     #                         mining_issue_id = field.get("value")
#     #                         break
                    
#     #                 # Skip if this TPL doesn't belong to our mining license
#     #                 if not mining_issue_id or mining_issue_id != mining_license_number.strip():
#     #                     continue

#     #                 # Convert custom fields to dictionary for easier access
#     #                 custom_fields_dict = {
#     #                     field["name"]: field["value"] 
#     #                     for field in custom_fields
#     #                 }

#     #                 # --- Calculate Status ---
#     #                 created_date_str = issue.get("created_on")
#     #                 estimated_hours_str = issue.get("estimated_hours")  # Keep as string initially
#     #                 status = "Undetermined"  # Default status

#     #                 if created_date_str and estimated_hours_str is not None:
#     #                     try:
#     #                         created_date = datetime.strptime(created_date_str, "%Y-%m-%dT%H:%M:%SZ")
#     #                         estimated_hours = float(estimated_hours_str)
                            
#     #                         expiration_datetime = created_date + timedelta(hours=estimated_hours)
#     #                         status = "Active" if current_datetime < expiration_datetime else "Expired"

#     #                     except ValueError as e:
                           
#     #                         continue  # Skip to next issue on error

#     #                 tpl_data = {
#     #                     "tpl_id": issue.get("id"),
#     #                     "license_number": mining_license_number,
#     #                     "subject": issue.get("subject", ""),
#     #                     "status": status,
#     #                     "lorry_number": custom_fields_dict.get("Lorry Number"),
#     #                     "driver_contact": custom_fields_dict.get("Driver Contact"),
#     #                     "destination": custom_fields_dict.get("Destination"),
#     #                     "Route_01": custom_fields_dict.get("Route 01"),
#     #                     "Route_02": custom_fields_dict.get("Route 02"),
#     #                     "Route_03": custom_fields_dict.get("Route 03"),
#     #                     "cubes": custom_fields_dict.get("Cubes"),  
#     #                     "Create_Date": issue.get("created_on", ""),
#     #                     "Estimated Hours": estimated_hours_str,
#     #                 }

#     #                 tpl_list.append(tpl_data)

#     #             except Exception as e:
#     #                 print(f"Error processing issue {issue.get('id', 'N/A')}: {str(e)}")
#     #                 continue

#     #         print(f"Finished processing. Returning {len(tpl_list)} TPLs.")  # Debugging
#     #         return tpl_list, None


#     #     except requests.exceptions.RequestException as e:
#     #         error_msg = f"Network error connecting to Redmine: {str(e)}"
#     #         return None, error_msg
#     #     except Exception as e:
#     #         print(f"Unexpected error: {str(e)}")
#     #         return None, f"Processing error: {str(e)}"
    

#     @staticmethod
#     def view_tpls(token: str, mining_license_number: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
#         try:
#             if not mining_license_number or not mining_license_number.strip():
#                 return None, "Valid mining license number is required"

#             mining_license_number = mining_license_number.strip()

#             # --- Configuration ---
#             REDMINE_URL = os.getenv("REDMINE_URL")
#             API_KEY = JWTUtils.get_api_key_from_token(token)

#             if not REDMINE_URL or not API_KEY:
#                 return None, "System configuration error - missing Redmine URL or API Key"

#             # --- Decode user ID from token ---
#             result = JWTUtils.decode_jwt_and_get_user_id(token)
#             if not result['success']:
#                 return None, result['message']
            
#             user_id = result['user_id']

#             # --- Prepare headers ---
#             headers = {
#                 "Content-Type": "application/json",
#                 "X-Redmine-API-Key": API_KEY
#             }

#             # --- Direct Redmine API call with query parameters ---
#             limit = 100
#             tpl_url = (
#                 f"{REDMINE_URL}/issues.json?"
#                 f"project_id=1&tracker_id=5&assigned_to_id={user_id}&limit={limit}&offset=0"
#             )

#             response = requests.get(tpl_url, headers=headers, timeout=30)

#             if response.status_code != 200:
#                 error_msg = f"Redmine API error ({response.status_code}): {response.text}"
#                 return None, error_msg

#             # --- Parse JSON response ---
#             try:
#                 issues = response.json().get("issues", [])
#             except ValueError:
#                 return None, "Failed to parse response from Redmine"

#             tpl_list = []
#             current_datetime = datetime.now()

#             # --- Process each issue ---
#             for issue in issues:
#                 try:
#                     custom_fields = issue.get("custom_fields", [])

#                     # Match Mining License Number (custom field ID = 59)
#                     mining_issue_id = next(
#                         (field.get("value") for field in custom_fields if field.get("id") == 59), None
#                     )

#                     if not mining_issue_id or mining_issue_id != mining_license_number:
#                         continue  # Skip if not related to the provided license

#                     # Build a dictionary for quick lookup of custom fields
#                     custom_fields_dict = {
#                         field["name"]: field["value"]
#                         for field in custom_fields
#                     }

#                     # Calculate Status (Active / Expired)
#                     created_date_str = issue.get("created_on")
#                     estimated_hours_str = issue.get("estimated_hours")
#                     status = "Undetermined"

#                     if created_date_str and estimated_hours_str is not None:
#                         try:
#                             created_date = datetime.strptime(created_date_str, "%Y-%m-%dT%H:%M:%SZ")
#                             estimated_hours = float(estimated_hours_str)
#                             expiration_datetime = created_date + timedelta(hours=estimated_hours)
#                             status = "Active" if current_datetime < expiration_datetime else "Expired"
#                         except ValueError:
#                             pass  # Leave as "Undetermined" if parsing fails

#                     tpl_list.append({
#                         "tpl_id": issue.get("id"),
#                         "license_number": mining_license_number,
#                         "subject": issue.get("subject", ""),
#                         "status": status,
#                         "lorry_number": custom_fields_dict.get("Lorry Number"),
#                         "driver_contact": custom_fields_dict.get("Driver Contact"),
#                         "destination": custom_fields_dict.get("Destination"),
#                         "Route_01": custom_fields_dict.get("Route 01"),
#                         "Route_02": custom_fields_dict.get("Route 02"),
#                         "Route_03": custom_fields_dict.get("Route 03"),
#                         "cubes": custom_fields_dict.get("Cubes"),
#                         "Create_Date": created_date_str,
#                         "Estimated Hours": estimated_hours_str,
#                     })

#                 except Exception as e:
#                     print(f"Error processing issue {issue.get('id', 'N/A')}: {str(e)}")
#                     continue

#             print(f"Finished processing. Returning {len(tpl_list)} TPLs.")
#             return tpl_list, None

#         except requests.exceptions.RequestException as e:
#             return None, f"Network error connecting to Redmine: {str(e)}"
#         except Exception as e:
#             print(f"Unexpected error: {str(e)}")
#             return None, f"Processing error: {str(e)}"


#     @staticmethod
#     def ml_request(data, token, user_mobile):
#         try:
#             # Get the Redmine URL from environment variables
#             REDMINE_URL = os.getenv("REDMINE_URL")
#             if not REDMINE_URL:
#                 return None, "Redmine URL is not configured"

#             # Get the API key from the token
#             API_KEY = JWTUtils.get_api_key_from_token(token)
#             if not API_KEY:
#                 return None, "Invalid or missing API key"
            
#             headers = {
#                 "Content-Type": "application/json",
#                 "X-Redmine-API-Key": API_KEY
#             }
    
#             # Prepare the payload for the ML request
#             payload = {
#                 "issue": {
#                     "project_id": data.get("project_id", 1),
#                     "status_id": data.get("status_id", 8),
#                     "priority_id": data.get("priority_id", 2),
#                     "assigned_to_id": data.get("assigned_to"),  # Get from data dictionary
#                     "author_id": data.get("author"), 
#                     "subject": data.get("subject", "ML Request"),
#                     "description": data.get("description", ""),
#                     "custom_fields": [
#                         {"id": 19, "value": data.get("exploration_nb", "")},
#                         {"id": 28, "value": data.get("land_name", "")},  
#                         {"id": 29, "value": data.get("land_owner_name", "")},
#                         {"id": 30, "value": data.get("village_name", "")},
#                         {"id": 31, "value": data.get("grama_niladari", "")},
#                         {"id": 31, "value": data.get("grama_niladari", "")},
#                         {"id": 32, "value": data.get("divisional_secretary_division", "")},
#                         {"id": 33, "value": data.get("administrative_district", "")},   
#                         {"id": 92, "value": data.get("google_location", "")}, 
#                         {"id": 66, "value": user_mobile},
#                         *data.get("custom_fields", [])                              
#                     ]
#                 }
#             }

#             # First create the issue
#             response = requests.post(f"{REDMINE_URL}/issues.json", json=payload, headers=headers)
            
#             if response.status_code != 201:
#                 return None, f"Failed to create issue: {response.text}"
        
#             issue_id = response.json()["issue"]["id"]
#             issue_id = response.json()["issue"]["id"]
        
#         # Now, update the Mining License Number field with LLL/100/{issue_id}
#             update_payload = {
#                 "issue": {
#                     "custom_fields": [
#                         {
#                             "id": 101,  # Mining License Number field ID
#                             "value": f"ML Request LLL/100/{issue_id}"
#                         }
#                     ]
#                 }
#             }

#             update_response = requests.put(
#                 f"{REDMINE_URL}/issues/{issue_id}.json",
#                 headers=headers,
#                 json=update_payload
#             )

#             if update_response.status_code != 204:
#                 return None, f"Failed to update Mining License Number: {update_response.status_code} - {update_response.text}"

#             # Return the complete issue data including the updated mining license number
#             issue_data = response.json()
#             issue_data["issue"]["mining_license_number"] = f"LLL/100/{issue_id}"
            
#             return issue_data, None

#         except requests.exceptions.RequestException as e:
#             return None, f"Request failed: {str(e)}"
#         except Exception as e:
#             return None, f"Unexpected error: {str(e)}"
        
#     @staticmethod
#     def get_mining_license_requests(token):
#         try:
#             user_api_key = JWTUtils.get_api_key_from_token(token)
#             if not user_api_key:
#                 return None, "Invalid or missing API key in the token"

#             user_response = JWTUtils.decode_jwt_and_get_user_id(token)

#             user_id = user_response["user_id"]
#             if not user_id:
#                 return None, f"Failed to extract user info"

#             REDMINE_URL = os.getenv("REDMINE_URL")
#             if not REDMINE_URL:
#                 return None, "Environment variable 'REDMINE_URL' is not set"

#             ml_issues_url = f"{REDMINE_URL}/issues.json?tracker_id=4&project_id=1&status_id=!7"
#             response = requests.get(
#                 ml_issues_url,
#                 headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
#             )

#             if response.status_code != 200:
#                 return None, f"Failed to fetch ML issues: {response.status_code} - {response.text}"

#             issues = response.json().get("issues", [])

#             formatted_mls = []

#             for issue in issues:
#                 assigned_to = issue.get("assigned_to", {})
#                 assigned_to_id = assigned_to.get("id")

#                 # ✅ Filter: only include issues assigned to current user
#                 if assigned_to_id != user_id:
#                     continue

#                 custom_fields = issue.get("custom_fields", [])
#                 attachment_urls = MLOwnerService.get_attachment_urls(user_api_key, REDMINE_URL, custom_fields)

#                 assigned_to_details = None
#                 if assigned_to_id:
#                     user_response = requests.get(
#                         f"{REDMINE_URL}/users/{assigned_to_id}.json",
#                         headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
#                     )
#                     if user_response.status_code == 200:
#                         assigned_to_details = user_response.json().get("user", {})

#                 ml_data = {
#                     "id": issue.get("id"),
#                     "subject": issue.get("subject"),
#                     "status": issue.get("status", {}).get("name"),
#                     "assigned_to": assigned_to.get("name"),
#                     "created_on": issue.get("created_on"),
#                     "updated_on": issue.get("updated_on"),
#                     "assigned_to_details": {
#                         "id": assigned_to_details.get("id"),
#                         "name": f"{assigned_to_details.get('firstname', '')} {assigned_to_details.get('lastname', '')}".strip(),
#                         "email": assigned_to_details.get("mail"),
#                         "custom_fields": assigned_to_details.get("custom_fields", [])
#                     } if assigned_to_details else None,
#                     "exploration_licence_no": MLOwnerService.get_custom_field_value(custom_fields, "Exploration Licence No"),
#                     "land_name": MLOwnerService.get_custom_field_value(custom_fields, "Land Name(Licence Details)"),
#                     "land_owner_name": MLOwnerService.get_custom_field_value(custom_fields, "Land owner name"),
#                     "village_name": MLOwnerService.get_custom_field_value(custom_fields, "Name of village "),
#                     "grama_niladhari_division": MLOwnerService.get_custom_field_value(custom_fields, "Grama Niladhari Division"),
#                     "divisional_secretary_division": MLOwnerService.get_custom_field_value(custom_fields, "Divisional Secretary Division"),
#                     "administrative_district": MLOwnerService.get_custom_field_value(custom_fields, "Administrative District"),
#                     "google_location": MLOwnerService.get_custom_field_value(custom_fields, "Google location "),
#                     "mobile_number": MLOwnerService.get_custom_field_value(custom_fields, "Mobile Number"),
#                     "detailed_mine_restoration_plan": attachment_urls.get("Detailed Mine Restoration Plan"),
#                     "economic_viability_report": attachment_urls.get("Economic Viability Report"),
#                     "license_boundary_survey": attachment_urls.get("License Boundary Survey"),
#                     "deed_and_survey_plan": attachment_urls.get("Deed and Survey Plan"),
#                     "payment_receipt": attachment_urls.get("Payment Receipt"),
#                 }

#                 formatted_mls.append(ml_data)

#             return formatted_mls, None

#         except Exception as e:
#             return None, f"Server error: {str(e)}"

        
#     @staticmethod
#     def get_attachment_urls(api_key, redmine_url, custom_fields):
#         try:
#             # Define the mapping of custom field names to their attachment IDs
#             file_fields = {
#                 "Economic Viability Report": None,
#                 "License fee receipt": None,
#                 "Detailed Mine Restoration Plan": None,
#                 "Professional": None,
#                 "Deed and Survey Plan": None,
#                 "Payment Receipt": None
#             }

#             # Extract attachment IDs from custom fields
#             for field in custom_fields:
#                 field_name = field.get("name")
#                 attachment_id = field.get("value")

#                 if field_name in file_fields and attachment_id.isdigit():
#                     file_fields[field_name] = attachment_id

#             # Fetch URLs for valid attachment IDs
#             file_urls = {}
#             for field_name, attachment_id in file_fields.items():
#                 if attachment_id:
#                     attachment_url = f"{redmine_url}/attachments/{attachment_id}.json"
#                     response = requests.get(
#                         attachment_url,
#                         headers={"X-Redmine-API-Key": api_key, "Content-Type": "application/json"}
#                     )

#                     if response.status_code == 200:
#                         attachment_data = response.json().get("attachment", {})
#                         file_urls[field_name] = attachment_data.get("content_url", "")

#             return file_urls

#         except Exception as e:
#             return {}


#     @staticmethod
#     def get_custom_field_value(custom_fields, field_name):
#         """Helper function to extract custom field value by name."""
#         for field in custom_fields:
#             if field.get("name") == field_name:
#                 return field.get("value")
#         return None
    

#     @staticmethod
#     def get_pending_mining_license_details(token):
#         try:
#             user_api_key = JWTUtils.get_api_key_from_token(token)
#             if not user_api_key:
#                 return None, "Invalid or missing API key in the token"

#             user_response = JWTUtils.decode_jwt_and_get_user_id(token)
#             user_id = user_response.get("user_id")
#             if not user_id:
#                 return None, "Failed to extract user info"

#             REDMINE_URL = os.getenv("REDMINE_URL")
#             if not REDMINE_URL:
#                 return None, "Environment variable 'REDMINE_URL' is not set"

#             ml_issues_url = f"{REDMINE_URL}/issues.json?tracker_id=4&project_id=1&status_id=!7"
#             response = requests.get(
#                 ml_issues_url,
#                 headers={"X-Redmine-API-Key": user_api_key, "Content-Type": "application/json"}
#             )

#             if response.status_code != 200:
#                 return None, f"Failed to fetch ML issues: {response.status_code} - {response.text}"

#             issues = response.json().get("issues", [])

#             license_summaries = []

#             for issue in issues:
#                 assigned_to = issue.get("assigned_to", {})
#                 assigned_to_id = assigned_to.get("id")

#                 # Filter: only include issues assigned to current user
#                 if assigned_to_id != user_id:
#                     continue

#                 custom_fields = issue.get("custom_fields", [])

#                 mining_license_no = MLOwnerService.get_custom_field_value(custom_fields, "Mining License Number")

#                 license_summaries.append({
#                     "mining_license_number": mining_license_no,
#                     "created_on": issue.get("created_on"),
#                     "updated_on": issue.get("updated_on"),
#                     "status": issue.get("status", {}).get("name")
#                 })

#             return license_summaries, None

#         except Exception as e:
#             return None, f"Server error: {str(e)}"
        
#     @staticmethod
#     def get_mining_license_by_id(token, issue_id):
#         try:
#             # 🔐 Extract API key from JWT token
#             api_key = JWTUtils.get_api_key_from_token(token)
#             if not api_key:
#                 return None, "Invalid or missing API key"

#             # 🌍 Load Redmine URL from environment
#             REDMINE_URL = os.getenv("REDMINE_URL")
#             if not REDMINE_URL:
#                 return None, "REDMINE_URL environment variable not set"

#             # 🔗 Fetch issue details
#             issue_url = f"{REDMINE_URL}/issues/{issue_id}.json?include=attachments"
#             response = requests.get(
#                 issue_url,
#                 headers={"X-Redmine-API-Key": api_key, "Content-Type": "application/json"}
#             )

#             if response.status_code != 200:
#                 return None, f"Failed to fetch issue: {response.status_code} - {response.text}"

#             issue = response.json().get("issue")
#             if not issue:
#                 return None, "Issue data not found"

#             # 🗂️ Extract and map custom fields to a dictionary
#             custom_fields = issue.get("custom_fields", [])
#             custom_field_map = {field["name"]: field.get("value") for field in custom_fields}

#             # 📎 Get attachment URLs
#             attachments = MLOwnerService.get_attachment_urls(api_key, REDMINE_URL, custom_fields)

#             # 🧾 Build the final structured response
#             formatted_issue = {
#                 "id": issue.get("id"),
#                 "subject": issue.get("subject"),
#                 "status": issue.get("status", {}).get("name"),
#                 "author": issue.get("author", {}).get("name"),
#                 "assigned_to": issue.get("assigned_to", {}).get("name"),
#                 "start_date": issue.get("start_date"),
#                 "due_date": issue.get("due_date"),
#                 "exploration_licence_no": custom_field_map.get("Exploration Licence No"),
#                 # "applicant_or_company_name": custom_field_map.get("Name of Applicant OR Company"),
#                 "land_name": custom_field_map.get("Land Name(Licence Details)"),
#                 "land_owner_name": custom_field_map.get("Land owner name"),
#                 "village_name": custom_field_map.get("Name of village "),
#                 "grama_niladhari_division": custom_field_map.get("Grama Niladhari Division"),
#                 "divisional_secretary_division": custom_field_map.get("Divisional Secretary Division"),
#                 "administrative_district": custom_field_map.get("Administrative District"),
#                 "capacity": custom_field_map.get("Capacity"),
#                 "used": custom_field_map.get("Used"),
#                 "remaining": custom_field_map.get("Remaining"),
#                 "royalty": custom_field_map.get("Royalty"),
#                 "license_number": custom_field_map.get("Mining License Number"),
#                 "mining_license_number": custom_field_map.get("Mining License Number"),
#                 "mobile_number": custom_field_map.get("Mobile Number"),
#                 "reason_for_hold":custom_field_map.get("Reason For Hold"),
#                 "economic_viability_report": attachments.get("Economic Viability Report"),
#                 "license_fee_receipt": attachments.get("License fee receipt"),
#                 "detailed_mine_restoration_plan": attachments.get("Detailed Mine Restoration Plan"),
#                 # "professional": attachments.get("Professional"),
#                 "deed_and_survey_plan": attachments.get("Deed and Survey Plan"),
#                 "payment_receipt": attachments.get("Payment Receipt"),
#                 "license_boundary_survey": attachments.get("License Boundary Survey")
#             }

#             return formatted_issue, None

#         except Exception as e:
#             return None, f"Server error: {str(e)}"

#     @staticmethod
#     def get_mining_license_summary(token):
#         try:
#             user_api_key = JWTUtils.get_api_key_from_token(token)
#             if not user_api_key:
#                 return None, "Invalid or missing API key in the token"

#             user_response = JWTUtils.decode_jwt_and_get_user_id(token)
#             user_id = user_response.get("user_id")
#             if not user_id:
#                 return None, "Failed to extract user ID"

#             REDMINE_URL = os.getenv("REDMINE_URL")
#             if not REDMINE_URL:
#                 return None, "Environment variable 'REDMINE_URL' is not set"

#             ml_issues_url = f"{REDMINE_URL}/issues.json?tracker_id=4&project_id=1&status_id=!7"
#             response = requests.get(
#                 ml_issues_url,
#                 headers={
#                     "X-Redmine-API-Key": user_api_key,
#                     "Content-Type": "application/json"
#                 }
#             )

#             if response.status_code != 200:
#                 return None, f"Failed to fetch ML issues: {response.status_code} - {response.text}"

#             issues = response.json().get("issues", [])
#             summary_list = []

#             for issue in issues:
#                 assigned_to = issue.get("assigned_to", {})
#                 assigned_to_id = assigned_to.get("id")

#                 # Filter: only issues assigned to current user
#                 if assigned_to_id != user_id:
#                     continue

#                 custom_fields = issue.get("custom_fields", [])

#                 summary = {
#                     "id": issue.get("id"),
#                     "subject": issue.get("subject"),
#                     "assigned_to": assigned_to.get("name"),
#                     "mobile": MLOwnerService.get_custom_field_value(custom_fields, "Mobile Number"),
#                     "district": MLOwnerService.get_custom_field_value(custom_fields, "Administrative District"),
#                     "date_created": issue.get("created_on"),
#                     "status": issue.get("status", {}).get("name"),
#                 }

#                 summary_list.append(summary)

#             return summary_list, None

#         except Exception as e:
#             return None, f"Server error: {str(e)}"
        
#     @staticmethod
#     def update_royalty_field(token, issue_id, royalty_amount):
#         try:
#             user_api_key = JWTUtils.get_api_key_from_token(token)
#             if not user_api_key:
#                 return False, "Invalid or missing API key in token"

#             REDMINE_URL = os.getenv("REDMINE_URL")
#             if not REDMINE_URL:
#                 return False, "Environment variable 'REDMINE_URL' is not set"

#             issue_url = f"{REDMINE_URL}/issues/{issue_id}.json"

#             # Step 1: Fetch current issue to read existing royalty value
#             get_response = requests.get(
#                 issue_url,
#                 headers={
#                     "X-Redmine-API-Key": user_api_key,
#                     "Content-Type": "application/json"
#                 }
#             )

#             if get_response.status_code != 200:
#                 return False, f"Failed to fetch issue: {get_response.status_code} - {get_response.text}"

#             issue_data = get_response.json().get("issue", {})
#             custom_fields = issue_data.get("custom_fields", [])

#             # Find existing royalty value
#             existing_royalty = 0
#             for field in custom_fields:
#                 if field.get("id") == 18:  # Royalty field ID
#                     try:
#                         existing_royalty = int(field.get("value", 0)) if field.get("value") else 0
#                     except ValueError:
#                         existing_royalty = 0
#                     break

#             # Step 2: Add new royalty to existing as integer
#             new_total_royalty = existing_royalty + int(royalty_amount)

#             # Step 3: Update the issue with new total
#             payload = {
#                 "issue": {
#                     "custom_fields": [
#                         {
#                             "id": 18,
#                             "value": str(new_total_royalty)
#                         }
#                     ]
#                 }
#             }

#             update_response = requests.put(
#                 issue_url,
#                 headers={
#                     "X-Redmine-API-Key": user_api_key,
#                     "Content-Type": "application/json"
#                 },
#                 json=payload
#             )

#             if update_response.status_code != 204:
#                 return False, f"Failed to update issue: {update_response.status_code} - {update_response.text}"

#             return True, None

#         except Exception as e:
#             return False, f"Server error: {str(e)}"


