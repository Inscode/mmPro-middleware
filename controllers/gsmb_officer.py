# from flask_cors import CORS
from flask import Blueprint, jsonify, request
from middleware.auth_middleware import role_required
from services.gsmb_officer_service import GsmbOfficerService


# Define the Blueprint for gsmb_officer
gsmb_officer_bp = Blueprint('gsmb_officer', __name__)




@gsmb_officer_bp.route('/gsmb-issue', methods=['GET'])
@role_required(['GSMBOfficer'])
def get_mining_licenses():
    # Get the token from the request header
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({"error": "Authorization token is missing"}), 400

    # Pass the token to the service method
    issues, error = GsmbOfficerService.get_Issues_Data(token)
    
    if error:
        return jsonify({"error": error}), 500

    return jsonify({"mining_licenses": issues})



  # Allow requests from React Vite frontend

            
@gsmb_officer_bp.route('/user-detail/<int:user_id>', methods=['GET'])
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
@role_required(['GSMBOfficer'])
def update_license(licenseId):
    try:
        #Get the token from the request header
        token =request.headers.get('Authorization')

        if not token:
            return jsonify({"error":"Authorization token is missing"}), 400

        # Get the payload from the request body (expected to be a JSON)
        payload = request.json 
        # print(payload) 

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
        









           # Register  ML Owner
@gsmb_officer_bp.route('/add-mlowner', methods=['POST'])
@role_required(['GSMBOfficer'])
def add_new_mlowner():
    try:
        #Get the token from the request header
        token =request.headers.get('Authorization')

        if not token:
            return jsonify({"error":"Authorization token is missing"}), 400

        # Get the userData from the request body (expected to be a JSON)
        userData = request.json 
        print(userData) 

        #validate the userData, ensure required data is present 
        if not userData or 'user' not in userData:
            return jsonify({"error" : "Missing required data in the request"}), 400
        
        # pass the token and userData to the service method
        new_owner, error =GsmbOfficerService.add_new_mlowner(token, userData)

        if error:
            return jsonify({"error": error}), 500
        
        # After the user is created, assign them to a project
        project_id = 31  # Define the project ID here (GSMB project, for example)
        role_id = 10  # Define the role ID here (ML Owner role, for example)
        assignment_response, assignment_error = GsmbOfficerService.assign_user_to_project(new_owner['id'], project_id, role_id, token)

        if assignment_error:
            return jsonify({"error": assignment_error}), 500

        return jsonify({"success": True, "data": new_owner}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    

# Get TPL History


@gsmb_officer_bp.route('/view-tpls', methods=['GET'])
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













           # Get MLowners
@gsmb_officer_bp.route('/get-mlowners', methods=['GET'])
@role_required(['GSMBOfficer'])
def get_mlowners():
    try:
        # Get the token from the request header
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        # pass the token and payload to the service method
        mlowners_details, error = GsmbOfficerService.get_mlowners(token)

        if error:
            return jsonify({"error": error}), 500
        
        # For each ML Owner, get their associated licenses
        for owner in mlowners_details:
            user_id = owner['id']
            licenses, error = GsmbOfficerService.get_user_licenses(user_id, token)
            if error:
                return jsonify({"error": error}), 500
            owner['licenses'] = licenses

        return jsonify({"success": True, "data": mlowners_details}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500        
    
    

    
          