# import pytest
# from unittest.mock import patch, MagicMock
# from services.gsmb_officer_service import GsmbOfficerService
# from io import BytesIO
# import json


# @pytest.mark.usefixtures("mock_env")
# def test_get_mlowners():
#     # Sample users data returned from Redmine
#     mock_users_response = {
#         "users": [
#             {
#                 "id": 101,
#                 "firstname": "John",
#                 "lastname": "Doe",
#                 "mail": "john.doe@example.com",
#                 "custom_fields": [
#                     {"name": "User Type", "value": "mlOwner"},
#                     {"name": "National Identity Card", "value": "987654321V"},
#                     {"name": "Mobile Number", "value": "0712345678"}
#                 ]
#             },
#             {
#                 "id": 102,
#                 "firstname": "Jane",
#                 "lastname": "Smith",
#                 "mail": "jane.smith@example.com",
#                 "custom_fields": [
#                     {"name": "User Type", "value": "otherUser"},
#                     {"name": "National Identity Card", "value": "123456789V"},
#                     {"name": "Mobile Number", "value": "0771234567"}
#                 ]
#             }
#         ]
#     }

#     # Mock license counts returned from get_mining_license_counts
#     mock_license_counts = {
#         "John Doe": 3
#     }

#     with patch("services.gsmb_officer_service.requests.get") as mock_get, \
#          patch.object(GsmbOfficerService, "get_mining_license_counts", return_value=(mock_license_counts, None)) as mock_license_counts_fn:

#         # Mock Redmine users API call
#         mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=mock_users_response))

#         # Call the method under test
#         result, error = GsmbOfficerService.get_mlowners("fake-jwt-token")

#         # Assertions
#         assert error is None
#         assert result is not None
#         assert isinstance(result, list)

#         # Only John Doe (mlOwner) should be in the results
#         assert len(result) == 1
#         ml_owner = result[0]

#         assert ml_owner["id"] == 101
#         assert ml_owner["ownerName"] == "John Doe"
#         assert ml_owner["NIC"] == "987654321V"
#         assert ml_owner["email"] == "john.doe@example.com"
#         assert ml_owner["phoneNumber"] == "0712345678"
#         assert ml_owner["totalLicenses"] == 3

#         # Ensure get_mining_license_counts was called once
#         mock_license_counts_fn.assert_called_once_with("fake-jwt-token")

# @pytest.mark.usefixtures("mock_env")
# def test_get_tpls():
#     # Sample Redmine issues response
#     mock_issues_response = {
#         "issues": [
#             {
#                 "id": 1,
#                 "subject": "TPL Issue 1",
#                 "status": {"name": "Open"},
#                 "author": {"name": "Alice"},
#                 "tracker": {"name": "TPL"},
#                 "assigned_to": {"name": "Bob"},
#                 "start_date": "2025-06-01",
#                 "due_date": "2025-06-10",
#                 "custom_fields": [
#                     {"name": "Lorry Number", "value": "ABC-1234"},
#                     {"name": "Driver Contact", "value": "0712345678"},
#                     {"name": "Cubes", "value": "5.0"},
#                     {"name": "Mining issue id", "value": "ML-2025-001"},
#                     {"name": "Destination", "value": "Colombo"}
#                 ]
#             }
#         ]
#     }

#     # Mock the API key extracted from JWT
#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
#          patch("services.gsmb_officer_service.requests.get") as mock_get, \
#          patch.object(GsmbOfficerService, "get_custom_field_value") as mock_get_custom_field:

#         # Setup get_custom_field_value to simulate correct field retrieval
#         def side_effect(custom_fields, field_name):
#             for field in custom_fields:
#                 if field["name"] == field_name:
#                     return field["value"]
#             return None

#         mock_get_custom_field.side_effect = side_effect

#         # Mock Redmine API response
#         mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=mock_issues_response))

#         # Call the service method
#         result, error = GsmbOfficerService.get_tpls("fake-jwt-token")

#         # Assertions
#         assert error is None
#         assert result is not None
#         assert isinstance(result, list)
#         assert len(result) == 1

#         tpl = result[0]
#         assert tpl["id"] == 1
#         assert tpl["subject"] == "TPL Issue 1"
#         assert tpl["status"] == "Open"
#         assert tpl["author"] == "Alice"
#         assert tpl["tracker"] == "TPL"
#         assert tpl["assigned_to"] == "Bob"
#         assert tpl["start_date"] == "2025-06-01"
#         assert tpl["due_date"] == "2025-06-10"
#         assert tpl["lorry_number"] == "ABC-1234"
#         assert tpl["driver_contact"] == "0712345678"
#         assert tpl["cubes"] == "5.0"
#         assert tpl["mining_license_number"] == "ML-2025-001"
#         assert tpl["destination"] == "Colombo"

