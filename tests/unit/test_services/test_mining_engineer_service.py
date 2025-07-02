import os
import pytest
from unittest.mock import patch, MagicMock
from services.mining_engineer_service import MiningEnginerService
from utils.jwt_utils import JWTUtils
from utils.MLOUtils import MLOUtils

MOCK_TOKEN = "mocked.jwt.token"
MOCK_ISSUE_ID = 123
MOCK_API_KEY = "mocked_api_key"
MOCK_REDMINE_URL = "http://mocked-redmine-url.com"

# Helper: mock environment variables
@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    monkeypatch.setenv("REDMINE_URL", "http://fake-redmine.com")
    monkeypatch.setenv("ORS_API_KEY", "fake_ors_key")
    yield

# Mock JWTUtils.get_api_key_from_token to always return a fake API key
@pytest.fixture(autouse=True)
def mock_jwt_api_key():
    with patch.object(JWTUtils, "get_api_key_from_token", return_value="fake_api_key"):
        yield

# Mock MLOUtils.get_user_info_from_token for get_me_pending_licenses
@pytest.fixture(autouse=True)
def mock_mloutils_user_info():
    with patch.object(MLOUtils, "get_user_info_from_token", return_value=(123, None)):
        yield


@patch("services.mining_engineer_service.requests.put")
def test_update_miningOwner_appointment_success(mock_put):
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"issue": {"id": 1}}
    mock_put.return_value = mock_resp

    result, err = MiningEnginerService.update_miningOwner_appointment("token", 1, {"status_id": 31, "due_date": "2025-06-01"})
    assert err is None
    assert result == {"issue": {"id": 1}}
    mock_put.assert_called_once()

@patch("services.mining_engineer_service.requests.put")
def test_update_miningOwner_appointment_fail_status_code(mock_put):
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"errors": ["Invalid data"]}
    mock_put.return_value = mock_resp

    result, err = MiningEnginerService.update_miningOwner_appointment("token", 1, {})
    assert result is None
    assert "Failed to create appointment" in err


@patch("services.mining_engineer_service.requests.get")
def test_get_me_pending_licenses_success(mock_get):
    # Mock Redmine API paginated response
    issues_page_1 = {
        "issues": [
            {
                "id": 1,
                "subject": "Test License",
                "status": {"id": 31, "name": "Open"},
                "assigned_to": {"name": "User1"},
                "custom_fields": [
                    {"id": 19, "value": "EL123"},
                    {"id": 28, "value": "LandA"},
                    {"id": 29, "value": "OwnerA"},
                    {"id": 30, "value": "VillageX"},
                    {"id": 31, "value": "GN1"},
                    {"id": 32, "value": "DivSec1"},
                    {"id": 33, "value": "District1"},
                    {"id": 34, "value": "100"},
                    {"id": 66, "value": "0712345678"},
                    {"id": 92, "value": "GPS123"},
                    {"id": 72, "value": "Plan1"},
                    {"id": 80, "value": "Receipt1"},
                    {"id": 90, "value": "DeedPlan1"},
                    {"id": 101, "value": "ML123"},
                ],
            }
        ]
    }
    issues_page_2 = {"issues": []}  # no more pages

    def side_effect(*args, **kwargs):
        offset = kwargs.get("params", {}).get("offset", 0)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if offset == 0:
            mock_resp.json.return_value = issues_page_1
        else:
            mock_resp.json.return_value = issues_page_2
        return mock_resp

    mock_get.side_effect = side_effect

    # Patch get_attachment_urls to return an empty dictionary
    with patch.object(MiningEnginerService, "get_attachment_urls", return_value={}):
        result, err = MiningEnginerService.get_me_pending_licenses("token")

    # Assertions
    assert err is None
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["assigned_to"] == "User1"
    assert result[0]["Google_location"] == "GPS123"
    assert result[0]["mining_number"] == "ML123"
 


def test_get_attachment_urls_success():
    custom_fields = [
        {"name": "Detailed Mine Restoration Plan", "value": "10"},
        {"name": "Deed and Survey Plan", "value": "20"},
        {"name": "Payment Receipt", "value": "30"},
    ]

    urls = MiningEnginerService.get_attachment_urls("fake_key", "http://fake-redmine.com", custom_fields)

    assert urls["Detailed Mine Restoration Plan"] == 10
    assert urls["Deed and Survey Plan"] == 20
    assert urls["Payment Receipt"] == 30


