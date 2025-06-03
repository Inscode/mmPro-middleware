# tests/test_auth_service.py

import pytest
from unittest.mock import patch, Mock
from services.auth_service import AuthService
from unittest.mock import patch, MagicMock, ANY
import requests

def test_authenticate_user_success():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'user': {
            'id': 1,
            'firstname': 'Jane',
            'lastname': 'Doe',
            'api_key': 'mock_api_key',
            'memberships': [
                {
                    'project': {'name': 'MMPRO-GSMB'},
                    'roles': [{'name': 'Developer'}]
                }
            ]
        }
    }
    
    with patch('services.auth_service.requests.get', return_value=mock_response):
        user_data, role, api_key = AuthService.authenticate_user('testuser', 'testpass')
        
        assert user_data['id'] == 1
        assert role == 'Developer'
        assert api_key == 'mock_api_key'

def test_authenticate_user_invalid_credentials():
    mock_response = Mock()
    mock_response.status_code = 401
    with patch('services.auth_service.requests.get', return_value=mock_response):
        user_data, role, api_key = AuthService.authenticate_user('invaliduser', 'invalidpass')
        assert user_data is None
        assert role is None
        assert 'Invalid credentials' in api_key

def test_authenticate_user_no_role():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'user': {
            'id': 2,
            'firstname': 'NoRole',
            'lastname': 'User',
            'api_key': 'mock_api_key',
            'memberships': []
        }
    }
    
    with patch('services.auth_service.requests.get', return_value=mock_response):
        user_data, role, api_key = AuthService.authenticate_user('user', 'pass')
        assert user_data is None
        assert role is None
        assert 'User does not have a role' in api_key

def test_authenticate_google_token_success():
    mock_token = "valid_google_token"
    
    # Mock return value for Google's token verification
    mock_id_info = {
        'email': 'testuser@example.com'
    }
    
    # Mock Redmine user data
    mock_users_response = {
        'users': [
            {'id': 123, 'firstname': 'Test', 'lastname': 'User'}
        ]
    }
    
    # mock_user_details_response = {
    #     'user': {
    #         'api_key': 'mock_api_key'
    #     }
    # }
    
    mock_memberships_response = {
        'memberships': [
            {
                'user': {'id': 123},
                'roles': [{'name': 'Developer'}]
            }
        ]
    }
    
    with patch('services.auth_service.id_token.verify_oauth2_token', return_value=mock_id_info) as mock_verify:
        with patch('services.auth_service.requests.get') as mock_get:
            # Mock sequence of requests.get calls:
            # 1. users.json call
            # 2. user details call
            # 3. memberships call
            
            mock_get.side_effect = [
                MagicMock(status_code=200, json=lambda: mock_users_response),
                # MagicMock(status_code=200, json=lambda: mock_user_details_response),
                MagicMock(status_code=200, json=lambda: mock_memberships_response)
            ]
            
            result = AuthService.authenticate_google_token(mock_token)
            
            # Expected returned tuple: user_id, user_data, gsm_project_role, api_key
            user_id, user_data, user_role  = result
            
            assert user_id == 123
            assert user_data == {'id': 123, 'firstname': 'Test', 'lastname': 'User'}
            assert user_role == 'Developer'

            
            mock_verify.assert_called_once_with(mock_token, ANY, ANY)
            assert mock_get.call_count == 2


def test_authenticate_google_token_missing_email():
    with patch('services.auth_service.id_token.verify_oauth2_token', return_value={}):
        result = AuthService.authenticate_google_token('some_token')
        assert result == (None, "Email not found in Google token")


def test_authenticate_google_token_user_not_found():
    with patch('services.auth_service.id_token.verify_oauth2_token', return_value={'email': 'test@example.com'}):
        with patch('services.auth_service.requests.get') as mock_get:
            # Simulate user not found (empty users list)
            mock_get.return_value = MagicMock(status_code=200, json=lambda: {'users': []})
            
            result = AuthService.authenticate_google_token('some_token')
            assert result == (None, "User not found in Redmine")



def test_authenticate_google_token_role_not_found():
    with patch('services.auth_service.id_token.verify_oauth2_token', return_value={'email': 'test@example.com'}):
        with patch('services.auth_service.requests.get') as mock_get:
            mock_get.side_effect = [
                MagicMock(status_code=200, json=lambda: {'users': [{'id': 123}]}),
                MagicMock(status_code=200, json=lambda: {'user': {'api_key': 'key'}}),
                MagicMock(status_code=200, json=lambda: {'memberships': []})  # no memberships found
            ]
            result = AuthService.authenticate_google_token('some_token')
            assert result == (None, "User role not found in Redmine")


def test_authenticate_google_token_invalid_token():
    with patch('services.auth_service.id_token.verify_oauth2_token', side_effect=ValueError("Invalid token")):
        result = AuthService.authenticate_google_token('invalid_token')
        assert result[0] is None
        assert "Invalid Google token" in result[1]


def test_authenticate_google_token_generic_exception():
    with patch('services.auth_service.id_token.verify_oauth2_token', side_effect=Exception("Some error")):
        result = AuthService.authenticate_google_token('token')
        assert result[0] is None
        assert "Server error" in result[1]