#         # Confirm that get_custom_field_value was called for each custom field
#         expected_fields = [
#             "Lorry Number",
#             "Driver Contact",
#             "Cubes",
#             "Mining issue id",
#             "Destination"
#         ]
#         for field_name in expected_fields:
#             mock_get_custom_field.assert_any_call(mock_issues_response["issues"][0]["custom_fields"], field_name)

# @pytest.mark.usefixtures("mock_env")
# def test_get_mining_licenses():
#     # Sample Redmine mining licenses response
#     mock_issues_response = {
#         "issues": [
#             {
#                 "id": 1,
#                 "status": {"name": "Active"},
#                 "assigned_to": {"name": "Inspector John"},
#                 "start_date": "2025-06-01",
#                 "due_date": "2025-06-30",
#                 "custom_fields": [
#                     {"name": "Divisional Secretary Division", "value": "Kandy"},
#                     {"name": "Capacity", "value": "1000"},
#                     {"name": "Used", "value": "500"},
#                     {"name": "Remaining", "value": "500"},
#                     {"name": "Royalty", "value": "15000"},
#                     {"name": "Mining License Number", "value": "ML-2025-001"},
#                     {"name": "Mobile Number", "value": "0712345678"}
#                 ]
#             }
#         ]
#     }

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
#          patch("services.gsmb_officer_service.requests.get") as mock_get, \
#          patch.object(GsmbOfficerService, "get_custom_field_value") as mock_get_custom_field, \
#          patch.object(GsmbOfficerService, "get_attachment_urls", return_value={}) as mock_get_attachments, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

#         # Setup get_custom_field_value to simulate correct field retrieval
#         def side_effect(custom_fields, field_name):
#             for field in custom_fields:
#                 if field["name"] == field_name:
#                     return field["value"]
#             return None

#         mock_get_custom_field.side_effect = side_effect

#         # Mock Redmine API response
#         mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=mock_issues_response))

#         # Call the service method
#         result, error = GsmbOfficerService.get_mining_licenses("fake-jwt-token")

#         # Assertions
#         assert error is None
#         assert result is not None
#         assert isinstance(result, list)
#         assert len(result) == 1

#         ml = result[0]
#         assert ml["id"] == 1
#         assert ml["status"] == "Active"
#         assert ml["assigned_to"] == "Inspector John"
#         assert ml["start_date"] == "2025-06-01"
#         assert ml["due_date"] == "2025-06-30"
#         assert ml["divisional_secretary_division"] == "Kandy"
#         assert ml["capacity"] == "1000"
#         assert ml["used"] == "500"
#         assert ml["remaining"] == "500"
#         assert ml["royalty"] == "15000"
#         assert ml["mining_license_number"] == "ML-2025-001"
#         assert ml["mobile_number"] == "0712345678"

#         # Confirm that get_custom_field_value was called for each field
#         expected_fields = [
#             "Divisional Secretary Division",
#             "Capacity",
#             "Used",
#             "Remaining",
#             "Royalty",
#             "Mining License Number",
#             "Mobile Number"
#         ]
#         for field_name in expected_fields:
#             mock_get_custom_field.assert_any_call(mock_issues_response["issues"][0]["custom_fields"], field_name)

#         # Confirm that get_attachment_urls was called
#         mock_get_attachments.assert_called_once_with(
#             "fake-api-key",
#             "https://redmine.example.com",
#             mock_issues_response["issues"][0]["custom_fields"]
#         )

# @pytest.mark.usefixtures("mock_env")
# def test_get_mining_license_by_id_success():
#     # 🧪 Sample Redmine issue response
#     mock_issue_response = {
#         "issue": {
#             "id": 1,
#             "subject": "Mining License 001",
#             "status": {"name": "Active"},
#             "author": {"name": "Officer Alice"},
#             "assigned_to": {"name": "Inspector John"},
#             "start_date": "2025-06-01",
#             "due_date": "2025-06-30",
#             "custom_fields": [
#                 {"name": "Exploration Licence No", "value": "EXPL-123"},
#                 {"name": "Land Name(Licence Details)", "value": "Green Hill"},
#                 {"name": "Land owner name", "value": "Mr. Silva"},
#                 {"name": "Name of village ", "value": "Kandy"},
#                 {"name": "Grama Niladhari Division", "value": "GN-45"},
#                 {"name": "Divisional Secretary Division", "value": "Kandy"},
#                 {"name": "Administrative District", "value": "Kandy District"},
#                 {"name": "Capacity", "value": "1000"},
#                 {"name": "Used", "value": "500"},
#                 {"name": "Remaining", "value": "500"},
#                 {"name": "Royalty", "value": "15000"},
#                 {"name": "Mining License Number", "value": "ML-2025-001"},
#                 {"name": "Mobile Number", "value": "0712345678"},
#                 {"name": "Reason For Hold", "value": "Pending Clearance"}
#             ]
#         }
#     }

