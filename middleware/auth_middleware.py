import jwt
from flask import request, jsonify
from functools import wraps
from config import Config


class TokenValidationError(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def check_token(f):
    """Decorator that extracts, verifies, and decodes the JWT token from the request headers."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token is missing"}), 403

        try:
            token = token.split(" ")[1]  # Remove 'Bearer ' prefix
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
            request.payload = payload  # Pass decoded payload in request
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)

    return decorated_function



#     def wrapper(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             token = request.headers.get('Authorization')
#             if not token:
#                 return jsonify({"message": "Token is missing"}), 403

#             try:      
#                 token = token.split(" ")[1]    
#                 payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
#                 user_role = payload.get("role")

#                 if user_role not in allowed_roles:
#                     return jsonify({"message": "Access Denied: Insufficient permissions"}), 403

#             except jwt.ExpiredSignatureError:
#                 return jsonify({"message": "Token has expired"}), 401
#             except jwt.InvalidTokenError:
#                 return jsonify({"message": "Invalid token"}), 401


        
#         return decorated_function
#     return wrapper

def role_required(allowed_roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({"error": "Authorization token is missing"}), 400

            if not token.startswith("Bearer "):
                return jsonify({"error": "Malformed token"}), 400

            try:
                token = token.split(" ")[1]
                # Use check_token to get the payload (and handle errors)
                payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
                # payload = request.payload  # The payload should be set by the check_token decorator
            # except AttributeError:
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401
                # return jsonify({"message": "Token is missing"}), 403
            # if isinstance(payload, tuple):  # Check if payload is an error response
                # return payload[0], payload[1]  # Return the error message and status code

            # Extract the user role from the payload and check if it's allowed
            user_role = payload.get("role")

            if user_role not in allowed_roles:
                return jsonify({"message": "Access Denied: Insufficient permissions"}), 403

            request.payload = payload
            return f(*args, **kwargs)
        
        return decorated_function
    return wrapper

