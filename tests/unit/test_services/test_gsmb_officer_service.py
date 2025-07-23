
import pytest
from unittest.mock import patch, MagicMock
from services.gsmb_officer_service import GsmbOfficerService
from io import BytesIO
import json
import os



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
        "Economic Viability Report": "https://example.com/economic_report.pdf",
        "License fee receipt": "https://example.com/license_fee.pdf",
        "Detailed Mine Restoration Plan": "https://example.com/restoration_plan.pdf",
        "Deed and Survey Plan": "https://example.com/deed.pdf",
        "Payment Receipt": "https://example.com/payment_receipt.pdf",
        "License Boundary Survey": "https://example.com/boundary_survey.pdf"
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


class MockFile:
    def __init__(self, filename, content):
        self.filename = filename
        self.stream = BytesIO(content)


class TestUploadFileToRedmine:

    @patch.dict(os.environ, {
        "REDMINE_URL": "https://test.redmine.com",
        "REDMINE_ADMIN_API_KEY": "admin_key"
    })
    @patch("services.gsmb_officer_service.requests.post")  # ✅ correct path
    def test_successful_upload(self, mock_post):
        test_file = MockFile("test.pdf", b"dummy content")

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "upload": {"id": 12345}
        }
        mock_post.return_value = mock_response

        result = GsmbOfficerService.upload_file_to_redmine(test_file)

        assert result == 12345
        mock_post.assert_called_once()
        assert "uploads.json?filename=test.pdf" in mock_post.call_args[0][0]

    @patch.dict(os.environ, {
        "REDMINE_URL": "https://test.redmine.com",
        "REDMINE_ADMIN_API_KEY": "admin_key"
    })
    @patch("services.gsmb_officer_service.requests.post")
    def test_failed_upload(self, mock_post):
        test_file = MockFile("test.pdf", b"dummy content")

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        result = GsmbOfficerService.upload_file_to_redmine(test_file)
        assert result is None

    @patch("services.gsmb_officer_service.requests.post")
    def test_missing_env_variables(self, mock_post):
        with patch.dict(os.environ, {}, clear=True):
            test_file = MockFile("test.pdf", b"dummy content")
            # Simulate missing env vars gracefully
            try:
                result = GsmbOfficerService.upload_file_to_redmine(test_file)
                assert result is None
            except Exception:
                pytest.fail("upload_file_to_redmine() raised unexpectedly!")


@pytest.fixture
def mock_data():
    return {
        "exploration_licence_no": "EXP123",
        "land_name": "Sample Land",
        "village_name": "Village X",
        "grama_niladhari_division": "GND Y",
        "divisional_secretary_division": "DSD Z",
        "administrative_district": "District A",
        "mobile_number": "0771234567",
        "land_owner_name": "Owner Name",
        "royalty": "1000",
        "capacity": "5000",
        "used": "1000",
        "remaining": "4000",
        "google_location": "https://maps.google.com/sample",
        "mining_license_number": "MLN001",
        "month_capacity": "200",
        "assignee_id": 55,
        "economic_viability_report": "file_token_1",
        "payment_receipt": "file_token_2",
        "subject": "Test Mining License",
        "start_date": "2025-06-01",
        "due_date": "2025-12-31",
        "author": "Test Officer"
    }


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.put")
@patch("services.gsmb_officer_service.requests.post")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_successful_upload(mock_api_key, mock_post, mock_put, mock_data):
    mock_api_key.return_value = "valid_api_key"

    # Mock POST: issue creation
    mock_post_response = MagicMock()
    mock_post_response.status_code = 201
    mock_post_response.json.return_value = {"issue": {"id": 101}}
    mock_post.return_value = mock_post_response

    # Mock PUT: updating license number
    mock_put_response = MagicMock()
    mock_put_response.status_code = 204
    mock_put.return_value = mock_put_response

    success, error = GsmbOfficerService.upload_mining_license("token", mock_data)
    assert success is True
    assert error is None
    mock_post.assert_called_once()
    mock_put.assert_called_once()


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.post")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_issue_creation_failed(mock_api_key, mock_post, mock_data):
    mock_api_key.return_value = "valid_api_key"

    mock_post_response = MagicMock()
    mock_post_response.status_code = 400
    mock_post_response.text = "Bad Request"
    mock_post.return_value = mock_post_response

    success, error = GsmbOfficerService.upload_mining_license("token", mock_data)
    assert success is False
    assert "Redmine issue creation failed" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.put")
