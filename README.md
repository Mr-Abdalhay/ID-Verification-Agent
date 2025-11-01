# ID Verification Agent - User Guide

## What Does This System Do?

This system extracts information from identity documents automatically:
- **Passports** - Extract name, passport number, dates, nationality, etc.
- **ID Cards** - Extract national ID, name, address, blood type, etc.
- **Driving Licenses** - Extract license type, name, dates, etc.
- **Face Verification** - Compare faces between documents and selfies

## How to Use the API

### Step 1: Login First

**What it does:** Gets you access to use the system

**How to do it:**
1. Use this URL: `https://5.22.215.77:5001/auth/login`
2. Send your username and password
3. You'll get a **token** - save this token, you need it for every request

**Example:**
```json
{
  "username": "admin",
  "password": "X7uFB9k@cxSnuBXhlVIo"
}
```

**You'll receive:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### Step 2: Use the Token

For every request after login, you need to include:
- **Authorization:** `Bearer YOUR_TOKEN_HERE`
- **X-API-Key:** `your-admin-api-key`

---

## Available Services

### 1. Extract Passport Data

**What it does:** Reads all information from a passport image

**Endpoint:** `POST https://5.22.215.77:5001/secure/extract-file`

**How to send:**
- Upload the passport image file
- Make sure the image is clear and readable

**What you get back:**
```json
{
  "success": true,
  "data": {
    "passport_number": "A12345678",
    "first_name": "AHMED",
    "second_name": "MOHAMED",
    "last_name": "ALI",
    "full_name": "AHMED MOHAMED ALI",
    "nationality": "Sudanese",
    "date_of_birth": "01-01-1990",
    "date_of_expiry": "01-01-2030"
  }
}
```

---

### 2. Extract ID Card Data (Sudanese National ID)

**What it does:** Reads all information from Sudanese ID cards (front and/or back)

**Endpoint:** `POST https://5.22.215.77:5001/secure/extract-id-card-files`

**Important:** ID cards have information on BOTH sides. You can:
- Upload only the **front** image
- Upload only the **back** image
- Upload **BOTH** front AND back images in the same request (recommended for complete data)

---

#### Option A: Upload BOTH Front and Back (Recommended)

**How to send:**
Use form-data with two files:
- `front`: Front side image
- `back`: Back side image

**Example using Postman:**
1. Select POST method
2. Use URL: `https://5.22.215.77:5001/secure/extract-id-card-files`
3. Go to Body → form-data
4. Add field `front` with type "File" → Upload front image
5. Add field `back` with type "File" → Upload back image
6. Add headers:
   - `Authorization: Bearer YOUR_TOKEN`
   - `X-API-Key: your-admin-api-key`
7. Send request

**What you get back:**
```json
{
  "success": true,
  "document_type": "sudanese_id_card",
  "front_filename": "id_front.jpg",
  "back_filename": "id_back.jpg",
  "data": {
    "الرقم الوطني": "12345678901234",
    "الإسم": "احمد محمد علي",
    "الإسم الأول": "احمد",
    "الإسم الثاني": "محمد",
    "إسم العائلة": "علي",
    "تاريخ الميلاد": "01-01-1990",
    "مكان الميلاد": "الخرطوم",
    "فصيلة الدم": "O+",
    "المهنة": "مهندس",
    "العنوان": "الخرطوم - المنطقة الصناعية",
    "مكان الإصدار": "الخرطوم",
    "تاريخ الإصدار": "01-01-2020",
    "تاريخ الإنتهاء": "01-01-2030"
  },
  "confidence_scores": {
    "الرقم الوطني": 0.98,
    "الإسم": 0.95,
    "تاريخ الميلاد": 0.92
  }
}
```

---

#### Option B: Upload Only Front Side

**How to send:**
Use form-data with one file:
- `front`: Front side image only

**What you get back:**
```json
{
  "success": true,
  "front_filename": "id_front.jpg",
  "back_filename": null,
  "data": {
    "الرقم الوطني": "12345678901234",
    "الإسم": "احمد محمد علي",
    "الإسم الأول": "احمد",
    "الإسم الثاني": "محمد",
    "إسم العائلة": "علي",
    "تاريخ الميلاد": "01-01-1990",
    "مكان الميلاد": "الخرطوم"
  }
}
```

---

#### Option C: Upload Only Back Side

**How to send:**
Use form-data with one file:
- `back`: Back side image only

**What you get back:**
```json
{
  "success": true,
  "front_filename": null,
  "back_filename": "id_back.jpg",
  "data": {
    "فصيلة الدم": "O+",
    "المهنة": "مهندس",
    "العنوان": "الخرطوم - المنطقة الصناعية",
    "مكان الإصدار": "الخرطوم",
    "تاريخ الإصدار": "01-01-2020",
    "تاريخ الإنتهاء": "01-01-2030"
  }
}
```