#     # 🌟 Mock attachments
#     mock_attachments = {
#         "Economic Viability Report": "http://example.com/economic_report.pdf",
#         "License fee receipt": "http://example.com/license_fee.pdf",
#         "Detailed Mine Restoration Plan": "http://example.com/restoration_plan.pdf",
#         "Deed and Survey Plan": "http://example.com/deed.pdf",
#         "Payment Receipt": "http://example.com/payment_receipt.pdf",
#         "License Boundary Survey": "http://example.com/boundary_survey.pdf"
#     }

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
#          patch("services.gsmb_officer_service.requests.get") as mock_get, \
#          patch.object(GsmbOfficerService, "get_attachment_urls", return_value=mock_attachments), \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

#         # Mock the Redmine API response
#         mock_response = MagicMock(status_code=200)
#         mock_response.json.return_value = mock_issue_response
#         mock_get.return_value = mock_response

#         # Act
#         result, error = GsmbOfficerService.get_mining_license_by_id("fake-token", 1)

#         # Assert no errors
#         assert error is None
#         assert result is not None
#         assert isinstance(result, dict)
#         assert result["id"] == 1
#         assert result["subject"] == "Mining License 001"
#         assert result["status"] == "Active"
#         assert result["author"] == "Officer Alice"
#         assert result["assigned_to"] == "Inspector John"
#         assert result["start_date"] == "2025-06-01"
#         assert result["due_date"] == "2025-06-30"
#         assert result["exploration_licence_no"] == "EXPL-123"
#         assert result["land_name"] == "Green Hill"
#         assert result["land_owner_name"] == "Mr. Silva"
#         assert result["village_name"] == "Kandy"
#         assert result["grama_niladhari_division"] == "GN-45"
#         assert result["divisional_secretary_division"] == "Kandy"
#         assert result["administrative_district"] == "Kandy District"
#         assert result["capacity"] == "1000"
#         assert result["used"] == "500"
#         assert result["remaining"] == "500"
#         assert result["royalty"] == "15000"
#         assert result["license_number"] == "ML-2025-001"
#         assert result["mining_license_number"] == "ML-2025-001"
#         assert result["mobile_number"] == "0712345678"
#         assert result["reason_for_hold"] == "Pending Clearance"

#         # 📝 Check that attachment URLs are included
#         assert result["economic_viability_report"] == mock_attachments["Economic Viability Report"]
#         assert result["license_fee_receipt"] == mock_attachments["License fee receipt"]
#         assert result["detailed_mine_restoration_plan"] == mock_attachments["Detailed Mine Restoration Plan"]
#         assert result["deed_and_survey_plan"] == mock_attachments["Deed and Survey Plan"]
#         assert result["payment_receipt"] == mock_attachments["Payment Receipt"]
#         assert result["license_boundary_survey"] == mock_attachments["License Boundary Survey"]

#         # 🔍 Confirm that get_attachment_urls was called with correct arguments
#         mock_get.assert_called_once_with(
#             "https://redmine.example.com/issues/1.json?include=attachments",
#             headers={"X-Redmine-API-Key": "fake-api-key", "Content-Type": "application/json"}
#         )
#         GsmbOfficerService.get_attachment_urls.assert_called_once_with(
#             "fake-api-key",
#             "https://redmine.example.com",
#             mock_issue_response["issue"]["custom_fields"]
#         )

# @pytest.mark.usefixtures("mock_env")
# def test_get_complaints():
#     mock_issues_response = {
#         "issues": [
#             {
#                 "id": 123,
#                 "created_on": "2025-06-01T10:00:00Z",
#                 "custom_fields": [
#                     {"name": "Lorry Number", "value": "NB-1234"},
#                     {"name": "Mobile Number", "value": "0771234567"},
#                     {"name": "Role", "value": "Driver"},
#                     {"name": "Resolved", "value": "Yes"}
#                 ]
#             }
#         ]
#     }

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
#          patch("services.gsmb_officer_service.requests.get") as mock_get, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

#         mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=mock_issues_response))

#         complaints, error = GsmbOfficerService.get_complaints("fake-token")

#         assert error is None
#         assert complaints is not None
#         assert len(complaints) == 1

#         complaint = complaints[0]
#         assert complaint["id"] == 123
#         assert complaint["lorry_number"] == "NB-1234"
#         assert complaint["mobile_number"] == "0771234567"
#         assert complaint["role"] == "Driver"
#         assert complaint["resolved"] == "Yes"
#         assert complaint["complaint_date"] == "2025-06-01 10:00:00"

# def test_get_attachment_urls():
#     custom_fields = [
#         {"name": "Economic Viability Report", "value": "101"},
#         {"name": "Professional", "value": "102"},
#         {"name": "Some Irrelevant Field", "value": "999"}
#     ]

