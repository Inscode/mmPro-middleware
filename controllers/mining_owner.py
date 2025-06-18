import os
from flask import Blueprint, jsonify, request
from middleware.auth_middleware import role_required,check_token
from services.auth_service import AuthService
from services.mining_owner_service import MLOwnerService
from utils.jwt_utils import JWTUtils
from utils.user_utils import UserUtils
from hashlib import md5
import time
import requests


# Define the Blueprint for mining_owner
mining_owner_bp = Blueprint('mining_owner', __name__)

# GET route for /mining-licenses (already exists)(slt redmine server done)
@mining_owner_bp.route('/mining-licenses', methods=['GET'])
@check_token
@role_required(['MLOwner'])
def get_mining_licenses():
    try:
        # Extract token from the request headers
        token = request.headers.get("Authorization")
        
        if not token:
            return {"error": "Authorization token is missing"}, 400
        
        # Call the mining_licenses method with the token
        issues, error = MLOwnerService.mining_licenses(token)
        
        if error:
            return {"error": error}, 500
        
        return {"issues": issues}, 200
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}, 500

@mining_owner_bp.route('/create-tpl', methods=['POST'])
@check_token
@role_required(['MLOwner'])
def create_tpl():
    try:
        # Check if the Authorization token is present in the request
        token = request.headers.get('Authorization')

        # Get request data
        data = request.json

        # Call the service to create the TPL issue
        issue, error = MLOwnerService.create_tpl(data, token)

        if error:
            return jsonify({"error": error}), 400  # Return error message if something went wrong

        return jsonify(issue), 201  # Return created issue if successful

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return server error message
    
# View tpl route
# GET route for /view-tpls    http://127.0.0.1:5000/mining-owner/view-tpls?mining_license_number=LLL/100/100
@mining_owner_bp.route('/view-tpls', methods=['GET'])
@check_token
@role_required(['MLOwner'])
def view_tpl_by_license_number():
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

        # Get the mining_license_number from the query parameters
        mining_license_number = request.args.get('mining_license_number')

        # Fetch TPL data for the specific Mining License Number
        issues, error = MLOwnerService.view_tpls(token, mining_license_number)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"view_tpls": issues})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return server error message

        
#done
@mining_owner_bp.route('/mining-homeLicenses', methods=['GET'])
@check_token
@role_required(['MLOwner'])
def mining_home():
    try:
        # Check if the Authorization token is present in the request
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 401
        
        # If the token is valid, proceed with the mining_licenses logic
        issues, error = MLOwnerService.mining_homeLicenses(token) # Pass token here
        
        if error:
            return jsonify({"error": error}), 500

        return jsonify({"mining_home": issues})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@mining_owner_bp.route('/ml-detail', methods=['GET'])
@check_token
@role_required(['MLOwner'])
def ml_detail():
    try:
        # Extract the 'l_number' query parameter
        l_number = request.args.get('l_number')
        if not l_number:
            return jsonify({"error": "Missing 'l_number' query parameter"}), 400

        # Extract the Authorization token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization token is missing"}), 403
    
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Invalid token format. Expected 'Bearer <token>'"}), 403

        # Extract only the token value
        token = auth_header.split(' ')[1]

        # Call the service function with l_number and token
        issue, error = MLOwnerService.ml_detail(l_number, auth_header)

        if error:
            status_code = 404 if error == "License not found" else 500
            return jsonify({"error": error}), status_code

        return jsonify({"ml_detail": issue})

    except Exception as e:
        return jsonify({"error": str(e)}), 500




            # Put route for /update-ML


@mining_owner_bp.route('/user-detail/<int:user_id>', methods=['GET'])
@check_token
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
        # issue, error = MLOwnerService.create_tpl(data)
        detail, error = MLOwnerService.user_detail(user_id, auth_header)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"user_detail": detail})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@mining_owner_bp.route('/ml-request', methods=['POST'])
