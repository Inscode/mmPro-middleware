# from flask_cors import CORS
from tabnanny import check
from flask import Blueprint, jsonify, request
from middleware.auth_middleware import role_required, check_token
from services.gsmb_officer_service import GsmbOfficerService
import os
from werkzeug.utils import secure_filename
import tempfile
from utils.user_utils import UserUtils


# Define the Blueprint for gsmb_officer
gsmb_officer_bp = Blueprint('gsmb_officer', __name__)


            
@gsmb_officer_bp.route('/user-detail/<int:user_id>', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def user_detail(user_id):
    try:
        # Check if the Authorization token is present in the request
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization token is missing"}), 401
        
        # Check if the token starts with 'Bearer ' (you can also validate it further here if needed)
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Invalid token format. Expected 'Bearer <token>'"}), 401
        
        # Extract the token from the header
        token = auth_header.split(' ')[1]
        
        # Now validate the token, you can add your custom token validation logic here
        # For simplicity, we will assume the token is valid if it's present
        if not token:  # You can add further validation logic here
            return jsonify({"error": "Invalid or missing token"}), 401


        # Call the create_tpl method with the provided 'data'
        # issue, error = GsmbOfficerService.create_tpl(data)
        detail, error = GsmbOfficerService.user_detail(user_id, auth_header)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"user_detail": detail})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# Put route for /update-ML
@gsmb_officer_bp.route('/add-license', methods=['POST'])
@check_token
@role_required(['GSMBOfficer'])
def add_new_license():
    try:
        #Get the token from the request header
        token =request.headers.get('Authorization')

        if not token:
            return jsonify({"error":"Authorization token is missing"}), 400

        # Get the payload from the request body (expected to be a JSON)
        payload = request.json 
        print(payload) 

        #validate the payload, ensure required data is present 
        if not payload or 'issue' not in payload:
            return jsonify({"error" : "Missing required data in the request"}), 400
        
        # pass the token and payload to the service method
        new_license, error =GsmbOfficerService.add_new_license(token, payload)

        if error:
            return jsonify({"error": error}), 500
        
        return jsonify({"success": True, "data": new_license}),201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

           # Fetch a single license by ID
@gsmb_officer_bp.route('/get-license/<int:licenseId>', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_license_details(licenseId):
    try:
        #Get the token from the request header
        token =request.headers.get('Authorization')

        if not token:
            return jsonify({"error":"Authorization token is missing"}), 400

        # pass the token and payload to the service method
        license_details, error =GsmbOfficerService.get_license_details(token,licenseId )

        if error:
            return jsonify({"error": error}), 500
        
        return jsonify({"success": True, "data": license_details}),201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500    


           # Update a license by ID
@gsmb_officer_bp.route('/update-license/<int:licenseId>', methods=['PUT'])
@check_token
@role_required(['GSMBOfficer'])
def update_license(licenseId):
    try:
        #Get the token from the request header
        token =request.headers.get('Authorization')

        if not token:
            return jsonify({"error":"Authorization token is missing"}), 400

        # Get the payload from the request body (expected to be a JSON)
        payload = request.json 
       

        #validate the payload, ensure required data is present 
        if not payload or 'issue' not in payload:
            return jsonify({"error" : "Missing required data in the request"}), 400
        
        # pass the token and payload to the service method
        update_license, error =GsmbOfficerService.update_license(token, payload ,licenseId)

        if error:
            return jsonify({"error": error}), 500
        
        return jsonify({"success": True, "data": update_license}),201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# Get TPL History


@gsmb_officer_bp.route('/view-tpls', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def view_tpls():
    try:
        # Get the token from the request header
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        # Fetch tpl data from service
        issues, error = GsmbOfficerService.view_tpls(token)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"view_tpls": issues})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return server error message




