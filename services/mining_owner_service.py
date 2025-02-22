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

class MLOwnerService:
    

    @staticmethod
    def mining_licenses(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            # Step 1: Extract user_id from the token
            user_id, error = MLOUtils.get_user_info_from_token(token)
            if not user_id:
                return None, error

            # Debugging: Print the user_id
            print(f"User ID from token: {user_id}")

            # Step 2: Define query parameters for project_id=31 and tracker_id=7 (ML)
            params = {
                "project_id": 31,
                "tracker_id": 7  # ML tracker ID
            }

            headers = {
                "Content-Type": "application/json",
                "X-Redmine-API-Key": API_KEY
            }

            # Make the Redmine request
            # response = requests.get(
            #     f"{REDMINE_URL}/projects/gsmb/issues.json",
            #     params=params,
            #     headers=headers
            # )
            limit = LimitUtils.get_limit()
            response = requests.get(
                f"{REDMINE_URL}/projects/gsmb/issues.json?offset=0&limit={limit}",
                params=params,
                headers=headers
            )
            # Check if the request was successful
            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])

            # Debugging: Print the issues to see if there are any
            print("Redmine Issues:", issues)

            # Step 3: Filter the issues based on the logged-in user's user_id
            filtered_issues = [
                issue for issue in issues if MLOUtils.issue_belongs_to_user(issue, user_id)
            ]

            # Debugging: Print the filtered issues to verify the result
            print("Filtered Issues:", filtered_issues)

            # Only return relevant issue details like subject, description, dates, etc.
            relevant_issues = [
                {
                    "id": issue.get("id"),
                    "subject": issue.get("subject"),
                    "status": issue.get("status"),
                    "description": issue.get("description"),
                    "start_date": issue.get("start_date"),
                    "due_date": issue.get("due_date"),
                    "done_ratio": issue.get("done_ratio"),
                    "is_private": issue.get("is_private"),
                    "estimated_hours": issue.get("estimated_hours"),
                    "total_estimated_hours": issue.get("total_estimated_hours"),
                    "custom_fields": issue.get("custom_fields")
                }
                for issue in filtered_issues
            ]

            # Return the relevant issue data
            return relevant_issues, None  # Returning filtered issues and no error

        except Exception as e:
            return None, f"Server error: {str(e)}"

    # Home function (mining_homeLicenses)
    @staticmethod
    def mining_homeLicenses(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            # Step 1: Extract user_id from the token
            user_id, error = MLOUtils.get_user_info_from_token(token)
            if not user_id:
                return None, error

            # Debugging: Print the user_id
            print(f"User ID from token: {user_id}")

            # Step 2: Define query parameters for project_id=31 and tracker_id=7 (ML)
            params = {
                "project_id": 31,
                "tracker_id": 7  # ML tracker ID
            }

            headers = {
                "X-Redmine-API-Key": API_KEY
            }

            # Make the Redmine request
            limit = LimitUtils.get_limit()
            response = requests.get(
                f"{REDMINE_URL}/projects/gsmb/issues.json?offset=0&limit={limit}",
                params=params,
                headers=headers
            )

            # Check if the request was successful
            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])

            # Debugging: Print the issues to see if there are any
            print("Redmine Issues:", issues)

            # Step 3: Filter the issues based on the logged-in user's user_id
            filtered_issues = [
                issue for issue in issues if MLOUtils.issue_belongs_to_user(issue, user_id)
            ]

            # Debugging: Print the filtered issues to verify the result
            print("Filtered Issues:", filtered_issues)

            # Step 4: Further filter the issues based on the conditions:
            # - Valid status (not "Expired", "Closed", etc.)
            # - Sort by most recent due_date
            # - Limit to 5 issues

            valid_statuses = ["Valid"]  # Define valid statuses as per your requirements
            valid_issues = [
                issue for issue in filtered_issues
                if issue.get("status", {}).get("name") in valid_statuses
            ]

            # Sort by due_date in descending order to get the most recent issues first
            valid_issues_sorted = sorted(valid_issues, key=lambda x: datetime.strptime(x["due_date"], "%Y-%m-%d") if x.get("due_date") else datetime.min, reverse=True)

            # Limit to a maximum of 5 issues
            top_5_issues = valid_issues_sorted[:5]

            # Only return relevant issue details like subject, description, dates, etc.
            relevant_issues = [
                {
                    "subject": issue.get("subject"),
                    "status": issue.get("status"),
                    "description": issue.get("description"),
                    "start_date": issue.get("start_date"),
                    "due_date": issue.get("due_date"),
                    "done_ratio": issue.get("done_ratio"),
                    "is_private": issue.get("is_private"),
                    "estimated_hours": issue.get("estimated_hours"),
                    "total_estimated_hours": issue.get("total_estimated_hours"),
                    "custom_fields": issue.get("custom_fields")
                }
                for issue in top_5_issues
            ]

            # Return the relevant issue data
            return relevant_issues, None  # Returning filtered issues and no error

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def view_tpls(token):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = JWTUtils.get_api_key_from_token(token)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"

            # Step 1: Extract user_id from the token
            user_id, error = MLOUtils.get_user_info_from_token(token)
            if not user_id:
                return None, error

            # Step 2: Define query parameters for project_id=31 and tracker_id=8 (TPL)
            params = {
                "project_id": 31,
                "tracker_id": 8  # TPL tracker ID
            }

            headers = {
                "X-Redmine-API-Key": API_KEY
            }

            # Make the Redmine request
            limit = LimitUtils.get_limit()
            response = requests.get(
                f"{REDMINE_URL}/projects/gsmb/issues.json?offset=0&limit={limit}",
                params=params,
                headers=headers
            )

            # Check if the request was successful
            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])

            # Filter the issues based on the user_id, if any
            filtered_issues = [
                issue for issue in issues if MLOUtils.issue_belongs_to_user(issue, user_id)
            ]

            # Debugging: Print the filtered issues to verify the result
            print("Filtered Issues:", filtered_issues)

            return filtered_issues, None  # Returning filtered issues and no error

        except Exception as e:
            return None, f"Server error: {str(e)}"


    @staticmethod
    def create_tpl(data, token):
        # print('----------------------------tpl data-----------------------------')
        # print(data)
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            # Extract the user-specific API key from the token
            api_key = JWTUtils.get_api_key_from_token(token)

            # Check if Redmine URL and API Key exist
            if not REDMINE_URL or not api_key:
                return None, "Redmine URL or API Key is missing"

            # Ensure the API token is present before proceeding
            if not api_key:
                return None, "API Token is required to create the issue"


            headers = {
                "X-Redmine-API-Key": api_key,  # Include the token for authorization
                "Content-Type": "application/json"
            }
            # print("------------------------------------------------")
            # print(data)
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
    def update_issue(issue_id, data):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")
            # print("View TPLs")
            # print(REDMINE_URL)
            # print(API_KEY)

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"
            headers = {
                "X-Redmine-API-Key": API_KEY,  # Include the token for authorization
                "Content-Type": "application/json"
            }

            # print("------------------------------------------------")
            # print("Request Payload:", data)
            # print("------------------------------------------------")
            # print('\n\n\n\n\n')
            # print("data payload", json.dumps(data))
            # print('Headers', headers)
            url = f"{REDMINE_URL}/issues/{issue_id}.json"
            # print("URL:", url)
            response = requests.put(
                url,
                json = data,  # Ensure correct JSON structure
                headers=headers
            )

            # print("Response Status Code:", response.status_code)
            # print("Response Headers:", response.headers)

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
        
        # Service function to update an issue
    @staticmethod
    def update_issue(issue_id, data):
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")
            API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")

            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"
            headers = {
                "X-Redmine-API-Key": API_KEY,  # Include the token for authorization
                "Content-Type": "application/json"
            }
            update_data = {"issue": data}  # Ensure "issue" is wrapped correctly

            print("------------------------------------------------")
            print("Request Payload:", data)
            print("------------------------------------------------")
            print('\n\n\n\n\n')
            print("data payload", json.dumps(data))
            print('Headers', headers)
            url = f"{REDMINE_URL}/issues/{issue_id}.json"
            print("URL:", url)
            response = requests.put(
                url,
                json = data,  # Ensure correct JSON structure
                headers=headers
            )

            print("Response Status Code:", response.status_code)
            print("Response Headers:", response.headers)

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
    
    # @staticmethod
    # def ml_detail(issue_id, token):
    #     api_key = JWTUtils.get_api_key_from_token(token)
    #     try:
    #         REDMINE_URL = os.getenv("REDMINE_URL")

    #         if not REDMINE_URL or not api_key:
    #             return None, "Redmine URL or API Key is missing"
    #         headers = {
    #             "X-Redmine-API-Key": api_key,  # Include the token for authorization
    #             "Content-Type": "application/json"
    #         }
    #         url = f"{REDMINE_URL}/issues/{issue_id}.json"
    #         print("URL:", url)
    #         response = requests.get(
    #             url,  # Ensure correct JSON structure
    #             headers=headers
    #         )

    #         if response.status_code != 200:
    #             return None, f"Failed to fetch issue: {response.status_code} - {response.text}"

    #         issue = response.json().get("issue", {})


    #         return issue, None  # Returning filtered issues and no error

    #     except Exception as e:
    #         return None, f"Server error: {str(e)}"
    
    @staticmethod
    def ml_detail(l_number, token):
        api_key = JWTUtils.get_api_key_from_token(token)
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")

            if not REDMINE_URL or not api_key:
                return None, "Redmine URL or API Key is missing"
            
            
            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json"
            }
            limit = LimitUtils.get_limit()
            url = f"{REDMINE_URL}/projects/gsmb/issues.json?offset=0&limit={limit}"
            # print(f"Requesting: {url}")

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])

            # Filter issues based on subject matching l_number
            filtered_issues = [issue for issue in issues if issue.get("subject") == l_number]
            # print("Filtered Issues:", filtered_issues[0])

            return filtered_issues[0] if filtered_issues else None, None

        except Exception as e:
            return None, f"Server error: {str(e)}"
        
        
    @staticmethod
    def user_detail(user_id, token):
        api_key = JWTUtils.get_api_key_from_token(token)
        try:
            REDMINE_URL = os.getenv("REDMINE_URL")

            if not REDMINE_URL or not api_key:
                return None, "Redmine URL or API Key is missing"
            headers = {
                "X-Redmine-API-Key": api_key,  # Include the token for authorization
                "Content-Type": "application/json"
            }
            url = f"{REDMINE_URL}/users/{user_id}.json"
            # print("URL:", url)
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

   

    