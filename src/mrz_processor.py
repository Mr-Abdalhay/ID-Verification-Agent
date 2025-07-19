"""
Enhanced MRZ Processor using FastMRZ
Integrates FastMRZ for better Machine Readable Zone processing
"""

import cv2
import numpy as np
import logging
from typing import Dict, Optional, Tuple, List
import re

try:
    import fastmrz
    FASTMRZ_AVAILABLE = True
except ImportError:
    FASTMRZ_AVAILABLE = False
    fastmrz = None

class EnhancedMRZProcessor:
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        if not FASTMRZ_AVAILABLE:
            self.logger.warning("FastMRZ is not available. Using fallback MRZ processing.")
    
    def extract_mrz_data(self, image: np.ndarray) -> Dict:
        """
        Extract MRZ data using FastMRZ and fallback methods
        
        Args:
            image: Input passport image as numpy array
            
        Returns:
            Dictionary containing extracted MRZ data
        """
        mrz_data = {
            'mrz_text': None,
            'passport_number': None,
            'nationality': None,
            'date_of_birth': None,
            'date_of_expiry': None,
            'sex': None,
            'names': None,
            'document_type': None,
            'issuing_country': None,
            'mrz_confidence': 0.0,
            'extraction_method': 'none'
        }
        
        # Try FastMRZ first
        if FASTMRZ_AVAILABLE:
            mrz_data = self._extract_with_fastmrz(image, mrz_data)
        
        # If FastMRZ didn't find anything, try fallback
        if not mrz_data['mrz_text']:
            mrz_data = self._extract_with_fallback(image, mrz_data)
        
        return mrz_data
    
    def _extract_with_fastmrz(self, image: np.ndarray, mrz_data: Dict) -> Dict:
        """
        Extract MRZ using FastMRZ library
        """
        try:
            # FastMRZ expects BGR format (OpenCV default)
            if len(image.shape) == 3 and image.shape[2] == 3:
                # Ensure BGR format
                if image.dtype != np.uint8:
                    image = (image * 255).astype(np.uint8)
            
            # Try to extract MRZ
            mrz_result = fastmrz.FastMRZ.process_image(image)
            
            if mrz_result and hasattr(mrz_result, 'mrz_text') and mrz_result.mrz_text:
                self.logger.info("FastMRZ successfully extracted MRZ data")
                
                # Parse FastMRZ results
                mrz_data['mrz_text'] = mrz_result.mrz_text
                mrz_data['extraction_method'] = 'fastmrz'
                
                # Extract individual fields from FastMRZ result
                if hasattr(mrz_result, 'document_number'):
                    mrz_data['passport_number'] = mrz_result.document_number
                
                if hasattr(mrz_result, 'nationality'):
                    mrz_data['nationality'] = mrz_result.nationality
                
                if hasattr(mrz_result, 'date_of_birth'):
                    mrz_data['date_of_birth'] = self._format_date(mrz_result.date_of_birth)
                
                if hasattr(mrz_result, 'date_of_expiry'):
                    mrz_data['date_of_expiry'] = self._format_date(mrz_result.date_of_expiry)
                
                if hasattr(mrz_result, 'sex'):
                    mrz_data['sex'] = mrz_result.sex
                
                if hasattr(mrz_result, 'names'):
                    mrz_data['names'] = mrz_result.names
                elif hasattr(mrz_result, 'surname') and hasattr(mrz_result, 'given_names'):
                    mrz_data['names'] = f"{mrz_result.given_names} {mrz_result.surname}".strip()
                
                if hasattr(mrz_result, 'document_type'):
                    mrz_data['document_type'] = mrz_result.document_type
                
                if hasattr(mrz_result, 'issuing_country'):
                    mrz_data['issuing_country'] = mrz_result.issuing_country
                
                # Calculate confidence based on field completeness
                mrz_data['mrz_confidence'] = self._calculate_mrz_confidence(mrz_data)
                
        except Exception as e:
            self.logger.error(f"FastMRZ extraction failed: {str(e)}")
            mrz_data['extraction_method'] = 'fastmrz_failed'
        
        return mrz_data
    
    def _extract_with_fallback(self, image: np.ndarray, mrz_data: Dict) -> Dict:
        """
        Fallback MRZ extraction using traditional OCR methods
        """
        try:
            # Preprocess image for MRZ region detection
            mrz_region = self._find_mrz_region(image)
            
            if mrz_region is not None:
                # Extract text from MRZ region
                mrz_text = self._extract_mrz_text(mrz_region)
                
                if mrz_text:
                    mrz_data['mrz_text'] = mrz_text
                    mrz_data['extraction_method'] = 'fallback_ocr'
                    
                    # Parse MRZ text manually
                    parsed_data = self._parse_mrz_text(mrz_text)
                    mrz_data.update(parsed_data)
                    
                    mrz_data['mrz_confidence'] = self._calculate_mrz_confidence(mrz_data)
                    
                    self.logger.info("Fallback MRZ extraction completed")
        
        except Exception as e:
            self.logger.error(f"Fallback MRZ extraction failed: {str(e)}")
            mrz_data['extraction_method'] = 'fallback_failed'
        
        return mrz_data
    
    def _find_mrz_region(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Find MRZ region in the passport image
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # MRZ is typically in the bottom 30% of the passport
            height, width = gray.shape
            mrz_y_start = int(height * 0.7)
            mrz_region = gray[mrz_y_start:, :]
            
            # Apply morphological operations to enhance text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 2))
            morphed = cv2.morphologyEx(mrz_region, cv2.MORPH_CLOSE, kernel)
            
            # Find contours that might be MRZ lines
            contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size and aspect ratio
            text_contours = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                if w > width * 0.3 and aspect_ratio > 5:  # Long horizontal lines
                    text_contours.append((x, y, w, h))
            
            if text_contours:
                # Get bounding box of all text regions
                min_x = min(cont[0] for cont in text_contours)
                min_y = min(cont[1] for cont in text_contours)
                max_x = max(cont[0] + cont[2] for cont in text_contours)
                max_y = max(cont[1] + cont[3] for cont in text_contours)
                
                # Extract the MRZ region with some padding
                padding = 10
                mrz_extracted = mrz_region[
                    max(0, min_y - padding):min(mrz_region.shape[0], max_y + padding),
                    max(0, min_x - padding):min(mrz_region.shape[1], max_x + padding)
                ]
                
                return mrz_extracted
            
        except Exception as e:
            self.logger.error(f"MRZ region detection failed: {str(e)}")
        
        return None
    
    def _extract_mrz_text(self, mrz_region: np.ndarray) -> Optional[str]:
        """
        Extract text from MRZ region using OCR
        """
        try:
            import pytesseract
            
            # Enhance image for OCR
            enhanced = cv2.resize(mrz_region, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            
            # Apply threshold
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR configuration for MRZ (monospace font)
            config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<'
            
            text = pytesseract.image_to_string(thresh, config=config)
            
            # Clean and validate MRZ text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # MRZ should have 2-3 lines of specific length
            valid_lines = []
            for line in lines:
                if len(line) >= 30:  # Minimum MRZ line length
                    valid_lines.append(line)
            
            if valid_lines:
                return '\n'.join(valid_lines)
                
        except Exception as e:
            self.logger.error(f"MRZ text extraction failed: {str(e)}")
        
        return None
    
    def _parse_mrz_text(self, mrz_text: str) -> Dict:
        """
        Parse MRZ text to extract individual fields
        """
        parsed = {}
        
        try:
            lines = mrz_text.split('\n')
            
            if len(lines) >= 2:
                # First line: P<COUNTRY<SURNAME<<GIVEN_NAMES<<<<<
                line1 = lines[0]
                if line1.startswith('P<'):
                    # Extract country code
                    country_match = re.match(r'P<([A-Z]{3})', line1)
                    if country_match:
                        parsed['issuing_country'] = country_match.group(1)
                    
                    # Extract names
                    name_part = line1[5:]  # Skip 'P<XXX'
                    name_parts = name_part.split('<<')
                    if len(name_parts) >= 2:
                        surname = name_parts[0].replace('<', ' ').strip()
                        given_names = name_parts[1].replace('<', ' ').strip()
                        parsed['names'] = f"{given_names} {surname}".strip()
                
                # Second line: Document number + check + country + birth + check + sex + expiry + check + personal + check + final
                line2 = lines[1]
                if len(line2) >= 44:
                    # Extract passport number (first 9 characters)
                    doc_num = line2[:9].replace('<', '')
                    if doc_num:
                        parsed['passport_number'] = doc_num
                    
                    # Extract birth date (positions 13-18)
                    birth_date = line2[13:19]
                    if birth_date and birth_date != '<<<<<<':
                        parsed['date_of_birth'] = self._format_date(birth_date)
                    
                    # Extract sex (position 20)
                    sex = line2[20]
                    if sex in ['M', 'F']:
                        parsed['sex'] = sex
                    
                    # Extract expiry date (positions 21-26)
                    expiry_date = line2[21:27]
                    if expiry_date and expiry_date != '<<<<<<':
                        parsed['date_of_expiry'] = self._format_date(expiry_date)
        
        except Exception as e:
            self.logger.error(f"MRZ parsing failed: {str(e)}")
        
        return parsed
    
    def _format_date(self, date_str: str) -> Optional[str]:
        """
        Format date from MRZ format (YYMMDD) to DD-MM-YYYY
        """
        try:
            if not date_str or len(date_str) != 6:
                return None
            
            yy = int(date_str[:2])
            mm = int(date_str[2:4])
            dd = int(date_str[4:6])
            
            # Handle year conversion (assuming 21st century for years < 30, 20th century for >= 30)
            if yy < 30:
                yyyy = 2000 + yy
            else:
                yyyy = 1900 + yy
            
            # Validate date components
            if 1 <= mm <= 12 and 1 <= dd <= 31:
                return f"{dd:02d}-{mm:02d}-{yyyy}"
        
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _calculate_mrz_confidence(self, mrz_data: Dict) -> float:
        """
        Calculate confidence score based on extracted MRZ fields
        """
        fields = ['passport_number', 'nationality', 'date_of_birth', 'date_of_expiry', 'sex', 'names']
        filled_fields = sum(1 for field in fields if mrz_data.get(field))
        
        base_confidence = filled_fields / len(fields)
        
        # Bonus for having MRZ text
        if mrz_data.get('mrz_text'):
            base_confidence += 0.2
        
        # Bonus for FastMRZ extraction
        if mrz_data.get('extraction_method') == 'fastmrz':
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def enhance_extraction_with_mrz(self, extracted_data: Dict, mrz_data: Dict) -> Dict:
        """
        Enhance existing extraction data with MRZ data
        """
        enhanced_data = extracted_data.copy()
        
        # Mapping between MRZ fields and extraction fields
        field_mapping = {
            'passport_number': 'passport_number',
            'nationality': 'nationality',
            'date_of_birth': 'date_of_birth',
            'date_of_expiry': 'date_of_expiry',
            'sex': 'sex',
            'names': 'full_name',
            'issuing_country': 'country_code'
        }
        
        for mrz_field, extract_field in field_mapping.items():
            mrz_value = mrz_data.get(mrz_field)
            
            if mrz_value:
                # If extraction field is empty or has low confidence, use MRZ data
                current_value = enhanced_data.get(extract_field)
                current_confidence = enhanced_data.get('confidence_scores', {}).get(extract_field, 0.0)
                mrz_confidence = mrz_data.get('mrz_confidence', 0.8)
                
                if not current_value or mrz_confidence > current_confidence:
                    enhanced_data[extract_field] = mrz_value
                    
                    # Update confidence scores
                    if 'confidence_scores' not in enhanced_data:
                        enhanced_data['confidence_scores'] = {}
                    enhanced_data['confidence_scores'][extract_field] = mrz_confidence
                    
                    # Update extraction method
                    if 'extraction_method' not in enhanced_data:
                        enhanced_data['extraction_method'] = {}
                    enhanced_data['extraction_method'][extract_field] = mrz_data.get('extraction_method', 'mrz')
        
        # Add MRZ-specific data
        enhanced_data['mrz_text'] = mrz_data.get('mrz_text')
        enhanced_data['mrz_confidence'] = mrz_data.get('mrz_confidence', 0.0)
        enhanced_data['mrz_extraction_method'] = mrz_data.get('extraction_method', 'none')
        
        return enhanced_data