@patch("services.gsmb_officer_service.requests.post")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_license_number_update_failed(mock_api_key, mock_post, mock_put, mock_data):
    mock_api_key.return_value = "valid_api_key"

    # POST is successful
    mock_post_response = MagicMock()
    mock_post_response.status_code = 201
    mock_post_response.json.return_value = {"issue": {"id": 202}}
    mock_post.return_value = mock_post_response

    # PUT fails
    mock_put_response = MagicMock()
    mock_put_response.status_code = 400
    mock_put_response.text = "Bad PUT"
    mock_put.return_value = mock_put_response

    success, error = GsmbOfficerService.upload_mining_license("token", mock_data)
    assert success is False
    assert "Failed to update Mining License Number" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_api_key(mock_api_key, mock_data):
    mock_api_key.return_value = None
    with patch("services.gsmb_officer_service.requests.post") as mock_post:
        success, error = GsmbOfficerService.upload_mining_license("token", mock_data)
        assert success is False
        assert "None" not in error  # Ensure error is readable


@patch("services.gsmb_officer_service.requests.post")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_redmine_url(mock_api_key, mock_post, mock_data):
    mock_api_key.return_value = "valid_api_key"
    with patch.dict(os.environ, {}, clear=True):
        success, error = GsmbOfficerService.upload_mining_license("token", mock_data)
        assert success is False
        assert "REDMINE_URL" in error or error is not None


@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_exception_handling(mock_api_key, mock_data):
    mock_api_key.side_effect = Exception("Unexpected error")
    success, error = GsmbOfficerService.upload_mining_license("token", mock_data)
    assert success is False
    assert "Unexpected error" in error


@pytest.fixture
def valid_data():
    return {
        "mining_request_id": 123,
        "comments": "Paid via online transfer.",
        "payment_receipt_id": "file_token_abc123"
    }


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.put")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_successful_upload(mock_api_key, mock_put):
    mock_api_key.return_value = "valid_api_key"

    valid_data = {
        "mining_request_id": 101,
        "comments": "Payment uploaded.",
        "payment_receipt_id": "file_token_abc123"
    }

    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_put.return_value = mock_response

    success, error = GsmbOfficerService.upload_payment_receipt("token", valid_data)

    assert success is True
    assert error is None
    mock_put.assert_called_once()
    assert "issues/101.json" in mock_put.call_args[0][0]



@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_fields(mock_api_key):
    mock_api_key.return_value = "valid_api_key"
    incomplete_data = {
        "comments": "Missing mining_request_id and receipt"
    }

    success, error = GsmbOfficerService.upload_payment_receipt("token", incomplete_data)
    assert success is False
    assert "Missing required fields" in error


@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_env_variable(mock_api_key, valid_data):
    mock_api_key.return_value = "valid_api_key"
    with patch.dict(os.environ, {}, clear=True):
        success, error = GsmbOfficerService.upload_payment_receipt("token", valid_data)
        assert success is False
        assert "REDMINE_URL" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.put")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_failed_api_call(mock_api_key, mock_put, valid_data):
    mock_api_key.return_value = "valid_api_key"

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_put.return_value = mock_response

    success, error = GsmbOfficerService.upload_payment_receipt("token", valid_data)
    assert success is False
    assert "Failed to update mining request" in error
    assert "400" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_exception_handling(mock_api_key, valid_data):
    mock_api_key.side_effect = Exception("JWT token parse failed")
    success, error = GsmbOfficerService.upload_payment_receipt("token", valid_data)
    assert success is False
    assert "JWT token parse failed" in error    



