"""
Security Module for Passport Data Extractor
Comprehensive security layers for production deployment
"""

import os
import jwt
import hashlib
import hmac
import time
import secrets
import re
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Callable, Tuple
from flask import request, jsonify, current_app, g
import magic
from werkzeug.security import generate_password_hash, check_password_hash
# Add this at the top of src/security.py
from dotenv import load_dotenv
load_dotenv()  # Load .env file
print(f"DEBUG: Loaded .env file: {os.environ.get('SECRET_KEY')}")
logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration class"""
    
    def __init__(self, config: Dict):
        self.secret_key = config.get('secret_key', os.environ.get('SECRET_KEY', secrets.token_hex(32)))
        self.jwt_secret = config.get('jwt_secret', os.environ.get('JWT_SECRET', secrets.token_hex(32)))
        self.jwt_expiry_hours = config.get('jwt_expiry_hours', 24)
        
        # Rate limiting
        self.rate_limit_requests = config.get('rate_limit_requests', 100)  # requests per window
        self.rate_limit_window = config.get('rate_limit_window', 3600)    # 1 hour window
        
        # File validation
        self.max_file_size = config.get('max_file_size_mb', 10) * 1024 * 1024
        self.allowed_extensions = config.get('allowed_extensions', ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'])
        self.allowed_mime_types = config.get('allowed_mime_types', [
            'image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff'
        ])
        
        # API Keys
        self.require_api_key = config.get('require_api_key', True)
        self.api_keys = config.get('api_keys', {})
        
        # CORS
        self.allowed_origins = config.get('allowed_origins', ['*'])
        
        # IP Whitelist
        self.ip_whitelist = config.get('ip_whitelist', [])
        self.enable_ip_whitelist = config.get('enable_ip_whitelist', False)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, requests_per_window: int, window_seconds: int):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.requests = {}  # {ip: [(timestamp, count), ...]}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old entries
        if identifier in self.requests:
            self.requests[identifier] = [
                (ts, count) for ts, count in self.requests[identifier] 
                if ts > window_start
            ]
        
        # Count requests in current window
        current_count = sum(count for _, count in self.requests.get(identifier, []))
        
        if current_count >= self.requests_per_window:
            return False
        
        # Add current request
        if identifier not in self.requests:
            self.requests[identifier] = []
        self.requests[identifier].append((now, 1))
        
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        now = time.time()
        window_start = now - self.window_seconds
        
        if identifier not in self.requests:
            return self.requests_per_window
        
        current_count = sum(count for ts, count in self.requests[identifier] 
                          if ts > window_start)
        return max(0, self.requests_per_window - current_count)

class SecurityManager:
    """Main security manager"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.rate_limiter = RateLimiter(
            config.rate_limit_requests, 
            config.rate_limit_window
        )
        self.users = {}  # In production, use database
        self._load_users()
    
    def _load_users(self):
        """Load users from environment or config"""
        # DEBUG: Check environment variables
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        print(f"DEBUG: ADMIN_PASSWORD from env: {admin_password}")
        print(f"DEBUG: All env vars: {dict(os.environ)}")
        
        # In production, load from database
        self.users['admin'] = {
            'password_hash': generate_password_hash(admin_password),
            'role': 'admin',
            'permissions': ['read', 'write', 'admin']
        }
        print(f"DEBUG: Users loaded: {list(self.users.keys())}")
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        if check_password_hash(user['password_hash'], password):
            return user
        return None
    
    def create_token(self, username: str, user_data: Dict) -> str:
        """Create JWT token"""
        payload = {
            'username': username,
            'role': user_data['role'],
            'permissions': user_data['permissions'],
            'exp': datetime.utcnow() + timedelta(hours=self.config.jwt_expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.config.jwt_secret, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key"""
        if not self.config.require_api_key:
            return True
        
        return api_key in self.config.api_keys
    
    def validate_file(self, file) -> Tuple[bool, str]:
        """Validate uploaded file"""
        # Check file size
        if file.content_length and file.content_length > self.config.max_file_size:
            return False, f"File too large. Max size: {self.config.max_file_size // (1024*1024)}MB"
        
        # Check file extension
        if file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in self.config.allowed_extensions:
                return False, f"Invalid file extension. Allowed: {', '.join(self.config.allowed_extensions)}"
        
        # Check MIME type
        try:
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)  # Reset file pointer
            
            if mime_type not in self.config.allowed_mime_types:
                return False, f"Invalid file type. Allowed: {', '.join(self.config.allowed_mime_types)}"
        except Exception as e:
            logger.error(f"Error checking MIME type: {e}")
            return False, "Unable to verify file type"
        
        return True, "OK"
    
    def validate_base64_image(self, image_data: str) -> Tuple[bool, str]:
        """Validate base64 image data"""
        try:
            # Check if it's a data URL
            if image_data.startswith('data:image'):
                # Extract base64 part
                header, data = image_data.split(',', 1)
                mime_type = header.split(':')[1].split(';')[0]
                
                if mime_type not in self.config.allowed_mime_types:
                    return False, f"Invalid MIME type: {mime_type}"
                
                # Check data size (rough estimate)
                data_size = len(data) * 3 // 4  # Base64 to binary size
                if data_size > self.config.max_file_size:
                    return False, f"Image too large. Max size: {self.config.max_file_size // (1024*1024)}MB"
                
                # Validate base64
                import base64
                try:
                    base64.b64decode(data)
                except Exception:
                    return False, "Invalid base64 encoding"
            else:
                # Assume it's raw base64
                import base64
                try:
                    decoded = base64.b64decode(image_data)
                    if len(decoded) > self.config.max_file_size:
                        return False, f"Image too large. Max size: {self.config.max_file_size // (1024*1024)}MB"
                except Exception:
                    return False, "Invalid base64 encoding"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error validating base64 image: {e}")
            return False, "Invalid image data"
    
    def check_ip_whitelist(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        if not self.config.enable_ip_whitelist:
            return True
        
        return ip in self.config.ip_whitelist
    
    def sanitize_input(self, data: str) -> str:
        """Sanitize input data"""
        # Remove potentially dangerous characters
        data = re.sub(r'[<>"\']', '', data)
        return data.strip()
    
    def log_security_event(self, event_type: str, details: Dict):
        """Log security events"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'details': details
        }
        logger.info(f"SECURITY_EVENT: {log_entry}")

# Global security manager instance
security_manager = None

def init_security(config: Dict):
    """Initialize security manager"""
    global security_manager
    print(f"DEBUG: Initializing security with config: {config}")
    security_config = SecurityConfig(config)
    security_manager = SecurityManager(security_config)
    print(f"DEBUG: Security manager initialized: {security_manager is not None}")
    print(f"DEBUG: Security manager type: {type(security_manager)}")
    print(f"DEBUG: Security manager users: {list(security_manager.users.keys()) if security_manager else 'None'}")

def get_security_manager():
    """Get the global security manager instance"""
    global security_manager
    return security_manager

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not security_manager:
            return jsonify({'error': 'Security not initialized'}), 500
        
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        # Check if it's Bearer token
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            user_data = security_manager.verify_token(token)
            if not user_data:
                return jsonify({'error': 'Invalid or expired token'}), 401
            g.user = user_data
        else:
            return jsonify({'error': 'Invalid authorization format'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_role(role: str):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            if g.user.get('role') != role:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user_permissions = g.user.get('permissions', [])
            if permission not in user_permissions:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(f):
    """Decorator to apply rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not security_manager:
            return jsonify({'error': 'Security not initialized'}), 500
        
        # Use IP address as identifier
        identifier = request.remote_addr
        
        # Check rate limit
        if not security_manager.rate_limiter.is_allowed(identifier):
            remaining = security_manager.rate_limiter.get_remaining(identifier)
            return jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': security_manager.config.rate_limit_window
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function

def validate_file_upload(f):
    """Decorator to validate file uploads"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not security_manager:
            return jsonify({'error': 'Security not initialized'}), 500
        
        # Check for file in request
        if 'file' in request.files:
            file = request.files['file']
            is_valid, message = security_manager.validate_file(file)
            if not is_valid:
                security_manager.log_security_event('file_validation_failed', {
                    'filename': file.filename,
                    'error': message
                })
                return jsonify({'error': message}), 400
        
        return f(*args, **kwargs)
    return decorated_function

def validate_json_input(f):
    """Decorator to validate JSON input"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not security_manager:
            return jsonify({'error': 'Security not initialized'}), 500
        
        # Validate base64 images in JSON
        if request.is_json:
            data = request.get_json()
            if data and 'image' in data:
                is_valid, message = security_manager.validate_base64_image(data['image'])
                if not is_valid:
                    security_manager.log_security_event('base64_validation_failed', {
                        'error': message
                    })
                    return jsonify({'error': message}), 400
        
        return f(*args, **kwargs)
    return decorated_function

def check_ip_whitelist(f):
    """Decorator to check IP whitelist"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not security_manager:
            return jsonify({'error': 'Security not initialized'}), 500
        
        ip = request.remote_addr
        if not security_manager.check_ip_whitelist(ip):
            security_manager.log_security_event('ip_blocked', {
                'ip': ip,
                'endpoint': request.endpoint
            })
            return jsonify({'error': 'Access denied'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def require_api_key(f):
    """Decorator to require API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not security_manager:
            return jsonify({'error': 'Security not initialized'}), 500
        
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        if not security_manager.validate_api_key(api_key):
            security_manager.log_security_event('invalid_api_key', {
                'provided_key': api_key[:8] + '...' if api_key else 'None',
                'ip': request.remote_addr
            })
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function
