from typing import Dict, List, Optional, Tuple
import requests
import os
from dotenv import load_dotenv
import json
from datetime import date, timedelta , datetime 
from services.general_public_service import GeneralPublicService
from utils.jwt_utils import JWTUtils
from utils.MLOUtils import MLOUtils
from flask import request
from utils.limit_utils import LimitUtils
from werkzeug.utils import secure_filename
import time
from hashlib import md5
from utils.constants import REDMINE_API_ERROR_MSG,CONTENT_TYPE_JSON
from collections import Counter, defaultdict
from datetime import datetime



load_dotenv()

MINING_LICENSE_NUMBER = "Mining License Number"
DIVISIONAL_SECRETARY = "Divisional Secretary Division"
NAME_VILLAGE = "Name of village "
EXPLORATION_LICENSE_NO = "Exploration Licence No"
LAND_NAME_LICENCE_DETAILS = "Land Name(Licence Details)"
LAND_OWNER_NAME = "Land owner name"
GRAMA_NILADHARI = "Grama Niladhari Division"
ADMINISTRATIVE_DISTRICT = "Administrative District"
MOBILE_NUMBER = "Mobile Number"
ECONOMIC_VIABILITY_REPORT = "Economic Viability Report"
LICENSE_FEE_RECEIPT = "License fee receipt"
DETAILED_MINE_RESTORATION_PLAN = "Detailed Mine Restoration Plan"
DEED_AND_SURVEY_PLAN = "Deed and Survey Plan"
PAYMENT_RECEIPT = "Payment Receipt"
LICENSE_BOUNDARY_SURVEY = "License Boundary Survey"
REDMINE_URL_NOT_SET= "Environment variable 'REDMINE_URL' is not set"



