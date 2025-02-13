from flask import Flask
from flask_cors import CORS
from controllers import auth_bp, mining_owner_bp, gsmb_officer_bp, police_officer_bp, general_public_bp
import os

app = Flask(__name__)
CORS(app)

# Load environment variables
app.config.from_pyfile('.env')

# Register Blueprints for each role-based controller
app.register_blueprint(mining_owner_bp, url_prefix='/mining-owner')
app.register_blueprint(gsmb_officer_bp, url_prefix='/gsmb-officer')
app.register_blueprint(police_officer_bp, url_prefix='/police-officer')
app.register_blueprint(general_public_bp, url_prefix='/general-public')
app.register_blueprint(auth_bp, url_prefix='/auth')

if __name__ == '__main__':
    app.run(debug=True)



# import time

# while True:
#     print("hello")
#     time.sleep(3)  # Wait for 3 seconds before printing again

