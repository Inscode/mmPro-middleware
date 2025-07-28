from datetime import datetime, timedelta, timezone
import os
import requests
from dotenv import load_dotenv
from utils.jwt_utils import JWTUtils
from utils.user_utils import UserUtils
from utils.constants import CONTENT_TYPE_JSON, REDMINE_API_ERROR_MSG

load_dotenv()

REDMINE_URL = os.getenv("REDMINE_URL")


class PoliceOfficerService:
    @staticmethod
    def check_lorry_number(lorry_number, token):
        try:
            api_key = JWTUtils.get_api_key_from_token(token)
            if not REDMINE_URL or not api_key:
                return None, REDMINE_API_ERROR_MSG

            headers = {"X-Redmine-API-Key": api_key}
            current_time = datetime.now(timezone.utc)

            tpl_issue, is_valid, created_on, estimated_hours = (
                PoliceOfficerService._get_valid_tpl_issue(lorry_number.lower(), headers, current_time)
            )

            if not tpl_issue:
                return None, "No valid (non-expired) TPL with this lorry number"

            tpl_data = PoliceOfficerService._extract_tpl_data(tpl_issue, is_valid, created_on, estimated_hours)

            license_number = tpl_data["LicenseNumber"]
            if license_number:
                mining_data = PoliceOfficerService._get_mining_license_data(license_number, headers)
                if mining_data:
                    tpl_data.update(mining_data)

            return tpl_data, None

        except Exception as e:
            return None, f"Server error: {str(e)}"

    @staticmethod
    def _get_valid_tpl_issue(lorry_number, headers, now_utc):
        tpl_params = {"tracker_id": 5}
        response = requests.get(f"{REDMINE_URL}/issues.json", params=tpl_params, headers=headers)
        if response.status_code != 200:
            return None, None, None, None

        for issue in response.json().get("issues", []):
            if not PoliceOfficerService._lorry_number_matches(issue, lorry_number):
                continue

            created_str = issue.get("created_on")
            if not created_str:
                continue

            try:
                created_on = datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                estimated_hours = float(issue.get("estimated_hours", 0))
                expires_at = created_on + timedelta(hours=estimated_hours)
                is_valid = now_utc < expires_at
                return issue, is_valid, created_on, estimated_hours
            except Exception as e:
                print(f"Error parsing issue {issue.get('id')}: {e}")
                continue

        return None, None, None, None

    @staticmethod
    def _lorry_number_matches(issue, lorry_number):
        return any(
            cf["id"] == 53 and cf.get("value") and str(cf["value"]).lower() == lorry_number
            for cf in issue.get("custom_fields", [])
        )

    @staticmethod
    def _extract_tpl_data(issue, is_valid, created_on, estimated_hours):
        cf = issue.get("custom_fields", [])
        offset = timedelta(hours=5, minutes=30)
        created_sl = created_on + offset

        def get_cf(id_):
            return next((c["value"] for c in cf if c["id"] == id_), None)

        return {
            "LicenseNumber": get_cf(59),
            "Cubes": get_cf(58),
            "Destination": get_cf(68),
            "ValidUntil": (created_sl + timedelta(hours=estimated_hours)).strftime("%A, %B %d, %Y at %I:%M %p"),
            "Route_01": get_cf(55),
            "Route_02": get_cf(56),
            "Route_03": get_cf(57),
            "IsValid": is_valid,
            "Assignee": issue["assigned_to"]["name"] if isinstance(issue.get("assigned_to"), dict) else str(issue.get("assigned_to")),
        }

    @staticmethod
    def _get_mining_license_data(license_number, headers):
        ml_params = {"tracker_id": 4, "status_id": "*"}
        response = requests.get(f"{REDMINE_URL}/issues.json", params=ml_params, headers=headers)
        if response.status_code != 200:
            return None

        for issue in response.json().get("issues", []):
            for cf in issue.get("custom_fields", []):
                if cf.get("id") == 101 and str(cf.get("value")) == str(license_number):
                    return {
                        "owner": issue["assigned_to"]["name"] if isinstance(issue["assigned_to"], dict) else str(issue["assigned_to"]),
                        "License Start Date": issue.get("start_date"),
                        "License End Date": issue.get("due_date"),
                        "License Owner Contact Number": next((cf["value"] for cf in issue["custom_fields"] if cf.get("id") == 66), None),
                        "Grama Niladhari Division": next((cf["value"] for cf in issue["custom_fields"] if cf.get("id") == 31), None),
                    }
        return None

    @staticmethod
    def create_complaint(vehicle_number, user_id, token):
        phone_number = UserUtils.get_user_phone(user_id)

        issue_data = {
            'issue': {
                'project_id': 1,
                'tracker_id': 6,
                'subject': "New Complaint",
                'status_id': 1,
                'priority_id': 2,
                'assigned_to_id': 8,
                'custom_fields': [
                    {'id': 66, 'name': "Mobile Number", 'value': phone_number},
                    {'id': 53, 'name': "Lorry Number", 'value': vehicle_number},
                    {'id': 67, 'name': "Role", 'value': "PoliceOfficer"}
                ]
            }
        }

        api_key = JWTUtils.get_api_key_from_token(token)
        response = requests.post(
            f'{REDMINE_URL}/issues.json',
            json=issue_data,
            headers={'X-Redmine-API-Key': api_key, 'Content-Type': CONTENT_TYPE_JSON}
        )

        if response.status_code == 201:
            issue_id = response.json()['issue']['id']
            return True, issue_id
        else:
            return False, 'Failed to create complaint'
