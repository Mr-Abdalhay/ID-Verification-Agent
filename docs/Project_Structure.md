# Passport Data Extractor - Project Structure

``` 
passport-extractor/
│
├── README.md                    # Main documentation
├── requirements.txt             # Python dependencies
├── install.bat                  # Windows installation script
├── install.sh                   # Linux/Mac installation script
├── run_server.bat               # Windows server starter
├── run_server.sh               # Linux/Mac server starter
│
├── src/                        # Source code
│   ├── __init__.py
│   ├── app.py                  # Ultra Enhanced Flask Server
│   ├── extractor.py            # Core extraction logic
│   ├── preprocessor.py         # Image preprocessing utilities
|   ├── tesseract_config.py     # Tesseract Configuration Module
│   └── patterns.py             # Passport patterns and configurations
│
├── tools/                      # Utility tools
│   ├── __init__.py
│   ├── diagnose.py             # Passport diagnostic tool
│   ├── enhance.py              # Image enhancement tool
│   └── calibrate.py            # Calibration tool
│
├── tests/                      # Test scripts
│   ├── test_extraction.py      # Main test script
│   ├── test_batch.py           # Batch processing test
│   └── quick_test.py           # Quick validation test
│
├── config/                         # Configuration files
│   ├── default_config.json         # Default settings
│   └── tesseract_paths.json        # Tesseract paths for different OS
│
├── examples/                       # Example usage
│   ├── sample_passport.jpg         # Sample passport image
│   ├── example_single.py           # Single image example
│   └── example_batch.py            # Batch processing example
│
├── docs/                           # Additional documentation
│   ├── USER_GUIDE.md               # Detailed user guide
│   ├── API_REFERENCE.md            # API documentation
|   ├── Configuration.md            # This Guide explains all configuration files and options in the system
|   ├── Tesseract_paths_config.md   # Tesseract_paths.json - Configuration File
│   └── TROUBLESHOOTING.md          # Common issues and solutions
│
└── output/                     # Output directory (created on first run)
    ├── enhanced/               # Enhanced images
    ├── diagnostics/            # Diagnostic reports
    └── results/                # Extraction results
```
# Results:
```
    the results is here
    
```