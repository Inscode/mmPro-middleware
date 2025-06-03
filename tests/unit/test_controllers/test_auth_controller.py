# tests/unit/test_auth_controller.py

import pytest
from unittest.mock import patch
from flask import url_for


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

