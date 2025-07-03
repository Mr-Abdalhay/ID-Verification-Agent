#!/usr/bin/env python3
"""
Passport Data Extractor - Test Script
Test passport extraction with detailed results
"""

import requests
import base64
import json
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PassportTester:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.results = []
        
    def check_server(self) -> bool:
        """Check if server is running"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=2)
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Server is running: {health.get('service', 'Unknown')}")
                print(f"   Version: {health.get('version', 'Unknown')}")
                return True
        except:
            pass
        
        print("❌ Server is not running!")
        print(f"   Please start the server first:")
        print(f"   Windows: run_server.bat")
        print(f"   Linux/Mac: ./run_server.sh")
        return False
    
    def test_passport(self, image_path: str, save_results: bool = True) -> Dict:
        """Test passport extraction"""
        print(f"\n{'='*60}")
        print(f"TESTING PASSPORT EXTRACTION")
        print(f"{'='*60}")
        print(f"Image: {image_path}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"❌ Error: File not found: {image_path}")
            return {'success': False, 'error': 'File not found'}
        
        # Get file size
        file_size = os.path.getsize(image_path) / (1024 * 1024)  # MB
        print(f"File size: {file_size:.2f} MB")
        
        # Read and encode image
        print("Processing image...")
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Send request
        start_time = datetime.now()
        
        try:
            response = requests.post(
                f"{self.server_url}/extract",
                json={'image': f'data:image/jpeg;base64,{image_data}'},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                
                if result['success']:
                    data = result['data']
                    accuracy = result.get('accuracy', 'Unknown')
                    
                    print(f"\n✨ EXTRACTION SUCCESSFUL")
                    print(f"Processing time: {processing_time:.2f} seconds")
                    print(f"Accuracy: {accuracy}")
                    print(f"{'-'*60}")
                    
                    # Display results
                    fields = [
                        ('Passport Type', 'passport_type'),
                        ('Country Code', 'country_code'),
                        ('Passport Number', 'passport_number'),
                        ('Full Name', 'full_name'),
                        ('Nationality', 'nationality'),
                        ('National ID', 'national_id'),
                        ('Place of Birth', 'place_of_birth'),
                        ('Gender', 'sex'),
                        ('Date of Birth', 'date_of_birth'),
                        ('Date of Issue', 'date_of_issue'),
                        ('Date of Expiry', 'date_of_expiry'),
                    ]
                    
                    found_count = 0
                    missing_fields = []
                    
                    for display_name, field_key in fields:
                        value = data.get(field_key)
                        if value:
                            confidence = data.get('confidence_scores', {}).get(field_key, 0)
                            print(f"✅ {display_name:20}: {value}")
                            if confidence:
                                print(f"   Confidence: {confidence:.0%}")
                            found_count += 1
                        else:
                            print(f"❌ {display_name:20}: Not found")
                            missing_fields.append(display_name)
                    
                    print(f"{'-'*60}")
                    print(f"Summary: {data.get('extraction_summary', f'{found_count} fields found')}")
                    print(f"Overall Score: {data.get('extraction_score', 0):.1f}%")
                    
                    # Save results if requested
                    if save_results:
                        result_file = result.get('result_file', 'output/results/last_extraction.json')
                        print(f"\nResults saved to: {result_file}")
                    
                    # Analysis
                    print(f"\n📊 ANALYSIS:")
                    if data.get('extraction_score', 0) >= 90:
                        print("   🎉 Excellent extraction rate!")
                    elif data.get('extraction_score', 0) >= 70:
                        print("   ⚡ Good extraction rate")
                        if missing_fields:
                            print(f"   Missing fields: {', '.join(missing_fields[:3])}")
                    else:
                        print("   ⚠️  Low extraction rate")
                        print("   Try running: python tools/diagnose.py")
                    
                    # Store result
                    self.results.append({
                        'file': os.path.basename(image_path),
                        'success': True,
                        'score': data.get('extraction_score', 0),
                        'found_fields': found_count,
                        'processing_time': processing_time,
                        'data': data
                    })
                    
                    return result
                    
                else:
                    print(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")
                    self.results.append({
                        'file': os.path.basename(image_path),
                        'success': False,
                        'error': result.get('error', 'Unknown error')
                    })
                    return result
                    
            else:
                print(f"❌ Request failed with status: {response.status_code}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except requests.exceptions.Timeout:
            print("❌ Request timed out (30 seconds)")
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def test_batch(self, folder_path: str):
        """Test multiple passports in a folder"""
        print(f"\n{'='*60}")
        print(f"BATCH TESTING")
        print(f"{'='*60}")
        print(f"Folder: {folder_path}\n")
        
        # Find image files
        extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
        image_files = []
        
        for file in os.listdir(folder_path):
            if any(file.endswith(ext) for ext in extensions):
                image_files.append(os.path.join(folder_path, file))
        
        if not image_files:
            print("No image files found!")
            return
        
        print(f"Found {len(image_files)} images\n")
        
        # Process each image
        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] Processing: {os.path.basename(image_path)}")
            self.test_passport(image_path, save_results=True)
        
        # Summary
        self.print_batch_summary()
    
    def print_batch_summary(self):
        """Print summary of batch results"""
        if not self.results:
            return
        
        print(f"\n{'='*60}")
        print(f"BATCH SUMMARY")
        print(f"{'='*60}")
        
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        print(f"Total processed: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        
        if successful:
            avg_score = sum(r['score'] for r in successful) / len(successful)
            avg_time = sum(r['processing_time'] for r in successful) / len(successful)
            
            print(f"\nAverage accuracy: {avg_score:.1f}%")
            print(f"Average processing time: {avg_time:.2f} seconds")
            
            print(f"\nDetailed Results:")
            print(f"{'File':<30} {'Score':<10} {'Fields':<10} {'Time':<10}")
            print(f"{'-'*60}")
            
            for r in self.results:
                if r['success']:
                    print(f"{r['file']:<30} {r['score']:<10.1f} {r['found_fields']:<10} {r['processing_time']:<10.2f}")
                else:
                    print(f"{r['file']:<30} {'ERROR':<10} {'-':<10} {'-':<10}")

def main():
    parser = argparse.ArgumentParser(description='Test passport extraction')
    parser.add_argument('image_path', nargs='?', help='Path to passport image or folder')
    parser.add_argument('--server', default='http://localhost:5000', help='Server URL')
    parser.add_argument('--batch', action='store_true', help='Batch process folder')
    
    args = parser.parse_args()
    
    # Create tester
    tester = PassportTester(args.server)
    
    # Check server
    if not tester.check_server():
        return
    
    # If no image path provided, use sample
    if not args.image_path:
        sample_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'sample_passport.jpg')
        if os.path.exists(sample_path):
            print(f"\nNo image specified. Using sample: {sample_path}")
            args.image_path = sample_path
        else:
            print("\nUsage: python test_extraction.py <image_path>")
            print("       python test_extraction.py <folder_path> --batch")
            return
    
    # Test
    if args.batch or os.path.isdir(args.image_path):
        tester.test_batch(args.image_path)
    else:
        tester.test_passport(args.image_path)

if __name__ == "__main__":
    main()