@patch("services.mining_engineer_service.requests.put")
def test_miningEngineer_approve_success(mock_put):
    # First put call - update ML issue
    mock_resp1 = MagicMock()
    mock_resp1.status_code = 200
    mock_resp1.content = b'{"issue": {"id": 1}}'
    mock_resp1.json.return_value = {"issue": {"id": 1}}

    # Second put call - close ME appointment
    mock_resp2 = MagicMock()
    mock_resp2.status_code = 204
    mock_resp2.content = b""

    mock_put.side_effect = [mock_resp1, mock_resp2]

    result, err = MiningEnginerService.miningEngineer_approve("token", 1, 2, {"status_id": 32})
    assert err is None
    assert result == {"issue": {"id": 1}}
    assert mock_put.call_count == 2


@patch("services.mining_engineer_service.requests.put")
def test_miningEngineer_approve_fail_close_me(mock_put):
    # First put call success
    mock_resp1 = MagicMock()
    mock_resp1.status_code = 200
    mock_resp1.content = b'{"issue": {"id": 1}}'
    mock_resp1.json.return_value = {"issue": {"id": 1}}

    # Second put call fails
    mock_resp2 = MagicMock()
    mock_resp2.status_code = 400
    mock_resp2.text = "Error closing ME appointment"
    mock_resp2.content = b"Error closing ME appointment"

    mock_put.side_effect = [mock_resp1, mock_resp2]

    result, err = MiningEnginerService.miningEngineer_approve("token", 1, 2, {"status_id": 32})
    assert result is None
    assert "Failed to close ME Appointment" in err


@patch("services.mining_engineer_service.requests.put")
def test_miningEngineer_reject_success(mock_put):
    # ML issue update success
    mock_ml_resp = MagicMock()
    mock_ml_resp.status_code = 200
    mock_ml_resp.content = b'{"issue": {"id": 1}}'
    mock_ml_resp.json.return_value = {"issue": {"id": 1}}

    # ME appointment close success
    mock_me_resp = MagicMock()
    mock_me_resp.status_code = 204
    mock_me_resp.content = b""

    mock_put.side_effect = [mock_ml_resp, mock_me_resp]

    result, err = MiningEnginerService.miningEngineer_reject("token", 1, 2, {"status_id": 6, "me_comment": "No", "me_report": "Fail"})
    assert err is None
    assert result == {"issue": {"id": 1}}
    assert mock_put.call_count == 2

