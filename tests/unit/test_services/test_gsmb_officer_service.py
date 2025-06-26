
import pytest
from unittest.mock import patch, MagicMock
from services.gsmb_officer_service import GsmbOfficerService
from io import BytesIO
import json


@pytest.mark.usefixtures("mock_env")
def test_get_mlowners():
    # Sample users data returned from Redmine
    mock_users_response = {
        "users": [
            {
                "id": 101,
                "firstname": "John",
                "lastname": "Doe",
                "mail": "john.doe@example.com",
                "custom_fields": [
                    {"name": "User Type", "value": "mlOwner"},
                    {"name": "National Identity Card", "value": "987654321V"},
                    {"name": "Mobile Number", "value": "0712345678"}
                ]
            },
            {
                "id": 102,
                "firstname": "Jane",
                "lastname": "Smith",
                "mail": "jane.smith@example.com",
                "custom_fields": [
                    {"name": "User Type", "value": "otherUser"},
                    {"name": "National Identity Card", "value": "123456789V"},
                    {"name": "Mobile Number", "value": "0771234567"}
                ]
            }
        ]
    }

    # Mock license counts returned from get_mining_license_counts
    mock_license_counts = {
        "John Doe": 3
    }

    with patch("services.gsmb_officer_service.requests.get") as mock_get, \
         patch.object(GsmbOfficerService, "get_mining_license_counts", return_value=(mock_license_counts, None)) as mock_license_counts_fn:

        # Mock Redmine users API call
        mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=mock_users_response))

        # Call the method under test
        result, error = GsmbOfficerService.get_mlowners("fake-jwt-token")

        # Assertions
        assert error is None
        assert result is not None
        assert isinstance(result, list)

        # Only John Doe (mlOwner) should be in the results
        assert len(result) == 1
        ml_owner = result[0]

        assert ml_owner["id"] == 101
        assert ml_owner["ownerName"] == "John Doe"
        assert ml_owner["NIC"] == "987654321V"
        assert ml_owner["email"] == "john.doe@example.com"
        assert ml_owner["phoneNumber"] == "0712345678"
        assert ml_owner["totalLicenses"] == 3

        # Ensure get_mining_license_counts was called once
        mock_license_counts_fn.assert_called_once_with("fake-jwt-token")

@pytest.mark.usefixtures("mock_env")
def test_get_tpls():
    # Sample Redmine issues response
    mock_issues_response = {
        "issues": [
            {
                "id": 1,
                "subject": "TPL Issue 1",
                "status": {"name": "Open"},
                "author": {"name": "Alice"},
                "tracker": {"name": "TPL"},
                "assigned_to": {"name": "Bob"},
                "start_date": "2025-06-01",
                "due_date": "2025-06-10",
                "custom_fields": [
                    {"name": "Lorry Number", "value": "ABC-1234"},
                    {"name": "Driver Contact", "value": "0712345678"},
                    {"name": "Cubes", "value": "5.0"},
                    {"name": "Mining issue id", "value": "ML-2025-001"},
                    {"name": "Destination", "value": "Colombo"}
                ]
            }
        ]
    }

    # Mock the API key extracted from JWT
    with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_officer_service.requests.get") as mock_get, \
         patch.object(GsmbOfficerService, "get_custom_field_value") as mock_get_custom_field:

        # Setup get_custom_field_value to simulate correct field retrieval
        def side_effect(custom_fields, field_name):
            for field in custom_fields:
                if field["name"] == field_name:
                    return field["value"]
            return None

        mock_get_custom_field.side_effect = side_effect

        # Mock Redmine API response
        mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=mock_issues_response))

        # Call the service method
        result, error = GsmbOfficerService.get_tpls("fake-jwt-token")

        # Assertions
        assert error is None
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1

        tpl = result[0]
        assert tpl["id"] == 1
        assert tpl["subject"] == "TPL Issue 1"
        assert tpl["status"] == "Open"
        assert tpl["author"] == "Alice"
        assert tpl["tracker"] == "TPL"
        assert tpl["assigned_to"] == "Bob"
        assert tpl["start_date"] == "2025-06-01"
        assert tpl["due_date"] == "2025-06-10"
        assert tpl["lorry_number"] == "ABC-1234"
        assert tpl["driver_contact"] == "0712345678"
        assert tpl["cubes"] == "5.0"
        assert tpl["mining_license_number"] == "ML-2025-001"
        assert tpl["destination"] == "Colombo"

        # Confirm that get_custom_field_value was called for each custom field
        expected_fields = [
            "Lorry Number",
            "Driver Contact",
            "Cubes",
            "Mining issue id",
            "Destination"
        ]
        for field_name in expected_fields:
            mock_get_custom_field.assert_any_call(mock_issues_response["issues"][0]["custom_fields"], field_name)