#     mock_responses = {
#         "101": {"attachment": {"content_url": "https://example.com/file1.pdf"}},
#         "102": {"attachment": {"content_url": "https://example.com/file2.pdf"}}
#     }

#     def mock_get(url, headers):
#         attachment_id = url.split("/")[-1].replace(".json", "")
#         if attachment_id in mock_responses:
#             return MagicMock(status_code=200, json=MagicMock(return_value=mock_responses[attachment_id]))
#         return MagicMock(status_code=404)

#     with patch("services.gsmb_officer_service.requests.get", side_effect=mock_get):
#         urls = GsmbOfficerService.get_attachment_urls("fake-api-key", "https://redmine.example.com", custom_fields)

#         assert urls["Economic Viability Report"] == "https://example.com/file1.pdf"
#         assert urls["Professional"] == "https://example.com/file2.pdf"
#         assert "Some Irrelevant Field" not in urls

# def test_get_custom_field_value():
#     custom_fields = [
#         {"name": "Mobile Number", "value": "0711111111"},
#         {"name": "License Number", "value": "LIC-123"}
#     ]

#     value = GsmbOfficerService.get_custom_field_value(custom_fields, "Mobile Number")
#     assert value == "0711111111"

#     value = GsmbOfficerService.get_custom_field_value(custom_fields, "License Number")
#     assert value == "LIC-123"

#     value = GsmbOfficerService.get_custom_field_value(custom_fields, "Non-Existent Field")
#     assert value is None


# @pytest.mark.usefixtures("mock_env")
# def test_get_mining_license_counts():
#     mock_issues_response = {
#         "issues": [
#             {"id": 1, "assigned_to": {"name": "Officer A"}},
#             {"id": 2, "assigned_to": {"name": "Officer A"}},
#             {"id": 3, "assigned_to": {"name": "Officer B"}},
#             {"id": 4}  # No assigned_to -> should be counted under "Unassigned"
#         ]
#     }

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="fake-api-key"), \
#          patch("services.gsmb_officer_service.requests.get") as mock_get, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

#         mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=mock_issues_response))

#         counts, error = GsmbOfficerService.get_mining_license_counts("fake-token")

#         assert error is None
#         assert counts is not None
#         assert counts["Officer A"] == 2
#         assert counts["Officer B"] == 1
#         assert counts["Unassigned"] == 1


# def test_upload_file_to_redmine_success():
#     file_mock = MagicMock()
#     file_mock.filename = "test.pdf"
#     file_mock.stream = BytesIO(b"dummy data")

#     with patch("services.gsmb_officer_service.requests.post") as mock_post, \
#          patch.dict("os.environ", {
#              "REDMINE_URL": "https://redmine.example.com",
#              "REDMINE_ADMIN_API_KEY": "admin-key"
#          }):

#         mock_response = MagicMock(status_code=201)
#         mock_response.json.return_value = {"upload": {"id": 12345}}
#         mock_post.return_value = mock_response


#         attachment_id = GsmbOfficerService.upload_file_to_redmine(file_mock)

#         assert attachment_id == 12345


# def test_upload_file_to_redmine_failure():
#     file_mock = MagicMock()
#     file_mock.filename = "test.pdf"
#     file_mock.stream = BytesIO(b"dummy data")

#     with patch("services.gsmb_officer_service.requests.post") as mock_post, \
#          patch.dict("os.environ", {
#              "REDMINE_URL": "https://redmine.example.com",
#              "REDMINE_ADMIN_API_KEY": "admin-key"
#          }):

#         mock_post.return_value = MagicMock(status_code=400)

#         attachment_id = GsmbOfficerService.upload_file_to_redmine(file_mock)

#         assert attachment_id is None


  
# def test_upload_mining_license_success():
#     data = {
#         "subject": "Mining License Request",
#         "start_date": "2024-01-01",
#         "due_date": "2024-01-31",
#         "author": "Test Officer",
#         "assignee_id": 5,
#         "exploration_licence_no": "EXP123",
#         "land_name": "TestLand",
#         "village_name": "TestVillage",
#         "grama_niladhari_division": "GND",
#         "divisional_secretary_division": "DSD",
#         "administrative_district": "District",
#         "mobile_number": "0771234567",
#         "land_owner_name": "John Doe",
#         "royalty": "5000",
#         "capacity": "1000",
#         "used": "200",
#         "remaining": "800",
#         "google_location": "8.123,80.123",
#         "mining_license_number": "",
#         "month_capacity": "1200",
#         "economic_viability_report": "file-token-1",
#         "detailed_mine_restoration_plan": "file-token-2"
#     }

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#             patch("services.gsmb_officer_service.requests.post") as mock_post, \
#             patch("services.gsmb_officer_service.requests.put") as mock_put, \
#             patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

#         # Mock issue creation
#         mock_post.return_value = MagicMock(status_code=201, json=MagicMock(return_value={"issue": {"id": 101}}))

