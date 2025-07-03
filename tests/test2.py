# tests/test_face_verification.py
"""
Test script for face verification functionality
"""

import os
import sys
import json
import requests
import cv2
import numpy as np
from datetime import datetime
import argparse
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from face_processor import FaceProcessor, create_face_processor

class FaceVerificationTester:
    """Test suite for face verification"""
    
    def __init__(self, api_url="http://localhost:5000"):
        self.api_url = api_url
        self.face_processor = create_face_processor()
        self.results = []
        
    def test_face_extraction(self, document_path: str, document_type: str = "passport"):
        """Test face extraction from document"""
        print(f"\n🔍 Testing face extraction from {document_path}")
        print("=" * 50)
        
        try:
            # Test direct extraction
            document_img = cv2.imread(document_path)
            if document_img is None:
                print("❌ Failed to load document image")
                return False
            
            face_img = self.face_processor.extract_face_from_document(document_img, document_type)
            
            if face_img is None:
                print("❌ Failed to extract face from document")
                return False
            
            # Save extracted face
            output_path = f"output/test_extracted_face_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(output_path, face_img)
            
            print(f"✅ Face extracted successfully")
            print(f"📁 Saved to: {output_path}")
            print(f"📐 Face dimensions: {face_img.shape[1]}x{face_img.shape[0]}")
            
            # Test API endpoint
            print("\n🌐 Testing API endpoint...")
            with open(document_path, 'rb') as f:
                files = {'file': f}
                data = {'document_type': document_type}
                response = requests.post(f"{self.api_url}/api/extract-face", files=files, data=data)
            
            if response.status_code == 200:
                print("✅ API extraction successful")
                result = response.json()
                if 'face_base64' in result:
                    print("✅ Base64 encoding successful")
            else:
                print(f"❌ API extraction failed: {response.text}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during face extraction: {str(e)}")
            return False
    
    def test_face_verification(self, document_path: str, selfie_path: str):
        """Test face verification between document and selfie"""
        print(f"\n👤 Testing face verification")
        print(f"📄 Document: {document_path}")
        print(f"🤳 Selfie: {selfie_path}")
        print("=" * 50)
        
        try:
            # Test direct verification
            results = self.face_processor.process_verification_request(
                document_path, selfie_path
            )
            
            if results['success']:
                verification = results['verification']
                print(f"✅ Verification completed")
                print(f"🔍 Verified: {'✅' if verification['verified'] else '❌'}")
                print(f"📊 Confidence: {verification['confidence']:.2%}")
                print(f"🔧 Method: {verification['method']}")
                
                if verification.get('liveness_score') is not None:
                    print(f"🎭 Liveness score: {verification['liveness_score']:.2%}")
            else:
                print(f"❌ Verification failed: {results['errors']}")
                return False
            
            # Test API endpoint
            print("\n🌐 Testing API endpoint...")
            with open(document_path, 'rb') as doc_f, open(selfie_path, 'rb') as selfie_f:
                files = {
                    'document': doc_f,
                    'selfie': selfie_f
                }
                response = requests.post(f"{self.api_url}/api/verify", files=files)
            
            if response.status_code == 200:
                print("✅ API verification successful")
                api_result = response.json()
                if api_result.get('success'):
                    api_verification = api_result.get('verification', {})
                    print(f"🔍 API Verified: {'✅' if api_verification.get('verified') else '❌'}")
                    print(f"📊 API Confidence: {api_verification.get('confidence', 0):.2%}")
            else:
                print(f"❌ API verification failed: {response.text}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during face verification: {str(e)}")
            return False
    
    def test_complete_verification(self, document_path: str, selfie_path: str):
        """Test complete verification (passport data + face)"""
        print(f"\n🛂 Testing complete verification")
        print("=" * 50)
        
        try:
            with open(document_path, 'rb') as doc_f, open(selfie_path, 'rb') as selfie_f:
                files = {
                    'document': doc_f,
                    'selfie': selfie_f
                }
                response = requests.post(f"{self.api_url}/api/complete-verification", files=files)
            
            if response.status_code == 200:
                result = response.json()
                
                print("✅ Complete verification successful")
                print("\n📄 Passport Data:")
                passport_data = result.get('passport_data', {})
                for field, value in passport_data.items():
                    if field != 'success' and value:
                        print(f"  - {field}: {value}")
                
                print("\n👤 Face Verification:")
                face_ver = result.get('face_verification', {}).get('verification', {})
                print(f"  - Verified: {'✅' if face_ver.get('verified') else '❌'}")
                print(f"  - Confidence: {face_ver.get('confidence', 0):.2%}")
                
                print(f"\n🎯 Overall Verified: {'✅' if result.get('overall_verified') else '❌'}")
                
                return True
            else:
                print(f"❌ Complete verification failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error during complete verification: {str(e)}")
            return False
    
    def test_liveness_detection(self, image_path: str):
        """Test liveness detection"""
        print(f"\n🎭 Testing liveness detection on {image_path}")
        print("=" * 50)
        
        try:
            img = cv2.imread(image_path)
            if img is None:
                print("❌ Failed to load image")
                return False
            
            liveness_score = self.face_processor.check_liveness(img)
            
            print(f"📊 Liveness score: {liveness_score:.2%}")
            print(f"🎯 Status: {'Live' if liveness_score >= 0.7 else 'Spoof/Low quality'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during liveness detection: {str(e)}")
            return False
    
    def run_all_tests(self, document_path: str, selfie_path: str):
        """Run all tests"""
        print("\n🚀 Running Face Verification Test Suite")
        print("=" * 70)
        
        # Check if API is running
        try:
            response = requests.get(f"{self.api_url}/api/health")
            if response.status_code != 200:
                print("⚠️  Warning: API server not responding. Some tests will be skipped.")
        except:
            print("⚠️  Warning: API server not running. Some tests will be skipped.")
        
        # Run tests
        tests = [
            ("Face Extraction", lambda: self.test_face_extraction(document_path)),
            ("Face Verification", lambda: self.test_face_verification(document_path, selfie_path)),
            ("Complete Verification", lambda: self.test_complete_verification(document_path, selfie_path)),
            ("Liveness Detection", lambda: self.test_liveness_detection(selfie_path))
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                success = test_func()
                results.append((test_name, success))
            except Exception as e:
                print(f"❌ {test_name} failed with error: {str(e)}")
                results.append((test_name, False))
        
        # Summary
        print("\n📊 Test Summary")
        print("=" * 70)
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
        
        return passed == total

def main():
    parser = argparse.ArgumentParser(description='Test face verification system')
    parser.add_argument('document', help='Path to passport/ID document image')
    parser.add_argument('selfie', help='Path to selfie image')
    parser.add_argument('--api-url', default='http://localhost:5000', help='API server URL')
    parser.add_argument('--document-type', default='passport', choices=['passport', 'id_card'], 
                       help='Type of document')
    
    args = parser.parse_args()
    
    # Validate paths
    if not os.path.exists(args.document):
        print(f"❌ Document file not found: {args.document}")
        return
    
    if not os.path.exists(args.selfie):
        print(f"❌ Selfie file not found: {args.selfie}")
        return
    
    # Run tests
    tester = FaceVerificationTester(args.api_url)
    success = tester.run_all_tests(args.document, args.selfie)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()