#!/usr/bin/env python3
"""
Test script for face verification functionality
Tests both individual face endpoints and combined OCR + face verification
"""

import requests
import base64
import json
import os
import sys
import argparse
from datetime import datetime

class FaceVerificationTester:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        
    def encode_image(self, image_path):
        """Encode image to base64"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def test_face_extraction(self, passport_image_path):
        """Test face extraction from passport"""
        print("\n" + "="*60)
        print("TEST 1: Face Extraction from Passport")
        print("="*60)
        
        try:
            # Encode image
            image_data = self.encode_image(passport_image_path)
            
            # Send request
            response = requests.post(
                f"{self.server_url}/extract-face",
                json={
                    'image': f'data:image/jpeg;base64,{image_data}',
                    'document_type': 'passport'
                },
                headers={'Content-Type': 'application/json'}
            )
            
            result = response.json()
            
            if result['success']:
                print("✅ Face extraction successful!")
                print(f"   Detection score: {result['metadata'].get('det_score', 'N/A')}")
                print(f"   Face location: {result['metadata'].get('bbox', 'N/A')}")
                
                # Save extracted face
                if 'face_image' in result:
                    face_data = base64.b64decode(result['face_image'])
                    with open('output/test_extracted_face.jpg', 'wb') as f:
                        f.write(face_data)
                    print("   Extracted face saved to: output/test_extracted_face.jpg")
            else:
                print(f"❌ Face extraction failed: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def test_face_verification(self, face1_path, face2_path):
        """Test face verification between two images"""
        print("\n" + "="*60)
        print("TEST 2: Face Verification")
        print("="*60)
        
        try:
            # Encode images
            face1_data = self.encode_image(face1_path)
            face2_data = self.encode_image(face2_path)
            
            # Send request
            response = requests.post(
                f"{self.server_url}/verify-faces",
                json={
                    'face1': f'data:image/jpeg;base64,{face1_data}',
                    'face2': f'data:image/jpeg;base64,{face2_data}'
                },
                headers={'Content-Type': 'application/json'}
            )
            
            result = response.json()
            
            if result['success']:
                print(f"✅ Face verification completed!")
                print(f"   Verified: {'YES' if result['verified'] else 'NO'}")
                print(f"   Confidence: {result['confidence']:.2%}")
                print(f"   Method: {result['method']}")
                if result.get('liveness_score'):
                    print(f"   Liveness score: {result['liveness_score']:.2f}")
            else:
                print(f"❌ Face verification failed: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def test_complete_passport_verification(self, passport_path, selfie_path):
        """Test complete passport verification (OCR + Face)"""
        print("\n" + "="*60)
        print("TEST 3: Complete Passport Verification (OCR + Face)")
        print("="*60)
        
        try:
            # Encode images
            passport_data = self.encode_image(passport_path)
            selfie_data = self.encode_image(selfie_path)
            
            print("Sending passport and selfie for verification...")
            
            # Send request
            response = requests.post(
                f"{self.server_url}/verify-passport",
                json={
                    'passport_image': f'data:image/jpeg;base64,{passport_data}',
                    'selfie_image': f'data:image/jpeg;base64,{selfie_data}'
                },
                headers={'Content-Type': 'application/json'},
                timeout=120  # Increased timeout to 2 minutes for complete verification
            )
            
            result = response.json()
            
            if result['success']:
                print("\n✅ Complete verification successful!")
                
                # OCR Results
                print("\n📝 Passport Data Extracted:")
                passport_data = result['passport_data']
                fields = [
                    ('Passport Number', 'passport_number'),
                    ('Full Name', 'full_name'),
                    ('Nationality', 'nationality'),
                    ('Date of Birth', 'date_of_birth'),
                    ('Date of Expiry', 'date_of_expiry')
                ]
                
                for display, key in fields:
                    value = passport_data.get(key, 'Not found')
                    if value and value != 'Not found':
                        print(f"   {display}: {value}")
                
                print(f"\n   OCR Score: {passport_data.get('extraction_score', 0):.1f}%")
                
                # Face Verification Results
                print("\n👤 Face Verification:")
                face_result = result['face_verification']
                print(f"   Face Match: {'YES' if face_result['verified'] else 'NO'}")
                print(f"   Confidence: {face_result['confidence']:.2%}")
                print(f"   Liveness Score: {face_result['liveness_score']:.2f}")
                print(f"   Liveness Check: {'PASSED' if face_result['liveness_passed'] else 'FAILED'}")
                
                # Overall Result
                print("\n🔍 Overall Verification:")
                overall = result['overall_verification']
                print(f"   Status: {overall['status']}")
                print(f"   OCR Score: {overall['ocr_score']:.1f}%")
                print(f"   Face Match: {'YES' if overall['face_match'] else 'NO'}")
                print(f"   Liveness: {'PASSED' if overall['liveness_check'] else 'FAILED'}")
                
                # Save extracted face
                if 'extracted_face' in result:
                    face_data = base64.b64decode(result['extracted_face'])
                    with open('output/test_passport_face.jpg', 'wb') as f:
                        f.write(face_data)
                    print("\n   Extracted passport face saved to: output/test_passport_face.jpg")
                
            else:
                print(f"❌ Complete verification failed: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def test_file_upload_verification(self, passport_path, selfie_path):
        """Test verification with file upload"""
        print("\n" + "="*60)
        print("TEST 4: File Upload Verification")
        print("="*60)
        
        try:
            with open(passport_path, 'rb') as p, open(selfie_path, 'rb') as s:
                files = {
                    'passport': p,
                    'selfie': s
                }
                
                response = requests.post(
                    f"{self.server_url}/verify-complete",
                    files=files,
                    timeout=120  # Increased timeout to 2 minutes for complete verification
                )
            
            result = response.json()
            
            if result['success']:
                print("✅ File upload verification successful!")
                overall = result['overall_verification']
                print(f"   Final Status: {overall['status']}")
            else:
                print(f"❌ Verification failed: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Test face verification functionality')
    parser.add_argument('--server', default='http://localhost:5000', help='Server URL')
    parser.add_argument('--passport', help='Path to passport image')
    parser.add_argument('--selfie', help='Path to selfie image')
    parser.add_argument('--face1', help='Path to first face image')
    parser.add_argument('--face2', help='Path to second face image')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    tester = FaceVerificationTester(args.server)
    
    print("\n🔍 Face Verification Test Suite")
    print("="*60)
    
    # Check server
    try:
        response = requests.get(f"{args.server}/health", timeout=2)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Server is running: {health['service']} v{health['version']}")
            print(f"   Features: {', '.join(health['features'][:3])}...")
        else:
            print("❌ Server not responding properly")
            return
    except:
        print("❌ Server is not running!")
        print("   Start it with: python src/app.py")
        return
    
    # Run tests based on arguments
    if args.all or (args.passport and args.selfie):
        if args.passport and args.selfie:
            # Test complete verification
            tester.test_complete_passport_verification(args.passport, args.selfie)
            
            # Test file upload
            tester.test_file_upload_verification(args.passport, args.selfie)
        else:
            print("\n⚠️  --all requires --passport and --selfie arguments")
    
    elif args.passport:
        # Test face extraction only
        tester.test_face_extraction(args.passport)
    
    elif args.face1 and args.face2:
        # Test face verification only
        tester.test_face_verification(args.face1, args.face2)
    
    else:
        print("\nUsage examples:")
        print("  1. Extract face from passport:")
        print("     python test_face_verification.py --passport passport.jpg")
        print("\n  2. Verify two faces:")
        print("     python test_face_verification.py --face1 face1.jpg --face2 face2.jpg")
        print("\n  3. Complete passport verification:")
        print("     python test_face_verification.py --passport passport.jpg --selfie selfie.jpg")
        print("\n  4. Run all tests:")
        print("     python test_face_verification.py --all --passport passport.jpg --selfie selfie.jpg")

if __name__ == "__main__":
    main()