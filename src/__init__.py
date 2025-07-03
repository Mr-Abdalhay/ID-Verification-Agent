# src/__init__.py
"""
Passport Data Extractor - Core Package
Version 3.0 with Face Verification
"""

__version__ = "3.0.0"
__author__ = "Passport Extractor Team"

# Auto-configure Tesseract on import
try:
    from .tesseract_config import configure_tesseract
    configure_tesseract()
except Exception as e:
    print(f"Warning: Tesseract auto-configuration failed: {e}")
    print("Please run 'python tools/check_tesseract.py' to diagnose")

# Make modules available at package level
from .extractor import UltraPassportExtractor
from .preprocessor import ImagePreprocessor
from .patterns import PassportPatterns
from .face_processor import FaceProcessor, FaceVerificationResult

__all__ = [
    'UltraPassportExtractor', 
    'ImagePreprocessor', 
    'PassportPatterns',
    'FaceProcessor',
    'FaceVerificationResult'
]