@pytest.fixture
def valid_data():
    return {
        "mining_request_id": 101
    }


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.put")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_successful_rejection(mock_api_key, mock_put, valid_data):
    mock_api_key.return_value = "valid_api_key"

    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_put.return_value = mock_response

    success, error = GsmbOfficerService.reject_mining_request("token", valid_data)

    assert success is True
    assert error is None
    mock_put.assert_called_once()
    assert "issues/101.json" in mock_put.call_args[0][0]


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_mining_request_id(mock_api_key):
    mock_api_key.return_value = "valid_api_key"
    data = {}

    success, error = GsmbOfficerService.reject_mining_request("token", data)
    assert success is False
    assert "Missing required field" in error


@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_redmine_url(mock_api_key, valid_data):
    mock_api_key.return_value = "valid_api_key"
    with patch.dict(os.environ, {}, clear=True):
        success, error = GsmbOfficerService.reject_mining_request("token", valid_data)
        assert success is False
        assert "REDMINE_URL" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.put")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_failed_api_call(mock_api_key, mock_put, valid_data):
    mock_api_key.return_value = "valid_api_key"

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_put.return_value = mock_response

    success, error = GsmbOfficerService.reject_mining_request("token", valid_data)
    assert success is False
    assert "Failed to reject mining request" in error
    assert "400" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_exception_handling(mock_api_key, valid_data):
    mock_api_key.side_effect = Exception("Unexpected failure")

    success, error = GsmbOfficerService.reject_mining_request("token", valid_data)
    assert success is False
    assert "Unexpected failure" in error


@patch.dict(os.environ, {
    "REDMINE_URL": "https://test.redmine.com",
    "REDMINE_ADMIN_API_KEY": "admin_key"
})
@patch("services.gsmb_officer_service.requests.get")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_successful_fetch(mock_get_api_key, mock_requests_get):
    mock_get_api_key.return_value = "user_api_key"

    # First GET request (memberships)
    memberships_response = MagicMock()
    memberships_response.status_code = 200
    memberships_response.json.return_value = {
        "memberships": [
            {
                "user": {"id": 1},
                "roles": [{"name": "MLOwner"}]
            },
            {
                "user": {"id": 2},
                "roles": [{"name": "OtherRole"}]
            }
        ]
    }

    # Second GET request (users)
    users_response = MagicMock()
    users_response.status_code = 200
    users_response.json.return_value = {
        "users": [
            {
                "id": 1,
                "firstname": "John",
                "lastname": "Doe",
                "custom_fields": [
                    {"name": "National Identity Card", "value": "901234567V"}
                ]
            },
            {
                "id": 2,
                "firstname": "Jane",
                "lastname": "Smith",
                "custom_fields": []
            }
        ]
    }

    mock_requests_get.side_effect = [memberships_response, users_response]

    result, error = GsmbOfficerService.get_mlownersDetails("token")

    assert error is None
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["ownerName"] == "John Doe"
    assert result[0]["NIC"] == "901234567V"


@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_user_api_key(mock_get_api_key):
    mock_get_api_key.return_value = None
    result, error = GsmbOfficerService.get_mlownersDetails("token")
    assert result is None
    assert "Invalid or missing API key" in error


@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_env_vars(mock_get_api_key):
    mock_get_api_key.return_value = "valid_key"
    with patch.dict(os.environ, {}, clear=True):
        result, error = GsmbOfficerService.get_mlownersDetails("token")
        assert result is None
        assert "REDMINE_ADMIN_API_KEY" in error or "REDMINE_URL" in error


@patch.dict(os.environ, {
    "REDMINE_URL": "https://test.redmine.com",
    "REDMINE_ADMIN_API_KEY": "admin_key"
})
@patch("services.gsmb_officer_service.requests.get")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_membership_api_failure(mock_get_api_key, mock_requests_get):
    mock_get_api_key.return_value = "valid_key"

    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    mock_requests_get.return_value = mock_response

    result, error = GsmbOfficerService.get_mlownersDetails("token")
    assert result is None
    assert "Failed to fetch memberships" in error


