#!/usr/bin/env python3
"""
Example usage of integrated passport verification API
Demonstrates OCR + Face Verification in one request
"""

import requests
import base64
import json
import sys
import os

def verify_passport_with_selfie(passport_path, selfie_path, server_url="http://localhost:5000"):
    """
    Complete example of passport verification with face matching
    
    Args:
        passport_path: Path to passport image
        selfie_path: Path to selfie image
        server_url: API server URL
    """
    
    print("🛂 Passport Verification Example")
    print("="*50)
    
    # Check if files exist
    if not os.path.exists(passport_path):
        print(f"❌ Error: Passport image not found: {passport_path}")
        return
    
    if not os.path.exists(selfie_path):
        print(f"❌ Error: Selfie image not found: {selfie_path}")
        return
    
    # Step 1: Encode images to base64
    print("\n1️⃣ Encoding images...")
    
    try:
        with open(passport_path, 'rb') as f:
            passport_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        with open(selfie_path, 'rb') as f:
            selfie_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        print("   ✅ Images encoded successfully")
    except Exception as e:
        print(f"   ❌ Error encoding images: {str(e)}")
        return
    
    # Step 2: Send verification request
    print("\n2️⃣ Sending verification request...")
    
    try:
        response = requests.post(
            f"{server_url}/verify-passport",
            json={
                'passport_image': f'data:image/jpeg;base64,{passport_base64}',
                'selfie_image': f'data:image/jpeg;base64,{selfie_base64}'
            },
            headers={'Content-Type': 'application/json'},
            timeout=1200
        )
        
        if response.status_code != 200:
            print(f"   ❌ Server returned error: {response.status_code}")
            return
        
        result = response.json()
        
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out (30 seconds)")
        return
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")
        return
    
    # Step 3: Process results
    if not result.get('success'):
        print(f"   ❌ Verification failed: {result.get('error', 'Unknown error')}")
        return
    
    print("   ✅ Verification completed!")
    
    # Step 4: Display passport data
    print("\n3️⃣ Extracted Passport Data:")
    print("-"*50)
    
    passport_data = result['passport_data']
    
    # Display main fields
    fields = [
        ('Passport Number', 'passport_number', '🔢'),
        ('Full Name', 'full_name', '👤'),
        ('Nationality', 'nationality', '🌍'),
        ('Date of Birth', 'date_of_birth', '🎂'),
        ('Date of Issue', 'date_of_issue', '📅'),
        ('Date of Expiry', 'date_of_expiry', '📅'),
        ('Gender', 'sex', '⚧'),
        ('Place of Birth', 'place_of_birth', '📍'),
        ('National ID', 'national_id', '🆔')
    ]
    
    for display_name, field_key, emoji in fields:
        value = passport_data.get(field_key, 'Not found')
        if value and value != 'Not found':
            print(f"   {emoji} {display_name}: {value}")
    
    print(f"\n   📊 OCR Accuracy: {passport_data.get('extraction_score', 0):.1f}%")
    print(f"   📝 Fields Extracted: {passport_data.get('extraction_summary', 'N/A')}")
    
    # Step 5: Display face verification results
    print("\n4️⃣ Face Verification Results:")
    print("-"*50)
    
    face_result = result['face_verification']
    
    print(f"   🎯 Face Match: {'✅ YES' if face_result['verified'] else '❌ NO'}")
    print(f"   🔍 Confidence: {face_result['confidence']:.1%}")
    print(f"   🤳 Liveness Score: {face_result['liveness_score']:.2f}/1.00")
    print(f"   🛡️ Anti-Spoofing: {'✅ PASSED' if face_result['liveness_passed'] else '❌ FAILED'}")
    
    # Step 6: Overall verification status
    print("\n5️⃣ Overall Verification Status:")
    print("-"*50)
    
    overall = result['overall_verification']
    
    status_emoji = "✅" if overall['status'] == "VERIFIED" else "❌"
    print(f"\n   {status_emoji} Final Status: {overall['status']}")
    
    print("\n   Verification Components:")
    print(f"   {'✅' if overall['ocr_score'] > 70 else '❌'} OCR Quality: {overall['ocr_score']:.1f}% (min: 70%)")
    print(f"   {'✅' if overall['face_match'] else '❌'} Face Match: {'Verified' if overall['face_match'] else 'Failed'}")
    print(f"   {'✅' if overall['liveness_check'] else '❌'} Liveness: {'Passed' if overall['liveness_check'] else 'Failed'}")
    
    # Step 7: Save results
    print("\n6️⃣ Saving Results...")
    
    # Save full results
    results_file = f"verification_result_{passport_data.get('passport_number', 'unknown')}.json"
    with open(results_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"   📄 Full results saved to: {results_file}")
    
    # Save extracted face
    if 'extracted_face' in result:
        face_file = f"extracted_face_{passport_data.get('passport_number', 'unknown')}.jpg"
        face_data = base64.b64decode(result['extracted_face'])
        with open(face_file, 'wb') as f:
            f.write(face_data)
        print(f"   🖼️ Extracted face saved to: {face_file}")
    
    # Summary
    print("\n" + "="*50)
    if overall['status'] == "VERIFIED":
        print("✅ VERIFICATION SUCCESSFUL")
        print(f"   Person: {passport_data.get('full_name', 'Unknown')}")
        print(f"   Passport: {passport_data.get('passport_number', 'Unknown')}")
        print(f"   Valid Until: {passport_data.get('date_of_expiry', 'Unknown')}")
    else:
        print("❌ VERIFICATION FAILED")
        print("   Please check:")
        if overall['ocr_score'] <= 70:
            print("   - Passport image quality")
        if not overall['face_match']:
            print("   - Face doesn't match passport")
        if not overall['liveness_check']:
            print("   - Liveness check failed (possible spoofing)")
    
    print("="*50)

def main():
    """Main function"""
    if len(sys.argv) != 3:
        print("Usage: python example_integrated_verification.py <passport_image> <selfie_image>")
        print("\nExample:")
        print("  python example_integrated_verification.py passport.jpg selfie.jpg")
        sys.exit(1)
    
    passport_path = sys.argv[1]
    selfie_path = sys.argv[2]
    
    # Check server
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code != 200:
            print("❌ Error: Server is not running properly")
            print("   Start the server with: python src/app.py")
            sys.exit(1)
    except:
        print("❌ Error: Server is not running!")
        print("   Start the server with: python src/app.py")
        sys.exit(1)
    
    # Run verification
    verify_passport_with_selfie(passport_path, selfie_path)

if __name__ == "__main__":
    main()