@pytest.mark.usefixtures("mock_env")
def test_get_mining_licenses():
    # Sample Redmine mining licenses response
    mock_issues_response = {
        "issues": [
            {
                "id": 1,
                "status": {"name": "Active"},
                "assigned_to": {"name": "Inspector John"},
                "start_date": "2025-06-01",
                "due_date": "2025-06-30",
                "custom_fields": [
                    {"name": "Divisional Secretary Division", "value": "Kandy"},
                    {"name": "Capacity", "value": "1000"},
                    {"name": "Used", "value": "500"},
                    {"name": "Remaining", "value": "500"},
                    {"name": "Royalty", "value": "15000"},
                    {"name": "Mining License Number", "value": "ML-2025-001"},
                    {"name": "Mobile Number", "value": "0712345678"}
                ]
            }
        ]
    }

    with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_officer_service.requests.get") as mock_get, \
         patch.object(GsmbOfficerService, "get_custom_field_value") as mock_get_custom_field, \
         patch.object(GsmbOfficerService, "get_attachment_urls", return_value={}) as mock_get_attachments, \
         patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

        # Setup get_custom_field_value to simulate correct field retrieval
        def side_effect(custom_fields, field_name):
            for field in custom_fields:
                if field["name"] == field_name:
                    return field["value"]
            return None

        mock_get_custom_field.side_effect = side_effect

        # Mock Redmine API response
        mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=mock_issues_response))

        # Call the service method
        result, error = GsmbOfficerService.get_mining_licenses("fake-jwt-token")

        # Assertions
        assert error is None
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1

        ml = result[0]
        assert ml["id"] == 1
        assert ml["status"] == "Active"
        assert ml["assigned_to"] == "Inspector John"
        assert ml["start_date"] == "2025-06-01"
        assert ml["due_date"] == "2025-06-30"
        assert ml["divisional_secretary_division"] == "Kandy"
        assert ml["capacity"] == "1000"
        assert ml["used"] == "500"
        assert ml["remaining"] == "500"
        assert ml["royalty"] == "15000"
        assert ml["mining_license_number"] == "ML-2025-001"
        assert ml["mobile_number"] == "0712345678"

        # Confirm that get_custom_field_value was called for each field
        expected_fields = [
            "Divisional Secretary Division",
            "Capacity",
            "Used",
            "Remaining",
            "Royalty",
            "Mining License Number",
            "Mobile Number"
        ]
        for field_name in expected_fields:
            mock_get_custom_field.assert_any_call(mock_issues_response["issues"][0]["custom_fields"], field_name)

        # Confirm that get_attachment_urls was called
        mock_get_attachments.assert_called_once_with(
            "fake-api-key",
            "https://redmine.example.com",
            mock_issues_response["issues"][0]["custom_fields"]
        )

@pytest.mark.usefixtures("mock_env")
def test_get_mining_license_by_id_success():
    # 🧪 Sample Redmine issue response
    mock_issue_response = {
        "issue": {
            "id": 1,
            "subject": "Mining License 001",
            "status": {"name": "Active"},
            "author": {"name": "Officer Alice"},
            "assigned_to": {"name": "Inspector John"},
            "start_date": "2025-06-01",
            "due_date": "2025-06-30",
            "custom_fields": [
                {"name": "Exploration Licence No", "value": "EXPL-123"},
                {"name": "Land Name(Licence Details)", "value": "Green Hill"},
                {"name": "Land owner name", "value": "Mr. Silva"},
                {"name": "Name of village ", "value": "Kandy"},
                {"name": "Grama Niladhari Division", "value": "GN-45"},
                {"name": "Divisional Secretary Division", "value": "Kandy"},
                {"name": "Administrative District", "value": "Kandy District"},
                {"name": "Capacity", "value": "1000"},
                {"name": "Used", "value": "500"},
                {"name": "Remaining", "value": "500"},
                {"name": "Royalty", "value": "15000"},
                {"name": "Mining License Number", "value": "ML-2025-001"},
                {"name": "Mobile Number", "value": "0712345678"},
                {"name": "Reason For Hold", "value": "Pending Clearance"}
            ]
        }
    }

    # 🌟 Mock attachments
    mock_attachments = {
        "Economic Viability Report": "http://example.com/economic_report.pdf",
        "License fee receipt": "http://example.com/license_fee.pdf",
        "Detailed Mine Restoration Plan": "http://example.com/restoration_plan.pdf",
        "Deed and Survey Plan": "http://example.com/deed.pdf",
        "Payment Receipt": "http://example.com/payment_receipt.pdf",
        "License Boundary Survey": "http://example.com/boundary_survey.pdf"
    }

    with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_officer_service.requests.get") as mock_get, \
         patch.object(GsmbOfficerService, "get_attachment_urls", return_value=mock_attachments), \
         patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

        # Mock the Redmine API response
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = mock_issue_response
        mock_get.return_value = mock_response

        # Act
        result, error = GsmbOfficerService.get_mining_license_by_id("fake-token", 1)

        # Assert no errors
        assert error is None
        assert result is not None
        assert isinstance(result, dict)
        assert result["id"] == 1
        assert result["subject"] == "Mining License 001"
        assert result["status"] == "Active"
        assert result["author"] == "Officer Alice"
        assert result["assigned_to"] == "Inspector John"
        assert result["start_date"] == "2025-06-01"
        assert result["due_date"] == "2025-06-30"
        assert result["exploration_licence_no"] == "EXPL-123"
        assert result["land_name"] == "Green Hill"
        assert result["land_owner_name"] == "Mr. Silva"
        assert result["village_name"] == "Kandy"
        assert result["grama_niladhari_division"] == "GN-45"
        assert result["divisional_secretary_division"] == "Kandy"
        assert result["administrative_district"] == "Kandy District"
        assert result["capacity"] == "1000"
        assert result["used"] == "500"
        assert result["remaining"] == "500"
        assert result["royalty"] == "15000"
        assert result["license_number"] == "ML-2025-001"
        assert result["mining_license_number"] == "ML-2025-001"
        assert result["mobile_number"] == "0712345678"
        assert result["reason_for_hold"] == "Pending Clearance"

        # 📝 Check that attachment URLs are included
        assert result["economic_viability_report"] == mock_attachments["Economic Viability Report"]
        assert result["license_fee_receipt"] == mock_attachments["License fee receipt"]
        assert result["detailed_mine_restoration_plan"] == mock_attachments["Detailed Mine Restoration Plan"]
        assert result["deed_and_survey_plan"] == mock_attachments["Deed and Survey Plan"]
        assert result["payment_receipt"] == mock_attachments["Payment Receipt"]
        assert result["license_boundary_survey"] == mock_attachments["License Boundary Survey"]

        # 🔍 Confirm that get_attachment_urls was called with correct arguments
        mock_get.assert_called_once_with(
            "https://redmine.example.com/issues/1.json?include=attachments",
            headers={"X-Redmine-API-Key": "fake-api-key", "Content-Type": "application/json"}
        )
        GsmbOfficerService.get_attachment_urls.assert_called_once_with(
            "fake-api-key",
            "https://redmine.example.com",
            mock_issue_response["issue"]["custom_fields"]
        )

