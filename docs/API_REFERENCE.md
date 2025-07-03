# Passport Data Extractor - API Reference

## Base URL
```
http://localhost:5000
```

## Endpoints

### 1. Health Check

Check if the server is running and healthy.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "passport-extractor-ultra",
  "version": "2.0",
  "uptime": "0:15:30.123456",
  "features": [
    "auto-enhancement",
    "multi-pass-extraction",
    "confidence-scoring",
    "diagnostic-tools"
  ]
}
```

**Status Codes:**
- `200 OK`: Server is healthy
- `503 Service Unavailable`: Server is not ready

---

### 2. Extract from Base64

Extract passport data from a base64-encoded image.

**Endpoint:** `POST /extract`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "passport_type": "PC",
    "country_code": "SDN",
    "passport_number": "P01469195",
    "full_name": "BAHGA ABDELRHMAN ALI ABASHAR",
    "nationality": "SUDANESE",
    "national_id": "101-0068-9869",
    "place_of_birth": "ALFASHER",
    "sex": "F",
    "date_of_birth": "04-10-1966",
    "date_of_issue": "20-11-2014",
    "date_of_expiry": "19-11-2019",
    "confidence_scores": {
      "passport_number": 0.95,
      "full_name": 0.85,
      "nationality": 0.95,
      "national_id": 0.9,
      "date_of_birth": 0.85,
      "date_of_issue": 0.8,
      "date_of_expiry": 0.85,
      "sex": 0.95,
      "place_of_birth": 0.85
    },
    "extraction_method": {
      "passport_number": "uniform_block_high_confidence",
      "full_name": "adaptive_single_column"
    },
    "extraction_score": 87.5,
    "extraction_summary": "7/10 fields extracted"
  },
  "accuracy": "87.5%",
  "result_file": "output/results/extraction_20231215_143022.json"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Failed to decode image"
}
```

**Status Codes:**
- `200 OK`: Successful extraction
- `400 Bad Request`: Invalid request (missing image)
- `500 Internal Server Error`: Processing error

**Example - Python:**
```python
import requests
import base64

# Read and encode image
with open('passport.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Send request
response = requests.post(
    'http://localhost:5000/extract',
    json={'image': f'data:image/jpeg;base64,{image_data}'},
    headers={'Content-Type': 'application/json'}
)

result = response.json()
print(result['data'])
```

**Example - cURL:**
```bash
# First encode image to base64
base64 passport.jpg > passport_base64.txt

# Send request
curl -X POST http://localhost:5000/extract \
  -H "Content-Type: application/json" \
  -d "{\"image\":\"data:image/jpeg;base64,$(cat passport_base64.txt)\"}"
```

---

### 3. Extract from File Upload

Extract passport data from an uploaded file.

**Endpoint:** `POST /extract-file`

**Headers:**
```
Content-Type: multipart/form-data
```

**Request:**
- Method: POST
- Body: Form data with file field
- Field name: `file`
- Supported formats: JPG, JPEG, PNG, BMP, TIFF

**Response:** Same as `/extract` endpoint

**Status Codes:**
- `200 OK`: Successful extraction
- `400 Bad Request`: No file uploaded or invalid file
- `413 Payload Too Large`: File exceeds size limit (10MB)
- `500 Internal Server Error`: Processing error

**Example - Python:**
```python
import requests

with open('passport.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:5000/extract-file',
        files=files
    )

result = response.json()
print(result['data'])
```

**Example - cURL:**
```bash
curl -X POST -F "file=@passport.jpg" http://localhost:5000/extract-file
```

**Example - JavaScript:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:5000/extract-file', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(result => {
    console.log(result.data);
});
```

---

### 4. Get Statistics

Get extraction statistics since server start.

**Endpoint:** `GET /stats`

**Response:**
```json
{
  "total_requests": 156,
  "successful_extractions": 142,
  "failed_extractions": 14,
  "average_accuracy": 86.3,
  "start_time": "2023-12-15T14:00:00.000000"
}
```

**Status Codes:**
- `200 OK`: Statistics returned

---

## Data Models

### Passport Data

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| passport_type | string | Type of passport | "PC" |
| country_code | string | ISO country code | "SDN" |
| passport_number | string | Passport number | "P01469195" |
| full_name | string | Full name in caps | "JOHN DOE SMITH" |
| nationality | string | Nationality | "SUDANESE" |
| national_id | string | National ID number | "101-0068-9869" |
| place_of_birth | string | Birth place | "KHARTOUM" |
| sex | string | Gender (M/F) | "M" |
| date_of_birth | string | Birth date | "15-03-1985" |
| date_of_issue | string | Issue date | "20-11-2020" |
| date_of_expiry | string | Expiry date | "19-11-2030" |

### Confidence Scores

Each extracted field has an associated confidence score (0-1):
- `0.9 - 1.0`: Very high confidence
- `0.7 - 0.9`: High confidence
- `0.5 - 0.7`: Medium confidence
- `< 0.5`: Low confidence

### Extraction Methods

Indicates which preprocessing and OCR method successfully extracted each field:
- Format: `{preprocessing}_{ocr_method}`
- Example: `"clahe_uniform_block"`

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Detailed error message"
}
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "No image provided" | Missing image in request | Include image data |
| "Failed to decode image" | Invalid base64 | Check encoding |
| "File too large" | > 10MB file | Reduce file size |
| "Unsupported format" | Not JPG/PNG | Convert image |
| "OCR timeout" | Processing took too long | Simplify image |

## Rate Limiting

Currently no rate limiting is implemented. For production use, consider:
- Adding request throttling
- Implementing API keys
- Setting concurrent request limits

## Best Practices

### 1. Image Preparation

Before sending to API:
- Ensure good image quality (300+ DPI)
- Crop to passport page only
- Avoid shadows and glare
- Keep file size reasonable (1-5MB)

### 2. Error Handling

```python
def extract_with_retry(image_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(...)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### 3. Batch Processing

For multiple passports:
```python
import concurrent.futures

def process_batch(image_paths):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(extract_passport, path) for path in image_paths]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    return results
```

### 4. Response Validation

Always validate the response:
```python
def validate_extraction(result):
    if not result.get('success'):
        raise Exception(f"Extraction failed: {result.get('error')}")
    
    data = result.get('data', {})
    required_fields = ['passport_number', 'full_name', 'date_of_expiry']
    
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        print(f"Warning: Missing fields: {missing}")
    
    return data
```

## Performance

- Average processing time: 2-3 seconds per passport
- Memory usage: ~200MB base + 50MB per concurrent request
- Recommended specs: 4GB RAM, 2+ CPU cores

## Security Considerations

1. **Do not expose to internet** without authentication
2. **Validate file uploads** (type, size, content)
3. **Sanitize extracted data** before storage
4. **Use HTTPS** in production
5. **Implement rate limiting** to prevent abuse

---

**Need more help?** See the [User Guide](USER_GUIDE.md) or [Troubleshooting](TROUBLESHOOTING.md) guide.