@patch.dict(os.environ, {
    "REDMINE_URL": "https://test.redmine.com",
    "REDMINE_ADMIN_API_KEY": "admin_key"
})
@patch("services.gsmb_officer_service.requests.get")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_users_api_failure(mock_get_api_key, mock_requests_get):
    mock_get_api_key.return_value = "valid_key"

    # First call (memberships) succeeds
    memberships_response = MagicMock()
    memberships_response.status_code = 200
    memberships_response.json.return_value = {
        "memberships": [
            {"user": {"id": 1}, "roles": [{"name": "MLOwner"}]}
        ]
    }

    # Second call (users) fails
    users_response = MagicMock()
    users_response.status_code = 500
    users_response.text = "Internal Server Error"

    mock_requests_get.side_effect = [memberships_response, users_response]

    result, error = GsmbOfficerService.get_mlownersDetails("token")
    assert result is None
    assert "Failed to fetch user details" in error


@patch.dict(os.environ, {
    "REDMINE_URL": "https://test.redmine.com",
    "REDMINE_ADMIN_API_KEY": "admin_key"
})
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_exception_handling(mock_get_api_key):
    mock_get_api_key.side_effect = Exception("Something went wrong")

    result, error = GsmbOfficerService.get_mlownersDetails("token")
    assert result is None
    assert "Server error: Something went wrong" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.GsmbOfficerService.get_custom_field_value")
@patch("services.gsmb_officer_service.requests.get")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_successful_get_appointments(mock_get_api_key, mock_requests_get, mock_custom_field):
    mock_get_api_key.return_value = "valid_api_key"
    mock_custom_field.return_value = "ML/2024/001"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "issues": [
            {
                "id": 1,
                "subject": "Site Visit Appointment",
                "status": {"name": "Scheduled"},
                "author": {"name": "Officer A"},
                "tracker": {"name": "Appointment"},
                "assigned_to": {"name": "Engineer B"},
                "start_date": "2025-07-01",
                "due_date": "2025-07-01",
                "description": "Site visit for ML/2024/001",
                "custom_fields": [{"name": "Mining License Number", "value": "ML/2024/001"}]
            }
        ]
    }
    mock_requests_get.return_value = mock_response

    result, error = GsmbOfficerService.get_appointments("valid_token")

    assert error is None
    assert isinstance(result, list)
    assert result[0]["subject"] == "Site Visit Appointment"
    assert result[0]["mining_license_number"] == "ML/2024/001"


@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_api_key(mock_get_api_key):
    mock_get_api_key.return_value = None
    result, error = GsmbOfficerService.get_appointments("bad_token")
    assert result is None
    assert "Invalid or missing API key" in error


@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_redmine_url(mock_get_api_key):
    mock_get_api_key.return_value = "valid_api_key"
    with patch.dict(os.environ, {}, clear=True):
        result, error = GsmbOfficerService.get_appointments("valid_token")
        assert result is None
        assert "REDMINE_URL" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.get")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_api_failure(mock_get_api_key, mock_requests_get):
    mock_get_api_key.return_value = "valid_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_requests_get.return_value = mock_response

    result, error = GsmbOfficerService.get_appointments("valid_token")
    assert result is None
    assert "Failed to fetch appointment issues" in error
    assert "500" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_exception_handling(mock_get_api_key):
    mock_get_api_key.side_effect = Exception("Unexpected failure")

    result, error = GsmbOfficerService.get_appointments("token")
    assert result is None
    assert "Server error: Unexpected failure" in error


