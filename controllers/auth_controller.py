from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from utils.jwt_utils import JWTUtils
from utils.user_utils import UserUtils
from utils.constants import MISSING_REQUIRED_FIELDS_ERROR, INTERNAL_SERVER_ERROR
import jwt
from config import Config
import requests
import smtplib
from email.mime.text import MIMEText
from services.cache import cache
import random
import secrets  
from dotenv import load_dotenv
import os

load_dotenv()

auth_bp = Blueprint('auth_controller', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user_data, user_role, api_key = AuthService.authenticate_user(username, password)
    
    if not user_data:
        return jsonify({'message': "Invalid Credentials"}), 401

    # Extract user details
    # print("user data", user_data)
    user_id = user_data.get('id')
    
    username = f"{user_data.get('firstname')} {user_data.get('lastname')}"

    # Generate access & refresh tokens
    tokens = JWTUtils.create_jwt_token(user_id, user_role)

    return jsonify({
        'token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
        'role': user_role,
        'username': username,
        'userId': user_id
    })


@auth_bp.route('/google-login', methods=['POST'])
def auth_google():
    token = request.json.get('token')
    if not token:
        return jsonify({"error": "Google token is required"}), 400
    
    auth_result = AuthService.authenticate_google_token(token)
    
    if auth_result[0] is None:  # If authentication failed
        return jsonify({"error": auth_result[1]}), 401

    user_id, user_data, user_role = auth_result  

    username=f"{user_data.get('firstname')} {user_data.get('lastname')}",
    # Create JWT token using the service
    tokens =  JWTUtils.create_jwt_token(user_id,user_role)

    return jsonify({'token': tokens['access_token'], 'refresh_token': tokens['refresh_token'],'role': user_role, 'username':username, 'userId':user_id})

@auth_bp.route('/mobile-google-login', methods=['POST'])
def mobile_auth_google():
    access_token = request.json.get('token')
    if not access_token:
        return jsonify({"error": "Google access token is required"}), 400

    auth_result = AuthService.authenticate_google_access_token(access_token)

    if auth_result[0] is None:
        return jsonify({"error": auth_result[1]}), 401

    user_id, user_data, user_role = auth_result

    username = f"{user_data.get('firstname')} {user_data.get('lastname')}"
    jwt_token = JWTUtils.create_jwt_token(user_id, user_role)

    return jsonify({'token': jwt_token, 'role': user_role, 'username': username, 'userId': user_id})


@auth_bp.route('/refresh-token', methods=['POST'])
def refresh_token():
    
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"message": "Refresh token is required"}), 401

    try:
        decoded_payload = jwt.decode(refresh_token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])

        if not decoded_payload.get("refresh"):
            return jsonify({"message": "Invalid refresh token"}), 401

        user_id = decoded_payload["user_id"]
      
        user_role = decoded_payload["role"]
       
       
        new_access_token = JWTUtils.create_access_token(user_id, user_role)

        return jsonify({
            'access_token': new_access_token  
        })

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Refresh token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
       
        return jsonify({"message": INTERNAL_SERVER_ERROR}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Forgot Password Endpoint
    - Validates the email.
    - Calls the AuthService to handle the password reset process.
    """
    data = request.get_json()
    email = data.get('email')
    redirect_base_url = data.get('redirect_base_url')
   

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    # Call the AuthService to handle the password reset process
    result = AuthService.initiate_password_reset(email,redirect_base_url)

    if result.get('error'):
        return jsonify({'message': result['error']}), 400
    
    return jsonify({'message': 'If the email exists, a reset link will be sent'}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset Password Endpoint
    - Validates the reset token.
    - Updates the user's password.
    """
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required'}), 400

    # Call the AuthService to handle the password reset
    result = AuthService.reset_password(token, new_password)

    if not result.get('success'):
        error_message = result.get('error', 'Failed to reset password')
        return jsonify({'error': error_message}), 400

    return jsonify({'message': 'Password updated successfully'}), 200

@auth_bp.route('/register-police-officer', methods=['POST'])
def register_police_officer():
    """
    Register a Police Officer with inactive status and assign them a "PoliceOfficer" role in the GSMB project.
    """
    try:
        login = request.form.get('login')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        designation = request.form.get('designation')
        nic_number = request.form.get('nic_number')
        mobile_number = request.form.get('mobile_number')
        user_Type = request.form.get('user_Type')

        if not all([login, first_name, last_name, email, password, nic_number, mobile_number, designation]):
            return jsonify({"error": MISSING_REQUIRED_FIELDS_ERROR}), 400

        nic_front_file = request.files.get('nic_front')
        nic_back_file = request.files.get('nic_back')
        work_id_file = request.files.get('work_id')


        nic_front_id = AuthService.upload_file_to_redmine(nic_front_file) if nic_front_file else None
        nic_back_id = AuthService.upload_file_to_redmine(nic_back_file) if nic_back_file else None
        work_id_file_id = AuthService.upload_file_to_redmine(work_id_file) if work_id_file else None

        custom_fields = [
            {"id": 41, "value": nic_number},
            {"id": 65, "value": mobile_number},
            {"id": 86, "value": designation},
            {"id": 89, "value": user_Type},
        ]

        if nic_front_id:
            custom_fields.append({"id": 83, "value": nic_front_id})
        if nic_back_id:
            custom_fields.append({"id": 84, "value": nic_back_id})
        if work_id_file_id:
            custom_fields.append({"id": 85, "value": work_id_file_id})

        # Register the Police Officer in Redmine
        result, error = AuthService.register_police_officer(
            login, first_name, last_name, email, password, custom_fields
        )

        if error:
            return jsonify({"error": error}), 500

        # Assign the "PoliceOfficer" role in the GSMB project
        user_id = result.get('user', {}).get('id')
        if user_id:
            role_name = "PoliceOfficer"
            role_result, role_error = AuthService.assign_role(user_id, role_name)
            if role_error:
                return jsonify({"error": role_error}), 500

        return jsonify({"success": True, "role": "Police Officer", "status": "inactive", "data": result}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@auth_bp.route('/register-gsmb-officer', methods=['POST'])
def register_gsmb_officer():
    """
    Register a GSMB Officer with inactive status and assign them a "GSMB Officer" role in the GSMB project.
    """
    try:
        login = request.form.get('login')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        designation = request.form.get('designation')
        nic_number = request.form.get('nic_number')
        mobile_number = request.form.get('mobile_number')
        user_Type = request.form.get('user_Type')

        if not all([login, first_name, last_name, email, password, nic_number, mobile_number, designation]):
            return jsonify({"error": MISSING_REQUIRED_FIELDS_ERROR}), 400

        nic_front_file = request.files.get('nic_front') 
        nic_back_file = request.files.get('nic_back')
        work_id_file = request.files.get('work_id')


        nic_front_id = AuthService.upload_file_to_redmine(nic_front_file) if nic_front_file else None
        nic_back_id = AuthService.upload_file_to_redmine(nic_back_file) if nic_back_file else None
        work_id_file_id = AuthService.upload_file_to_redmine(work_id_file) if work_id_file else None

        custom_fields = [
            {"id": 41, "value": nic_number},
            {"id": 65, "value": mobile_number},
            {"id": 86, "value": designation},
            {"id": 89, "value": user_Type},
        ]

        if nic_front_id:
            custom_fields.append({"id": 83, "value": nic_front_id})
        if nic_back_id:
            custom_fields.append({"id": 84, "value": nic_back_id})
        if work_id_file_id:
            custom_fields.append({"id": 85, "value": work_id_file_id})

        # Register the GSMB Officer in Redmine
        result, error = AuthService.register_gsmb_officer(
            login, first_name, last_name, email, password, custom_fields
        )

        if error:
            return jsonify({"error": error}), 500

        # Assign the "GSMB Officer" role in the GSMB project
        user_id = result.get('user', {}).get('id')
        if user_id:
            role_name = "GSMBOfficer"
            role_result, role_error = AuthService.assign_role(user_id, role_name)
            if role_error:
                return jsonify({"error": role_error}), 500

        return jsonify({"success": True, "role": "GSMB Officer", "status": "inactive", "data": result}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/register-mining-engineer', methods=['POST'])
def register_mining_engineer():
    
    try:
        login = request.form.get('login')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        designation = request.form.get('designation')
        nic_number = request.form.get('nic_number')
        mobile_number = request.form.get('mobile_number')
        user_Type = request.form.get('user_Type')

        if not all([login, first_name, last_name, email, password, nic_number, mobile_number, designation]):
            return jsonify({"error": MISSING_REQUIRED_FIELDS_ERROR}), 400

        nic_front_file = request.files.get('nic_front') 
        nic_back_file = request.files.get('nic_back')
        work_id_file = request.files.get('work_id')


        nic_front_id = AuthService.upload_file_to_redmine(nic_front_file) if nic_front_file else None
        nic_back_id = AuthService.upload_file_to_redmine(nic_back_file) if nic_back_file else None
        work_id_file_id = AuthService.upload_file_to_redmine(work_id_file) if work_id_file else None

        custom_fields = [
            {"id": 41, "value": nic_number},
            {"id": 65, "value": mobile_number},
            {"id": 86, "value": designation},
            {"id": 89, "value": user_Type},
        ]

        if nic_front_id:
            custom_fields.append({"id": 83, "value": nic_front_id})
        if nic_back_id:
            custom_fields.append({"id": 84, "value": nic_back_id})
        if work_id_file_id:
            custom_fields.append({"id": 85, "value": work_id_file_id})

        # Register the GSMB Officer in Redmine
        result, error = AuthService.register_mining_engineer(
            login, first_name, last_name, email, password, custom_fields
        )

        if error:
            return jsonify({"error": error}), 500

        # Assign the "GSMB Officer" role in the GSMB project
        user_id = result.get('user', {}).get('id')
        if user_id:
            role_name = "miningEngineer"
            role_result, role_error = AuthService.assign_role(user_id, role_name)
            if role_error:
                return jsonify({"error": role_error}), 500

        return jsonify({"success": True, "role": "GSMB Officer", "status": "inactive", "data": result}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/register-mlowners/individual', methods=['POST'])
def register_individual_mlowner():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = [
            'login', 'first_name', 'last_name', 'email', 'password',
            'national_identity_card', 'mobile_number'
            # 'address', 'nationality', 
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Prepare custom fields for individual
        custom_fields = [
            {"id": 41, "value": data['national_identity_card']},  # National Identity Card
            {"id": 65, "value": data.get('mobile_number', '')},  # Mobile Number
            {"id": 89, "value": 'mlOwner'},
        ]

        # Call service to create user
        result, error = AuthService.register_mlowner(
            login=data['login'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=data['password'],
            custom_fields=custom_fields
        )

        if error:
            return jsonify({"error": error}), 500

        user_id = result.get('user', {}).get('id')
        if user_id:
            role_name = "MLOwner"
            role_result, role_error = AuthService.assign_role(user_id, role_name)
            if role_error:
                return jsonify({"error": role_error}), 500

        return jsonify({
            "success": True,
            "role": "mlOwner",
            "status": "inactive",
            "data": result
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@auth_bp.route('/register-mlowners/company', methods=['POST'])
def register_company():
    """
    Register Mining License Company
    - Accepts form-data (including file uploads)
    - Uploads files to Redmine and retrieves attachment IDs
    - Registers company with Redmine API
    """

    try:
        # Get required fields
        login = request.form.get('login')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        country_of_incorporation = request.form.get('country_of_incorporation')
        head_office = request.form.get('head_office')
        address_of_registered_company = request.form.get('address_of_registered_company')

        # Validate required fields
        if not all([login, first_name, last_name, email, password, country_of_incorporation, head_office, address_of_registered_company]):
            return jsonify({"error": MISSING_REQUIRED_FIELDS_ERROR}), 400

        # Handle file uploads (Articles of Association & Annual Reports)
        articles_file = request.files.get('articles_of_association')
        annual_reports_file = request.files.get('annual_reports')

        articles_id = None
        annual_reports_id = None

        if articles_file:
            articles_id = AuthService.upload_file_to_redmine(articles_file)
        if annual_reports_file:
            annual_reports_id = AuthService.upload_file_to_redmine(annual_reports_file)

        # Prepare custom fields
        custom_fields = [
            {"id": 47, "value": country_of_incorporation},  # Country of Incorporation
            {"id": 48, "value": head_office},  # Head Office
            {"id": 49, "value": address_of_registered_company},  # Address of Registered Company
        ]

        if articles_id:
            custom_fields.append({"id": 75, "value": articles_id})  # Articles of Association
        if annual_reports_id:
            custom_fields.append({"id": 76, "value": annual_reports_id})  # Annual Reports

        # Register company in Redmine
        result, error = AuthService.register_company(
            login, first_name, last_name, email, password, custom_fields
        )

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": result}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# testing code delete
@auth_bp.route('/tracker-issues', methods=['GET'])
def get_tracker_issues():
    """
    Get Sample Tracker Issues Endpoint
    - Fetches issues from Redmine API with tracker_id=9
    - Acts as a proxy to avoid CORS issues
    - Returns the issues data
    """
    # Your Redmine API configuration
    REDMINE_API_URL = os.getenv("REDMINE_API_URL")
    REDMINE_API_KEY = "2fe97b781bc33e9d38305356949639971a921fb0"  # Move this to config in production
    
    # Required parameters
    project_id = request.args.get('project_id', default=1, type=int)
    tracker_id = request.args.get('tracker_id', default=9, type=int)
    
    try:
        # Make request to Redmine API
        response = requests.get(
            REDMINE_API_URL,
            params={
                'project_id': project_id,
                'tracker_id': tracker_id,
                'include': 'attachments'
            },
            headers={
                'X-Redmine-API-Key': REDMINE_API_KEY,
                'Content-Type': 'application/json'
            }
        )
        
        # Check for errors
        response.raise_for_status()
        
        # Return the data to the frontend
        return jsonify(response.json()), 200
        
    except requests.exceptions.RequestException as e:
        # Handle different types of errors
        error_message = str(e)
        status_code = 500
        
        if isinstance(e, requests.exceptions.HTTPError):
            status_code = e.response.status_code
            try:
                error_details = e.response.json()
                error_message = error_details.get('error', error_message)
            except ValueError:
                error_message = e.response.text or error_message
        
        return jsonify({
            'error': 'Failed to fetch tracker issues',
            'details': error_message
        }), status_code

@auth_bp.route('/create-issue', methods=['POST'])
def create_issue():
    """
    Create New Issue Endpoint
    - Creates a new issue in Redmine with attachments
    - Properly handles file uploads to Redmine
    """
    REDMINE_API_URL = os.getenv("REDMINE_API_URL")
    REDMINE_UPLOAD_URL = os.getenv("REDMINE_UPLOAD_URL")
    REDMINE_API_KEY = "2fe97b781bc33e9d38305356949639971a921fb0"

    try:
        # Validate input
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        start_date = request.form.get('start_date')
        due_date = request.form.get('due_date')
        
        if not all([start_date, due_date]):
            return jsonify({'error': MISSING_REQUIRED_FIELDS_ERROR}), 400

        # Step 1: Upload the file first to get token
        upload_response = requests.post(
            REDMINE_UPLOAD_URL,
            headers={
                'X-Redmine-API-Key': REDMINE_API_KEY,
                'Content-Type': 'application/octet-stream',
                'Accept': 'application/json'  # Explicitly accept JSON responses
            },
            data=uploaded_file.stream  # Send the file as binary
        )
        
        if upload_response.status_code != 201:
            return jsonify({
                'error': 'File upload failed',
                'details': upload_response.text
            }), upload_response.status_code

        upload_token = upload_response.json().get('upload', {}).get('token')
        if not upload_token:
            return jsonify({'error': 'Failed to get upload token'}), 500

        # Step 2: Create the issue with the upload token
        issue_data = {
            "issue": {
                "project_id": 1,
                "tracker_id": 9,
                "subject": f"New issue",
                "start_date": start_date,
                "due_date": due_date,
                "description": "Issue created via API",
                "uploads": [{
                    "token": upload_token,
                    "filename": uploaded_file.filename,
                    "content_type": uploaded_file.content_type,
                    "description":"survey report"
                }]
            }
        }

        response = requests.post(
            REDMINE_API_URL,
            headers={
                'X-Redmine-API-Key': REDMINE_API_KEY,
                'Content-Type': 'application/json'
            },
            json=issue_data
        )

        if response.status_code != 201:
            return jsonify({
                'error': 'Issue creation failed',
                'details': response.text
            }), response.status_code

        issue_id = response.json().get('issue', {}).get('id')
        return jsonify({
            'message': 'Issue created successfully',
            'issue_id': issue_id
        }), 201

    except Exception as e:
        return jsonify({
            'error': INTERNAL_SERVER_ERROR,
            'details': str(e)
        }), 500

@auth_bp.route('/mobile-forgot-password', methods=['POST'])
def mobile_forgot_password():
    """
    Generates a 6-digit OTP, stores it in cache, and sends it to the user's email.
    """
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'message': 'Email is required'}), 400

    # Generate 6-digit OTP
    otp = str(secrets.randbelow(900000) + 100000)
    cache.set(f"otp:{email}", otp, expire=300)  # 5 minutes expiry

    # Send OTP via email
    subject = "Your OTP Code"
    message = f"Your OTP code is: {otp}. It is valid for 5 minutes."
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = 'noreply@yourdomain.com'
    msg['To'] = email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('insaf.ahmedh@gmail.com', 'ulge fzkp izhg idwf')
            server.sendmail('insaf.ahmedh@gmail.com', [email], msg.as_string())
    except Exception as e:
        return jsonify({'message': f'Failed to send OTP email: {e}'}), 500

    return jsonify({'message': 'OTP sent to email if it exists'}), 200

@auth_bp.route('/mobile-verify-otp', methods=['POST'])
def mobile_verify_otp():
    """
    Verifies the OTP for the given email.
    """
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    if not email or not otp:
        return jsonify({'message': 'Email and OTP are required'}), 400

    cached_otp = cache.get(f"otp:{email}")
    if not cached_otp:
        return jsonify({'message': 'OTP expired or not found'}), 400
    if str(cached_otp) != str(otp):
        return jsonify({'message': 'Invalid OTP'}), 400

    # Optionally, delete OTP after successful verification
    cache.delete(f"otp:{email}")
    # Mark as verified for password reset (optional)
    cache.set(f"otp_verified:{email}", True, expire=600)  # 10 min to reset password

    return jsonify({'message': 'OTP verified'}), 200

@auth_bp.route('/mobile-reset-password', methods=['POST'])
def mobile_reset_password():
    """
    Resets the user's password if OTP is verified.
    """
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('new_password')
    if not email or not new_password:
        return jsonify({'message': 'Email and new password are required'}), 400

    verified = cache.get(f"otp_verified:{email}")
    if not verified:
        return jsonify({'message': 'OTP not verified or expired'}), 400

    # Call your AuthService to update the password using the email
    result = AuthService.reset_password_with_email(email, new_password)
    if not result.get('success'):
        return jsonify({'message': result.get('error', 'Failed to reset password')}), 400

    cache.delete(f"otp_verified:{email}")
    return jsonify({'message': 'Password updated successfully'}), 200


@auth_bp.route('/ping', methods=['GET'])
def ping():
    print("✅ /ping endpoint hit")
    return jsonify({ "message": "Ping successfuy 🎯" })

    


