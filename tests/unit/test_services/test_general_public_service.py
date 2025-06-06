import pytest
from unittest.mock import patch, MagicMock
from services.general_public_service import GeneralPublicService
from datetime import datetime, timedelta, UTC


# is_lorry_number_valid


def test_is_lorry_number_valid_success():
    future_time = (datetime.now(UTC) - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    mock_issues = [{
        "id": 1,
        "created_on": future_time,
        "estimated_hours": 2,
        "custom_fields": [
            {"id": 53, "value": "AB1234"}
        ]
    }]
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = {"issues": mock_issues}

    with patch('services.general_public_service.requests.get', return_value=mock_response):
        result, error = GeneralPublicService.is_lorry_number_valid("AB1234")
        assert result is True
        assert error is None

def test_is_lorry_number_valid_expired():
    past_time = (datetime.now(UTC) - timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M:%SZ')
    mock_issues = [{
        "id": 1,
        "created_on": past_time,
        "estimated_hours": 2,
        "custom_fields": [
            {"id": 53, "value": "AB1234"}
        ]
    }]
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = {"issues": mock_issues}

    with patch('services.general_public_service.requests.get', return_value=mock_response):
        result, error = GeneralPublicService.is_lorry_number_valid("AB1234")
        assert result is False
        assert error is None

def test_is_lorry_number_valid_failure():
    mock_response = MagicMock(status_code=500, text="Server error")
    with patch('services.general_public_service.requests.get', return_value=mock_response):
        result, error = GeneralPublicService.is_lorry_number_valid("AB1234")
        assert result is None
        assert "Failed to fetch" in error


# generate_otp


def test_generate_otp_format():
    otp = GeneralPublicService.generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()


# send_verification_code


@patch('services.general_public_service.cache.set')
@patch('services.general_public_service.GeneralPublicService.generate_otp', return_value="123456")
@patch('services.general_public_service.requests.get')
def test_send_verification_code_success(mock_get, mock_otp, mock_cache):
    mock_get.return_value = MagicMock(status_code=200)
    result, message = GeneralPublicService.send_verification_code("0771234567")
    assert result is True
    assert message == "Message sent successfully"
    mock_cache.assert_called_once_with("0771234567", "123456", expire=600)

@patch('services.general_public_service.requests.get')
def test_send_verification_code_failure(mock_get):
    mock_get.return_value = MagicMock(status_code=400, text="Bad request")
    result, message = GeneralPublicService.send_verification_code("0771234567")
    assert result is False
    assert "Failed to send message" in message


# verify_code


@patch('services.general_public_service.cache.get', return_value="123456")
@patch('services.general_public_service.cache.delete')
def test_verify_code_success(mock_delete, mock_get):
    result, error = GeneralPublicService.verify_code("0771234567", "123456")
    assert result is True
    assert error is None
    mock_delete.assert_called_once()

@patch('services.general_public_service.cache.get', return_value="654321")
def test_verify_code_invalid(mock_get):
    result, error = GeneralPublicService.verify_code("0771234567", "123456")
    assert result is False
    assert error == "Invalid OTP"

@patch('services.general_public_service.cache.get', return_value=None)
def test_verify_code_expired(mock_get):
    result, error = GeneralPublicService.verify_code("0771234567", "123456")
    assert result is False
    assert error == "OTP expired or not found"


# create_complaint


@patch('services.general_public_service.requests.post')
def test_create_complaint_success(mock_post):
    mock_response = MagicMock(status_code=201)
    mock_response.json.return_value = {'issue': {'id': 99}}
    mock_post.return_value = mock_response

    result, issue_id = GeneralPublicService.create_complaint("0771234567", "AB1234")
    assert result is True
    assert issue_id == 99

@patch('services.general_public_service.requests.post')
def test_create_complaint_failure(mock_post):
    mock_post.return_value = MagicMock(status_code=400, text="Bad Request")
    result, msg = GeneralPublicService.create_complaint("0771234567", "AB1234")
    assert result is False
    assert msg == "Failed to create complaint"
