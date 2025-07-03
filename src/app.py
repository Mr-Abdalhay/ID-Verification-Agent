"""
Passport Data Extractor - Ultra Enhanced Server with Face Verification
Main Flask application with integrated OCR and face verification endpoints
"""

from flask import Flask, request, jsonify, render_template_string
import base64
import logging
import os
import json
import cv2
import numpy as np
from datetime import datetime
from extractor import UltraPassportExtractor
from preprocessor import ImagePreprocessor
from face_processor import FaceProcessor, encode_image_to_base64, decode_base64_to_image

# Initialize Flask app
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'default_config.json')
with open(config_path, 'r') as f:
    CONFIG = json.load(f)

# Initialize components
preprocessor = ImagePreprocessor(CONFIG['preprocessing'])
extractor = UltraPassportExtractor(CONFIG['extraction'])
face_processor = FaceProcessor(CONFIG.get('face_processing'))

# Ensure output directories exist
output_dirs = ['output', 'output/enhanced', 'output/diagnostics', 'output/results', 'output/faces']
for dir_path in output_dirs:
    os.makedirs(dir_path, exist_ok=True)

# Home page HTML
HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Passport Data Extractor with Face Verification</title>
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
        h2 {
            color: #555;
            margin-top: 30px;
        }
        .status {
            background: #4CAF50;
            color: white;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            margin: 20px 0;
        }
        .endpoints {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .endpoint-group {
            margin-bottom: 30px;
        }
        code {
            background: #eee;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
        }
        .new-badge {
            background: #ff5722;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            margin-left: 5px;
        }
        .feature-list {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .feature-list ul {
            margin: 5px 0;
            padding-left: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛂 Passport Data Extractor</h1>
        <h3 style="text-align: center; color: #666;">with Face Verification 🤖</h3>
        <div class="status">✅ Server is running</div>
        
        <div class="feature-list">
            <strong>Features:</strong>
            <ul>
                <li>OCR Text Extraction (90%+ accuracy)</li>
                <li>Face Detection & Extraction</li>
                <li>Face Verification with InsightFace</li>
                <li>Liveness Detection (Anti-spoofing)</li>
                <li>Combined OCR + Face Verification</li>
            </ul>
        </div>
        
        <h2>API Endpoints:</h2>
        
        <div class="endpoint-group">
            <h3>📝 Text Extraction Only</h3>
            <div class="endpoints">
                <p><strong>Extract from file:</strong><br>
                <code>POST /extract-file</code></p>
                
                <p><strong>Extract from base64:</strong><br>
                <code>POST /extract</code></p>
            </div>
        </div>
        
        <div class="endpoint-group">
            <h3>👤 Face Verification Only</h3>
            <div class="endpoints">
                <p><strong>Extract face from document:</strong><span class="new-badge">NEW</span><br>
                <code>POST /extract-face</code></p>
                
                <p><strong>Verify two faces:</strong><span class="new-badge">NEW</span><br>
                <code>POST /verify-faces</code></p>
            </div>
        </div>
        
        <div class="endpoint-group">
            <h3>🔗 Combined OCR + Face Verification</h3>
            <div class="endpoints">
                <p><strong>Complete passport verification:</strong><span class="new-badge">NEW</span><br>
                <code>POST /verify-passport</code><br>
                <em>Extract text + verify face in one request</em></p>
                
                <p><strong>Verify with separate images:</strong><span class="new-badge">NEW</span><br>
                <code>POST /verify-complete</code><br>
                <em>Passport + selfie verification</em></p>
            </div>
        </div>
        
        <div class="endpoint-group">
            <h3>📊 Utilities</h3>
            <div class="endpoints">
                <p><strong>Health check:</strong><br>
                <code>GET /health</code></p>
                
                <p><strong>Statistics:</strong><br>
                <code>GET /stats</code></p>
            </div>
        </div>
        
        <h2>Quick Test:</h2>
        <p>Run in terminal: <code>python tests/test_extraction.py</code></p>
        <p>Test face verification: <code>python tests/test_face_verification.py</code></p>
        
        <div style="text-align: center; margin-top: 30px; color: #666;">
            Version 3.0 | OCR Accuracy: 90%+ | Face Verification: InsightFace
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
    'average_accuracy': 0,
    'start_time': datetime.now().isoformat()
}

@app.route('/')
def home():
    """Home page"""
    return render_template_string(HOME_PAGE)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'passport-extractor-ultra',
        'version': '3.0',
        'uptime': str(datetime.now() - datetime.fromisoformat(stats['start_time'])),
        'features': [
            'auto-enhancement',
            'multi-pass-extraction',
            'confidence-scoring',
            'diagnostic-tools',
            'face-verification',
            'liveness-detection'
        ]
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get extraction statistics"""
    return jsonify(stats)

# Original OCR endpoints
@app.route('/extract', methods=['POST'])
def extract():
    """Extract passport data from base64 image"""
    global stats
    stats['total_requests'] += 1
    
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
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
        
        # Save result
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_path = f"output/results/extraction_{timestamp}.json"
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Clean response
        response_data = {k: v for k, v in result.items() if v is not None}
        
        return jsonify({
            'success': True,
            'data': response_data,
            'accuracy': f"{result.get('extraction_score', 0):.1f}%",
            'result_file': result_path
        })
        
    except Exception as e:
        stats['failed_extractions'] += 1
        logger.error(f"Extraction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/extract-file', methods=['POST'])
def extract_file():
    """Extract passport data from uploaded file"""
    global stats
    stats['total_requests'] += 1
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file
        image_bytes = file.read()
        
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
        
        # Save result
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_path = f"output/results/extraction_{timestamp}.json"
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Clean response
        response_data = {k: v for k, v in result.items() if v is not None}
        
        return jsonify({
            'success': True,
            'data': response_data,
            'accuracy': f"{result.get('extraction_score', 0):.1f}%",
            'filename': file.filename,
            'result_file': result_path
        })
        
    except Exception as e:
        stats['failed_extractions'] += 1
        logger.error(f"File extraction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# New face verification endpoints
@app.route('/extract-face', methods=['POST'])
def extract_face():
    """Extract face from passport/ID document"""
    global stats
    stats['total_requests'] += 1
    
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        document_type = data.get('document_type', 'passport')
        
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
        face_path = f"output/faces/extracted_face_{timestamp}.jpg"
        cv2.imwrite(face_path, face_img)
        
        return jsonify({
            'success': True,
            'face_image': encode_image_to_base64(face_img),
            'metadata': metadata,
            'face_file': face_path
        })
        
    except Exception as e:
        logger.error(f"Face extraction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/verify-faces', methods=['POST'])
def verify_faces():
    """Verify two face images"""
    global stats
    stats['total_requests'] += 1
    stats['face_verifications'] += 1
    
    try:
        data = request.get_json()
        
        # Check required fields
        if not data or 'face1' not in data or 'face2' not in data:
            return jsonify({'error': 'Two face images required'}), 400
        
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
        logger.error(f"Face verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/verify-passport', methods=['POST'])
def verify_passport():
    """Complete passport verification: OCR + Face extraction + verification"""
    global stats
    stats['total_requests'] += 1
    
    try:
        data = request.get_json()
        
        # Check required fields
        if not data or 'passport_image' not in data or 'selfie_image' not in data:
            return jsonify({'error': 'Passport and selfie images required'}), 400
        
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
        
        # Save complete result
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_path = f"output/results/complete_verification_{timestamp}.json"
        
        complete_result = {
            'timestamp': timestamp,
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
        logger.error(f"Complete verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/verify-complete', methods=['POST'])
def verify_complete():
    """Complete verification with separate passport and selfie files"""
    global stats
    stats['total_requests'] += 1
    
    try:
        # Check if files are uploaded
        if 'passport' not in request.files or 'selfie' not in request.files:
            return jsonify({'error': 'Both passport and selfie files required'}), 400
        
        passport_file = request.files['passport']
        selfie_file = request.files['selfie']
        
        if passport_file.filename == '' or selfie_file.filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        # Read files
        passport_bytes = passport_file.read()
        selfie_bytes = selfie_file.read()
        
        # Process passport OCR
        preprocessed_images = preprocessor.process(passport_bytes)
        ocr_result = extractor.extract(preprocessed_images)
        
        # Process face verification
        passport_img = cv2.imdecode(np.frombuffer(passport_bytes, np.uint8), cv2.IMREAD_COLOR)
        selfie_img = cv2.imdecode(np.frombuffer(selfie_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        # Extract face from passport
        face_img, face_metadata = face_processor.extract_face_from_document(passport_img, 'passport')
        
        if face_img is None:
            return jsonify({
                'success': False,
                'error': 'No face detected in passport',
                'ocr_data': ocr_result
            }), 400
        
        # Verify faces
        verification_result = face_processor.verify_faces(face_img, selfie_img, face_metadata)
        
        # Check liveness
        liveness_score = face_processor.check_liveness(selfie_img)
        
        # Update statistics
        if ocr_result['extraction_score'] > 0:
            stats['successful_extractions'] += 1
        if verification_result.verified:
            stats['successful_verifications'] += 1
        stats['face_verifications'] += 1
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_path = f"output/results/complete_verification_{timestamp}.json"
        
        complete_result = {
            'timestamp': timestamp,
            'passport_file': passport_file.filename,
            'selfie_file': selfie_file.filename,
            'ocr_results': ocr_result,
            'face_verification': {
                'verified': verification_result.verified,
                'confidence': float(verification_result.confidence),
                'method': verification_result.verification_method,
                'liveness_score': float(liveness_score)
            }
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
                'status': 'VERIFIED' if (verification_result.verified and ocr_result['extraction_score'] > 70) else 'FAILED',
                'ocr_score': float(ocr_result['extraction_score']),
                'face_match': bool(verification_result.verified),
                'liveness_check': bool(liveness_score >= face_processor.config['liveness']['min_score'])
            },
            'extracted_face': encode_image_to_base64(face_img),
            'result_file': result_path
        })
        
    except Exception as e:
        logger.error(f"Complete verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🛂 Passport Data Extractor - Ultra Enhanced Server with Face Verification")
    print("=" * 70)
    print("Version: 3.0")
    print("OCR Accuracy Target: 90%+")
    print("Face Verification: InsightFace")
    print("Server URL: http://localhost:5000")
    print("=" * 70)
    print("\nEndpoints:")
    print("  - GET  /                    : Web interface")
    print("  - GET  /health              : Health check")
    print("  - GET  /stats               : Statistics")
    print("\n  OCR Endpoints:")
    print("  - POST /extract             : Extract from base64")
    print("  - POST /extract-file        : Extract from file upload")
    print("\n  Face Verification Endpoints:")
    print("  - POST /extract-face        : Extract face from document")
    print("  - POST /verify-faces        : Verify two faces")
    print("\n  Combined Endpoints:")
    print("  - POST /verify-passport     : Complete passport verification (JSON)")
    print("  - POST /verify-complete     : Complete verification (file upload)")
    print("\nPress Ctrl+C to stop the server")
    
    # Configure Flask for better performance
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)