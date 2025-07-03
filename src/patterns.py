"""
Passport Patterns
Regular expressions and constants for passport field extraction
"""

class PassportPatterns:
    def __init__(self):
        # Passport number patterns
        self.passport_number = [
            r'P\s*[0-9]{8,9}',
            r'P[0-9]{8,9}',
            r'Passport\s*No\.?\s*:?\s*([A-Z0-9]{8,10})',
            r'No\.?\s*:?\s*([A-Z0-9]{8,10})',
            r'([A-Z]{1,2}\s*[0-9]{6,9})',
            r'P\s*O\s*[0-9]{7,9}',  # Handle OCR confusion
            r'[PD][0-9O]{8,9}',     # Handle O/0 confusion
            r'جواز\s*رقم\s*:?\s*([A-Z0-9]{8,10})',  # Arabic
        ]
        
        # National ID patterns
        self.national_id = [
            r'\d{3}[-\s]?\d{4}[-\s]?\d{4,5}',
            r'\d{3}\s*[-\s]?\s*\d{4}\s*[-\s]?\s*\d{4,5}',
            r'National\s*No\.?\s*:?\s*(\d{3}[-\s]?\d{4}[-\s]?\d{4,5})',
            r'\d{11,12}',
            r'\d{3}\d{4}\d{4,5}',
            r'[0-9]{3}[\s\-\.][0-9]{4}[\s\-\.][0-9]{4,5}',
            r'الرقم\s*الوطني\s*:?\s*(\d{3}[-\s]?\d{4}[-\s]?\d{4,5})',  # Arabic
        ]
        
        # Date patterns
        self.date = [
            r'\d{2}[-/]\d{2}[-/]\d{4}',
            r'\d{2}\s*[-/]\s*\d{2}\s*[-/]\s*\d{4}',
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
            r'\d{2}\.\d{2}\.\d{4}',
            r'\d{2}\s+\d{2}\s+\d{4}',
            r'[0-3][0-9][\s\-/\.][0-1][0-9][\s\-/\.][1-2][0-9]{3}',
            r'\d{4}[-/]\d{2}[-/]\d{2}',  # ISO format
        ]
        
        # Name patterns
        self.name = [
            r'[A-Z]{3,}\s+[A-Z]{3,}(?:\s+[A-Z]{3,})*',
            r'[A-Z][A-Z\s\-\']{10,50}',
            r'(?:Name|NAME)\s*:?\s*([A-Z\s]+)',
            r'Full\s*Name\s*:?\s*([A-Z\s]+)',
            r'([A-Z]{2,}\s+){2,6}[A-Z]{2,}',
            r'[A-Z]+(?:\s+[A-Z]+){1,5}',
            r'الاسم\s*:?\s*([A-Z\s]+)',  # Arabic
            r'الاسم\s*الكامل\s*:?\s*([A-Z\s]+)',  # Arabic full name
        ]
        
        # Sex/Gender patterns
        self.sex = [
            r'\b[F/]\b',
            r'\b[M/]\b',
            r'(?:Sex|Gender)\s*:?\s*([MF])',
            r'(?:Sex|Gender)\s*:?\s*([MF])/',
            r'[MF]\s*/',
            r'[MF]/',
            r'الجنس\s*:?\s*([MF])',  # Arabic
            r'ذكر|أنثى',  # Arabic male/female
            r'(?:Male|Female)\s*:?\s*([MF])',
            r'(?:MALE|FEMALE)\s*:?\s*([MF])',
            r'(?:M|F)\s*:?\s*([MF])',
            r'(?:MALE|FEMALE)',
            r'(?:ذكر|أنثى)\s*:?\s*([MF])',  # Arabic with Latin letters
            r'(?:ذكر|أنثى)\s*:?\s*([MF])/',  # Arabic with Latin letters and slash
        ]
        
        # Common Sudanese places
        self.sudan_places = [
            'KHARTOUM', 'OMDURMAN', 'BAHRI', 'KASSALA', 'PORTSUDAN',
            'NYALA', 'ELOBEID', 'GEDAREF', 'WAD MADANI', 'KOSTI',
            'ALFASHER', 'DAMAZIN', 'KADUGLI', 'DONGOLA', 'ATBARA',
            'SENNAR', 'RABAK', 'GENEINA', 'DILLING', 'ALAYYAT',
            'UMM RUWABA', 'ZALINGEI', 'ALQADARIF', 'AD DOUIEM',
            'الخرطوم', 'أم درمان', 'بحري', 'كسلا', 'بورتسودان',
            'نيالا', 'الأبيض', 'القضارف', 'ود مدني', 'كوستي',
            'الفاشر', 'الدمازين', 'كادقلي', 'دنقلا', 'عطبرة',
            'KUWAIT','الكويت','RIYADH','الرياض','JEDDAH','جدة','MECCA','مكة',
            'SAUDI ARABIA','المملكة العربية السعودية',
            'SAUDI','السعودية','SAUDI ARABIA','المملكة العربية السعودية',
            'IRAN','إيران','TUNISIA','تونس','ALGERIA','الجزائر',
            'MOROCCO','المغرب','LIBYA','ليبيا','TURKEY','تركيا','SYRIA','سوريا',
            'LEBANON','لبنان','JORDAN','الأردن','IRAQ','العراق','EGYPT','مصر',
            'MOROCCO','المغرب','TURKEY','تركيا','SYRIA','سوريا','MOGTARBEEN','المغتربين','ALBYNEIA','البينة'
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
            'تاريخ', 'ميلاد', 'إصدار', 'انتهاء', 'مكان'
        ]