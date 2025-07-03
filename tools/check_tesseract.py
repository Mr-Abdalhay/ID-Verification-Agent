#!/usr/bin/env python3
"""
Check Tesseract Installation and Configuration
"""

import sys
import os
import json
import platform
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tesseract_config import TesseractConfig, configure_tesseract

def check_tesseract_installation():
    """Comprehensive Tesseract installation check"""
    print("=" * 60)
    print("TESSERACT OCR INSTALLATION CHECK")
    print("=" * 60)
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Python Version: {sys.version}")
    print("=" * 60)
    
    # Load configuration
    config = TesseractConfig()
    
    print("\n1. CHECKING TESSERACT EXECUTABLE")
    print("-" * 40)
    
    if config.find_tesseract():
        print(f"✅ Tesseract found at: {config.tesseract_path}")
        
        # Get version
        try:
            import pytesseract
            if config.tesseract_path != 'tesseract':
                pytesseract.pytesseract.tesseract_cmd = config.tesseract_path
            
            version = pytesseract.get_tesseract_version()
            print(f"   Version: {version}")
            
            # Check version requirements
            version_str = str(version).split()[0]
            major_version = int(version_str.split('.')[0])
            
            if major_version >= 4:
                print(f"   ✅ Version {version_str} meets minimum requirement (4.0+)")
            else:
                print(f"   ⚠️  Version {version_str} is below recommended (4.0+)")
                
        except Exception as e:
            print(f"   ❌ Error getting version: {str(e)}")
    else:
        print("❌ Tesseract NOT FOUND")
        print("\nPossible locations checked:")
        for path in config.config[config.system]['alternative_paths']:
            print(f"   - {path}")
    
    print("\n2. CHECKING LANGUAGE PACKS")
    print("-" * 40)
    
    try:
        languages = pytesseract.get_languages()
        print(f"Installed languages: {len(languages)}")
        
        # Check required languages
        required = ['eng']
        optional = ['ara', 'fra', 'spa']
        
        print("\nRequired languages:")
        for lang in required:
            if lang in languages:
                print(f"   ✅ {lang} - installed")
            else:
                print(f"   ❌ {lang} - MISSING")
        
        print("\nOptional languages:")
        for lang in optional:
            if lang in languages:
                print(f"   ✅ {lang} - installed")
            else:
                print(f"   ⚪ {lang} - not installed")
        
        # Show all languages
        if len(languages) > len(required) + len(optional):
            other_langs = [l for l in languages if l not in required + optional + ['osd', 'snum']]
            if other_langs:
                print(f"\nOther languages: {', '.join(other_langs[:10])}")
                if len(other_langs) > 10:
                    print(f"   ... and {len(other_langs) - 10} more")
                    
    except Exception as e:
        print(f"❌ Error checking languages: {str(e)}")
    
    print("\n3. CHECKING TESSDATA PATH")
    print("-" * 40)
    
    tessdata_path = config.get_tessdata_path()
    if tessdata_path and os.path.exists(tessdata_path):
        print(f"✅ Tessdata directory: {tessdata_path}")
        
        # Count language files
        try:
            files = [f for f in os.listdir(tessdata_path) if f.endswith('.traineddata')]
            print(f"   Language files: {len(files)}")
        except:
            pass
    else:
        print("⚠️  Tessdata directory not found")
        print(f"   Expected at: {config.config['language_data']['paths'][config.system]}")
    
    print("\n4. INSTALLATION STATUS")
    print("-" * 40)
    
    if config.tesseract_path:
        print("✅ Tesseract is installed and configured")
        print("\nYou can use the passport extractor!")
    else:
        print("❌ Tesseract is NOT installed")
        print("\nINSTALLATION INSTRUCTIONS:")
        print("-" * 40)
        print(config.get_install_instructions())
    
    print("\n5. TESTING OCR FUNCTIONALITY")
    print("-" * 40)
    
    if config.tesseract_path:
        try:
            # Create a simple test image
            import numpy as np
            import cv2
            
            # Create white image with black text
            img = np.ones((50, 200, 3), dtype=np.uint8) * 255
            cv2.putText(img, "TEST 123", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            
            # Try OCR
            text = pytesseract.image_to_string(img)
            if "TEST" in text and "123" in text:
                print("✅ OCR test successful!")
                print(f"   Extracted: {text.strip()}")
            else:
                print("⚠️  OCR test returned unexpected result")
                print(f"   Expected: TEST 123")
                print(f"   Got: {text.strip()}")
                
        except Exception as e:
            print(f"❌ OCR test failed: {str(e)}")
    
    print("\n" + "=" * 60)
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'system': platform.system(),
        'tesseract_found': bool(config.tesseract_path),
        'tesseract_path': config.tesseract_path,
        'tessdata_path': tessdata_path,
        'languages': languages if 'languages' in locals() else [],
        'status': 'ready' if config.tesseract_path else 'not_installed'
    }
    
    with open('tesseract_check_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("Report saved to: tesseract_check_report.json")
    
    return config.tesseract_path is not None

def main():
    """Main function"""
    success = check_tesseract_installation()
    
    if not success:
        print("\n💡 Quick Fix:")
        print("1. Run the installer: install.bat (Windows) or ./install.sh (Linux/Mac)")
        print("2. Or install manually using the instructions above")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())