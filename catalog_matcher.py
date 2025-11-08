"""
Catalog Matching and Fallback Module
====================================

Handles querying external library catalogs and implements fallback
matching strategies when ISBNs are missing or invalid.
"""

import time
import requests
from bs4 import BeautifulSoup
import cloudscraper
from typing import Optional, Dict, Tuple
from urllib.parse import urlencode, urljoin
import difflib


class CatalogMatcher:
    """
    Handles catalog querying and matching with fallback strategies.
    """
    
    def __init__(self, catalog_base_url: str, delay: float = 1.5):
        """
        Initialize catalog matcher.
        
        Args:
            catalog_base_url: Base URL of the library catalog
            delay: Delay between requests in seconds (rate limiting)
        """
        self.catalog_base_url = catalog_base_url
        self.delay = delay
        self.scraper = cloudscraper.create_scraper()
        
        self.stats = {
            'isbn_matches': 0,
            'fallback_matches': 0,
            'no_match': 0,
            'errors': 0
        }
    
    def search_by_isbn(self, isbn: str) -> Optional[Dict[str, str]]:
        """
        Search catalog by ISBN.
        
        Args:
            isbn: Normalized ISBN string
            
        Returns:
            Dictionary with match info or None if not found
        """
        if not isbn:
            return None
        
        try:
            # Construct search URL (adjust based on actual catalog)
            params = {'isbn': isbn}
            search_url = f"{self.catalog_base_url}/search?{urlencode(params)}"
            
            # Add delay for rate limiting
            time.sleep(self.delay)
            
            # Perform request
            response = self.scraper.get(search_url, timeout=30)
            response.raise_for_status()
            
            # Parse response
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for title link (adjust selector based on actual HTML)
            title_element = soup.find('a', class_='title')
            
            if title_element:
                self.stats['isbn_matches'] += 1
                return {
                    'found': True,
                    'catalog_url': urljoin(self.catalog_base_url, title_element.get('href', '')),
                    'title': title_element.get_text(strip=True),
                    'match_type': 'isbn'
                }
            
            return None
        
        except requests.exceptions.RequestException as e:
            self.stats['errors'] += 1
            print(f"Error searching by ISBN {isbn}: {e}")
            return None
    
    def search_by_title_author(self, title: str, author: str = '') -> Optional[Dict[str, str]]:
        """
        Fallback search using title and author.
        
        Args:
            title: Book title
            author: Author name (optional)
            
        Returns:
            Dictionary with match info or None if not found
        """
        if not title:
            return None
        
        try:
            # Construct query
            query_parts = [title]
            if author:
                query_parts.append(author)
            query = ' '.join(query_parts)
            
            params = {'q': query}
            search_url = f"{self.catalog_base_url}/search?{urlencode(params)}"
            
            # Add delay
            time.sleep(self.delay)
            
            # Perform request
            response = self.scraper.get(search_url, timeout=30)
            response.raise_for_status()
            
            # Parse response
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get first result
            title_element = soup.find('a', class_='title')
            
            if title_element:
                result_title = title_element.get_text(strip=True)
                
                # Calculate similarity to verify it's a good match
                similarity = difflib.SequenceMatcher(None, 
                                                     title.lower(), 
                                                     result_title.lower()).ratio()
                
                # Require at least 60% similarity
                if similarity >= 0.6:
                    self.stats['fallback_matches'] += 1
                    return {
                        'found': True,
                        'catalog_url': urljoin(self.catalog_base_url, title_element.get('href', '')),
                        'title': result_title,
                        'match_type': 'fallback',
                        'similarity': similarity
                    }
            
            return None
        
        except requests.exceptions.RequestException as e:
            self.stats['errors'] += 1
            print(f"Error searching by title/author: {e}")
            return None
    
    def match_record(self, isbn: Optional[str], title: str, author: str = '') -> Dict[str, any]:
        """
        Attempt to match a record, trying ISBN first then fallback.
        
        Args:
            isbn: Normalized ISBN (can be None)
            title: Book title
            author: Author name
            
        Returns:
            Dictionary with match results
        """
        result = {
            'found': False,
            'catalog_url': '',
            'match_type': 'none',
            'isbn_used': isbn,
            'title': title,
            'author': author
        }
        
        # Try ISBN match first
        if isbn:
            match = self.search_by_isbn(isbn)
            if match:
                result.update(match)
                return result
        
        # Fallback to title/author
        match = self.search_by_title_author(title, author)
        if match:
            result.update(match)
            return result
        
        # No match found
        self.stats['no_match'] += 1
        return result
    
    def get_statistics(self) -> Dict[str, int]:
        """Return matching statistics."""
        return self.stats.copy()


