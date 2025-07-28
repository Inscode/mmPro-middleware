from flask import Blueprint, jsonify, request
from middleware.auth_middleware import role_required,check_token
from services.police_officer_service import PoliceOfficerService


police_officer_bp = Blueprint('police_officer', __name__)

@police_officer_bp.route('/check-lorry-number', methods=['GET'])
@check_token
@role_required(['PoliceOfficer'])
def get_tpl_licenses():
    lorry_number = request.args.get("lorry_number")  

    if not lorry_number:
        return jsonify({"error": "Lorry number is required"}), 400

    token = request.headers.get("Authorization")
    issues, error = PoliceOfficerService.check_lorry_number(lorry_number,token)

    if error:
        if "No TPL with this lorry number" in error:
            return jsonify({"error": error}), 200   
        else:
            return jsonify({"error": error}), 500

    return jsonify({"license_details": issues})

@police_officer_bp.route('/create-complaint', methods=['POST'])
@check_token
@role_required(['PoliceOfficer'])
def create_complaint():
    data = request.json

    token = request.headers.get("Authorization")
    
    success, result = PoliceOfficerService.create_complaint(data['input'],data['user_id'],token)

    if success:
        return jsonify({'success': True, 'complaint_id': result})
    else:
        return jsonify({'success': False, 'error': result}), 500
    
