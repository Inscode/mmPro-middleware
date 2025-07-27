import jwt
import datetime
from cryptography.fernet import Fernet
from config import Config
from utils.user_utils import UserUtils


class JWTUtils:
    """Utility class for JWT operations with API key encryption."""

    # Generate a symmetric key for encryption (should be stored securely)
    key = Fernet.generate_key()
    cipher = Fernet(key)

    
    
    @staticmethod
    def create_jwt_token(user_id, user_role):
        access_token_exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=240)

        access_payload = {
            'user_id': user_id,
            'role': user_role,
            'exp': access_token_exp
        }
        access_token = jwt.encode(access_payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

        refresh_token_exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
        refresh_payload = {
            'user_id': user_id,
            'role': user_role,
            'exp': refresh_token_exp,
            'refresh': True
        }
        refresh_token = jwt.encode(refresh_payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }


    @staticmethod
    def create_access_token(user_id, user_role):
        """
        Generate a short-lived access token.
        """
        

        access_token_exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
        access_payload = {
            'user_id': user_id,
            'role': user_role,
            'exp': access_token_exp
        }

        return jwt.encode(access_payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)


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
    def decode_jwt_and_get_user_id(token):
        try:
            # Strip "Bearer " prefix if present
            token = token.split(" ")[1] if " " in token else token

            # Decode the JWT
            payload = jwt.decode(
                token,
                Config.SECRET_KEY,
                algorithms=[Config.JWT_ALGORITHM],
                options={"verify_exp": True}
            )

            # Extract user ID
            user_id = payload.get("user_id")
            if user_id is not None:
                return {'success': True, 'user_id': user_id}
            else:
                return {'success': False, 'message': 'User ID not found in token'}

        except jwt.ExpiredSignatureError:
            return {'success': False, 'message': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'success': False, 'message': 'Invalid token'}
        except Exception as e:
            return {'success': False, 'message': f'Error decoding token: {str(e)}'}

    # @staticmethod
    # def get_api_key_from_token(token):
    #     try:
    #         # Handle tokens with 'Bearer ' prefix
    #         token = token.split(" ")[1] if " " in token else token
            
    #         # Decode the token without verifying expiration to avoid potential issues
    #         payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
            
    #         # Decrypt and return only the API key
    #         encrypted_api_key = payload.get('api_key')
    #         if encrypted_api_key:
    #             return JWTUtils.decrypt_api_key(encrypted_api_key)
    #         else:
    #             raise ValueError("API key is missing from the token")

    #     except jwt.ExpiredSignatureError:
    #         raise ValueError("Token has expired")
    #     except jwt.InvalidTokenError:
    #         raise ValueError("Invalid token")
    #     except Exception as e:
    #         raise ValueError(f"Error decoding token: {str(e)}")

    @staticmethod
    def get_api_key_from_token(token):
        try:
            # Handle tokens with 'Bearer ' prefix
            token = token.split(" ")[1] if " " in token else token
            
            # Decode the token without verifying expiration to avoid expiration errors
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
            
            user_id = payload.get('user_id')
            if not user_id:
                raise ValueError("User ID is missing from the token")
            
            # 🔥 Now call your UserUtils function to get fresh API key
            api_key = UserUtils.get_user_api_key(user_id)
            
            if not api_key or api_key == "N/A":
                raise ValueError("API key not found for the user")
            
            return api_key

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
        except Exception as e:
            raise ValueError(f"Error decoding token: {str(e)}")
