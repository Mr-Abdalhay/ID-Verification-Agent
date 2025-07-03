# Configuration Guide

This guide explains all configuration files and options in the Passport Data Extractor.

## Configuration Files

### 1. `config/default_config.json`

Main configuration file for the application:

```json
{
  "preprocessing": {
    "upscale": true,              // Enable image upscaling
    "upscale_factor": 2,          // How much to upscale (2x)
    "auto_rotate": true,          // Auto-correct skewed images
    "denoise": true,              // Apply noise reduction
    "clahe_clip_limit": 3.0       // Contrast enhancement strength
  },
  "extraction": {
    "multi_pass": true,           // Try multiple OCR methods
    "confidence_threshold": 60,    // Minimum confidence (0-100)
    "use_regions": true,          // Extract from specific regions
    "preferred_ocr_methods": [    // Preferred OCR configurations
      "uniform_block",
      "high_confidence",
      "single_column"
    ]
  },
  "server": {
    "host": "0.0.0.0",           // Listen on all interfaces
    "port": 5000,                // Server port
    "debug": false,              // Debug mode
    "max_file_size_mb": 10       // Maximum upload size
  }
}
```

### 2. `config/tesseract_paths.json`

Tesseract OCR paths for different operating systems:

```json
{
  "windows": {
    "default": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "alternative_paths": [...],  // Fallback locations
    "installer_url": "..."       // Where to download
  },
  "linux": {
    "default": "/usr/bin/tesseract",
    "install_commands": {        // OS-specific install commands
      "ubuntu": "sudo apt-get install tesseract-ocr"
    }
  }
}
```

## Environment Variables

You can override settings using environment variables:

```bash
# Server configuration
export PASSPORT_EXTRACTOR_HOST=0.0.0.0
export PASSPORT_EXTRACTOR_PORT=8080

# Tesseract path (if not auto-detected)
export TESSERACT_PATH=/custom/path/to/tesseract

# Tessdata directory
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
```

## Customization Options

### 1. Preprocessing Settings

Adjust image preprocessing in `default_config.json`:

```json
{
  "preprocessing": {
    "upscale_factor": 3,        // Increase for very small images
    "clahe_clip_limit": 4.0,    // Higher = more contrast
    "denoise": false            // Disable if images are clean
  }
}
```

### 2. OCR Configuration

Fine-tune OCR settings:

```json
{
  "extraction": {
    "confidence_threshold": 70,  // Increase for higher accuracy
    "multi_pass": false,         // Disable for faster processing
    "preferred_ocr_methods": [   // Reorder by preference
      "single_column",           // Best for simple layouts
      "sparse_text",             // Good for scattered text
      "uniform_block"            // Good for dense text
    ]
  }
}
```

### 3. Server Settings

Configure the web server:

```json
{
  "server": {
    "port": 8080,                // Change port
    "max_file_size_mb": 20,      // Increase file size limit
    "timeout": 60                // Request timeout in seconds
  }
}
```

### 4. Language Configuration

Add support for more languages:

```json
{
  "tesseract": {
    "languages": ["eng", "ara", "fra", "spa"],  // Languages to use
    "timeout": 30                                // OCR timeout
  }
}
```

## Creating Custom Configurations

### 1. Development Configuration

Create `config/dev_config.json`:

```json
{
  "server": {
    "debug": true,
    "port": 5001
  },
  "extraction": {
    "confidence_threshold": 50
  }
}
```

### 2. Production Configuration

Create `config/prod_config.json`:

```json
{
  "server": {
    "debug": false,
    "host": "0.0.0.0",
    "port": 80
  },
  "preprocessing": {
    "upscale_factor": 1.5
  }
}
```

### 3. Loading Custom Configuration

```python
# In your code
import json

# Load custom config
with open('config/custom_config.json') as f:
    custom_config = json.load(f)

# Merge with default
config = {**default_config, **custom_config}
```

## Pattern Customization

Edit `src/patterns.py` for specific passport formats:

```python
# Add custom passport number pattern
self.passport_number.append(r'[A-Z]{2}[0-9]{7}')  # AA1234567

# Add custom date format
self.date.append(r'\d{4}/\d{2}/\d{2}')  # 2024/12/15

# Add custom ID format
self.national_id.append(r'\d{4}-\d{6}')  # 1234-567890
```

## Performance Tuning

### For Speed:
```json
{
  "preprocessing": {
    "upscale": false,
    "denoise": false
  },
  "extraction": {
    "multi_pass": false,
    "use_regions": false
  }
}
```

### For Accuracy:
```json
{
  "preprocessing": {
    "upscale_factor": 3,
    "denoise": true,
    "auto_rotate": true
  },
  "extraction": {
    "multi_pass": true,
    "confidence_threshold": 80,
    "use_regions": true
  }
}
```

### For Low-Quality Images:
```json
{
  "preprocessing": {
    "upscale_factor": 4,
    "clahe_clip_limit": 5.0,
    "denoise": true
  },
  "extraction": {
    "confidence_threshold": 40,
    "multi_pass": true
  }
}
```

## Monitoring Configuration

Enable detailed logging:

```json
{
  "logging": {
    "level": "DEBUG",
    "file": "passport_extractor.log",
    "max_size_mb": 100,
    "backup_count": 5
  }
}
```

## Security Configuration

For production deployment:

```json
{
  "security": {
    "allowed_hosts": ["localhost", "your-domain.com"],
    "max_requests_per_minute": 60,
    "require_api_key": true,
    "allowed_file_types": [".jpg", ".png"],
    "max_file_size_mb": 5
  }
}
```

## Applying Configuration Changes

1. **Restart Required**: Most changes require server restart
2. **Hot Reload**: Some settings can be changed without restart
3. **Validation**: Invalid configuration will prevent startup

## Configuration Hierarchy

1. Default configuration (`default_config.json`)
2. Environment variables (override defaults)
3. Custom configuration files (override all)
4. Runtime parameters (highest priority)

## Best Practices

1. **Don't edit default_config.json** - Create custom configs instead
2. **Use environment variables** for sensitive data
3. **Test configuration changes** in development first
4. **Document custom settings** for team members
5. **Version control** your configuration files