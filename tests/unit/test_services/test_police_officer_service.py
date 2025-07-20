import pytest
from unittest.mock import patch, MagicMock
from services.police_officer_service import PoliceOfficerService
from datetime import datetime, timedelta, timezone

REDMINE_URL = "https://fake-redmine-url.com"

@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    # patch environment variable for REDMINE_URL
    monkeypatch.setenv("REDMINE_URL", REDMINE_URL)


@patch('services.police_officer_service.JWTUtils.get_api_key_from_token')
@patch('services.police_officer_service.requests.get')
def test_check_lorry_number_success_valid_license(mock_get, mock_get_api_key):
    mock_get_api_key.return_value = 'mock_api_key'

    current_time = datetime.now(timezone.utc)
    created_on = (current_time - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    estimated_hours = 5

    # Prepare mock TPL issues response with one valid license
    tpl_issues_response = {
        "issues": [
            {
                "id": 101,
                "created_on": created_on,
                "estimated_hours": estimated_hours,
                "custom_fields": [
                    {"id": 53, "value": "ABC123"},   # lorry number (matching)
                    {"id": 59, "value": "LLL/100/109"},  # LicenseNumber
                    {"id": 58, "value": "10"},       # Cubes
                    {"id": 68, "value": "Colombo"},  # Destination
                    {"id": 55, "value": "Route A"},
                    {"id": 56, "value": "Route B"},
                    {"id": 57, "value": "Route C"},
                ],
                "assigned_to": {"name": "Officer A"},
            }
        ]
    }

    # Prepare mock Mining License issues response
    ml_issues_response = {
        "issues": [
            {
                "assigned_to": {"name": "Owner A"},
                "start_date": "2023-01-01",
                "due_date": "2024-01-01",
                "custom_fields": [
                    {"id": 101, "value": "LLL/100/109"},
                    {"id": 66, "value": "0712345678"},
                    {"id": 31, "value": "Division 1"},
                ],
            }
        ]
    }

    def side_effect(url, params, headers):
        if params.get("tracker_id") == 5:
            return MagicMock(status_code=200, json=lambda: tpl_issues_response)
        elif params.get("tracker_id") == 4:
            return MagicMock(status_code=200, json=lambda: ml_issues_response)
        else:
            return MagicMock(status_code=404, text="Not Found")

    mock_get.side_effect = side_effect

    tpl_data, error = PoliceOfficerService.check_lorry_number("ABC123", "mock_token")

    assert error is None
    assert tpl_data is not None
    assert tpl_data["LicenseNumber"] == "LLL/100/109"
    assert tpl_data["IsValid"] is True
    assert tpl_data["Assignee"] == "Officer A"
    assert tpl_data["owner"] == "Owner A"
    assert tpl_data["License Owner Contact Number"] == "0712345678"


@patch('services.police_officer_service.JWTUtils.get_api_key_from_token')
def test_check_lorry_number_missing_redmine_url_or_api_key(mock_get_api_key, monkeypatch):
    monkeypatch.delenv("REDMINE_URL", raising=False)
    mock_get_api_key.return_value = None
    result, error = PoliceOfficerService.check_lorry_number("ABC123", "mock_token")
    assert result is None
    assert "Redmine URL or API Key is missing" in error


@patch('services.police_officer_service.JWTUtils.get_api_key_from_token')
@patch('services.police_officer_service.requests.get')
def test_check_lorry_number_tpl_issues_fetch_fail(mock_get, mock_get_api_key):
    mock_get_api_key.return_value = "mock_api_key"
    mock_get.return_value = MagicMock(status_code=500, text="Server Error")
    result, error = PoliceOfficerService.check_lorry_number("ABC123", "mock_token")
    assert result is None
    assert "Failed to fetch TPL issues" in error


@patch('services.police_officer_service.JWTUtils.get_api_key_from_token')
@patch('services.police_officer_service.requests.get')
def test_check_lorry_number_no_valid_tpl_license(mock_get, mock_get_api_key):
    mock_get_api_key.return_value = "mock_api_key"
    # Issues that either do not match or expired
    issues = {
        "issues": [
            {
                "id": 102,
                "created_on": (datetime.now(timezone.utc) - timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "estimated_hours": 1,  # expired license
                "custom_fields": [{"id": 53, "value": "ABC123"}],
                "assigned_to": {"name": "Officer B"},
            }
        ]
    }
    mock_get.return_value = MagicMock(status_code=200, json=lambda: issues)
    result, error = PoliceOfficerService.check_lorry_number("ABC123", "mock_token")

    assert result is not None  # license info returned even if expired
    assert result["IsValid"] is False
    assert error is None



@patch('services.police_officer_service.UserUtils.get_user_phone')
@patch('services.police_officer_service.JWTUtils.get_api_key_from_token')
@patch('services.police_officer_service.requests.post')
def test_create_complaint_success(mock_post, mock_get_api_key, mock_get_user_phone):
    mock_get_api_key.return_value = "mock_api_key"
    mock_get_user_phone.return_value = "0712345678"

    mock_post.return_value = MagicMock(status_code=201, json=lambda: {"issue": {"id": 999}})

    success, issue_id = PoliceOfficerService.create_complaint("ABC123", 1, "mock_token")

    assert success is True
    assert issue_id == 999
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["issue"]["custom_fields"][0]["value"] == "0712345678"
    assert kwargs["json"]["issue"]["custom_fields"][1]["value"] == "ABC123"


@patch('services.police_officer_service.UserUtils.get_user_phone')
@patch('services.police_officer_service.JWTUtils.get_api_key_from_token')
@patch('services.police_officer_service.requests.post')
def test_create_complaint_failure(mock_post, mock_get_api_key, mock_get_user_phone):
    mock_get_api_key.return_value = "mock_api_key"
    mock_get_user_phone.return_value = "0712345678"

    mock_post.return_value = MagicMock(status_code=400, text="Bad Request")

    success, error_msg = PoliceOfficerService.create_complaint("ABC123", 1, "mock_token")

    assert success is False
    assert error_msg == "Failed to create complaint"
