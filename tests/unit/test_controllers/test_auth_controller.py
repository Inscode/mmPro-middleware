# tests/unit/test_auth_controller.py

import pytest
from unittest.mock import patch
from flask import url_for
import jwt
from config import Config
import io

def test_login_success(client):
    mock_user_data = {
        'id': 1,
        'firstname': 'Jane',
        'lastname': 'Doe',
        'api_key': 'mock_api_key'
    }
    mock_user_role = 'Developer'
    mock_api_key = 'mock_api_key'
    mock_tokens = {
        'access_token': 'mock_access_token',
        'refresh_token': 'mock_refresh_token'
    }

    # Patch AuthService.authenticate_user and JWTUtils.create_jwt_token
    with patch('services.auth_service.AuthService.authenticate_user', return_value=(mock_user_data, mock_user_role, mock_api_key)):
        with patch('utils.jwt_utils.JWTUtils.create_jwt_token', return_value=mock_tokens):
            response = client.post('/auth/login', json={
                'username': 'testuser',
                'password': 'testpass'
            })
            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['token'] == 'mock_access_token'
            assert json_data['refresh_token'] == 'mock_refresh_token'
            assert json_data['role'] == mock_user_role
            assert json_data['username'] == 'Jane Doe'
            assert json_data['userId'] == 1

def test_login_missing_credentials(client):
    response = client.post('auth/login', json={
        'username': '',
        'password': ''
    })
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['message'] == 'Username and password are required'