#         # Mock update call
#         mock_put.return_value = MagicMock(status_code=204)

#         result, error = GsmbOfficerService.upload_mining_license("fake-token", data)

#         assert result is True
#         assert error is None


# def test_upload_payment_receipt_success():
#     data = {
#         "mining_request_id": "101",
#         "comments": "Payment received successfully.",
#         "payment_receipt_id": "file-token-123"
#     }

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#          patch("services.gsmb_officer_service.requests.put") as mock_put, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

#         # Mock successful PUT request
#         mock_put.return_value = MagicMock(status_code=204, text="")

#         result, error = GsmbOfficerService.upload_payment_receipt("fake-token", data)

#         assert result is True
#         assert error is None
#         mock_put.assert_called_once_with(
#             "https://redmine.example.com/issues/101.json",
#             headers={
#                 "X-Redmine-API-Key": "user-api-key",
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "issue": {
#                     "status_id": 26,
#                     "custom_fields": [
#                         {"id": 80, "value": "file-token-123"},
#                         {"id": 103, "value": "Payment received successfully."}
#                     ]
#                 }
#             }
#         )


# def test_reject_mining_request_success():
#     data = {
#         "mining_request_id": "101"
#     }

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#          patch("services.gsmb_officer_service.requests.put") as mock_put, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

#         # Mock successful PUT request
#         mock_put.return_value = MagicMock(status_code=204, text="")

#         result, error = GsmbOfficerService.reject_mining_request("fake-token", data)

#         assert result is True
#         assert error is None
#         mock_put.assert_called_once_with(
#             "https://redmine.example.com/issues/101.json",
#             headers={
#                 "X-Redmine-API-Key": "user-api-key",
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "issue": {
#                     "status_id": 6
#                 }
#             }
#         )

# def test_get_mlownersDetails_success():
#     token = "fake-token"

#     # Mock memberships API response
#     memberships_data = {
#         "memberships": [
#             {
#                 "user": {"id": 1},
#                 "roles": [{"name": "MLOwner"}]
#             },
#             {
#                 "user": {"id": 2},
#                 "roles": [{"name": "OtherRole"}]
#             }
#         ]
#     }

#     # Mock users API response
#     users_data = {
#         "users": [
#             {
#                 "id": 1,
#                 "firstname": "John",
#                 "lastname": "Doe",
#                 "custom_fields": [
#                     {"name": "National Identity Card", "value": "123456789V"}
#                 ]
#             },
#             {
#                 "id": 2,
#                 "firstname": "Jane",
#                 "lastname": "Smith",
#                 "custom_fields": [
#                     {"name": "National Identity Card", "value": "987654321X"}
#                 ]
#             }
#         ]
#     }

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#          patch("services.gsmb_officer_service.requests.get") as mock_get, \
#          patch.dict("os.environ", {
#              "REDMINE_ADMIN_API_KEY": "admin-api-key",
#              "REDMINE_URL": "https://redmine.example.com"
#          }):

#         # Configure mock responses
#         def side_effect(url, headers):
#             if "memberships" in url:
#                 return MagicMock(status_code=200, json=MagicMock(return_value=memberships_data))
#             elif "users" in url:
#                 return MagicMock(status_code=200, json=MagicMock(return_value=users_data))
#             else:
#                 return MagicMock(status_code=404, text="Not Found")

#         mock_get.side_effect = side_effect

#         result, error = GsmbOfficerService.get_mlownersDetails(token)

#         assert error is None
#         assert result == [
#             {
#                 "id": 1,
#                 "ownerName": "John Doe",
#                 "NIC": "123456789V"
#             }
#         ]

#         # Assert calls
#         assert mock_get.call_count == 2
#         mock_get.assert_any_call(
#             "https://redmine.example.com/projects/mmpro-gsmb/memberships.json",
#             headers={"X-Redmine-API-Key": "user-api-key", "Content-Type": "application/json"}
#         )
#         mock_get.assert_any_call(
#             "https://redmine.example.com/users.json?status=1&limit=100",
#             headers={"X-Redmine-API-Key": "admin-api-key", "Content-Type": "application/json"}
#         )

# def test_get_appointments_success():
#     token = "fake-token"

#     # Mock Redmine issues API response
#     issues_data = {
#         "issues": [
#             {
#                 "id": 1,
#                 "subject": "Appointment 1",
#                 "status": {"name": "Open"},
#                 "author": {"name": "Officer A"},
#                 "tracker": {"name": "Appointment"},
#                 "assigned_to": {"name": "Assignee A"},
#                 "start_date": "2025-06-01",
#                 "due_date": "2025-06-10",
#                 "description": "Appointment description",
#                 "custom_fields": [
#                     {"name": "Mining License Number", "value": "ML-001"}
#                 ]
#             },
#             {
#                 "id": 2,
#                 "subject": "Appointment 2",
#                 "status": {"name": "Closed"},
#                 "author": {"name": "Officer B"},
#                 "tracker": {"name": "Appointment"},
#                 "assigned_to": None,
#                 "start_date": "2025-06-05",
#                 "due_date": "2025-06-15",
#                 "description": "Another appointment",
#                 "custom_fields": []
#             }
#         ]
#     }

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#          patch("services.gsmb_officer_service.requests.get") as mock_get, \
#          patch.dict("os.environ", {
#              "REDMINE_URL": "https://redmine.example.com"
#          }), \
#          patch.object(GsmbOfficerService, "get_custom_field_value", side_effect=lambda cf_list, field_name: next((cf["value"] for cf in cf_list if cf["name"] == field_name), "")):

#         # Configure mock response
#         mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=issues_data))

#         result, error = GsmbOfficerService.get_appointments(token)

#         assert error is None
#         assert result == [
#             {
#                 "id": 1,
#                 "subject": "Appointment 1",
#                 "status": "Open",
#                 "author": "Officer A",
#                 "tracker": "Appointment",
#                 "assigned_to": "Assignee A",
#                 "start_date": "2025-06-01",
#                 "due_date": "2025-06-10",
#                 "description": "Appointment description",
#                 "mining_license_number": "ML-001"
#             },
#             {
#                 "id": 2,
#                 "subject": "Appointment 2",
#                 "status": "Closed",
#                 "author": "Officer B",
#                 "tracker": "Appointment",
#                 "assigned_to": None,
#                 "start_date": "2025-06-05",
#                 "due_date": "2025-06-15",
#                 "description": "Another appointment",
#                 "mining_license_number": ""
#             }
#         ]

#         # Assert call
#         mock_get.assert_called_once_with(
#             "https://redmine.example.com/issues.json?tracker_id=11&project_id=1",
#             headers={"X-Redmine-API-Key": "user-api-key", "Content-Type": "application/json"}
#         )

# def test_create_appointment_success():
#     token = "fake-token"
#     assigned_to_id = 5
#     physical_meeting_location = "Mining Office"
#     start_date = "2025-06-15"
#     description = "Discuss mining license"
#     mining_request_id = "1001"

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#          patch("services.gsmb_officer_service.JWTUtils.decode_jwt_and_get_user_id", return_value=42), \
#          patch("services.gsmb_officer_service.requests.post") as mock_post, \
#          patch("services.gsmb_officer_service.requests.put") as mock_put, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

#         # Mock POST response for creating appointment
#         mock_post.return_value = MagicMock(
#             status_code=201,
#             json=MagicMock(return_value={"issue": {"id": 999}})
#         )

#         # Mock PUT response for updating mining request
#         mock_put.return_value = MagicMock(status_code=204)

#         result, error = GsmbOfficerService.create_appointment(
#             token,
#             assigned_to_id,
#             physical_meeting_location,
#             start_date,
#             description,
#             mining_request_id
#         )

#         assert error is None
#         assert result == 999

#         # Check that POST request was made with correct data
#         mock_post.assert_called_once()
#         posted_url, posted_kwargs = mock_post.call_args
#         assert posted_url[0] == "https://redmine.example.com/issues.json"
#         assert "application/json" in posted_kwargs["headers"]["Content-Type"]

#         # Check that PUT request was made with correct URL
#         mock_put.assert_called_once_with(
#             f"https://redmine.example.com/issues/{mining_request_id}.json",
#             headers={"X-Redmine-API-Key": "user-api-key", "Content-Type": "application/json"},
#             data=json.dumps({"issue": {"status_id": 34}})
#         )

# def test_approve_mining_license_success():
#     token = "fake-token"
#     issue_id = 123
#     new_status_id = 10

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#          patch("services.gsmb_officer_service.requests.put") as mock_put, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

#         # Mock successful response
#         mock_put.return_value = MagicMock(status_code=204)

#         result = GsmbOfficerService.approve_mining_license(token, issue_id, new_status_id)

#         assert result['success'] is True
#         assert result['message'] == "License approved and updated successfully"

#         # Verify the correct API call was made
#         mock_put.assert_called_once_with(
#             f"https://redmine.example.com/issues/{issue_id}.json",
#             headers={
#                 "X-Redmine-API-Key": "user-api-key",
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "issue": {
#                     "status_id": new_status_id,
#                     "subject": "Approved by (GSMB)",
#                     "custom_fields": [
#                         {
#                             "id": 101,
#                             "name": "Mining License Number",
#                             "value": f"LLL/100/{issue_id}"
#                         }
#                     ]
#                 }
#             }
#         )

# def test_change_issue_status_success():
#     token = "fake-token"
#     issue_id = 456
#     new_status_id = 12

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#          patch("services.gsmb_officer_service.requests.put") as mock_put, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

#         # Mock successful response
#         mock_put.return_value = MagicMock(status_code=204)

#         result, error = GsmbOfficerService.change_issue_status(token, issue_id, new_status_id)

#         assert result is True
#         assert error is None

#         # Verify correct API call
#         mock_put.assert_called_once_with(
#             f"https://redmine.example.com/issues/{issue_id}.json",
#             headers={
#                 "X-Redmine-API-Key": "user-api-key",
#                 "Content-Type": "application/json"
#             },
#             data=json.dumps({
#                 "issue": {
#                     "status_id": new_status_id
#                 }
#             })
#         )

# def test_mark_complaint_resolved_success():
#     token = "fake-token"
#     issue_id = 789

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#          patch("services.gsmb_officer_service.requests.put") as mock_put, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}):

#         # Mock successful response
#         mock_put.return_value = MagicMock(status_code=204)

#         result, error = GsmbOfficerService.mark_complaint_resolved(token, issue_id)

#         assert result is True
#         assert error is None

#         # Verify correct API call
#         mock_put.assert_called_once_with(
#             f"https://redmine.example.com/issues/{issue_id}.json",
#             headers={
#                 "X-Redmine-API-Key": "user-api-key",
#                 "Content-Type": "application/json"
#             },
#             data=json.dumps({
#                 "issue": {
#                     "custom_fields": [
#                         {
#                             "id": 107,
#                             "value": "1"
#                         }
#                     ]
#                 }
#             })
#         )

# def test_get_mining_license_request_success():
#     token = "fake-token"
#     mock_issues = [
#         {
#             "id": 123,
#             "subject": "Test Mining License",
#             "assigned_to": {"name": "John Doe", "id": 5},
#             "custom_fields": [
#                 {"name": "Mobile Number", "value": "0771234567"},
#                 {"name": "Administrative District", "value": "District A"}
#             ],
#             "created_on": "2025-06-10T12:00:00Z",
#             "status": {"name": "New"}
#         }
#     ]

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#          patch("services.gsmb_officer_service.requests.get") as mock_get, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}), \
#          patch.object(GsmbOfficerService, "get_custom_field_value", side_effect=lambda fields, name: next((f["value"] for f in fields if f["name"] == name), None)):

#         mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value={"issues": mock_issues}))

#         result, error = GsmbOfficerService.get_mining_license_request(token)

#         assert error is None
#         assert isinstance(result, list)
#         assert len(result) == 1
#         assert result[0]["id"] == 123
#         assert result[0]["subject"] == "Test Mining License"
#         assert result[0]["assigned_to"] == "John Doe"
#         assert result[0]["assigned_to_id"] == 5
#         assert result[0]["mobile"] == "0771234567"
#         assert result[0]["district"] == "District A"
#         assert result[0]["date_created"] == "2025-06-10T12:00:00Z"
#         assert result[0]["status"] == "New"

#         mock_get.assert_called_once_with(
#             "https://redmine.example.com/issues.json?tracker_id=4&project_id=1&status_id=!7",
#             headers={
#                 "X-Redmine-API-Key": "user-api-key",
#                 "Content-Type": "application/json"
#             }
#         )

# def test_get_miningRequest_view_button_success():
#     token = "fake-token"
#     issue_id = 123
#     mock_issue = {
#         "id": issue_id,
#         "subject": "Mining Request Example",
#         "status": {"name": "Open"},
#         "assigned_to": {"name": "Jane Doe"},
#         "custom_fields": [
#             {"name": "Land Name(Licence Details)", "value": "Green Valley"},
#             {"name": "Land owner name", "value": "John Smith"},
#             {"name": "Name of village ", "value": "Village X"},
#             {"name": "Grama Niladhari Division", "value": "Division A"},
#             {"name": "Divisional Secretary Division", "value": "Division B"},
#             {"name": "Administrative District", "value": "District Y"},
#             {"name": "Mining License Number", "value": "LLL/100/123"},
#             {"name": "Mobile Number", "value": "0771234567"}
#         ]
#     }
#     attachments_mock = {
#         "Economic Viability Report": "http://example.com/economic_report.pdf",
#         "License fee receipt": "http://example.com/license_fee.pdf",
#         "Detailed Mine Restoration Plan": "http://example.com/restoration_plan.pdf",
#         "Deed and Survey Plan": "http://example.com/deed_survey.pdf",
#         "Payment Receipt": "http://example.com/payment_receipt.pdf",
#         "License Boundary Survey": "http://example.com/boundary_survey.pdf"
#     }

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#          patch("services.gsmb_officer_service.requests.get") as mock_get, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}), \
#          patch.object(GsmbOfficerService, "get_attachment_urls", return_value=attachments_mock):

#         mock_get.return_value = MagicMock(
#             status_code=200,
#             json=MagicMock(return_value={"issue": mock_issue})
#         )

#         result, error = GsmbOfficerService.get_miningRequest_view_button(token, issue_id)

#         assert error is None
#         assert isinstance(result, dict)
#         assert result["id"] == issue_id
#         assert result["subject"] == "Mining Request Example"
#         assert result["status"] == "Open"
#         assert result["assigned_to"] == "Jane Doe"
#         assert result["land_name"] == "Green Valley"
#         assert result["land_owner_name"] == "John Smith"
#         assert result["village_name"] == "Village X"
#         assert result["grama_niladhari_division"] == "Division A"
#         assert result["divisional_secretary_division"] == "Division B"
#         assert result["administrative_district"] == "District Y"
#         assert result["mining_license_number"] == "LLL/100/123"
#         assert result["mobile_number"] == "0771234567"

#         # Check attachment URLs are included
#         assert result["economic_viability_report"] == attachments_mock["Economic Viability Report"]
#         assert result["license_fee_receipt"] == attachments_mock["License fee receipt"]

#         mock_get.assert_called_once_with(
#             "https://redmine.example.com/issues/123.json?include=attachments",
#             headers={
#                 "X-Redmine-API-Key": "user-api-key",
#                 "Content-Type": "application/json"
#             }
#         )

# def test_get_miningLicense_view_button_success():
#     token = "fake-token"
#     issue_id = 456
#     mock_issue = {
#         "id": issue_id,
#         "subject": "Mining License Example",
#         "start_date": "2025-06-01",
#         "due_date": "2026-06-01",
#         "status": {"name": "Approved"},
#         "assigned_to": {"name": "John Doe"},
#         "custom_fields": [
#             {"name": "Land Name(Licence Details)", "value": "Blue Hills"},
#             {"name": "Land owner name", "value": "Alice Smith"},
#             {"name": "Name of village ", "value": "Village Y"},
#             {"name": "Grama Niladhari Division", "value": "Division C"},
#             {"name": "Capacity", "value": "1000"},
#             {"name": "Used", "value": "600"},
#             {"name": "Remaining", "value": "400"},
#             {"name": "Exploration Licence No", "value": "EXP-789"},
#             {"name": "Royalty", "value": "5%"},
#             {"name": "Divisional Secretary Division", "value": "Division D"},
#             {"name": "Administrative District", "value": "District Z"},
#             {"name": "Mining License Number", "value": "LLL/100/456"},
#             {"name": "Mobile Number", "value": "0789876543"},
#         ]
#     }

#     attachments_mock = {
#         "Economic Viability Report": "http://example.com/economic_viability.pdf",
#         "License fee receipt": "http://example.com/license_fee.pdf",
#         "Detailed Mine Restoration Plan": "http://example.com/mine_restoration.pdf",
#         "Deed and Survey Plan": "http://example.com/deed_survey.pdf",
#         "Payment Receipt": "http://example.com/payment_receipt.pdf",
#         "License Boundary Survey": "http://example.com/boundary_survey.pdf"
#     }

#     with patch("services.gsmb_officer_service.JWTUtils.get_api_key_from_token", return_value="user-api-key"), \
#          patch("services.gsmb_officer_service.requests.get") as mock_get, \
#          patch.dict("os.environ", {"REDMINE_URL": "https://redmine.example.com"}), \
#          patch.object(GsmbOfficerService, "get_attachment_urls", return_value=attachments_mock):

#         mock_get.return_value = MagicMock(
#             status_code=200,
#             json=MagicMock(return_value={"issue": mock_issue})
#         )

#         result, error = GsmbOfficerService.get_miningLicense_view_button(token, issue_id)

#         assert error is None
#         assert isinstance(result, dict)
#         assert result["id"] == issue_id
#         assert result["subject"] == "Mining License Example"
#         assert result["start_date"] == "2025-06-01"
#         assert result["due_date"] == "2026-06-01"
#         assert result["status"] == "Approved"
#         assert result["assigned_to"] == "John Doe"
#         assert result["land_name"] == "Blue Hills"
#         assert result["land_owner_name"] == "Alice Smith"
#         assert result["village_name"] == "Village Y"
#         assert result["grama_niladhari_division"] == "Division C"
#         assert result["capacity"] == "1000"
#         assert result["used"] == "600"
#         assert result["remaining"] == "400"
#         assert result["exploration_licence_no"] == "EXP-789"
#         assert result["royalty"] == "5%"
#         assert result["divisional_secretary_division"] == "Division D"
#         assert result["administrative_district"] == "District Z"
#         assert result["mining_license_number"] == "LLL/100/456"
#         assert result["mobile_number"] == "0789876543"

#         # Check attachment URLs are included
#         for key in attachments_mock:
#             assert result[key.lower().replace(" ", "_")] == attachments_mock[key]

#         mock_get.assert_called_once_with(
#             "https://redmine.example.com/issues/456.json?include=attachments",
#             headers={
#                 "X-Redmine-API-Key": "user-api-key",
#                 "Content-Type": "application/json"
#             }
#         )