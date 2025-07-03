# Passport Data Extractor - Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Python Not Found
```
ERROR: Python is not installed or not in PATH
```

**Solution:**
1. Install Python 3.8+ from https://python.org
2. During installation, check "Add Python to PATH"
3. Restart terminal/command prompt
4. Verify: `python --version`

#### Tesseract Not Found
```
WARNING: Tesseract OCR not found at default location
```

**Solution - Windows:**
```bash
# Download and install from:
https://github.com/UB-Mannheim/tesseract/wiki

# Install to default location:
C:\Program Files\Tesseract-OCR\
```

**Solution - Linux:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-ara
```

**Solution - Mac:**
```bash
brew install tesseract
brew install tesseract-lang
```

#### Pip Install Fails
```
ERROR: Failed to install dependencies
```

**Solution:**
1. Upgrade pip: `python -m pip install --upgrade pip`
2. Install manually: `pip install -r requirements.txt --no-cache-dir`
3. If SSL error: `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt`

### Server Issues

#### Server Won't Start
```
ERROR: Failed to activate virtual environment
```

**Solution:**
1. Delete venv folder
2. Run installation again
3. Check Python version compatibility

#### Port Already in Use
```
ERROR: [Errno 48] Address already in use
```

**Solution:**
1. Find process: `netstat -ano | findstr :5000` (Windows)
2. Kill process: `taskkill /PID <process_id> /F`
3. Or change port in `config/default_config.json`

#### Import Errors
```
ModuleNotFoundError: No module named 'cv2'
```

**Solution:**
```bash
# Activate virtual environment first
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Then reinstall:
pip install opencv-contrib-python
```

### Extraction Issues

#### Very Low Accuracy (<50%)

**Diagnostic Steps:**
```bash
# 1. Run diagnostic
python tools/diagnose.py problem_passport.jpg

# 2. Check diagnostic report
# Look for:
# - Resolution (should be >200 DPI)
# - Brightness (should be 100-200)
# - Sharpness (should be >100)
# - OCR readability
```

**Common Fixes:**
1. **Poor Image Quality**
   - Take new photo with better lighting
   - Use scanner instead of camera
   - Ensure 300+ DPI resolution

2. **Image Too Dark/Light**
   ```bash
   python tools/enhance.py passport.jpg
   # Test all three versions created
   ```

3. **Blurry Image**
   - Retake photo with steady hand
   - Clean camera lens
   - Check focus before capturing

#### Specific Fields Not Extracting

**Passport Number Missing**

Check if:
- 'P' character is clearly visible
- No glare on holographic elements
- Number not cut off at edge

Fix:
```python
# If pattern is different (e.g., starts with 'D' not 'P')
# Edit src/patterns.py and add:
self.passport_number.append(r'D[0-9]{8,9}')
```

**Name Not Found**

Check if:
- Name is in CAPITAL letters
- Good contrast between text and background
- No shadows on name area

Fix:
```bash
# Enhance contrast
python tools/enhance.py passport.jpg
# Use the _otsu version for better contrast
```

**Dates Wrong Format**

Check if:
- Date format is DD-MM-YYYY
- Numbers are clear and complete
- No confusion between day/month

Fix:
```python
# If format is different (e.g., MM/DD/YYYY)
# Edit src/patterns.py and add:
self.date.append(r'\d{2}/\d{2}/\d{4}')
```

#### OCR Language Issues

**Arabic Text Not Reading**

Check:
```bash
tesseract --list-langs
```

Should show 'ara' for Arabic. If not:
```bash
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr-ara

# Windows:
# Download ara.traineddata from:
https://github.com/tesseract-ocr/tessdata
# Place in: C:\Program Files\Tesseract-OCR\tessdata\
```

### Performance Issues

#### Slow Processing (>10 seconds)

**Causes:**
1. Image too large (>10MB)
2. Very high resolution (>4000px)
3. Slow CPU

**Solutions:**
```bash
# Resize image first
python -c "
import cv2
img = cv2.imread('large_passport.jpg')
resized = cv2.resize(img, (1500, 1000))
cv2.imwrite('passport_resized.jpg', resized)
"
```

#### High Memory Usage

**Solution:**
1. Process images one at a time
2. Reduce upscale_factor in config
3. Disable some preprocessing methods

### Debugging Tips

#### Enable Debug Logging

Create `debug.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from tests.test_extraction import test_passport
test_passport('passport.jpg')
```

#### Test Individual Components

**Test OCR:**
```python
import pytesseract
from PIL import Image

img = Image.open('passport.jpg')
text = pytesseract.image_to_string(img)
print(f"OCR Output:\n{text}")
```

**Test Preprocessing:**
```python
import cv2
from src.preprocessor import ImagePreprocessor

with open('passport.jpg', 'rb') as f:
    img_bytes = f.read()

processor = ImagePreprocessor({})
variants = processor.process(img_bytes)

for name, img in variants.items():
    cv2.imwrite(f'test_{name}.jpg', img)
    print(f"Saved test_{name}.jpg")
```

### Error Messages Reference

| Error | Meaning | Fix |
|-------|---------|-----|
| `ValueError: Failed to decode image` | Corrupt image file | Use valid image |
| `TesseractNotFoundError` | Tesseract not installed | Install Tesseract |
| `timeout` | Processing too long | Use smaller image |
| `HTTP 413` | File too large | Reduce file size |
| `No text detected` | OCR failed completely | Check image quality |

### Platform-Specific Issues

#### Windows

**Long Path Error:**
```
FileNotFoundError: [Errno 2] No such file or directory
```

Enable long paths:
1. Run as Administrator: `gpedit.msc`
2. Navigate to: Computer Configuration > Administrative Templates > System > Filesystem
3. Enable: "Enable Win32 long paths"

#### Linux

**Permission Denied:**
```bash
# Fix permissions
chmod +x install.sh
chmod +x run_server.sh
chmod -R 755 tools/
```

#### Mac

**SSL Certificate Error:**
```bash
# Install certificates
pip install --upgrade certifi
# Or
brew install ca-certificates
```

### Getting Help

If issues persist:

1. **Collect Information:**
   - OS and version
   - Python version: `python --version`
   - Tesseract version: `tesseract --version`
   - Error messages (full traceback)
   - Sample image (if possible)

2. **Run Diagnostic:**
   ```bash
   python tools/diagnose.py your_passport.jpg
   ```
   Share the diagnostic report

3. **Check Logs:**
   - Server logs from terminal
   - Files in `output/diagnostics/`

4. **Create Minimal Example:**
   ```python
   # minimal_test.py
   from tests.test_extraction import test_passport
   result = test_passport('problem_passport.jpg')
   print(result)
   ```

---

**Still need help?** Open an issue with all the above information.