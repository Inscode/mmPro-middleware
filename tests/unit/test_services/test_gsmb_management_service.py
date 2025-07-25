import pytest
from unittest.mock import patch, Mock
from services.gsmb_managemnt_service import GsmbManagmentService  # replace with actual import path
from flask import Response
from datetime import datetime, timedelta

@pytest.mark.usefixtures("mock_env")
def test_monthly_total_sand_cubes():
    mock_issues_page1 = {
        "issues": [
            {
                "created_on": "2025-01-15T12:34:56Z",
                "custom_fields": [
                    {"id": 58, "name": "Cubes", "value": "2.5"}
                ]
            },
            {
                "created_on": "2025-02-10T09:00:00Z",
                "custom_fields": [
                    {"id": 58, "name": "Cubes", "value": "3.0"}
                ]
            }
        ]
    }

    mock_issues_page2 = {"issues": []}  # End of pagination

    with patch("utils.jwt_utils.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_managemnt_service.requests.get") as mock_get:

        mock_get.side_effect = [
            Mock(status_code=200, json=Mock(return_value=mock_issues_page1)),
            Mock(status_code=200, json=Mock(return_value=mock_issues_page2)),
        ]

        result, error = GsmbManagmentService.monthly_total_sand_cubes("fake-jwt-token")

        assert error is None
        assert result is not None

        # Validate January and February
        jan = next((r for r in result if r["month"] == "Jan"), None)
        feb = next((r for r in result if r["month"] == "Feb"), None)

        assert jan["totalCubes"] == 2.5
        assert feb["totalCubes"] == 3.0

        # Validate other months are 0
        for r in result:
            if r["month"] not in ["Jan", "Feb"]:
                assert r["totalCubes"] == 0

@pytest.mark.usefixtures("mock_env")
def test_fetch_top_mining_holders():
    mock_issues_page1 = {
        "issues": [
            {
                "assigned_to": {"name": "Company A"},
                "custom_fields": [
                    {"name": "Capacity", "value": "100"},
                    {"name": "Used", "value": "75"}
                ]
            },
            {
                "assigned_to": {"name": "Company B"},
                "custom_fields": [
                    {"name": "Capacity", "value": "200"},
                    {"name": "Used", "value": "50"}
                ]
            }
        ]
    }

    mock_issues_page2 = {"issues": []}  # End of pagination

    with patch("utils.jwt_utils.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_managemnt_service.requests.get") as mock_get:

        # Simulate paginated API response
        mock_get.side_effect = [
            Mock(status_code=200, json=Mock(return_value=mock_issues_page1)),
            Mock(status_code=200, json=Mock(return_value=mock_issues_page2)),
        ]

        result, error = GsmbManagmentService.fetch_top_mining_holders("fake-jwt-token")

        assert error is None
        assert result is not None
        assert len(result) == 2

        # Ensure result is sorted by capacity descending
        assert result[0]["label"] == "Company B"
        assert result[0]["capacity"] == 200
        assert result[0]["value"] == 25.0  # 50/200 = 25%

        assert result[1]["label"] == "Company A"
        assert result[1]["capacity"] == 100
        assert result[1]["value"] == 75.0  # 75/100 = 75%

@pytest.mark.usefixtures("mock_env")
def test_fetch_royalty_counts_success(app):
    mock_issues_page1 = {
        "issues": [
            {
                "tracker": {"id": 4, "name": "ML"},
                "status": {"name": "Valid"},
                "assigned_to": {"name": "Company A"},
                "custom_fields": [{"name": "Royalty", "value": "1200"}]
            },
            {
                "tracker": {"id": 4, "name": "ML"},
                "status": {"name": "Valid"},
                "assigned_to": {"name": "Company B"},
                "custom_fields": [{"name": "Royalty", "value": "800"}]
            }
        ]
    }

    mock_issues_page2 = {"issues": []}  # Simulate end of pagination

    with app.app_context(), \
         patch("utils.jwt_utils.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_managemnt_service.requests.get") as mock_get:

        mock_get.side_effect = [
            Mock(status_code=200, json=Mock(return_value=mock_issues_page1)),
            Mock(status_code=200, json=Mock(return_value=mock_issues_page2)),
        ]

        # Service returns (response, error) tuple
        response, error = GsmbManagmentService.fetch_royalty_counts("fake-jwt-token")
        
        # Check error is None
        assert error is None
        
        # Verify response is a Flask Response
        assert isinstance(response, Response)
        assert response.status_code == 200
        
        # Get the JSON data from the response
        data = response.get_json()
        
        # Now make assertions on the data
        assert data is not None
        assert "total_royalty" in data
        assert data["total_royalty"] == 2000
        assert len(data["orders"]) == 2

        # Ensure result is sorted by royalty descending
        assert data["orders"][0]["title"] == "Company A"
        assert data["orders"][0]["royalty_value"] == 1200

        assert data["orders"][1]["title"] == "Company B"
        assert data["orders"][1]["royalty_value"] == 800

