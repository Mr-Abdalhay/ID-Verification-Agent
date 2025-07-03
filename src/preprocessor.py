"""
Image Preprocessor
Advanced image preprocessing for optimal OCR results
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
import logging
import pytesseract
import platform

# Configure Tesseract path for Windows
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ImagePreprocessor:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def process(self, image_bytes: bytes) -> dict:
        """
        Process image bytes and return multiple preprocessed variants
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary of preprocessed image variants
        """
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if original is None:
            raise ValueError("Failed to decode image")
        
        # Auto-rotate if needed
        if self.config.get('auto_rotate', True):
            original = self._auto_rotate(original)
        
        # Generate multiple preprocessing variants
        variants = {}
        
        # 1. Basic grayscale
        gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        variants['grayscale'] = gray
        
        # 2. Upscaled version
        if self.config.get('upscale', True):
            upscaled = self._upscale(original)
            variants['upscaled'] = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
        
        # 3. Enhanced contrast (CLAHE)
        variants['clahe'] = self._apply_clahe(gray)
        
        # 4. Denoised
        if self.config.get('denoise', True):
            variants['denoised'] = self._denoise(gray)
        
        # 5. Binary threshold
        variants['otsu'] = self._otsu_threshold(gray)
        
        # 6. Adaptive threshold
        variants['adaptive'] = self._adaptive_threshold(gray)
        
        # 7. Sharpened
        variants['sharpened'] = self._sharpen(gray)
        
        # 8. Combined enhancement
        variants['ultra_enhanced'] = self._ultra_enhance(original)
        
        # 9. Edge preserved
        variants['edge_preserved'] = self._edge_preserve(original)
        
        # 10. Morphological processing
        variants['morphological'] = self._morphological(gray)
        
        return variants
    
    def _auto_rotate(self, image: np.ndarray) -> np.ndarray:
        """Detect and correct image rotation"""
        try:
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
                        self.logger.info(f"Auto-rotated image by {median_angle:.1f} degrees")
                        return rotated
        except Exception as e:
            self.logger.warning(f"Auto-rotation failed: {str(e)}")
        
        return image
    
    def _upscale(self, image: np.ndarray) -> np.ndarray:
        """Upscale image for better OCR"""
        scale_factor = self.config.get('upscale_factor', 2)
        width = int(image.shape[1] * scale_factor)
        height = int(image.shape[0] * scale_factor)
        
        # Use INTER_CUBIC for upscaling
        upscaled = cv2.resize(image, (width, height), interpolation=cv2.INTER_CUBIC)
        
        return upscaled
    
    def _apply_clahe(self, gray: np.ndarray) -> np.ndarray:
        """Apply CLAHE for contrast enhancement"""
        clahe = cv2.createCLAHE(
            clipLimit=self.config.get('clahe_clip_limit', 3.0),
            tileGridSize=(8, 8)
        )
        return clahe.apply(gray)
    
    def _denoise(self, gray: np.ndarray) -> np.ndarray:
        """Apply denoising"""
        # Try multiple denoising methods
        try:
            # Non-local means denoising
            denoised = cv2.fastNlMeansDenoising(gray, h=30)
        except:
            # Fallback to bilateral filter
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        return denoised
    
    def _otsu_threshold(self, gray: np.ndarray) -> np.ndarray:
        """Apply Otsu's thresholding"""
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    def _adaptive_threshold(self, gray: np.ndarray) -> np.ndarray:
        """Apply adaptive thresholding"""
        adaptive = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        return adaptive
    
    def _sharpen(self, gray: np.ndarray) -> np.ndarray:
        """Apply sharpening filter"""
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        return sharpened
    
    def _ultra_enhance(self, image: np.ndarray) -> np.ndarray:
        """Apply combined ultra enhancement"""
        # Convert to PIL for some operations
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Auto-contrast
        pil_image = ImageOps.autocontrast(pil_image, cutoff=1)
        
        # Enhance sharpness
        sharpener = ImageEnhance.Sharpness(pil_image)
        pil_image = sharpener.enhance(2.0)
        
        # Enhance contrast
        contrast = ImageEnhance.Contrast(pil_image)
        pil_image = contrast.enhance(1.5)
        
        # Convert back to OpenCV
        enhanced = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Apply bilateral filter
        enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # Convert to grayscale
        gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        final = clahe.apply(gray)
        
        return final
    
    def _edge_preserve(self, image: np.ndarray) -> np.ndarray:
        """Apply edge-preserving filter"""
        edge_preserved = cv2.edgePreservingFilter(
            image,
            flags=2,
            sigma_s=50,
            sigma_r=0.4
        )
        return cv2.cvtColor(edge_preserved, cv2.COLOR_BGR2GRAY)
    
    def _morphological(self, gray: np.ndarray) -> np.ndarray:
        """Apply morphological operations"""
        # Morphological closing to connect broken text
        kernel = np.ones((2, 2), np.uint8)
        closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Then apply threshold
        _, binary = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary