#   

This JSON file contains all the Tesseract OCR paths and configuration for different operating systems. Here's what's inside:


## 1. **Windows Configuration**
```json
{
  "windows": {
    "default": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "alternative_paths": [
      "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
      "C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
      "C:\\Users\\%USERNAME%\\AppData\\Local\\Tesseract-OCR\\tesseract.exe"
    ],
    "download_url": "https://github.com/UB-Mannheim/tesseract/wiki",
    "installer_url": "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe"
  }
}
```

## 2. **Linux Configuration**
```json
{
  "linux": {
    "default": "/usr/bin/tesseract",
    "alternative_paths": [
      "/usr/bin/tesseract",
      "/usr/local/bin/tesseract",
      "/opt/tesseract/bin/tesseract"
    ],
    "install_commands": {
      "ubuntu": "sudo apt-get install tesseract-ocr tesseract-ocr-ara",
      "fedora": "sudo dnf install tesseract tesseract-langpack-ara",
      "arch": "sudo pacman -S tesseract tesseract-data-ara"
    }
  }
}
```

## 3. **macOS Configuration**
```json
{
  "darwin": {
    "default": "/usr/local/bin/tesseract",
    "alternative_paths": [
      "/usr/local/bin/tesseract",
      "/opt/homebrew/bin/tesseract"
    ],
    "install_commands": {
      "homebrew": "brew install tesseract",
      "homebrew_languages": "brew install tesseract-lang"
    }
  }
}
```

## 4. **Language Data Paths**
```json
{
  "language_data": {
    "required": ["eng"],
    "optional": ["ara", "fra", "spa", "deu"],
    "paths": {
      "windows": "C:\\Program Files\\Tesseract-OCR\\tessdata\\",
      "linux": "/usr/share/tesseract-ocr/5/tessdata/",
      "darwin": "/usr/local/share/tessdata/"
    }
  }
}
```

## 5. **Troubleshooting Information**
```json
{
  "troubleshooting": {
    "not_found_error": {
      "error_message": "TesseractNotFoundError",
      "solutions": [
        "Install Tesseract OCR for your operating system",
        "Add Tesseract to system PATH",
        "Specify full path in configuration"
      ]
    }
  }
}
```

## How It's Used

The system uses this file to:

1. **Auto-detect Tesseract**: Automatically finds Tesseract on your system
2. **Fallback Paths**: If not in default location, checks alternative paths
3. **Installation Help**: Provides OS-specific installation instructions
4. **Language Support**: Knows where to find/install language packs
5. **Error Handling**: Gives helpful error messages if Tesseract not found

## Benefits

- **No Manual Configuration**: The system automatically finds Tesseract
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Smart Detection**: Checks multiple possible installation locations
- **Easy Troubleshooting**: Clear error messages and solutions
- **Language Management**: Handles language pack installation

## Usage in Code

The `tesseract_config.py` module reads this JSON file and:
```python
# Automatically configures Tesseract when you import the module
from src.tesseract_config import configure_tesseract

# Or check installation
python tools/check_tesseract.py
```

This eliminates the need to manually set paths in your code!