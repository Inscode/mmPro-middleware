import pytest
from unittest.mock import patch
from utils.jwt_utils import JWTUtils

@pytest.fixture
def valid_token():
    tokens = JWTUtils.create_jwt_token(user_id=1, user_role='PoliceOfficer')
    return f"Bearer {tokens['access_token']}"

def test_check_lorry_number_success(client, valid_token):
    mock_issues = {
        'license_number': 'TPL-123',
        'lorry_number': 'ABC-1234',
        'status': 'Valid'
    }

    with patch('services.police_officer_service.PoliceOfficerService.check_lorry_number', return_value=(mock_issues, None)):
        response = client.get('/police-officer/check-lorry-number?lorry_number=ABC-1234',
                              headers={"Authorization": valid_token})
        assert response.status_code == 200

def test_check_lorry_number_missing_param(client, valid_token):
    response = client.get('/police-officer/check-lorry-number',
                          headers={"Authorization": valid_token})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Lorry number is required'

def test_check_lorry_number_not_found(client, valid_token):
    with patch('services.police_officer_service.PoliceOfficerService.check_lorry_number',
               return_value=(None, "No TPL with this lorry number")):
        response = client.get('/police-officer/check-lorry-number?lorry_number=XYZ-9999',
                              headers={"Authorization": valid_token})
        assert response.status_code == 200
        assert response.get_json()['error'] == 'No TPL with this lorry number'

def test_check_lorry_number_service_error(client, valid_token):
    with patch('services.police_officer_service.PoliceOfficerService.check_lorry_number',
               return_value=(None, "Database error")):
        response = client.get('/police-officer/check-lorry-number?lorry_number=ERROR-001',
                              headers={"Authorization": valid_token})
        assert response.status_code == 500
        assert response.get_json()['error'] == 'Database error'

def test_create_complaint_success(client, valid_token):
    mock_input = {
        'input': {'subject': 'Illegal transport', 'description': 'Observed without license'},
        'userID': 7
    }

    with patch('services.police_officer_service.PoliceOfficerService.create_complaint',
               return_value=(True, 123)):
        response = client.post('/police-officer/create-complaint',
                               json=mock_input,
                               headers={"Authorization": valid_token})
        assert response.status_code == 200
        assert response.get_json()['success'] is True
        assert response.get_json()['complaint_id'] == 123

def test_create_complaint_failure(client, valid_token):
    mock_input = {
        'input': {'subject': 'Illegal transport'},
        'userID': 7
    }

    with patch('services.police_officer_service.PoliceOfficerService.create_complaint',
               return_value=(False, 'Failed to create complaint')):
        response = client.post('/police-officer/create-complaint',
                               json=mock_input,
                               headers={"Authorization": valid_token})
        assert response.status_code == 500
        assert response.get_json()['success'] is False
        assert response.get_json()['error'] == 'Failed to create complaint'
