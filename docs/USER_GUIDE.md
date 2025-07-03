# Passport Data Extractor - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Image Requirements](#image-requirements)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

## Getting Started

### Installation

1. **Install the software:**
   ```bash
   # Windows
   install.bat
   
   # Linux/Mac
   ./install.sh
   ```

2. **Start the server:**
   ```bash
   # Windows
   run_server.bat
   
   # Linux/Mac
   ./run_server.sh
   ```

3. **Verify installation:**
   ```bash
   python tests/quick_test.py
   ```

### Quick Start

Extract passport data in 3 simple steps:

1. Start the server
2. Place your passport image in an accessible location
3. Run: `python tests/test_extraction.py your_passport.jpg`

## Basic Usage

### Single Passport Extraction

```bash
python tests/test_extraction.py path/to/passport.jpg
```

This will:
- Extract all passport fields
- Show confidence scores
- Save results to `output/results/`

### Batch Processing

Process multiple passports at once:

```bash
python tests/test_extraction.py path/to/folder --batch
```

### Using the Web Interface

1. Start the server
2. Open browser: http://localhost:5000
3. Use the API endpoints or upload interface

### API Usage

#### Using cURL:
```bash
# Upload file
curl -X POST -F "file=@passport.jpg" http://localhost:5000/extract-file

# Check health
curl http://localhost:5000/health
```

#### Using Python:
```python
import requests

# Upload and extract
with open('passport.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/extract-file',
        files={'file': f}
    )
    
result = response.json()
print(f"Extracted: {result['data']}")
```

## Advanced Features

### 1. Diagnostic Tool

Analyze why extraction might be failing:

```bash
python tools/diagnose.py problematic_passport.jpg
```

This will:
- Analyze image quality
- Test OCR readability
- Create visualizations
- Generate an enhanced version
- Provide specific recommendations

### 2. Image Enhancement

Improve image quality before extraction:

```bash
python tools/enhance.py passport.jpg
```

Creates three versions:
- Enhanced grayscale
- Binary threshold (otsu)
- Adaptive threshold

### 3. Batch Enhancement

Enhance multiple images:

```bash
python tools/enhance.py folder_path --batch
```

### 4. Custom Configuration

Edit `config/default_config.json` to customize:

```json
{
  "preprocessing": {
    "upscale_factor": 2,    // Increase for very small images
    "denoise": true,        // Enable/disable denoising
    "auto_rotate": true     // Auto-correct skewed images
  },
  "extraction": {
    "confidence_threshold": 60,  // Minimum OCR confidence
    "multi_pass": true          // Try multiple OCR methods
  }
}
```

## Image Requirements

### Optimal Image Specifications

| Specification | Recommended | Minimum |
|--------------|-------------|----------|
| Resolution   | 300+ DPI    | 200 DPI  |
| Image Width  | 1500+ px    | 1000 px  |
| File Format  | JPG/PNG     | Any      |
| File Size    | 1-5 MB      | < 10 MB  |

### Image Quality Checklist

✅ **DO:**
- Use good lighting (natural daylight is best)
- Keep passport flat on surface
- Capture entire passport page
- Ensure text is in focus
- Hold camera parallel to passport

❌ **DON'T:**
- Use flash directly (causes glare)
- Include shadows
- Cut off any part of passport
- Use blurry/out-of-focus images
- Take photos at an angle

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Glare on passport | Change angle, avoid direct light |
| Shadows on text | Use diffused lighting |
| Blurry text | Hold camera steady, check focus |
| Low accuracy | Run diagnostic tool |
| Missing fields | Enhance image first |

## Troubleshooting

### Server Won't Start

1. **Check Python version:**
   ```bash
   python --version  # Should be 3.8+
   ```

2. **Check Tesseract installation:**
   ```bash
   tesseract --version
   ```

3. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Low Extraction Accuracy

1. **Run diagnostic:**
   ```bash
   python tools/diagnose.py your_passport.jpg
   ```

2. **Try enhanced versions:**
   ```bash
   python tools/enhance.py your_passport.jpg
   python tests/test_extraction.py output/enhanced/your_passport_enhanced.jpg
   ```

3. **Check image quality:**
   - Resolution too low? → Use higher quality scan/photo
   - Too dark/bright? → Adjust lighting
   - Blurry? → Retake photo with steady hand

### Specific Field Not Extracting

#### Passport Number Missing:
- Ensure the "P" followed by numbers is clearly visible
- Check for glare on holographic elements
- Try different angle to avoid reflections

#### Name Not Found:
- Names must be in CAPITAL LETTERS
- Check if name area has good contrast
- Avoid shadows on name field

#### Dates Incorrect:
- Ensure date format is clear (DD-MM-YYYY)
- Check if numbers are not cut off
- Improve focus on date fields

## Best Practices

### 1. Image Capture

**Using Phone Camera:**
```
1. Set to highest quality
2. Use HDR mode if available
3. Turn off flash
4. Use timer to avoid shake
5. Take multiple shots
```

**Using Scanner:**
```
1. Set to 300 DPI minimum
2. Use color mode
3. Save as JPG or PNG
4. Clean scanner glass first
```

### 2. Pre-processing

Always enhance images if accuracy is below 90%:

```bash
# Step 1: Diagnose
python tools/diagnose.py passport.jpg

# Step 2: Enhance
python tools/enhance.py passport.jpg

# Step 3: Extract
python tests/test_extraction.py output/enhanced/passport_enhanced.jpg
```

### 3. Batch Processing Workflow

For multiple passports:

```bash
# 1. Enhance all images
python tools/enhance.py passports_folder --batch

# 2. Extract from enhanced versions
python tests/test_extraction.py output/enhanced --batch

# 3. Check results in output/results/
```

### 4. Integration Tips

**For Production Use:**

1. Use the API endpoints
2. Implement retry logic
3. Set appropriate timeouts
4. Handle errors gracefully
5. Log all requests

**Example Integration:**
```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure retry strategy
session = requests.Session()
retry = Retry(total=3, backoff_factor=0.3)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)

# Extract with retry
def extract_passport(image_path):
    with open(image_path, 'rb') as f:
        response = session.post(
            'http://localhost:5000/extract-file',
            files={'file': f},
            timeout=30
        )
    return response.json()
```

## Additional Resources

- **API Reference**: See [API_REFERENCE.md](API_REFERENCE.md)
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **GitHub**: [Project Repository](#)
- **Support**: Open an issue on GitHub

---

**Need more help?** Check the troubleshooting guide or open an issue with:
- Your OS and Python version
- Error messages
- Sample image (if possible)
- Steps to reproduce the issue