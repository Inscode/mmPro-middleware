import jwt
import datetime
from cryptography.fernet import Fernet
from config import Config


class JWTUtils:
    """Utility class for JWT operations with API key encryption."""

    # Generate a symmetric key for encryption (should be stored securely)
    key = Fernet.generate_key()
    cipher = Fernet(key)

    @staticmethod
    def create_jwt_token(user_id, user_role, api_key):
        encrypted_api_key = JWTUtils.cipher.encrypt(api_key.encode()).decode()
        expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)

        payload = {
            'user_id': user_id,
            'role': user_role,
            'api_key': encrypted_api_key,
            'exp': expiration_time
        }

        token = jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)
        return token

    @staticmethod
    def decrypt_api_key(encrypted_api_key):
        return JWTUtils.cipher.decrypt(encrypted_api_key.encode()).decode()
    

    @staticmethod
    def decode_jwt_and_decrypt_api_key(token):
        try:
            
            token = token.split(" ")[1] if " " in token else token
          
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM], options={"verify_exp": True})
      
            encrypted_api_key = payload.get('api_key')
            if encrypted_api_key:
              
                decrypted_api_key = JWTUtils.decrypt_api_key(encrypted_api_key)
                payload['api_key'] = decrypted_api_key  
                return payload  
            else:
                return {'message': 'API key is missing from the token'}

        except jwt.ExpiredSignatureError:
            return {'message': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'message': 'Invalid token'}
        except Exception as e:
            return {'message': f'Error decoding token: {str(e)}'}

    @staticmethod
    def get_api_key_from_token(token):
        try:
            # Handle tokens with 'Bearer ' prefix
            token = token.split(" ")[1] if " " in token else token
            
            # Decode the token without verifying expiration to avoid potential issues
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
            
            # Decrypt and return only the API key
            encrypted_api_key = payload.get('api_key')
            if encrypted_api_key:
                return JWTUtils.decrypt_api_key(encrypted_api_key)
            else:
                raise ValueError("API key is missing from the token")

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
        except Exception as e:
            raise ValueError(f"Error decoding token: {str(e)}")
