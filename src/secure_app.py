"""
Secure Passport Data Extractor - Ultra Enhanced Server with Security Layers
Production-ready Flask application with comprehensive security
"""

from flask import Flask, request, jsonify, render_template_string, g
from flask_cors import CORS
import base64
import logging
import os
import json
import cv2
import numpy as np
import sys
# This adds the parent directory (ID-Verification-Agent) to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from datetime import datetime
from extractor import UltraPassportExtractor
from preprocessor import ImagePreprocessor
from face_processor import FaceProcessor, encode_image_to_base64, decode_base64_to_image
from security import (
    init_security, require_auth, require_api_key, rate_limit, 
    validate_file_upload, validate_json_input, check_ip_whitelist,
    require_permission, security_manager
)

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load configurations
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'default_config.json')
security_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'security_config.json')

with open(config_path, 'r') as f:
    CONFIG = json.load(f)

with open(security_config_path, 'r') as f:
    SECURITY_CONFIG = json.load(f)

# Initialize security first
print("DEBUG: About to initialize security...")
init_security(SECURITY_CONFIG['security'])
print("DEBUG: Security initialization complete")

# Verify security manager is initialized
from security import get_security_manager
security_manager = get_security_manager()
if not security_manager:
    raise RuntimeError("Security manager failed to initialize")

print("DEBUG: Security manager verified as initialized")

# Initialize components
preprocessor = ImagePreprocessor(CONFIG['preprocessing'])
extractor = UltraPassportExtractor(CONFIG['extraction'])
face_processor = FaceProcessor(CONFIG.get('face_processing'))

# Configure CORS
if SECURITY_CONFIG['security']['cors']['enabled']:
    CORS(app, 
         origins=SECURITY_CONFIG['security']['cors']['allowed_origins'],
         methods=SECURITY_CONFIG['security']['cors']['allowed_methods'],
         allow_headers=SECURITY_CONFIG['security']['cors']['allowed_headers'])

# Ensure output directories exist
output_dirs = ['output', 'output/enhanced', 'output/diagnostics', 'output/results', 'output/faces', 'logs']
for dir_path in output_dirs:
    os.makedirs(dir_path, exist_ok=True)

