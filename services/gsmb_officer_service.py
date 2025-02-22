import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from utils.jwt_utils import JWTUtils
from utils.MLOUtils import MLOUtils
from flask import request



load_dotenv()

class GsmbOfficerService:
    @staticmethod
    def get_Issues_Data(token):  # Accept token as a parameter
        try:
            # Use the passed token here
            api_key = JWTUtils.get_api_key_from_token(token)

            if not api_key:
                return None, "API Key is missing"

            REDMINE_URL = os.getenv("REDMINE_URL")

            if not REDMINE_URL:
                return None, "Redmine URL is missing"

            headers = {
                "X-Redmine-API-Key": api_key,
                "Content-Type": "application/json"
            }

            url = f"{REDMINE_URL}/projects/gsmb/issues.json"
            print(f"Fetching data from URL: {url}")

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

            issues = response.json().get("issues", [])
            print(f"Issues retrieved: {issues}")

            return issues, None  # Returning the list of issues and no error

        except Exception as e:
            return None, f"Server error: {str(e)}"