@check_token
@role_required(['MLOwner'])
def ml_request():
    try:
        token = request.headers.get('Authorization')
        response_data = JWTUtils.decode_jwt_and_get_user_id(token)
        user_mobile = UserUtils.get_user_phone(response_data["user_id"])

        data = request.form.to_dict()

        # Initialize custom_fields list
        custom_fields = []

        # Handle file uploads through AuthService
        detailed_mine_file = request.files.get('detailed_mine_plan') 
        economic_report_file = request.files.get('economic_viability_report')
        payment_receipt_file = request.files.get('payment_receipt')  #Deed and Survey Plan
        Deed_plan_file = request.files.get('Deed_plan')
        license_boundary_survey_file = request.files.get('license_boundary_survey')


        detailed_mine_plan_id = AuthService.upload_file_to_redmine(detailed_mine_file) if detailed_mine_file else None
        economic_viability_report_id = AuthService.upload_file_to_redmine(economic_report_file) if economic_report_file else None
        payment_receipt_id = AuthService.upload_file_to_redmine(payment_receipt_file) if payment_receipt_file else None
        Deed_plan_id = AuthService.upload_file_to_redmine(Deed_plan_file) if Deed_plan_file else None
        license_boundary_survey_id = AuthService.upload_file_to_redmine(license_boundary_survey_file) if license_boundary_survey_file else None

        # Add file references to custom fields
        if detailed_mine_plan_id:
            custom_fields.append({"id": 72, "value": detailed_mine_plan_id})
        if payment_receipt_id:
            custom_fields.append({"id": 80, "value": payment_receipt_id})
        if Deed_plan_id:
            custom_fields.append({"id": 90, "value": Deed_plan_id})
        if economic_viability_report_id:
            custom_fields.append({"id": 100, "value": economic_viability_report_id})    
        if license_boundary_survey_id:
            custom_fields.append({"id": 105, "value": license_boundary_survey_id})    
        # Update data with custom_fields
        data['custom_fields'] = custom_fields
        
        # Call the service
        issue, error = MLOwnerService.ml_request(data, token, user_mobile)
        
        if error:
            return jsonify({"error": error}), 400
        return jsonify(issue), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@mining_owner_bp.route('/get-mining-license-requests', methods=['GET'])
@check_token
@role_required(['MLOwner'])
def get_mining_license_requests():
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        mining_licenses, error = MLOwnerService.get_mining_license_requests(token)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": mining_licenses}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mining_owner_bp.route('/get-pending-license-details', methods=['GET'])
@check_token
@role_required(['MLOwner'])
def get_mining_license_summary():
    try:
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        mining_licenses, error = MLOwnerService.get_pending_mining_license_details(token)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": mining_licenses}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mining_owner_bp.route('/get-mining-license/<int:issue_id>', methods=['GET'])
@check_token
@role_required(['MLOwner'])
def get_mining_license_by_id(issue_id):
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        # Fetch issue details
        mining_license, error = MLOwnerService.get_mining_license_by_id(token, issue_id)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": mining_license}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mining_owner_bp.route('/get-mining-license-refined', methods=['GET'])
