import os
import tempfile
from flask import Blueprint, jsonify, request
from middleware.auth_middleware import role_required,check_token
from services.auth_service import AuthService
from services.mining_engineer_service import MiningEnginerService


# Define the Blueprint for mining_enginer
mining_enginer_bp = Blueprint('mining_enginer', __name__)

@mining_enginer_bp.route('/miningOwner-appointment/<int:issue_id>', methods=['PUT'])
@check_token
@role_required(['miningEngineer'])
def update_miningOwner_appointment(issue_id):
    try:
        # Extract token from headers
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "Authorization token is missing"}, 400
        
        token = auth_header.replace("Bearer ", "")
        if not token:
            return {"error": "Authorization token is invalid"}, 400
        
        # Get update data from request body
        update_data = request.get_json()
        if not update_data:
            return {"error": "No update data provided"}, 400
        
        # Call service to update the appointment
        result, error = MiningEnginerService.update_miningOwner_appointment(
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
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401
            
        # Split the header to get the token part (handle both "Bearer token" and just "token")
        parts = auth_header.split()
        token = parts[1] if len(parts) == 2 else auth_header
        
        # Fetch Mining Licenses from the service
        mining_licenses, error = MiningEnginerService.get_me_pending_licenses(token)
        
        if error:
            return jsonify({"error": error}), 500 if "Server error" in error else 400
            
        return jsonify({"success": True, "data": mining_licenses}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@mining_enginer_bp.route('/create-ml-appointment', methods=['POST'])
@check_token
@role_required(['miningEngineer'])
def create_ml_appointment():
    try:
        # 1. Extract token
        auth_header = request.headers.get('Authorization')
        token = auth_header.split()[1] if auth_header and ' ' in auth_header else auth_header
        
        if not token:
            return jsonify({"error": "Authorization header missing"}), 401

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
def miningEngineer_approve(me_appointment_issue_id):                               
    try:
        # Extract token from headers
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "Authorization token is missing"}, 400
        
        token = auth_header.replace("Bearer ", "")
        if not token:
            return {"error": "Authorization token is invalid"}, 400
        
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



        # Get form data (not JSON)
        update_data = {
            "status_id": request.form.get("status_id", 32),
            "start_date": request.form.get("start_date", ""),
            "due_date": request.form.get("due_date", ""),
            "Capacity": request.form.get("Capacity", ""),
            "month_capacity": request.form.get("month_capacity", ""),
            "me_comment": request.form.get("me_comment", ""),
            "me_report":me_report_file_id
        }
        
        # Call service to update the appointment
        result, error = MiningEnginerService.miningEngineer_approve(
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
def miningEngineer_reject(me_appointment_issue_id):                               
    try:
        # Extract token from headers
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"error": "Authorization token is missing"}, 400
        
        token = auth_header.replace("Bearer ", "")
        if not token:
            return {"error": "Authorization token is invalid"}, 400
        
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
        result, error = MiningEnginerService.miningEngineer_reject(
            token=token,
            ml_id=ml_request_id,
            me_appointment_id = me_appointment_issue_id,
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
            return jsonify({"error": "Authorization token is missing"}), 400

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
    

@mining_enginer_bp.route('/me-meetingeShedule-licenses', methods=['GET'])
@check_token
@role_required(['miningEngineer'])
def get_me_meetingeShedule_licenses():
    try:
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401
            
        # Split the header to get the token part (handle both "Bearer token" and just "token")
        parts = auth_header.split()
        token = parts[1] if len(parts) == 2 else auth_header
        
        # Fetch Mining Licenses from the service
        mining_licenses, error = MiningEnginerService.get_me_meetingeShedule_licenses(token)
        
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
        auth_header = request.headers.get('Authorization')
        token = auth_header.split()[1] if auth_header and ' ' in auth_header else auth_header
        
        if not token:
            return jsonify({"error": "Authorization header missing"}), 401

        result = MiningEnginerService.get_me_appointments(token)
        
        if "error" in result:
            status_code = 500 if "Server error" in result["error"] else 400
            return jsonify({"error": result["error"]}), status_code
            
        return jsonify(result), 200

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
            return jsonify({"error": "Authorization header missing"}), 401

        result = MiningEnginerService.get_me_approve_license(token)
        
        if "error" in result:
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
            return jsonify({"error": "Authorization header missing"}), 401

        result = MiningEnginerService.get_me_approve_single_license(token,issue_id=issue_id,)
        
        if "error" in result:
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
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401
            
        # Split the header to get the token part (handle both "Bearer token" and just "token")
        parts = auth_header.split()
        token = parts[1] if len(parts) == 2 else auth_header
        
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
            return jsonify({"error": "Authorization token is missing"}), 400

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
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization token is missing"}), 401

        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            return jsonify({"error": "Authorization token is invalid"}), 401

        # Call service
        licenses, error = MiningEnginerService.get_me_hold_licenses(token)

        if error:
            return jsonify({"error": error}), 500 if "Server error" in error else 400

        return jsonify({"success": True, "data": licenses}), 200

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
