import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    REDMINE_ADMIN_API_KEY = os.getenv('REDMINE_ADMIN_API_KEY')
    REDMINE_URL = os.getenv('REDMINE_URL','http://redmine.aasait.lk')
    PROJECT_ID = 31
    MINING_LICENSE_TRACKER_ID = 7
