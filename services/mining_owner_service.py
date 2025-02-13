import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class MLOwnerService:
    @staticmethod
    def mining_licenses():
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = os.getenv("REDMINE_API_KEY")

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            # Define query parameters for project_id=31 and tracker_id=8 (TPL)
            params = {
                "project_id": 31,
                "tracker_id": 7  # ML tracker ID
            }

            headers = {
                "X-Redmine-API-Key": API_KEY
            }

            response = requests.get(
                f"{REDMINE_URL}/issues.json",
                params=params,
                headers=headers
            )

            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])

            # Hardcoded Owner Name (could be dynamically retrieved from a token in the future)
            OwnerName = "Pasindu Lakshan" 

            # Filter the issues based on the hardcoded OwnerName
            filtered_issues = [
                issue for issue in issues if MLOwnerService.issue_belongs_to_owner(issue, OwnerName)
            ]

            return filtered_issues, None  # Returning filtered issues and no error

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def issue_belongs_to_owner(issue, owner_name):
        """
        Check if the issue belongs to the specified owner name.
        This assumes that the owner name is stored in a specific custom field or in issue details.
        """
        # Assuming the Owner Name is stored in a custom field or issue attribute
        custom_fields = issue.get('custom_fields', [])
        
        for field in custom_fields:
            # Assuming the owner name is stored in a custom field, modify the field identifier accordingly
            if field.get('name') == "Owner" and field.get('value') == owner_name:
                return True
        
        # If it's not in custom fields, check in the issue's assigned_to or other possible fields
        assigned_to = issue.get('assigned_to', {}).get('name', "")
        if assigned_to == owner_name:
            return True
        
        return False

    @staticmethod
    def create_tpl(data):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = os.getenv("REDMINE_API_KEY")

            # Check if Redmine URL and API Key exist
            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            # Ensure the API token is present before proceeding
            if not API_KEY:
                return None, "API Token is required to create the issue"

            # Assign the correct owner name (Pasindu Lakshan)
            data["custom_fields"] = data.get("custom_fields", [])
            data["custom_fields"].append({
                "name": "Owner",
                "value": "Pasindu Lakshan"
            })

            headers = {
                "X-Redmine-API-Key": API_KEY,  # Include the token for authorization
                "Content-Type": "application/json"
            }

            # Sending POST request to Redmine to create the issue
            response = requests.post(
                f"{REDMINE_URL}/issues.json",
                json=data,
                headers=headers
            )

            # Check if the response is successful
            if response.status_code != 201:
                return None, f"Failed to create issue: {response.status_code} - {response.text}"

            issue = response.json().get("issue", {})
            return issue, None  # Returning created issue and no error

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def view_tpls():
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = os.getenv("REDMINE_API_KEY")

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            # Define query parameters for project_id=31 and tracker_id=8 (TPL)
            params = {
                "project_id": 31,
                "tracker_id": 8  # TPL tracker ID
            }

            headers = {
                "X-Redmine-API-Key": API_KEY
            }

            response = requests.get(
                f"{REDMINE_URL}/issues.json",
                params=params,
                headers=headers
            )

            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])

            # Hardcoded Owner Name (could be dynamically retrieved from a token in the future)
            OwnerName = "Pasindu Lakshan" 

            # Filter the issues based on the hardcoded OwnerName
            filtered_issues = [
                issue for issue in issues if MLOwnerService.issue_belongs_to_owner(issue, OwnerName)
            ]

            return filtered_issues, None  # Returning filtered issues and no error

        except Exception as e:
            return None, f"Server error: {str(e)}"
        
    

    @staticmethod
    def mining_homeLicenses():
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = os.getenv("REDMINE_API_KEY")

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            # Define query parameters for project_id=31 and tracker_id=7 (ML)
            params = {
                "project_id": 31,
                "tracker_id": 7  # ML tracker ID
            }

            headers = {
                "X-Redmine-API-Key": API_KEY
            }

            response = requests.get(
                f"{REDMINE_URL}/issues.json",
                params=params,
                headers=headers
            )

            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])

            # Hardcoded Owner Name (could be dynamically retrieved from a token in the future)
            OwnerName = "Pasindu Lakshan" 

            # Filter and process the issues based on the custom rules for "Valid" licenses
            valid_issues = []
            for issue in issues:
                if MLOwnerService.issue_belongs_to_owner(issue, OwnerName) and MLOwnerService.is_valid_license(issue):
                    valid_issues.append(issue)

            # Sort the issues by created_on date (most recent first)
            sorted_issues = sorted(valid_issues, key=lambda x: x.get("created_on", ""), reverse=True)

            # Get only the most recent 5 licenses
            recent_5_licenses = sorted_issues[:5]

            return recent_5_licenses, None  # Returning filtered issues and no error

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def issue_belongs_to_owner(issue, owner_name):
        """
        Check if the issue belongs to the specified owner name.
        This assumes that the owner name is stored in a specific custom field or in issue details.
        """
        custom_fields = issue.get('custom_fields', [])
        
        for field in custom_fields:
            # Assuming the owner name is stored in a custom field, modify the field identifier accordingly
            if field.get('name') == "Owner Name" and field.get('value') == owner_name:
                return True
        
        assigned_to = issue.get('assigned_to', {}).get('name', "")
        if assigned_to == owner_name:
            return True
        
        return False

    @staticmethod
    def is_valid_license(issue):
        """
        Check if the license is valid based on the given rules:
        - Due date is not exceeded today
        - Remaining should be > 0
        - Status should be either Active or Valid
        """
        # Check the status
        status = issue.get("status", {}).get("name", "")
        if status not in ["Active", "Valid"]:
            return False

        # Check if the due date is not exceeded (today or in the future)
        due_date_str = issue.get("due_date", "")
        if not due_date_str:
            return False
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        except ValueError:
            return False  # Invalid date format
        
        today = datetime.today().date()
        if due_date.date() < today:
            return False  # Due date is exceeded

        # Check if remaining is greater than 0
        remaining = next((field['value'] for field in issue.get('custom_fields', []) if field['name'] == 'Remaining'), None)
        if remaining is None or int(remaining) <= 0:
            return False  # Remaining must be greater than 0
        
        return True