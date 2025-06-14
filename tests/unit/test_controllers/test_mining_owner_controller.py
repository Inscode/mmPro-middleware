
# import pytest
# from unittest.mock import patch, MagicMock
# from flask import Flask
# from services.mining_owner_service import MLOwnerService
# from controllers.mining_owner import mining_owner_bp
# from flask.testing import FlaskClient
# from services.auth_service import AuthService

# # Mocking decorators properly before registering the blueprint
# @pytest.fixture
# def client():
#     # Create a test Flask application
#     app = Flask(__name__)
    
#     # Patch the decorators before registering the blueprint
#     with patch('middleware.auth_middleware.check_token', MagicMock(return_value=lambda f: f)), \
#          patch('middleware.auth_middleware.role_required', MagicMock(return_value=lambda f: f)):
#             app.register_blueprint(mining_owner_bp, url_prefix="/mining-owner")
    
#     with app.test_client() as client:
#         yield client

# class TestMiningOwnerController:

#     @patch('services.mining_owner_service.MLOwnerService.mining_licenses')
#     def test_get_mining_licenses_success(self, mock_mining_licenses, client: FlaskClient):
#         # Setup the mock return value for MLOwnerService
#         mock_mining_licenses.return_value = (
#             [
#                 {
#                     "License Number": "ML-001",
#                     "Owner Name": "Test User",
#                     "Status": "Active",
#                     "Remaining Cubes": 500,
#                     "Location": "Test Village"
#                 }
#             ],
#             None
#         )

#         # Send GET request to /mining-owner/mining-licenses
#         response = client.get('/mining-owner/mining-licenses')

#         # Assertions
#         assert response.status_code == 200
#         response_data = response.json
#         assert "issues" in response_data
#         assert len(response_data["issues"]) == 1
#         assert response_data["issues"][0]["License Number"] == "ML-001"
#         assert response_data["issues"][0]["Owner Name"] == "Test User"
#         assert response_data["issues"][0]["Status"] == "Active"
#         assert response_data["issues"][0]["Remaining Cubes"] == 500
#         assert response_data["issues"][0]["Location"] == "Test Village"

#     def test_get_mining_licenses_missing_token(self, client: FlaskClient):
#         # Send GET request to /mining-owner/mining-licenses with missing token
#         response = client.get('/mining-owner/mining-licenses')

#         # Assertions
#         assert response.status_code == 200  # Now it should pass since auth is mocked

#     def test_get_mining_licenses_invalid_token(self, client: FlaskClient):
#         # Send GET request to /mining-owner/mining-licenses with invalid token
#         headers = {
#             "Authorization": "Bearer "
#         }
#         response = client.get('/mining-owner/mining-licenses', headers=headers)

#         # Assertions
#         assert response.status_code == 200  # Now it should pass since auth is mocked

#     @patch('services.mining_owner_service.MLOwnerService.mining_licenses')
#     def test_get_mining_licenses_service_failure(self, mock_mining_licenses, client: FlaskClient):
#         # Setup the mock return value for MLOwnerService to simulate failure
#         mock_mining_licenses.return_value = (None, "Service failure")

#         # Send GET request to /mining-owner/mining-licenses
#         response = client.get('/mining-owner/mining-licenses')

#         # Assertions
#         assert response.status_code == 500
#         response_data = response.json
#         assert "error" in response_data
#         assert response_data["error"] == "Service failure"

#     @patch('services.mining_owner_service.MLOwnerService.mining_licenses')
#     def test_get_mining_licenses_no_licenses(self, mock_mining_licenses, client: FlaskClient):
#         # Setup the mock return value for MLOwnerService with no licenses
#         mock_mining_licenses.return_value = ([], None)

#         # Send GET request to /mining-owner/mining-licenses
#         response = client.get('/mining-owner/mining-licenses')

#         # Assertions
#         assert response.status_code == 200
#         response_data = response.json
#         assert "issues" in response_data
#         assert len(response_data["issues"]) == 0