import os
import json
import pytest
from unittest.mock import patch, MagicMock
from services.gsmb_officer_service import GsmbOfficerService


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.put")
@patch("services.gsmb_officer_service.requests.post")
@patch("services.gsmb_officer_service.JWTUtils.decode_jwt_and_get_user_id")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_create_appointment_success(
    mock_get_api_key, mock_get_user_id, mock_post, mock_put
):
    mock_get_api_key.return_value = "valid_api_key"
    mock_get_user_id.return_value = 999

    # Mock successful POST
    mock_post_response = MagicMock()
    mock_post_response.status_code = 201
    mock_post_response.json.return_value = {"issue": {"id": 555}}
    mock_post.return_value = mock_post_response

    # Mock successful PUT
    mock_put_response = MagicMock()
    mock_put_response.status_code = 204
    mock_put.return_value = mock_put_response

    issue_id, error = GsmbOfficerService.create_appointment(
        "token", 888, "Colombo Office", "2025-07-15", "Meeting scheduled", 123
    )

    assert error is None
    assert issue_id == 555
    mock_post.assert_called_once()
    mock_put.assert_called_once()


@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
@patch("services.gsmb_officer_service.JWTUtils.decode_jwt_and_get_user_id")
def test_missing_api_key_or_user_id(mock_user_id, mock_api_key):
    mock_api_key.return_value = None
    mock_user_id.return_value = None
    issue_id, error = GsmbOfficerService.create_appointment(
        "token", 888, "Office", "2025-07-01", "Desc", 123
    )
    assert issue_id is None
    assert "Invalid or missing API key" in error


@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
@patch("services.gsmb_officer_service.JWTUtils.decode_jwt_and_get_user_id")
def test_missing_redmine_url(mock_user_id, mock_api_key):
    mock_api_key.return_value = "valid_key"
    mock_user_id.return_value = 101
    with patch.dict(os.environ, {}, clear=True):
        issue_id, error = GsmbOfficerService.create_appointment(
            "token", 888, "Office", "2025-07-01", "Desc", 123
        )
        assert issue_id is None
        assert "REDMINE_URL" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.post")
@patch("services.gsmb_officer_service.JWTUtils.decode_jwt_and_get_user_id")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_create_appointment_failure_on_post(mock_api_key, mock_user_id, mock_post):
    mock_api_key.return_value = "valid_key"
    mock_user_id.return_value = 1

    mock_post_response = MagicMock()
    mock_post_response.status_code = 400
    mock_post_response.text = "Bad Request"
    mock_post.return_value = mock_post_response

    issue_id, error = GsmbOfficerService.create_appointment(
        "token", 888, "Office", "2025-07-01", "Desc", 123
    )
    assert issue_id is None
    assert "Failed to create appointment" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.put")
@patch("services.gsmb_officer_service.requests.post")
@patch("services.gsmb_officer_service.JWTUtils.decode_jwt_and_get_user_id")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_create_appointment_failure_on_put(mock_api_key, mock_user_id, mock_post, mock_put):
    mock_api_key.return_value = "valid_key"
    mock_user_id.return_value = 1

    mock_post_response = MagicMock()
    mock_post_response.status_code = 201
    mock_post_response.json.return_value = {"issue": {"id": 777}}
    mock_post.return_value = mock_post_response

    mock_put_response = MagicMock()
    mock_put_response.status_code = 500
    mock_put_response.text = "PUT error"
    mock_put.return_value = mock_put_response

    issue_id, error = GsmbOfficerService.create_appointment(
        "token", 888, "Office", "2025-07-01", "Desc", 123
    )
    assert issue_id is None
    assert "Failed to update mining request" in error


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
@patch("services.gsmb_officer_service.JWTUtils.decode_jwt_and_get_user_id")
def test_exception_handling(mock_user_id, mock_api_key):
    mock_api_key.side_effect = Exception("Something went wrong")
    mock_user_id.return_value = 1

    issue_id, error = GsmbOfficerService.create_appointment(
        "token", 888, "Office", "2025-07-01", "Desc", 123
    )
    assert issue_id is None
    assert "Server error: Something went wrong" in error



@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.put")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_approve_mining_license_success(mock_api_key, mock_put):
    mock_api_key.return_value = "valid_api_key"

    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_put.return_value = mock_response

    result = GsmbOfficerService.approve_mining_license("token", 123, 42)

    assert result["success"] is True
    assert "License approved" in result["message"]
    mock_put.assert_called_once()
    assert "issues/123.json" in mock_put.call_args[0][0]


