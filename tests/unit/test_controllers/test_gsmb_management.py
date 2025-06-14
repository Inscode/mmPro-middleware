import pytest
from unittest.mock import patch, MagicMock
from utils.jwt_utils import JWTUtils
from flask import jsonify


@pytest.fixture
def valid_token():
    tokens = JWTUtils.create_jwt_token(user_id=1, user_role='GSMBManagement')
    return f"Bearer {tokens['access_token']}"

@pytest.fixture
def mock_monthly_data():
    return [
        {"month": "Jan", "totalCubes": 1000},
        {"month": "Feb", "totalCubes": 1200},
        # ... other months
    ]

def test_monthly_total_sand_cubes_success(client, valid_token, mock_monthly_data):
    """Test successful retrieval of monthly sand cubes"""
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.monthly_total_sand_cubes') as mock_service:
        mock_service.return_value = (mock_monthly_data, None)
        
        response = client.get('/gsmb-management/monthly-total-sand', 
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert "issues" in data
        assert data["issues"] == mock_monthly_data
        mock_service.assert_called_once_with(valid_token)

def test_monthly_total_sand_cubes_error(client, valid_token):
    """Test error scenario"""
    error_msg = "Failed to fetch data from Redmine"
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.monthly_total_sand_cubes') as mock_service:
        mock_service.return_value = (None, error_msg)
        
        response = client.get('/gsmb-management/monthly-total-sand',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert data["error"] == error_msg


@pytest.fixture
def mock_top_mining_holders_data():
    """Mock data for top mining holders."""
    return [
        {"owner": "Company A", "totalCubes": 5000},
        {"owner": "Company B", "totalCubes": 4500},
        {"owner": "Company C", "totalCubes": 3000},
    ]

def test_fetch_top_mining_holders_success(client, valid_token, mock_top_mining_holders_data):
    """Test successful retrieval of top mining holders."""
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.fetch_top_mining_holders') as mock_service:
        mock_service.return_value = (mock_top_mining_holders_data, None)

        response = client.get('/gsmb-management/fetch-top-mining-holders',
                              headers={"Authorization": valid_token})

        assert response.status_code == 200
        data = response.get_json()
        assert "issues" in data
        assert data["issues"] == mock_top_mining_holders_data
        mock_service.assert_called_once_with(valid_token)

def test_fetch_top_mining_holders_service_error(client, valid_token):
    """Test error scenario when service fails to fetch top mining holders."""
    error_msg = "Failed to fetch top mining holders from Redmine"
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.fetch_top_mining_holders') as mock_service:
        mock_service.return_value = (None, error_msg)

        response = client.get('/gsmb-management/fetch-top-mining-holders',
                              headers={"Authorization": valid_token})

        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert data["error"] == error_msg
        mock_service.assert_called_once_with(valid_token)


@pytest.fixture
def mock_royalty_counts_data():
    """Mock data for royalty counts (what the service jsonify's)."""
    return {
        "monthly_royalty_breakdown": [
            {"month": "Jan", "paid": 5, "pending": 2, "overdue": 1},
            {"month": "Feb", "paid": 7, "pending": 1, "overdue": 0},
            # ... other months
        ],
        "total_paid": 12,
        "total_pending": 3,
        "total_overdue": 1
    }

def test_fetch_royalty_counts_success(client, valid_token, mock_royalty_counts_data):
    """Test successful retrieval of royalty counts"""
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.fetch_royalty_counts') as mock_service:
        # Return the raw data instead of jsonify
        mock_service.return_value = (mock_royalty_counts_data, None)
        
        response = client.get('/gsmb-management/fetch-royalty-counts',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data == mock_royalty_counts_data
        mock_service.assert_called_once_with(valid_token)

def test_fetch_royalty_counts_error(client, valid_token):
    """Test error scenario when fetching royalty counts"""
    error_msg = "Database connection failed"
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.fetch_royalty_counts') as mock_service:
        mock_service.return_value = (None, error_msg)
        
        response = client.get('/gsmb-management/fetch-royalty-counts',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert data["error"] == error_msg
        mock_service.assert_called_once_with(valid_token)


@pytest.fixture
def mock_monthly_license_data():
    """Mock data for monthly mining license counts"""
    return [
        {"month": "Jan", "new_licenses": 15, "renewed_licenses": 10},
        {"month": "Feb", "new_licenses": 12, "renewed_licenses": 8},
        {"month": "Mar", "new_licenses": 18, "renewed_licenses": 12}
    ]

def test_monthly_mining_license_count_success(client, valid_token, mock_monthly_license_data):
    """Test successful retrieval of monthly mining license counts"""
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.monthly_mining_license_count') as mock_service:
        mock_service.return_value = (mock_monthly_license_data, None)
        
        response = client.get('/gsmb-management/monthly-mining-license-count',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert "issues" in data
        assert data["issues"] == mock_monthly_license_data
        mock_service.assert_called_once_with(valid_token)

def test_monthly_mining_license_count_service_error(client, valid_token):
    """Test error response from service layer"""
    error_msg = "Database connection error"
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.monthly_mining_license_count') as mock_service:
        mock_service.return_value = (None, error_msg)
        
        response = client.get('/gsmb-management/monthly-mining-license-count',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert data["error"] == error_msg

@pytest.fixture
def mock_transport_license_data():
    """Mock data for transport license destinations"""
    return [
        {"destination": "Colombo", "count": 45},
        {"destination": "Kandy", "count": 32},
        {"destination": "Galle", "count": 28}
    ]

def test_transport_license_destination_success(client, valid_token, mock_transport_license_data):
    """Test successful retrieval of transport license destinations"""
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.transport_license_destination') as mock_service:
        mock_service.return_value = (mock_transport_license_data, None)
        
        response = client.get('/gsmb-management/transport-license-destination',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert "issues" in data
        assert data["issues"] == mock_transport_license_data
        mock_service.assert_called_once_with(valid_token)

def test_transport_license_destination_service_error(client, valid_token):
    """Test error response from service layer"""
    error_msg = "Failed to fetch transport license data"
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.transport_license_destination') as mock_service:
        mock_service.return_value = (None, error_msg)
        
        response = client.get('/gsmb-management/transport-license-destination',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert data["error"] == error_msg
        mock_service.assert_called_once_with(valid_token)

@pytest.fixture
def mock_location_ml_data():
    """Mock data for total mining locations"""
    return [
        {"location": "Colombo District", "total_ml": 15},
        {"location": "Gampaha District", "total_ml": 12},
        {"location": "Kalutara District", "total_ml": 8}
    ]

def test_total_location_ml_success(client, valid_token, mock_location_ml_data):
    """Test successful retrieval of total mining locations"""
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.total_location_ml') as mock_service:
        mock_service.return_value = (mock_location_ml_data, None)
        
        response = client.get('/gsmb-management/total-location-ml',
                            headers={"Authorization": valid_token})
        
        # Assert response status and structure
        assert response.status_code == 200
        data = response.get_json()
        assert "issues" in data
        assert isinstance(data["issues"], list)
        
        # Assert data content
        assert data["issues"] == mock_location_ml_data
        assert len(data["issues"]) == 3
        assert all("location" in item and "total_ml" in item for item in data["issues"])
        
        # Verify service was called correctly
        mock_service.assert_called_once_with(valid_token)

def test_total_location_ml_service_error(client, valid_token):
    """Test error response from service layer"""
    error_msg = "Failed to connect to location database"
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.total_location_ml') as mock_service:
        mock_service.return_value = (None, error_msg)
        
        response = client.get('/gsmb-management/total-location-ml',
                            headers={"Authorization": valid_token})
        
        # Assert error response
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert data["error"] == error_msg
        
        # Verify service was called correctly
        mock_service.assert_called_once_with(valid_token)

@pytest.fixture
def mock_complaint_data():
    """Mock data for complaint counts"""
    return [
        {"month": "January", "total_complaints": 25, "resolved": 18},
        {"month": "February", "total_complaints": 32, "resolved": 25},
        {"month": "March", "total_complaints": 28, "resolved": 20}
    ]


def test_complaint_counts_success(client, valid_token, mock_complaint_data):
    """Test successful retrieval of complaint counts"""
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.complaint_counts') as mock_service:
        mock_service.return_value = (mock_complaint_data, None)
        
        response = client.get('/gsmb-management/complaint-counts',
                            headers={"Authorization": valid_token})
        
        # Assert response status and structure
        assert response.status_code == 200
        data = response.get_json()
        assert "issues" in data
        assert isinstance(data["issues"], list)
        
        # Assert data content
        assert data["issues"] == mock_complaint_data
        assert len(data["issues"]) == 3
        assert all("month" in item and "total_complaints" in item and "resolved" in item 
                 for item in data["issues"])
        
        # Verify service was called correctly
        mock_service.assert_called_once_with(valid_token)

def test_complaint_counts_service_error(client, valid_token):
    """Test error response from service layer"""
    error_msg = "Database connection failed"
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.complaint_counts') as mock_service:
        mock_service.return_value = (None, error_msg)
        
        response = client.get('/gsmb-management/complaint-counts',
                            headers={"Authorization": valid_token})
        
        # Assert error response
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert data["error"] == error_msg
        
        # Verify service was called correctly
        mock_service.assert_called_once_with(valid_token)

@pytest.fixture
def mock_role_counts():
    return [
        {"role": "GSMBManagement", "count": 5},
        {"role": "GSMBOfficer", "count": 32},
        {"role": "MiningOwner", "count": 128}
    ]

@pytest.fixture
def mock_license_counts():
    return [
        {"license_type": "A", "count": 45},
        {"license_type": "B", "count": 32},
        {"license_type": "C", "count": 28}
    ]

@pytest.fixture
def mock_inactive_officers():
    return [
        {"id": 101, "name": "Officer 1", "status": 3},
        {"id": 102, "name": "Officer 2", "status": 3}
    ]

def test_role_counts_success(client, valid_token, mock_role_counts):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.role_counts') as mock_service:
        mock_service.return_value = (mock_role_counts, None)
        
        response = client.get('/gsmb-management/role-counts',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert "issues" in data
        assert data["issues"] == mock_role_counts
        mock_service.assert_called_once_with(valid_token)

def test_role_counts_service_error(client, valid_token):
    error_msg = "Database error"
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.role_counts') as mock_service:
        mock_service.return_value = (None, error_msg)
        
        response = client.get('/gsmb-management/role-counts',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 500
        assert response.json["error"] == error_msg

def test_mining_license_count_success(client, valid_token, mock_license_counts):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.mining_license_count') as mock_service:
        mock_service.return_value = (mock_license_counts, None)
        
        response = client.get('/gsmb-management/mining-license-count',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 200
        assert response.json["issues"] == mock_license_counts

def test_mining_license_count_empty(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.mining_license_count') as mock_service:
        mock_service.return_value = ([], None)
        
        response = client.get('/gsmb-management/mining-license-count',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 200
        assert response.json["issues"] == []

def test_unactive_officers_success(client, valid_token, mock_inactive_officers):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.unactive_gsmb_officers') as mock_service:
        mock_service.return_value = (mock_inactive_officers, None)
        
        response = client.get('/gsmb-management/unactive-gsmb-officers',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 200
        data = response.json
        assert "officers" in data
        assert "count" in data
        assert data["count"] == 2

def test_unactive_officers_error(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.unactive_gsmb_officers') as mock_service:
        mock_service.return_value = (None, "Permission denied")
        
        response = client.get('/gsmb-management/unactive-gsmb-officers',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 500
        assert "Permission denied" in response.json["error"]

def test_activate_officer_success(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.activate_gsmb_officer') as mock_service:
        mock_service.return_value = (True, None)
        
        response = client.put('/gsmb-management/active-gsmb-officers/101',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 200
        assert response.json["success"] is True
        assert response.json["new_status"] == 1

def test_activate_officer_not_found(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.activate_gsmb_officer') as mock_service:
        mock_service.return_value = (False, "Officer not found")
        
        response = client.put('/gsmb-management/active-gsmb-officers/999',
                            headers={"Authorization": valid_token})
        
        assert response.status_code == 500
        assert "Officer not found" in response.json["error"]

def test_activate_officer_invalid_id(client, valid_token):
    response = client.put('/gsmb-management/active-gsmb-officers/abc',
                        headers={"Authorization": valid_token})
    assert response.status_code == 404



