#!/usr/bin/env python3
"""
Example: Extract data from a single passport image
"""

import requests
import json
import sys
import os

def extract_single_passport(image_path):
    """Extract passport data from a single image"""
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return None
    
    # Server URL
    url = "http://localhost:5000/extract-file"
    
    print(f"Extracting passport data from: {image_path}")
    print("-" * 50)
    
    try:
        # Open and send file
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files, timeout=30)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            
            if result['success']:
                data = result['data']
                
                # Display results
                print("✅ Extraction Successful!")
                print(f"Accuracy: {result['accuracy']}")
                print("\nExtracted Data:")
                print("-" * 50)
                
                # Format and display each field
                field_names = {
                    'passport_number': 'Passport Number',
                    'full_name': 'Full Name',
                    'nationality': 'Nationality',
                    'date_of_birth': 'Date of Birth',
                    'date_of_issue': 'Date of Issue',
                    'date_of_expiry': 'Date of Expiry',
                    'place_of_birth': 'Place of Birth',
                    'sex': 'Gender',
                    'national_id': 'National ID'
                }
                
                for key, display_name in field_names.items():
                    value = data.get(key, 'Not found')
                    if value and value != 'Not found':
                        confidence = data.get('confidence_scores', {}).get(key, 0)
                        print(f"{display_name}: {value}")
                        if confidence:
                            print(f"  └─ Confidence: {confidence:.0%}")
                
                # Save results
                output_file = 'passport_data.json'
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"\n💾 Results saved to: {output_file}")
                
                return data
                
            else:
                print(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")
                return None
                
        else:
            print(f"❌ Server error: HTTP {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to server")
        print("Make sure the server is running: run_server.bat (Windows) or ./run_server.sh (Linux/Mac)")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python example_single.py <passport_image>")
        print("Example: python example_single.py passport.jpg")
        return
    
    image_path = sys.argv[1]
    extract_single_passport(image_path)

if __name__ == "__main__":
    main()