**Tip:** For complete KYC verification, always upload BOTH sides!

---

### 3. Extract Driving License Data

**What it does:** Reads all information from Sudanese driving licenses

**Endpoint:** `POST https://5.22.215.77:5001/secure/extract-license-file`

**How to send:**
- Upload the license image file

**What you get back:**
```json
{
  "success": true,
  "data": {
    "License_Type": "PRIVATE",
    "نوع_الرخصة": "خاصة",
    "Name": "AHMED MOHAMED ALI",
    "First_Name": "AHMED",
    "Second_Name": "MOHAMED",
    "Last_Name": "ALI",
    "الاسم": "احمد محمد علي"
  }
}
```

---

### 4. Face Verification (Compare Two Faces)

**What it does:** Checks if two faces are the same person

**Endpoint:** `POST https://5.22.215.77:5001/secure/verify-faces`

**How to send:**
```json
{
  "face1": "base64_encoded_first_image",
  "face2": "base64_encoded_second_image"
}
```

**What you get back:**
```json
{
  "success": true,
  "match": true,
  "confidence": 0.95,
  "message": "Faces match with 95% confidence"
}
```

---

### 5. Complete Passport + Selfie Verification

**What it does:** Extracts passport data AND verifies if passport photo matches selfie

**Endpoint:** `POST https://5.22.215.77:5001/secure/verify-complete`

**How to send:**
- Upload two files:
  - `passport`: The passport image
  - `selfie`: The person's selfie photo

**What you get back:**
```json
{
  "success": true,
  "passport_data": {
    "full_name": "AHMED MOHAMED ALI",
    "passport_number": "A12345678"
  },
  "face_verification": {
    "match": true,
    "confidence": 0.92
  }
}
```

---

## Admin Features

### View Statistics

**Endpoint:** `GET https://5.22.215.77:5001/admin/stats`

Shows:
- Total requests processed
- Successful extractions
- Failed extractions
- Average accuracy

### View Security Logs

**Endpoint:** `GET https://5.22.215.77:5001/admin/security-logs`

Shows all security events and access logs

---

## Quick Tips

✅ **Always login first** - You can't use any service without a token

✅ **Check image quality** - Clear, well-lit images give better results

✅ **Use HTTPS** - The system uses secure encrypted connections

✅ **Save results** - Store API responses in your application database

✅ **Handle errors properly** - Implement retry logic for network issues

---

## Troubleshooting

**Problem: "Authentication required"**
- Solution: Login again and get a new token

**Problem: "Rate limit exceeded"**
- Solution: Wait a few seconds before trying again

**Problem: "Low accuracy extraction"**
- Solution: Upload a clearer, higher quality image

**Problem: "No face detected"**
- Solution: Make sure the face is clearly visible in the image

---

## FAQ for Developers (KYC Integration)

### Q1: How do I integrate this API into my KYC system?

**Answer:**
```python
import requests
import json

# Step 1: Login and get token
def login():
    response = requests.post(
        'https://5.22.215.77:5001/auth/login',
        json={
            'username': 'admin',
            'password': 'X7uFB9k@cxSnuBXhlVIo'
        },
        verify=False  # For self-signed SSL
    )
    return response.json()['token']

# Step 2: Extract ID card data
def extract_id_card(token, front_image_path, back_image_path):
    headers = {
        'Authorization': f'Bearer {token}',
        'X-API-Key': 'your-admin-api-key'
    }

    files = {
        'front': open(front_image_path, 'rb'),
        'back': open(back_image_path, 'rb')
    }

    response = requests.post(
        'https://5.22.215.77:5001/secure/extract-id-card-files',
        headers=headers,
        files=files,
        verify=False
    )

    return response.json()

# Step 3: Verify face match
def verify_face(token, passport_path, selfie_path):
    headers = {
        'Authorization': f'Bearer {token}',
        'X-API-Key': 'your-admin-api-key'
    }

    files = {
        'passport': open(passport_path, 'rb'),
        'selfie': open(selfie_path, 'rb')
    }

    response = requests.post(
        'https://5.22.215.77:5001/secure/verify-complete',
        headers=headers,
        files=files,
        verify=False
    )

    return response.json()

# Usage
token = login()
id_data = extract_id_card(token, 'front.jpg', 'back.jpg')
verification = verify_face(token, 'passport.jpg', 'selfie.jpg')

# Store in your database
if id_data['success']:
    national_id = id_data['data']['الرقم الوطني']
    full_name = id_data['data']['الإسم']
    # ... save to your database
```

---

### Q2: What is the API rate limit?

**Answer:**
- Rate limiting is configured per IP address
- Rate limit errors return HTTP 429 status code
- Wait a few seconds and retry if you receive this error
- Contact support for rate limit increases

