# tests/__init__.py
"""
Passport Data Extractor - Tests Package
"""

from .test_extraction import PassportTester
from .quick_test import quick_test

__all__ = ['PassportTester', 'quick_test']