@patch("services.mining_engineer_service.requests.put")
def test_miningEngineer_reject_fail_ml_update(mock_put):
    mock_ml_resp = MagicMock()
    mock_ml_resp.status_code = 400
    mock_ml_resp.text = "Bad Request"
    mock_ml_resp.content = b"Bad Request"

    mock_put.return_value = mock_ml_resp

    result, err = MiningEnginerService.miningEngineer_reject("token", 1, 2, {"status_id": 6, "me_comment": "No", "me_report": "Fail"})
    assert result is None
    assert "Redmine API error" in err

    @patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token")
    @patch("services.mining_engineer_service.MLOUtils.get_user_info_from_token")
    @patch("services.mining_engineer_service.requests.post")
    @patch("services.mining_engineer_service.MiningEnginerService.change_issue_status")
    def test_create_ml_appointment_success(self, mock_change_status, mock_post, mock_get_user_info, mock_get_api_key):
        token = make_token()
        start_date = "2025-06-14"
        mining_license_number = "LLL/100/206"
        google_location = "Some Location"

        mock_get_api_key.return_value = make_api_key()
        mock_get_user_info.return_value = (make_user_id(), None)

        # Mock successful Redmine post creation response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"issue": {"id": 999}}
        mock_post.return_value = mock_response

        # Mock successful status change
        mock_change_status.return_value = (True, None)

        result, error = MiningEnginerService.create_ml_appointment(token, start_date, mining_license_number, google_location)

        assert error is None
        assert "issue" in result
        assert mock_post.called
        mock_change_status.assert_called_once()

    @patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token")
    def test_create_ml_appointment_invalid_token(self, mock_get_api_key):
        mock_get_api_key.return_value = None
        result, error = MiningEnginerService.create_ml_appointment("badtoken", "2025-06-14", "LLL/100/206", "loc")
        assert result is None
        assert "Invalid API token" in error

    def test_create_ml_appointment_invalid_license_format(self):
        token = make_token()
        result, error = MiningEnginerService.create_ml_appointment(token, "2025-06-14", "INVALIDLICENSE", "loc")
        assert result is None
        assert "Invalid mining license number format" in error

    @patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token")
    @patch("services.mining_engineer_service.requests.put")
    def test_change_issue_status_success(self, mock_put, mock_get_api_key):
        mock_get_api_key.return_value = make_api_key()

        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        success, error = MiningEnginerService.change_issue_status(make_token(), 1, 31)
        assert success is True
        assert error is None

    @patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token")
    @patch("services.mining_engineer_service.requests.put")
    def test_change_issue_status_failure(self, mock_put, mock_get_api_key):
        mock_get_api_key.return_value = make_api_key()

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_put.return_value = mock_response

        success, error = MiningEnginerService.change_issue_status(make_token(), 1, 31)
        assert success is None
        assert "Failed to update issue status" in error

    def test_change_issue_status_invalid_api_key(self):
        success, error = MiningEnginerService.change_issue_status("badtoken", 1, 31)
        assert success is None
        assert "Invalid or missing API key" in error

    @patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token")
    @patch("services.mining_engineer_service.MLOUtils.get_user_info_from_token")
    @patch("services.mining_engineer_service.requests.get")
    @patch("services.mining_engineer_service.MiningEnginerService.get_attachment_urls")
    @patch("services.mining_engineer_service.LimitUtils.get_limit")
    def test_get_me_meetingeShedule_licenses_success(self, mock_get_limit, mock_get_attachment_urls, mock_requests_get, mock_get_user_info, mock_get_api_key):
        mock_get_api_key.return_value = make_api_key()
        mock_get_user_info.return_value = (make_user_id(), None)
        mock_get_limit.return_value = 10
        mock_get_attachment_urls.return_value = {
            "Detailed Mine Restoration Plan": "http://example.com/plan.pdf",
            "Payment Receipt": "http://example.com/receipt.pdf",
            "Deed and Survey Plan": "http://example.com/deed.pdf"
        }

        issues_data = {
            "issues": [
                {
                    "id": 1,
                    "subject": "Test Issue",
                    "status": {"name": "Scheduled"},
                    "assigned_to": {"name": "Engineer"},
                    "custom_fields": [
                        {"id": 19, "value": "ELN123"},
                        {"id": 28, "value": "LandName"},
                        {"id": 29, "value": "OwnerName"},
                        {"id": 30, "value": "VillageName"},
                        {"id": 31, "value": "GN Division"},
                        {"id": 32, "value": "DS Division"},
                        {"id": 33, "value": "District"},
                        {"id": 34, "value": "CapacityVal"},
                        {"id": 66, "value": "1234567890"},
                        {"id": 92, "value": "Loc"},
                        {"id": 72, "value": None},
                        {"id": 80, "value": None},
                        {"id": 90, "value": None}
                    ]
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = issues_data
        mock_requests_get.return_value = mock_response

        results, error = MiningEnginerService.get_me_meetingeShedule_licenses(make_token())
        assert error is None
        assert len(results) == 1
        assert results[0]["id"] == 1
        assert results[0]["Detailed_Plan"] == "http://example.com/plan.pdf"

    @patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token")
    @patch("services.mining_engineer_service.requests.get")
    def test_get_me_appointments_success(self, mock_requests_get, mock_get_api_key):
        mock_get_api_key.return_value = make_api_key()
        issues_data = {
            "issues": [
                {
                    "id": 10,
                    "subject": "Appointment 1",
                    "start_date": "2025-06-14",
                    "status": {"name": "Open"},
                    "assigned_to": {"name": "Engineer 1"},
                    "custom_fields": [
                        {"id": 92, "value": "Location1"},
                        {"id": 101, "value": "ML-101"}
                    ]
                }
            ]
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = issues_data
        mock_requests_get.return_value = mock_response

        result = MiningEnginerService.get_me_appointments(make_token())
        assert "appointments" in result
        assert len(result["appointments"]) == 1
        assert result["appointments"][0]["id"] == 10
        assert result["appointments"][0]["Google_location"] == "Location1"

    @patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token")
    def test_get_me_appointments_invalid_token(self, mock_get_api_key):
        mock_get_api_key.return_value = None
        result = MiningEnginerService.get_me_appointments("badtoken")
        assert "error" in result
        assert "Invalid API token" in result["error"]

    @patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token")
    @patch("services.mining_engineer_service.requests.get")
    def test_get_me_appointments_api_error(self, mock_requests_get, mock_get_api_key):
        mock_get_api_key.return_value = make_api_key()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_requests_get.return_value = mock_response

        result = MiningEnginerService.get_me_appointments(make_token())
        assert "error" in result
        assert "Redmine API error" in result["error"]

    
@patch("services.mining_engineer_service.requests.get")
def test_get_me_approve_license_success(mock_get):
    # Mock Redmine API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "issues": [
            {
                "id": 1,
                "subject": "Issue 1",
                "status": {"name": "Open"},
                "assigned_to": {"name": "User A"},
                "custom_fields": [
                    {"id": 19, "value": "EL-123"},
                    {"id": 28, "value": "Land A"},
                ]
            }
        ]
    }
    mock_get.return_value = mock_response

    # Patch get_attachment_urls to return empty dict to avoid actual call
    with patch("services.mining_engineer_service.MiningEnginerService.get_attachment_urls", return_value={}):
        issues, error = MiningEnginerService.get_me_approve_license(MOCK_TOKEN)
        assert error is None
        assert issues is not None
        assert len(issues) == 1
        assert issues[0]["exploration_license_no"] == "EL-123"
        assert issues[0]["Land_Name"] == "Land A"


@patch("services.mining_engineer_service.requests.get")
def test_get_me_approve_license_api_error(mock_get):
    mock_response = MagicMock(status_code=500, text="Internal Server Error")
    mock_get.return_value = mock_response

    issues, error = MiningEnginerService.get_me_approve_license(MOCK_TOKEN)
    assert issues is None
    assert "Redmine API error" in error


@patch("services.mining_engineer_service.requests.get")
def test_get_me_approve_single_license_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "issue": {
            "id": MOCK_ISSUE_ID,
            "subject": "Single Issue",
            "status": {"name": "Open"},
            "assigned_to": {"name": "User B"},
            "tracker": {"id": 4},
            "project": {"id": 1},
            "custom_fields": [
                {"id": 19, "value": "EL-456"},
                {"id": 28, "value": "Land B"},
            ]
        }
    }
    mock_get.return_value = mock_response

    with patch("services.mining_engineer_service.MiningEnginerService.get_attachment_urls", return_value={}):
        result = MiningEnginerService.get_me_approve_single_license(MOCK_TOKEN, MOCK_ISSUE_ID)
        assert "error" not in result
        assert result["exploration_license_no"] == "EL-456"
        assert result["Land_Name"] == "Land B"


@patch("services.mining_engineer_service.requests.get")
def test_get_me_approve_single_license_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response

    result = MiningEnginerService.get_me_approve_single_license(MOCK_TOKEN, MOCK_ISSUE_ID)
    assert "error" in result
    assert "Redmine API error" in result["error"]


@patch("services.mining_engineer_service.requests.get")
@patch("services.mining_engineer_service.MLOUtils.get_user_info_from_token")
@patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token")
def test_get_me_licenses_count_success(mock_get_api_key, mock_get_user_info, mock_requests_get):
     
    mock_get_api_key.return_value = "fake_api_key"  
    mock_get_user_info.return_value = ("fake_user_id", None)
    # Prepare paginated issues data
    issues_page1 = (
        [{"status": {"id": 6}}] * 50 +     # 50 Rejected
        [{"status": {"id": 26}}] * 50      # 50 Awaiting ME Scheduling
)
    issues_page2 = [
        {"status": {"id": 31}}, # ME Appointment Scheduled
        {"status": {"id": 32}}, # ME Approved
    ]

    def side_effect(*args, **kwargs):
        params = kwargs.get("params", {})
        offset = params.get("offset", 0)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if offset == 0:
            mock_resp.json.return_value = {"issues": issues_page1}
        elif offset == 100:
            mock_resp.json.return_value = {"issues": issues_page2}
        else:
            mock_resp.json.return_value = {"issues": []}
        return mock_resp

    mock_requests_get.side_effect = side_effect

    counts, error = MiningEnginerService.get_me_licenses_count(MOCK_TOKEN)

    print("DEBUG counts:", counts) 
    
    assert error is None
    assert counts["Rejected"] == 50
    assert counts["Awaiting ME Scheduling"] == 50
    assert counts["ME Appointment Scheduled"] == 1
    assert counts["ME Approved"] == 1


@patch("services.mining_engineer_service.requests.put")
def test_set_license_hold_success(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_put.return_value = mock_response

    success, error = MiningEnginerService.set_license_hold(MOCK_ISSUE_ID, "Reason for hold", MOCK_TOKEN)
    assert success is True
    assert error is None


@patch("services.mining_engineer_service.requests.put")
def test_set_license_hold_fail(mock_put):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_put.return_value = mock_response

    success, error = MiningEnginerService.set_license_hold(MOCK_ISSUE_ID, "Reason for hold", MOCK_TOKEN)
    assert success is False
    assert "Failed to update issue" in error


@patch("services.mining_engineer_service.requests.get")
def test_get_me_hold_licenses_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "issues": [
            {
                "id": MOCK_ISSUE_ID,
                "subject": "Hold Issue",
                "status": {"name": "Hold"},
                "assigned_to": {"name": "User Hold"},
                "custom_fields": [
                    {"id": 19, "value": "EL-789"},
                    {"id": 106, "value": "Hold Reason"},
                ]
            }
        ]
    }
    mock_get.return_value = mock_response

    with patch("services.mining_engineer_service.MiningEnginerService.get_attachment_urls", return_value={}):
        issues, error = MiningEnginerService.get_me_hold_licenses(MOCK_TOKEN)
        assert error is None
        assert len(issues) == 1
        assert issues[0]["hold"] == "Hold Reason"


@patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token")
@patch("services.mining_engineer_service.requests.get")
@patch("services.mining_engineer_service.os.getenv")
def test_get_miningLicense_view_button_success(mock_getenv, mock_requests_get, mock_get_api_key):
    # Arrange
    mock_get_api_key.return_value = MOCK_API_KEY
    mock_getenv.return_value = MOCK_REDMINE_URL

    mock_issue_data = {
        "issue": {
            "id": MOCK_ISSUE_ID,
            "subject": "Test Subject",
            "start_date": "2025-06-01",
            "due_date": "2025-06-10",
            "status": {"name": "Approved"},
            "assigned_to": {"name": "Engineer A"},
            "custom_fields": [
                {"name": "Land Name(Licence Details)", "value": "Land A"},
                {"name": "Land owner name", "value": "Owner X"},
                {"name": "Mining License Number", "value": "ML-2025-100"},
                {"name": "Payment Receipt", "value": "123"},
            ]
        }
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_issue_data
    mock_requests_get.return_value = mock_response

    with patch("services.mining_engineer_service.MiningEnginerService.get_attachment_urls", return_value={"Payment Receipt": "http://files.com/123"}):
        result, error = MiningEnginerService.get_miningLicense_view_button(MOCK_TOKEN, MOCK_ISSUE_ID)

    # Assert
    assert error is None
    assert result["id"] == MOCK_ISSUE_ID
    assert result["land_name"] == "Land A"
    assert result["land_owner_name"] == "Owner X"
    assert result["payment_receipt"] == "http://files.com/123"


@patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token", return_value=None)
def test_get_miningLicense_view_button_invalid_token(mock_get_api_key):
    result, error = MiningEnginerService.get_miningLicense_view_button("badtoken", MOCK_ISSUE_ID)
    assert result is None
    assert "Invalid or missing API key" in error


@patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token", return_value=MOCK_API_KEY)
@patch("services.mining_engineer_service.requests.get")
@patch("services.mining_engineer_service.os.getenv", return_value=MOCK_REDMINE_URL)
def test_get_miningLicense_view_button_api_error(mock_getenv, mock_requests_get, mock_get_api_key):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_requests_get.return_value = mock_response

    result, error = MiningEnginerService.get_miningLicense_view_button(MOCK_TOKEN, MOCK_ISSUE_ID)
    assert result is None
    assert "Failed to fetch issue" in error


@patch("services.mining_engineer_service.JWTUtils.get_api_key_from_token", return_value=MOCK_API_KEY)
@patch("services.mining_engineer_service.requests.get")
@patch("services.mining_engineer_service.os.getenv", return_value=MOCK_REDMINE_URL)
def test_get_miningLicense_view_button_missing_issue(mock_getenv, mock_requests_get, mock_get_api_key):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}  # No "issue" key
    mock_requests_get.return_value = mock_response

    result, error = MiningEnginerService.get_miningLicense_view_button(MOCK_TOKEN, MOCK_ISSUE_ID)
    assert result is None
    assert "Issue data not found" in error