class FallbackMatcher:
    """
    Implements fuzzy matching strategies for incomplete records.
    """
    
    @staticmethod
    def calculate_title_similarity(title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles.
        
        Args:
            title1: First title
            title2: Second title
            
        Returns:
            Similarity score between 0 and 1
        """
        # Normalize titles
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()
        
        # Use sequence matcher
        return difflib.SequenceMatcher(None, t1, t2).ratio()
    
    @staticmethod
    def normalize_author_name(author: str) -> str:
        """
        Normalize author name for matching (handle name order variations).
        
        Args:
            author: Author name
            
        Returns:
            Normalized author name
        """
        if not author:
            return ""
        
        # Remove common prefixes/suffixes
        prefixes = ['dr.', 'prof.', 'mr.', 'ms.', 'mrs.']
        author_clean = author.lower().strip()
        
        for prefix in prefixes:
            if author_clean.startswith(prefix):
                author_clean = author_clean[len(prefix):].strip()
        
        return author_clean
    
    @staticmethod
    def match_by_metadata(record: Dict, catalog_records: list) -> Optional[Dict]:
        """
        Match a record against catalog using metadata fields.
        
        Args:
            record: Dictionary with 'title', 'author' fields
            catalog_records: List of catalog records to match against
            
        Returns:
            Best matching catalog record or None
        """
        title = record.get('title', '')
        author = FallbackMatcher.normalize_author_name(record.get('author', ''))
        
        if not title:
            return None
        
        best_match = None
        best_score = 0.0
        
        for catalog_record in catalog_records:
            catalog_title = catalog_record.get('title', '')
            catalog_author = FallbackMatcher.normalize_author_name(
                catalog_record.get('author', '')
            )
            
            # Calculate title similarity
            title_sim = FallbackMatcher.calculate_title_similarity(title, catalog_title)
            
            # Calculate author similarity if both present
            author_sim = 0.0
            if author and catalog_author:
                author_sim = FallbackMatcher.calculate_title_similarity(author, catalog_author)
            
            # Combined score (weighted)
            score = 0.7 * title_sim + 0.3 * author_sim
            
            if score > best_score and score >= 0.6:  # Threshold
                best_score = score
                best_match = {
                    **catalog_record,
                    'match_score': score,
                    'title_similarity': title_sim,
                    'author_similarity': author_sim
                }
        
        return best_match


def create_mock_catalog():
    """Create mock catalog for testing."""
    return [
        {
            'isbn': '9780195153071',
            'title': 'Islamic Philosophy: A Beginner\'s Guide',
            'author': 'Ibn Sina',
            'catalog_id': 'CAT001'
        },
        {
            'isbn': '9786001002540',
            'title': 'مجموعة الحديث الشريف',
            'author': 'المؤلف العربي',
            'catalog_id': 'CAT002'
        },
        {
            'isbn': '9781234567890',
            'title': 'Digital Libraries and Islamic Studies',
            'author': 'Smith, John',
            'catalog_id': 'CAT003'
        }
    ]


if __name__ == "__main__":
    print("=" * 60)
    print("Catalog Matching Module - Demo")
    print("=" * 60)
    
    # Create mock catalog
    mock_catalog = create_mock_catalog()
    
    # Test fallback matching
    print("\nTesting Fallback Matching:")
    print("-" * 60)
    
    test_records = [
        {
            'title': 'Islamic Philosophy: A Beginners Guide',  # Slight variation
            'author': 'Ibn Sina'
        },
        {
            'title': 'Digital Libraries',  # Partial title
            'author': 'John Smith'  # Name order reversed
        },
        {
            'title': 'Unknown Book Title',
            'author': 'Unknown Author'
        }
    ]
    
    matcher = FallbackMatcher()
    
    for i, record in enumerate(test_records, 1):
        print(f"\nTest Record {i}:")
        print(f"  Title: {record['title']}")
        print(f"  Author: {record['author']}")
        
        match = matcher.match_by_metadata(record, mock_catalog)
        
        if match:
            print(f"  ✓ MATCH FOUND:")
            print(f"    Catalog Title: {match['title']}")
            print(f"    Match Score: {match['match_score']:.2f}")
            print(f"    Title Similarity: {match['title_similarity']:.2f}")
            print(f"    Author Similarity: {match['author_similarity']:.2f}")
        else:
            print(f"  ✗ NO MATCH")
    
    print("\n" + "=" * 60)
