"""
Test Suite for ISBN Normalization Pipeline
==========================================

Tests for ISBN extraction, normalization, validation, and matching.
"""

import pytest
from isbn_pipeline import ISBNNormalizer, MetadataExtractor
from catalog_matcher import FallbackMatcher


class TestISBNNormalizer:
    """Test cases for ISBN normalization."""
    
    @pytest.fixture
    def normalizer(self):
        """Create normalizer instance for tests."""
        return ISBNNormalizer()
    
    def test_convert_arabic_indic_numerals(self, normalizer):
        """Test conversion of Arabic-Indic numerals to ASCII."""
        arabic = "٩٧٨٦٠٠١٠٠٢٥٤٠"
        expected = "9786001002540"
        result = normalizer.convert_numerals(arabic)
        assert result == expected
    
    def test_convert_persian_numerals(self, normalizer):
        """Test conversion of Persian numerals to ASCII."""
        persian = "۹۷۸۶۰۰۱۰۰۲۵۴۰"
        expected = "9786001002540"
        result = normalizer.convert_numerals(persian)
        assert result == expected
    
    def test_remove_isbn_prefix_english(self, normalizer):
        """Test removal of English ISBN prefix."""
        text = "ISBN: 9786001002540"
        result = normalizer.remove_prefixes(text)
        assert "ISBN" not in result
        assert "9786001002540" in result
    
    def test_remove_isbn_prefix_arabic(self, normalizer):
        """Test removal of Arabic ISBN prefix."""
        text = "ردمك: ٩٧٨٦٠٠١٠٠٢٥٤٠"
        result = normalizer.remove_prefixes(text)
        assert "ردمك" not in result
    
    def test_clean_isbn_string(self, normalizer):
        """Test cleaning of ISBN string."""
        text = "978-0-19-515307-1"
        result = normalizer.clean_isbn_string(text)
        assert result == "9780195153071"
        assert "-" not in result
    
    def test_validate_isbn10_valid(self, normalizer):
        """Test validation of valid ISBN-10."""
        isbn10 = "0195153073"
        assert normalizer.validate_isbn10(isbn10) is True
    
    def test_validate_isbn10_with_x(self, normalizer):
        """Test validation of ISBN-10 with X check digit."""
        isbn10 = "043942089X"
        assert normalizer.validate_isbn10(isbn10) is True
    
    def test_validate_isbn10_invalid(self, normalizer):
        """Test validation of invalid ISBN-10."""
        isbn10 = "0195153070"  # Wrong check digit
        assert normalizer.validate_isbn10(isbn10) is False
    
    def test_validate_isbn13_valid(self, normalizer):
        """Test validation of valid ISBN-13."""
        isbn13 = "9780195153071"
        assert normalizer.validate_isbn13(isbn13) is True
    
    def test_validate_isbn13_invalid(self, normalizer):
        """Test validation of invalid ISBN-13."""
        isbn13 = "9780195153070"  # Wrong check digit
        assert normalizer.validate_isbn13(isbn13) is False
    
    def test_character_correction_single_error(self, normalizer):
        """Test correction of single OCR error."""
        # 'ه' (Arabic heh) often confused with '0'
        noisy = "978600100254ه"
        corrected = normalizer.attempt_character_correction(noisy)
        assert corrected == "9786001002540"
    
    def test_character_correction_multiple_errors(self, normalizer):
        """Test correction with multiple OCR errors."""
        noisy = "978O1951530l1"  # 'O' for '0', 'l' for '1'
        corrected = normalizer.attempt_character_correction(noisy)
        assert corrected == "9780195153011"
    
    def test_normalize_isbn_complete_pipeline(self, normalizer):
        """Test complete normalization pipeline."""
        test_cases = [
            ("ISBN: 978-0-19-515307-1", "9780195153071"),
            ("ردمك: ٩٧٨٦٠٠١٠٠٢٥٤٠", "9786001002540"),
            ("978600100254ه", "9786001002540"),
            ("I.S.B.N 0-19-515307-3", "0195153073"),
        ]
        
        for raw, expected in test_cases:
            result = normalizer.normalize_isbn(raw)
            assert result == expected, f"Failed for {raw}: got {result}, expected {expected}"
    
    def test_normalize_isbn_invalid_length(self, normalizer):
        """Test normalization with invalid length."""
        invalid = "ISBN: 12345"
        result = normalizer.normalize_isbn(invalid)
        assert result is None
    
    def test_normalize_isbn_no_valid_digits(self, normalizer):
        """Test normalization with no valid digits."""
        invalid = "ISBN: ABCDEFGHIJ"
        result = normalizer.normalize_isbn(invalid)
        assert result is None


