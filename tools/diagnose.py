#!/usr/bin/env python3
"""
Passport Diagnostic Tool
Analyzes passport images to identify extraction problems
"""

import cv2
import numpy as np
import pytesseract
import platform
import matplotlib.pyplot as plt
import json
import os
import sys
import argparse
from datetime import datetime

# Configure Tesseract
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class PassportDiagnostic:
    def __init__(self, image_path: str, output_dir: str = "output/diagnostics"):
        self.image_path = image_path
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load image
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError(f"Cannot load image from {image_path}")
        
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'image_path': image_path,
            'image_quality': {},
            'ocr_readability': {},
            'preprocessing_recommendations': [],
            'extraction_problems': []
        }
    
    def run_full_diagnostic(self):
        """Run complete diagnostic analysis"""
        print("\n" + "="*60)
        print("PASSPORT DIAGNOSTIC ANALYSIS")
        print("="*60)
        print(f"Image: {self.image_path}")
        print(f"Time: {datetime.now()}")
        
        # Analyze image quality
        self.analyze_image_quality()
        
        # Test OCR readability
        self.test_ocr_readability()
        
        # Create visualizations
        self.create_visualizations()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Create enhanced version
        self.create_enhanced_image()
        
        # Save report
        self.save_report()
        
        return self.diagnostics
    
    def analyze_image_quality(self):
        """Analyze image quality metrics"""
        print("\n" + "="*60)
        print("IMAGE QUALITY ANALYSIS")
        print("="*60)
        
        # Resolution
        height, width = self.image.shape[:2]
        dpi = width / 3.5  # Assuming passport width ~3.5 inches
        
        self.diagnostics['image_quality']['resolution'] = f"{width}x{height}"
        self.diagnostics['image_quality']['estimated_dpi'] = int(dpi)
        
        print(f"Resolution: {width}x{height} pixels")
        print(f"Estimated DPI: {int(dpi)}")
        
        if dpi < 200:
            print("⚠️  Low resolution! Recommended: 300+ DPI")
            self.diagnostics['preprocessing_recommendations'].append(
                "Increase image resolution (use higher quality scan/photo)"
            )
        else:
            print("✅ Good resolution")
        
        # Brightness
        brightness = np.mean(self.gray)
        self.diagnostics['image_quality']['brightness'] = float(brightness)
        
        print(f"\nBrightness: {brightness:.1f}/255")
        if brightness < 100:
            print("⚠️  Image too dark")
            self.diagnostics['preprocessing_recommendations'].append("Increase brightness")
        elif brightness > 200:
            print("⚠️  Image too bright")
            self.diagnostics['preprocessing_recommendations'].append("Decrease brightness")
        else:
            print("✅ Good brightness")
        
        # Contrast
        contrast = np.std(self.gray)
        self.diagnostics['image_quality']['contrast'] = float(contrast)
        
        print(f"Contrast (std dev): {contrast:.1f}")
        if contrast < 30:
            print("⚠️  Low contrast")
            self.diagnostics['preprocessing_recommendations'].append("Increase contrast")
        else:
            print("✅ Good contrast")
        
        # Sharpness
        laplacian_var = cv2.Laplacian(self.gray, cv2.CV_64F).var()
        self.diagnostics['image_quality']['sharpness'] = float(laplacian_var)
        
        print(f"Sharpness score: {laplacian_var:.1f}")
        if laplacian_var < 100:
            print("⚠️  Image is blurry")
            self.diagnostics['preprocessing_recommendations'].append(
                "Use sharper image or apply sharpening filter"
            )
        else:
            print("✅ Image is sharp")
        
        # Noise level
        noise_level = self._estimate_noise()
        self.diagnostics['image_quality']['noise_level'] = float(noise_level)
        
        print(f"Noise level: {noise_level:.2f}")
        if noise_level > 10:
            print("⚠️  High noise detected")
            self.diagnostics['preprocessing_recommendations'].append("Apply denoising filter")
        else:
            print("✅ Low noise")
        
        # Skew angle
        skew_angle = self._detect_skew()
        self.diagnostics['image_quality']['skew_angle'] = float(skew_angle)
        
        print(f"Skew angle: {skew_angle:.1f}°")
        if abs(skew_angle) > 2:
            print("⚠️  Image is skewed")
            self.diagnostics['preprocessing_recommendations'].append(
                f"Rotate image by {-skew_angle:.1f}°"
            )
        else:
            print("✅ Image is properly aligned")
    
    def test_ocr_readability(self):
        """Test what OCR can read from the image"""
        print("\n" + "="*60)
        print("OCR READABILITY TEST")
        print("="*60)
        
        # Basic OCR test
        text = pytesseract.image_to_string(self.gray)
        self.diagnostics['ocr_readability']['total_characters'] = len(text)
        self.diagnostics['ocr_readability']['total_words'] = len(text.split())
        
        print(f"Total characters detected: {len(text)}")
        print(f"Total words detected: {len(text.split())}")
        
        if len(text) < 100:
            print("⚠️  Very little text detected!")
            self.diagnostics['extraction_problems'].append(
                "OCR cannot read the image properly"
            )
        
        # Check for passport elements
        import re
        
        print("\nChecking for passport elements:")
        
        # Passport number
        passport_found = False
        passport_patterns = [r'P[0-9]{8,9}', r'P\s*[0-9]{8,9}']
        
        for pattern in passport_patterns:
            match = re.search(pattern, text)
            if match:
                passport_found = True
                print(f"✅ Possible passport number found: {match.group()}")
                break
        
        if not passport_found:
            print("❌ No passport number pattern found")
            self.diagnostics['extraction_problems'].append("Passport number not readable")
        
        # Dates
        date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'
        dates = re.findall(date_pattern, text)
        
        if dates:
            print(f"✅ Dates found: {dates[:3]}")
        else:
            print("❌ No dates found")
            self.diagnostics['extraction_problems'].append("Dates not readable")
        
        # Names (uppercase words)
        uppercase_words = re.findall(r'[A-Z]{3,}', text)
        
        if uppercase_words:
            print(f"✅ Uppercase words found: {len(uppercase_words)} (potential names)")
        else:
            print("❌ No uppercase words found")
            self.diagnostics['extraction_problems'].append("Names not in readable format")
        
        # Save OCR output
        self.diagnostics['ocr_readability']['sample_text'] = text[:500]
        
        print("\nSample of extracted text (first 200 chars):")
        print("-" * 40)
        print(text[:200])
    
    def create_visualizations(self):
        """Create diagnostic visualizations"""
        print("\n" + "="*60)
        print("CREATING DIAGNOSTIC VISUALIZATIONS")
        print("="*60)
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Passport Diagnostic Analysis', fontsize=16)
        
        # 1. Original image
        axes[0, 0].imshow(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))
        axes[0, 0].set_title('Original Image')
        axes[0, 0].axis('off')
        
        # 2. Grayscale
        axes[0, 1].imshow(self.gray, cmap='gray')
        axes[0, 1].set_title('Grayscale')
        axes[0, 1].axis('off')
        
        # 3. Histogram
        axes[0, 2].hist(self.gray.ravel(), 256, [0, 256])
        axes[0, 2].set_title('Intensity Histogram')
        axes[0, 2].set_xlabel('Pixel Value')
        axes[0, 2].set_ylabel('Frequency')
        
        # 4. Edge detection
        edges = cv2.Canny(self.gray, 50, 150)
        axes[1, 0].imshow(edges, cmap='gray')
        axes[1, 0].set_title('Edge Detection')
        axes[1, 0].axis('off')
        
        # 5. Binary threshold
        _, thresh = cv2.threshold(self.gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        axes[1, 1].imshow(thresh, cmap='gray')
        axes[1, 1].set_title('Binary Threshold')
        axes[1, 1].axis('off')
        
        # 6. Text regions
        # Detect potential text regions
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(self.gray)
        
        text_regions = self.image.copy()
        for region in regions[:100]:  # Limit to first 100 regions
            hull = cv2.convexHull(region.reshape(-1, 1, 2))
            cv2.polylines(text_regions, [hull], True, (0, 255, 0), 2)
        
        axes[1, 2].imshow(cv2.cvtColor(text_regions, cv2.COLOR_BGR2RGB))
        axes[1, 2].set_title('Detected Text Regions')
        axes[1, 2].axis('off')
        
        plt.tight_layout()
        
        # Save visualization
        viz_path = os.path.join(self.output_dir, f'diagnostic_{self.timestamp}.png')
        plt.savefig(viz_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Diagnostic visualization saved: {viz_path}")
    
    def generate_recommendations(self):
        """Generate specific recommendations"""
        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        
        if not self.diagnostics['preprocessing_recommendations']:
            self.diagnostics['preprocessing_recommendations'].append("Image quality is acceptable")
        
        print("\n1. Preprocessing recommendations:")
        for i, rec in enumerate(self.diagnostics['preprocessing_recommendations'], 1):
            print(f"   {i}. {rec}")
        
        print("\n2. Extraction problems identified:")
        if self.diagnostics['extraction_problems']:
            for problem in self.diagnostics['extraction_problems']:
                print(f"   - {problem}")
        else:
            print("   - No major problems identified")
        
        print("\n3. Specific actions to improve extraction:")
        
        # Based on diagnostics, suggest specific fixes
        if self.diagnostics['image_quality']['estimated_dpi'] < 200:
            print("   📸 Take a higher resolution photo")
            print("      - Use camera's highest quality setting")
            print("      - Or scan at 300+ DPI")
        
        if self.diagnostics['image_quality']['brightness'] < 100:
            print("   💡 Improve lighting:")
            print("      - Use natural daylight")
            print("      - Avoid shadows")
            print("      - Use flash if needed")
        
        if self.diagnostics['image_quality']['sharpness'] < 100:
            print("   📷 Improve focus:")
            print("      - Hold camera steady")
            print("      - Ensure passport is flat")
            print("      - Clean camera lens")
        
        if "Passport number not readable" in self.diagnostics['extraction_problems']:
            print("   🔢 For passport number:")
            print("      - Ensure area with 'P' followed by numbers is clear")
            print("      - Check for glare on holographic elements")
            print("      - Try different angle to avoid reflections")
    
    def create_enhanced_image(self):
        """Create an enhanced version of the image"""
        print("\n" + "="*60)
        print("CREATING ENHANCED IMAGE")
        print("="*60)
        
        enhanced = self.gray.copy()
        
        # Apply recommended enhancements
        if self.diagnostics['image_quality']['brightness'] < 100:
            # Increase brightness
            enhanced = cv2.convertScaleAbs(enhanced, alpha=1.3, beta=30)
            print("✓ Applied brightness enhancement")
        
        if self.diagnostics['image_quality']['contrast'] < 30:
            # Increase contrast using CLAHE
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(enhanced)
            print("✓ Applied contrast enhancement")
        
        if self.diagnostics['image_quality']['sharpness'] < 100:
            # Sharpen
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            enhanced = cv2.filter2D(enhanced, -1, kernel)
            print("✓ Applied sharpening")
        
        if abs(self.diagnostics['image_quality']['skew_angle']) > 2:
            # Correct skew
            angle = self.diagnostics['image_quality']['skew_angle']
            (h, w) = enhanced.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, -angle, 1.0)
            enhanced = cv2.warpAffine(enhanced, M, (w, h))
            print(f"✓ Corrected skew by {-angle:.1f}°")
        
        # Save enhanced image
        enhanced_path = os.path.join(self.output_dir, f'enhanced_{self.timestamp}.jpg')
        cv2.imwrite(enhanced_path, enhanced)
        
        print(f"\nEnhanced image saved: {enhanced_path}")
        
        # Test OCR on enhanced image
        enhanced_text = pytesseract.image_to_string(enhanced)
        improvement = len(enhanced_text) - len(pytesseract.image_to_string(self.gray))
        
        print(f"OCR improvement: {improvement:+d} characters")
        
        self.diagnostics['enhanced_image_path'] = enhanced_path
        self.diagnostics['ocr_improvement'] = improvement
    
    def save_report(self):
        """Save diagnostic report"""
        report_path = os.path.join(self.output_dir, f'report_{self.timestamp}.json')
        
        with open(report_path, 'w') as f:
            json.dump(self.diagnostics, f, indent=2)
        
        print("\n" + "="*60)
        print("DIAGNOSTIC COMPLETE")
        print("="*60)
        print(f"\nFiles generated:")
        print(f"  - Diagnostic visualization: diagnostic_{self.timestamp}.png")
        print(f"  - Enhanced image: enhanced_{self.timestamp}.jpg")
        print(f"  - Full report: report_{self.timestamp}.json")
        print(f"\nAll files saved in: {self.output_dir}")
    
    def _estimate_noise(self):
        """Estimate image noise level"""
        denoised = cv2.bilateralFilter(self.gray, 9, 75, 75)
        noise = np.abs(self.gray.astype(float) - denoised.astype(float))
        return np.mean(noise)
    
    def _detect_skew(self):
        """Detect image skew angle"""
        edges = cv2.Canny(self.gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is not None:
            angles = []
            for rho, theta in lines[:, 0]:
                angle = theta * 180 / np.pi - 90
                if -45 < angle < 45:
                    angles.append(angle)
            
            if angles:
                return np.median(angles)
        return 0.0

def main():
    parser = argparse.ArgumentParser(description='Diagnose passport image problems')
    parser.add_argument('image_path', help='Path to passport image')
    parser.add_argument('--output', default='output/diagnostics', help='Output directory')
    
    args = parser.parse_args()
    
    try:
        diagnostic = PassportDiagnostic(args.image_path, args.output)
        diagnostic.run_full_diagnostic()
        
        print("\n💡 Next steps:")
        print("1. Try the enhanced image with the extractor")
        print("2. Follow the recommendations above")
        print("3. If still having issues, try different lighting/angle")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())