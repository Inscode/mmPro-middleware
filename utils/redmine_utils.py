# utils/redmine_utils.py
import os
import requests
from flask import jsonify, Response, request
from utils.jwt_utils import JWTUtils  # adjust this import according to your project

def download_attachment_by_id(attachment_id):
    try:
        token = request.headers.get('Authorization')
        api_key = JWTUtils.get_api_key_from_token(token)
        
        REDMINE_URL = os.getenv("REDMINE_URL")
        attachment_url = f"{REDMINE_URL}/attachments/download/{attachment_id}"
        
        response = requests.get(
            attachment_url,
            headers={"X-Redmine-API-Key": api_key},
            stream=True
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch attachment"}), response.status_code
            
        return Response(
            response.iter_content(chunk_size=1024),
            content_type=response.headers.get('Content-Type', 'application/octet-stream'),
            headers={
                'Content-Disposition': response.headers.get(
                    'Content-Disposition', 
                    f'attachment; filename=attachment_{attachment_id}'
                )
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