class TestMetadataExtractor:
    """Test cases for metadata extraction."""
    
    @pytest.fixture
    def extractor(self):
        """Create extractor instance for tests."""
        return MetadataExtractor()
    
    def test_extract_from_filename_basic(self, extractor):
        """Test basic filename extraction."""
        filename = "Islamic_Philosophy_9780195153071.pdf"
        result = extractor.extract_from_filename(filename)
        
        assert result['title'] == "Islamic_Philosophy"
        assert "9780195153071" in result['isbn']
    
    def test_extract_from_filename_with_author(self, extractor):
        """Test filename extraction with author."""
        filename = "Title_Author_9780195153071.pdf"
        result = extractor.extract_from_filename(filename)
        
        assert "Title" in result['title']
        assert "Author" in result['author']
        assert "9780195153071" in result['isbn']
    
    def test_extract_from_text_with_isbn(self, extractor):
        """Test text extraction with ISBN."""
        text = """
        Islamic Philosophy: A Beginner's Guide
        By Ibn Sina
        ISBN: 978-0-19-515307-1
        """
        result = extractor.extract_from_text(text)
        
        assert "Islamic Philosophy" in result['title']
        assert "9780195153071" in result['isbn']


class TestFallbackMatcher:
    """Test cases for fallback matching."""
    
    def test_title_similarity_exact_match(self):
        """Test title similarity with exact match."""
        similarity = FallbackMatcher.calculate_title_similarity(
            "Islamic Philosophy",
            "Islamic Philosophy"
        )
        assert similarity == 1.0
    
    def test_title_similarity_partial_match(self):
        """Test title similarity with partial match."""
        similarity = FallbackMatcher.calculate_title_similarity(
            "Islamic Philosophy: A Guide",
            "Islamic Philosophy"
        )
        assert 0.7 < similarity < 1.0
    
    def test_title_similarity_no_match(self):
        """Test title similarity with no match."""
        similarity = FallbackMatcher.calculate_title_similarity(
            "Islamic Philosophy",
            "Computer Science"
        )
        assert similarity < 0.3
    
    def test_normalize_author_name(self):
        """Test author name normalization."""
        test_cases = [
            ("Dr. John Smith", "john smith"),
            ("Prof. Jane Doe", "jane doe"),
            ("Mr. Ahmed Ali", "ahmed ali"),
        ]
        
        for input_name, expected in test_cases:
            result = FallbackMatcher.normalize_author_name(input_name)
            assert result == expected
    
    def test_match_by_metadata_good_match(self):
        """Test metadata matching with good match."""
        record = {
            'title': 'Islamic Philosophy',
            'author': 'Ibn Sina'
        }
        
        catalog = [
            {
                'isbn': '9780195153071',
                'title': 'Islamic Philosophy: A Guide',
                'author': 'Ibn Sina'
            }
        ]
        
        match = FallbackMatcher.match_by_metadata(record, catalog)
        assert match is not None
        assert match['isbn'] == '9780195153071'
        assert match['match_score'] > 0.6
    
    def test_match_by_metadata_no_match(self):
        """Test metadata matching with no match."""
        record = {
            'title': 'Unknown Book',
            'author': 'Unknown Author'
        }
        
        catalog = [
            {
                'isbn': '9780195153071',
                'title': 'Islamic Philosophy',
                'author': 'Ibn Sina'
            }
        ]
        
        match = FallbackMatcher.match_by_metadata(record, catalog)
        assert match is None


class TestIntegration:
    """Integration tests for complete pipeline."""
    
    def test_end_to_end_pipeline(self):
        """Test complete pipeline from raw ISBN to normalized."""
        normalizer = ISBNNormalizer()
        
        # Simulate real-world noisy data
        test_data = [
            {
                'raw': 'ISBN: ٩٧٨-٠-١٩-٥١٥٣٠٧-١',
                'expected': '9780195153071'
            },
            {
                'raw': 'ردمك ۹۷۸۶۰۰۱۰۰۲۵۴۰',
                'expected': '9786001002540'
            },
            {
                'raw': 'I5BN: 978O19515307l',  # Multiple OCR errors
                'expected': '9780195153071'
            }
        ]
        
        for case in test_data:
            result = normalizer.normalize_isbn(case['raw'])
            assert result == case['expected'], \
                f"Failed for {case['raw']}: got {result}, expected {case['expected']}"
    
    def test_statistics_tracking(self):
        """Test that statistics are correctly tracked."""
        normalizer = ISBNNormalizer()
        
        # Process some ISBNs
        normalizer.normalize_isbn("ISBN: 9780195153071")  # Valid
        normalizer.normalize_isbn("978600100254ه")  # Needs correction
        normalizer.normalize_isbn("ISBN: 12345")  # Invalid
        
        stats = normalizer.get_statistics()
        
        assert stats['total_processed'] == 3
        assert stats['valid_isbns'] >= 1
        assert stats['corrected_isbns'] >= 1
        assert stats['failed_validation'] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=html"])
