#!/usr/bin/env python3
"""
Passport Image Enhancement Tool
Preprocesses passport images for optimal OCR extraction
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
import os
import sys
import argparse
from datetime import datetime

class ImageEnhancer:
    def __init__(self, output_dir="output/enhanced"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def enhance_passport(self, input_path: str, output_path: str = None) -> str:
        """
        Apply multiple enhancement techniques to improve passport readability
        
        Args:
            input_path: Path to input image
            output_path: Optional output path
            
        Returns:
            Path to enhanced image
        """
        print("\n" + "="*50)
        print("PASSPORT IMAGE ENHANCEMENT")
        print("="*50)
        print(f"Input: {input_path}")
        
        # Load image
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError(f"Cannot load image from {input_path}")
        
        # Generate output path if not specified
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(self.output_dir, f"{base_name}_enhanced_{timestamp}.jpg")
        
        print(f"Output: {output_path}")
        print("\nApplying enhancements...")
        
        # 1. Check and resize if needed
        height, width = image.shape[:2]
        if width < 1000:
            scale = 1500 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            print(f"✓ Upscaled to {new_width}x{new_height}")
        
        # 2. Convert to PIL for some operations
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # 3. Auto-contrast
        pil_image = ImageOps.autocontrast(pil_image, cutoff=1)
        print("✓ Applied auto-contrast")
        
        # 4. Enhance sharpness
        sharpener = ImageEnhance.Sharpness(pil_image)
        pil_image = sharpener.enhance(2.0)
        print("✓ Enhanced sharpness")
        
        # 5. Enhance contrast
        contrast = ImageEnhance.Contrast(pil_image)
        pil_image = contrast.enhance(1.5)
        print("✓ Enhanced contrast")
        
        # Convert back to OpenCV
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # 6. Denoise
        image = cv2.bilateralFilter(image, 9, 75, 75)
        print("✓ Applied denoising")
        
        # 7. Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 8. CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        print("✓ Applied CLAHE")
        
        # Save main enhanced version
        cv2.imwrite(output_path, gray)
        
        # 9. Create additional versions
        base, ext = os.path.splitext(output_path)
        
        # Binary threshold version
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_path = f"{base}_otsu{ext}"
        cv2.imwrite(otsu_path, otsu)
        
        # Adaptive threshold version
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        adaptive_path = f"{base}_adaptive{ext}"
        cv2.imwrite(adaptive_path, adaptive)
        
        print("\nEnhancement complete!")
        print(f"Generated files:")
        print(f"  - {output_path} (enhanced grayscale)")
        print(f"  - {otsu_path} (binary threshold)")
        print(f"  - {adaptive_path} (adaptive threshold)")
        
        return output_path
    
    def batch_enhance(self, folder_path: str):
        """Enhance all passport images in a folder"""
        print("\n" + "="*50)
        print("BATCH PASSPORT ENHANCEMENT")
        print("="*50)
        print(f"Folder: {folder_path}")
        
        # Find all image files
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
        results = []
        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] Processing {os.path.basename(image_path)}")
            print("-" * 40)
            
            try:
                enhanced_path = self.enhance_passport(image_path)
                results.append({
                    'original': image_path,
                    'enhanced': enhanced_path,
                    'success': True
                })
            except Exception as e:
                print(f"Error: {str(e)}")
                results.append({
                    'original': image_path,
                    'error': str(e),
                    'success': False
                })
        
        # Summary
        print("\n" + "="*50)
        print("BATCH ENHANCEMENT COMPLETE")
        print("="*50)
        
        successful = sum(1 for r in results if r['success'])
        print(f"Successfully enhanced: {successful}/{len(results)}")
        print(f"Enhanced images saved in: {self.output_dir}")
        
        return results
    
    def auto_rotate(self, image: np.ndarray) -> np.ndarray:
        """Detect and correct image rotation"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is not None:
            angles = []
            for rho, theta in lines[:, 0]:
                angle = theta * 180 / np.pi - 90
                if -45 < angle < 45:
                    angles.append(angle)
            
            if angles:
                median_angle = np.median(angles)
                
                # Rotate if needed
                if abs(median_angle) > 0.5:
                    (h, w) = image.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    rotated = cv2.warpAffine(image, M, (w, h),
                                           flags=cv2.INTER_CUBIC,
                                           borderMode=cv2.BORDER_REPLICATE)
                    print(f"✓ Auto-rotated by {median_angle:.1f}°")
                    return rotated
        
        return image

def main():
    parser = argparse.ArgumentParser(description='Enhance passport images for better OCR')
    parser.add_argument('input_path', help='Path to image or folder')
    parser.add_argument('--output', help='Output path (optional)')
    parser.add_argument('--batch', action='store_true', help='Batch process folder')
    
    args = parser.parse_args()
    
    enhancer = ImageEnhancer()
    
    try:
        if args.batch or os.path.isdir(args.input_path):
            # Batch processing
            enhancer.batch_enhance(args.input_path)
        else:
            # Single image
            enhancer.enhance_passport(args.input_path, args.output)
            
            print("\n💡 Next steps:")
            print("1. Test the enhanced image with the extractor")
            print("2. Try different versions (otsu, adaptive) if needed")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())