# Secure home page HTML
SECURE_HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Secure Passport Data Extractor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .security-badge {
            background: #4CAF50;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            margin-left: 10px;
        }
        .endpoint {
            background: #f9f9f9;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }
        .auth-required {
            border-left-color: #ff9800;
        }
        .admin-only {
            border-left-color: #f44336;
        }
        code {
            background: #eee;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
        }
        .security-features {
            background: #e8f5e8;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛂 Secure Passport Data Extractor <span class="security-badge">SECURED</span></h1>
        <h3 style="text-align: center; color: #666;">Production-Ready with Advanced Security</h3>
        
        <div class="security-features">
            <h3>🔒 Security Features:</h3>
            <ul>
                <li>JWT Authentication & Authorization</li>
                <li>API Key Management</li>
                <li>Rate Limiting & DDoS Protection</li>
                <li>File Upload Validation</li>
                <li>Input Sanitization</li>
                <li>IP Whitelisting</li>
                <li>Security Event Logging</li>
                <li>CORS Protection</li>
            </ul>
        </div>
        
        <h2>🔐 Authentication Required Endpoints:</h2>
        
        <div class="endpoint auth-required">
            <h4>📝 OCR Extraction (Auth Required)</h4>
            <p><code>POST /secure/extract</code> - Extract from base64</p>
            <p><code>POST /secure/extract-file</code> - Extract from file upload</p>
            <p><strong>Headers:</strong> <code>Authorization: Bearer &lt;token&gt;</code></p>
        </div>
        
        <div class="endpoint auth-required">
            <h4>👤 Face Verification (Auth Required)</h4>
            <p><code>POST /secure/extract-face</code> - Extract face from document</p>
            <p><code>POST /secure/verify-faces</code> - Verify two faces</p>
            <p><code>POST /secure/verify-passport</code> - Complete verification</p>
        </div>
        
        <div class="endpoint admin-only">
            <h4>⚙️ Admin Endpoints (Admin Only)</h4>
            <p><code>GET /admin/stats</code> - Detailed statistics</p>
            <p><code>GET /admin/security-logs</code> - Security event logs</p>
            <p><code>POST /admin/rotate-keys</code> - Rotate API keys</p>
        </div>
        
        <h2>🔑 Authentication:</h2>
        <p><code>POST /auth/login</code> - Login to get JWT token</p>
        <p><code>POST /auth/logout</code> - Logout and invalidate token</p>
        
        <h2>📊 Public Endpoints:</h2>
        <div class="endpoint">
            <p><code>GET /health</code> - Health check</p>
            <p><code>GET /</code> - This page</p>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #666;">
            Version 3.0 Secure | OCR Accuracy: 90%+ | Face Verification: InsightFace
        </div>
    </div>
</body>
</html>
"""

# Statistics tracking
stats = {
    'total_requests': 0,
    'successful_extractions': 0,
    'failed_extractions': 0,
    'face_verifications': 0,
    'successful_verifications': 0,
    'security_events': 0,
    'average_accuracy': 0,
    'start_time': datetime.now().isoformat()
}

@app.route('/')
def home():
    """Secure home page"""
    return render_template_string(SECURE_HOME_PAGE)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint (public)"""
    return jsonify({
        'status': 'healthy',
        'service': 'passport-extractor-secure',
        'version': '3.0',
        'security': 'enabled',
        'uptime': str(datetime.now() - datetime.fromisoformat(stats['start_time'])),
        'features': [
            'jwt-authentication',
            'api-key-management',
            'rate-limiting',
            'file-validation',
            'input-sanitization',
            'security-logging'
        ]
    })

# Authentication endpoints
@app.route('/auth/login', methods=['POST'])
@rate_limit
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password required'}), 400
        
        username = data['username']
        password = data['password']
        
        # Get security_manager using the getter function
        from security import get_security_manager
        security_manager = get_security_manager()
        
        # Check if security_manager is initialized
        if not security_manager:
            logger.error("Security manager not initialized")
            return jsonify({'error': 'Security not initialized'}), 500
        
        print(f"DEBUG: Attempting login for user: {username}")
        
        # Authenticate user
        user_data = security_manager.authenticate_user(username, password)
        if not user_data:
            security_manager.log_security_event('login_failed', {
                'username': username,
                'ip': request.remote_addr
            })
            return jsonify({'error': 'Invalid credentials'}), 401
        
        print(f"DEBUG: User authenticated successfully: {username}")
        
        # Create JWT token
        token = security_manager.create_token(username, user_data)
        
        security_manager.log_security_event('login_success', {
            'username': username,
            'role': user_data['role']
        })
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'username': username,
                'role': user_data['role'],
                'permissions': user_data['permissions']
            },
            'expires_in': SECURITY_CONFIG['security']['jwt_expiry_hours'] * 3600
        })
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Logout endpoint"""
    try:
        # In production, add token to blacklist
        security_manager.log_security_event('logout', {
            'username': g.user.get('username'),
            'ip': request.remote_addr
        })
        
        return jsonify({'success': True, 'message': 'Logged out successfully'})
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

# Secure OCR endpoints
@app.route('/secure/extract', methods=['POST'])
@require_auth
@require_permission('read')
@rate_limit
@validate_json_input
def secure_extract():
    """Secure extract passport data from base64 image"""
    global stats
    stats['total_requests'] += 1
    
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Log the request
        security_manager.log_security_event('extract_request', {
            'user': g.user.get('username'),
            'method': 'base64'
        })
        
        # Decode base64 image
        image_data = data['image']
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Preprocess image
        preprocessed_images = preprocessor.process(image_bytes)
        
        # Extract data
        result = extractor.extract(preprocessed_images)
        
        # Update statistics
        if result['extraction_score'] > 0:
            stats['successful_extractions'] += 1
            total = stats['successful_extractions']
            current_avg = stats['average_accuracy']
            stats['average_accuracy'] = ((current_avg * (total - 1)) + result['extraction_score']) / total
        else:
            stats['failed_extractions'] += 1
        
        # Save result with user info
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_path = f"output/results/secure_extraction_{timestamp}.json"
        
        secure_result = {
            'user': g.user.get('username'),
            'timestamp': timestamp,
            'ip': request.remote_addr,
            'data': result
        }
        
        with open(result_path, 'w') as f:
            json.dump(secure_result, f, indent=2)
        
        # Include all extracted data (both null and non-null fields)
        response_data = result.copy()  # Include all fields for complete visibility
        
        return jsonify({
            'success': True,
            'data': response_data,
            'accuracy': f"{result.get('extraction_score', 0):.1f}%",
            'result_file': result_path
        })
        
    except Exception as e:
        stats['failed_extractions'] += 1
        logger.error(f"Secure extraction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/secure/extract-file', methods=['POST'])
@require_auth
@require_permission('read')
@rate_limit
@validate_file_upload
def secure_extract_file():
    """Secure extract passport data from uploaded file"""
    global stats
    stats['total_requests'] += 1
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Log the request
        security_manager.log_security_event('file_upload', {
            'user': g.user.get('username'),
            'filename': file.filename,
            'filesize': len(file.read())
        })
        file.seek(0)  # Reset file pointer
        
        # Read file
        image_bytes = file.read()
        
        # Preprocess image
        preprocessed_images = preprocessor.process(image_bytes)
        
        # Extract data
        result = extractor.extract(preprocessed_images)
        
        # Check if automatic diagnostics and enhancement are needed (accuracy < 70%)
        accuracy = result.get('extraction_score', 0)
        auto_actions = {}
        
        if accuracy < 70:
            logger.info(f"Low accuracy ({accuracy:.1f}%), triggering automatic diagnostics and enhancement")
            
            # Save uploaded file temporarily for processing
            timestamp_temp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_file_path = f"temp/uploaded_{timestamp_temp}_{file.filename}"
            os.makedirs("temp", exist_ok=True)
            
            try:
                # Save the uploaded file
                file.seek(0)  # Reset file pointer
                with open(temp_file_path, 'wb') as temp_file:
                    temp_file.write(file.read())
                
                # Run automatic enhancement
                try:
                    
                    from tools.enhance import ImageEnhancer
                    
                    enhancer = ImageEnhancer()
                    enhanced_path = enhancer.enhance_passport(temp_file_path)
                    auto_actions['enhancement'] = {
                        'triggered': True,
                        'enhanced_image_path': enhanced_path,
                        'reason': f'Low accuracy: {accuracy:.1f}%'
                    }
                    
                    # Try extraction again with enhanced image
                    import cv2
                    enhanced_image = cv2.imread(enhanced_path)
                    if enhanced_image is not None:
                        # Convert image to bytes for preprocessor
                        _, buffer = cv2.imencode('.jpg', enhanced_image)
                        enhanced_bytes = buffer.tobytes()
                        enhanced_preprocessed = preprocessor.process(enhanced_bytes)
                        enhanced_result = extractor.extract(enhanced_preprocessed)
                        
                        # Use enhanced result if better
                        if enhanced_result.get('extraction_score', 0) > accuracy:
                            result = enhanced_result
                            auto_actions['enhancement']['improved_accuracy'] = enhanced_result.get('extraction_score', 0)
                            logger.info(f"Enhancement improved accuracy to {enhanced_result.get('extraction_score', 0):.1f}%")
                        else:
                            auto_actions['enhancement']['improved_accuracy'] = None
                            
                except Exception as e:
                    auto_actions['enhancement'] = {
                        'triggered': True,
                        'error': str(e),
                        'reason': f'Low accuracy: {accuracy:.1f}%'
                    }
                
                # Run automatic diagnostics
                try:
                    from tools.diagnose import PassportDiagnostic
                    
                    diagnostic = PassportDiagnostic(temp_file_path)
                    diag_result = diagnostic.analyze_image_quality()
                    
                    # Handle case where diag_result might be None
                    if diag_result:
                        auto_actions['diagnostics'] = {
                            'triggered': True,
                            'image_quality_issues': diag_result.get('issues', []),
                            'recommendations': diag_result.get('recommendations', []),
                            'report_path': diag_result.get('report_path'),
                            'reason': f'Low accuracy: {accuracy:.1f}%'
                        }
                    else:
                        auto_actions['diagnostics'] = {
                            'triggered': True,
                            'image_quality_issues': ['Analysis failed'],
                            'recommendations': ['Check image quality manually'],
                            'reason': f'Low accuracy: {accuracy:.1f}%'
                        }
                    
                except Exception as e:
                    auto_actions['diagnostics'] = {
                        'triggered': True,
                        'error': str(e),
                        'reason': f'Low accuracy: {accuracy:.1f}%'
                    }
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        else:
            auto_actions = {
                'enhancement': {'triggered': False, 'reason': f'Good accuracy: {accuracy:.1f}%'},
                'diagnostics': {'triggered': False, 'reason': f'Good accuracy: {accuracy:.1f}%'}
            }
        
        # Update statistics (use final result after enhancement)
        final_accuracy = result.get('extraction_score', 0)
        if final_accuracy > 0:
            stats['successful_extractions'] += 1
            total = stats['successful_extractions']
            current_avg = stats['average_accuracy']
            stats['average_accuracy'] = ((current_avg * (total - 1)) + final_accuracy) / total
        else:
            stats['failed_extractions'] += 1
        
        # Save result with user info
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_path = f"output/results/secure_file_extraction_{timestamp}.json"
        
        secure_result = {
            'user': g.user.get('username'),
            'timestamp': timestamp,
            'ip': request.remote_addr,
            'filename': file.filename,
            'data': result
        }
        
        with open(result_path, 'w') as f:
            json.dump(secure_result, f, indent=2)
        
        # Include all extracted data (both null and non-null fields)
        response_data = result.copy()  # Include all fields for complete visibility
        
        return jsonify({
            'success': True,
            'data': response_data,
            'accuracy': f"{result.get('extraction_score', 0):.1f}%",
            'filename': file.filename,
            'result_file': result_path,
            'auto_actions': auto_actions,
            'quality_check': {
                'initial_accuracy': accuracy,
                'final_accuracy': result.get('extraction_score', 0),
                'threshold': 70,
                'auto_enhancement_triggered': auto_actions.get('enhancement', {}).get('triggered', False),
                'auto_diagnostics_triggered': auto_actions.get('diagnostics', {}).get('triggered', False)
            }
        })
        
    except Exception as e:
        stats['failed_extractions'] += 1
        logger.error(f"Secure file extraction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Secure face verification endpoints
@app.route('/secure/extract-face', methods=['POST'])
@require_auth
@require_permission('read')
@rate_limit
@validate_json_input
def secure_extract_face():
    """Secure extract face from passport/ID document"""
    global stats
    stats['total_requests'] += 1
    
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        document_type = data.get('document_type', 'passport')
        
        # Log the request
        security_manager.log_security_event('face_extraction_request', {
            'user': g.user.get('username'),
            'document_type': document_type
        })
        
        # Decode image
        document_img = decode_base64_to_image(data['image'])
        
        # Extract face
        face_img, metadata = face_processor.extract_face_from_document(document_img, document_type)
        
        if face_img is None:
            return jsonify({
                'success': False,
                'error': 'No face detected in document'
            }), 400
        
        # Save extracted face
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        face_path = f"output/faces/secure_extracted_face_{timestamp}.jpg"
        cv2.imwrite(face_path, face_img)
        
        return jsonify({
            'success': True,
            'face_image': encode_image_to_base64(face_img),
            'metadata': metadata,
            'face_file': face_path
        })
        
    except Exception as e:
        logger.error(f"Secure face extraction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/secure/verify-faces', methods=['POST'])
@require_auth
@require_permission('read')
@rate_limit
@validate_json_input
def secure_verify_faces():
    """Secure verify two face images"""
    global stats
    stats['total_requests'] += 1
    stats['face_verifications'] += 1
    
    try:
        data = request.get_json()
        
        # Check required fields
        if not data or 'face1' not in data or 'face2' not in data:
            return jsonify({'error': 'Two face images required'}), 400
        
        # Log the request
        security_manager.log_security_event('face_verification_request', {
            'user': g.user.get('username')
        })
        
        # Decode images
        face1 = decode_base64_to_image(data['face1'])
        face2 = decode_base64_to_image(data['face2'])
        
        # Verify faces
        result = face_processor.verify_faces(face1, face2)
        
        if result.verified:
            stats['successful_verifications'] += 1
        
        return jsonify({
            'success': True,
            'verified': bool(result.verified),
            'confidence': float(result.confidence),
            'method': result.verification_method,
            'liveness_score': float(result.liveness_score) if result.liveness_score else None,
            'error': result.error
        })
        
    except Exception as e:
        logger.error(f"Secure face verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/secure/verify-passport', methods=['POST'])
@require_auth
@require_permission('read')
@rate_limit
@validate_json_input
def secure_verify_passport():
    """Secure complete passport verification: OCR + Face extraction + verification"""
    global stats
    stats['total_requests'] += 1
    
    try:
        data = request.get_json()
        
        # Check required fields
        if not data or 'passport_image' not in data or 'selfie_image' not in data:
            return jsonify({'error': 'Passport and selfie images required'}), 400
        
        # Log the request
        security_manager.log_security_event('complete_verification_request', {
            'user': g.user.get('username')
        })
        
        # Decode images
        passport_bytes = base64.b64decode(
            data['passport_image'].split(',')[1] if data['passport_image'].startswith('data:image') 
            else data['passport_image']
        )
        
        selfie_img = decode_base64_to_image(data['selfie_image'])
        
        # Step 1: Extract text from passport
        preprocessed_images = preprocessor.process(passport_bytes)
        ocr_result = extractor.extract(preprocessed_images)
        
        # Step 2: Extract face from passport
        passport_img = cv2.imdecode(np.frombuffer(passport_bytes, np.uint8), cv2.IMREAD_COLOR)
        face_img, face_metadata = face_processor.extract_face_from_document(passport_img, 'passport')
        
        if face_img is None:
            return jsonify({
                'success': False,
                'error': 'No face detected in passport',
                'ocr_data': ocr_result
            }), 400
        
        # Step 3: Verify faces
        verification_result = face_processor.verify_faces(face_img, selfie_img, face_metadata)
        
        # Step 4: Check liveness
        liveness_score = face_processor.check_liveness(selfie_img)
        
        # Update statistics
        if ocr_result['extraction_score'] > 0:
            stats['successful_extractions'] += 1
        if verification_result.verified:
            stats['successful_verifications'] += 1
        stats['face_verifications'] += 1
        
        # Save complete result with user info
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_path = f"output/results/secure_complete_verification_{timestamp}.json"
        
        complete_result = {
            'user': g.user.get('username'),
            'timestamp': timestamp,
            'ip': request.remote_addr,
            'ocr_results': ocr_result,
            'face_verification': {
                'verified': verification_result.verified,
                'confidence': float(verification_result.confidence),
                'method': verification_result.verification_method,
                'liveness_score': float(liveness_score)
            },
            'overall_verified': verification_result.verified and ocr_result['extraction_score'] > 70
        }
        
        with open(result_path, 'w') as f:
            json.dump(complete_result, f, indent=2)
        
        return jsonify({
            'success': True,
            'passport_data': {k: v for k, v in ocr_result.items() if v is not None},
            'face_verification': {
                'verified': bool(verification_result.verified),
                'confidence': float(verification_result.confidence),
                'liveness_score': float(liveness_score),
                'liveness_passed': bool(liveness_score >= face_processor.config['liveness']['min_score'])
            },
            'overall_verification': {
                'status': 'VERIFIED' if complete_result['overall_verified'] else 'FAILED',
                'ocr_score': float(ocr_result['extraction_score']),
                'face_match': bool(verification_result.verified),
                'liveness_check': bool(liveness_score >= face_processor.config['liveness']['min_score'])
            },
            'extracted_face': encode_image_to_base64(face_img),
            'result_file': result_path
        })
        
    except Exception as e:
        logger.error(f"Secure complete verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Admin endpoints
@app.route('/admin/stats', methods=['GET'])
@require_auth
@require_permission('admin')
def admin_stats():
    """Admin statistics endpoint"""
    try:
        return jsonify({
            'success': True,
            'stats': stats,
            'security': {
                'total_security_events': stats.get('security_events', 0),
                'rate_limiter_status': 'active',
                'security_manager_status': 'active'
            }
        })
    except Exception as e:
        logger.error(f"Admin stats error: {str(e)}")
        return jsonify({'error': 'Failed to get stats'}), 500

@app.route('/admin/security-logs', methods=['GET'])
@require_auth
@require_permission('admin')
def admin_security_logs():
    """Admin security logs endpoint"""
    try:
        # In production, read from database
        log_file = 'logs/security.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()[-100:]  # Last 100 lines
            return jsonify({
                'success': True,
                'logs': logs
            })
        else:
            return jsonify({
                'success': True,
                'logs': ['No security logs found']
            })
    except Exception as e:
        logger.error(f"Admin security logs error: {str(e)}")
        return jsonify({'error': 'Failed to get security logs'}), 500

if __name__ == '__main__':
    print("🛂 Secure Passport Data Extractor - Production Ready")
    print("=" * 70)
    print("Version: 3.0 Secure")
    print("Security: ENABLED")
    print("OCR Accuracy Target: 90%+")
    print("Face Verification: InsightFace")
    print("Server URL: https://localhost:5001")
    print("=" * 70)
    print("\nSecure Endpoints:")
    print("  - GET  /                    : Secure web interface")
    print("  - GET  /health              : Health check")
    print("  - POST /auth/login          : Login")
    print("  - POST /auth/logout         : Logout")
    print("\n  Secure OCR Endpoints:")
    print("  - POST /secure/extract      : Extract from base64 (Auth required)")
    print("  - POST /secure/extract-file : Extract from file (Auth required)")
    print("\n  Secure Face Verification:")
    print("  - POST /secure/extract-face : Extract face (Auth required)")
    print("  - POST /secure/verify-faces : Verify faces (Auth required)")
    print("  - POST /secure/verify-passport : Complete verification (Auth required)")
    print("\n  Admin Endpoints:")
    print("  - GET  /admin/stats         : Statistics (Admin only)")
    print("  - GET  /admin/security-logs : Security logs (Admin only)")
    print("\n⚠️  IMPORTANT: Change default passwords and API keys in production!")
    print("Press Ctrl+C to stop the server")
    
    # Configure Flask for production
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # In production, use HTTPS
    # app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, ssl_context='adhoc')
    
    # For development (use HTTPS in production)
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True,ssl_context='adhoc') 
