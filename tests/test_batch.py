#!/usr/bin/env python3
"""
Batch Testing for Passport Data Extractor
Test multiple passport images in a folder
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_extraction import PassportTester

def main():
    """Main function for batch testing"""
    parser = argparse.ArgumentParser(description='Batch test passport extraction')
    parser.add_argument('folder', help='Folder containing passport images')
    parser.add_argument('--server', default='http://localhost:5000', 
                       help='Server URL (default: http://localhost:5000)')
    
    args = parser.parse_args()
    
    # Check if folder exists
    if not os.path.isdir(args.folder):
        print(f"Error: Folder not found: {args.folder}")
        return
    
    # Initialize tester
    tester = PassportTester(args.server)
    
    # Check server
    if not tester.check_server():
        return
    
    # Run batch test
    tester.test_batch(args.folder)

if __name__ == "__main__":
    main()
