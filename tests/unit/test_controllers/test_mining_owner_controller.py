import pytest
from unittest.mock import patch
from utils.jwt_utils import JWTUtils

@pytest.fixture
def valid_token():
    tokens = JWTUtils.create_jwt_token(user_id=1, user_role='MLOwner')
    return f"Bearer {tokens['access_token']}"

def test_get_mining_licenses_success(client, valid_token):
    mock_issues = [
        {
            'id': 1,
            'license_number': 'ML-001',
            'status': 'Active',
            'owner_id': 1
        },
        {
            'id': 2,
            'license_number': 'ML-002',
            'status': 'Pending',
            'owner_id': 1
        }
    ]

    with patch('services.mining_owner_service.MLOwnerService.mining_licenses', 
               return_value=(mock_issues, None)):
        response = client.get('mining-owner/mining-licenses',
                             headers={"Authorization": valid_token})
        
        assert response.status_code == 200
        assert 'issues' in response.get_json()
        assert len(response.get_json()['issues']) == 2

def test_get_mining_licenses_missing_token(client):
    response = client.get('mining-owner/mining-licenses')
    assert response.status_code == 403  # Changed from 400 to 403
    assert 'error' in response.get_json()
    # The error message might be different from what you expected

def test_get_mining_licenses_invalid_token(client):
    response = client.get('mining-owner/mining-licenses',
                         headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    assert 'error' in response.get_json()

def test_get_mining_licenses_service_error(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.mining_licenses',
               return_value=(None, "Database connection error")):
        response = client.get('mining-owner/mining-licenses',
                             headers={"Authorization": valid_token})
        assert response.status_code == 500
        assert response.get_json()['error'] == 'Database connection error'

def test_get_mining_licenses_empty_result(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.mining_licenses',
               return_value=([], None)):
        response = client.get('mining-owner/mining-licenses',
                             headers={"Authorization": valid_token})
        assert response.status_code == 200
        assert response.get_json()['issues'] == []


@pytest.fixture
def valid_token():
    tokens = JWTUtils.create_jwt_token(user_id=1, user_role='MLOwner')
    return f"Bearer {tokens['access_token']}"

@pytest.fixture
def valid_tpl_data():
    return {
        "license_number": "TPL-123",
        "lorry_number": "ABC-1234",
        "driver_name": "John Doe",
        "valid_from": "2023-01-01",
        "valid_to": "2023-12-31"
    }

def test_create_tpl_success(client, valid_token, valid_tpl_data):
    mock_response = {
        "id": 1,
        "license_number": "TPL-123",
        "status": "Active"
    }

    with patch('services.mining_owner_service.MLOwnerService.create_tpl', 
               return_value=(mock_response, None)):
        response = client.post(
            'mining-owner/create-tpl',
            json=valid_tpl_data,
            headers={"Authorization": valid_token}
        )
        
        assert response.status_code == 201
        assert 'id' in response.get_json()
        assert response.get_json()['license_number'] == "TPL-123"

def test_create_tpl_missing_token(client, valid_tpl_data):
    response = client.post(
        'mining-owner/create-tpl',
        json=valid_tpl_data
    )
    assert response.status_code == 403
    assert 'error' in response.get_json()

def test_create_tpl_invalid_token(client, valid_tpl_data):
    response = client.post(
        'mining-owner/create-tpl',
        json=valid_tpl_data,
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert 'error' in response.get_json()

def test_create_tpl_invalid_data(client, valid_token):
    invalid_data = {"license_number": "TPL-123"}  # Missing required fields
    with patch('services.mining_owner_service.MLOwnerService.create_tpl',
               return_value=(None, "Missing required fields")):
        response = client.post(
            'mining-owner/create-tpl',
            json=invalid_data,
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 400
        assert response.get_json()['error'] == "Missing required fields"

def test_create_tpl_service_error(client, valid_token, valid_tpl_data):
    with patch('services.mining_owner_service.MLOwnerService.create_tpl',
               return_value=(None, "Database error")):
        response = client.post(
            'mining-owner/create-tpl',
            json=valid_tpl_data,
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 400
        assert response.get_json()['error'] == "Database error"

def test_create_tpl_server_error(client, valid_token, valid_tpl_data):
    with patch('services.mining_owner_service.MLOwnerService.create_tpl',
               side_effect=Exception("Unexpected error")):
        response = client.post(
            'mining-owner/create-tpl',
            json=valid_tpl_data,
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 500
        assert 'error' in response.get_json()

@pytest.fixture
def valid_token():
    tokens = JWTUtils.create_jwt_token(user_id=1, user_role='MLOwner')
    return f"Bearer {tokens['access_token']}"

@pytest.fixture
def mock_tpl_data():
    return [
        {
            "id": 1,
            "license_number": "TPL-001",
            "mining_license_number": "ML-123",
            "status": "Active"
        },
        {
            "id": 2,
            "license_number": "TPL-002",
            "mining_license_number": "ML-123",
            "status": "Pending"
        }
    ]

def test_view_tpls_success(client, valid_token, mock_tpl_data):
    with patch('services.mining_owner_service.MLOwnerService.view_tpls', 
               return_value=(mock_tpl_data, None)):
        response = client.get(
            'mining-owner/view-tpls?mining_license_number=ML-123',
            headers={"Authorization": valid_token}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'view_tpls' in data
        assert len(data['view_tpls']) == 2
        assert data['view_tpls'][0]['mining_license_number'] == "ML-123"

def test_view_tpls_missing_token(client):
    response = client.get('mining-owner/view-tpls?mining_license_number=ML-123')
    assert response.status_code == 403
    assert response.get_json()['error'] == "Token is missing"  # Changed to match middleware

def test_view_tpls_invalid_token_content(client):
    response = client.get(
        'mining-owner/view-tpls?mining_license_number=ML-123',
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401
    assert 'Invalid token' in response.get_json()['error']

def test_view_tpls_missing_license_param(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.view_tpls',
               return_value=(None, "Mining license number is required")):
        response = client.get(
            'mining-owner/view-tpls',
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 500
        assert "Mining license number is required" in response.get_json()['error']

def test_view_tpls_service_error(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.view_tpls',
               return_value=(None, "Database error")):
        response = client.get(
            'mining-owner/view-tpls?mining_license_number=ML-123',
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 500
        assert response.get_json()['error'] == "Database error"

def test_view_tpls_empty_result(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.view_tpls',
               return_value=([], None)):
        response = client.get(
            'mining-owner/view-tpls?mining_license_number=ML-999',
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 200
        assert response.get_json()['view_tpls'] == []

def test_view_tpls_unexpected_error(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.view_tpls',
               side_effect=Exception("Unexpected error")):
        response = client.get(
            'mining-owner/view-tpls?mining_license_number=ML-123',
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 500
        assert "Unexpected error" in response.get_json()['error']



@pytest.fixture
def valid_token():
    tokens = JWTUtils.create_jwt_token(user_id=1, user_role='MLOwner')
    return f"Bearer {tokens['access_token']}"

@pytest.fixture
def mock_license_data():
    return [
        {
            "id": 1,
            "license_number": "ML-001",
            "status": "Active",
            "owner_id": 1
        },
        {
            "id": 2,
            "license_number": "ML-002",
            "status": "Pending",
            "owner_id": 1
        }
    ]

def test_mining_home_licenses_success(client, valid_token, mock_license_data):
    with patch('services.mining_owner_service.MLOwnerService.mining_homeLicenses', 
               return_value=(mock_license_data, None)):
        response = client.get(
            'mining-owner/mining-homeLicenses',
            headers={"Authorization": valid_token}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'mining_home' in data
        assert len(data['mining_home']) == 2
        assert data['mining_home'][0]['license_number'] == "ML-001"

def test_mining_home_licenses_missing_token(client):
    response = client.get('mining-owner/mining-homeLicenses')
    assert response.status_code == 403
    assert 'error' in response.get_json()

def test_mining_home_licenses_empty_token(client):
    response = client.get(
        'mining-owner/mining-homeLicenses',
        headers={"Authorization": "Bearer "}  # Empty token after Bearer
    )
    assert response.status_code == 401
    assert response.get_json()['error'] == "Invalid token"

def test_mining_home_licenses_service_error(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.mining_homeLicenses',
               return_value=(None, "Database error")):
        response = client.get(
            'mining-owner/mining-homeLicenses',
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 500
        assert response.get_json()['error'] == "Database error"

def test_mining_home_licenses_empty_result(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.mining_homeLicenses',
               return_value=([], None)):
        response = client.get(
            'mining-owner/mining-homeLicenses',
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 200
        assert response.get_json()['mining_home'] == []

def test_mining_home_licenses_unexpected_error(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.mining_homeLicenses',
               side_effect=Exception("Unexpected error")):
        response = client.get(
            'mining-owner/mining-homeLicenses',
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 500
        assert "Unexpected error" in response.get_json()['error'] 
               


@pytest.fixture
def valid_token():
    tokens = JWTUtils.create_jwt_token(user_id=1, user_role='MLOwner')
    return f"Bearer {tokens['access_token']}"

@pytest.fixture
def mock_ml_detail():
    return {
        "id": 1,
        "license_number": "ML-123",
        "status": "Active",
        "owner": "John Doe"
    }

def test_ml_detail_success(client, valid_token, mock_ml_detail):
    with patch('services.mining_owner_service.MLOwnerService.ml_detail', 
               return_value=(mock_ml_detail, None)):
        response = client.get(
            'mining-owner/ml-detail?l_number=ML-123',
            headers={"Authorization": valid_token}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'ml_detail' in data
        assert data['ml_detail']['license_number'] == "ML-123"

def test_ml_detail_missing_l_number(client, valid_token):
    response = client.get(
        'mining-owner/ml-detail',
        headers={"Authorization": valid_token}
    )
    assert response.status_code == 400
    assert response.get_json()['error'] == "Missing 'l_number' query parameter"

def test_ml_detail_service_error(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.ml_detail',
               return_value=(None, "Database error")):
        response = client.get(
            'mining-owner/ml-detail?l_number=ML-123',
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 500
        assert response.get_json()['error'] == "Database error"

def test_ml_detail_not_found(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.ml_detail',
               return_value=(None, "License not found")):
        response = client.get(
            'mining-owner/ml-detail?l_number=ML-999',
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 404
        assert response.get_json()['error'] == "License not found"

def test_ml_detail_unexpected_error(client, valid_token):
    with patch('services.mining_owner_service.MLOwnerService.ml_detail',
               side_effect=Exception("Unexpected error")):
        response = client.get(
            'mining-owner/ml-detail?l_number=ML-123',
            headers={"Authorization": valid_token}
        )
        assert response.status_code == 500
        assert "Unexpected error" in response.get_json()['error']