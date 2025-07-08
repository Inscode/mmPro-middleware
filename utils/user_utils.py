import os
import requests


class UserUtils:
    @staticmethod
    def get_user_phone(user_id):

        REDMINE_URL = os.getenv("REDMINE_URL")
        REDMINE_API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")
       
        headers = {
            "X-Redmine-API-Key": REDMINE_API_KEY,
            "Content-Type": "application/json"
        }

        url = f"{REDMINE_URL}/users/{user_id}.json"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status() 

            user_data = response.json().get("user", {})

            custom_fields = user_data.get("custom_fields", [])

            for field in custom_fields:
                if field["name"] == "Mobile Number":
                    return field.get("value", "N/A")  
                
            return "N/A"  
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user phone number: {e}")
            return None
    
    @staticmethod
    def get_user_api_key(user_id):
        """Fetch the API key of a user from Redmine using their user ID."""
        REDMINE_URL = os.getenv("REDMINE_URL")
        REDMINE_API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")

        headers = {
            "X-Redmine-API-Key": REDMINE_API_KEY,
            "Content-Type": "application/json"
        }

        url = f"{REDMINE_URL}/users/{user_id}.json"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            user_data = response.json().get("user", {})

            # ✅ Directly fetch API key from the response
            api_key = user_data.get("api_key")

            return api_key if api_key else "N/A"  


        except requests.exceptions.RequestException as e:
            print(f"Error fetching user API key: {e}")
            return None