def test_login_invalid_credentials(client):
    with patch('services.auth_service.AuthService.authenticate_user', return_value=(None, None, 'Invalid credentials')):
        response = client.post('auth/login', json={
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        assert response.status_code == 401
        json_data = response.get_json()
        assert json_data['message'] == 'Invalid Credentials'

def test_google_login_success(client):
    mock_user_id = 42
    mock_user_data = {
        'firstname': 'John',
        'lastname': 'Smith'
    }
    mock_user_role = 'Admin'
    mock_tokens = {
        'access_token': 'mock_access_token',
        'refresh_token': 'mock_refresh_token'
    }

    with patch('services.auth_service.AuthService.authenticate_google_token', return_value=(mock_user_id, mock_user_data, mock_user_role)):
        with patch('utils.jwt_utils.JWTUtils.create_jwt_token', return_value=mock_tokens):
            response = client.post('/auth/google-login', json={
                'token': 'valid_google_token'
            })
            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['token'] == 'mock_access_token'
            assert json_data['refresh_token'] == 'mock_refresh_token'
            assert json_data['role'] == mock_user_role
            assert json_data['username'] == ['John Smith'] 
            assert json_data['userId'] == 42


def test_google_login_missing_token(client):
    response = client.post('/auth/google-login', json={})
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'Google token is required'


def test_google_login_invalid_token(client):
    with patch('services.auth_service.AuthService.authenticate_google_token', return_value=(None, 'Invalid Google token')):
        response = client.post('/auth/google-login', json={
            'token': 'invalid_token'
        })
        assert response.status_code == 401
        json_data = response.get_json()
        assert json_data['error'] == 'Invalid Google token'


def test_mobile_google_login_success(client):
    mock_user_id = 99
    mock_user_data = {
        'firstname': 'Alice',
        'lastname': 'Wong'
    }
    mock_user_role = 'User'
    mock_token = {
        'access_token': 'mock_mobile_access_token',
        'refresh_token': 'mock_mobile_refresh_token'
    }

    with patch('services.auth_service.AuthService.authenticate_google_access_token',
               return_value=(mock_user_id, mock_user_data, mock_user_role)):
        with patch('utils.jwt_utils.JWTUtils.create_jwt_token',
                   return_value=mock_token):
            response = client.post('/auth/mobile-google-login', json={
                'token': 'valid_mobile_token'
            })

            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['token'] == mock_token
            assert json_data['role'] == mock_user_role
            assert json_data['username'] == 'Alice Wong'
            assert json_data['userId'] == 99

def test_refresh_token_success(client):
    mock_user_id = 123
    mock_user_role = 'Admin'
    mock_api_key = 'mock_api_key'
    mock_access_token = 'new_mock_access_token'

    # Create a valid refresh token manually for test
    payload = {
        "user_id": mock_user_id,
        "role": mock_user_role,
        "refresh": True
    }
    valid_refresh_token = jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

    with patch('utils.user_utils.UserUtils.get_user_api_key', return_value=mock_api_key):
        with patch('utils.jwt_utils.JWTUtils.create_access_token', return_value=mock_access_token):
            response = client.post('/auth/refresh-token', json={
                "refresh_token": valid_refresh_token
            })

            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['access_token'] == mock_access_token

def test_forgot_password_success(client):
    email = 'user@example.com'
    redirect_url = 'https://app.example.com/reset-password'

    with patch('services.auth_service.AuthService.initiate_password_reset', return_value={}):
        response = client.post('/auth/forgot-password', json={
            'email': email,
            'redirect_base_url': redirect_url
        })

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'If the email exists, a reset link will be sent'


def test_reset_password_success(client):
    token = 'valid-reset-token'
    new_password = 'newStrongPassword123'

    with patch('services.auth_service.AuthService.reset_password', return_value={'success': True}):
        response = client.post('/auth/reset-password', json={
            'token': token,
            'new_password': new_password
        })

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'Password updated successfully'


def test_register_police_officer_success(client):
    # Prepare dummy files (simulate file uploads)
    nic_front_file = (io.BytesIO(b"dummy nic front content"), 'nic_front.jpg')
    nic_back_file = (io.BytesIO(b"dummy nic back content"), 'nic_back.jpg')
    work_id_file = (io.BytesIO(b"dummy work id content"), 'work_id.jpg')

    form_data = {
        'login': 'john_doe',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'password': 'password123',
        'designation': 'Officer',
        'nic_number': '123456789V',
        'mobile_number': '0712345678',
        'user_Type': 'FullTime'
    }

    # Prepare a dictionary to simulate file uploads in Flask test client
    data = {
        **form_data,
        'nic_front': nic_front_file,
        'nic_back': nic_back_file,
        'work_id': work_id_file
    }

    with patch('services.auth_service.AuthService.upload_file_to_redmine', side_effect=['file_id_1', 'file_id_2', 'file_id_3']):
     
        with patch('services.auth_service.AuthService.register_police_officer', return_value=({'user': {'id': 123}}, None)):
      
            with patch('services.auth_service.AuthService.assign_role', return_value=(True, None)):
                response = client.post('/auth/register-police-officer', data=data, content_type='multipart/form-data')

                assert response.status_code == 201
                json_data = response.get_json()
                assert json_data['success'] is True
                assert json_data['role'] == "Police Officer"
                assert json_data['status'] == "inactive"
                assert 'data' in json_data
                assert json_data['data']['user']['id'] == 123

def test_register_gsmb_officer_success(client):
    # Prepare dummy files
    nic_front_file = (io.BytesIO(b"dummy nic front content"), 'nic_front.jpg')
    nic_back_file = (io.BytesIO(b"dummy nic back content"), 'nic_back.jpg')
    work_id_file = (io.BytesIO(b"dummy work id content"), 'work_id.jpg')

    # Prepare form data
    form_data = {
        'login': 'john_gsmb',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'password': 'password123',
        'designation': 'GSMB Officer',
        'nic_number': '987654321V',
        'mobile_number': '0712345678',
        'user_Type': 'FullTime'
    }

    # Combine form data and files
    data = {
        **form_data,
        'nic_front': nic_front_file,
        'nic_back': nic_back_file,
        'work_id': work_id_file
    }

    with patch('services.auth_service.AuthService.upload_file_to_redmine', side_effect=['file_id_1', 'file_id_2', 'file_id_3']):
        with patch('services.auth_service.AuthService.register_gsmb_officer', return_value=({'user': {'id': 123}}, None)):
            with patch('services.auth_service.AuthService.assign_role', return_value=(True, None)):
                response = client.post('/auth/register-gsmb-officer', data=data, content_type='multipart/form-data')

                assert response.status_code == 201
                json_data = response.get_json()
                assert json_data['success'] is True
                assert json_data['role'] == "GSMB Officer"
                assert json_data['status'] == "inactive"
                assert 'data' in json_data
                assert json_data['data']['user']['id'] == 123

def test_register_mining_engineer_success(client):
    nic_front_file = (io.BytesIO(b"dummy nic front content"), 'nic_front.jpg')
    nic_back_file = (io.BytesIO(b"dummy nic back content"), 'nic_back.jpg')
    work_id_file = (io.BytesIO(b"dummy work id content"), 'work_id.jpg')

    form_data = {
        'login': 'john_mining',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'password': 'password123',
        'designation': 'Mining Engineer',
        'nic_number': '112233445V',
        'mobile_number': '0771234567',
        'user_Type': 'FullTime'
    }

    data = {
        **form_data,
        'nic_front': nic_front_file,
        'nic_back': nic_back_file,
        'work_id': work_id_file
    }

    with patch('services.auth_service.AuthService.upload_file_to_redmine', side_effect=['file_id_1', 'file_id_2', 'file_id_3']):
        with patch('services.auth_service.AuthService.register_mining_engineer', return_value=({'user': {'id': 456}}, None)):
            with patch('services.auth_service.AuthService.assign_role', return_value=(True, None)):
                response = client.post('/auth/register-mining-engineer', data=data, content_type='multipart/form-data')

                assert response.status_code == 201
                json_data = response.get_json()
                assert json_data['success'] is True
                assert json_data['role'] == "GSMB Officer"  # Matches the controller's hardcoded role
                assert json_data['status'] == "inactive"
                assert 'data' in json_data
                assert json_data['data']['user']['id'] == 456


def test_register_individual_mlowner_success(client):
    request_data = {
        'login': 'john_mlowner',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'password': 'password123',
        'national_identity_card': '998877665V',
        'mobile_number': '0779876543'
    }

    with patch('services.auth_service.AuthService.register_mlowner', return_value=({'user': {'id': 789}}, None)):
        with patch('services.auth_service.AuthService.assign_role', return_value=(True, None)):
            response = client.post('/auth/register-mlowners/individual', json=request_data)

            assert response.status_code == 201
            json_data = response.get_json()
            assert json_data['success'] is True
            assert json_data['role'] == "mlOwner"
            assert json_data['status'] == "inactive"
            assert 'data' in json_data
            assert json_data['data']['user']['id'] == 789

def test_mobile_forgot_password_success(client):
    email = 'test@example.com'
    with patch('smtplib.SMTP') as mock_smtp:
        with patch('services.cache.cache.set') as mock_cache_set:
            response = client.post('/auth/mobile-forgot-password', json={'email': email})
            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['message'] == 'OTP sent to email if it exists'
            mock_cache_set.assert_called_once()
            mock_smtp.assert_called_once()

def test_mobile_verify_otp_success(client):
    email = 'test@example.com'
    otp = '123456'
    
    with patch('cache.get', return_value=otp) as mock_cache_get:
        with patch('cache.delete') as mock_cache_delete:
            with patch('cache.set') as mock_cache_set:
                response = client.post('/auth/mobile-verify-otp', json={'email': email, 'otp': otp})
                assert response.status_code == 200
                json_data = response.get_json()
                assert json_data['message'] == 'OTP verified'
                mock_cache_get.assert_called_once_with(f'otp:{email}')
                mock_cache_delete.assert_called_once_with(f'otp:{email}')
                mock_cache_set.assert_called_once_with(f'otp_verified:{email}', True, expire=600)

def test_mobile_verify_otp_success(client):
    email = 'test@example.com'
    otp = '123456'
    
    with patch('services.cache.cache.get', return_value=otp) as mock_cache_get:
        with patch('services.cache.cache.delete') as mock_cache_delete:
            with patch('services.cache.cache.set') as mock_cache_set:
                response = client.post('/auth/mobile-verify-otp', json={'email': email, 'otp': otp})
                assert response.status_code == 200
                json_data = response.get_json()
                assert json_data['message'] == 'OTP verified'
                mock_cache_get.assert_called_once_with(f'otp:{email}')
                mock_cache_delete.assert_called_once_with(f'otp:{email}')
                mock_cache_set.assert_called_once_with(f'otp_verified:{email}', True, expire=600)

def test_mobile_reset_password_success(client):
    email = 'test@example.com'
    new_password = 'newpassword123'
    
    with patch('services.cache.cache.get', return_value=True) as mock_cache_get:
        with patch('services.cache.cache.delete') as mock_cache_delete:
            with patch('services.auth_service.AuthService.reset_password_with_email', return_value={'success': True}) as mock_reset_password:
                response = client.post('/auth/mobile-reset-password', json={'email': email, 'new_password': new_password})
                assert response.status_code == 200
                json_data = response.get_json()
                assert json_data['message'] == 'Password updated successfully'
                mock_cache_get.assert_called_once_with(f'otp_verified:{email}')
                mock_reset_password.assert_called_once_with(email, new_password)
                mock_cache_delete.assert_called_once_with(f'otp_verified:{email}')


