import requests
import os
from dotenv import load_dotenv
from utils.jwt_utils import JWTUtils
from flask import jsonify
from utils.limit_utils import LimitUtils

load_dotenv()

class GsmbManagmentService:
    @staticmethod
    def monthly_total_sand_cubes(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, "Redmine URL is missing"

            if not api_key:
                return None, "API Key is missing"

            params = {
                "project_id": 1,
                "tracker_id": 5  # TPL
            }

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json"
            }

            monthly_data = {
                "Jan": 0, "Feb": 0, "Mar": 0, "Apr": 0, "May": 0, "Jun": 0,
                "Jul": 0, "Aug": 0, "Sep": 0, "Oct": 0, "Nov": 0, "Dec": 0
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
                    custom_fields = issue.get("custom_fields", [])
                    cube_field = next(
                        (field for field in custom_fields if field.get("id") == 58 and field.get("name") == "Cubes"), None
                    )

                    if cube_field and cube_field.get("value"):
                        issue_date = issue.get("created_on")
                        if issue_date:
                            month_index = int(issue_date[5:7]) - 1  # Extract month from YYYY-MM-DD
                            month_name = list(monthly_data.keys())[month_index]
                            monthly_data[month_name] += float(cube_field["value"])

                offset += len(issues)

            ordered_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

            formatted_data = [
                {"month": month, "totalCubes": monthly_data[month]}
                for month in ordered_months
            ]

            return formatted_data, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def fetch_top_mining_holders(token):
        def safe_float(value):
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, "Redmine URL is missing"

            if not api_key:
                return None, "API Key is missing"

            params = {
                "project_id": 1,
                "tracker_id": 4  # Mining Licenses
            }

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json"
            }

            mining_data = []
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
                    assigned_to = issue.get("assigned_to", {})
                    owner = assigned_to.get("name") if assigned_to else None

                    custom_fields = issue.get("custom_fields", [])
                   
                    capacity_str = next(
                        (field.get("value") for field in custom_fields if field.get("name") == "Capacity"), None
                    )
                    used_str = next(
                        (field.get("value") for field in custom_fields if field.get("name") == "Used"), None
                    )

                    # capacity = float(capacity_str) if capacity_str and capacity_str.strip() != "" else 0
                    # used = float(used_str) if used_str and used_str.strip() != "" else 0

                    # if owner and capacity > 0:
                    #     percentage_used = ((used / capacity) * 100) if capacity else 0
                    #     mining_data.append({"label": owner, "value": round(percentage_used, 2), "capacity": capacity})
                    capacity = safe_float(capacity_str)
                    used = safe_float(used_str)

                    if owner and capacity > 0:
                        percentage_used = ((used / capacity) * 100)
                        mining_data.append({
                            "label": owner,
                            "value": round(percentage_used, 2),
                            "capacity": capacity
                        })

                offset += len(issues)

            mining_data.sort(key=lambda x: x['capacity'], reverse=True)
            return mining_data[:10], None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def fetch_royalty_counts(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, "Redmine URL is missing"

            if not api_key:
                return None, "API Key is missing"

            total_royalty = 0
            fetched_orders = []

            params = {
                "project_id": 1,
                "tracker_id": 4,
            }

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json"
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
                issues = data.get('issues', [])

                if not issues:
                    has_more_issues = False
                    break

                for issue in issues:
                    if issue.get("tracker", {}).get("id") == 4 and issue.get("tracker", {}).get("name") == "ML" and issue.get("status", {}).get("name") == "Valid":
                        royalty_field = next(
                            (field for field in issue.get("custom_fields", []) if field.get("name") == "Royalty"),
                            None
                        )

                        royalty_value = 0
                        if royalty_field:
                            try:
                                royalty_value = float(royalty_field.get("value", "0") or "0")
                            except ValueError:
                                royalty_value = 0

                        if royalty_value > 0:
                            total_royalty += royalty_value
                            fetched_orders.append({
                                "title": issue.get("assigned_to", {}).get("name", "Unknown"),
                                "description": f"Royalty: {royalty_value}",
                                "avatar": "https://via.placeholder.com/40",
                                "royalty_value": royalty_value 
                            })

                offset += len(issues)

                fetched_orders.sort(key=lambda x: x["royalty_value"], reverse=True)
                top_5_orders = fetched_orders[:5]

            return jsonify({
                "total_royalty": total_royalty,
                "orders": top_5_orders
            }), None

        except Exception as e:
            print("Error fetching royalty data:", e)
            return None, "An error occurred while fetching data"

    @staticmethod
    def monthly_mining_license_count(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, "Redmine URL is missing"

            if not api_key:
                return None, "API Key is missing"

            headers = {
                "Content-Type": "application/json",
                "X-Redmine-API-Key": api_key
            }

            license_counts = {}
            offset = 0
            has_more_issues = True

            while has_more_issues:
                response = requests.get(
                    f"{REDMINE_URL}/issues.json?offset={offset}",
                    headers=headers
                )

                if response.status_code != 200:
                    return None, f"Failed to fetch data from Redmine: {response.status_code}"

                data = response.json()
                issues = data.get("issues", [])

                if not issues:
                    has_more_issues = False
                    break

                for issue in issues:
                    if issue.get("tracker", {}).get("id") == 4 and issue.get("tracker", {}).get("name") == "ML":
                        created_date = issue.get("created_on")
                        if created_date:
                            month = created_date.split("-")[1]
                            license_counts[month] = license_counts.get(month, 0) + 1

                offset += len(issues)

            formatted_data = [
                {"month": "Jan", "miningLicense": license_counts.get("01", 0)},
                {"month": "Feb", "miningLicense": license_counts.get("02", 0)},
                {"month": "Mar", "miningLicense": license_counts.get("03", 0)},
                {"month": "Apr", "miningLicense": license_counts.get("04", 0)},
                {"month": "May", "miningLicense": license_counts.get("05", 0)},
                {"month": "Jun", "miningLicense": license_counts.get("06", 0)},
                {"month": "Jul", "miningLicense": license_counts.get("07", 0)},
                {"month": "Aug", "miningLicense": license_counts.get("08", 0)},
                {"month": "Sep", "miningLicense": license_counts.get("09", 0)},
                {"month": "Oct", "miningLicense": license_counts.get("10", 0)},
                {"month": "Nov", "miningLicense": license_counts.get("11", 0)},
                {"month": "Dec", "miningLicense": license_counts.get("12", 0)},
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
                return None, "Redmine URL is missing"

            if not api_key:
                return None, "API Key is missing"

            params = {
                "project_id": 1,
                "tracker_id": 5
            }

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json"
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
                return None, "Redmine URL is missing"

            if not api_key:
                return None, "API Key is missing"

            params = {
                "project_id": 1,
                "tracker_id": 4
            }

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json"
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
                return None, "Redmine URL is missing"

            if not api_key:
                return None, "API Key is missing"

            params = {
                "project_id": 1,
                "tracker_id": 6
            }

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json"
            }

            counts = {
                "New": 0,
                "Rejected": 0,
                "InProgress": 0,
                "Executed": 0,
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
                    if status == "New":
                        counts["New"] += 1
                    elif status == "Rejected":
                        counts["Rejected"] += 1
                    elif status == "In Progress":
                        counts["InProgress"] += 1
                    elif status == "Executed":
                        counts["Executed"] += 1

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
                return None, "Redmine URL is missing"

            if not api_key:
                return None, "API Key is missing"

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json"
            }

            counts = {
                "licenceOwner": 0,
                "activeGSMBOfficers": 0,
                "policeOfficers": 0,
                "miningEngineer": 0
            }

            offset = 0
            has_more_memberships = True

            while has_more_memberships:
                url = f"{REDMINE_URL}/projects/mmpro-gsmb/memberships.json?offset={offset}"
                response = requests.get(url, headers=headers)

                if response.status_code != 200:
                    return None, f"Failed to fetch memberships: {response.status_code} - {response.text}"

                data = response.json()
                memberships = data.get("memberships", [])

                if not memberships:
                    has_more_memberships = False
                    break

                for membership in memberships:
                    roles = membership.get("roles", [])
                    if roles:
                        role_name = roles[0].get("name", "")
                        if role_name == "MLOwner":
                            counts["licenceOwner"] += 1
                        elif role_name == "GSMBOfficer":
                            counts["activeGSMBOfficers"] += 1
                        elif role_name == "PoliceOfficer":
                            counts["policeOfficers"] += 1
                        elif role_name == "miningEngineer":
                            counts["miningEngineer"] += 1

                offset += len(memberships)

                total_count = (
                    counts["licenceOwner"]
                    + counts["activeGSMBOfficers"]
                    + counts["policeOfficers"]
                    + counts["miningEngineer"]
                )
                counts["total_count"] = total_count

            return counts, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def mining_license_count(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            api_key = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL:
                return None, "Redmine URL is missing"

            if not api_key:
                return None, "API Key is missing"

            params = {
                "project_id": 1,
                "tracker_id": 4,
                "include": "custom_fields"
            }

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json"
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
                    due_date = None
                    
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
        

    def is_license_expired(due_date_str):
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

            if not api_key:
                return None, "API Key is missing"

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "GSMB-Management-Service/1.0"
            }

            params = {"status": 3, "include": "custom_fields"}
            request_url = f"{REDMINE_URL}/users.json?status=3"


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
           # custom_fields = issue.get("custom_fields", [])  # Extract custom fields
           # attachment_urls = GsmbManagmentService.get_attachment_urls(user_api_key, REDMINE_URL, custom_fields)
        
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
                        "NIC back image":custom_fields_dict.get("NIC back image"),
                        "NIC front image": custom_fields_dict.get("NIC front image"),
                        "National Identity Card": custom_fields_dict.get("National Identity Card"),
                        "User Type": custom_fields_dict.get("User Type"),
                        "work ID": custom_fields_dict.get("work ID")
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

            if not api_key:
                return None, "API Key is missing"

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "GSMB-Management-Service/1.0"
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

                if custom_fields_dict.get("User Type") == user_type:
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

            if not api_key:
                return None, "API Key is missing"

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "GSMB-Management-Service/1.0"
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

                user_type = custom_fields_dict.get("User Type", "")

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

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"
            
            payload = {
                "user": {
                    "status": 1  # Set status to active
                }
            }

            headers = {
            "Content-Type": "application/json",
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
                except:
                    error_msg += f", Response: {response.text}"
                return None, error_msg

        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"
        

    # @staticmethod
    # def get_attachment_urls(api_key, redmine_url, custom_fields):
    #     try:
    #         # Define the mapping of custom field names to their attachment IDs
    #         file_fields = {
    #             "NIC back image": None,
    #             "NIC front image": None,
    #             "work ID": None
                
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
                "NIC back image": None,
                "NIC front image": None,
                "work ID": None
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
            