---

### Q3: How accurate is the extraction? Can I trust the data?

**Answer:**
- System returns **confidence_scores** for each field (0.0 to 1.0)
- Check confidence before using data:
  ```python
  if data['confidence_scores']['الرقم الوطني'] > 0.85:
      # High confidence - safe to use
      save_to_database(data['data']['الرقم الوطني'])
  else:
      # Low confidence - manual review required
      flag_for_manual_review()
  ```
- Recommended threshold: **0.85 or higher** for automated processing
- Below 0.85: Flag for manual review

---

### Q4: Can this detect fake or tampered documents?

**Answer:**
- **Current system:** Extracts text only, does NOT detect forgery
- **What it checks:**
  - Image quality
  - Text readability
  - Confidence scores for extracted data
- **What it CANNOT do:**
  - Detect photoshopped images
  - Verify hologram authenticity
  - Check security features
  - Validate against government databases

**Recommendation for KYC:**
1. Use this API for data extraction
2. Implement additional checks:
   - Face liveness detection (external service)
   - Document forgery detection (external service)
   - Cross-reference with government databases
   - Check expiry dates

---

### Q5: What image formats and quality are supported?

**Answer:**
- **Supported formats:** JPG, JPEG, PNG, BMP, TIFF
- **Minimum resolution:** 800x600 pixels (higher is better)
- **Recommended resolution:** 1920x1080 or higher
- **File size limit:** 10MB maximum
- **Image quality tips:**
  - Good lighting (no shadows)
  - Clear focus (not blurry)
  - Full document visible
  - No glare or reflections
  - Straight angle (not tilted)

---

### Q6: How do I handle errors in production?

**Answer:**
```python
def safe_extract(token, front_path, back_path):
    try:
        response = requests.post(
            'https://5.22.215.77:5001/secure/extract-id-card-files',
            headers={'Authorization': f'Bearer {token}', 'X-API-Key': 'key'},
            files={'front': open(front_path, 'rb'), 'back': open(back_path, 'rb')},
            timeout=120,  # 2 minutes timeout
            verify=False
        )

        if response.status_code == 401:
            # Token expired - re-login
            token = login()
            return safe_extract(token, front_path, back_path)

        elif response.status_code == 429:
            # Rate limited - wait and retry
            time.sleep(5)
            return safe_extract(token, front_path, back_path)

        elif response.status_code == 500:
            # Server error - log and retry
            logger.error(f"Server error: {response.text}")
            time.sleep(2)
            return safe_extract(token, front_path, back_path)

        elif response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                # Extraction failed
                logger.warning(f"Extraction failed: {data.get('error')}")
                return None
            return data

    except requests.Timeout:
        logger.error("Request timeout - image processing took too long")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None
```

---

### Q7: Can I batch process multiple documents?

**Answer:**
- **Current API:** One document per request
- **For batch processing:**
  ```python
  import concurrent.futures

  def process_batch(token, documents):
      with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
          futures = [
              executor.submit(extract_id_card, token, doc['front'], doc['back'])
              for doc in documents
          ]

          results = [f.result() for f in concurrent.futures.as_completed(futures)]
      return results
  ```
- **Warning:** Respect rate limits when using parallel requests
- **Recommendation:** Max 5 concurrent requests to avoid rate limiting

---

### Q8: How do I map Arabic fields to my database?

**Answer:**
```python
# Field mapping for ID cards
ID_FIELD_MAPPING = {
    'الرقم الوطني': 'national_id',
    'الإسم': 'full_name_ar',
    'الإسم الأول': 'first_name_ar',
    'الإسم الثاني': 'middle_name_ar',
    'إسم العائلة': 'last_name_ar',
    'تاريخ الميلاد': 'date_of_birth',
    'مكان الميلاد': 'place_of_birth_ar',
    'فصيلة الدم': 'blood_type',
    'المهنة': 'occupation_ar',
    'العنوان': 'address_ar',
    'مكان الإصدار': 'issue_place_ar',
    'تاريخ الإصدار': 'issue_date',
    'تاريخ الإنتهاء': 'expiry_date'
}

def map_to_database(api_response):
    mapped = {}
    for arabic_key, db_field in ID_FIELD_MAPPING.items():
        mapped[db_field] = api_response['data'].get(arabic_key)
    return mapped

# Usage
result = extract_id_card(token, 'front.jpg', 'back.jpg')
db_data = map_to_database(result)
# Insert db_data into your database
```

---

### Q9: What happens to uploaded images? (Data Privacy)

**Answer:**
- **Result logs:** Extraction results saved to `output/results/` with timestamp
- **Security logs:** All API calls logged in `logs/security.log`
- **Uploaded images:** Processed in memory and not permanently stored by default

