import pytest
from unittest.mock import patch

def test_validate_lorry_number_missing(client):
    response = client.get('/general-public/validate-lorry-number')
    assert response.status_code == 400
    assert response.get_json() == {"error": "Lorry number is required"}

@patch('services.general_public_service.GeneralPublicService.is_lorry_number_valid')
def test_validate_lorry_number_valid(mock_is_valid, client):
    mock_is_valid.return_value = (True, None)
    response = client.get('/general-public/validate-lorry-number?lorry_number=ABC123')
    assert response.status_code == 200
    assert response.get_json() == {"valid": True}

@patch('services.general_public_service.GeneralPublicService.is_lorry_number_valid')
def test_validate_lorry_number_not_found(mock_is_valid, client):
    mock_is_valid.return_value = (False, "No TPL with this lorry number")
    response = client.get('/general-public/validate-lorry-number?lorry_number=XYZ999')
    assert response.status_code == 200
    assert response.get_json() == {"valid": False}

@patch('services.general_public_service.GeneralPublicService.is_lorry_number_valid')
def test_validate_lorry_number_error(mock_is_valid, client):
    mock_is_valid.return_value = (False, "Database connection error")
    response = client.get('/general-public/validate-lorry-number?lorry_number=ERROR123')
    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal Server Error"}

@patch('services.general_public_service.GeneralPublicService.create_complaint')
def test_create_complaint_success(mock_create, client):
    mock_create.return_value = (True, 123)
    response = client.post('/general-public/create-complaint', json={'phone': '1234567890', 'vehicleNumber': 'ABC123'})
    assert response.status_code == 200
    assert response.get_json() == {'success': True, 'complaint_id': 123}

@patch('services.general_public_service.GeneralPublicService.create_complaint')
def test_create_complaint_failure(mock_create, client):
    mock_create.return_value = (False, "Failed to create complaint")
    response = client.post('/general-public/create-complaint', json={'phone': '1234567890', 'vehicleNumber': 'ABC123'})
    assert response.status_code == 500
    assert response.get_json() == {'success': False, 'error': 'Failed to create complaint'}

@patch('services.general_public_service.GeneralPublicService.send_verification_code')
def test_send_verification_success(mock_send, client):
    mock_send.return_value = (True, "Verification code sent")
    response = client.post('/general-public/send-verification', json={'phone': '1234567890'})
    assert response.status_code == 200
    assert response.get_json() == {'success': True, 'message': 'Verification code sent'}

def test_send_verification_missing_phone(client):
    response = client.post('/general-public/send-verification', json={})
    assert response.status_code == 400
    assert response.get_json() == {'success': False, 'error': 'Phone number is required'}

@patch('services.general_public_service.GeneralPublicService.send_verification_code')
def test_send_verification_failure(mock_send, client):
    mock_send.return_value = (False, "Invalid phone number")
    response = client.post('/general-public/send-verification', json={'phone': 'badphone'})
    assert response.status_code == 400
    assert response.get_json() == {'success': False, 'error': 'Invalid phone number'}

@patch('services.general_public_service.GeneralPublicService.verify_code')
def test_verify_code_success(mock_verify, client):
    mock_verify.return_value = (True, None)
    response = client.post('/general-public/verify-code', json={'phone': '1234567890', 'code': '123456'})
    assert response.status_code == 200
    assert response.get_json() == {'success': True}

def test_verify_code_missing_fields(client):
    response = client.post('/general-public/verify-code', json={'phone': '1234567890'})
    assert response.status_code == 400
    assert response.get_json() == {'success': False, 'error': 'Phone number and code are required'}

@patch('services.general_public_service.GeneralPublicService.verify_code')
def test_verify_code_failure(mock_verify, client):
    mock_verify.return_value = (False, 'Invalid code')
    response = client.post('/general-public/verify-code', json={'phone': '1234567890', 'code': 'wrongcode'})
    assert response.status_code == 401
    assert response.get_json() == {'success': False, 'error': 'Invalid code'}

@patch('utils.jwt_utils.JWTUtils.decode_jwt_and_decrypt_api_key')
@patch('jwt.decode')
def test_get_api_success(mock_jwt_decode, mock_decode, client):
    mock_jwt_decode.return_value = {'role': 'GeneralPublic'}
    mock_decode.return_value = {'api_key': '123abc', 'user': 'testuser'}

    headers = {'Authorization': 'Bearer validtoken'}
    response = client.get('/general-public/get-api', headers=headers)
    
    assert response.status_code == 200
    assert response.get_json() == {'api_key': '123abc', 'user': 'testuser'}

def test_get_api_missing_token(client):
    response = client.get('/general-public/get-api')
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Authorization token is missing'}

@patch('utils.jwt_utils.JWTUtils.decode_jwt_and_decrypt_api_key')
def test_get_api_invalid_token(mock_decode, client):
    mock_decode.return_value = {'message': 'Invalid token'}
    headers = {'Authorization': 'Bearer invalidtoken'}
    response = client.get('/general-public/get-api', headers=headers)
    assert response.status_code == 401
    assert response.get_json() == {'error': 'Invalid token'}