@pytest.mark.usefixtures("mock_env")
def test_monthly_mining_license_count_success():
    # Mock data
    mock_issues_page1 = {
        "issues": [
            {
                "tracker": {"id": 4, "name": "ML"},
                "created_on": "2023-01-15T12:34:56Z"
            },
            {
                "tracker": {"id": 4, "name": "ML"},
                "created_on": "2023-01-20T10:00:00Z"
            },
            {
                "tracker": {"id": 4, "name": "ML"},
                "created_on": "2023-02-10T09:00:00Z"
            },
            {
                "tracker": {"id": 5, "name": "Other"},  # Should be filtered out
                "created_on": "2023-01-25T11:00:00Z"
            }
        ]
    }

    mock_issues_page2 = {"issues": []}  # End of pagination

    with patch("utils.jwt_utils.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_managemnt_service.requests.get") as mock_get:

        # Set up mock responses
        mock_get.side_effect = [
            Mock(status_code=200, json=Mock(return_value=mock_issues_page1)),
            Mock(status_code=200, json=Mock(return_value=mock_issues_page2)),
        ]

        # Call the method
        result, error = GsmbManagmentService.monthly_mining_license_count("fake-token")

        # Assertions
        assert error is None
        assert result is not None
        
        # Find January and February in results
        jan = next((item for item in result if item["month"] == "Jan"), None)
        feb = next((item for item in result if item["month"] == "Feb"), None)
        
        # Verify counts
        assert jan["miningLicense"] == 2  # Two licenses in January
        assert feb["miningLicense"] == 1  # One license in February
        
        # Verify other months are 0
        for month_data in result:
            if month_data["month"] not in ["Jan", "Feb"]:
                assert month_data["miningLicense"] == 0

@pytest.mark.usefixtures("mock_env")
def test_transport_license_destination_success():
    mock_issues_page1 = {
        "issues": [
            {
                "custom_fields": [{"name": "Destination", "value": "Colombo"}]
            },
            {
                "custom_fields": [{"name": "Destination", "value": "Galle"}]
            },
            {
                "custom_fields": [{"name": "Destination", "value": "Colombo"}]
            }
        ]
    }

    mock_issues_page2 = {"issues": []}  # Simulate end of pagination

    with patch("utils.jwt_utils.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_managemnt_service.requests.get") as mock_get:

        # Mocking paginated response
        mock_get.side_effect = [
            Mock(status_code=200, json=Mock(return_value=mock_issues_page1)),
            Mock(status_code=200, json=Mock(return_value=mock_issues_page2)),
        ]

        result, error = GsmbManagmentService.transport_license_destination("fake-token")

        assert error is None
        assert result is not None

        # Sort result for consistent testing
        sorted_result = sorted(result, key=lambda x: x["name"])

        assert sorted_result == [
            {"name": "Colombo", "value": 2},
            {"name": "Galle", "value": 1}
        ]

@pytest.mark.usefixtures("mock_env")
def test_total_location_ml_success():
    mock_issues_page1 = {
        "issues": [
            {
                "custom_fields": [{"name": "Administrative District", "value": "Colombo"}]
            },
            {
                "custom_fields": [{"name": "Administrative District", "value": "Galle"}]
            },
            {
                "custom_fields": [{"name": "Administrative District", "value": "Colombo"}]
            }
        ]
    }

    mock_issues_page2 = {"issues": []}  # End of pagination

    with patch("utils.jwt_utils.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_managemnt_service.requests.get") as mock_get:

        # Simulate paginated Redmine responses
        mock_get.side_effect = [
            Mock(status_code=200, json=Mock(return_value=mock_issues_page1)),
            Mock(status_code=200, json=Mock(return_value=mock_issues_page2))
        ]

        result, error = GsmbManagmentService.total_location_ml("fake-token")

        assert error is None
        assert result is not None

        # Sort for consistent order
        sorted_result = sorted(result, key=lambda x: x["name"])
        assert sorted_result == [
            {"name": "Colombo", "value": 2},
            {"name": "Galle", "value": 1}
        ]

@pytest.mark.usefixtures("mock_env")
def test_complaint_counts_success():

    mock_page1 = {
        "issues": [
            {"status": {"name": "New"}},
            {"status": {"name": "Rejected"}},
            {"status": {"name": "In Progress"}},
            {"status": {"name": "Executed"}},
            {"status": {"name": "New"}}
        ]
    }

    mock_page2 = {"issues": []}  # End of pagination

    with patch("utils.jwt_utils.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_managemnt_service.requests.get") as mock_get:

        mock_get.side_effect = [
            Mock(status_code=200, json=Mock(return_value=mock_page1)),
            Mock(status_code=200, json=Mock(return_value=mock_page2))
        ]

        result, error = GsmbManagmentService.complaint_counts("fake-token")

        assert error is None
        assert result == {
            "New": 2,
            "Rejected": 1,
            "InProgress": 1,
            "Executed": 1,
            "total": 5
        }