**For GDPR/Privacy Compliance:**
1. **No persistent storage:** Images are processed and discarded after extraction
2. **Secure logs:** Only extraction results and metadata are logged
3. **Access control:** All endpoints require JWT authentication
4. **User consent:** Get user consent before uploading sensitive documents

---

### Q10: How to handle document expiry dates?

**Answer:**
```python
from datetime import datetime

def is_document_valid(extraction_result):
    expiry_str = extraction_result['data'].get('تاريخ الإنتهاء')  # ID card
    # OR
    expiry_str = extraction_result['data'].get('date_of_expiry')  # Passport

    if not expiry_str:
        return False, "No expiry date found"

    try:
        # Parse date (format: DD-MM-YYYY)
        expiry_date = datetime.strptime(expiry_str, '%d-%m-%Y')
        today = datetime.now()

        if expiry_date < today:
            return False, "Document expired"

        # Warn if expiring within 30 days
        days_until_expiry = (expiry_date - today).days
        if days_until_expiry < 30:
            return True, f"Document expiring soon ({days_until_expiry} days)"

        return True, "Document valid"

    except ValueError:
        return False, "Invalid date format"

# Usage
result = extract_id_card(token, 'front.jpg', 'back.jpg')
is_valid, message = is_document_valid(result)

if not is_valid:
    reject_kyc_application(message)
```

---

### Q11: Can I request custom extraction fields?

**Answer:**
- Current system extracts standard document fields
- To request additional fields or customization, contact support
- Custom field extraction may require configuration changes

---

### Q12: What's the response time? Is it fast enough for real-time KYC?

**Answer:**
- **Average response time:** 3-8 seconds per document
- **Factors affecting speed:**
  - Image size (larger = slower)
  - Document quality
  - Network latency

**For real-time KYC:**
- ✅ **Acceptable:** For web applications (user waits 3-5 seconds)
- ✅ **Consider:** For mobile apps (show loading indicator)
- ❌ **Not suitable:** For instant verification (< 1 second required)

---

### Q13: How do I test the API before integrating?

**Answer:**
1. **Use Postman:**
   - Import [IDAgent.postman_collection.json](IDAgent.postman_collection.json)
   - Set base_url: `https://5.22.215.77:5001`
   - Login to get token
   - Test all endpoints

2. **Use curl:**
   ```bash
   # Login
   curl -k -X POST https://5.22.215.77:5001/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"X7uFB9k@cxSnuBXhlVIo"}'

   # Extract ID card
   curl -k -X POST https://5.22.215.77:5001/secure/extract-id-card-files \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "X-API-Key: your-admin-api-key" \
     -F "front=@front.jpg" \
     -F "back=@back.jpg"
   ```

3. **Test in sandbox environment first** before production integration

---

### Q14: Does it work with other countries' IDs (not just Sudan)?

**Answer:**
- **Currently optimized for:**
  - Sudanese Passports
  - Sudanese National ID Cards
  - Sudanese Driving Licenses

- **For other countries:**
  - May work with similar document formats
  - Accuracy varies by document type
  - Arabic/English text works best
  - Other languages may have lower accuracy

**To add support for other countries:**
- Contact support for country-specific implementations
- Custom training may be required for optimal accuracy

---

### Q15: How do I monitor API health and uptime?

**Answer:**
```python
import requests
import time

def health_check():
    try:
        response = requests.get(
            'https://5.22.215.77:5001/health',
            timeout=5,
            verify=False
        )

        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'healthy':
                return True, "API is healthy"

        return False, f"API unhealthy: {response.text}"

    except requests.Timeout:
        return False, "API timeout - server not responding"
    except Exception as e:
        return False, f"API down: {str(e)}"

# Monitor every 60 seconds
while True:
    is_healthy, message = health_check()
    if not is_healthy:
        # Send alert to your monitoring system
        send_alert(message)
    time.sleep(60)
```

**Production monitoring:**
- Use services like UptimeRobot, Pingdom, or Datadog
- Monitor endpoint: `https://5.22.215.77:5001/health`
- Set up alerts for downtime

---

## System Health Check

**Endpoint:** `GET https://5.22.215.77:5001/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "passport-extractor-secure",
  "version": "3.0"
}
```

Use this to check if the system is running properly.

---

## Contact & Support

- **Server URL:** `https://5.22.215.77:5001`
- All API endpoints require JWT authentication and API key
- For support or questions, contact your system administrator

---

## Security Notes

🔒 **Your data is secure:**
- All connections use HTTPS encryption
- JWT token authentication required
- API key validation
- Rate limiting to prevent abuse
- All actions are logged
- File validation checks

⚠️ **Important:**
- Never share your JWT token
- Never share your API key
- Tokens expire after some time - login again when needed
- Keep your password secure
