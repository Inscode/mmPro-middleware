import os
import tempfile
from flask import Blueprint, jsonify, request
from middleware.auth_middleware import role_required,check_token
from services.auth_service import AuthService
from services.mining_engineer_service import MiningEnginerService
import requests  # For making HTTP requests to Redmine
from flask import Response  # For streaming file responses in Flask
from utils.jwt_utils import JWTUtils
from flask import send_file
from io import BytesIO
from utils.constants import AUTH_TOKEN_INVALID_ERROR,AUTH_TOKEN_MISSING_ERROR
    
# Constants
BEARER_PREFIX = "Bearer "

# Define the Blueprint for mining_enginer
mining_enginer_bp = Blueprint('mining_enginer', __name__)

@mining_enginer_bp.route('/miningOwner-appointment/<int:issue_id>', methods=['PUT'])
@check_token
@role_required(['miningEngineer'])
def update_mining_owner_appointment(issue_id):
    try:
        # Extract token from headers
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": AUTH_TOKEN_MISSING_ERROR}, 400

        token = auth_header.replace(BEARER_PREFIX, "")
        if not token:
            return {"error": AUTH_TOKEN_INVALID_ERROR}, 400

        # Get update data from request body
        update_data = request.get_json()
        if not update_data:
            return {"error": "No update data provided"}, 400
        
        # Call service to update the appointment
        result, error = MiningEnginerService.update_mining_owner_appointment(
            token=token,
            issue_id=issue_id,
            update_data=update_data
        )
        
        if error:
            return {"error": error}, 500
        
        return {"message": "Appointment updated successfully", "issue": result}, 200
    
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}, 500
    

