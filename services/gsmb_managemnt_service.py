import requests
import os
from dotenv import load_dotenv
from utils.jwt_utils import JWTUtils
from flask import jsonify
from utils.limit_utils import LimitUtils    
from utils.constants import REDMINE_API_ERROR_MSG,API_KEY_MISSING_ERROR,CONTENT_TYPE_JSON


load_dotenv()

USER_AGENT = "GSMB-Management-Service/1.0"
NIC_BACK_IMAGE_FIELD = "NIC back image"
NIC_FRONT_IMAGE_FIELD = "NIC front image"
USER_TYPE_FIELD = "User Type"
WORK_ID_FIELD = "work ID"

class GsmbManagmentService:
    @staticmethod
    def _fetch_issues_page(redmine_url, headers, params):
        response = requests.get(f"{redmine_url}/issues.json", headers=headers, params=params)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch issues: {response.status_code} - {response.text}")
        return response.json().get("issues", [])

    @staticmethod
    def _process_issue(issue, monthly_data):
        custom_fields = issue.get("custom_fields", [])
        cube_field = next((f for f in custom_fields if f.get("id") == 58 and f.get("name") == "Cubes"), None)
        if not cube_field or not cube_field.get("value"):
            return
        issue_date = issue.get("created_on")
        if not issue_date:
            return
        month_index = int(issue_date[5:7]) - 1
        month_name = list(monthly_data.keys())[month_index]
        monthly_data[month_name] += float(cube_field["value"])

    @staticmethod
    def monthly_total_sand_cubes(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)
            if not REDMINE_URL:
                return None, REDMINE_API_ERROR_MSG
            if not api_key:
                return None, API_KEY_MISSING_ERROR

            params = {"project_id": 1, "tracker_id": 5}  # TPL
            headers = {"X-Redmine-API-Key": api_key, "Content-Type": CONTENT_TYPE_JSON}
            monthly_data = {m: 0 for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
            offset = 0

            while True:
                params["offset"] = offset
                issues = GsmbManagmentService._fetch_issues_page(REDMINE_URL, headers, params)
                if not issues:
                    break
                for issue in issues:
                    GsmbManagmentService._process_issue(issue, monthly_data)
                offset += len(issues)

            ordered_months = list(monthly_data.keys())
            formatted_data = [{"month": month, "totalCubes": monthly_data[month]} for month in ordered_months]
            return formatted_data, None
        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def safe_float(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def get_redmine_url_and_api_key(token):
        redmine_url = os.getenv("REDMINE_URL")
        api_key = JWTUtils.get_api_key_from_token(token)
        if not redmine_url:
            return None, None, REDMINE_API_ERROR_MSG
        if not api_key:
            return None, None, API_KEY_MISSING_ERROR
        return redmine_url, api_key, None

    @staticmethod
    def fetch_all_issues(redmine_url, headers, params):
        all_issues = []
        offset = 0
        while True:
            paged_params = {**params, "offset": offset}
            response = requests.get(f"{redmine_url}/issues.json", headers=headers, params=paged_params)
            if response.status_code != 200:
                return None, f"Issue fetch failed: {response.status_code} - {response.text}"
            batch = response.json().get("issues", [])
            if not batch:
                break
            all_issues.extend(batch)
            offset += len(batch)
        return all_issues, None

    @staticmethod
    def get_field_value(fields, name):
        return GsmbManagmentService.safe_float(next((f.get("value") for f in fields if f.get("name") == name), None))

    @staticmethod
    def build_holder_entry(issue):
        assigned = issue.get("assigned_to")
        if assigned is None:
            return None
        owner = assigned.get("name")
        if not owner:
            return None
        fields = issue.get("custom_fields", [])
        capacity = GsmbManagmentService.get_field_value(fields, "Capacity")
        used = GsmbManagmentService.get_field_value(fields, "Used")
        if capacity <= 0:
            return None
        percentage_used = round((used / capacity) * 100, 2)
        return {
            "label": owner,
            "value": percentage_used,
            "capacity": capacity
        }

    @staticmethod
    def fetch_top_mining_holders(token):
        try:
            redmine_url, api_key, error = GsmbManagmentService.get_redmine_url_and_api_key(token)
            if error:
                return None, error

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": CONTENT_TYPE_JSON
            }
            params = {
                "project_id": 1,
                "tracker_id": 4
            }

            issues, fetch_error = GsmbManagmentService.fetch_all_issues(redmine_url, headers, params)
            if fetch_error:
                return None, fetch_error

            holders = filter(None, map(GsmbManagmentService.build_holder_entry, issues))
            top_holders = sorted(holders, key=lambda x: x["capacity"], reverse=True)[:10]

            return top_holders, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def safe_float_strict(value):
        if isinstance(value, (int, float)):
            # Accept numeric types directly
            return float(value)
        if isinstance(value, str):
            value = value.strip()
            # Optional: reject empty strings or non-numeric strings strictly
            if value == '':
                return None
            try:
                val = float(value)
                # Reject NaN and Inf values
                if val != val or val == float('inf') or val == float('-inf'):
                    return None
                return val
            except ValueError:
                return None
        # Reject other types strictly
        return None


    @staticmethod
    def is_valid_issue(issue):
        tracker = issue.get("tracker", {})
        status = issue.get("status", {})
        return tracker.get("id") == 4 and tracker.get("name") == "ML" and status.get("name") == "Valid"

    @staticmethod
    def extract_royalty(issue):
        royalty_field = next(
            (f for f in issue.get("custom_fields", []) if f.get("name") == "Royalty"), None
        )
        return GsmbManagmentService.safe_float_strict(royalty_field.get("value", "0") or "0") if royalty_field else 0

    @staticmethod
    def fetch_issues(redmine_url, headers, params):
        try:
            response = requests.get(f"{redmine_url}/issues.json", headers=headers, params=params)
            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"
            return response.json().get("issues", []), None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def fetch_royalty_counts(token):
        redmine_url = os.getenv("REDMINE_URL")
        if not redmine_url:
            return None, REDMINE_API_ERROR_MSG

        api_key = JWTUtils.get_api_key_from_token(token)
        if not api_key:
            return None, API_KEY_MISSING_ERROR

        headers = {
            "X-Redmine-API-Key": api_key,
            "Content-Type": CONTENT_TYPE_JSON,
        }
        params = {"project_id": 1, "tracker_id": 4, "offset": 0}

        total_royalty = 0
        fetched_orders = []

        while True:
            issues, error = GsmbManagmentService.fetch_issues(redmine_url, headers, params)
            if error:
                return None, error
            if not issues:
                break

            for issue in issues:
                if not GsmbManagmentService.is_valid_issue(issue):
                    continue

                royalty_value = GsmbManagmentService.extract_royalty(issue)
                if royalty_value <= 0:
                    continue

                total_royalty += royalty_value
                fetched_orders.append({
                    "title": issue.get("assigned_to", {}).get("name", "Unknown"),
                    "description": f"Royalty: {royalty_value}",
                    "avatar": "https://via.placeholder.com/40",
                    "royalty_value": royalty_value,
                })

            params["offset"] += len(issues)

        fetched_orders.sort(key=lambda x: x["royalty_value"], reverse=True)
        top_5_orders = fetched_orders[:5]

        return jsonify({"total_royalty": total_royalty, "orders": top_5_orders}), None



    @staticmethod
    def _get_headers(api_key):
        return {
            "Content-Type": CONTENT_TYPE_JSON,
            "X-Redmine-API-Key": api_key
        }

    @staticmethod
    def _fetch_issues(url, headers, offset):
        response = requests.get(f"{url}/issues.json?offset={offset}", headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch data from Redmine: {response.status_code}")
        return response.json().get("issues", [])

    @staticmethod
    def _process_issues(issues, license_counts):
        for issue in issues:
            tracker = issue.get("tracker", {})
            if tracker.get("id") != 4 or tracker.get("name") != "ML":
                continue
            created_date = issue.get("created_on")
            if not created_date:
                continue
            month = created_date.split("-")[1]
            license_counts[month] = license_counts.get(month, 0) + 1

    @staticmethod
    def monthly_mining_license_count(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            if not REDMINE_URL:
                return None, REDMINE_API_ERROR_MSG

            api_key = JWTUtils.get_api_key_from_token(token)
            if not api_key:
                return None, API_KEY_MISSING_ERROR

            headers = GsmbManagmentService._get_headers(api_key)
            license_counts = {}
            offset = 0

            while True:
                issues = GsmbManagmentService._fetch_issues(REDMINE_URL, headers, offset)
                if not issues:
                    break
                GsmbManagmentService._process_issues(issues, license_counts)
                offset += len(issues)

            month_map = {
                "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
                "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
                "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
            }

            formatted_data = [
                {"month": month_map[m], "miningLicense": license_counts.get(m, 0)}
                for m in sorted(month_map.keys())
            ]

            return formatted_data, None

        except Exception as e:
            return None, str(e)


    @staticmethod
    def transport_license_destination(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, REDMINE_API_ERROR_MSG

            if not api_key:
                return None, API_KEY_MISSING_ERROR

            params = {
                "project_id": 1,
                "tracker_id": 5
            }

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": CONTENT_TYPE_JSON
            }

            destination_counts = {}
            offset = 0
            has_more_issues = True

            while has_more_issues:
                params["offset"] = offset
                response = requests.get(
                    f"{REDMINE_URL}/issues.json",
                    headers=headers,
                    params=params
                )

                if response.status_code != 200:
                    return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

                data = response.json()
                issues = data.get("issues", [])

                if not issues:
                    has_more_issues = False
                    break

                for issue in issues:
                    custom_fields = issue.get("custom_fields", [])
                    location_field = next(
                        (field for field in custom_fields if field.get("name") == "Destination"), None
                    )

                    if location_field and location_field.get("value"):
                        destination = location_field["value"]
                        destination_counts[destination] = destination_counts.get(destination, 0) + 1

                offset += len(issues)

            formatted_data = [
                {"name": destination, "value": count}
                for destination, count in destination_counts.items()
            ]

            return formatted_data, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def total_location_ml(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, REDMINE_API_ERROR_MSG

            if not api_key:
                return None, API_KEY_MISSING_ERROR

            params = {
                "project_id": 1,
                "tracker_id": 4
            }

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": CONTENT_TYPE_JSON
            }

            location_counts = {}
            offset = 0
            has_more_issues = True

            while has_more_issues:
                params["offset"] = offset
                response = requests.get(
                    f"{REDMINE_URL}/issues.json",
                    headers=headers,
                    params=params
                )

                if response.status_code != 200:
                    return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

                data = response.json()
                issues = data.get("issues", [])

                if not issues:
                    has_more_issues = False
                    break

                for issue in issues:
                    custom_fields = issue.get("custom_fields", [])
                    location_field = next(
                        (field for field in custom_fields if field.get("name") == "Administrative District"), None
                    )

                    if location_field and location_field.get("value"):
                        location = location_field["value"]
                        location_counts[location] = location_counts.get(location, 0) + 1

                offset += len(issues)

            formatted_data = [
                {"name": location, "value": count}
                for location, count in location_counts.items()
            ]

            return formatted_data, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def complaint_counts(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)
            if not REDMINE_URL:
                return None, REDMINE_API_ERROR_MSG
            if not api_key:
                return None, API_KEY_MISSING_ERROR
            params = {
                "project_id": 1,
                "tracker_id": 6
            }
            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": CONTENT_TYPE_JSON
            }
            counts = {
                "New": 0,
                "Rejected": 0,
                "InProgress": 0,
                "Executed": 0,
                "total": 0
            }
            # Map statuses to keys in counts dictionary
            status_map = {
                "New": "New",
                "Rejected": "Rejected",
                "In Progress": "InProgress",
                "Executed": "Executed"
            }
            offset = 0
            has_more_issues = True
            while has_more_issues:
                params["offset"] = offset
                response = requests.get(
                    f"{REDMINE_URL}/issues.json",
                    headers=headers,
                    params=params
                )
                if response.status_code != 200:
                    return None, f"Failed to fetch issues: {response.status_code} - {response.text}"
                data = response.json()
                issues = data.get("issues", [])
                if not issues:
                    has_more_issues = False
                    break
                for issue in issues:
                    status = issue.get("status", {}).get("name", "")
                    key = status_map.get(status)
                    if key:
                        counts[key] += 1
                counts["total"] += len(issues)
                offset += len(issues)
            return counts, None
        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def role_counts(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, REDMINE_API_ERROR_MSG
            if not api_key:
                return None, API_KEY_MISSING_ERROR

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": CONTENT_TYPE_JSON
            }

            counts = {
                "licenceOwner": 0,
                "activeGSMBOfficers": 0,
                "policeOfficers": 0,
                "miningEngineer": 0
            }

            def increment_role_count(role_name):
                role_map = {
                    "MLOwner": "licenceOwner",
                    "GSMBOfficer": "activeGSMBOfficers",
                    "PoliceOfficer": "policeOfficers",
                    "miningEngineer": "miningEngineer"
                }
                key = role_map.get(role_name)
                if key:
                    counts[key] += 1

            offset = 0
            while True:
                url = f"{REDMINE_URL}/projects/mmpro-gsmb/memberships.json?offset={offset}"
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    return None, f"Failed to fetch memberships: {response.status_code} - {response.text}"

                memberships = response.json().get("memberships", [])
                if not memberships:
                    break

                for membership in memberships:
                    roles = membership.get("roles", [])
                    if roles:
                        role_name = roles[0].get("name", "")
                        increment_role_count(role_name)

                offset += len(memberships)

            counts["total_count"] = sum(counts.values())
            return counts, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def mining_license_count(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, REDMINE_API_ERROR_MSG

            if not api_key:
                return None, API_KEY_MISSING_ERROR

            params = {
                "project_id": 1,
                "tracker_id": 4,
                "include": "custom_fields"
            }

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": CONTENT_TYPE_JSON
            }

            counts = {
                "valid": 0,
                "expired": 0,
                "rejected": 0,
                "total": 0
            }

            offset = 0
            has_more_issues = True

            while has_more_issues:
                params["offset"] = offset
                response = requests.get(
                    f"{REDMINE_URL}/issues.json",
                    headers=headers,
                    params=params
                )

                if response.status_code != 200:
                    return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

                data = response.json()
                issues = data.get("issues", [])

                if not issues:
                    has_more_issues = False
                    break

                for issue in issues:
                    status = issue.get("status", {}).get("name", "")
                    
                    
                    if status == "Valid":
                        counts["valid"] += 1
                    elif status == "Expired":
                        counts["expired"] += 1
                    elif status == "Rejected":
                        counts["rejected"] += 1

                counts["total"] += len(issues)
                offset += len(issues)

            return counts, None

        except Exception as e:
            return None, f"Server error: {str(e)}"
        

    def is_license_expired(self,due_date_str):
        try:
            from datetime import datetime
        
            if not due_date_str:
                return False  # If no due date, consider it not expired
            
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            current_date = datetime.now().date()
        
            return due_date < current_date
        except Exception:
            return False  # In case of any parsing error, consider it not expired



    @staticmethod
    def unactive_gsmb_officers(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, REDMINE_API_ERROR_MSG

            if not api_key:
                return None, API_KEY_MISSING_ERROR

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": CONTENT_TYPE_JSON,
                "User-Agent": USER_AGENT
            }

            params = {"status": 3, "include": "custom_fields"}
    
            response = requests.get(
                f"{REDMINE_URL}/users.json",
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code != 200:  # Changed from 201 to 200 for GET requests
                print(f"Full Error Response: {response.text}")
                return None, f"API request failed (Status {response.status_code})"

            users = response.json().get("users", [])
           
        
            # Filter GSMB officers
            officers = []
            for user in users:
                custom_fields = user.get("custom_fields", [])
            
                # Convert custom fields to dictionary
                custom_fields_dict = {
                    field["name"]: field["value"]
                    for field in custom_fields
                    if field.get("value")
                }

                officer = {
                    "id": user["id"],
                    "name": f"{user.get('firstname', '')} {user.get('lastname', '')}".strip(),
                    "email": user.get("mail", ""),
                    "status": user.get("status", 3),  # Default to inactive (3)
                    "custom_fields": {
                        "Designation": custom_fields_dict.get("Designation"),
                        "Mobile Number": custom_fields_dict.get("Mobile Number"),
                        NIC_BACK_IMAGE_FIELD:custom_fields_dict.get(NIC_BACK_IMAGE_FIELD),
                        NIC_FRONT_IMAGE_FIELD: custom_fields_dict.get(NIC_FRONT_IMAGE_FIELD),
                        "National Identity Card": custom_fields_dict.get("National Identity Card"),
                        USER_TYPE_FIELD: custom_fields_dict.get(USER_TYPE_FIELD),
                        WORK_ID_FIELD: custom_fields_dict.get(WORK_ID_FIELD)
                    }
                }
                officers.append(officer)

            return {"count": len(officers), "officers": officers}, None
         
        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {str(e)}")
            return None, f"Network error occurred"
        except Exception as e:
            print(f"Unexpected Error: {str(e)}")
            return None, f"Processing error occurred"    
        

    @staticmethod
    def get_users_by_type(token, user_type):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, REDMINE_API_ERROR_MSG

            if not api_key:
                return None, API_KEY_MISSING_ERROR

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": CONTENT_TYPE_JSON,
                "User-Agent": USER_AGENT
            }

            all_users = []
            offset = 0
            limit = 100  # Redmine's max per page
            
            while True:
                params = {
                    "status": 3, 
                    "include": "custom_fields",
                    "offset": offset,
                    "limit": limit
                }
                
                response = requests.get(
                    f"{REDMINE_URL}/users.json",
                    headers=headers,
                    params=params,
                    timeout=10
                )

                if response.status_code != 200:
                    return None, f"API request failed (Status {response.status_code})"

                data = response.json()
                users = data.get("users", [])
                all_users.extend(users)
                
                # Check if we've got all users
                total_count = data.get("total_count", 0)
                if len(all_users) >= total_count or len(users) < limit:
                    break
                    
                offset += limit

            # Filter users by type
            matched_users = []
            for user in all_users:
                custom_fields = user.get("custom_fields", [])
                custom_fields_dict = {
                    field["name"]: field["value"]
                    for field in custom_fields
                    if field.get("value")
                }

                if custom_fields_dict.get(USER_TYPE_FIELD) == user_type:
                    matched_users.append({
                        "id": user["id"],
                        "name": f"{user.get('firstname', '')} {user.get('lastname', '')}".strip(),
                        "email": user.get("mail", ""),
                        "status": user.get("status", 1),
                        **custom_fields_dict
                    })

            return matched_users, None

        except requests.exceptions.RequestException as e:
            return None, f"Network error occurred: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"
        

    @staticmethod
    def get_active_ml_owners(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, REDMINE_API_ERROR_MSG

            if not api_key:
                return None, API_KEY_MISSING_ERROR

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": CONTENT_TYPE_JSON,
                "User-Agent": USER_AGENT
            }

            limit = 100
            offset = 0
            all_users = []

            while True:
                params = {
                    "status": 1,  # active users
                    "include": "custom_fields",
                    "limit": limit,
                    "offset": offset
                }

                response = requests.get(
                    f"{REDMINE_URL}/users.json",
                    headers=headers,
                    params=params,
                    timeout=10
                )

                if response.status_code != 200:
                    return None, f"API request failed (Status {response.status_code})"

                users_page = response.json().get("users", [])
                all_users.extend(users_page)

                if len(users_page) < limit:
                    break  # no more pages

                offset += limit

            matched_users = []

            for user in all_users:
                custom_fields = user.get("custom_fields", [])
                custom_fields_dict = {
                    field["name"]: field["value"]
                    for field in custom_fields
                    if field.get("value")
                }

                user_type = custom_fields_dict.get(USER_TYPE_FIELD, "")

                if user_type == "mlOwner":
                    matched_users.append({
                        "id": user["id"],
                        "name": f"{user.get('firstname', '')} {user.get('lastname', '')}".strip(),
                        "email": user.get("mail", ""),
                        "status": user.get("status", 1),
                        **custom_fields_dict
                    })

            return matched_users, None

        except requests.exceptions.RequestException as e:
            return None, f"Network error occurred"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"


        
    @staticmethod
    def activate_gsmb_officer(token,id):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, REDMINE_API_ERROR_MSG

            if not API_KEY:
                return None, API_KEY_MISSING_ERROR

            payload = {
                "user": {
                    "status": 1  # Set status to active
                }
            }

            headers = {
            "Content-Type": CONTENT_TYPE_JSON,
            "X-Redmine-API-Key": API_KEY
            }

            response = requests.put(
            f"{REDMINE_URL}/users/{id}.json",
            json=payload,
            headers=headers
            )

            if response.status_code == 204:
               return {"status": "success", "message": "User activated successfully"}, None
            else:
                error_msg = f"Failed to User Active. Status: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f", Error: {error_data.get('errors', 'Unknown error')}"
                except ValueError:
                    error_msg += f", Response: {response.text}"
                return None, error_msg

        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"
        
        
    @staticmethod
    def get_attachment_urls(custom_fields):
        try:
            upload_field_names = {
                NIC_BACK_IMAGE_FIELD: None,
                NIC_FRONT_IMAGE_FIELD: None,
                WORK_ID_FIELD: None
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
    def get_custom_field_value(custom_fields, field_name):
        """Helper method to get value from custom fields"""
        for field in custom_fields:
            if field.get("name") == field_name:
                return field.get("value")
        return None
            
