import pytest
from unittest.mock import patch
from utils.jwt_utils import JWTUtils
from flask import jsonify 

@pytest.fixture
def valid_token():
    tokens = JWTUtils.create_jwt_token(user_id=1, user_role='GSMBManagement')
    return f"Bearer {tokens['access_token']}"

def test_monthly_total_sand_cubes(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.monthly_total_sand_cubes',
               return_value=([{"month": "June", "total": 1200}], None)):
        response = client.get('/gsmb-management/monthly-total-sand', headers={"Authorization": valid_token})
        assert response.status_code == 200
        assert "issues" in response.get_json()

def test_fetch_top_mining_holders(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.fetch_top_mining_holders',
               return_value=([{"holder": "John Doe", "volume": 5000}], None)):
        response = client.get('/gsmb-management/fetch-top-mining-holders', headers={"Authorization": valid_token})
        assert response.status_code == 200
        assert "issues" in response.get_json()

def test_fetch_royalty_counts(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.fetch_royalty_counts',
               return_value=({"royalty": 200}, None)):
        response = client.get(
            '/gsmb-management/fetch-royalty-counts',
            headers={'Authorization': valid_token}
        )
        assert response.status_code == 200
        assert response.json == {"royalty": 200}

def test_monthly_mining_license_count(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.monthly_mining_license_count',
               return_value=([{"month": "June", "count": 30}], None)):
        response = client.get('/gsmb-management/monthly-mining-license-count', headers={"Authorization": valid_token})
        assert response.status_code == 200
        assert "issues" in response.get_json()

def test_transport_license_destination(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.transport_license_destination',
               return_value=([{"location": "Colombo", "count": 50}], None)):
        response = client.get('/gsmb-management/transport-license-destination', headers={"Authorization": valid_token})
        assert response.status_code == 200
        assert "issues" in response.get_json()

def test_total_location_ml(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.total_location_ml',
               return_value=([{"location": "Galle", "count": 15}], None)):
        response = client.get('/gsmb-management/total-location-ml', headers={"Authorization": valid_token})
        assert response.status_code == 200
        assert "issues" in response.get_json()

def test_complaint_counts(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.complaint_counts',
               return_value=([{"pending": 5, "resolved": 10}], None)):
        response = client.get('/gsmb-management/complaint-counts', headers={"Authorization": valid_token})
        assert response.status_code == 200
        assert "issues" in response.get_json()

def test_role_counts(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.role_counts',
               return_value=([{"role": "PoliceOfficer", "count": 100}], None)):
        response = client.get('/gsmb-management/role-counts', headers={"Authorization": valid_token})
        assert response.status_code == 200
        assert "issues" in response.get_json()

def test_mining_license_count(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.mining_license_count',
               return_value=([{"type": "Type A", "count": 20}], None)):
        response = client.get('/gsmb-management/mining-license-count', headers={"Authorization": valid_token})
        assert response.status_code == 200
        assert "issues" in response.get_json()

def test_unactive_gsmb_officers(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.unactive_gsmb_officers',
               return_value=([{"id": 3, "name": "Officer C"}], None)):
        response = client.get('/gsmb-management/unactive-gsmb-officers', headers={"Authorization": valid_token})
        data = response.get_json()
        assert response.status_code == 200
        assert "officers" in data
        assert data["count"] == 1

def test_active_gsmb_officers_success(client, valid_token):
    with patch('services.gsmb_managemnt_service.GsmbManagmentService.activate_gsmb_officer',
               return_value=(True, None)):
        response = client.put('/gsmb-management/active-gsmb-officers/5', headers={"Authorization": valid_token})
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] is True
        assert data['id'] == 5
        assert data['new_status'] == 1
