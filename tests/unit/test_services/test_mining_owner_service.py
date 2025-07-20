
from datetime import datetime, timedelta
import pytest
from unittest.mock import patch, MagicMock
import os
import requests
from services.mining_owner_service import MLOwnerService
from typing import Tuple, List, Dict, Optional
from datetime import datetime as real_datetime

class TestMiningLicenses:

    @patch.dict('os.environ', {'REDMINE_URL': 'http://gsmb.aasait.lk'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    def test_mining_licenses_success(self, mock_get, mock_decode, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}

        # Setup mock Redmine response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 1,
                    "assigned_to": {"id": 123, "name": "Test User"},
                    "status": {"name": "Active"},
                    "start_date": "2023-01-01",
                    "due_date": "2023-12-31",
                    "custom_fields": [
                        {"name": "Mining License Number", "value": "ML-001"},
                        {"name": "Divisional Secretary Division", "value": "Test Division"},
                        {"name": "Name of village ", "value": "Test Village"},
                        {"name": "Remaining", "value": "500"},
                        {"name": "Royalty", "value": "1000"}
                    ]
                }
            ],
            "total_count": 1
        }
        mock_get.return_value = mock_response

        result, error = MLOwnerService.mining_licenses("valid_token")
        assert error is None
        assert result[0]["License Number"] == "ML-001"

    @patch.dict('os.environ', {'REDMINE_URL': ''})  # Empty URL
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_mining_licenses_missing_redmine_url(self, mock_api_key):
        mock_api_key.return_value = 'test_api_key'  # Provide a dummy API key so the URL check happens
        result, error = MLOwnerService.mining_licenses("valid_token")
        assert result is None
        assert "Redmine URL or API Key is missing" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'http://gsmb.aasait.lk'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_mining_licenses_missing_api_key(self, mock_api_key):
        mock_api_key.return_value = None
        result, error = MLOwnerService.mining_licenses("valid_token")
        assert result is None
        assert "Redmine URL or API Key is missing" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'http://gsmb.aasait.lk'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    def test_mining_licenses_user_info_error(self, mock_decode, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_decode.return_value = {'success': False, 'message': 'Token error'}

        result, error = MLOwnerService.mining_licenses("valid_token")
        assert result is None
        assert error == "Token error"


    @patch.dict('os.environ', {'REDMINE_URL': 'http://gsmb.aasait.lk'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    def test_mining_licenses_api_failure(self, mock_get, mock_limit, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": True,
            "user_id": 123
        }
        mock_limit.return_value = 100
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.mining_licenses("valid_token")
        assert result is None
        assert "Failed to fetch issues: 500 - Server error" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'http://gsmb.aasait.lk'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    def test_mining_licenses_no_assigned_licenses(self, mock_get, mock_limit, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": True,
            "user_id": 123
        }
        mock_limit.return_value = 100

        # This simulates Redmine returning 0 issues assigned to the user
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": []  # No issues at all
        }
        mock_get.return_value = mock_response

        result, error = MLOwnerService.mining_licenses("valid_token")
        assert error is None
        assert len(result) == 0  # No licenses assigned


    @patch.dict('os.environ', {'REDMINE_URL': 'http://gsmb.aasait.lk'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    def test_mining_licenses_invalid_remaining_cubes(self, mock_get, mock_limit, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": True,
            "user_id": 123
        }
        mock_limit.return_value = 100
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 1,
                    "assigned_to": {"id": 123, "name": "Test User"},
                    "status": {"name": "Active"},
                    "custom_fields": [
                        {"name": "Remaining", "value": "invalid"},  # Non-numeric value
                        {"name": "Royalty", "value": "1000"}
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.mining_licenses("valid_token")
        assert error is None
        assert result[0]["Remaining Cubes"] == 0  # Should default to 0 for invalid values

    @patch.dict('os.environ', {'REDMINE_URL': 'http://gsmb.aasait.lk'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    def test_mining_licenses_exception_handling(self, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": True,
            "user_id": 123
        }

        
        with patch('services.mining_owner_service.requests.get', side_effect=Exception("Test exception")):
            result, error = MLOwnerService.mining_licenses("valid_token")
            assert result is None
            assert "Server error: Test exception" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'http://gsmb.aasait.lk'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    def test_mining_licenses_missing_fields(self, mock_get, mock_limit, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": True,
            "user_id": 123
        }
        mock_limit.return_value = 100
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 1,
                    "assigned_to": {"id": 123},  # Missing name
                    "status": {},  # Missing status name
                    "custom_fields": []  # Empty custom fields
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.mining_licenses("valid_token")
        assert error is None
        assert result[0]["Owner Name"] == "N/A"
        assert result[0]["Status"] == "Unknown"
        assert result[0]["License Number"] == "N/A"



class TestMiningHomeLicenses:

    # Common helper function to patch datetime correctly
    def _patch_datetime(self, mock_datetime, fixed_date):
        mock_datetime.now.return_value = fixed_date
        mock_datetime.strptime.side_effect = lambda date_string, fmt: datetime.strptime(date_string, fmt)

    @patch.dict(os.environ, {'REDMINE_URL': 'http://gsmb.aasait.lk'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    @patch('services.mining_owner_service.datetime')
    def test_mining_home_licenses_success(self, mock_datetime, mock_get, mock_limit, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": True,
            "user_id": 123
        }

        mock_limit.return_value = 100
        
        today = datetime(2023, 6, 1)
        self._patch_datetime(mock_datetime, today)

        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 1,
                    "assigned_to": {"id": 123, "name": "Test User"},
                    "start_date": "2023-01-01",
                    "due_date": future_date,
                    "custom_fields": [
                        {"name": "Mining License Number", "value": "ML-001"},
                        {"name": "Divisional Secretary Division", "value": "Test Division"},
                        {"name": "Name of village ", "value": "Test Village"},
                        {"name": "Remaining", "value": "500"},
                        {"name": "Royalty", "value": "1000"}
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        result, error = MLOwnerService.mining_homeLicenses("valid_token")
        assert error is None
        assert len(result) == 1
        assert result[0]["License Number"] == "ML-001"
        assert result[0]["Owner Name"] == "Test User"
        assert result[0]["Due Date"] == future_date
        assert result[0]["Remaining Cubes"] == 500
        assert result[0]["Location"] == "Test Village"

    @patch.dict(os.environ, {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    @patch('services.mining_owner_service.datetime')
    def test_mining_home_licenses_past_due_date(self, mock_datetime, mock_get, mock_limit, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": True,
            "user_id": 123
        }

        mock_limit.return_value = 100
        
        today = datetime(2023, 6, 1)
        self._patch_datetime(mock_datetime, today)

        past_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 1,
                    "assigned_to": {"id": 123, "name": "Test User"},
                    "due_date": past_date,
                    "custom_fields": []
                }
            ]
        }
        mock_get.return_value = mock_response

        result, error = MLOwnerService.mining_homeLicenses("valid_token")
        assert error is None
        assert len(result) == 0

    @patch.dict(os.environ, {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    @patch('services.mining_owner_service.datetime')
    def test_mining_home_licenses_invalid_remaining_cubes(self, mock_datetime, mock_get, mock_limit, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": True,
            "user_id": 123
        }
        mock_limit.return_value = 100
        
        today = datetime(2023, 6, 1)
        self._patch_datetime(mock_datetime, today)

        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 1,
                    "assigned_to": {"id": 123, "name": "Test User"},
                    "due_date": future_date,
                    "custom_fields": [
                        {"name": "Remaining", "value": "invalid"},
                        {"name": "Royalty", "value": "1000"}
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        result, error = MLOwnerService.mining_homeLicenses("valid_token")
        assert error is None
        assert result[0]["Remaining Cubes"] == 0

    @patch.dict(os.environ, {'REDMINE_URL': ''})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_mining_home_licenses_missing_redmine_url(self, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        result, error = MLOwnerService.mining_homeLicenses("valid_token")
        assert result is None
        assert "Redmine URL or API Key is missing" in error

    @patch.dict(os.environ, {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_mining_home_licenses_missing_api_key(self, mock_api_key):
        mock_api_key.return_value = None
        result, error = MLOwnerService.mining_homeLicenses("valid_token")
        assert result is None
        assert "Redmine URL or API Key is missing" in error

    @patch.dict(os.environ, {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    def test_mining_home_licenses_user_info_error(self, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": False,
            "message": "Token error"
        }
        result, error = MLOwnerService.mining_homeLicenses("valid_token")
        assert result is None
        assert error == "Token error"

    @patch.dict(os.environ, {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    def test_mining_home_licenses_api_failure(self, mock_get, mock_limit, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": True,
            "user_id": 123
        }
        mock_limit.return_value = 100

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_get.return_value = mock_response

        result, error = MLOwnerService.mining_homeLicenses("valid_token")
        assert result is None
        assert "Failed to fetch issues: 500 - Server error" in error

    @patch.dict(os.environ, {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    @patch('services.mining_owner_service.datetime')
    def test_mining_home_licenses_missing_fields(self, mock_datetime, mock_get, mock_limit, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": True,
            "user_id": 123
        }
        mock_limit.return_value = 100
        
        today = datetime(2023, 6, 1)
        self._patch_datetime(mock_datetime, today)

        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 1,
                    "assigned_to": {"id": 123},
                    "due_date": future_date,
                    "custom_fields": []
                }
            ]
        }
        mock_get.return_value = mock_response

        result, error = MLOwnerService.mining_homeLicenses("valid_token")
        assert error is None
        assert result[0]["Owner Name"] == "N/A"
        assert result[0]["License Number"] == "N/A"
        assert result[0]["Location"] == "N/A"

    @patch.dict(os.environ, {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    def test_mining_home_licenses_exception_handling(self, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {
            "success": True,
            "user_id": 123
        }

        with patch('services.mining_owner_service.requests.get', side_effect=Exception("Test exception")):
            result, error = MLOwnerService.mining_homeLicenses("valid_token")
            assert result is None
            assert "Server error: Test exception" in error

class TestCreateTPL:

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    @patch('services.mining_owner_service.requests.put')
    @patch('services.mining_owner_service.requests.post')
    @patch('services.mining_owner_service.MLOwnerService.calculate_time')
    def test_create_tpl_success(self, mock_calculate_time, mock_post, mock_put, mock_get, 
                              mock_decode_jwt, mock_api_key):
        # Setup mocks
        mock_api_key.return_value = 'test_api_key'
        mock_decode_jwt.return_value = {'user_id': 123}
        
        # Mock mining license fetch response
        mock_mining_response = MagicMock()
        mock_mining_response.status_code = 200
        mock_mining_response.json.return_value = {
            "issue": {
                "id": 456,
                "custom_fields": [
                    {"id": 1, "name": "Used", "value": "100"},
                    {"id": 2, "name": "Remaining", "value": "500"},
                    {"id": 3, "name": "Royalty", "value": "25000"}
                ]
            }
        }
        mock_get.return_value = mock_mining_response
        
        # Mock update response
        mock_update_response = MagicMock()
        mock_update_response.status_code = 204
        mock_put.return_value = mock_update_response
        
        # Mock TPL creation response
        mock_tpl_response = MagicMock()
        mock_tpl_response.status_code = 201
        mock_tpl_response.json.return_value = {"issue": {"id": 789}}
        mock_post.return_value = mock_tpl_response
        
        # Mock time calculation
        mock_calculate_time.return_value = {
            "success": True,
            "time_hours": 2
        }
        
        # Test data
        test_data = {
            "mining_license_number": "ML/456",
            "cubes": "50",
            "lorry_number": "ABC-123",
            "driver_contact": "0712345678",
            "route_01": "Location A",
            "route_02": "Location B",
            "route_03": "Location C",
            "destination": "Final Destination",
            "start_date": "2023-01-01"
        }
        
        # Call the method
        result, error = MLOwnerService.create_tpl(test_data, "valid_token")
        
        # Assertions
        assert error is None
        assert result == {"issue": {"id": 789}}
        
        # Verify API calls
        mock_get.assert_called_once_with(
            "https://test.redmine.com/issues/456.json",
            headers={
                "Content-Type": "application/json",
                "X-Redmine-API-Key": "test_api_key"
            }
        )
        
        mock_put.assert_called_once()
        mock_post.assert_called_once()

    @patch.dict('os.environ', {'REDMINE_URL': ''})
    def test_create_tpl_missing_redmine_url(self):
        result, error = MLOwnerService.create_tpl({}, "token")
        assert result is None
        assert error == "Redmine URL is not configured"

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_create_tpl_missing_api_key(self, mock_api_key):
        mock_api_key.return_value = None
        result, error = MLOwnerService.create_tpl({}, "token")
        assert result is None
        assert error == "Invalid or missing API key"

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_create_tpl_missing_license_number(self, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        result, error = MLOwnerService.create_tpl({}, "token")
        assert result is None
        assert error == "Mining license number is required"

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_create_tpl_invalid_license_format(self, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        result, error = MLOwnerService.create_tpl({"mining_license_number": "invalid"}, "token")
        assert result is None
        assert error == "Invalid mining license number format"

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.get')
    def test_create_tpl_failed_to_fetch_license(self, mock_get, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.create_tpl({"mining_license_number": "ML/456"}, "token")
        assert result is None
        assert "Failed to fetch mining license issue" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.get')
    def test_create_tpl_missing_required_fields(self, mock_get, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issue": {
                "custom_fields": []  # Missing required fields
            }
        }
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.create_tpl({"mining_license_number": "ML/456"}, "token")
        assert result is None
        assert "Required fields (Used, Remaining, or Royalty) not found" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.get')
    def test_create_tpl_insufficient_royalty(self, mock_get, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issue": {
                "custom_fields": [
                    {"id": 1, "name": "Used", "value": "100"},
                    {"id": 2, "name": "Remaining", "value": "500"},
                    {"id": 3, "name": "Royalty", "value": "100"}  # Low royalty
                ]
            }
        }
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.create_tpl({
            "mining_license_number": "ML/456",
            "cubes": "50"
        }, "token")
        assert result is None
        assert "Insufficient royalty balance" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.get')
    def test_create_tpl_insufficient_cubes(self, mock_get, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issue": {
                "custom_fields": [
                    {"id": 1, "name": "Used", "value": "100"},
                    {"id": 2, "name": "Remaining", "value": "10"},
                    {"id": 3, "name": "Royalty", "value": "25000"}
                ]
            }
        }
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.create_tpl({
            "mining_license_number": "ML/456",
            "cubes": "50"
        }, "token")
        assert result is None
        assert "Insufficient remaining cubes" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.get')
    @patch('services.mining_owner_service.requests.put')
    def test_create_tpl_failed_to_update_license(self, mock_put, mock_get, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        
        # Mock mining license fetch
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "issue": {
                "custom_fields": [
                    {"id": 1, "name": "Used", "value": "100"},
                    {"id": 2, "name": "Remaining", "value": "500"},
                    {"id": 3, "name": "Royalty", "value": "25000"}
                ]
            }
        }
        mock_get.return_value = mock_get_response
        
        # Mock failed update
        mock_put_response = MagicMock()
        mock_put_response.status_code = 500
        mock_put.return_value = mock_put_response
        
        result, error = MLOwnerService.create_tpl({
            "mining_license_number": "ML/456",
            "cubes": "50"
        }, "token")
        assert result is None
        assert "Failed to update mining license issue" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.get')
    @patch('services.mining_owner_service.requests.put')
    @patch('services.mining_owner_service.requests.post')
    def test_create_tpl_failed_to_create_tpl(self, mock_post, mock_put, mock_get, mock_api_key):
        mock_api_key.return_value = 'test_api_key'

    
    

        result, error = MLOwnerService.create_tpl({
            "mining_license_number": "ML/456",
            "cubes": "50"
        }, "token")
        assert result is None
        assert error is not None
        assert "Failed to fetch mining license issue" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_create_tpl_exception_handling(self, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_api_key.side_effect = Exception("Test exception")
        
        result, error = MLOwnerService.create_tpl({}, "token")
        assert result is None
        assert "Test exception" in error

class TestMLDetail:

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    def test_ml_detail_success(self, mock_get, mock_limit, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_limit.return_value = 100
        mock_user_info.return_value = {"success": True, "user_id": 123}

        # Mock first response (search issues)
        mock_search_response = MagicMock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = {
            "issues": [
                {
                    "id": 123,
                    "custom_fields": [
                        {"id": 101, "value": "ML-001"}
                    ]
                }
            ]
        }

        # Mock detail response
        mock_detail_response = MagicMock()
        mock_detail_response.status_code = 200
        mock_detail_response.json.return_value = {
            "issue": {
                "id": 123,
                "subject": "Mining License",
                "status": {"name": "Active"},
                "author": {"name": "Admin"},
                "assigned_to": {"name": "Owner"},
                "start_date": "2023-01-01",
                "due_date": "2023-12-31",
                "created_on": "2023-01-01T00:00:00Z",
                "updated_on": "2023-01-01T00:00:00Z",
                "custom_fields": [
                    {"name": "Royalty", "value": "1000"},
                    {"name": "Exploration Licence No", "value": "EXP-001"},
                    {"name": "Land Name(Licence Details)", "value": "Test Land"},
                    {"name": "Land owner name", "value": "Test Owner"},
                    {"name": "Name of village ", "value": "Test Village"},
                    {"name": "Grama Niladhari Division", "value": "Test GN"},
                    {"name": "Divisional Secretary Division", "value": "Test DS"},
                    {"name": "Administrative District", "value": "Test District"},
                    {"name": "Capacity", "value": "1000"},
                    {"name": "Used", "value": "500"},
                    {"name": "Remaining", "value": "500"},
                    {"name": "Mobile Number", "value": "0712345678"},
                    {"name": "Google location ", "value": "1.234,5.678"},
                    {"name": "Reason For Hold", "value": "None"},
                    {"name": "Economic Viability Report", "value": "Approved"},
                    {"name": "Detailed Mine Restoration Plan", "value": "Submitted"},
                    {"name": "Deed and Survey Plan", "value": "On file"},
                    {"name": "Payment Receipt", "value": "Paid"},
                    {"name": "License Boundary Survey", "value": "Completed"},
                    {"name": "Mining License Number", "value": "ML-001"}
                ]
            }
        }

        mock_get.side_effect = [mock_search_response, mock_detail_response]

        result, error = MLOwnerService.ml_detail("ML-001", "valid_token")

        assert error is None
        assert result["id"] == 123
        assert result["mining_license_number"] == "ML-001"
        assert result["royalty"] == "1000"
        assert result["remaining"] == "500"

        # Verify API calls with correct URLs and timeout
        mock_get.assert_any_call(
            "https://test.redmine.com/issues.json?project_id=1&tracker_id=4&status_id=7&assigned_to_id=123&limit=100&offset=0",
            headers={
                "X-Redmine-API-Key": "test_api_key",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        mock_get.assert_any_call(
            "https://test.redmine.com/issues/123.json",
            headers={
                "X-Redmine-API-Key": "test_api_key",
                "Content-Type": "application/json"
            },
            timeout=30
        )


    @patch.dict('os.environ', {'REDMINE_URL': ''})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_ml_detail_missing_redmine_url(self, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        result, error = MLOwnerService.ml_detail("ML-001", "valid_token")
        assert result is None
        assert "Redmine URL or API Key is missing" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_ml_detail_missing_api_key(self, mock_api_key):
        mock_api_key.return_value = None
        result, error = MLOwnerService.ml_detail("ML-001", "valid_token")
        assert result is None
        assert "Redmine URL or API Key is missing" in error


    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    def test_ml_detail_search_failure(self, mock_get, mock_limit, mock_decode_user_id, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_decode_user_id.return_value = {"success": True, "user_id": 123}  # Mock successful decode
        mock_limit.return_value = 100

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_get.return_value = mock_response

        result, error = MLOwnerService.ml_detail("ML-001", "valid_token")
        assert result is None
        assert "Failed to fetch issues" in error


    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    def test_ml_detail_detail_failure(self, mock_get, mock_limit, mock_decode_user_id, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_limit.return_value = 100

        # First call (search) succeeds
        mock_search_response = MagicMock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = {
            "issues": [
                {
                    "id": 123,
                    "custom_fields": [
                        {"id": 101, "value": "ML-001"}
                    ]
                }
            ]
        }

        # Second call (detail) fails
        mock_detail_response = MagicMock()
        mock_detail_response.status_code = 404
        mock_detail_response.text = "Not found"

        mock_get.side_effect = [mock_search_response, mock_detail_response]

        result, error = MLOwnerService.ml_detail("ML-001", "valid_token")
        assert result is None
        assert "Failed to fetch issue details" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    def test_ml_detail_not_found(self, mock_get, mock_limit, mock_decode_user_id, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_decode_user_id.return_value = {"success": True, "user_id": 123}  # mock success for decoding token
        mock_limit.return_value = 100

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"issues": []}
        mock_get.return_value = mock_response

        result, error = MLOwnerService.ml_detail("ML-001", "valid_token")
        assert result is None
        assert "No mining license found" in error


    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    def test_ml_detail_pagination(self, mock_get, mock_decode_jwt, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_decode_jwt.return_value = {"success": True, "user_id": 123}

        default_limit = 100  # matches your method's default_limit

        # Page 1: return exactly 100 issues with non-matching license
        mock_page1 = MagicMock()
        mock_page1.status_code = 200
        mock_page1.json.return_value = {
            "issues": [
                {
                    "id": i,
                    "custom_fields": [
                        {"id": 101, "name": "Mining License Number", "value": "OTHER"}
                    ]
                } for i in range(1, default_limit + 1)  # 100 dummy issues
            ]
        }

        # Page 2: one issue with matching license number "ML-001"
        mock_page2 = MagicMock()
        mock_page2.status_code = 200
        mock_page2.json.return_value = {
            "issues": [
                {
                    "id": 101,
                    "custom_fields": [
                        {"id": 101, "name": "Mining License Number", "value": "ML-001"}
                    ]
                }
            ]
        }

        # Detail fetch for issue id=101
        mock_detail = MagicMock()
        mock_detail.status_code = 200
        mock_detail.json.return_value = {
            "issue": {
                "id": 101,
                "subject": "Mining License",
                "status": {"name": "Active"},
                "author": {"name": "Admin"},
                "assigned_to": {"name": "Owner"},
                "start_date": "2023-01-01",
                "due_date": "2023-12-31",
                "created_on": "2023-01-01T00:00:00Z",
                "updated_on": "2023-01-01T00:00:00Z",
                "custom_fields": [
                    {"name": "Mining License Number", "value": "ML-001"},
                    {"name": "Royalty", "value": "1000"},
                ]
            }
        }

        # The sequence of requests.get calls:
        # 1) fetch page 1 (100 issues)
        # 2) fetch page 2 (matching issue)
        # 3) fetch detail for id=101
        mock_get.side_effect = [mock_page1, mock_page2, mock_detail]

        result, error = MLOwnerService.ml_detail("ML-001", "valid_token")

        assert error is None
        assert result is not None
        assert result.get("mining_license_number") == "ML-001"
        assert result.get("royalty") == "1000"




    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_ml_detail_exception_handling(self, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_api_key.side_effect = Exception("Test exception")
        
        result, error = MLOwnerService.ml_detail("ML-001", "valid_token")
        assert result is None
        assert "Server error: Test exception" in error

class TestUserDetail:

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.get')
    def test_user_detail_success(self, mock_get, mock_api_key):
        # Setup mocks
        mock_api_key.return_value = 'test_api_key'
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user": {
                "id": 123,
                "login": "testuser",
                "firstname": "Test",
                "lastname": "User",
                "mail": "test@example.com",
                "created_on": "2023-01-01T00:00:00Z",
                "last_login_on": "2023-06-01T00:00:00Z"
            }
        }
        mock_get.return_value = mock_response

        # Call the method
        result, error = MLOwnerService.user_detail(123, "valid_token")

        # Assertions
        assert error is None
        assert result["id"] == 123
        assert result["login"] == "testuser"
        assert result["firstname"] == "Test"
        
        # Verify API call
        mock_get.assert_called_once_with(
            "https://test.redmine.com/users/123.json",
            headers={
                "X-Redmine-API-Key": "test_api_key",
                "Content-Type": "application/json"
            }
        )

    @patch.dict('os.environ', {'REDMINE_URL': ''})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_user_detail_missing_redmine_url(self, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        result, error = MLOwnerService.user_detail(123, "valid_token")
        assert result is None
        assert "Redmine URL or API Key is missing" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_user_detail_missing_api_key(self, mock_api_key):
        mock_api_key.return_value = None
        result, error = MLOwnerService.user_detail(123, "valid_token")
        assert result is None
        assert "Redmine URL or API Key is missing" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.get')
    def test_user_detail_api_failure(self, mock_get, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "User not found"
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.user_detail(123, "valid_token")
        assert result is None
        assert "Failed to fetch issue: 404 - User not found" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.get')
    def test_user_detail_invalid_response(self, mock_get, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing user data
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.user_detail(123, "valid_token")
        assert result == {}
        assert error is None

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.get')
    def test_user_detail_partial_data(self, mock_get, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user": {
                "id": 123,
                "login": "testuser"
                # Missing other fields
            }
        }
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.user_detail(123, "valid_token")
        assert error is None
        assert result["id"] == 123
        assert result["login"] == "testuser"
        assert "firstname" not in result     

class TestViewTpls:

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    def test_view_tpls_success(self, mock_get, mock_limit, mock_user_info, mock_api_key):
        # Setup mocks
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {"success": True, "user_id": 123}
        mock_limit.return_value = 100
        
        # Create test data
        test_date = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 390,
                    "subject": "TPL 001",
                    "created_on": test_date,
                    "estimated_hours": "24",
                    "custom_fields": [
                        {"id": 53, "name": "Lorry Number", "value": "ABX1234"},
                        {"id": 54, "name": "Driver Contact", "value": "0771234567"},
                        {"id": 59, "name": "Mining issue id", "value": "ML-001"},
                        {"id": 68, "name": "Destination", "value": "Colombo"}
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Call method
        result, error = MLOwnerService.view_tpls("valid_token", "ML-001")
        
        # Assertions
        assert error is None
        assert len(result) == 1
        assert result[0]["tpl_id"] == 390
        assert result[0]["status"] == "Active"
        assert result[0]["lorry_number"] == "ABX1234"
        assert result[0]["driver_contact"] == "0771234567"

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    def test_view_tpls_expired_status(self, mock_get, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_api_key'
        mock_user_info.return_value = {"success": True, "user_id": 123}

        # Mock Redmine API response with one issue matching license number
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"issues": [...]}'
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 1,
                    "created_on": "2023-01-01T00:00:00Z",
                    "estimated_hours": 1000,
                    "subject": "Test TPL",
                    "custom_fields": [
                        {"id": 59, "name": "Mining License Number", "value": "some_license_number"},
                        {"id": 60, "name": "Lorry Number", "value": "LN123"},
                        {"id": 61, "name": "Driver Contact", "value": "0123456789"},
                        # other custom fields if needed
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        result, error = MLOwnerService.view_tpls("valid_token", "some_license_number")

        assert error is None
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["license_number"] == "some_license_number"
        assert result[0]["status"] in ("Active", "Expired")

    @patch.dict('os.environ', {'REDMINE_URL': ''})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_view_tpls_missing_redmine_url(self, mock_api_key):
        mock_api_key.return_value = 'test_key'
        result, error = MLOwnerService.view_tpls("valid_token", "ML-001")
        assert result is None
        assert "System configuration error" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_view_tpls_missing_api_key(self, mock_api_key):
        mock_api_key.return_value = None
        result, error = MLOwnerService.view_tpls("valid_token", "ML-001")
        assert result is None
        assert "System configuration error" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    def test_view_tpls_auth_error(self, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_key'
        mock_user_info.return_value = {"success": False, "message": "Invalid token"}
        result, error = MLOwnerService.view_tpls("valid_token", "ML-001")
        assert result is None
        assert error == "Invalid token"

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    def test_view_tpls_api_error(self, mock_get,mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_key'
        mock_user_info.return_value = {'success': True, 'user_id': 'user123'}

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.view_tpls("valid_token", "ML-001")

        assert result is None
        assert "Redmine API error" in error
        assert "500" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    def test_view_tpls_invalid_json(self, mock_get,mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_key'
        mock_user_info.return_value = {"success": True, "user_id": 'user123'}


        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.view_tpls("valid_token", "ML-001")

        assert result is None
        assert "Failed to parse response from Redmine" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_view_tpls_exception_handling(self, mock_api_key):
        mock_api_key.side_effect = Exception("Test exception")
        result, error = MLOwnerService.view_tpls("valid_token", "ML-001")
        assert result is None
        assert "Processing error: Test exception" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.LimitUtils.get_limit')
    @patch('services.mining_owner_service.requests.get')
    def test_view_tpls_skip_invalid_issues(self, mock_get, mock_limit, mock_user_info, mock_api_key):
        mock_api_key.return_value = 'test_key'
        mock_user_info.return_value = {"success": True, "user_id": 'user123'}
        mock_limit.return_value = 100

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {  # Valid TPL
                "id": 1,
                "subject": "Valid TPL",
                "project": {"id": 1},
                "tracker": {"id": 5},
                "created_on": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "estimated_hours": "24",
                "custom_fields": [
                    {"id": 59, "value": "ML-001", "name": "Mining License"},
                    {"id": 1, "value": "Lorry-1", "name": "Lorry Number"}
                ]
                },
                {  # Invalid TPL (missing required fields)
                "id": 2,
                "subject": "Invalid TPL",
                "project": {"id": 1},
                "tracker": {"id": 5},
                "custom_fields": [{"id": 59, "value": "ML-001"}]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.view_tpls("valid_token", "ML-001")
        assert error is None
        assert len(result) == 1
        assert result[0]["tpl_id"] == 1      


class TestMLRequest():

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.post')
    @patch('services.mining_owner_service.requests.put')
    def test_ml_request_success(self, mock_put, mock_post, mock_api_key):
        # Setup mocks
        mock_api_key.return_value = 'test_key'
        
        # Mock create issue response
        mock_create_response = MagicMock()
        mock_create_response.status_code = 201
        mock_create_response.json.return_value = {"issue": {"id": 123}}
        mock_post.return_value = mock_create_response
        
        # Mock update response
        mock_update_response = MagicMock()
        mock_update_response.status_code = 204
        mock_put.return_value = mock_update_response
        
        # Test data
        test_data = {
            "subject": "Test ML Request",
            "description": "Test description",
            "project_id": 1,
            "exploration_nb": "EXP-001",
            "land_name": "Test Land",
            "land_owner_name": "John Doe",
            "village_name": "Test Village",
            "grama_niladari": "GN Division",
            "divisional_secretary_division": "DS Division",
            "administrative_district": "Colombo",
            "google_location": "6.9271,79.8612"
        }
        
        # Call method
        result, error = MLOwnerService.ml_request(test_data, "valid_token", "0771234567")
        
        # Assertions
        assert error is None
        assert result["issue"]["id"] == 123
        assert result["issue"]["mining_license_number"] == "LLL/100/123"
        mock_post.assert_called_once()
        mock_put.assert_called_once()

    @patch.dict('os.environ', {'REDMINE_URL': ''})
    def test_ml_request_missing_redmine_url(self):
        result, error = MLOwnerService.ml_request({}, "token", "0771234567")
        assert result is None
        assert "Redmine URL is not configured" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_ml_request_missing_api_key(self, mock_api_key):
        mock_api_key.return_value = None
        result, error = MLOwnerService.ml_request({}, "token", "0771234567")
        assert result is None
        assert "Invalid or missing API key" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.post')
    def test_ml_request_create_failure(self, mock_post, mock_api_key):
        mock_api_key.return_value = 'test_key'
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_post.return_value = mock_response
        
        result, error = MLOwnerService.ml_request({}, "token", "0771234567")
        assert result is None
        assert "Failed to create issue" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.post')
    @patch('services.mining_owner_service.requests.put')
    def test_ml_request_update_failure(self, mock_put, mock_post, mock_api_key):
        # Setup create success
        mock_api_key.return_value = 'test_key'
        mock_create_response = MagicMock()
        mock_create_response.status_code = 201
        mock_create_response.json.return_value = {"issue": {"id": 123}}
        mock_post.return_value = mock_create_response
        
        # Setup update failure
        mock_update_response = MagicMock()
        mock_update_response.status_code = 400
        mock_update_response.text = "Update failed"
        mock_put.return_value = mock_update_response
        
        result, error = MLOwnerService.ml_request({}, "token", "0771234567")
        assert result is None
        assert "Failed to update Mining License Number" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.post')
    def test_ml_request_network_error(self, mock_post, mock_api_key):
        mock_api_key.return_value = 'test_key'
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        result, error = MLOwnerService.ml_request({}, "token", "0771234567")
        assert result is None
        assert "Request failed" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_ml_request_unexpected_error(self, mock_api_key):
        mock_api_key.side_effect = Exception("Unexpected error")
        result, error = MLOwnerService.ml_request({}, "token", "0771234567")
        assert result is None
        assert "Unexpected error" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.requests.post')
    def test_ml_request_missing_required_fields(self, mock_post, mock_api_key):
        mock_api_key.return_value = 'test_key'

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "issue": {
                "id": 123,
                "subject": "Minimal Request",
                "project": {"id": 1, "name": "Test Project"},
                "status": {"id": 8, "name": "New"},
                "mining_license_number": "LLL/100/123"
            }
        }
        mock_post.return_value = mock_response

        minimal_data = {
            "subject": "Minimal Request"
        }

        with patch('services.mining_owner_service.requests.put') as mock_put:
            mock_put.return_value.status_code = 204

            # Pass the required third arg `user_mobile`
            result, error = MLOwnerService.ml_request(minimal_data, "valid_token", "0123456789")

            assert error is None
            assert result["issue"]["id"] == 123
            assert result["issue"]["subject"] == "Minimal Request"
            assert result["issue"]["mining_license_number"] == "LLL/100/123"




class TestGetMiningLicenseRequests():

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    @patch('services.mining_owner_service.MLOwnerService.get_attachment_urls')
    @patch('services.mining_owner_service.MLOwnerService.get_custom_field_value')
    def test_successful_request(self, mock_custom_field, mock_attachments, mock_get, mock_decode, mock_api_key):
        # Setup mocks
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}
        
        # Mock main issues response
        mock_issues_response = MagicMock()
        mock_issues_response.status_code = 200
        mock_issues_response.json.return_value = {
            "issues": [{
                "id": 456,
                "subject": "Test Mining License",
                "status": {"name": "Pending"},
                "assigned_to": {"id": 123, "name": "Test User"},
                "created_on": "2023-01-01T00:00:00Z",
                "updated_on": "2023-01-02T00:00:00Z",
                "custom_fields": []
            }]
        }
        
        # Mock user details response
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "user": {
                "id": 123,
                "firstname": "Test",
                "lastname": "User",
                "mail": "test@example.com",
                "custom_fields": []
            }
        }
        
        # Configure mock side effects
        mock_get.side_effect = [mock_issues_response, mock_user_response]
        mock_attachments.return_value = {
            "Detailed Mine Restoration Plan": "https://attachment1.url",
            "Payment Receipt": "https://payment.url"
        }
        mock_custom_field.side_effect = lambda fields, name: f"Mock {name}"
        
        # Call method
        result, error = MLOwnerService.get_mining_license_requests("valid_token")
        
        # Assertions
        assert error is None
        assert len(result) == 1
        assert result[0]["id"] == 456
        assert result[0]["subject"] == "Test Mining License"
        assert result[0]["status"] == "Pending"
        assert result[0]["assigned_to_details"]["email"] == "test@example.com"
        assert "https://attachment1.url" in result[0]["detailed_mine_restoration_plan"]
        assert "Mock Exploration Licence No" in result[0]["exploration_licence_no"]

    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_invalid_token(self, mock_api_key):
        mock_api_key.return_value = None
        result, error = MLOwnerService.get_mining_license_requests("invalid_token")
        assert result is None
        assert "Invalid or missing API key" in error

    @patch.dict('os.environ', {'REDMINE_URL': ''})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    def test_missing_redmine_url(self,mock_decode, mock_api_key):
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}
 

        result, error = MLOwnerService.get_mining_license_requests("valid_token")

        assert result is None
        assert "REDMINE_URL' is not set" in error
        assert "Environment variable 'REDMINE_URL' is not set" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    def test_failed_user_extraction(self, mock_decode, mock_api_key):
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {}

        result, error = MLOwnerService.get_mining_license_requests("valid_token")

        assert result is None
        assert "user_id" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    def test_redmine_api_error(self, mock_get, mock_decode, mock_api_key):
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}

        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.get_mining_license_requests("valid_token")
        assert result is None
        assert "Failed to fetch ML issues" in error
        assert "500" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    def test_user_assignment_filter(self, mock_get, mock_decode, mock_api_key):
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}

        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {"id": 1, "assigned_to": {"id": 123}, "custom_fields": []},
                {"id": 2, "assigned_to": {"id": 456}, "custom_fields": []}
            ]
        }
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.get_mining_license_requests("valid_token")
        assert error is None
        assert len(result) == 1
        assert result[0]["id"] == 1

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    def test_user_details_failure(self, mock_get, mock_decode, mock_api_key):
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}

        
        # Mock issues response
        mock_issues_response = MagicMock()
        mock_issues_response.status_code = 200
        mock_issues_response.json.return_value = {
            "issues": [{
                "id": 789,
                "assigned_to": {"id": 123, "name": "Test User"},
                "custom_fields": []
            }]
        }
        
        # Mock failed user details response
        mock_user_response = MagicMock()
        mock_user_response.status_code = 404
        
        mock_get.side_effect = [mock_issues_response, mock_user_response]
        
        result, error = MLOwnerService.get_mining_license_requests("valid_token")
        assert error is None
        assert result[0]["assigned_to_details"] is None

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    def test_exception_handling(self, mock_get, mock_decode, mock_api_key):
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}

        mock_get.side_effect = Exception("Test exception")
        
        result, error = MLOwnerService.get_mining_license_requests("valid_token")
        assert result is None
        assert "Server error" in error   


class TestGetPendingMiningLicenseDetails():

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    @patch('services.mining_owner_service.MLOwnerService.get_custom_field_value')
    def test_successful_request(self, mock_custom_field, mock_get, mock_decode, mock_api_key):
        # Setup mocks
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}

        mock_custom_field.return_value = "ML-00123"
        
        # Mock Redmine API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [{
                "id": 456,
                "status": {"name": "Pending"},
                "assigned_to": {"id": 123, "name": "Test User"},
                "created_on": "2023-01-01T00:00:00Z",
                "updated_on": "2023-01-02T00:00:00Z",
                "custom_fields": []
            }]
        }
        mock_get.return_value = mock_response
        
        # Call method
        result, error = MLOwnerService.get_pending_mining_license_details("valid_token")
        
        # Assertions
        assert error is None
        assert len(result) == 1
        assert result[0]["mining_license_number"] == "ML-00123"
        assert result[0]["status"] == "Pending"
        assert result[0]["created_on"] == "2023-01-01T00:00:00Z"

    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    def test_invalid_token(self, mock_api_key):
        mock_api_key.return_value = None
        result, error = MLOwnerService.get_pending_mining_license_details("invalid_token")
        assert result is None
        assert "Invalid or missing API key" in error

    @patch.dict('os.environ', {'REDMINE_URL': ''})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    def test_missing_redmine_url(self, mock_decode, mock_api_key):
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}

        result, error = MLOwnerService.get_pending_mining_license_details("valid_token")
        assert result is None
        assert "Environment variable 'REDMINE_URL' is not set" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    def test_failed_user_extraction(self, mock_decode, mock_api_key):
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {}
        result, error = MLOwnerService.get_pending_mining_license_details("valid_token")
        assert result is None
        assert "Failed to extract user info" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    def test_redmine_api_error(self, mock_get, mock_decode, mock_api_key):
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}

        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.get_pending_mining_license_details("valid_token")
        assert result is None
        assert "Failed to fetch ML issues" in error
        assert "500" in error

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    @patch('services.mining_owner_service.MLOwnerService.get_custom_field_value')
    def test_user_assignment_filter(self, mock_custom_field, mock_get, mock_decode, mock_api_key):
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}

        mock_custom_field.return_value = "ML-001" 
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                "id": 1,
                "assigned_to": {"id": 123},
                "status": {"name": "Pending"},
                "created_on": "2023-01-01T00:00:00Z",
                "updated_on": "2023-01-02T00:00:00Z",
                "custom_fields": []
                },
                {
                "id": 2, 
                "assigned_to": {"id": 456},
                "status": {"name": "Pending"},
                "created_on": "2023-01-03T00:00:00Z",
                "updated_on": "2023-01-04T00:00:00Z",
                "custom_fields": []
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result, error = MLOwnerService.get_pending_mining_license_details("valid_token")
        assert error is None
        assert len(result) == 1  # Should only include the issue assigned to our user
        assert result[0]["mining_license_number"] == "ML-001"  # Verify we got the mocked license number
        assert result[0]["status"] == "Pending"

    @patch.dict('os.environ', {'REDMINE_URL': 'https://test.redmine.com'})
    @patch('services.mining_owner_service.JWTUtils.get_api_key_from_token')
    @patch('services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id')
    @patch('services.mining_owner_service.requests.get')
    def test_exception_handling(self, mock_get, mock_decode, mock_api_key):
        mock_api_key.return_value = 'valid_api_key'
        mock_decode.return_value = {'success': True, 'user_id': 123}

        mock_get.side_effect = Exception("Test exception")
        
        result, error = MLOwnerService.get_pending_mining_license_details("valid_token")
        assert result is None
        assert "Server error" in error                 

import os
import pytest
from unittest.mock import patch, MagicMock
from services.mining_owner_service import MLOwnerService

class TestGetMiningLicenseById:

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.MLOwnerService.get_attachment_urls")
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_successful_response(self, mock_get_api_key, mock_requests_get, mock_get_attachments):
        # Setup
        mock_get_api_key.return_value = "test_api_key"
        
        mock_issue = {
            "issue": {
                "id": 101,
                "subject": "Test Mining License",
                "status": {"name": "Approved"},
                "author": {"name": "John Doe"},
                "assigned_to": {"name": "Jane Smith"},
                "start_date": "2024-01-01",
                "due_date": "2024-12-31",
                "custom_fields": [
                    {"name": "Mining License Number", "value": "ML-2024-01"},
                    {"name": "Mobile Number", "value": "0771234567"}
                ]
            }
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_issue
        mock_requests_get.return_value = mock_response

        mock_get_attachments.return_value = {
            "License fee receipt": "https://attachments/license.pdf"
        }

        result, error = MLOwnerService.get_mining_license_by_id("token", 101)

        assert error is None
        assert result["id"] == 101
        assert result["status"] == "Approved"
        assert result["mining_license_number"] == "ML-2024-01"
        assert result["mobile_number"] == "0771234567"
        assert result["license_fee_receipt"] == "https://attachments/license.pdf"

    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_invalid_api_key(self, mock_get_api_key):
        mock_get_api_key.return_value = None
        result, error = MLOwnerService.get_mining_license_by_id("bad_token", 999)
        assert result is None
        assert error == "Invalid or missing API key"

    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_missing_redmine_url(self, mock_get_api_key):
        mock_get_api_key.return_value = "valid_api_key"
        with patch.dict(os.environ, {}, clear=True):
            result, error = MLOwnerService.get_mining_license_by_id("token", 999)
            assert result is None
            assert error == "REDMINE_URL environment variable not set"

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_redmine_http_error(self, mock_get_api_key, mock_requests_get):
        mock_get_api_key.return_value = "valid_api_key"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_requests_get.return_value = mock_response

        result, error = MLOwnerService.get_mining_license_by_id("token", 999)
        assert result is None
        assert "Failed to fetch issue" in error
        assert "404" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_no_issue_data(self, mock_get_api_key, mock_requests_get):
        mock_get_api_key.return_value = "valid_api_key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing "issue"
        mock_requests_get.return_value = mock_response

        result, error = MLOwnerService.get_mining_license_by_id("token", 999)
        assert result is None
        assert error == "Issue data not found"

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_exception_handling(self, mock_get_api_key, mock_requests_get):
        mock_get_api_key.return_value = "valid_api_key"
        mock_requests_get.side_effect = Exception("Simulated Failure")

        result, error = MLOwnerService.get_mining_license_by_id("token", 101)
        assert result is None
        assert "Server error" in error
        assert "Simulated Failure" in error

class TestGetMiningLicenseSummary:

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.MLOwnerService.get_custom_field_value")
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_successful_summary(self, mock_get_api_key, mock_decode, mock_requests_get, mock_get_field):
        mock_get_api_key.return_value = "valid_key"
        mock_decode.return_value = {"user_id": 123}

        # Mock custom field extraction
        def side_effect(fields, field_name):
            return {
                "Mobile Number": "0771234567",
                "Administrative District": "Colombo"
            }.get(field_name, None)
        mock_get_field.side_effect = side_effect

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 1,
                    "subject": "ML License A",
                    "assigned_to": {"id": 123, "name": "User A"},
                    "custom_fields": [],
                    "created_on": "2023-01-01T00:00:00Z",
                    "status": {"name": "In Progress"}
                },
                {
                    "id": 2,
                    "subject": "ML License B",
                    "assigned_to": {"id": 999, "name": "Other User"},
                    "custom_fields": [],
                    "created_on": "2023-01-02T00:00:00Z",
                    "status": {"name": "New"}
                }
            ]
        }
        mock_requests_get.return_value = mock_response

        result, error = MLOwnerService.get_mining_license_summary("valid_token")
        assert error is None
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["mobile"] == "0771234567"
        assert result[0]["district"] == "Colombo"
        assert result[0]["status"] == "In Progress"

    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_invalid_token(self, mock_get_api_key):
        mock_get_api_key.return_value = None
        result, error = MLOwnerService.get_mining_license_summary("bad_token")
        assert result is None
        assert "Invalid or missing API key" in error

    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    @patch("services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id")
    def test_missing_user_id(self, mock_decode, mock_get_api_key):
        mock_get_api_key.return_value = "valid_key"
        mock_decode.return_value = {}
        result, error = MLOwnerService.get_mining_license_summary("token")
        assert result is None
        assert "Failed to extract user ID" in error

    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    @patch("services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id")
    def test_missing_redmine_url(self, mock_decode, mock_get_api_key):
        mock_get_api_key.return_value = "valid_key"
        mock_decode.return_value = {"user_id": 123}
        with patch.dict(os.environ, {}, clear=True):
            result, error = MLOwnerService.get_mining_license_summary("token")
            assert result is None
            assert "Environment variable 'REDMINE_URL'" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_redmine_api_failure(self, mock_get_api_key, mock_decode, mock_requests_get):
        mock_get_api_key.return_value = "valid_key"
        mock_decode.return_value = {"user_id": 123}

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Error"
        mock_requests_get.return_value = mock_response

        result, error = MLOwnerService.get_mining_license_summary("token")
        assert result is None
        assert "Failed to fetch ML issues" in error
        assert "500" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.decode_jwt_and_get_user_id")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_exception_handling(self, mock_get_api_key, mock_decode, mock_requests_get):
        mock_get_api_key.return_value = "valid_key"
        mock_decode.return_value = {"user_id": 123}
        mock_requests_get.side_effect = Exception("Test crash")

        result, error = MLOwnerService.get_mining_license_summary("token")
        assert result is None
        assert "Server error" in error
        assert "Test crash" in error


class TestUpdateRoyaltyField:

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.requests.put")
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_successful_update(self, mock_api_key, mock_get, mock_put):
        mock_api_key.return_value = "valid_api_key"
        
        # Mock current issue GET with existing royalty
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "issue": {
                "custom_fields": [
                    {"id": 18, "value": "1000"}
                ]
            }
        }
        mock_get.return_value = mock_get_response

        # Mock PUT update
        mock_put_response = MagicMock()
        mock_put_response.status_code = 204
        mock_put.return_value = mock_put_response

        success, error = MLOwnerService.update_royalty_field("token", 101, 500)
        assert success is True
        assert error is None
        mock_put.assert_called_once()

    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_invalid_token(self, mock_api_key):
        mock_api_key.return_value = None
        success, error = MLOwnerService.update_royalty_field("invalid_token", 101, 200)
        assert success is False
        assert "Invalid or missing API key" in error

    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_missing_redmine_url(self, mock_api_key):
        mock_api_key.return_value = "valid_key"
        with patch.dict(os.environ, {}, clear=True):
            success, error = MLOwnerService.update_royalty_field("token", 101, 200)
            assert success is False
            assert "REDMINE_URL" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_failed_get_request(self, mock_api_key, mock_get):
        mock_api_key.return_value = "valid_key"

        mock_get_response = MagicMock()
        mock_get_response.status_code = 404
        mock_get_response.text = "Not Found"
        mock_get.return_value = mock_get_response

        success, error = MLOwnerService.update_royalty_field("token", 101, 100)
        assert success is False
        assert "Failed to fetch issue" in error
        assert "404" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.requests.put")
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_failed_put_request(self, mock_api_key, mock_get, mock_put):
        mock_api_key.return_value = "valid_key"

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "issue": {
                "custom_fields": [{"id": 18, "value": "1000"}]
            }
        }
        mock_get.return_value = mock_get_response

        mock_put_response = MagicMock()
        mock_put_response.status_code = 400
        mock_put_response.text = "Bad Request"
        mock_put.return_value = mock_put_response

        success, error = MLOwnerService.update_royalty_field("token", 101, 100)
        assert success is False
        assert "Failed to update issue" in error
        assert "400" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.requests.put")
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_non_integer_existing_royalty(self, mock_api_key, mock_get, mock_put):
        mock_api_key.return_value = "valid_key"

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "issue": {
                "custom_fields": [{"id": 18, "value": "not_a_number"}]
            }
        }
        mock_get.return_value = mock_get_response

        mock_put_response = MagicMock()
        mock_put_response.status_code = 204
        mock_put.return_value = mock_put_response

        success, error = MLOwnerService.update_royalty_field("token", 101, 100)
        assert success is True
        assert error is None

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.mining_owner_service.requests.get")
    @patch("services.mining_owner_service.JWTUtils.get_api_key_from_token")
    def test_exception_handling(self, mock_api_key, mock_get):
        mock_api_key.return_value = "valid_key"
        mock_get.side_effect = Exception("Something went wrong")

        success, error = MLOwnerService.update_royalty_field("token", 101, 100)
        assert success is False
        assert "Server error" in error
        assert "Something went wrong" in error     