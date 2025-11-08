"""
ISBN Extraction and Normalization Pipeline
===========================================

This module implements an automated pipeline for extracting, normalizing, 
and validating ISBNs from Arabic-script documents with OCR noise.

Reference: "The Codes Talk: Automated Extraction and Normalization of ISBNs 
for Metadata Integration" (JCDL Conference Paper)

Author: [Your Name]
License: MIT
"""

import re
import pandas as pd
from typing import Optional, Tuple, Dict, List
import unicodedata


class ISBNNormalizer:
    """
    Handles ISBN extraction, normalization, and validation for multilingual
    metadata with support for Arabic-Indic and Persian numerals.
    """
    
    # Unicode mappings for numeral conversion
    ARABIC_INDIC_TO_ASCII = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    
    PERSIAN_TO_ASCII = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    
    # OCR confusion dictionary for character-level correction
    CONFUSION_DICT = {
        'o': '0', 'O': '0', 'l': '1', 'I': '1', 
        'B': '8', 'S': '5', 'Z': '2',
        'ه': '0', 'س': '5', '٨': '8',  # Arabic-specific confusions
    }
    
    # ISBN prefix patterns (Arabic and English)
    ISBN_PREFIXES = [
        'ISBN', 'I.S.B.N', 'isbn',
        'ردمك', 'ر.د.م.ك',  # Arabic ISBN
        'الرقم الدولي المعياري',  # Full Arabic name
    ]
    
    def __init__(self):
        """Initialize the ISBN normalizer."""
        self.stats = {
            'total_processed': 0,
            'valid_isbns': 0,
            'corrected_isbns': 0,
            'failed_validation': 0
        }
    
    def convert_numerals(self, text: str) -> str:
        """
        Convert Arabic-Indic and Persian numerals to ASCII digits.
        
        Args:
            text: Input string potentially containing non-ASCII numerals
            
        Returns:
            String with all numerals converted to ASCII (0-9)
        """
        if not text:
            return text
            
        # Convert Arabic-Indic numerals
        for arabic, ascii_digit in self.ARABIC_INDIC_TO_ASCII.items():
            text = text.replace(arabic, ascii_digit)
        
        # Convert Persian numerals
        for persian, ascii_digit in self.PERSIAN_TO_ASCII.items():
            text = text.replace(persian, ascii_digit)
        
        return text
    
    def remove_prefixes(self, text: str) -> str:
        """
        Remove ISBN prefix keywords from the candidate string.
        
        Args:
            text: Input string potentially containing ISBN prefix
            
        Returns:
            String with ISBN prefixes removed
        """
        if not text:
            return text
        
        text_clean = text.strip()
        
        for prefix in self.ISBN_PREFIXES:
            # Case-insensitive removal
            pattern = re.compile(re.escape(prefix), re.IGNORECASE)
            text_clean = pattern.sub('', text_clean)
        
        return text_clean.strip()
    
    def clean_isbn_string(self, text: str) -> str:
        """
        Remove non-digit characters except 'X' for ISBN-10.
        
        Args:
            text: Input ISBN candidate string
            
        Returns:
            Cleaned string containing only digits and possibly 'X'
        """
        if not text:
            return ""
        
        # Remove hyphens, colons, spaces, and other punctuation
        # Keep only digits and 'X' (valid for ISBN-10 check digit)
        cleaned = re.sub(r'[^\dXx]', '', text)
        
        return cleaned.upper()
    
    def handle_bidirectionality(self, text: str) -> str:
        """
        Correct bidirectionality issues in mixed Arabic-Latin text.
        
        Args:
            text: Input string with potential direction issues
            
        Returns:
            String with corrected digit order
        """
        if not text:
            return text
        
        # Check if string contains Arabic characters
        has_arabic = any('\u0600' <= c <= '\u06FF' for c in text)
        
        if has_arabic:
            # Extract digits and check if they appear reversed
            digits = re.findall(r'\d+', text)
            if digits:
                # If digits follow Arabic text, they might be reversed
                # Simple heuristic: reverse digit sequences
                for digit_seq in digits:
                    if len(digit_seq) >= 10:  # Likely an ISBN
                        text = text.replace(digit_seq, digit_seq[::-1])
        
        return text
    
    def validate_isbn10(self, isbn: str) -> bool:
        """
        Validate ISBN-10 using MOD11 checksum algorithm.
        
        Args:
            isbn: 10-digit ISBN string (last char can be 'X')
            
        Returns:
            True if valid, False otherwise
        """
        if len(isbn) != 10:
            return False
        
        try:
            # Calculate weighted sum
            total = 0
            for i in range(9):
                if not isbn[i].isdigit():
                    return False
                total += int(isbn[i]) * (10 - i)
            
            # Handle check digit (can be 'X' for 10)
            if isbn[9] == 'X':
                total += 10
            elif isbn[9].isdigit():
                total += int(isbn[9])
            else:
                return False
            
            # Valid if divisible by 11
            return total % 11 == 0
        
        except (ValueError, IndexError):
            return False
    
    def validate_isbn13(self, isbn: str) -> bool:
        """
        Validate ISBN-13 using MOD10 (EAN-13) checksum algorithm.
        
        Args:
            isbn: 13-digit ISBN string
            
        Returns:
            True if valid, False otherwise
        """
        if len(isbn) != 13:
            return False
        
        try:
            # Calculate weighted sum (alternating 1 and 3)
            total = 0
            for i in range(12):
                if not isbn[i].isdigit():
                    return False
                weight = 1 if i % 2 == 0 else 3
                total += int(isbn[i]) * weight
            
            # Calculate check digit
            check_digit = (10 - (total % 10)) % 10
            
            return int(isbn[12]) == check_digit
        
        except (ValueError, IndexError):
            return False
    
    def validate_isbn(self, isbn: str) -> Tuple[bool, str]:
        """
        Validate ISBN and return validation status and type.
        
        Args:
            isbn: ISBN string to validate
            
        Returns:
            Tuple of (is_valid, isbn_type) where isbn_type is '10', '13', or 'invalid'
        """
        if len(isbn) == 10:
            is_valid = self.validate_isbn10(isbn)
            return (is_valid, '10' if is_valid else 'invalid')
        elif len(isbn) == 13:
            is_valid = self.validate_isbn13(isbn)
            return (is_valid, '13' if is_valid else 'invalid')
        else:
            return (False, 'invalid')
    
    def attempt_character_correction(self, isbn: str) -> Optional[str]:
        """
        Attempt to correct ISBN by substituting confused characters.
        
        Args:
            isbn: Invalid ISBN candidate
            
        Returns:
            Corrected valid ISBN if found, None otherwise
        """
        # Try substituting each character that might be confused
        for i, char in enumerate(isbn):
            if char in self.CONFUSION_DICT:
                # Try each possible correction
                for correct_char in self.CONFUSION_DICT[char]:
                    corrected = isbn[:i] + correct_char + isbn[i+1:]
                    is_valid, _ = self.validate_isbn(corrected)
                    if is_valid:
                        self.stats['corrected_isbns'] += 1
                        return corrected
        
        # Try multiple substitutions for severe OCR noise
        confused_positions = [i for i, c in enumerate(isbn) if c in self.CONFUSION_DICT]
        
        if len(confused_positions) <= 3:  # Limit to avoid combinatorial explosion
            # Recursive correction (simplified - could be optimized)
            for pos in confused_positions:
                char = isbn[pos]
                for correct_char in self.CONFUSION_DICT.get(char, []):
                    corrected = isbn[:pos] + correct_char + isbn[pos+1:]
                    is_valid, _ = self.validate_isbn(corrected)
                    if is_valid:
                        self.stats['corrected_isbns'] += 1
                        return corrected
        
        return None
    
    def normalize_isbn(self, raw_text: str) -> Optional[str]:
        """
        Main normalization pipeline for ISBN extraction and cleaning.
        
        Args:
            raw_text: Raw text potentially containing ISBN
            
        Returns:
            Normalized and validated ISBN, or None if invalid
        """
        if not raw_text:
            return None
        
        self.stats['total_processed'] += 1
        
        # Step 1: Convert numerals
        text = self.convert_numerals(raw_text)
        
        # Step 2: Handle bidirectionality
        text = self.handle_bidirectionality(text)
        
        # Step 3: Remove prefixes
        text = self.remove_prefixes(text)
        
        # Step 4: Clean string
        isbn_candidate = self.clean_isbn_string(text)
        
        # Step 5: Length check
        if len(isbn_candidate) not in [10, 13]:
            # Soft validation: check if close to valid length
            if 11 <= len(isbn_candidate) <= 12:
                # Flag as soft candidate for fallback matching
                return None
            return None
        
        # Step 6: Validate
        is_valid, isbn_type = self.validate_isbn(isbn_candidate)
        
        if is_valid:
            self.stats['valid_isbns'] += 1
            return isbn_candidate
        
        # Step 7: Attempt correction
        corrected = self.attempt_character_correction(isbn_candidate)
        
        if corrected:
            return corrected
        
        self.stats['failed_validation'] += 1
        return None
    
    def get_statistics(self) -> Dict[str, int]:
        """Return processing statistics."""
        return self.stats.copy()