@mining_enginer_bp.route('/me-pending-licenses', methods=['GET'])
@check_token
@role_required(['miningEngineer'])
def get_me_pending_licenses():
    try:
        # Get the token from the Authorization header
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": AUTH_TOKEN_MISSING_ERROR}), 401

        # Fetch Mining Licenses from the service
        mining_licenses, error = MiningEnginerService.get_me_pending_licenses(token)
        
        if error:
            return jsonify({"error": error}), 500 if "Server error" in error else 400
            
        return jsonify({"success": True, "data": mining_licenses}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@mining_enginer_bp.route('/download-attachment/<int:attachment_id>', methods=['GET'])
@check_token
def download_attachment(attachment_id):
    try:
        token = request.headers.get('Authorization')
        api_key = JWTUtils.get_api_key_from_token(token)
        
        REDMINE_URL = os.getenv("REDMINE_URL")
        attachment_url = f"{REDMINE_URL}/attachments/download/{attachment_id}"
        
        # Stream the response from Redmine
        response = requests.get(
            attachment_url,
            headers={"X-Redmine-API-Key": api_key},
            stream=True
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch attachment"}), response.status_code
            
        return Response(
            response.iter_content(chunk_size=1024),
            content_type=response.headers.get('Content-Type', 'application/octet-stream'),
            headers={
                'Content-Disposition': response.headers.get(
                    'Content-Disposition', 
                    f'attachment; filename=attachment_{attachment_id}'
                )
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@mining_enginer_bp.route('/create-ml-appointment', methods=['POST'])
@check_token
@role_required(['miningEngineer'])
def create_ml_appointment():
    try:
        # 1. Extract token
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": AUTH_TOKEN_MISSING_ERROR}), 401

        # 2. Validate input
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is empty"}), 400

        required_fields = ['start_date', 'mining_license_number','Google_location']
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": f"Missing required fields: {', '.join(required_fields)}"
            }), 400

        # 3. Call service
        result, error = MiningEnginerService.create_ml_appointment(
            token=token,
            start_date=data['start_date'],
            mining_license_number=data['mining_license_number'],
            Google_location=data['Google_location']
        )

        # 4. Handle response
        if error:
            status_code = 500 if "Redmine error" in error else 400
            return jsonify({"error": error}), status_code

        return jsonify({
            "success": True,
            "data": result,
            "message": "Appointment created successfully"
        }), 201

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    
    
@mining_enginer_bp.route('/miningEngineer-approve/<int:me_appointment_issue_id>', methods=['PUT'])
@check_token
@role_required(['miningEngineer'])
def mining_engineer_approve(me_appointment_issue_id):                               
    try:
        # Extract token from headers
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": AUTH_TOKEN_MISSING_ERROR}, 400
        
        token = auth_header.replace(BEARER_PREFIX, "")
        if not token:
            return {"error": AUTH_TOKEN_INVALID_ERROR}, 400

        me_report_file = request.files.get('me_report')

        ml_number_full = request.form.get("ml_number")  # e.g., "ML Request LLL/100/206"
        if not ml_number_full:
            return {"error": "ML number is required"}, 400

        # Extract numeric part (e.g., 206)
        try:
            ml_request_id = ml_number_full.strip().split("/")[-1]
        except Exception:
            return {"error": "Invalid ML number format"}, 400
        # Upload the file to Redmine and get the file ID
        me_report_file_id = AuthService.upload_file_to_redmine(me_report_file) if me_report_file else None

        # Get capacity value first to use for remaining
        capacity_value = request.form.get("Capacity", "")

        # Get form data (not JSON)
        update_data = {
            "status_id": request.form.get("status_id", 32),
            "Remaining": request.form.get("Remaining", capacity_value),
            "Used": request.form.get("Used", 0),
            "royalty": request.form.get("royalty", 5000),
            "start_date": request.form.get("start_date", ""),
            "due_date": request.form.get("due_date", ""),
            "Capacity": capacity_value,
            "month_capacity": request.form.get("month_capacity", ""),
            "me_comment": request.form.get("me_comment", ""),
            "me_report":me_report_file_id
        }
        
        # Call service to update the appointment
        result, error = MiningEnginerService.mining_engineer_approve(
            token=token,
            me_appointment_id = me_appointment_issue_id,
            ml_id=ml_request_id,
            update_data=update_data,
            attachments={"me_report": me_report_file} if me_report_file else None
        )
        
        if error:
            return {"error": error}, 500
        
        return {"message": "Mining license updated successfully", "issue": result}, 200
    
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}, 500
    

@mining_enginer_bp.route('/miningEngineer-reject/<int:me_appointment_issue_id>', methods=['PUT'])
@check_token
@role_required(['miningEngineer'])
def mining_engineer_reject(me_appointment_issue_id):                               
    try:
        # Extract token from headers
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": AUTH_TOKEN_MISSING_ERROR}, 400
        
        token = auth_header.replace(BEARER_PREFIX, "")
        if not token:
            return {"error": AUTH_TOKEN_INVALID_ERROR}, 400

        ml_number_full = request.form.get("ml_number")  # e.g., "ML Request LLL/100/206"
        if not ml_number_full:
            return {"error": "ML number is required"}, 400

        # Extract numeric part (e.g., 206)
        try:
            ml_request_id = ml_number_full.strip().split("/")[-1]
        except Exception:
            return {"error": "Invalid ML number format"}, 400
        
        # Get rejection report file
        me_report_file = request.files.get('me_report') 

        # Upload the file to Redmine and get the file ID
        me_report_file_id = AuthService.upload_file_to_redmine(me_report_file) if me_report_file else None

        # Get form data
        update_data = {
            "status_id": 6,  # Rejected status
            "me_comment": request.form.get("me_comment", ""),
            "me_report": me_report_file_id
        }
        
        # Call service to update the issue in Redmine
        result, error = MiningEnginerService.mining_engineer_reject(
            token=token,
            ml_id=ml_request_id,
            me_appointment_id=me_appointment_issue_id,
            update_data=update_data
        )
        
        if error:
            return {"error": error}, 500
        
        return {"message": "Mining license rejected successfully", "issue": result}, 200
    
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}, 500