@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_api_key(mock_api_key):
    mock_api_key.return_value = None

    result = GsmbOfficerService.approve_mining_license("bad_token", 123, 42)
    assert result["success"] is False
    assert "Invalid API key" in result["message"]


@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_missing_redmine_url(mock_api_key):
    mock_api_key.return_value = "valid_key"
    with patch.dict(os.environ, {}, clear=True):
        result = GsmbOfficerService.approve_mining_license("token", 123, 42)
        assert result["success"] is False
        assert "Redmine URL not configured" in result["message"]


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.requests.put")
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
def test_redmine_update_failure(mock_api_key, mock_put):
    mock_api_key.return_value = "valid_key"

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_put.return_value = mock_response

    result = GsmbOfficerService.approve_mining_license("token", 123, 42)
    assert result["success"] is False
    assert "Update failed" in result["message"]
    assert "400" in result["message"]


@patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
@patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
@patch("services.gsmb_officer_service.requests.put")
def test_network_exception(mock_put, mock_api_key):
    mock_api_key.return_value = "valid_key"
    mock_put.side_effect = Exception("Simulated network failure")

    result = GsmbOfficerService.approve_mining_license("token", 123, 42)
    assert result["success"] is False
    assert "Unexpected error" in result["message"]

class TestChangeIssueStatus:

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.requests.put")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_change_issue_status_success(self, mock_get_api_key, mock_put):
        mock_get_api_key.return_value = "valid_api_key"

        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        result, error = GsmbOfficerService.change_issue_status("token", 123, 42)

        assert result is True
        assert error is None
        mock_put.assert_called_once()
        assert "issues/123.json" in mock_put.call_args[0][0]

    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_missing_api_key(self, mock_get_api_key):
        mock_get_api_key.return_value = None
        result, error = GsmbOfficerService.change_issue_status("token", 123, 42)
        assert result is None
        assert "Invalid or missing API key" in error

    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_missing_redmine_url(self, mock_get_api_key):
        mock_get_api_key.return_value = "valid_api_key"
        with patch.dict(os.environ, {}, clear=True):
            result, error = GsmbOfficerService.change_issue_status("token", 123, 42)
            assert result is None
            assert "REDMINE_URL" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.requests.put")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_redmine_update_failure(self, mock_get_api_key, mock_put):
        mock_get_api_key.return_value = "valid_api_key"

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_put.return_value = mock_response

        result, error = GsmbOfficerService.change_issue_status("token", 123, 42)
        assert result is None
        assert "Failed to update issue status" in error
        assert "400" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    @patch("services.gsmb_officer_service.requests.put")
    def test_exception_handling(self, mock_put, mock_get_api_key):
        mock_get_api_key.return_value = "valid_api_key"
        mock_put.side_effect = Exception("Something went wrong")

        result, error = GsmbOfficerService.change_issue_status("token", 123, 42)
        assert result is None
        assert "Server error: Something went wrong" in error



class TestMarkComplaintResolved:

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.requests.put")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_mark_resolved_success(self, mock_api_key, mock_put):
        mock_api_key.return_value = "valid_api_key"

        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        result, error = GsmbOfficerService.mark_complaint_resolved("token", 456)

        assert result is True
        assert error is None
        mock_put.assert_called_once()
        assert "issues/456.json" in mock_put.call_args[0][0]

    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_missing_api_key(self, mock_api_key):
        mock_api_key.return_value = None

        result, error = GsmbOfficerService.mark_complaint_resolved("token", 456)

        assert result is None
        assert "Invalid or missing API key" in error

    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_missing_redmine_url(self, mock_api_key):
        mock_api_key.return_value = "valid_api_key"
        with patch.dict(os.environ, {}, clear=True):
            result, error = GsmbOfficerService.mark_complaint_resolved("token", 456)
            assert result is None
            assert "REDMINE_URL" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.requests.put")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_redmine_failure(self, mock_api_key, mock_put):
        mock_api_key.return_value = "valid_api_key"

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_put.return_value = mock_response

        result, error = GsmbOfficerService.mark_complaint_resolved("token", 456)

        assert result is None
        assert "Failed to update issue" in error
        assert "400" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    @patch("services.gsmb_officer_service.requests.put")
    def test_exception_handling(self, mock_put, mock_api_key):
        mock_api_key.return_value = "valid_api_key"
        mock_put.side_effect = Exception("Unexpected failure")

        result, error = GsmbOfficerService.mark_complaint_resolved("token", 456)

        assert result is None
        assert "Server error: Unexpected failure" in error



