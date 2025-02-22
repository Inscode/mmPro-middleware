import os
import requests

class LimitUtils:
    @staticmethod
    def get_limit():
        try:
            # REDMINE_URL = os.getenv("REDMINE_URL")
            # API_KEY = os.getenv("REDMINE_ADMIN_API_KEY")
            REDMINE_URL = "http://redmine.aasait.lk"
            API_KEY = "3042ca9b23e30cdadd71d1e23fa35eb46a3487a9"
            if not REDMINE_URL or not API_KEY:
                return None, "Redmine URL or API Key is missing"
            
            headers = {
                "X-Redmine-API-Key": API_KEY,
                "Content-Type": "application/json"
            }
            
            url = f"{REDMINE_URL}/projects/gsmb/issues.json"
            print(f"Requesting: {url}")

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                return None, f"Failed to fetch issues: {response.status_code} - {response.text}"

            data = response.json()
            issues = data.get("issues", [0][0])
            latest_issue_id = issues[0].get("id")

            return latest_issue_id, None  # Return the issues list and no error

        except Exception as e:
            return None, f"Server error: {str(e)}"

# # Example usage:
# id, error = LimitUtils.get_limit()
# if error:
#     print(f"Error: {error}")
# else:
#     print(f"latest_issue_id:",id)
