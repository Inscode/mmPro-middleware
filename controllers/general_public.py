from flask import Blueprint, jsonify, request
from services.general_public_service import GeneralPublicService
from middleware.auth_middleware import role_required
from utils.jwt_utils import JWTUtils
from utils.constants import INTERNAL_SERVER_ERROR

general_public_bp = Blueprint('general_public', __name__)

@general_public_bp.route('/validate-lorry-number', methods=['GET'])
def validate_lorry_number():
    lorry_number = request.args.get("lorry_number")  

    if not lorry_number:
        return jsonify({"error": "Lorry number is required"}), 400

    tpl_license_exists, error = GeneralPublicService.is_lorry_number_valid(lorry_number)

    if error:
        if "No TPL with this lorry number" in error:
            return jsonify({"valid": False}), 200  # Return False if not found
        else:
            return jsonify({"error": INTERNAL_SERVER_ERROR}), 500  # Hide technical errors

    return jsonify({"valid": tpl_license_exists}), 200  # Return True if valid


@general_public_bp.route('/create-complaint', methods=['POST'])
def create_complaint():
    data = request.json
    success, result = GeneralPublicService.create_complaint(data['phone'], data['vehicleNumber'])

    if success:
        return jsonify({'success': True, 'complaint_id': result})
    else:
        return jsonify({'success': False, 'error': result}), 500
    

@general_public_bp.route('/send-verification', methods=['POST'])
def send_verification():
    data = request.json
    phone = data.get('phone')

    if not phone:
        return jsonify({'success': False, 'error': 'Phone number is required'}), 400


    success, result = GeneralPublicService.send_verification_code(phone)

    if success:
        return jsonify({'success': True, 'message': result})
    else:
        return jsonify({'success': False, 'error': result}), 400

@general_public_bp.route('/verify-code', methods=['POST'])
def verify_code(): 
    data = request.json
    phone = data.get('phone')
    code = data.get('code')

    if not phone or not code:
        return jsonify({'success': False, 'error': 'Phone number and code are required'}), 400

    success, result = GeneralPublicService.verify_code(phone, code)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': result}), 401
    

@general_public_bp.route('/get-api', methods=['GET'])
@role_required(['GeneralPublic'])
def get_api():
    token = request.headers.get('Authorization')

    if not token or not token.startswith('Bearer '):
        return jsonify({'message': 'Authorization token is missing or malformed'}), 400

    token = token[len('Bearer '):]

    api_key = JWTUtils.decode_jwt_and_decrypt_api_key(token)

    if 'message' in api_key:
        return jsonify({'error': api_key['message']}), 401 

    return jsonify(api_key)