class MLOwnerService:

    ORS_API_KEY = os.getenv("ORS_API_KEY")
    INVALID_API_KEY_MSG = "Invalid or missing API key in the token"
    

    @staticmethod
    def mining_licenses(token):
        try:
            redmine_url = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)
            if not redmine_url or not api_key:
                return None, REDMINE_API_ERROR_MSG

            result = JWTUtils.decode_jwt_and_get_user_id(token)
            if not result['success']:
                return None, result['message']
            user_id = result['user_id']

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": CONTENT_TYPE_JSON
            }

            issues, error = MLOwnerService._fetch_all_issues(redmine_url, headers, user_id)
            if error:
                return None, error

            parsed_issues = [MLOwnerService._parse_issue(issue) for issue in issues]
            return parsed_issues, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def _fetch_all_issues(url, headers, user_id):
        offset = 0
        all_issues = []
        total_count = None

        while True:
            params = {
                "project_id": 1,
                "tracker_id": 4,
                "status_id": 7,
                "assigned_to_id": user_id,
                "offset": offset
            }
            response = requests.get(f"{url}/issues.json", headers=headers, params=params)
            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

            data = response.json()
            issues = data.get("issues", [])
            if total_count is None:
                total_count = data.get("total_count", 0)

            all_issues.extend(issues)
            offset += len(issues)
            if offset >= total_count or not issues:
                break

        return all_issues, None

    @staticmethod
    def _parse_issue(issue):
        assigned_to = issue.get("assigned_to", {})
        custom_fields = {field["name"]: field["value"] for field in issue.get("custom_fields", [])}

        owner_name = assigned_to.get("name", "N/A")
        license_number = custom_fields.get(MINING_LICENSE_NUMBER, "N/A")
        divisional_secretary = custom_fields.get(DIVISIONAL_SECRETARY, "N/A")
        location = custom_fields.get(NAME_VILLAGE, "N/A")
        start_date = issue.get("start_date", "N/A")
        due_date = issue.get("due_date", "N/A")
        royalty = custom_fields.get("Royalty", "N/A")
        status = issue.get("status", {}).get("name", "Unknown")

        remaining_cubes = MLOwnerService._safe_int(custom_fields.get("Remaining", "0"))
        status = MLOwnerService._update_status_if_expired(due_date, status)

        return {
            "License Number": license_number,
            DIVISIONAL_SECRETARY: divisional_secretary,
            "Owner Name": owner_name,
            "Location": location,
            "Start Date": start_date,
            "Due Date": due_date,
            "Remaining Cubes": remaining_cubes,
            "Royalty": royalty,
            "Status": status
        }

    @staticmethod
    def _update_status_if_expired(due_date_str, current_status):
        if due_date_str == "N/A":
            return current_status
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            if datetime.now().date() > due_date:
                return "Expired"
        except ValueError:
            pass
        return current_status

    @staticmethod
    def _safe_int(value):
        try:
            return int(value.strip()) if value.strip() else 0
        except (ValueError, AttributeError):
            return 0



    @staticmethod
    def get_mining_home_licenses(token):
        try:
            redmine_url = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)
            if not redmine_url or not api_key:
                return None, REDMINE_API_ERROR_MSG

            result = JWTUtils.decode_jwt_and_get_user_id(token)
            if not result["success"]:
                return None, result["message"]
            user_id = result["user_id"]

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": CONTENT_TYPE_JSON
            }

            issues, error = MLOwnerService._fetch_all_issues_with_status(
                redmine_url, headers, user_id, status_id=7
            )
            if error:
                return None, error

            filtered = [
                MLOwnerService._parse_mining_home_issue(issue)
                for issue in issues
                if MLOwnerService._is_valid_home_license(issue)
            ]

            return filtered, None

        except Exception as e:
            return None, f"Server error: {str(e)}"



    @staticmethod
    def _fetch_all_issues_with_status(url, headers, user_id, status_id):
        offset = 0
        all_issues = []
        total_count = None

        while True:
            params = {
                "project_id": 1,
                "tracker_id": 4,
                "status_id": status_id,
                "assigned_to_id": user_id,
                "offset": offset
            }
            response = requests.get(f"{url}/issues.json", headers=headers, params=params)
            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

            data = response.json()
            issues = data.get("issues", [])
            if total_count is None:
                total_count = data.get("total_count", 0)

            all_issues.extend(issues)
            offset += len(issues)
            if offset >= total_count or not issues:
                break

        return all_issues, None

    @staticmethod
    def _is_valid_home_license(issue):
        due_date = issue.get("due_date", "N/A")
        if due_date == "N/A":
            return False
        try:
            due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
            if due_date_obj <= datetime.now().date():
                return False
        except ValueError:
            return False

        custom_fields = {f["name"]: f["value"] for f in issue.get("custom_fields", [])}
        remaining_str = custom_fields.get("Remaining", "0")
        try:
            return int(remaining_str.strip()) > 0
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def _parse_mining_home_issue(issue):
        custom_fields = {f["name"]: f["value"] for f in issue.get("custom_fields", [])}
        assigned_to = issue.get("assigned_to", {})

        def safe_int(value):
            try:
                return int(value.strip()) if value.strip() else 0
            except (ValueError, AttributeError):
                return 0

        return {
            "Issue ID": issue.get("id", "N/A"),
            "License Number": custom_fields.get(MINING_LICENSE_NUMBER, "N/A"),
            DIVISIONAL_SECRETARY: custom_fields.get(DIVISIONAL_SECRETARY, "N/A"),
            "Owner Name": assigned_to.get("name", "N/A"),
            "Location": custom_fields.get(NAME_VILLAGE, "N/A"),
            "Start Date": issue.get("start_date", "N/A"),
            "Due Date": issue.get("due_date", "N/A"),
            "Remaining Cubes": safe_int(custom_fields.get("Remaining", "0")),
            "Royalty": custom_fields.get("Royalty", "N/A")
        }


    @staticmethod
    def _safe_int(val, default=0):
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _fetch_mining_issue(redmine_url, api_key, issue_id):
        url = f"{redmine_url}/issues/{issue_id}.json"
        headers = {
            "Content-Type": CONTENT_TYPE_JSON,
            "X-Redmine-API-Key": api_key
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None, f"Failed to fetch mining license issue: {response.status_code} - {response.text}"
        data = response.json()
        issue = data.get("issue")
        if not issue:
            return None, "Mining license issue not found"
        return issue, None

    @staticmethod
    def _update_mining_issue(redmine_url, api_key, issue_id, payload):
        url = f"{redmine_url}/issues/{issue_id}.json"
        headers = {
            "Content-Type": CONTENT_TYPE_JSON,
            "X-Redmine-API-Key": api_key
        }
        response = requests.put(url, json=payload, headers=headers)
        if response.status_code != 204:
            return f"Failed to update mining license issue"
        return None

    @staticmethod
    def _create_tpl_issue(redmine_url, api_key, payload):
        url = f"{redmine_url}/issues.json"
        headers = {
            "Content-Type": CONTENT_TYPE_JSON,
            "X-Redmine-API-Key": api_key
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            if response.text.strip():
                return response.json(), None
            else:
                return {"message": "TPL issue created, but Redmine returned an empty response"}, None
        return None, response.text or "Failed to create TPL issue"


    @staticmethod
    def create_tpl(data, token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Redmine URL is not configured"

            API_KEY = JWTUtils.get_api_key_from_token(token)
            if not API_KEY:
                return None, "Invalid or missing API key"

            mining_license_number = data.get("mining_license_number")
            if not mining_license_number:
                return None, "Mining license number is required"

            try:
                mining_issue_id = int(mining_license_number.strip().split('/')[-1])
            except (IndexError, ValueError):
                return None, "Invalid mining license number format"

            mining_issue, err = MLOwnerService._fetch_mining_issue(REDMINE_URL, API_KEY, mining_issue_id)
            if err:
                return None, err

            custom_fields = mining_issue.get("custom_fields", [])
            used_field = next((f for f in custom_fields if f.get("name") == "Used"), None)
            remaining_field = next((f for f in custom_fields if f.get("name") == "Remaining"), None)
            royalty_field = next((f for f in custom_fields if f.get("name") == "Royalty"), None)
            if not used_field or not remaining_field or not royalty_field:
                return None, "Required fields (Used, Remaining, or Royalty) not found in the mining license issue"

            current_used = MLOwnerService._safe_int(used_field.get("value"))
            current_remaining = MLOwnerService._safe_int(remaining_field.get("value"))
            current_royalty = MLOwnerService._safe_int(royalty_field.get("value"))
            cubes = MLOwnerService._safe_int(data.get("cubes"))

            tpl_cost = cubes * 500
            if current_royalty < tpl_cost:
                return None, f"Insufficient royalty balance. Required: {tpl_cost}, Available: {current_royalty}"

            new_used = current_used + cubes
            new_remaining = current_remaining - cubes
            new_royalty = current_royalty - tpl_cost
            if new_remaining < 0:
                return None, "Insufficient remaining cubes"

            update_payload = {
                "issue": {
                    "custom_fields": [
                        {"id": used_field.get("id"), "value": str(new_used)},
                        {"id": remaining_field.get("id"), "value": str(new_remaining)},
                        {"id": royalty_field.get("id"), "value": str(new_royalty)}
                    ]
                }
            }

            err = MLOwnerService._update_mining_issue(REDMINE_URL, API_KEY, mining_issue_id, update_payload)
            if err:
                return None, err

            route_01 = data.get("route_01", "")
            destination = data.get("destination", "")
            time_result = MLOwnerService.calculate_time(route_01, destination)
            if not time_result.get("success"):
                return None, time_result.get("error")

            time_hours = time_result.get("time_hours", 0)

            result = JWTUtils.decode_jwt_and_get_user_id(token)
            user_id = result['user_id']

            payload = {
                "issue": {
                    "project_id": 1,
                    "tracker_id": 5,
                    "status_id": 8,
                    "priority_id": 2,
                    "subject": "TPL",
                    "start_date": data.get("start_date", date.today().isoformat()),
                    "assigned_to_id": user_id,
                    "estimated_hours": time_hours,
                    "custom_fields": [
                        {"id": 53, "name": "Lorry Number", "value": data.get("lorry_number", "")},
                        {"id": 54, "name": "Driver Contact", "value": data.get("driver_contact", "")},
                        {"id": 55, "name": "Route 01", "value": data.get("route_01", "")},
                        {"id": 56, "name": "Route 02", "value": data.get("route_02", "")},
                        {"id": 57, "name": "Route 03", "value": data.get("route_03", "")},
                        {"id": 58, "name": "Cubes", "value": str(cubes)},
                        {"id": 59, "name": MINING_LICENSE_NUMBER, "value": mining_license_number},
                        {"id": 68, "name": "Destination", "value": destination}
                    ]
                }
            }

            return MLOwnerService._create_tpl_issue(REDMINE_URL, API_KEY, payload)

        except Exception as e:
            return None, str(e)

        
    @staticmethod
    def calculate_time(city1, city2):
        """
        Calculate the distance between two cities using OpenRouteService API and return the time in hours.

        Args:
            city1 (str): Name of the first city.
            city2 (str): Name of the second city.

        Returns:
            dict: A dictionary containing the time in hours or an error message.
        """
        try:
            # Step 1: Geocode cities to get coordinates
            def geocode_location(city_name): 
                url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json"
                headers = {
                    "User-Agent": "MiningLicenseTPL/1.0 (it-support@miningcompany.com)"  # <-- important for Nominatim usage policy
                }
                response_first = requests.get(url, headers=headers, timeout=5)
                
                if response_first.status_code != 200:
                    raise ValueError(f"Geocoding failed with status code {response_first.status_code}, body: {response_first.text}")

                try:
                    response = response_first.json()
                except ValueError:
                    raise ValueError(f"Invalid JSON response: {response_first.text}")  
                
                if response:
                    lat = float(response[0]['lat'])
                    lon = float(response[0]['lon'])
                    return lon, lat  # Return as [longitude, latitude]
                else:
                    raise ValueError(f"Location '{city_name}' not found")

            # Geocode both cities
            coord1 = geocode_location(city1)
            time.sleep(1)
            coord2 = geocode_location(city2)


            # Step 2: Calculate distance using OpenRouteService
            url = "https://api.openrouteservice.org/v2/directions/driving-car"
            headers = {
                "Authorization": MLOwnerService.ORS_API_KEY,
                "Content-Type": CONTENT_TYPE_JSON
            }
            body = {
                "coordinates": [coord1, coord2],
                "units": "km"
            }
            response = requests.post(url, headers=headers, json=body).json()

            # Extract distance from the response
            distance_km = response['routes'][0]['summary']['distance']

            # Calculate the time in hours: (distance / 30 km/h) + 2 hours
            time_hours = (distance_km / 30) + 2

            # Return the time in hours
            return {
                "success": True,
                "city1": city1,
                "city2": city2,
                "time_hours": int(round(time_hours))
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


   
    def update_issue(self, issue_id, data):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")

            if not REDMINE_URL or not API_KEY:
                return None, REDMINE_API_ERROR_MSG
            headers = {
                "X-Redmine-API-Key": API_KEY,  # Include the token for authorization
                "Content-Type": CONTENT_TYPE_JSON
            }
            

            url = f"{REDMINE_URL}/issues/{issue_id}.json"
           
            response = requests.put(
                url,
                json = data,  # Ensure correct JSON structure
                headers=headers
            )


            # Check if response is empty (204 No Content)
            if response.status_code == 204:
                return {"message": "Issue updated successfully, but no content returned"}, None

            # If status is not OK, return the error message
            if response.status_code != 200:
                return None, f"Failed to update issue: {response.status_code} - {response.text}"

            # Attempt to parse the JSON response
            try:
                issue = response.json().get("issue", {})
                return issue, None
            except json.JSONDecodeError:
                return None, "Invalid JSON response from server"

        except Exception as e:
            return None, f"Server error: {str(e)}"

      
    @staticmethod
    def _get_redmine_url_and_api_key(token: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        REDMINE_URL = os.getenv("REDMINE_URL")
        API_KEY = JWTUtils.get_api_key_from_token(token)
        if not REDMINE_URL or not API_KEY:
            return None, None, REDMINE_API_ERROR_MSG
        return REDMINE_URL, API_KEY, None

    @staticmethod
    def _decode_user_id(token: str) -> Tuple[Optional[int], Optional[str]]:
        result = JWTUtils.decode_jwt_and_get_user_id(token)
        if not result['success']:
            return None, result['message']
        return result['user_id'], None

    @staticmethod
    def _find_issue_with_l_number(issues: list, l_number: str) -> Optional[int]:
        l_number_lower = l_number.strip().lower()
        for issue in issues:
            for cf in issue.get("custom_fields", []):
                if cf.get("id") == 101 and str(cf.get("value", "")).strip().lower() == l_number_lower:
                    return issue["id"]
        return None

    @staticmethod
    def _fetch_issues_page(redmine_url: str, headers: dict, user_id: int, offset: int, limit: int) -> Tuple[Optional[list], Optional[str]]:
        issues_url = (
            f"{redmine_url}/issues.json?"
            f"project_id=1&tracker_id=4&status_id=7"
            f"&assigned_to_id={user_id}"
            f"&limit={limit}&offset={offset}"
        )
        try:
            resp = requests.get(issues_url, headers=headers, timeout=30)
            if resp.status_code != 200:
                return None, f"Failed to fetch issues: {resp.status_code} - {resp.text}"
            return resp.json().get("issues", []), None
        except requests.exceptions.RequestException as e:
            return None, f"Network error connecting to Redmine: {str(e)}"

    @staticmethod
    def _fetch_issue_detail(redmine_url: str, headers: dict, issue_id: int) -> Tuple[Optional[dict], Optional[str]]:
        detail_url = f"{redmine_url}/issues/{issue_id}.json"
        try:
            resp = requests.get(detail_url, headers=headers, timeout=30)
            if resp.status_code != 200:
                return None, f"Failed to fetch issue details: {resp.status_code} - {resp.text}"
            return resp.json().get("issue", {}), None
        except requests.exceptions.RequestException as e:
            return None, f"Network error connecting to Redmine: {str(e)}"

    @staticmethod
    def ml_detail(l_number: str, token: str) -> Tuple[Optional[Dict], Optional[str]]:
        REDMINE_URL, API_KEY, error = MLOwnerService._get_redmine_url_and_api_key(token)
        if error:
            return None, error

        user_id, error = MLOwnerService._decode_user_id(token)
        if error:
            return None, error

        headers = {
            "X-Redmine-API-Key": API_KEY,
            "Content-Type": CONTENT_TYPE_JSON
        }

        default_limit = 100
        offset = 0
        found_issue = None
        done = False

        while not done:
            issues, error = MLOwnerService._fetch_issues_page(REDMINE_URL, headers, user_id, offset, default_limit)
            if error:
                return None, error
            if not issues or len(issues) < default_limit:
                done = True

            issue_id = MLOwnerService._find_issue_with_l_number(issues, l_number)
            if not issue_id:
                offset += default_limit
                continue

            issue_data, error = MLOwnerService._fetch_issue_detail(REDMINE_URL, headers, issue_id)
            if error:
                return None, error

            cf_dict = {f["name"]: f.get("value") for f in issue_data.get("custom_fields", [])}
            found_issue = {
                "id": issue_data.get("id"),
                "subject": issue_data.get("subject"),
                "status": issue_data.get("status", {}).get("name"),
                "author": issue_data.get("author", {}).get("name"),
                "assigned_to": issue_data.get("assigned_to", {}).get("name"),
                "start_date": issue_data.get("start_date"),
                "due_date": issue_data.get("due_date"),
                "created_on": issue_data.get("created_on"),
                "updated_on": issue_data.get("updated_on"),
                # Add your custom fields here:
                "royalty": cf_dict.get("Royalty"),
                "exploration_licence_no": cf_dict.get(EXPLORATION_LICENSE_NO),
                "land_name": cf_dict.get(LAND_NAME_LICENCE_DETAILS),
                "land_owner_name": cf_dict.get(LAND_OWNER_NAME),
                "village_name": cf_dict.get(NAME_VILLAGE),
                "grama_niladhari_division": cf_dict.get(GRAMA_NILADHARI),
                "divisional_secretary_division": cf_dict.get(DIVISIONAL_SECRETARY),
                "administrative_district": cf_dict.get(ADMINISTRATIVE_DISTRICT),
                "capacity": cf_dict.get("Capacity"),
                "used": cf_dict.get("Used"),
                "remaining": cf_dict.get("Remaining"),
                "mobile_number": cf_dict.get(MOBILE_NUMBER),
                "google_location": cf_dict.get("Google location "),
                "reason_for_hold": cf_dict.get("Reason For Hold"),
                "economic_viability_report": cf_dict.get(ECONOMIC_VIABILITY_REPORT),
                "detailed_mine_restoration_plan": cf_dict.get(DETAILED_MINE_RESTORATION_PLAN),
                "deed_and_survey_plan": cf_dict.get(DEED_AND_SURVEY_PLAN),
                "payment_receipt": cf_dict.get(PAYMENT_RECEIPT),
                "license_boundary_survey": cf_dict.get(LICENSE_BOUNDARY_SURVEY),
                "mining_license_number": cf_dict.get(MINING_LICENSE_NUMBER),
            }
            break  # Found issue, exit loop

        if found_issue:
            return found_issue, None
        else:
            return None, "No mining license found for the given number."



        
        
    @staticmethod
    def user_detail(user_id, token):
        api_key = JWTUtils.get_api_key_from_token(token)
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")

            if not REDMINE_URL or not api_key:
                return None, REDMINE_API_ERROR_MSG
            headers = {
                "X-Redmine-API-Key": api_key,  # Include the token for authorization
                "Content-Type": CONTENT_TYPE_JSON
            }
            url = f"{REDMINE_URL}/users/{user_id}.json"
           
            response = requests.get(
                url,  # Ensure correct JSON structure
                headers=headers
            )

            if response.status_code != 200:
                return None, f"Failed to fetch issue: {response.status_code} - {response.text}"

            user_detail = response.json().get("user", {})


            return user_detail, None  # Returning filtered issues and no error

        except Exception as e:
            return None, f"Server error: {str(e)}"
     

    @staticmethod
    def view_tpls(token: str, mining_license_number: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
        try:
            if not mining_license_number or not mining_license_number.strip():
                return None, "Valid mining license number is required"
            mining_license_number = mining_license_number.strip()

            redmine_url, api_key, user_id, error = MLOwnerService._get_redmine_config_and_user(token)
            if error:
                return None, error

            headers = {
                "Content-Type": CONTENT_TYPE_JSON,
                "X-Redmine-API-Key": api_key
            }

            issues, error = MLOwnerService._fetch_tpl_issues(redmine_url, user_id, headers)
            if error:
                return None, error

            tpl_list = MLOwnerService._process_issues(issues, mining_license_number)
            print(f"Finished processing. Returning {len(tpl_list)} TPLs.")
            return tpl_list, None

        except requests.exceptions.RequestException as e:
            return None, f"Network error connecting to Redmine: {str(e)}"
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None, f"Processing error: {str(e)}"

   

    @staticmethod
    def _get_redmine_config_and_user(token: str) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[str]]:
        redmine_url = os.getenv("REDMINE_URL")
        api_key = JWTUtils.get_api_key_from_token(token)
        if not redmine_url or not api_key:
            return None, None, None, "System configuration error - missing Redmine URL or API Key"
        
        result = JWTUtils.decode_jwt_and_get_user_id(token)
        if not result['success']:
            return None, None, None, result['message']
        
        return redmine_url, api_key, result['user_id'], None

    @staticmethod
    def _fetch_tpl_issues(redmine_url: str, user_id: int, headers: Dict) -> Tuple[Optional[List[Dict]], Optional[str]]:
        tpl_url = (
            f"{redmine_url}/issues.json?"
            f"project_id=1&tracker_id=5&assigned_to_id={user_id}&limit=100&offset=0"
        )
        response = requests.get(tpl_url, headers=headers, timeout=30)
        if response.status_code != 200:
            return None, f"Redmine API error ({response.status_code}): {response.text}"
        
        try:
            return response.json().get("issues", []), None
        except ValueError:
            return None, "Failed to parse response from Redmine"

    @staticmethod
    def _process_issues(issues: List[Dict], mining_license_number: str) -> List[Dict]:
        tpl_list = []
        now = datetime.now()

        for issue in issues:
            try:
                custom_fields = issue.get("custom_fields", [])
                mln = next((f.get("value") for f in custom_fields if f.get("id") == 59), None)
                if mln != mining_license_number:
                    continue

                tpl_list.append(MLOwnerService._build_tpl_record(issue, custom_fields, mining_license_number, now))
            except Exception as e:
                print(f"Error processing issue {issue.get('id', 'N/A')}: {str(e)}")
                continue

        return tpl_list

    @staticmethod
    def _build_tpl_record(issue: Dict, custom_fields: List[Dict], mln: str, now: datetime) -> Dict:
        cf_dict = {field["name"]: field["value"] for field in custom_fields}
        created_on = issue.get("created_on")
        est_hours = issue.get("estimated_hours")
        status = "Undetermined"

        if created_on and est_hours is not None:
            try:
                created_dt = datetime.strptime(created_on, "%Y-%m-%dT%H:%M:%SZ")
                expiry_dt = created_dt + timedelta(hours=float(est_hours))
                status = "Active" if now < expiry_dt else "Expired"
            except ValueError:
                pass

        return {
            "tpl_id": issue.get("id"),
            "license_number": mln,
            "subject": issue.get("subject", ""),
            "status": status,
            "lorry_number": cf_dict.get("Lorry Number"),
            "driver_contact": cf_dict.get("Driver Contact"),
            "destination": cf_dict.get("Destination"),
            "Route_01": cf_dict.get("Route 01"),
            "Route_02": cf_dict.get("Route 02"),
            "Route_03": cf_dict.get("Route 03"),
            "cubes": cf_dict.get("Cubes"),
            "Create_Date": created_on,
            "Estimated Hours": est_hours,
        }



    @staticmethod
    def ml_request(data, token, user_mobile):
        try:
            # Get the Redmine URL from environment variables
            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "Redmine URL is not configured"

            # Get the API key from the token
            API_KEY = JWTUtils.get_api_key_from_token(token)
            if not API_KEY:
                return None, "Invalid or missing API key"
            
            headers = {
                "Content-Type": CONTENT_TYPE_JSON,
                "X-Redmine-API-Key": API_KEY
            }
    
            # Prepare the payload for the ML request
            payload = {
                "issue": {
                    "project_id": data.get("project_id", 1),
                    "status_id": data.get("status_id", 8),
                    "priority_id": data.get("priority_id", 2),
                    "assigned_to_id": data.get("assigned_to"),  # Get from data dictionary
                    "author_id": data.get("author"), 
                    "subject": data.get("subject", "ML Request"),
                    "description": data.get("description", ""),
                    "custom_fields": [
                        {"id": 19, "value": data.get("exploration_nb", "")},
                        {"id": 28, "value": data.get("land_name", "")},  
                        {"id": 29, "value": data.get("land_owner_name", "")},
                        {"id": 30, "value": data.get("village_name", "")},
                        {"id": 31, "value": data.get("grama_niladari", "")},
                        {"id": 32, "value": data.get("divisional_secretary_division", "")},
                        {"id": 33, "value": data.get("administrative_district", "")},   
                        {"id": 92, "value": data.get("google_location", "")}, 
                        {"id": 66, "value": user_mobile},
                        *data.get("custom_fields", [])                              
                    ]
                }
            }

            # First create the issue
            response = requests.post(f"{REDMINE_URL}/issues.json", json=payload, headers=headers)
            
            if response.status_code != 201:
                return None, f"Failed to create issue: {response.text}"
        
            issue_id = response.json()["issue"]["id"]
            issue_id = response.json()["issue"]["id"]
        
        # Now, update the Mining License Number field with LLL/100/{issue_id}
            update_payload = {
                "issue": {
                    "custom_fields": [
                        {
                            "id": 101,  # Mining License Number field ID
                            "value": f"ML Request LLL/100/{issue_id}"
                        }
                    ]
                }
            }

            update_response = requests.put(
                f"{REDMINE_URL}/issues/{issue_id}.json",
                headers=headers,
                json=update_payload
            )

            if update_response.status_code != 204:
                return None, f"Failed to update Mining License Number: {update_response.status_code} - {update_response.text}"

            # Return the complete issue data including the updated mining license number
            issue_data = response.json()
            issue_data["issue"]["mining_license_number"] = f"LLL/100/{issue_id}"
            
            return issue_data, None

        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"
        
    @staticmethod
    def get_mining_license_requests(token):
        try:
            user_api_key = JWTUtils.get_api_key_from_token(token)
            if not user_api_key:
                return None, MLOwnerService.INVALID_API_KEY_MSG

            user_response = JWTUtils.decode_jwt_and_get_user_id(token)

            user_id = user_response["user_id"]
            if not user_id:
                return None, f"Failed to extract user info"

            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, REDMINE_URL_NOT_SET

            ml_issues_url = f"{REDMINE_URL}/issues.json?tracker_id=4&project_id=1&status_id=!7"
            response = requests.get(
                ml_issues_url,
                headers={"X-Redmine-API-Key": user_api_key, "Content-Type": CONTENT_TYPE_JSON}
            )

            if response.status_code != 200:
                return None, f"Failed to fetch ML issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])

            formatted_mls = []

            for issue in issues:
                assigned_to = issue.get("assigned_to", {})
                assigned_to_id = assigned_to.get("id")

                # ✅ Filter: only include issues assigned to current user
                if assigned_to_id != user_id:
                    continue

                custom_fields = issue.get("custom_fields", [])
                attachment_urls = MLOwnerService.get_attachment_urls(user_api_key, REDMINE_URL, custom_fields)

                assigned_to_details = None
                if assigned_to_id:
                    user_response = requests.get(
                        f"{REDMINE_URL}/users/{assigned_to_id}.json",
                        headers={"X-Redmine-API-Key": user_api_key, "Content-Type": CONTENT_TYPE_JSON}
                    )
                    if user_response.status_code == 200:
                        assigned_to_details = user_response.json().get("user", {})

                ml_data = {
                    "id": issue.get("id"),
                    "subject": issue.get("subject"),
                    "status": issue.get("status", {}).get("name"),
                    "assigned_to": assigned_to.get("name"),
                    "created_on": issue.get("created_on"),
                    "updated_on": issue.get("updated_on"),
                    "assigned_to_details": {
                        "id": assigned_to_details.get("id"),
                        "name": f"{assigned_to_details.get('firstname', '')} {assigned_to_details.get('lastname', '')}".strip(),
                        "email": assigned_to_details.get("mail"),
                        "custom_fields": assigned_to_details.get("custom_fields", [])
                    } if assigned_to_details else None,
                    "exploration_licence_no": MLOwnerService.get_custom_field_value(custom_fields, EXPLORATION_LICENSE_NO),
                    "land_name": MLOwnerService.get_custom_field_value(custom_fields, LAND_NAME_LICENCE_DETAILS),
                    "land_owner_name": MLOwnerService.get_custom_field_value(custom_fields, LAND_OWNER_NAME),
                    "village_name": MLOwnerService.get_custom_field_value(custom_fields, NAME_VILLAGE),
                    "grama_niladhari_division": MLOwnerService.get_custom_field_value(custom_fields, GRAMA_NILADHARI),
                    "divisional_secretary_division": MLOwnerService.get_custom_field_value(custom_fields, DIVISIONAL_SECRETARY),
                    "administrative_district": MLOwnerService.get_custom_field_value(custom_fields, ADMINISTRATIVE_DISTRICT),
                    "google_location": MLOwnerService.get_custom_field_value(custom_fields, "Google location "),
                    "mobile_number": MLOwnerService.get_custom_field_value(custom_fields, MOBILE_NUMBER),
                    "detailed_mine_restoration_plan": attachment_urls.get(DETAILED_MINE_RESTORATION_PLAN),
                    "economic_viability_report": attachment_urls.get(ECONOMIC_VIABILITY_REPORT),
                    "license_boundary_survey": attachment_urls.get(LICENSE_BOUNDARY_SURVEY),
                    "deed_and_survey_plan": attachment_urls.get(DEED_AND_SURVEY_PLAN),
                    "payment_receipt": attachment_urls.get(PAYMENT_RECEIPT),
                }

                formatted_mls.append(ml_data)

            return formatted_mls, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

        
    @staticmethod
    def get_attachment_urls(api_key, redmine_url, custom_fields):
        try:
            # Define the mapping of custom field names to their attachment IDs
            file_fields = {
                ECONOMIC_VIABILITY_REPORT: None,
                LICENSE_FEE_RECEIPT: None,
                DETAILED_MINE_RESTORATION_PLAN: None,
                "Professional": None,
                DEED_AND_SURVEY_PLAN: None,
                PAYMENT_RECEIPT: None
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
                        headers={"X-Redmine-API-Key": api_key, "Content-Type": CONTENT_TYPE_JSON}
                    )

                    if response.status_code == 200:
                        attachment_data = response.json().get("attachment", {})
                        file_urls[field_name] = attachment_data.get("content_url", "")

            return file_urls

        except Exception:
            return {}


    @staticmethod
    def get_custom_field_value(custom_fields, field_name):
        """Helper function to extract custom field value by name."""
        for field in custom_fields:
            if field.get("name") == field_name:
                return field.get("value")
        return None
    

    @staticmethod
    def get_pending_mining_license_details(token):
        try:
            user_api_key, user_id, redmine_url, err = MLOwnerService._validate_and_extract(token)
            if err:
                return None, err

            issues = MLOwnerService._fetch_issues(
                f"{redmine_url}/issues.json?tracker_id=4&project_id=1&status_id=!7", user_api_key)
            
            summaries = [
                MLOwnerService._process_issue(issue, user_id, redmine_url, user_api_key)
                for issue in issues
                if issue.get("assigned_to", {}).get("id") == user_id
            ]

            summaries = [s for s in summaries if s]  # filter out None
            return summaries, None

        except Exception as e:
            return None, f"Server error: {str(e)}"


    @staticmethod
    def _validate_and_extract(token):
        api_key = JWTUtils.get_api_key_from_token(token)
        if not api_key:
            return None, None, None, MLOwnerService.INVALID_API_KEY_MSG

        user_data = JWTUtils.decode_jwt_and_get_user_id(token)
        user_id = user_data.get("user_id")
        if not user_id:
            return None, None, None, "Failed to extract user info"

        redmine_url = os.getenv("REDMINE_URL")
        if not redmine_url:
            return None, None, None, REDMINE_URL_NOT_SET

        return api_key, user_id, redmine_url, None


    @staticmethod
    def _fetch_issues(url, api_key):
        response = requests.get(url, headers={
            "X-Redmine-API-Key": api_key,
            "Content-Type": CONTENT_TYPE_JSON
        })
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"Failed to fetch issues: {response.status_code} - {response.text}")
        return response.json().get("issues", [])


    @staticmethod
    def _process_issue(issue, user_id, base_url, api_key):
        custom_fields = issue.get("custom_fields", [])
        license_no = MLOwnerService.get_custom_field_value(custom_fields, MINING_LICENSE_NUMBER)

        summary = {
            "mining_license_number": license_no,
            "created_on": issue.get("created_on"),
            "updated_on": issue.get("updated_on"),
            "status": issue.get("status", {}).get("name")
        }

        status_id = issue.get("status", {}).get("id")
        if status_id in (31, 34) and license_no:
            tracker_id = 12 if status_id == 31 else 11
            additional = MLOwnerService._get_tracker_match_data(base_url, tracker_id, api_key, license_no)
            if additional:
                summary.update(additional)

        return summary


    @staticmethod
    def _get_tracker_match_data(base_url, tracker_id, api_key, license_no):
        url = f"{base_url}/issues.json?tracker_id={tracker_id}&project_id=1"
        issues = MLOwnerService._fetch_issues(url, api_key)

        for issue in issues:
            fields = issue.get("custom_fields", [])
            matched_no = MLOwnerService.get_custom_field_value(fields, MINING_LICENSE_NUMBER)
            if matched_no == license_no:
                result = {"start_date": issue.get("start_date")}
                if tracker_id == 11:
                    result["GSMB_physical_meetinglocation"] = MLOwnerService.get_custom_field_value(
                        fields, "GSMB physical meeting location")
                return result

        return None

        
    @staticmethod
    def get_mining_license_by_id(token, issue_id):
        try:
            # 🔐 Extract API key from JWT token
            api_key = JWTUtils.get_api_key_from_token(token)
            if not api_key:
                return None, MLOwnerService.INVALID_API_KEY_MSG

            # 🌍 Load Redmine URL from environment
            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, "REDMINE_URL environment variable not set"

            # 🔗 Fetch issue details
            issue_url = f"{REDMINE_URL}/issues/{issue_id}.json?include=attachments"
            response = requests.get(
                issue_url,
                headers={"X-Redmine-API-Key": api_key, "Content-Type": CONTENT_TYPE_JSON}
            )

            if response.status_code != 200:
                return None, f"Failed to fetch issue: {response.status_code} - {response.text}"

            issue = response.json().get("issue")
            if not issue:
                return None, "Issue data not found"

            # 🗂️ Extract and map custom fields to a dictionary
            custom_fields = issue.get("custom_fields", [])
            custom_field_map = {field["name"]: field.get("value") for field in custom_fields}

            # 📎 Get attachment URLs
            attachments = MLOwnerService.get_attachment_urls(api_key, REDMINE_URL, custom_fields)

            # 🧾 Build the final structured response
            formatted_issue = {
                "id": issue.get("id"),
                "subject": issue.get("subject"),
                "status": issue.get("status", {}).get("name"),
                "author": issue.get("author", {}).get("name"),
                "assigned_to": issue.get("assigned_to", {}).get("name"),
                "start_date": issue.get("start_date"),
                "due_date": issue.get("due_date"),
                "exploration_licence_no": custom_field_map.get(EXPLORATION_LICENSE_NO),
                # "applicant_or_company_name": custom_field_map.get("Name of Applicant OR Company"),
                "land_name": custom_field_map.get(LAND_NAME_LICENCE_DETAILS),
                "land_owner_name": custom_field_map.get(LAND_OWNER_NAME),
                "village_name": custom_field_map.get(NAME_VILLAGE),
                "grama_niladhari_division": custom_field_map.get(GRAMA_NILADHARI),
                "divisional_secretary_division": custom_field_map.get(DIVISIONAL_SECRETARY),
                "administrative_district": custom_field_map.get(ADMINISTRATIVE_DISTRICT),
                "capacity": custom_field_map.get("Capacity"),
                "used": custom_field_map.get("Used"),
                "remaining": custom_field_map.get("Remaining"),
                "royalty": custom_field_map.get("Royalty"),
                "license_number": custom_field_map.get(MINING_LICENSE_NUMBER),
                "mining_license_number": custom_field_map.get(MINING_LICENSE_NUMBER),
                "mobile_number": custom_field_map.get(MOBILE_NUMBER),
                "reason_for_hold":custom_field_map.get("Reason For Hold"),
                "economic_viability_report": attachments.get(ECONOMIC_VIABILITY_REPORT),
                "license_fee_receipt": attachments.get(LICENSE_FEE_RECEIPT),
                "detailed_mine_restoration_plan": attachments.get(DETAILED_MINE_RESTORATION_PLAN),
                # "professional": attachments.get("Professional"),
                "deed_and_survey_plan": attachments.get(DEED_AND_SURVEY_PLAN),
                "payment_receipt": attachments.get(PAYMENT_RECEIPT),
                "license_boundary_survey": attachments.get(LICENSE_BOUNDARY_SURVEY)
            }

            return formatted_issue, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def get_mining_license_summary(token):
        try:
            user_api_key = JWTUtils.get_api_key_from_token(token)
            if not user_api_key:
                return None, MLOwnerService.INVALID_API_KEY_MSG

            user_response = JWTUtils.decode_jwt_and_get_user_id(token)
            user_id = user_response.get("user_id")
            if not user_id:
                return None, "Failed to extract user ID"

            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, REDMINE_URL_NOT_SET

            ml_issues_url = f"{REDMINE_URL}/issues.json?tracker_id=4&project_id=1&status_id=!7"
            response = requests.get(
                ml_issues_url,
                headers={
                    "X-Redmine-API-Key": user_api_key,
                    "Content-Type": CONTENT_TYPE_JSON
                }
            )

            if response.status_code != 200:
                return None, f"Failed to fetch ML issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])
            summary_list = []

            for issue in issues:
                assigned_to = issue.get("assigned_to", {})
                assigned_to_id = assigned_to.get("id")

                # Filter: only issues assigned to current user
                if assigned_to_id != user_id:
                    continue

                custom_fields = issue.get("custom_fields", [])

                summary = {
                    "id": issue.get("id"),
                    "subject": issue.get("subject"),
                    "assigned_to": assigned_to.get("name"),
                    "mobile": MLOwnerService.get_custom_field_value(custom_fields, MOBILE_NUMBER),
                    "district": MLOwnerService.get_custom_field_value(custom_fields, ADMINISTRATIVE_DISTRICT),
                    "date_created": issue.get("created_on"),
                    "status": issue.get("status", {}).get("name"),
                }

                summary_list.append(summary)

            return summary_list, None

        except Exception as e:
            return None, f"Server error: {str(e)}"
        
    @staticmethod
    def update_royalty_field(token, issue_id, royalty_amount):
        try:
            user_api_key = JWTUtils.get_api_key_from_token(token)
            if not user_api_key:
                return False, MLOwnerService.INVALID_API_KEY_MSG

            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return False, REDMINE_URL_NOT_SET

            issue_url = f"{REDMINE_URL}/issues/{issue_id}.json"

            # Step 1: Fetch current issue to read existing royalty value
            get_response = requests.get(
                issue_url,
                headers={
                    "X-Redmine-API-Key": user_api_key,
                    "Content-Type": CONTENT_TYPE_JSON
                }
            )

            if get_response.status_code != 200:
                return False, f"Failed to fetch issue: {get_response.status_code} - {get_response.text}"

            issue_data = get_response.json().get("issue", {})
            custom_fields = issue_data.get("custom_fields", [])

            # Find existing royalty value
            existing_royalty = 0
            for field in custom_fields:
                if field.get("id") == 18:  # Royalty field ID
                    try:
                        existing_royalty = int(field.get("value", 0)) if field.get("value") else 0
                    except ValueError:
                        existing_royalty = 0
                    break

            # Step 2: Add new royalty to existing as integer
            new_total_royalty = existing_royalty + int(royalty_amount)

            # Step 3: Update the issue with new total
            payload = {
                "issue": {
                    "custom_fields": [
                        {
                            "id": 18,
                            "value": str(new_total_royalty)
                        }
                    ]
                }
            }

            update_response = requests.put(
                issue_url,
                headers={
                    "X-Redmine-API-Key": user_api_key,
                    "Content-Type": CONTENT_TYPE_JSON
                },
                json=payload
            )

            if update_response.status_code != 204:
                return False, f"Failed to update issue: {update_response.status_code} - {update_response.text}"

            return True, None

        except Exception as e:
            return False, f"Server error: {str(e)}"


    @staticmethod
    def get_top_lorry_numbers(token: str, limit=3):
        try:
            redmine_url = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)
            if not redmine_url or not api_key:
                return [], "Redmine URL or API key not set"

            result = JWTUtils.decode_jwt_and_get_user_id(token)
            if not result['success']:
                return [], result.get('message', 'Failed to decode token')

            user_id = result['user_id']
            headers = {
                "Content-Type": CONTENT_TYPE_JSON,
                "X-Redmine-API-Key": api_key
            }

            offset = 0
            all_issues = []
            while True:
                params = {
                    "project_id": 1,
                    "tracker_id": 5,
                    "assigned_to_id": user_id,
                    "limit": 100,
                    "offset": offset
                }
                response = requests.get(f"{redmine_url}/issues.json", headers=headers, params=params)
                if response.status_code != 200:
                    return [], f"Failed to fetch issues: {response.status_code}"
                data = response.json()
                issues = data.get("issues", [])
                if not issues:
                    break
                all_issues.extend(issues)
                offset += len(issues)

            # Map lorry numbers to contact numbers
            lorry_contact_map = []
            for issue in all_issues:
                lorry_number = None
                driver_contact = None
                for f in issue.get("custom_fields", []):
                    if f["name"] == "Lorry Number":
                        lorry_number = f["value"]
                    elif f["name"] == "Driver Contact":
                        driver_contact = f["value"]
                if lorry_number:
                    lorry_contact_map.append((lorry_number, driver_contact))

            # Count frequency of lorry numbers
            lorry_counts = Counter([lc[0] for lc in lorry_contact_map])
            most_common = [num for num, _ in lorry_counts.most_common(limit)]

            # Final result with contact numbers
            result_list = []
            for lorry in most_common:
                contact = next((c for (ln, c) in lorry_contact_map if ln == lorry), None)
                result_list.append({
                    "lorry_number": lorry,
                    "driver_contact": contact
                })

            return result_list, None

        except Exception as e:
            return [], str(e)