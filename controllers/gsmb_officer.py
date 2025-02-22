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




            # Put route for /update-ML
@gsmb_officer_bp.route('/user-detail/<int:user_id>', methods=['GET'])
@role_required(['MLOwner'])
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