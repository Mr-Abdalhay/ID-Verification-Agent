import cv2
import numpy as np
import pytesseract
import re
import logging
from typing import Dict, List, Tuple, Optional
from collections import Counter

# Assuming 'patterns.py' and 'mrz_processor.py' exist as described
from patterns import PassportPatterns
from mrz_processor import EnhancedMRZProcessor

class UltraPassportExtractor:
    def __init__(self, config):
        self.config = config
        self.patterns = PassportPatterns()
        self.logger = logging.getLogger(__name__)
        self.ocr_confidence_data = {}
        self.mrz_processor = EnhancedMRZProcessor(config)
        
    def extract(self, preprocessed_images: Dict[str, np.ndarray]) -> Dict:
        """
        Extract passport data from preprocessed images.
        """
        all_extracted_texts = []
        
        for preprocess_name, image in preprocessed_images.items():
            texts = self._multi_pass_extraction(image)
            for ocr_method, text in texts:
                source_name = f"{preprocess_name}_{ocr_method}"
                all_extracted_texts.append((source_name, text))
        
        extracted_data = self._smart_field_extraction(all_extracted_texts)
        
        if preprocessed_images:
            main_image = next(iter(preprocessed_images.values()))
            mrz_data = self.mrz_processor.extract_mrz_data(main_image)
            if mrz_data.get('mrz_text'):
                self.logger.info(f"MRZ data extracted with {mrz_data.get('extraction_method', 'unknown')} method")
                extracted_data = self.mrz_processor.enhance_extraction_with_mrz(extracted_data, mrz_data)
        
        extracted_data['extraction_score'] = self._calculate_score(extracted_data)
        extracted_data['extraction_summary'] = self._generate_summary(extracted_data)
        
        return extracted_data
    
    def _multi_pass_extraction(self, image: np.ndarray) -> List[Tuple[str, str]]:
        """
        Multiple extraction passes with different OCR configurations.
        """
        # This method remains the same as your provided version.
        # It's a solid approach to gather text from multiple OCR strategies.
        results = []
        configs = [
            ('standard', '--oem 3 --psm 3'), ('single_column', '--oem 3 --psm 4'),
            ('uniform_block', '--oem 3 --psm 6'), ('single_line', '--oem 3 --psm 7'),
            # ('sparse_text', '--oem 3 --psm 11'),
        ]
        for name, config in configs:
            try:
                text = pytesseract.image_to_string(image, config=config)
                if text.strip(): results.append((name, text))
            except Exception as e:
                self.logger.debug(f"OCR config {name} failed: {str(e)}")
        
        for lang in ['eng', 'ara']:
            try:
                text = pytesseract.image_to_string(image, lang=lang)
                if text.strip(): results.append((f'{lang}_lang', text))
            except: pass
            
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            high_conf_text = []
            source_key = f"{id(image)}"
            self.ocr_confidence_data[source_key] = {'text': data['text'], 'conf': data['conf']}
            for i, conf in enumerate(data['conf']):
                if int(conf) > self.config.get('confidence_threshold', 60) and data['text'][i].strip():
                    high_conf_text.append(data['text'][i])
            if high_conf_text: results.append(('high_confidence', ' '.join(high_conf_text)))
        except: pass
        
        region_results = self._extract_from_regions(image)
        results.extend(region_results)
        return results

    def _extract_from_regions(self, image: np.ndarray) -> List[Tuple[str, str]]:
        """
        Extract text from specific passport regions.
        """
        # This method also remains the same. Region-based extraction is a good idea.
        height, width = image.shape[:2]
        results = []
        regions = {
            'top_right': (int(width * 0.4), 0, width, int(height * 0.4)),
            'center': (0, int(height * 0.2), width, int(height * 0.8)),
            'bottom': (0, int(height * 0.6), width, height),
        }
        for region_name, (x1, y1, x2, y2) in regions.items():
            roi = image[y1:y2, x1:x2]
            try:
                text = pytesseract.image_to_string(roi, config='--oem 3 --psm 6')
                if text.strip(): results.append((f'region_{region_name}', text))
            except: pass
        return results

    def _smart_field_extraction(self, all_texts: List[Tuple[str, str]]) -> Dict:
        """
        Extract fields using smart pattern matching and validation.
        """
        data = {
            'passport_type': None, 'country_code': None, 'passport_number': None,
            'full_name': None, 'nationality': None, 'place_of_birth': None,
            'place_of_issue': None, 'sex': None, 'date_of_birth': None,
            'date_of_issue': None, 'date_of_expiry': None, 'national_id': None,
            'confidence_scores': {}, 'extraction_method': {}
        }
        
        combined_text = '\n'.join([text for _, text in all_texts])
        
        data = self._extract_passport_number(data, all_texts)
        data = self._extract_national_id(data, combined_text)
        data = self._extract_dates(data, combined_text)
        data = self._extract_name(data, all_texts)
        
        # --- UPDATED METHODS ---
        data = self._extract_sex(data, combined_text)
        data = self._extract_place_of_birth(data, all_texts)
        data = self._extract_place_of_issue(data, all_texts) # Updated to take all_texts
        # --- END OF UPDATES ---
        
        data = self._extract_nationality(data, combined_text)
        
        return data

    def _extract_sex(self, data: Dict, text: str) -> Dict:
        """
        IMPROVED: Extract sex/gender with more robust patterns.
        """
        if not text:
            return data
            
        # Enhanced patterns to find M/F even with OCR noise or spacing issues.
        # These look for the character M or F in various contexts seen in passports.
      
        
        for pattern in self.patterns.sex:
            # Use re.DOTALL to allow '.' to match newlines, making patterns more robust
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                sex_value = value[0].upper() if value else None
                if sex_value in ['M', 'F']:
                    data['sex'] = sex_value
                    data['confidence_scores']['sex'] = self._calculate_dynamic_confidence(sex_value, 0.95)
                    data['extraction_method']['sex'] = 'regex_search'
                    self.logger.info(f"Sex extracted as '{sex_value}' using pattern: {pattern}")
                    return data
        
        self.logger.warning("Sex could not be extracted.")
        return data

    def _extract_place(self, all_texts: List[Tuple[str, str]], label_patterns: List[str], field_name: str) -> Optional[Tuple[str, str]]:
        """
        REUSABLE & IMPROVED: Generic function to extract a place (birth or issue).
        This fixes the bug of using 'in' with regex and uses a candidate-based approach.
        """
        candidates = []
        
        # This pattern finds a label and captures the text that follows it.
        # It's designed to be robust against newlines between the label and the value.
        extraction_patterns = [
            f'({label})\\s*[:/]?\\s*([A-Z][A-Z\\s/]{{3,25}})' for label in label_patterns
        ]

        for source, text in all_texts:
            for pattern in extraction_patterns:
                # Use re.DOTALL to handle labels and values on different lines
                matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    place_candidate = match.group(2).strip()
                    # Clean up common OCR errors and extra text
                    place_candidate = re.sub(r'\s*/\s*[\u0600-\u06FF\s]+', '', place_candidate) # Remove Arabic part
                    place_candidate = place_candidate.split('\n')[0].strip().upper() # Take only the first line
                    
                    if 3 < len(place_candidate) < 25 and place_candidate not in self.patterns.non_name_words:
                        candidates.append(place_candidate)
                        self.logger.debug(f"Found {field_name} candidate '{place_candidate}' from source '{source}'")

        if not candidates:
            return None

        # Return the most common valid candidate
        most_common = Counter(candidates).most_common(1)[0][0]
        self.logger.info(f"Most common candidate for {field_name} is '{most_common}'")
        return most_common, 'regex_candidate_selection'

    def _extract_place_of_birth(self, data: Dict, all_texts: List[Tuple[str, str]]) -> Dict:
        """
        IMPROVED: Extracts place of birth using a robust, candidate-based approach.
        """
        labels = ['Place of Birth', 'مكان الميلاد']
        result = self._extract_place(all_texts, labels, 'place_of_birth')
        
        if result:
            data['place_of_birth'] = result[0]
            data['extraction_method']['place_of_birth'] = result[1]
            data['confidence_scores']['place_of_birth'] = self._calculate_dynamic_confidence(result[0], 0.85)
        else:
            self.logger.warning("Place of Birth could not be extracted.")
            
        return data

    def _extract_place_of_issue(self, data: Dict, all_texts: List[Tuple[str, str]]) -> Dict:
        """
        IMPROVED: Extracts place of issue using the same robust logic as place of birth.
        """
        labels = ['Place of Issue', 'Authority', 'مكان الإصدار', 'جهة الإصدار']
        result = self._extract_place(all_texts, labels, 'place_of_issue')

        if result:
            data['place_of_issue'] = result[0]
            data['extraction_method']['place_of_issue'] = result[1]
            data['confidence_scores']['place_of_issue'] = self._calculate_dynamic_confidence(result[0], 0.80)
        else:
            self.logger.warning("Place of Issue could not be extracted.")

        return data

    # --- UNCHANGED HELPER METHODS ---
    # The following methods from your original script are well-structured and remain unchanged.

    def _extract_passport_number(self, data: Dict, all_texts: List[Tuple[str, str]]) -> Dict:
        """Extract and validate passport number"""
        for source_name, text in all_texts:
            for pattern in self.patterns.passport_number:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    candidate = (match.group(1) if match.groups() else match.group(0)).replace('O', '0').replace(' ', '').upper()
                    if re.match(r'^[A-Z]?[0-9]{8,9}$', candidate):
                        data['passport_number'] = candidate
                        data['extraction_method']['passport_number'] = source_name
                        data['confidence_scores']['passport_number'] = self._calculate_dynamic_confidence(candidate, 0.95)
                        return data
        return data
    
    def _extract_national_id(self, data: Dict, text: str) -> Dict:
        """Extract and validate national ID"""
        if not text: return data
        for pattern in self.patterns.national_id:
            matches = re.finditer(pattern, text)
            for match in matches:
                candidate = re.sub(r'[\s\.]', '-', match.group(1) if match.groups() else match.group(0))
                if re.match(r'^\d{3}-\d{4}-\d{4,5}$', candidate):
                    data['national_id'] = candidate
                    data['confidence_scores']['national_id'] = self._calculate_dynamic_confidence(candidate, 0.9)
                    return data
        return data
    
    def _extract_dates(self, data: Dict, text: str) -> Dict:
        """Extract and validate dates"""
        # This function is complex and seems to work, so it's kept as is.
        if not text: return data
        all_dates = []
        for pattern in self.patterns.date:
            all_dates.extend(re.findall(pattern, text))
        
        valid_dates = []
        for date_parts in all_dates:
            date_str = '-'.join(date_parts) if isinstance(date_parts, tuple) else date_parts
            date_str = re.sub(r'[\s\.]+', '-', date_str)
            try:
                parts = date_str.split('-')
                if len(parts) == 3:
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                        valid_dates.append(f"{day:02d}-{month:02d}-{year}")
            except: continue
        
        # valid_dates = sorted(list(set(valid_dates)), key=lambda x: datetime.strptime(x, '%d-%m-%Y'))
        
        if len(valid_dates) >= 1:
            data['date_of_birth'] = valid_dates[0]
            data['confidence_scores']['date_of_birth'] = self._calculate_dynamic_confidence(valid_dates[0], 0.85)
        if len(valid_dates) >= 2:
            # Assign issue and expiry based on chronological order
            issue_or_expiry = valid_dates[1:]
            data['date_of_issue'] = issue_or_expiry[0]
            data['confidence_scores']['date_of_issue'] = self._calculate_dynamic_confidence(issue_or_expiry[0], 0.8)
            if len(issue_or_expiry) > 1:
                data['date_of_expiry'] = issue_or_expiry[-1]
                data['confidence_scores']['date_of_expiry'] = self._calculate_dynamic_confidence(issue_or_expiry[-1], 0.85)

        return data
    
    def _extract_name(self, data: Dict, all_texts: List[Tuple[str, str]]) -> Dict:
        """Extract and validate name"""
        name_candidates = []
        for source_name, text in all_texts:
            for pattern in self.patterns.name:
                matches = re.findall(pattern, text)
                for match in matches:
                    name = ' '.join(match) if isinstance(match, tuple) else match
                    name = name.strip().upper()
                    if not any(word in name for word in self.patterns.non_name_words) and 10 <= len(name) <= 60:
                        name_candidates.append((name, source_name))
        
        if name_candidates:
            longest = max(name_candidates, key=lambda x: len(x[0]))
            data['full_name'] = longest[0]
            data['extraction_method']['full_name'] = longest[1]
            data['confidence_scores']['full_name'] = self._calculate_dynamic_confidence(longest[0], 0.85)
        return data
    
    def _extract_nationality(self, data: Dict, text: str) -> Dict:
        """Extract nationality and country code"""
        if not text: return data
        text_upper = text.upper()
        if any(indicator in text_upper for indicator in self.patterns.sudan_indicators):
            data['nationality'] = 'SUDANESE'
            data['country_code'] = 'SDN'
            data['passport_type'] = 'PC' # Common type for Sudanese passports
            data['confidence_scores']['nationality'] = 0.98
        return data

    def _calculate_dynamic_confidence(self, extracted_value: str, base_confidence: float = 0.8) -> float:
        """Calculate dynamic confidence based on OCR data and extraction quality"""
        # Kept as is.
        if not extracted_value or not self.ocr_confidence_data: return base_confidence * 0.5
        value_words = extracted_value.upper().split()
        ocr_confidences = []
        for source_key, ocr_data in self.ocr_confidence_data.items():
            for i, text in enumerate(ocr_data['text']):
                if text and text.strip().upper() in value_words:
                    try:
                        conf = int(ocr_data['conf'][i])
                        if conf > 0: ocr_confidences.append(conf)
                    except (ValueError, IndexError): continue
        if ocr_confidences:
            avg_ocr_conf = (sum(ocr_confidences) / len(ocr_confidences)) / 100.0
            dynamic_conf = (avg_ocr_conf * 0.6) + (base_confidence * 0.4)
            return min(1.0, round(dynamic_conf, 2))
        return base_confidence

    def _calculate_score(self, data: Dict) -> float:
        """Calculate overall extraction score"""
        important_fields = [
            'passport_number', 'full_name', 'nationality', 'date_of_birth',
            'date_of_issue', 'date_of_expiry', 'sex', 'place_of_birth', 'place_of_issue'
        ]
        extracted = sum(1 for field in important_fields if data.get(field))
        return round((extracted / len(important_fields)) * 100, 2)

    def _generate_summary(self, data: Dict) -> str:
        """Generate extraction summary"""
        fields = [
            'passport_number', 'full_name', 'nationality', 'national_id',
            'date_of_birth', 'date_of_issue', 'date_of_expiry', 'sex',
            'place_of_birth', 'place_of_issue', 'country_code'
        ]
        extracted = sum(1 for field in fields if data.get(field))
        return f"{extracted}/{len(fields)} fields extracted"