#ME Appointment Scheduled(status id = 31)
#Hold (status id = 39)
#Rejected(status id = 6)
@mining_enginer_bp.route('/update-issue-status', methods=['POST'])
@check_token
@role_required(['miningEngineer'])
def update_issue_status():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": AUTH_TOKEN_MISSING_ERROR}), 400

        data = request.get_json()
        issue_id = data.get('issue_id')
        new_status_id = data.get('new_status_id')

        if not all([issue_id, new_status_id]):
            return jsonify({"error": "Missing required parameters"}), 400

        result, error = MiningEnginerService.change_issue_status(
            token,
            issue_id,
            new_status_id
        )

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@mining_enginer_bp.route('/meetingScheduledLicenses', methods=['GET'])
@check_token
@role_required(['miningEngineer'])
def get_me_meeting_schedule_licenses():
    try:
        # Get the token from the Authorization header
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": AUTH_TOKEN_MISSING_ERROR}), 401

        # Fetch Mining Licenses from the service
        mining_licenses, error = MiningEnginerService.get_me_meeting_schedule_licenses(token)
        
        if error:
            return jsonify({"error": error}), 500 if "Server error" in error else 400
            
        return jsonify({"success": True, "data": mining_licenses}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mining_enginer_bp.route('/me-appointments', methods=['GET'])
@check_token
@role_required(['miningEngineer'])
def get_me_appointments():
    try:
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": AUTH_TOKEN_MISSING_ERROR}), 401

        result = MiningEnginerService.get_me_appointments(token)
        error = None
        
        if isinstance(result, dict) and "error" in result:
            status_code = 500 if "Server error" in result["error"] else 400
            return jsonify({"error": result["error"]}), status_code
            
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mining_enginer_bp.route('/view-mining-license/<int:issue_id>', methods=['GET'])
@check_token
@role_required(['miningEngineer'])
def get_mining_request_view_button(issue_id):
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": AUTH_TOKEN_MISSING_ERROR}), 400

        # Fetch issue details
        mining_license, error = MiningEnginerService.get_mining_license_view_button(token, issue_id)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": mining_license}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mining_enginer_bp.route('/me-approve-license', methods=['GET'])
@check_token
@role_required(['miningEngineer'])
def get_me_approve_license():
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split()[1] if auth_header and ' ' in auth_header else auth_header
        
        if not token:
            return jsonify({"error": AUTH_TOKEN_MISSING_ERROR}), 401

        result = MiningEnginerService.get_me_approve_license(token)
        error = None
        
        if isinstance(result, dict) and "error" in result:
            status_code = 500 if "Server error" in result["error"] else 400
            return jsonify({"error": result["error"]}), status_code
            
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@mining_enginer_bp.route('/me-approve-single-license/<int:issue_id>', methods=['GET'])
@check_token
@role_required(['miningEngineer'])
def get_me_approve_single_license(issue_id):
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split()[1] if auth_header and ' ' in auth_header else auth_header
        
        if not token:
            return jsonify({"error": AUTH_TOKEN_MISSING_ERROR}), 401

        result = MiningEnginerService.get_me_approve_single_license(token,issue_id=issue_id,)
        error = None
        
        if isinstance(result, dict) and "error" in result:
            status_code = 500 if "Server error" in result["error"] else 400
            return jsonify({"error": result["error"]}), status_code
            
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500    


# Get the count of Mining Licenses
@mining_enginer_bp.route('/me-licenses-count', methods=['GET'])
@check_token
@role_required(['miningEngineer'])
def get_me_licenses_count():
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split()[1] if auth_header and ' ' in auth_header else auth_header
        
        if not token:
            return jsonify({"error": AUTH_TOKEN_MISSING_ERROR}), 401
        # Fetch Mining Licenses from the service
        mining_licenses, error = MiningEnginerService.get_me_licenses_count(token)
        
        if error:
            return jsonify({"error": error}), 500 if "Server error" in error else 400
            
        return jsonify({"success": True, "data": mining_licenses}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@mining_enginer_bp.route('/set-license-hold', methods=['POST'])
@check_token
@role_required(['miningEngineer'])
def set_license_hold():
    try:
        data = request.get_json()
        issue_id = data.get("issue_id")
        reason_for_hold = data.get("reason_for_hold")

        if not issue_id or not reason_for_hold:
            return jsonify({"error": "Both 'issue_id' and 'reason_for_hold' are required."}), 400

        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": AUTH_TOKEN_MISSING_ERROR}), 400

        success, error = MiningEnginerService.set_license_hold(issue_id, reason_for_hold, token)
        if not success:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "message": f"Issue {issue_id} set to Hold successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mining_enginer_bp.route('/me-hold-licenses', methods=['GET'])
@check_token
@role_required(['miningEngineer'])
def get_me_hold_licenses():
    try:
        # Extract token from headers
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": AUTH_TOKEN_INVALID_ERROR}), 401

        # Call service
        licenses, error = MiningEnginerService.get_me_hold_licenses(token)

        if error:
            return jsonify({"error": error}), 500 if "Server error" in error else 400

        return jsonify({"success": True, "data": licenses}), 200

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@mining_enginer_bp.route('/me-reject-licenses', methods=['GET'])
@check_token
@role_required(['miningEngineer'])
def get_me_reject_licenses():
    try:
        # Get the token from the Authorization header
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": AUTH_TOKEN_MISSING_ERROR}), 401

        # Fetch Mining Licenses from the service
        mining_licenses, error = MiningEnginerService.get_me_reject_licenses(token)
        
        if error:
            return jsonify({"error": error}), 500 if "Server error" in error else 400
            
        return jsonify({"success": True, "data": mining_licenses}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    