def test_check_user_by_email_exists():
    """Test when user exists with given email"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'users': [
            {'id': 1, 'mail': 'test@example.com'},
            {'id': 2, 'mail': 'other@example.com'}
        ]
    }
    mock_response.raise_for_status.return_value = None

    with patch('services.auth_service.requests.get', return_value=mock_response) as mock_get:
        assert AuthService.check_user_by_email('test@example.com') is True
        mock_get.assert_called_once()


def test_check_user_by_email_not_exists():
    """Test when no user exists with given email"""
    mock_response = MagicMock()
    mock_response.json.return_value = {'users': []}
    mock_response.raise_for_status.return_value = None

    with patch('services.auth_service.requests.get', return_value=mock_response) as mock_get:
        assert AuthService.check_user_by_email('nonexistent@example.com') is False
        mock_get.assert_called_once()


def test_check_user_by_email_api_error():
    """Test when Redmine API returns an error"""
    with patch('services.auth_service.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        assert AuthService.check_user_by_email('test@example.com') is False
        mock_get.assert_called_once()

def test_initiate_password_reset_success():
    """Test successful password reset initiation"""
    with patch('services.auth_service.AuthService.check_user_by_email') as mock_check_user, \
         patch('services.auth_service.cache.set') as mock_cache_set, \
         patch('services.auth_service.AuthService.send_reset_email') as mock_send_email:
        
        mock_check_user.return_value = True
        
        result = AuthService.initiate_password_reset('test@example.com')
        
        assert result == {'message': 'Password reset initiated'}
        mock_check_user.assert_called_once_with('test@example.com')
        mock_cache_set.assert_called_once()
        mock_send_email.assert_called_once()

def test_initiate_password_reset_user_not_found():
    """Test when email doesn't exist in system"""
    with patch('services.auth_service.AuthService.check_user_by_email') as mock_check_user:
        mock_check_user.return_value = False
        
        result = AuthService.initiate_password_reset('nonexistent@example.com')
        
        assert result == {'error': 'If the email exists, a reset link will be sent'}
        mock_check_user.assert_called_once_with('nonexistent@example.com')

def test_initiate_password_reset_custom_redirect():
    """Test with custom redirect URL"""
    with patch('services.auth_service.AuthService.check_user_by_email') as mock_check_user, \
         patch('services.auth_service.cache.set'), \
         patch('services.auth_service.AuthService.send_reset_email') as mock_send_email:
        
        mock_check_user.return_value = True
        
        result = AuthService.initiate_password_reset('test@example.com', 'https://custom.domain/reset')
        
        assert result == {'message': 'Password reset initiated'}
        mock_send_email.assert_called_once()
        # Check the reset link contains the custom domain
        args, kwargs = mock_send_email.call_args
        assert args[1].startswith('https://custom.domain/reset?token=')

def test_reset_password_success():
    """Test successful password reset"""
    with patch('services.auth_service.cache.get') as mock_cache_get, \
         patch('services.auth_service.requests.get') as mock_get, \
         patch('services.auth_service.requests.put') as mock_put, \
         patch('services.auth_service.cache.delete') as mock_cache_del:
        
        # Mock cache lookup
        mock_cache_get.return_value = 'test@example.com'
        
        # Mock user lookup
        mock_user_response = MagicMock()
        mock_user_response.json.return_value = {'users': [{'id': 123}]}
        mock_user_response.raise_for_status.return_value = None
        mock_get.return_value = mock_user_response
        
        # Mock password update
        mock_put_response = MagicMock()
        mock_put_response.raise_for_status.return_value = None
        mock_put.return_value = mock_put_response
        
        result = AuthService.reset_password('valid_token', 'new_password123')
        
        assert result == {'success': True}
        mock_cache_get.assert_called_once_with('reset_token:valid_token')
        mock_get.assert_called_once()
        mock_put.assert_called_once()
        mock_cache_del.assert_called_once_with('reset_token:valid_token')

def test_reset_password_invalid_token():
    """Test with invalid/expired token"""
    with patch('services.auth_service.cache.get') as mock_cache_get:
        mock_cache_get.return_value = None
        
        result = AuthService.reset_password('invalid_token', 'new_password123')
        
        assert result == {'error': 'Invalid or expired token'}
        mock_cache_get.assert_called_once_with('reset_token:invalid_token')

def test_reset_password_user_not_found():
    """Test when user not found in Redmine"""
    with patch('services.auth_service.cache.get') as mock_cache_get, \
         patch('services.auth_service.requests.get') as mock_get:
        
        mock_cache_get.return_value = 'test@example.com'
        mock_get.return_value.json.return_value = {'users': []}
        mock_get.return_value.raise_for_status.return_value = None
        
        result = AuthService.reset_password('valid_token', 'new_password123')
        
        assert result == {'success': False, 'error': 'User not found in Redmine'}

def test_reset_password_update_failure():
    """Test when password update fails"""
    with patch('services.auth_service.cache.get') as mock_cache_get, \
         patch('services.auth_service.requests.get') as mock_get, \
         patch('services.auth_service.requests.put') as mock_put:
        
        mock_cache_get.return_value = 'test@example.com'
        mock_get.return_value.json.return_value = {'users': [{'id': 123}]}
        mock_get.return_value.raise_for_status.return_value = None
        mock_put.side_effect = requests.exceptions.RequestException("Update failed")
        
        result = AuthService.reset_password('valid_token', 'new_password123')
        
        assert result == {'success': False, 'error': 'Failed to update password in Redmine'}


def test_send_reset_email_success():
    """Test successful email sending"""
    with patch('services.auth_service.smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        AuthService.send_reset_email('test@example.com', 'http://reset.link')
        
        mock_smtp.assert_called_once_with('smtp.gmail.com', 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('insaf.ahmedh@gmail.com', 'ulge fzkp izhg idwf')
        mock_server.sendmail.assert_called_once()

def test_send_reset_email_failure():
    """Test email sending failure"""
    with patch('services.auth_service.smtplib.SMTP') as mock_smtp:
        mock_smtp.side_effect = Exception("SMTP Error")
        
        # This should not raise an exception
        AuthService.send_reset_email('test@example.com', 'http://reset.link')