class MetadataExtractor:
    """
    Extracts metadata fields (title, author, ISBN) from structured filenames
    or text content.
    """
    
    def __init__(self):
        """Initialize metadata extractor."""
        pass
    
    def extract_from_filename(self, filename: str) -> Dict[str, str]:
        """
        Extract metadata from structured filename.
        
        Expected format variations:
        - title_author_isbn.pdf
        - title_isbn.pdf
        - isbn_title_author.pdf
        
        Args:
            filename: Filename string
            
        Returns:
            Dictionary with 'title', 'author', 'isbn' keys
        """
        metadata = {
            'title': '',
            'author': '',
            'isbn': ''
        }
        
        # Remove extension
        name = filename.rsplit('.', 1)[0]
        
        # Split by common delimiters
        parts = re.split(r'[_\-]', name)
        
        # Heuristic: Look for ISBN-like patterns
        isbn_pattern = re.compile(r'\d{10,13}')
        
        for i, part in enumerate(parts):
            if isbn_pattern.search(part):
                metadata['isbn'] = part
                # Assume title is before ISBN, author after (if present)
                if i > 0:
                    metadata['title'] = '_'.join(parts[:i])
                if i < len(parts) - 1:
                    metadata['author'] = '_'.join(parts[i+1:])
                break
        
        # If no ISBN found, assume first part is title
        if not metadata['isbn'] and parts:
            metadata['title'] = parts[0]
            if len(parts) > 1:
                metadata['author'] = parts[1]
        
        return metadata
    
    def extract_from_text(self, text: str) -> Dict[str, str]:
        """
        Extract metadata from OCR text using pattern matching.
        
        Args:
            text: OCR-extracted text from title page
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            'title': '',
            'author': '',
            'isbn': ''
        }
        
        # ISBN extraction pattern (more permissive)
        isbn_patterns = [
            r'(?:ISBN|ردمك|I\.S\.B\.N)[:\s]*([0-9\-X]{10,17})',
            r'\b(\d{10}|\d{13})\b'
        ]
        
        for pattern in isbn_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['isbn'] = match.group(1)
                break
        
        # Title extraction (simple heuristic: first substantial line)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            metadata['title'] = lines[0]
        
        # Author extraction (look for common patterns)
        author_patterns = [
            r'(?:by|author|مؤلف|تأليف)[:\s]+([^\n]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)'  # Name pattern
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['author'] = match.group(1).strip()
                break
        
        return metadata


def create_sample_dataset():
    """Create sample dataset for testing."""
    sample_data = [
        {
            'filename': 'Islamic_Philosophy_Ibn_Sina_9780195153071.pdf',
            'raw_isbn': 'ISBN: 978-0-19-515307-1',
            'expected': '9780195153071'
        },
        {
            'filename': 'arabic_book_ردمك_٩٧٨٦٠٠١٠٠٢٥٤٠.pdf',
            'raw_isbn': 'ردمك: ٩٧٨٦٠٠١٠٠٢٥٤٠',
            'expected': '9786001002540'
        },
        {
            'filename': 'hadith_collection_978600100254ه.pdf',
            'raw_isbn': '978600100254ه',  # OCR error: ه instead of 0
            'expected': '9786001002540'
        },
        {
            'filename': 'noisy_ocr_I5BN_978O19515307l.pdf',
            'raw_isbn': 'I5BN: 978O19515307l',  # Multiple OCR errors
            'expected': '9780195153071'
        }
    ]
    
    return pd.DataFrame(sample_data)


if __name__ == "__main__":
    # Demonstration
    print("=" * 60)
    print("ISBN Extraction and Normalization Pipeline")
    print("=" * 60)
    
    # Initialize normalizer
    normalizer = ISBNNormalizer()
    extractor = MetadataExtractor()
    
    # Create sample data
    df = create_sample_dataset()
    
    print(f"\nProcessing {len(df)} sample records...\n")
    
    # Process each record
    results = []
    for idx, row in df.iterrows():
        print(f"Record {idx + 1}:")
        print(f"  Filename: {row['filename']}")
        print(f"  Raw ISBN: {row['raw_isbn']}")
        
        # Extract and normalize
        normalized = normalizer.normalize_isbn(row['raw_isbn'])
        
        print(f"  Normalized: {normalized}")
        print(f"  Expected: {row['expected']}")
        print(f"  Status: {'✓ PASS' if normalized == row['expected'] else '✗ FAIL'}")
        print()
        
        results.append({
            'raw': row['raw_isbn'],
            'normalized': normalized,
            'expected': row['expected'],
            'match': normalized == row['expected']
        })
    
    # Display statistics
    print("\n" + "=" * 60)
    print("Processing Statistics")
    print("=" * 60)
    stats = normalizer.get_statistics()
    for key, value in stats.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Calculate accuracy
    matches = sum(1 for r in results if r['match'])
    accuracy = (matches / len(results)) * 100 if results else 0
    print(f"\nAccuracy: {accuracy:.1f}%")