@pytest.mark.usefixtures("mock_env")
def test_role_counts_success(monkeypatch):
    monkeypatch.setenv("REDMINE_URL", "https://fake-redmine-url")

    mock_page1 = {
        "memberships": [
            {"roles": [{"name": "MLOwner"}]},
            {"roles": [{"name": "GSMBOfficer"}]},
            {"roles": [{"name": "PoliceOfficer"}]},
            {"roles": [{"name": "miningEngineer"}]},
            {"roles": [{"name": "MLOwner"}]}
        ]
    }

    mock_page2 = {"memberships": []}  # End of pagination

    with patch("utils.jwt_utils.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_managemnt_service.requests.get") as mock_get:

        mock_get.side_effect = [
            Mock(status_code=200, json=Mock(return_value=mock_page1)),
            Mock(status_code=200, json=Mock(return_value=mock_page2))
        ]

        result, error = GsmbManagmentService.role_counts("fake-token")

        assert error is None
        assert result == {
            "licenceOwner": 2,
            "activeGSMBOfficers": 1,
            "policeOfficers": 1,
            "miningEngineer": 1,
            "total_count": 5
        }

@pytest.mark.usefixtures("mock_env")
def test_mining_license_count_success():

    mock_page1 = {
        "issues": [
            {"status": {"name": "Valid"}},
            {"status": {"name": "Expired"}},
            {"status": {"name": "Rejected"}},
            {"status": {"name": "Valid"}}
        ]
    }

    mock_page2 = {"issues": []}  # End of pagination

    with patch("utils.jwt_utils.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_managemnt_service.requests.get") as mock_get:

        mock_get.side_effect = [
            Mock(status_code=200, json=Mock(return_value=mock_page1)),
            Mock(status_code=200, json=Mock(return_value=mock_page2))
        ]

        result, error = GsmbManagmentService.mining_license_count("fake-token")

        assert error is None
        assert result == {
            "valid": 2,
            "expired": 1,
            "rejected": 1,
            "total": 4
        }

def test_unactive_gsmb_officers_success():

    mock_users_response = {
        "users": [
            {
                "id": 1,
                "firstname": "John",
                "lastname": "Doe",
                "mail": "john.doe@example.com",
                "status": 3,
                "custom_fields": [
                    {"name": "Designation", "value": "Officer"},
                    {"name": "Mobile Number", "value": "123456789"},
                    {"name": "NIC back image", "value": "nic-back.jpg"},
                    {"name": "NIC front image", "value": "nic-front.jpg"},
                    {"name": "National Identity Card", "value": "NIC123456"},
                    {"name": "User Type", "value": "GSMB"},
                    {"name": "work ID", "value": "work-id.jpg"}
                ]
            }
        ]
    }

    # Mock attachment URLs
    mock_attachment_urls = {
        "NIC back image": "https://fake-redmine-url/attachments/nic-back.jpg",
        "NIC front image": "https://fake-redmine-url/attachments/nic-front.jpg",
        "work ID": "https://fake-redmine-url/attachments/work-id.jpg"
    }

    with patch("utils.jwt_utils.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_managemnt_service.requests.get", return_value=Mock(status_code=200, json=lambda: mock_users_response)), \
         patch("services.gsmb_managemnt_service.GsmbManagmentService.get_attachment_urls", return_value=mock_attachment_urls):

        result, error = GsmbManagmentService.unactive_gsmb_officers("fake-token")

        assert error is None
        assert result["count"] == 1
        assert result["officers"][0]["name"] == "John Doe"
        assert result["officers"][0]["custom_fields"]["Designation"] == "Officer"


def test_license_expired_with_past_date():
    past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    service = GsmbManagmentService()
    assert service.is_license_expired(past_date) is True

def test_license_expired_with_future_date():
    future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    service = GsmbManagmentService()
    assert service.is_license_expired(future_date) is False


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("REDMINE_URL", "https://fake-redmine.com")


@pytest.fixture
def test_activate_gsmb_officer_success():

    user_id = 1
    token = "fake-token"
    update_data = {"status": 1}

    # Patch JWTUtils.get_api_key_from_token
    with patch("utils.jwt_utils.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_managemnt_service.requests.put") as mock_put:

        mock_put.return_value = Mock(status_code=204)

        result, error = GsmbManagmentService.activate_gsmb_officer(token, user_id, update_data)

        assert error is None
        assert result == {"status": "success", "message": "User activated successfully"}

def test_get_custom_field_value_found():
    custom_fields = [
        {"name": "Designation", "value": "Officer"},
        {"name": "Mobile Number", "value": "123456789"}
    ]
    value = GsmbManagmentService.get_custom_field_value(custom_fields, "Designation")
    assert value == "Officer"

def test_get_custom_field_value_not_found():
    custom_fields = [
        {"name": "Designation", "value": "Officer"},
        {"name": "Mobile Number", "value": "123456789"}
    ]
    value = GsmbManagmentService.get_custom_field_value(custom_fields, "NonExistentField")
    assert value is None