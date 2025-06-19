import pytest
from unittest.mock import patch
from flask import Flask, jsonify
from utils.jwt_utils import JWTUtils
from io import BytesIO
from werkzeug.datastructures import FileStorage



@pytest.fixture
def valid_token():
    tokens = JWTUtils.create_jwt_token(user_id=1, user_role='miningEngineer')
    return f"Bearer {tokens['access_token']}"


class TestMiningEngineerController:

    ### --- /miningOwner-appointment/<int:issue_id> [PUT] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.update_miningOwner_appointment')
    def test_miningOwner_appointment_success(self, mock_service, client, valid_token):
        mock_service.return_value = ({"msg": "updated"}, None)
        json_data = {
            "appointment_date": "2025-06-20",
            "status": "confirmed"
        }
        res = client.put(
            '/mining-engineer/miningOwner-appointment/123',
            headers={"Authorization": valid_token},
            json=json_data
        )
        assert res.status_code == 200


    @patch('services.mining_engineer_service.MiningEnginerService.update_miningOwner_appointment')
    def test_miningOwner_appointment_service_error(self, mock_service, client, valid_token):
        mock_service.return_value = (None, "Server error occurred")
        res = client.put('/mining-engineer/miningOwner-appointment/123', headers={"Authorization": valid_token})
        assert res.status_code == 500
        assert "error" in res.json
        assert res.json["error"] is not None


    def test_miningOwner_appointment_missing_token(self, client, valid_token):
        res = client.put('/mining-engineer/miningOwner-appointment/123')
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /me-pending-licenses [GET] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.get_me_pending_licenses')
    def test_me_pending_licenses_success(self, mock_service, client, valid_token):
        mock_service.return_value = (["license1", "license2"], None)
        res = client.get('/mining-engineer/me-pending-licenses', headers={"Authorization": valid_token})
        assert res.status_code == 200
        assert res.json["success"] is True

    @patch('services.mining_engineer_service.MiningEnginerService.get_me_pending_licenses')
    def test_me_pending_licenses_service_error(self, mock_service, client, valid_token):
        mock_service.return_value = (None, "Bad request error")
        res = client.get('/mining-engineer/me-pending-licenses', headers={"Authorization": valid_token})
        assert res.status_code == 400
        assert "error" in res.json

    def test_me_pending_licenses_missing_token(self, client, valid_token):
        res = client.get('/mining-engineer/me-pending-licenses')
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /create-ml-appointment [POST] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.create_ml_appointment')
    def test_create_ml_appointment_success(self, mock_service, client, valid_token):
        mock_service.return_value = ({"appointment_id": 1}, None)
        json_data = {
            "start_date": "2025-06-20",
            "mining_license_number": "LLL/100/206",
            "Google_location": "7.8731,80.7718"
        }
        res = client.post(
            '/mining-engineer/create-ml-appointment',
            headers={"Authorization": valid_token},
            json=json_data
        )
        assert res.status_code == 201


    @patch('services.mining_engineer_service.MiningEnginerService.create_ml_appointment')
    def test_create_ml_appointment_service_error(self, mock_service, client, valid_token):
        # Change error message to include 'Redmine error'
        mock_service.return_value = (None, "Redmine error: Server error")

        json_data = {
            "start_date": "2025-06-20",
            "mining_license_number": "LLL/100/206",
            "Google_location": "7.8731,80.7718"
        }

        res = client.post(
            '/mining-engineer/create-ml-appointment',
            headers={"Authorization": valid_token},
            json=json_data
        )
        assert res.status_code == 500




    def test_create_ml_appointment_missing_token(self, client, valid_token):
        res = client.post('/mining-engineer/create-ml-appointment', json={"data": "test"})
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /miningEngineer-approve/<int:me_appointment_issue_id> [PUT] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.miningEngineer_approve')
    def test_miningEngineer_approve_success(self, mock_service, client, valid_token):
        mock_service.return_value = ({"msg": "approved"}, None)

        data = {
            "ml_number": "ML Request LLL/100/206",
            "me_comment": "Approved after review",
            "me_report": (BytesIO(b"dummy file content"), "report.pdf"),
        }

        res = client.put(
            '/mining-engineer/miningEngineer-approve/10',
            headers={"Authorization": valid_token},
            data=data,
            content_type='multipart/form-data',
        )

        assert res.status_code == 200
        assert res.json.get("message") == "Mining license updated successfully"

    @patch('services.mining_engineer_service.MiningEnginerService.miningEngineer_approve')
    def test_miningEngineer_approve_service_error(self, mock_service, client, valid_token):
        mock_service.return_value = (None, "Error approving")
        res = client.put('/mining-engineer/miningEngineer-approve/10', headers={"Authorization": valid_token})
        assert res.status_code == 400
        assert "error" in res.json

    def test_miningEngineer_approve_missing_token(self, client, valid_token):
        res = client.put('/mining-engineer/miningEngineer-approve/10')
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /miningEngineer-reject/<int:me_appointment_issue_id> [PUT] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.miningEngineer_reject')
    def test_miningEngineer_reject_success(self, mock_service, client, valid_token):
        mock_service.return_value = ({"msg": "rejected"}, None)
        
        data = {
            "ml_number": "ML Request LLL/100/206",
            "me_comment": "Rejecting due to incomplete documents",
            "me_report": (BytesIO(b"dummy file content"), "report.pdf")  # file as tuple
        }
        
        res = client.put(
            '/mining-engineer/miningEngineer-reject/10',
            headers={"Authorization": valid_token},
            data=data,
            content_type='multipart/form-data'
        )
        
        assert res.status_code == 200
        assert "message" in res.json
        assert res.json["message"] == "Mining license rejected successfully"


    @patch('services.mining_engineer_service.MiningEnginerService.miningEngineer_reject')
    def test_miningEngineer_reject_service_error(self, mock_service, client, valid_token):
        mock_service.return_value = (None, "Error rejecting")
        res = client.put('/mining-engineer/miningEngineer-reject/10', headers={"Authorization": valid_token})
        assert res.status_code == 400
        assert "error" in res.json

    def test_miningEngineer_reject_missing_token(self, client, valid_token):
        res = client.put('/mining-engineer/miningEngineer-reject/10')
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /update-issue-status [POST] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.change_issue_status')
    def test_update_issue_status_success(self, mock_service, client, valid_token):
        mock_service.return_value = ({"msg": "status updated"}, None)
        res = client.post(
            '/mining-engineer/update-issue-status', 
            headers={"Authorization": valid_token}, 
            json={"issue_id": 123, "new_status_id": 1}
        )
        assert res.status_code == 200
        assert res.json["success"] is True


    @patch('services.mining_engineer_service.MiningEnginerService.change_issue_status')
    def test_update_issue_status_service_error(self, mock_service, client, valid_token):
        # Mock the service to return an error
        mock_service.return_value = (None, "Server error")
        
        # Send required keys in JSON so it doesn't get 400 from controller validation
        res = client.post(
            '/mining-engineer/update-issue-status',
            headers={"Authorization": valid_token},
            json={"issue_id": 123, "new_status_id": 456}
        )
        
        assert res.status_code == 500
        assert res.json["error"] == "Server error"


    def test_update_issue_status_missing_token(self, client, valid_token):
        res = client.post('/mining-engineer/update-issue-status', json={"status": "new"})
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /me-meetingeShedule-licenses [GET] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.get_me_meetingeShedule_licenses')
    def test_me_meeting_schedule_licenses_success(self, mock_service, client, valid_token):
        mock_service.return_value = (["meeting1", "meeting2"], None)
        res = client.get('/mining-engineer/me-meetingeShedule-licenses', headers={"Authorization": valid_token})
        assert res.status_code == 200
        assert res.json["success"] is True

    @patch('services.mining_engineer_service.MiningEnginerService.get_me_meetingeShedule_licenses')
    def test_me_meeting_schedule_licenses_service_error(self, mock_service, client, valid_token):
        mock_service.return_value = (None, "Bad request")
        res = client.get('/mining-engineer/me-meetingeShedule-licenses', headers={"Authorization": valid_token})
        assert res.status_code == 400
        assert "error" in res.json

    def test_me_meeting_schedule_licenses_missing_token(self, client, valid_token):
        res = client.get('/mining-engineer/me-meetingeShedule-licenses')
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /me-appointments [GET] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.get_me_appointments')
    def test_me_appointments_success(self, mock_service, client, valid_token):
        mock_service.return_value = (["app1", "app2"], None)
        res = client.get('/mining-engineer/me-appointments', headers={"Authorization": valid_token})
        assert res.status_code == 200
        assert isinstance(res.json, list)
        assert res.json[0] == ["app1", "app2"]
        assert res.json[1] is None


    @patch('services.mining_engineer_service.MiningEnginerService.get_me_appointments')
    def test_me_appointments_service_error(self, mock_service, client, valid_token):
        mock_service.return_value = (None, "Server error occurred")
        res = client.get('/mining-engineer/me-appointments', headers={"Authorization": valid_token})
        assert res.status_code == 200  
        assert res.json[1] == "Server error occurred"  




    def test_me_appointments_missing_token(self, client, valid_token):
        res = client.get('/mining-engineer/me-appointments')
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /me-approve-license [GET] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.get_me_approve_license')
    def test_me_approve_license_success(self, mock_service, client, valid_token):
        mock_service.return_value = (["licenseA"], None)
        res = client.get('/mining-engineer/me-approve-license', headers={"Authorization": valid_token})
        assert res.status_code == 200
        assert res.json[0] == ["licenseA"]
        assert res.json[1] is None

    @patch('services.mining_engineer_service.MiningEnginerService.get_me_approve_license')
    def test_me_approve_license_service_error(self, mock_service, client, valid_token):
        mock_service.return_value = (None, "Server error")
        res = client.get('/mining-engineer/me-approve-license', headers={"Authorization": valid_token})
        assert res.status_code == 200
        assert res.json[1] is not None
        assert res.json[1] == "Server error"


    def test_me_approve_license_missing_token(self, client, valid_token):
        res = client.get('/mining-engineer/me-approve-license')
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /me-approve-single-license/<int:issue_id> [GET] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.get_me_approve_single_license')
    def test_me_approve_single_license_success(self, mock_service, client, valid_token):
        mock_service.return_value = ({"success": True, "license": "single"}, None)

        res = client.get('/mining-engineer/me-approve-single-license/15',
                        headers={"Authorization": valid_token})

        assert res.status_code == 200
        assert res.json[0]["success"] is True
        assert res.json[0]["license"] == "single"

    

    @patch('services.mining_engineer_service.MiningEnginerService.get_me_approve_single_license')
    def test_me_approve_single_license_service_error(self, mock_service, client, valid_token):
        mock_service.return_value = (None, "Error fetching license")
        res = client.get('/mining-engineer/me-approve-single-license/15', headers={"Authorization": valid_token})
        assert res.status_code == 200
        assert res.json[1] == "Error fetching license"
        

    def test_me_approve_single_license_missing_token(self, client, valid_token):
        res = client.get('/mining-engineer/me-approve-single-license/15')
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /me-licenses-count [GET] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.get_me_licenses_count')
    def test_me_licenses_count_success(self, mock_service, client, valid_token):
        mock_service.return_value = ({"count": 5}, None)
        res = client.get('/mining-engineer/me-licenses-count', headers={"Authorization": valid_token})
        assert res.status_code == 200
        assert res.json["success"] is True

    @patch('services.mining_engineer_service.MiningEnginerService.get_me_licenses_count')
    def test_me_licenses_count_service_error(self, mock_service, client, valid_token):
        mock_service.return_value = (None, "Server error")
        res = client.get('/mining-engineer/me-licenses-count', headers={"Authorization": valid_token})
        assert res.status_code == 500
        assert "error" in res.json

    def test_me_licenses_count_missing_token(self, client, valid_token):
        res = client.get('/mining-engineer/me-licenses-count')
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /set-license-hold [POST] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.set_license_hold')
    def test_set_license_hold_success(self, mock_service, client, valid_token):
        mock_service.return_value = (True, None)
        res = client.post(
            '/mining-engineer/set-license-hold',
            headers={"Authorization": valid_token},
            json={"issue_id": 7, "reason_for_hold": "Some reason"}
        )
        assert res.status_code == 200


    @patch('services.mining_engineer_service.MiningEnginerService.set_license_hold')
    def test_set_license_hold_service_error(self, mock_service, client, valid_token):
        mock_service.return_value = (None, "Invalid license ID")
        res = client.post('/mining-engineer/set-license-hold', headers={"Authorization": valid_token}, json={"license_id": 7})
        assert res.status_code == 400
        assert "error" in res.json

    def test_set_license_hold_missing_token(self, client, valid_token):
        res = client.post('/mining-engineer/set-license-hold', json={"license_id": 7})
        assert res.status_code == 403
        assert "error" in res.json

    ### --- /me-hold-licenses [GET] --- ###
    @patch('services.mining_engineer_service.MiningEnginerService.get_me_hold_licenses')
    def test_me_hold_licenses_success(self, mock_service, client, valid_token):
        mock_service.return_value = (["hold1", "hold2"], None)
        res = client.get('/mining-engineer/me-hold-licenses', headers={"Authorization": valid_token})
        assert res.status_code == 200
        assert res.json["success"] is True

    @patch('services.mining_engineer_service.MiningEnginerService.get_me_hold_licenses')
    def test_me_hold_licenses_service_error(self, mock_service, client, valid_token):
        mock_service.return_value = (None, "Server error occurred")
        res = client.get('/mining-engineer/me-hold-licenses', headers={"Authorization": valid_token})
        assert res.status_code == 500
        assert "error" in res.json

    def test_me_hold_licenses_missing_token(self, client, valid_token):
        res = client.get('/mining-engineer/me-hold-licenses')
        assert res.status_code == 403
        assert "error" in res.json
