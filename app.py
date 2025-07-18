import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from controllers import (
    auth_bp, mining_owner_bp, gsmb_officer_bp, 
    police_officer_bp, general_public_bp, 
    mining_enginer_bp, gsmb_management_bp,
    director_general_bp
)

def create_app():

    load_dotenv(dotenv_path=".env")

    app = Flask(__name__) # NOSONAR: JWT-based API, CSRF not required

    # ⚠️ SECURITY NOTE:
    # Ensure disabling CSRF protection is safe for your use case.
    # - If you're building a REST API using JWT or token-based authentication, CSRF protection is typically not needed.
    # - If you're using session-based auth or handling form submissions via cookies, enable CSRF protection (e.g., via Flask-WTF).
    
    app.config['TEXTWARE_USERNAME'] = os.getenv('TEXTWARE_USERNAME')
    app.config['TEXTWARE_PASSWORD'] = os.getenv('TEXTWARE_PASSWORD')
    app.config['TEST_USERNAME'] = os.getenv('TEST_USERNAME')
    app.config['TEST_PASSWORD'] = os.getenv('TEST_PASSWORD')
    app.config['INVALID_TEST_USERNAME'] = os.getenv('INVALID_TEST_USERNAME')
    app.config['INVALID_TEST_PASSWORD'] = os.getenv('INVALID_TEST_PASSWORD')

    # Load configuration
    # app.config.from_pyfile(config_filename)
    
    # Enable CORS
    # CORS(app)
    # Or your specific CORS config if needed:
    CORS(app, resources={r"/*": {"origins": ["http://localhost:5173"]}})
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(mining_enginer_bp, url_prefix='/mining-engineer')
    app.register_blueprint(mining_owner_bp, url_prefix='/mining-owner')
    app.register_blueprint(gsmb_officer_bp, url_prefix='/gsmb-officer')
    app.register_blueprint(police_officer_bp, url_prefix='/police-officer')
    app.register_blueprint(general_public_bp, url_prefix='/general-public')
    app.register_blueprint(gsmb_management_bp, url_prefix='/gsmb-management')
    app.register_blueprint(director_general_bp, url_prefix='/director-general')
    
    return app

# For running directly
if __name__ == '__main__':
    app = create_app()
    print("Server is running on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)