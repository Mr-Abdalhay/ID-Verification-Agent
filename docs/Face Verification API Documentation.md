# Face Verification API Documentation

## Overview

The Passport Data Extractor now includes advanced face verification capabilities using InsightFace. This document describes the new face-related endpoints.

## New Endpoints

### 1. Extract Face from Document

Extract face from a passport or ID document.

**Endpoint:** `POST /extract-face`

**Request:**
```json
{
    "image": "data:image/jpeg;base64,...",
    "document_type": "passport"  // or "id_card"
}
```

**Response:**
```json
{
    "success": true,
    "face_image": "base64_encoded_face_image",
    "metadata": {
        "bbox": [x, y, x2, y2],
        "det_score": 0.98,
        "landmark": [[x1,y1], [x2,y2], ...],
        "age": 35,
        "gender": 1
    },
    "face_file": "output/faces/extracted_face_20231215_143022.jpg"
}
```

### 2. Verify Two Faces

Compare two face images to determine if they belong to the same person.

**Endpoint:** `POST /verify-faces`

**Request:**
```json
{
    "face1": "data:image/jpeg;base64,...",
    "face2": "data:image/jpeg;base64,..."
}
```

**Response:**
```json
{
    "success": true,
    "verified": true,
    "confidence": 0.85,
    "method": "insightface",
    "liveness_score": 0.92,
    "error": null
}
```

### 3. Complete Passport Verification

Perform OCR extraction and face verification in a single request.

**Endpoint:** `POST /verify-passport`

**Request:**
```json
{
    "passport_image": "data:image/jpeg;base64,...",
    "selfie_image": "data:image/jpeg;base64,..."
}
```

**Response:**
```json
{
    "success": true,
    "passport_data": {
        "passport_number": "P01469195",
        "full_name": "JOHN DOE",
        "nationality": "SUDANESE",
        "date_of_birth": "04-10-1966",
        "date_of_expiry": "19-11-2029",
        "extraction_score": 87.5
    },
    "face_verification": {
        "verified": true,
        "confidence": 0.89,
        "liveness_score": 0.85,
        "liveness_passed": true
    },
    "overall_verification": {
        "status": "VERIFIED",
        "ocr_score": 87.5,
        "face_match": true,
        "liveness_check": true
    },
    "extracted_face": "base64_encoded_passport_face",
    "result_file": "output/results/complete_verification_20231215_143022.json"
}
```

### 4. Complete Verification with File Upload

Same as above but accepts files instead of base64 data.

**Endpoint:** `POST /verify-complete`

**Request:** `multipart/form-data` with fields:
- `passport`: Passport image file
- `selfie`: Selfie image file

**Response:** Same structure as `/verify-passport`

## Usage Examples

### Python Example - Complete Verification

```python
import requests
import base64

# Read images
with open('passport.jpg', 'rb') as f:
    passport_data = base64.b64encode(f.read()).decode('utf-8')

with open('selfie.jpg', 'rb') as f:
    selfie_data = base64.b64encode(f.read()).decode('utf-8')

# Send request
response = requests.post(
    'http://localhost:5000/verify-passport',
    json={
        'passport_image': f'data:image/jpeg;base64,{passport_data}',
        'selfie_image': f'data:image/jpeg;base64,{selfie_data}'
    }
)

result = response.json()

if result['success']:
    print(f"Passport Number: {result['passport_data']['passport_number']}")
    print(f"Name: {result['passport_data']['full_name']}")
    print(f"Face Match: {result['face_verification']['verified']}")
    print(f"Overall Status: {result['overall_verification']['status']}")
```

### cURL Example - Extract Face

```bash
# Extract face from passport
curl -X POST http://localhost:5000/extract-face \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,'$(base64 -w 0 passport.jpg)'",
    "document_type": "passport"
  }'
```

### JavaScript Example - Face Verification

```javascript
async function verifyFaces(face1File, face2File) {
    // Convert files to base64
    const toBase64 = file => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });

    const face1Base64 = await toBase64(face1File);
    const face2Base64 = await toBase64(face2File);

    // Send request
    const response = await fetch('http://localhost:5000/verify-faces', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            face1: face1Base64,
            face2: face2Base64
        })
    });

    const result = await response.json();
    
    if (result.success) {
        console.log(`Faces match: ${result.verified}`);
        console.log(`Confidence: ${result.confidence}`);
    }
}
```

## Configuration

Face verification settings can be configured in `config/default_config.json`:

```json
{
    "face_processing": {
        "verification": {
            "threshold": 0.4,  // Lower = stricter matching
            "model": "buffalo_l",  // InsightFace model
            "min_face_size": 30
        },
        "liveness": {
            "enabled": true,
            "min_score": 0.7  // Minimum liveness score required
        }
    }
}
```

## Error Handling

Common errors and their meanings:

| Error | Cause | Solution |
|-------|-------|----------|
| "No face detected in document" | Face not found in passport | Check image quality, ensure face is visible |
| "Could not extract face embeddings" | Face too small/blurry | Use higher resolution image |
| "Liveness check failed" | Possible spoofing detected | Use live selfie, not photo of photo |
| "Verification threshold not met" | Faces don't match | Ensure same person in both images |

## Performance

- Face extraction: ~0.5-1 second
- Face verification: ~0.5-1 second
- Complete verification (OCR + Face): ~3-4 seconds
- Liveness detection: ~0.2 seconds

## Security Considerations

1. **Always verify liveness** in production to prevent photo spoofing
2. **Set appropriate thresholds** based on your security requirements
3. **Store embeddings securely** if implementing a database
4. **Use HTTPS** in production
5. **Implement rate limiting** to prevent abuse

## Troubleshooting

### InsightFace Installation Issues

If you encounter issues installing InsightFace:

```bash
# Install dependencies first
pip install onnxruntime
pip install opencv-python
pip install numpy

# Then install InsightFace
pip install insightface

# For GPU support
pip install onnxruntime-gpu
```

### Model Download Issues

InsightFace models are downloaded automatically on first use. If download fails:

1. Check internet connection
2. Clear cache: `rm -rf ~/.insightface/models/`
3. Manually download from: https://github.com/deepinsight/insightface

### Performance Optimization

For better performance:

1. Use GPU if available (install onnxruntime-gpu)
2. Reduce image size before processing
3. Use batch processing for multiple faces
4. Cache face embeddings for known users