@gsmb_officer_bp.route('/get-mlowners', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_mlowners():
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        mlowners_details, error = GsmbOfficerService.get_mlowners(token)

        if error:
            return jsonify({"error": error}), 500

        return jsonify(mlowners_details)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gsmb_officer_bp.route('/get-mlowners/individual', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_individual_mlowners():
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        all_mlowners, error = GsmbOfficerService.get_mlowners(token)

        if error:
            return jsonify({"error": error}), 500

        # Function to extract field value by name
        def get_field_value(custom_fields, field_name):
            for field in custom_fields:
                if field["name"] == field_name:
                    return field["value"]
            return ""

        # Filter only individuals and format response
        individual_mlowners = []
        for owner in all_mlowners:
            if any(field["id"] == 41 and field["value"] for field in owner.get("custom_fields", [])):  # Check if NIC exists
                formatted_owner = {
                    "login": owner.get("login", ""),
                    "first_name": owner.get("firstname", "").strip(),
                    "last_name": owner.get("lastname", "").strip(),
                    "email": owner.get("mail", ""),
                    "national_identity_card": get_field_value(owner.get("custom_fields", []), "National Identity Card"),
                    "address": get_field_value(owner.get("custom_fields", []), "Address"),
                    "nationality": get_field_value(owner.get("custom_fields", []), "Nationality"),
                    "mobile_number": get_field_value(owner.get("custom_fields", []), "Mobile Number"),
                    "employment_name_of_employer": get_field_value(owner.get("custom_fields", []), "Employment ,Name of employer"),
                    "place_of_business": get_field_value(owner.get("custom_fields", []), "Place of Business"),
                    "residence": get_field_value(owner.get("custom_fields", []), "Residence"),
                }
                individual_mlowners.append(formatted_owner)

        return jsonify({"success": True, "data": individual_mlowners}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@gsmb_officer_bp.route('/get-mlowners/company', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_company_mlowners():
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        all_mlowners, error = GsmbOfficerService.get_mlowners(token)

        if error:
            return jsonify({"error": error}), 500

        # Function to extract field value by name
        def get_field_value(custom_fields, field_name):
            for field in custom_fields:
                if field["name"] == field_name:
                    return field["value"]
            return ""

        # Filter only company owners and format response
        company_mlowners = []
        for owner in all_mlowners:
            if any(field["id"] in [47, 49] and field["value"] for field in owner.get("custom_fields", [])):  
                formatted_owner = {
                    "login": owner.get("login", ""),
                    "first_name": owner.get("firstname", "").strip(),
                    "last_name": owner.get("lastname", "").strip(),
                    "country_of_incorporation": get_field_value(owner.get("custom_fields", []), "Country of Incorporation"),
                    "head_office": get_field_value(owner.get("custom_fields", []), "Head Office"),
                    "address_of_registered_company": get_field_value(owner.get("custom_fields", []), "Address of Registered Company"),
                    "capitalization": get_field_value(owner.get("custom_fields", []), "Capitalization"),
                    "articles_of_association": get_field_value(owner.get("custom_fields", []), "Articles of Association"),
                    "annual_reports": get_field_value(owner.get("custom_fields", []), "Annual Reports"),
                    "mobile_number": get_field_value(owner.get("custom_fields", []), "Mobile Number"),
                }
                company_mlowners.append(formatted_owner)

        return jsonify({"success": True, "data": company_mlowners}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@gsmb_officer_bp.route('/get-tpls', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_tpls():
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        # Fetch TPLs from the service
        tpls, error = GsmbOfficerService.get_tpls(token)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": tpls}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@gsmb_officer_bp.route('/get-mining-licenses', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_mining_licenses():
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        # Fetch Mining Licenses from the service
        mining_licenses, error = GsmbOfficerService.get_mining_licenses(token)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": mining_licenses}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@gsmb_officer_bp.route('/get-mining-license/<int:issue_id>', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_mining_license_by_id(issue_id):
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        # Fetch issue details
        mining_license, error = GsmbOfficerService.get_mining_license_by_id(token, issue_id)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": mining_license}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gsmb_officer_bp.route('/get-mining-license-requests', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_mining_license_requests():
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        mining_licenses, error = GsmbOfficerService.get_mining_license_requests(token)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": mining_licenses}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gsmb_officer_bp.route('/get-complaints', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_complaints():
    token = request.headers.get('Authorization')
    complaints, error = GsmbOfficerService.get_complaints(token)
    if error:
        return {"success": False, "message": error}
    return {"success": True, "data": complaints}




@gsmb_officer_bp.route('/get-mining-license-counts', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_mining_license_counts():
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        # Fetch mining license counts
        license_counts, error = GsmbOfficerService.get_mining_license_counts(token)
        
        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": license_counts}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@gsmb_officer_bp.route('/upload-mining-license', methods=['POST'])
@check_token
@role_required(['GSMBOfficer'])
def upload_mining_license():
    try:
        token = request.headers.get('Authorization')
        ml_owner_id = request.form.get('assignee_id')
        user_mobile = UserUtils.get_user_phone(ml_owner_id)

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        # Get form fields
        data = {
            "subject": request.form.get('subject'),
            "status_id": request.form.get('status_id'),
            "start_date": request.form.get('start_date'),
            "due_date": request.form.get('due_date'),
            "administrative_district": request.form.get('administrative_district'),
            "divisional_secretary_division": request.form.get('divisional_secretary_division'),
            "grama_niladhari_division": request.form.get('grama_niladhari_division'),
            "village_name": request.form.get('village_name'),
            "land_name": request.form.get('land_name'),
            "exploration_licence_no": request.form.get('exploration_licence_no'),
            #"author": request.form.get('author'),
            "mobile_number": request.form.get('mobile_number'),
            "land_owner_name": request.form.get('land_owner_name'),
            "royalty": request.form.get('royalty'),
            "capacity": request.form.get('capacity'),
            "used": request.form.get('used'),
            "remaining": request.form.get('remaining'),
            "google_location": request.form.get('google_location'),
            "assignee_id": request.form.get('assignee_id'),
            "mining_license_number": request.form.get('mining_license_number'),
            "month_capacity": request.form.get('month_capacity'),
            "mobile_number":user_mobile
        }

        # Get optional file uploads
        detailed_plan_file = request.files.get('detailed_mine_restoration_plan')
        economic_report_file = request.files.get('economic_viability_report')
        boundary_survey_file = request.files.get('deed_and_survey_plan')
        #license_fee_receipt_file = request.files.get('license_fee_receipt')
        payment_receipt_file = request.files.get('payment_receipt')
        license_boundary_survey_file = request.files.get('license_boundary_survey')


        # Upload files to Redmine or your storage method
        file_fields = {
            "detailed_mine_restoration_plan": detailed_plan_file,
            "economic_viability_report": economic_report_file,
            "license_boundary_survey": license_boundary_survey_file,
            "deed_and_survey_plan": boundary_survey_file,
            # "license_fee_receipt": license_fee_receipt_file,
            "payment_receipt": payment_receipt_file
        }
                 
        for field_name, file in file_fields.items():
            if file:
                file_id_or_url = GsmbOfficerService.upload_file_to_redmine(file)
                data[field_name] = file_id_or_url

        # Submit to service layer
        success, error = GsmbOfficerService.upload_mining_license(token, data)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "message": "Mining license uploaded successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@gsmb_officer_bp.route('/approve-physical-document', methods=['POST'])
@check_token
@role_required(['GSMBOfficer'])
def upload_payment_receipt():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        # Extract form-data
        
        payment_receipt = request.files.get('payment_receipt')

        
        payment_receipt_id = GsmbOfficerService.upload_file_to_redmine(payment_receipt)
        
        data = {
            "comments":request.form.get('comments'),
            "mining_request_id":request.form.get('mining_request_id'),
            "payment_receipt_id":payment_receipt_id
        }

        result, error = GsmbOfficerService.upload_payment_receipt(
            token,
            data
        )

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "message": "Payment receipt uploaded successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gsmb_officer_bp.route('/reject-physical-document', methods=['POST'])
@check_token
@role_required(['GSMBOfficer'])
def reject_physical_document():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        mining_request_id = request.form.get('mining_request_id')

        data = {
            "mining_request_id": mining_request_id
        }

        result, error = GsmbOfficerService.reject_mining_request(token, data)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "message": "Mining request rejected successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gsmb_officer_bp.route('/get-mlownersWithNic', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_mlownersWithNic():
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        mlowners_details, error = GsmbOfficerService.get_mlownersDetails(token)

        if error:
            return jsonify({"error": error}), 500

        return jsonify(mlowners_details)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gsmb_officer_bp.route('/get-appointments', methods=['GET'])
@check_token
@role_required(['GSMBOfficer'])
def get_appointments():
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        # Fetch appointments from the service
        appointments, error = GsmbOfficerService.get_appointments(token)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": appointments}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@gsmb_officer_bp.route('/create-appointment', methods=['POST'])
@check_token
@role_required(['GSMBOfficer'])
def create_appointment():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        # Get parameters from request body (JSON)
        data = request.get_json()
        
        assigned_to_id = data.get('assigned_to_id')
        physical_meeting_location = data.get('physical_meeting_location')
        start_date = data.get('start_date')
        description = data.get('description')
        mining_request_id = data.get("mining_request_id")

        # Validate required fields
        if not all([assigned_to_id, physical_meeting_location, start_date, description, mining_request_id]):
            return jsonify({"error": "Missing required parameters"}), 400

        result, error = GsmbOfficerService.create_appointment(
            token, 
            assigned_to_id, 
            physical_meeting_location, 
            start_date, 
            description,
            mining_request_id
        )

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "appointment_id": result}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500  

#Awaiting ME Scheduling (status id = 26)         
#Hold (status id = 39)
#Valid (status id = 7)
#Rejected(status id = 6)
@gsmb_officer_bp.route('/approve-mining-license', methods=['POST'])
@check_token
@role_required(['GSMBOfficer'])
def approve_license():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        data = request.get_json()
        issue_id = data.get('issue_id')
        # Use default value 7 if not provided
        new_status_id = data.get('new_status_id', 7)

        if not issue_id:
            return jsonify({"error": "Missing required parameter: issue_id"}), 400

        result = GsmbOfficerService.approve_mining_license(
            token=token,
            issue_id=issue_id,
            new_status_id=new_status_id
        )

        # Handle response
        if not result.get('success'):
            return jsonify({"error": result.get('message', 'Approval failed')}), 500

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@gsmb_officer_bp.route('/update-issue-status', methods=['POST'])
@check_token
@role_required(['GSMBOfficer'])
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

        result, error = GsmbOfficerService.change_issue_status(
            token,
            issue_id,
            new_status_id
        )

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@gsmb_officer_bp.route('/complaint/<int:issue_id>/resolve', methods=['PUT'])
@check_token
@role_required(['GSMBOfficer'])
def mark_complaint_resolved(issue_id):
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        result, error = GsmbOfficerService.mark_complaint_resolved(token, issue_id)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "message": "Complaint marked as resolved"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500