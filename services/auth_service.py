import requests
from dotenv import load_dotenv
import os
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from config import Config
from cryptography.fernet import Fernet
import uuid
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from services.cache import cache  # Import the existing cache instance
import logging

# Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
REDMINE_URL = os.getenv("REDMINE_URL")
REDMINE_API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")
REDMINE_ADMIN_API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")

class AuthService:
    ENCRYPTION_KEY = Fernet.generate_key()  # Generate only once and store safely
    cipher = Fernet(ENCRYPTION_KEY)
    
    @staticmethod
    def authenticate_user(username, password):
        try:
            # Authenticate user and get current user info
            response = requests.get(
                f"{REDMINE_URL}/users/current.json?include=memberships,groups",
                auth=(username, password)
            )

            if response.status_code != 200:
                return None, None, 'Invalid credentials. Check the Username and password and try again.'

            user_data = response.json().get('user')
            if not user_data:
                return None, None, 'User data not found'

            gsm_project_role = None
            for membership in user_data.get('memberships', []):
                project_name = membership.get('project', {}).get('name')
                if project_name == "MMPRO-GSMB":
                    roles = membership.get('roles', [])
                    if roles:
                        gsm_project_role = roles[0].get('name')
                        break

            if not gsm_project_role:
                return None, None, 'User does not have a role in project GSMB'

            api_key = user_data.get('api_key')
            if not api_key:
                return None, None, 'API key not found'

            return user_data, gsm_project_role, api_key

        except Exception as e:
            return None, None, f"Server error: {str(e)}"

    @staticmethod
    def authenticate_google_token(token):
        try:
            # Verify the Google token using Google's OAuth2 service
           
            id_info = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                GOOGLE_CLIENT_ID
            )


            # Extract email from the token info
            email = id_info.get('email')
            if not email:
                return None, "Email not found in Google token"

            # Get User ID from Redmine
            users_response = requests.get(
                f"{REDMINE_URL}/users.json",
                params={"mail": email},
                headers={"X-Redmine-API-Key": REDMINE_API_KEY}
            )

            if users_response.status_code != 200 or not users_response.json().get('users'):
                return None, "User not found in Redmine"

            user_id = users_response.json()['users'][0]['id']
            user_data = users_response.json()['users'][0] 

            user_details_response = requests.get(
                f"{REDMINE_URL}/users/{user_id}.json",
                headers={"X-Redmine-API-Key": REDMINE_API_KEY}
            )

            if user_details_response.status_code != 200:
                return None, "Failed to fetch user details"

            # Extract API key from the user details response
            user_details = user_details_response.json().get('user', {})
            api_key = user_details.get('api_key')
            if not api_key:
                return None, "API key not found for the user"

            # Get User Role from Redmine Memberships
            memberships_response = requests.get(
              
                f"{REDMINE_URL}/projects/GSMB/memberships.json",
                headers={"X-Redmine-API-Key": REDMINE_API_KEY}
            )

            if memberships_response.status_code != 200:
                return None, "Failed to fetch Redmine memberships"

            memberships = memberships_response.json().get('memberships', [])

            # Find the role associated with the user_id
            gsm_project_role = None
            for membership in memberships:
                if membership.get('user', {}).get('id') == user_id:
                    gsm_project_role = membership.get('roles', [{}])[0].get('name')  # Assuming first role is primary

            if not gsm_project_role:
                return None, "User role not found in Redmine"

            return user_id,user_data,gsm_project_role,api_key

        except ValueError as e:
            return None, f"Invalid Google token: {str(e)}"
        except Exception as e:
            return None, f"Server error: {str(e)}"
        
    @staticmethod
    def authenticate_google_access_token(access_token):
        try:
            # Here, we use Google's access token verification
            response = requests.get(
                f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
            )
            
            if response.status_code != 200:
                return None, "Failed to verify access token with Google"

            id_info = response.json()

            # Extract email and other user information from the access token
            email = id_info.get('email')
            if not email:
                return None, "Email not found in access token"

            # Proceed with the same logic for fetching user info from Redmine
            users_response = requests.get(
                f"{REDMINE_URL}/users.json",
                params={"mail": email},
                headers={"X-Redmine-API-Key": REDMINE_API_KEY}
            )

            if users_response.status_code != 200 or not users_response.json().get('users'):
                return None, "User not found in Redmine"

            user_id = users_response.json()['users'][0]['id']
            user_data = users_response.json()['users'][0]

            user_details_response = requests.get(
                f"{REDMINE_URL}/users/{user_id}.json",
                headers={"X-Redmine-API-Key": REDMINE_API_KEY}
            )

            if user_details_response.status_code != 200:
                return None, "Failed to fetch user details"

            user_details = user_details_response.json().get('user', {})
            api_key = user_details.get('api_key')
            if not api_key:
                return None, "API key not found for the user"

            memberships_response = requests.get(
              
                f"{REDMINE_URL}/projects/GSMB/memberships.json",
                headers={"X-Redmine-API-Key": REDMINE_API_KEY}

            )

            if memberships_response.status_code != 200:
                return None, "Failed to fetch Redmine memberships"

            memberships = memberships_response.json().get('memberships', [])

            gsm_project_role = None
            for membership in memberships:
                if membership.get('user', {}).get('id') == user_id:
                    gsm_project_role = membership.get('roles', [{}])[0].get('name')

            if not gsm_project_role:
                return None, "User role not found in Redmine"

            return user_id, user_data, gsm_project_role, api_key

        except Exception as e:
            return None, f"Error: {str(e)}"
        
    @staticmethod
    def initiate_password_reset(email):
        """
        Initiates the password reset process.
        - Checks if the email exists.
        - Generates a reset token and stores it in the cache.
        - Sends a reset email to the user.
        """
        # Check if the email exists in the system
        user_exists = AuthService.check_user_by_email(email)
        if not user_exists:
            return {'error': 'If the email exists, a reset link will be sent'}

        # Generate a unique password reset token
        reset_token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour

        expires_in = (expires_at - datetime.now()).total_seconds()

        # Store the token in the cache with a prefix
        cache_key = f"reset_token:{reset_token}"
        cache.set(cache_key, email, expires_in)

        # Send the reset link to the user's email
        reset_link = f"http://localhost:5173/reset-password?token={reset_token}"
        AuthService.send_reset_email(email, reset_link)

        return {'message': 'Password reset initiated'} 

    @staticmethod
    def check_user_by_email(email):
        """
        Checks if a user with the given email exists in Redmine.
        """
        # Redmine API endpoint for listing users
        url = f"{REDMINE_URL}/users.json"
        
        # Query parameters to filter users by email
        params = {
            'key': REDMINE_API_KEY,
            'name': email  # Redmine allows filtering by name or email
        }
        
        try:
            # Make a GET request to the Redmine API
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Parse the JSON response
            users = response.json().get('users', [])
            
            # Check if any user matches the email
            for user in users:
                if user.get('mail') == email:
                    return True
            
            # If no user matches, return False
            return False
        
        except requests.exceptions.RequestException as e:
            print(f"Error querying Redmine API: {e}")
            return False

    @staticmethod
    def send_reset_email(email, reset_link):
        """
        Sends a password reset email to the user.
        """
        msg = MIMEText(f"Click the link to reset your password: {reset_link}")
        msg['Subject'] = 'Password Reset Request'
        msg['From'] = 'noreply@yourdomain.com'
        msg['To'] = email

        # Send the email (configure your SMTP server)
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login('insaf.ahmedh@gmail.com', 'ulge fzkp izhg idwf')
                server.sendmail('insaf.ahmedh@gmail.com', [email], msg.as_string())
        except Exception as e:
            print(f"Failed to send email: {e}")

    @staticmethod
    def reset_password(token, new_password):
        """
        Resets the user's password.
        """
        # Validate the token
        cache_key = f"reset_token:{token}"
        email = cache.get(cache_key)
       

        if not email:
            return {'error': 'Invalid or expired token'}
        
        try:
            users_response = requests.get(
                f"{REDMINE_URL}/users.json",
                params={"mail": email},
                headers={"X-Redmine-API-Key": REDMINE_API_KEY}
            )
            users_response.raise_for_status()  # Raise an exception for HTTP errors

            users = users_response.json().get('users', [])
            if not users:
                return {'success': False, 'error': 'User not found in Redmine'}

            user_id = users[0]['id']
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch user details: {e}")
            return {'success': False, 'error': 'Failed to fetch user details from Redmine'}

        # Step 2: Update the user's password
        update_url = f"{REDMINE_URL}/users/{user_id}.json"
        headers = {
            'X-Redmine-API-Key': REDMINE_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {
            'user': {
                'password': new_password
            }
        }

        try:
            response = requests.put(update_url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors
            print(f"Password updated successfully for user {email}")
            return {'success': True}
        except requests.exceptions.RequestException as e:
            print(f"Failed to update password: {e}")
            return {'success': False, 'error': 'Failed to update password in Redmine'}
        finally:
            # Delete the token from the cache
            cache.delete(cache_key)

    @staticmethod
    def register_police_officer(login, first_name, last_name, email, password, custom_fields):
        """
        Registers a Police Officer in Redmine with status = inactive.
        """
        return AuthService._register_officer("Police Officer", login, first_name, last_name, email, password, custom_fields)

    @staticmethod
    def register_gsmb_officer(login, first_name, last_name, email, password, custom_fields):
        """
        Registers a GSMB Officer in Redmine with status = inactive.
        """
        return AuthService._register_officer("GSMB Officer", login, first_name, last_name, email, password, custom_fields)

    @staticmethod
    def register_mining_engineer(login, first_name, last_name, email, password, custom_fields):
        """
        Registers a GSMB Officer in Redmine with status = inactive.
        """
        return AuthService._register_officer("Mining Engineer", login, first_name, last_name, email, password, custom_fields)
    
    @staticmethod
    def _register_officer(role, login, first_name, last_name, email, password, custom_fields):
        """
        Registers an officer in Redmine with status = inactive.
        """
        REDMINE_URL = os.getenv("REDMINE_URL")
        admin_api_key = os.getenv("REDMINE_ADMIN_API_KEY")

        url = f"{REDMINE_URL}/users.json"
        headers = {
            "X-Redmine-API-Key": admin_api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "user": {
                "login": login,
                "firstname": first_name,
                "lastname": last_name,
                "mail": email,
                "password": password,
                "status": 3,  # Inactive
                "custom_fields": custom_fields
            }
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            return response.json(), None
        else:
            return None, response.json()
        
    @staticmethod
    def upload_file_to_redmine(file):
     
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
    def assign_role(user_id, role_name):
        try:
            # The role ID corresponding to the "PoliceOfficer" role in your project
            role_ids = {
                "PoliceOfficer": 7, 
                "GSMBOfficer":6 ,# Role ID for "PoliceOfficer" as per your Redmine API response
                "MLOwner":8,
                "miningEngineer":10
            }

            # Get the correct role ID
            role_id = role_ids.get(role_name)
            if not role_id:
                return None, f"Role '{role_name}' not found in the predefined role list."

            # Add the user to the project with the role ID
            membership_data = {
                "membership": {
                    "user_id": user_id,
                    "role_ids": [role_id],  # Pass the role ID here, not the name
                    "project_id": 1  # Ensure this is the correct project ID for GSMB
                }
            }

            # Make the API call to add the user to the project with the role
            response = requests.post(
                f"{REDMINE_URL}/projects/1/memberships.json",  # Ensure the project ID is correct
                headers={"X-Redmine-API-Key": REDMINE_API_KEY},
                json=membership_data
            )

            if response.status_code != 201:
                return None, f"Failed to create membership: {response.text}"

            return response.json(), None

        except Exception as e:
            return None, f"Error while assigning role: {str(e)}"    


    @staticmethod
    def register_mlowner(login, first_name, last_name, email, password, custom_fields, attachments=None):
        REDMINE_URL = os.getenv("REDMINE_URL")
        API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")
        try:
            user_payload = {
                "login": login,
                "firstname": first_name,
                "lastname": last_name,
                "mail": email,
                "status": 3, 
                "password": password,
                "custom_fields": custom_fields
            }
            
            # Call Redmine API to create user
            response = requests.post(f"{REDMINE_URL}/users.json", json={"user": user_payload}, headers={"X-Redmine-API-Key": API_KEY})
            
            if response.status_code != 201:
                return None, response.json()
            
            user_id = response.json()["user"]["id"]
            
            # Upload file attachments if available
            if attachments:
                for custom_field_id, file_path in attachments.items():
                    upload_response = requests.post(f"{REDMINE_URL}/uploads.json", files={"file": open(file_path, "rb")}, headers={"X-Redmine-API-Key": API_KEY})
                    
                    if upload_response.status_code == 201:
                        token = upload_response.json()["upload"]["token"]
                        update_payload = {"user": {"custom_fields": [{"id": custom_field_id, "value": token}]}}
                        requests.put(f"{REDMINE_URL}/users/{user_id}.json", json=update_payload, headers={"X-Redmine-API-Key": API_KEY})
            
            return response.json(), None
        
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def upload_file_to_redmine(file):
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
    def register_company(login, first_name, last_name, email, password, custom_fields):
        """
        Registers a mining license company in Redmine.
        """
        REDMINE_URL = os.getenv("REDMINE_URL")
        admin_api_key = os.getenv("REDMINE_ADMIN_API_KEY")

        url = f"{REDMINE_URL}/users.json"
        headers = {
            "X-Redmine-API-Key": admin_api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "user": {
                "login": login,
                "firstname": first_name,
                "lastname": last_name,
                "mail": email,
                "password": password,
                "custom_fields": custom_fields
            }
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            return response.json(), None
        else:
            return None, response.json()
        
