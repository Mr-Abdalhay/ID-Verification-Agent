"""
Ultra Enhanced Passport Extractor
Core extraction logic with multi-pass OCR and smart pattern matching
"""

import cv2
import numpy as np
import pytesseract
import re
import logging
from typing import Dict, List, Tuple, Optional
from patterns import PassportPatterns

class UltraPassportExtractor:
    def __init__(self, config):
        self.config = config
        self.patterns = PassportPatterns()
        self.logger = logging.getLogger(__name__)
        
    def extract(self, preprocessed_images: Dict[str, np.ndarray]) -> Dict:
        """
        Extract passport data from preprocessed images
        
        Args:
            preprocessed_images: Dictionary of preprocessed image variants
            
        Returns:
            Dictionary containing extracted data and metadata
        """
        all_extracted_texts = []
        
        # Multi-pass extraction on each preprocessed variant
        for preprocess_name, image in preprocessed_images.items():
            texts = self._multi_pass_extraction(image)
            
            # Add preprocessing method to source
            for ocr_method, text in texts:
                source_name = f"{preprocess_name}_{ocr_method}"
                all_extracted_texts.append((source_name, text))
        
        # Extract fields from all collected texts
        extracted_data = self._smart_field_extraction(all_extracted_texts)
        
        # Calculate extraction score
        extracted_data['extraction_score'] = self._calculate_score(extracted_data)
        extracted_data['extraction_summary'] = self._generate_summary(extracted_data)
        
        return extracted_data
    
    def _multi_pass_extraction(self, image: np.ndarray) -> List[Tuple[str, str]]:
        """
        Multiple extraction passes with different OCR configurations
        """
        results = []
        
        # OCR configurations to try
        configs = [
            ('standard', '--oem 3 --psm 3'),
            ('single_column', '--oem 3 --psm 4'),
            ('uniform_block', '--oem 3 --psm 6'),
            ('single_line', '--oem 3 --psm 7'),
            ('sparse_text', '--oem 3 --psm 11'),
        ]
        
        for name, config in configs:
            try:
                text = pytesseract.image_to_string(image, config=config)
                if text.strip():
                    results.append((name, text))
            except Exception as e:
                self.logger.debug(f"OCR config {name} failed: {str(e)}")
        
        # Try with different languages
        for lang in ['eng', 'ara']:
            try:
                text = pytesseract.image_to_string(image, lang=lang)
                if text.strip():
                    results.append((f'{lang}_lang', text))
            except:
                pass
        
        # High confidence text extraction
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            high_conf_text = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > self.config.get('confidence_threshold', 60):
                    if data['text'][i].strip():
                        high_conf_text.append(data['text'][i])
            
            # print(f"The extract data is: {data}")
            if high_conf_text:
                results.append(('high_confidence', ' '.join(high_conf_text)))
        except:
            pass
        
        # Region-based extraction
        region_results = self._extract_from_regions(image)
        results.extend(region_results)
        
        return results
    
    def _extract_from_regions(self, image: np.ndarray) -> List[Tuple[str, str]]:
        """
        Extract text from specific passport regions
        """
        height, width = image.shape[:2]
        results = []
        
        # Define regions based on typical passport layout
        regions = {
            'top_right': (int(width * 0.4), 0, width, int(height * 0.4)),
            'center': (0, int(height * 0.2), width, int(height * 0.8)),
            'bottom': (0, int(height * 0.6), width, height),
        }
        
        for region_name, (x1, y1, x2, y2) in regions.items():
            roi = image[y1:y2, x1:x2]
            
            try:
                text = pytesseract.image_to_string(roi, config='--oem 3 --psm 6')
                if text.strip():
                    results.append((f'region_{region_name}', text))
            except:
                pass
        
        return results
    
    def _smart_field_extraction(self, all_texts: List[Tuple[str, str]]) -> Dict:
        """
        Extract fields using smart pattern matching and validation
        """
        data = {
            'passport_type': None,
            'country_code': None,
            'passport_number': None,
            'full_name': None,
            'nationality': None,
            'place_of_birth': None,
            'sex': None,
            'date_of_birth': None,
            'date_of_issue': None,
            'date_of_expiry': None,
            'national_id': None,
            'confidence_scores': {},
            'extraction_method': {}
        }
        
        # Combine all texts for comprehensive search
        combined_text = '\n'.join([text for _, text in all_texts])
        
        # Extract passport number
        data = self._extract_passport_number(data, all_texts)
        
        # Extract national ID
        data = self._extract_national_id(data, combined_text)
        
        # Extract dates
        data = self._extract_dates(data, combined_text)
        
        # Extract name
        data = self._extract_name(data, all_texts)
        
        # Extract sex/gender
        data = self._extract_sex(data, combined_text)
        
        # Extract place of birth
        data = self._extract_place_of_birth(data, combined_text)
        
        # Extract nationality and country
        data = self._extract_nationality(data, combined_text)
        
        return data
    
    def _extract_passport_number(self, data: Dict, all_texts: List[Tuple[str, str]]) -> Dict:
        """Extract and validate passport number"""
        for source_name, text in all_texts:
            for pattern in self.patterns.passport_number:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    candidate = match.group(1) if match.groups() else match.group(0)
                    
                    # Clean common OCR errors
                    candidate = candidate.replace('O', '0').replace(' ', '').upper()
                    
                    # Validate format
                    if re.match(r'^P[0-9]{8,9}$', candidate):
                        data['passport_number'] = candidate
                        data['extraction_method']['passport_number'] = source_name
                        data['confidence_scores']['passport_number'] = 0.95
                        return data
        
        return data
    
    def _extract_national_id(self, data: Dict, text: str) -> Dict:
        """Extract and validate national ID"""
        for pattern in self.patterns.national_id:
            matches = re.finditer(pattern, text)
            
            for match in matches:
                candidate = match.group(1) if match.groups() else match.group(0)
                
                # Clean and format
                candidate = re.sub(r'[\s\.]', '-', candidate)
                
                # Validate format
                if re.match(r'^\d{3}-\d{4}-\d{4,5}$', candidate):
                    data['national_id'] = candidate
                    data['confidence_scores']['national_id'] = 0.9
                    return data
        
        return data
    
    def _extract_dates(self, data: Dict, text: str) -> Dict:
        """Extract and validate dates"""
        all_dates = []
        
        for pattern in self.patterns.date:
            dates = re.findall(pattern, text)
            all_dates.extend(dates)
        
        # Clean and validate dates
        valid_dates = []
        for date in all_dates:
            # Normalize format
            date = re.sub(r'[\s\.]+', '-', date)
            date = re.sub(r'/+', '-', date)
            
            # Validate components
            parts = date.split('-')
            if len(parts) == 3:
                try:
                    day = int(parts[0])
                    month = int(parts[1])
                    year = int(parts[2])
                    
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                        valid_dates.append(f"{day:02d}-{month:02d}-{year}")
                except:
                    continue
        
        # Remove duplicates and sort
        valid_dates = sorted(list(set(valid_dates)), 
                           key=lambda x: (int(x.split('-')[2]), 
                                        int(x.split('-')[1]), 
                                        int(x.split('-')[0])))
        
        # Assign dates logically
        if len(valid_dates) >= 1:
            data['date_of_birth'] = valid_dates[0]
            data['confidence_scores']['date_of_birth'] = 0.85
        
        if len(valid_dates) >= 2:
            data['date_of_issue'] = valid_dates[-2] if len(valid_dates) >= 3 else valid_dates[1]
            data['confidence_scores']['date_of_issue'] = 0.8
        
        if len(valid_dates) >= 3:
            data['date_of_expiry'] = valid_dates[-1]
            data['confidence_scores']['date_of_expiry'] = 0.85
        
        return data
    
    def _extract_name(self, data: Dict, all_texts: List[Tuple[str, str]]) -> Dict:
        """Extract and validate name"""
        name_candidates = []
        
        for source_name, text in all_texts:
            for pattern in self.patterns.name:
                matches = re.findall(pattern, text)
                
                for match in matches:
                    if isinstance(match, tuple):
                        match = ' '.join(match)
                    
                    name = match.strip()
                    
                    # Filter out non-name words
                    if not any(word in name for word in self.patterns.non_name_words):
                        if 10 <= len(name) <= 60:
                            name_candidates.append((name, source_name))
        
        # Select best candidate
        if name_candidates:
            # Prefer certain extraction methods
            preferred_sources = ['uniform_block', 'high_confidence', 'single_column']
            
            for source in preferred_sources:
                for name, name_source in name_candidates:
                    if source in name_source:
                        data['full_name'] = name
                        data['extraction_method']['full_name'] = name_source
                        data['confidence_scores']['full_name'] = 0.85
                        return data
            
            # Otherwise take longest name
            if name_candidates:
                longest = max(name_candidates, key=lambda x: len(x[0]))
                data['full_name'] = longest[0]
                data['extraction_method']['full_name'] = longest[1]
                data['confidence_scores']['full_name'] = 0.75
        
        return data
    
    def _extract_sex(self, data: Dict, text: str) -> Dict:
        """Extract sex/gender"""
        for pattern in self.patterns.sex:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                data['sex'] = value[0].upper() if value else None
                data['confidence_scores']['sex'] = 0.95
                return data
        
        return data
    
    def _extract_place_of_birth(self, data: Dict, text: str) -> Dict:
        """Extract place of birth"""
        text_upper = text.upper()
        
        for place in self.patterns.sudan_places:
            if place in text_upper:
                data['place_of_birth'] = place
                data['confidence_scores']['place_of_birth'] = 0.85
                return data
        
        return data
    
    def _extract_nationality(self, data: Dict, text: str) -> Dict:
        """Extract nationality and country code"""
        text_upper = text.upper()
        
        if any(indicator in text_upper for indicator in self.patterns.sudan_indicators):
            data['nationality'] = 'SUDANESE'
            data['country_code'] = 'SDN'
            data['passport_type'] = 'PC'
            data['confidence_scores']['nationality'] = 0.95
        
        return data
    
    def _calculate_score(self, data: Dict) -> float:
        """Calculate overall extraction score"""
        important_fields = [
            'passport_number', 'full_name', 'nationality', 'date_of_birth',
            'date_of_issue', 'date_of_expiry', 'national_id', 'sex'
        ]
        
        extracted = sum(1 for field in important_fields if data.get(field))
        return (extracted / len(important_fields)) * 100
    
    def _generate_summary(self, data: Dict) -> str:
        """Generate extraction summary"""
        fields = ['passport_number', 'full_name', 'nationality', 'national_id',
                 'date_of_birth', 'date_of_issue', 'date_of_expiry', 'sex',
                 'place_of_birth', 'country_code']
        
        extracted = sum(1 for field in fields if data.get(field))
        return f"{extracted}/{len(fields)} fields extracted"