class TestGetMiningLicenseRequest:

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.requests.get")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    @patch("services.gsmb_officer_service.GsmbOfficerService.get_custom_field_value")
    def test_successful_request(self, mock_get_field, mock_api_key, mock_get):
        mock_api_key.return_value = "valid_api_key"
        mock_get_field.side_effect = lambda fields, name: f"mock_{name.lower().replace(' ', '_')}"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 1,
                    "subject": "Request 1",
                    "assigned_to": {"name": "Officer A", "id": 10},
                    "custom_fields": [],
                    "created_on": "2025-06-01T10:00:00Z",
                    "status": {"name": "Pending"}
                }
            ]
        }
        mock_get.return_value = mock_response

        result, error = GsmbOfficerService.get_mining_license_request("token")

        assert error is None
        assert len(result) == 1
        assert result[0]["subject"] == "Request 1"
        assert result[0]["mobile"] == "mock_mobile_number"
        assert result[0]["district"] == "mock_administrative_district"
        mock_get.assert_called_once()

    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_missing_api_key(self, mock_api_key):
        mock_api_key.return_value = None
        result, error = GsmbOfficerService.get_mining_license_request("token")
        assert result is None
        assert "Invalid or missing API key" in error

    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_missing_redmine_url(self, mock_api_key):
        mock_api_key.return_value = "valid_api_key"
        with patch.dict(os.environ, {}, clear=True):
            result, error = GsmbOfficerService.get_mining_license_request("token")
            assert result is None
            assert "REDMINE_URL" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.requests.get")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_redmine_api_failure(self, mock_api_key, mock_get):
        mock_api_key.return_value = "valid_api_key"

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        result, error = GsmbOfficerService.get_mining_license_request("token")

        assert result is None
        assert "Failed to fetch mining license issues" in error
        assert "500" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    @patch("services.gsmb_officer_service.requests.get")
    def test_unexpected_exception(self, mock_get, mock_api_key):
        mock_api_key.return_value = "valid_api_key"
        mock_get.side_effect = Exception("Unexpected failure")

        result, error = GsmbOfficerService.get_mining_license_request("token")

        assert result is None
        assert "Server error: Unexpected failure" in error



class TestGetMiningRequestViewButton:

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.GsmbOfficerService.get_attachment_urls")
    @patch("services.gsmb_officer_service.requests.get")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_successful_fetch(self, mock_api_key, mock_get, mock_attachments):
        mock_api_key.return_value = "valid_key"

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "issue": {
                    "id": 1,
                    "subject": "Sample Issue",
                    "status": {"name": "Pending"},
                    "assigned_to": {"name": "Officer A"},
                    "custom_fields": [
                        {"name": "Land Name(Licence Details)", "value": "Test Land"},
                        {"name": "Mining License Number", "value": "ML123"},
                        {"name": "Mobile Number", "value": "0771234567"}
                    ]
                }
            }
        )

        mock_attachments.return_value = {
            "Economic Viability Report": "https://file1.pdf",
            "License fee receipt": "https://file2.pdf",
            "Detailed Mine Restoration Plan": "https://file3.pdf",
            "Deed and Survey Plan": "https://file4.pdf",
            "Payment Receipt": "https://file5.pdf",
            "License Boundary Survey": "https://file6.pdf"
        }

        result, error = GsmbOfficerService.get_mining_request_view_button("token", 1)

        assert error is None
        assert result["id"] == 1
        assert result["land_name"] == "Test Land"
        assert result["mining_license_number"] == "ML123"
        assert result["economic_viability_report"] == "https://file1.pdf"

    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_missing_api_key(self, mock_api_key):
        mock_api_key.return_value = None
        result, error = GsmbOfficerService.get_mining_request_view_button("token", 1)
        assert result is None
        assert "Invalid or missing API key" in error

    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_missing_env_variable(self, mock_api_key):
        mock_api_key.return_value = "valid_key"
        with patch.dict(os.environ, {}, clear=True):
            result, error = GsmbOfficerService.get_mining_request_view_button("token", 1)
            assert result is None
            assert "REDMINE_URL" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.requests.get")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_redmine_fetch_failure(self, mock_api_key, mock_get):
        mock_api_key.return_value = "valid_key"
        mock_get.return_value = MagicMock(status_code=404, text="Not Found")

        result, error = GsmbOfficerService.get_mining_request_view_button("token", 1)

        assert result is None
        assert "Failed to fetch issue" in error
        assert "404" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.requests.get")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_no_issue_in_response(self, mock_api_key, mock_get):
        mock_api_key.return_value = "valid_key"
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {})

        result, error = GsmbOfficerService.get_mining_request_view_button("token", 1)

        assert result is None
        assert "Issue data not found" in error



