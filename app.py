from flask import Flask
from flask_cors import CORS
import os
from controllers import (
    auth_bp, mining_owner_bp, gsmb_officer_bp, 
    police_officer_bp, general_public_bp, 
    mining_enginer_bp, gsmb_management_bp,
    director_general_bp
)

def create_app(config_filename='.env'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_pyfile(config_filename)
    
    # Parse allowed origins from .env
    allowed_origins = []
    if 'ALLOWED_ORIGINS' in app.config:
        allowed_origins = [
            origin.strip() 
            for origin in app.config['ALLOWED_ORIGINS'].split(',')
            if origin.strip()
        ]
    
    # Secure CORS configuration
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "supports_credentials": True,  
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
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

if __name__ == '__main__':
    app = create_app()
    print("Server is running on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)