@pytest.mark.usefixtures("mock_env")
def test_get_complaints():
    mock_issues_response = {
        "issues": [
            {
                "id": 123,
                "created_on": "2025-06-01T10:00:00Z",
                "custom_fields": [
                    {"name": "Lorry Number", "value": "NB-1234"},
                    {"name": "Mobile Number", "value": "0771234567"},
                    {"name": "Role", "value": "Driver"},
                    {"name": "Resolved", "value": "Yes"}
                ]
            }
        ]
    }

    with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_officer_service.requests.get") as mock_get, \
         patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

        mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=mock_issues_response))

        complaints, error = GsmbOfficerService.get_complaints("fake-token")

        assert error is None
        assert complaints is not None
        assert len(complaints) == 1

        complaint = complaints[0]
        assert complaint["id"] == 123
        assert complaint["lorry_number"] == "NB-1234"
        assert complaint["mobile_number"] == "0771234567"
        assert complaint["role"] == "Driver"
        assert complaint["resolved"] == "Yes"
        assert complaint["complaint_date"] == "2025-06-01 10:00:00"

def test_get_attachment_urls():
    custom_fields = [
        {"name": "Economic Viability Report", "value": "101"},
        {"name": "Professional", "value": "102"},
        {"name": "Some Irrelevant Field", "value": "999"}
    ]

    # Since the method returns IDs as integers, expected values should be ints
    expected_urls = {
        "Economic Viability Report": 101,
        "Professional": 102,
    }

    urls = GsmbOfficerService.get_attachment_urls("fake-api-key", "https://redmine.example.com", custom_fields)

    for key, expected_value in expected_urls.items():
        assert urls[key] == expected_value

    # Also check that irrelevant fields are not included
    assert "Some Irrelevant Field" not in urls

def test_get_custom_field_value():
    custom_fields = [
        {"name": "Mobile Number", "value": "0711111111"},
        {"name": "License Number", "value": "LIC-123"}
    ]

    value = GsmbOfficerService.get_custom_field_value(custom_fields, "Mobile Number")
    assert value == "0711111111"

    value = GsmbOfficerService.get_custom_field_value(custom_fields, "License Number")
    assert value == "LIC-123"

    value = GsmbOfficerService.get_custom_field_value(custom_fields, "Non-Existent Field")
    assert value is None


@pytest.mark.usefixtures("mock_env")
def test_get_mining_license_counts():
    mock_issues_response = {
        "issues": [
            {"id": 1, "assigned_to": {"name": "Officer A"}},
            {"id": 2, "assigned_to": {"name": "Officer A"}},
            {"id": 3, "assigned_to": {"name": "Officer B"}},
            {"id": 4}  # No assigned_to -> should be counted under "Unassigned"
        ]
    }

    with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
         patch("services.gsmb_officer_service.requests.get") as mock_get, \
         patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

        mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=mock_issues_response))

        counts, error = GsmbOfficerService.get_mining_license_counts("fake-token")