class TestGetMiningLicenseViewButton:

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.GsmbOfficerService.get_attachment_urls")
    @patch("services.gsmb_officer_service.requests.get")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_successful_view_button(self, mock_get_token, mock_get_request, mock_get_attachments):
        mock_get_token.return_value = "valid_api_key"

        mock_get_request.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "issue": {
                    "id": 1,
                    "subject": "Test License",
                    "start_date": "2024-01-01",
                    "due_date": "2024-12-31",
                    "status": {"name": "Approved"},
                    "assigned_to": {"name": "Officer A"},
                    "custom_fields": [
                        {"name": "Land Name(Licence Details)", "value": "Sample Land"},
                        {"name": "Mobile Number", "value": "0712345678"},
                        {"name": "Capacity", "value": "1000"},
                        {"name": "Mining License Number", "value": "ML-001"},
                        {"name": "Used", "value": "100"},
                        {"name": "Remaining", "value": "900"}
                    ]
                }
            }
        )

        mock_get_attachments.return_value = {
            "Economic Viability Report": "https://file1.com",
            "License fee receipt": "https://file2.com",
            "Detailed Mine Restoration Plan": "https://file3.com",
            "Deed and Survey Plan": "https://file4.com",
            "Payment Receipt": "https://file5.com",
            "License Boundary Survey": "https://file6.com"
        }

        result, error = GsmbOfficerService.get_miningLicense_view_button("token", 1)

        assert error is None
        assert result["id"] == 1
        assert result["land_name"] == "Sample Land"
        assert result["used"] == "100"
        assert result["license_fee_receipt"] == "https://file2.com"

    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_missing_api_key(self, mock_get_token):
        mock_get_token.return_value = None
        result, error = GsmbOfficerService.get_miningLicense_view_button("token", 1)
        assert result is None
        assert "Invalid or missing API key" in error

    def test_missing_env_variable(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="key"):
                result, error = GsmbOfficerService.get_miningLicense_view_button("token", 1)
                assert result is None
                assert "REDMINE_URL" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.requests.get")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_redmine_issue_not_found(self, mock_get_token, mock_get):
        mock_get_token.return_value = "valid_api_key"
        mock_get.return_value = MagicMock(status_code=404, text="Not Found")

        result, error = GsmbOfficerService.get_miningLicense_view_button("token", 1)

        assert result is None
        assert "Failed to fetch issue" in error

    @patch.dict(os.environ, {"REDMINE_URL": "https://test.redmine.com"})
    @patch("services.gsmb_officer_service.requests.get")
    @patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token")
    def test_redmine_response_no_issue_data(self, mock_get_token, mock_get):
        mock_get_token.return_value = "valid_api_key"
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {})

        result, error = GsmbOfficerService.get_miningLicense_view_button("token", 1)

        assert result is None
        assert "Issue data not found" in error
