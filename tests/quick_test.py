#!/usr/bin/env python3
"""
Quick Test Script
Fast validation of passport extraction
"""

import requests
import base64
import os
import sys

def quick_test(image_path=None):
    """Quick test of passport extraction"""
    
    print("\n" + "="*50)
    print("QUICK PASSPORT EXTRACTION TEST")
    print("="*50)
    
    # Use sample image if none provided
    if not image_path:
        # Try to find a test image
        test_paths = [
            "examples/sample_passport.jpg",
            "../examples/sample_passport.jpg",
            "test.jpg",
            "passport.jpg"
        ]
        
        for path in test_paths:
            if os.path.exists(path):
                image_path = path
                print(f"Using test image: {path}")
                break
        
        if not image_path:
            print("❌ No test image found!")
            print("Usage: python quick_test.py <image_path>")
            return
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    # Check server
    try:
        health = requests.get("http://localhost:5000/health", timeout=2)
        if health.status_code == 200:
            print("✅ Server is running")
        else:
            raise Exception("Server not responding")
    except:
        print("❌ Server is not running!")
        print("   Start it with: run_server.bat (Windows) or ./run_server.sh (Linux/Mac)")
        return
    
    # Read and encode image
    print(f"\nProcessing: {os.path.basename(image_path)}")
    print("-" * 50)
    
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Send request
    try:
        response = requests.post(
            "http://localhost:5000/extract",
            json={'image': f'data:image/jpeg;base64,{image_data}'},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result['success']:
                data = result['data']
                accuracy = result.get('accuracy', 'Unknown')
                
                print(f"✨ Extraction successful! Accuracy: {accuracy}")
                print("-" * 50)
                
                # Key fields to check
                fields = [
                    ('Passport Number', 'passport_number'),
                    ('Full Name', 'full_name'),
                    ('Nationality', 'nationality'),
                    ('Date of Birth', 'date_of_birth'),
                    ('Date of Expiry', 'date_of_expiry')
                ]
                
                found = 0
                for display, key in fields:
                    value = data.get(key)
                    if value:
                        print(f"✅ {display}: {value}")
                        found += 1
                    else:
                        print(f"❌ {display}: Not found")
                
                print("-" * 50)
                score = data.get('extraction_score', 0)
                print(f"Score: {score:.1f}% ({found}/{len(fields)} key fields)")
                
                if score >= 90:
                    print("🎉 Excellent extraction!")
                elif score >= 70:
                    print("⚡ Good extraction")
                else:
                    print("⚠️  Low extraction - run diagnostic tool")
                
            else:
                print(f"❌ Extraction failed: {result.get('error')}")
        else:
            print(f"❌ Request failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    quick_test(image_path)