@check_token
@role_required(['MLOwner'])
def get_mining_license_refined():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 400

        summaries, error = MLOwnerService.get_mining_license_summary(token)
        if error:
            return jsonify({"error": error}), 500

        return jsonify({"success": True, "data": summaries}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @mining_owner_bp.route('/update-royalty', methods=['POST'])
# # @check_token
# # @role_required(['MLOwner'])
# def update_royalty_amount():
#     try:
#         data = request.json
#         token = request.headers.get('Authorization')

#         issue_id = data.get("issue_id")
#         royalty_amount = data.get("royalty_amount")

#         if not issue_id or royalty_amount is None:
#             return jsonify({"error": "Missing 'issue_id' or 'royalty_amount'"}), 400

#         success, error = MLOwnerService.update_royalty_field(token, issue_id, royalty_amount)

#         if error:
#             return jsonify({"error": error}), 500

#         return jsonify({"success": True, "message": "Royalty updated successfully"}), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@mining_owner_bp.route('/update-royalty', methods=['POST'])
def handle_payhere_ipn():
    try:
        # 1. Get PayHere IPN data (form-urlencoded)
        data = request.form

        # 2. Required fields
        required_fields = [
            'merchant_id', 'order_id', 'payhere_amount',
            'payhere_currency', 'status_code', 'md5sig'
        ]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # 3. Verify PayHere signature
        merchant_secret = os.getenv("MERCHANT_SECRET")
        hashed_secret = md5(merchant_secret.encode()).hexdigest().upper()
        base_string = (
            f"{data['merchant_id']}{data['order_id']}{data['payhere_amount']}"
            f"{data['payhere_currency']}{data['status_code']}{hashed_secret}"
        )
        calculated_sig = md5(base_string.encode()).hexdigest().upper()

        if calculated_sig != data['md5sig']:
            return jsonify({"error": "Invalid signature"}), 403

        # 4. Only process successful payments
        if data['status_code'] != "2":
            return jsonify({"message": f"Ignoring non-successful payment status: {data['status_code']}"}), 200

        # 5. Extract issue ID from custom_1
        issue_id = data.get('custom_1')
        if not issue_id:
            return jsonify({"error": "Missing issue_id in custom_1"}), 400

        # 6. Redmine credentials
        redmine_url = os.getenv("REDMINE_URL")
        api_key = os.getenv("REDMINE_ADMIN_API_KEY")
        if not redmine_url or not api_key:
            return jsonify({"error": "Server configuration error"}), 500

        issue_url = f"{redmine_url}/issues/{issue_id}.json"
        headers = {
            "X-Redmine-API-Key": api_key,
            "Content-Type": "application/json"
        }

        # 7. Fetch current issue
        response = requests.get(issue_url, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to fetch issue: {response.text}"}), 400

        current_royalty = 0
        for field in response.json().get('issue', {}).get('custom_fields', []):
            if field.get('id') == 18:  # Royalty field ID
                try:
                    # Convert to float first, then to int to handle strings with decimals
                    current_royalty = int(float(field.get('value', 0)))
                except (ValueError, TypeError):
                    current_royalty = 0
                break

        # 8. Add royalty (convert amount to integer)
        try:
            amount = int(round(float(data['payhere_amount'])))  # Convert to integer
        except ValueError:
            return jsonify({"error": "Invalid amount format"}), 400

        new_royalty = current_royalty + amount

        # 9. Update Redmine issue with integer value
        update_response = requests.put(
            issue_url,
            headers=headers,
            json={
                "issue": {
                    "custom_fields": [{
                        "id": 18,
                        "value": str(new_royalty)  # Store as string but without decimals
                    }]
                }
            }
        )

        if update_response.status_code != 204:
            return jsonify({"error": f"Failed to update Redmine: {update_response.text}"}), 400

        # 10. Success response
        print(f"✅ Royalty updated for issue {issue_id}. New amount: {new_royalty}")
        return jsonify({
            "success": True,
            "message": f"Royalty updated to LKR {new_royalty}",
            "issue_id": issue_id,
            "payment_id": data.get('payment_id')
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500
    
@mining_owner_bp.route('/create-payhere-session', methods=['POST'])
@check_token
@role_required(['MLOwner'])
def create_payhere_session():
    try:
        data = request.json
        issue_id = data.get('issue_id')
        amount = data.get('amount')
        license_number = data.get('license_number')

        if not issue_id or not amount:
            return jsonify({"error": "Missing issue_id or amount"}), 400

        try:
            amount_float = float(amount)
            if amount_float <= 0:
                return jsonify({"error": "Amount must be positive"}), 400
        except ValueError:
            return jsonify({"error": "Invalid amount format"}), 400

        merchant_id = os.getenv("MERCHANT_ID")  # PayHere sandbox merchant ID
        merchant_secret = os.getenv("MERCHANT_SECRET")  # Sandbox secret
        order_id = f"ROYALTY_{issue_id}_{int(time.time())}"

        # Generate correct PayHere hash
        def generate_payhere_hash():
            hashed_secret = md5(merchant_secret.encode()).hexdigest().upper()
            base_string = f"{merchant_id}{order_id}{amount_float:.2f}LKR{hashed_secret}"
            return md5(base_string.encode()).hexdigest().upper()

        payment_config = {
            "sandbox": True,  # Set to False in production
            "merchant_id": merchant_id,
            "return_url": "http://localhost:3000/payment-success",
            "cancel_url": "http://localhost:3000/payment-canceled",
            "notify_url": "https://slt.aasait.lk/mining-owner/update-royalty",
            "order_id": order_id,
            "items": f"Mining Royalty for license {license_number}",
            "amount": f"{amount_float:.2f}",
            "currency": "LKR",
            "custom_1": issue_id,
            "hash": generate_payhere_hash(),
            "first_name": "Mining",
            "last_name": "Operator",
            "email": "mining@example.com",
            "phone": "0771234567",
            "address": "No.1, Mine Street",
            "city": "Colombo",
            "country": "Sri Lanka"
        }

        return jsonify({"paymentConfig": payment_config})

    except Exception as e:
        return jsonify({"error": str(e)}), 500








# achintha baranch publish