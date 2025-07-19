"""
Passport Patterns
Regular expressions and constants for passport field extraction
"""

import re
from datetime import datetime

class PassportPatterns:
    def __init__(self):
        # Passport number patterns - Enhanced for Sudanese passports
        self.passport_number = [
            # Standard patterns
            r'P\s*[0-9]{8,9}',
            r'P[0-9]{8,9}',
            r'Passport\s*No\.?\s*:?\s*([A-Z0-9]{8,10})',
            r'No\.?\s*:?\s*([A-Z0-9]{8,10})',
            r'([A-Z]{1,2}\s*[0-9]{6,9})',
            r'P\s*O\s*[0-9]{7,9}',  # Handle OCR confusion
            r'[PD][0-9O]{8,9}',     # Handle O/0 confusion
            r'جواز\s*رقم\s*:?\s*([A-Z0-9]{8,10})',  # Arabic
            # Sudanese specific patterns (B00013285 format)
            r'B[0-9]{8}',              # B followed by 8 digits
            r'[A-Z][0-9]{8}',          # Any letter followed by 8 digits
            r'P\s*[0-9]{8}\s*[0-9]?',  # P followed by 8-9 digits
            r'[Pp][0-9]{8,9}',         # Lowercase p sometimes
            r'(?:رقم|No\.?)\s*:?\s*([A-Z0-9]{8,10})',  # Number followed by digits
            r'(?:Passport\s*No\.?|رقم\s*الجواز)\s*:?\s*([A-Z][0-9]{8})',  # With label
        ]
        
        # National ID patterns - Updated for Sudanese format (242-9135-0472)
        self.national_id = [
            r'\d{3}[-\s]?\d{4}[-\s]?\d{4,5}',
            r'\d{3}\s*[-\s]?\s*\d{4}\s*[-\s]?\s*\d{4,5}',
            r'National\s*No\.?\s*:?\s*(\d{3}[-\s]?\d{4}[-\s]?\d{4,5})',
            r'\d{11,12}',
            r'\d{3}\d{4}\d{4,5}',
            r'[0-9]{3}[\s\-\.][0-9]{4}[\s\-\.][0-9]{4,5}',
            r'الرقم\s*الوطني\s*:?\s*(\d{3}[-\s]?\d{4}[-\s]?\d{4,5})',  # Arabic
            # Sudanese specific patterns
            r'(\d{3}[-]\d{4}[-]\d{4})',        # 242-9135-0472 format
            r'(\d{3}\d{4}\d{4})',              # Without separators
            r'(?:National\s*No\.?|الرقم\s*الوطني)\s*:?\s*(\d{3}[-]?\d{4}[-]?\d{4})',
        ]
        
        # Enhanced date patterns with better validation - Simplified to avoid extra capture groups
        self.date = [
            # Simple and effective date patterns
            
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',              # DD.MM.YYYY or MM.DD.YYYY  

         # DD MM YYYY or MM DD YYYY
       
 
        ]
        
        # Name patterns - Enhanced for Arabic/English names like "KASEM ABDULSALAM MOHAMED ABOURAS"
        self.name = [
            r'[A-Z]{3,}\s+[A-Z]{3,}(?:\s+[A-Z]{3,})*',
            r'[A-Z][A-Z\s\-\']{10,50}',
            r'(?:Name|NAME)\s*:?\s*([A-Z\s]+)',
            r'Full\s*Name\s*:?\s*([A-Z\s]+)',
            r'([A-Z]{2,}\s+){2,6}[A-Z]{2,}',
            r'[A-Z]+(?:\s+[A-Z]+){1,5}',
            r'الاسم\s*:?\s*([A-Z\s]+)',  # Arabic
            r'الاسم\s*الكامل\s*:?\s*([A-Z\s]+)',  # Arabic full name
            # Sudanese name patterns (3-4 part names common)
            r'([A-Z]{4,}\s+[A-Z]{4,}\s+[A-Z]{4,}\s+[A-Z]{4,})',  # Four part names

            r'(?:Full\s*Name|الاسم\s*الكامل)\s*:?\s*([A-Z\s]{15,50})',  # With label
        ]
        
        # Sex/Gender patterns (refactored for reliability)
        self.sex = [
            # r'(?:Sex|Gender)\s*:?-?\s*(MALE|FEMALE)',         # Sex: MALE or FEMALE
            # r'(?:Sex|Gender)\s*:?-?\s*([MF])/?',              # Sex: M or F (with optional slash)
            # r'(?:Sex|Gender)\s*:?-?\s*(ذكر|أنثى)',            # Arabic: ذكر or أنثى
            # r'الجنس\s*:?-?\s*(ذكر|أنثى)',                    # Arabic label
            # r'الجنس\s*:?-?\s*([MF])/?',                      # Arabic label with M/F (with optional slash)
            # r'\b(MALE|FEMALE)\b',                            # Just the word
            # r'\b(ذكر|أنثى)\b',                               # Just Arabic word
            # r'\b([MF])/?\b',                                 # Standalone M or F (with optional slash)
            # Enhanced patterns for Sudanese passports
            r'(?:الجنس|Sex)\s*:?\s*(ذكر|أنثى)\s*([MF])',    # ذكر M or أنثى F format
            r'(?:الجنس|Sex)\s*:?\s*([MF])\s*(ذكر|أنثى)',    # M ذكر or F أنثى format
            r'(?:الجنس|Sex)\s*:?\s*([MF])/?\s*ذكر',         # M ذكر format
            r'(?:الجنس|Sex)\s*:?\s*([MF])/?\s*أنثى',        # F أنثى format
            r'ذكر\s*([MF])',                                 # ذكر M format
            r'أنثى\s*([MF])',                                # أنثى F format
            r'([MF])\s*ذكر',                                 # M ذكر format
            r'([MF])\s*أنثى',                                # F أنثى format
        ]
        
        # Common Sudanese places - Enhanced with more variants
        self.sudan_places = [
            'KHARTOUM', 'OMDURMAN', 'BAHRI', 'KASSALA', 'PORTSUDAN',
            'NYALA', 'ELOBEID', 'GEDAREF', 'WAD MADANI', 'KOSTI',
            'ALFASHER', 'DAMAZIN', 'KADUGLI', 'DONGOLA', 'ATBARA',
            'SENNAR', 'RABAK', 'GENEINA', 'DILLING', 'ALAYYAT',
            'UMM RUWABA', 'ZALINGEI', 'ALQADARIF', 'AD DOUIEM',
            'الخرطوم', 'أم درمان', 'بحري', 'كسلا', 'بورتسودان',
            'نيالا', 'الأبيض', 'القضارف', 'ود مدني', 'كوستي',
            'الفاشر', 'الدمازين', 'كادقلي', 'دنقلا', 'عطبرة',
            # Additional places from passport template
            'HALFA', 'ALBYNEIA', 'ALI', 'حلفا', 'البينية',
            'KUWAIT','الكويت','RIYADH','الرياض','JEDDAH','جدة','MECCA','مكة',
            'SAUDI ARABIA','المملكة العربية السعودية',
            'SAUDI','السعودية','SAUDI ARABIA','المملكة العربية السعودية',
            'IRAN','إيران','TUNISIA','تونس','ALGERIA','الجزائر',
            'MOROCCO','المغرب','LIBYA','ليبيا','TURKEY','تركيا','SYRIA','سوريا',
            'LEBANON','لبنان','JORDAN','الأردن','IRAQ','العراق','EGYPT','مصر',
            'MOROCCO','المغرب','TURKEY','تركيا','SYRIA','سوريا','MOGTARBEEN','المغتربين','ALBYNEIA','البينة',
            'ود مدني الكبرى','RABK'
            'GREATER'
        ]
        
        # Sudan indicators
        self.sudan_indicators = [
            'SDN', 'SUDAN', 'REPUBLIC OF SUDAN', 'REPUBLIC OF THE SUDAN',
            'السودان', 'جمهورية السودان', 'SUDANESE', 'سوداني'
        ]
        
        # Non-name words to filter out
        self.non_name_words = [
            'REPUBLIC', 'SUDAN', 'PASSPORT', 'TYPE', 'NATIONAL',
            'NUMBER', 'DATE', 'BIRTH', 'ISSUE', 'EXPIRY', 'SEX',
            'PLACE', 'NATIONALITY', 'SIGNATURE', 'HOLDER', 'AUTHORITY',
            'GENDER', 'COUNTRY', 'CODE', 'DOCUMENT', 'IDENTIFICATION',
            'جمهورية', 'السودان', 'جواز', 'نوع', 'رقم',
            'تاريخ', 'ميلاد', 'إصدار', 'انتهاء', 'مكان',
            # Additional terms to filter
            'SDN'
        ]
        
        # MRZ (Machine Readable Zone) patterns
        self.mrz_patterns = [
            # First line: P<COUNTRYCODE<SURNAME<<GIVENNAMES<<<<<<<<
            r'P[<]([A-Z]{3})[<]([A-Z<]+)[<]([A-Z<]+)[<]*',
            # Second line: passport_number + country + birth_date + sex + expiry + national_id + checksum
            r'([A-Z0-9<]{9})[0-9]([A-Z]{3})([0-9]{6})[0-9]([MF])([0-9]{6})[0-9]([A-Z0-9<]{14,15})[0-9<]*',
            # Flexible MRZ patterns for damaged/unclear text
            r'([A-Z][0-9]{8})[0-9<]*([A-Z]{3})([0-9]{6})[0-9<]*([MF])([0-9]{6})[0-9<]*',
        ]
        
        # Authority patterns - for Sudanese passports
        self.authority_patterns = [
            r'Authority\s*:?\s*([A-Z\s/]+)',
            r'Issuing\s*Authority\s*:?\s*([A-Z\s/]+)',
            r'السلطة\s*المصدرة\s*:?\s*([A-Z\s/]+)',
            r'جهة\s*الإصدار\s*:?\s*([A-Z\s/]+)',
            # Common Sudanese authorities
            r'(ALBYNEIA\s*/\s*البينية)',
            r'(MINISTRY\s*OF\s*INTERIOR)',
            r'(وزارة\s*الداخلية)',
            # Enhanced patterns for place of issue
            r'(?:Place\s*of\s*Issue|Issuing\s*Authority)\s*:?\s*([A-Z\s/]+)',
            r'(?:مكان\s*الإصدار|جهة\s*الإصدار)\s*:?\s*([A-Z\s/]+)',
            r'(?:Issue|إصدار)\s*:?\s*([A-Z\s/]+)',
            # Specific patterns for common places
            r'(RIYADH\s*/\s*الرياض)',
            r'(JEDDAH\s*/\s*جدة)',
            r'(MECCA\s*/\s*مكة)',
            r'(KHARTOUM\s*/\s*الخرطوم)',
            r'(OMDURMAN\s*/\s*أم\s*درمان)',
            r'(ALBYNEIA\s*/\s*البينية)',
            # Pattern to catch place names with Arabic translations
            r'([A-Z]+)\s*/\s*([\u0600-\u06FF\s]+)',  # English/Arabic format
            r'([A-Z\s]+)\s*/\s*([\u0600-\u06FF\s]+)',  # English/Arabic format with spaces
        ]
        
        # Place of Birth patterns - Specific patterns to distinguish from place of issue
        self.place_of_birth_patterns = [
            r'(?:Place\s*of\s*Birth|Birth\s*Place)\s*:?/?\s*مكان\s*الميلاد\s*:?\s*([A-Z\s/]+)',
            r'(?:Place\s*of\s*Birth|Birth\s*Place)\s*:?\s*([A-Z\s/]+)',
            r'(?:POB|P\.O\.B\.)\s*:?\s*([A-Z\s/]+)',
            r'مكان\s*الميلاد\s*:?\s*([A-Z\s/]+)',
            r'محل\s*الولادة\s*:?\s*([A-Z\s/]+)',
            r'Born\s*:?\s*([A-Z\s/]+)',
            r'Born\s*in\s*:?\s*([A-Z\s/]+)',
            # Look for birth-related context before place names
            r'(?:Birth|Born|ميلاد|ولادة)[\s\w]*?:?\s*(' + '|'.join(self.sudan_places) + r')',
            # Pattern to catch birth place in structured format
            r'Birth\s*Place\s*/\s*مكان\s*الميلاد\s*:?\s*([A-Z\s/]+)',
            r'P\.?\s*O\.?\s*B\.?\s*:?\s*([A-Z\s/]+)',
        ]
   
    
    def parse_date_string(self, date_str: str) -> tuple:
        """
        Parse date string and return (day, month, year) tuple
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            tuple: (day, month, year) or None if invalid
        """
        # Clean the date string
        date_str = re.sub(r'[\s\.]+', '-', date_str.strip())
        date_str = re.sub(r'/+', '-', date_str)
        
        # Try different date formats
        formats_to_try = [
            # DD-MM-YYYY
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', 'DD-MM-YYYY'),
            # MM-DD-YYYY  
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', 'MM-DD-YYYY'),
            # YYYY-MM-DD
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'YYYY-MM-DD'),
        ]
        
        for pattern, format_type in formats_to_try:
            match = re.match(pattern, date_str)
            if match:
                try:
                    if format_type == 'DD-MM-YYYY':
                        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    elif format_type == 'MM-DD-YYYY':
                        month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    elif format_type == 'YYYY-MM-DD':
                        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    
                    # Validate the date
                    if self.validate_date(day, month, year):
                        return (day, month, year)
                        
                except (ValueError, IndexError):
                    continue
        
        return None
    
