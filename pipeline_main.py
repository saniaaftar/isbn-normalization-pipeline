"""
Main Pipeline Orchestrator
===========================

Coordinates the complete ISBN extraction, normalization, and catalog matching workflow.
"""

import pandas as pd
import argparse
from pathlib import Path
from typing import List, Dict
import json
from tqdm import tqdm

from isbn_pipeline import ISBNNormalizer, MetadataExtractor
from catalog_matcher import CatalogMatcher, FallbackMatcher


class ISBNPipeline:
    """
    Main pipeline coordinator for ISBN extraction and catalog matching.
    """
    
    def __init__(self, catalog_url: str = None, output_dir: str = 'output'):
        """
        Initialize the complete pipeline.
        
        Args:
            catalog_url: URL of the library catalog to query
            output_dir: Directory for output files
        """
        self.normalizer = ISBNNormalizer()
        self.extractor = MetadataExtractor()
        self.catalog_matcher = CatalogMatcher(catalog_url) if catalog_url else None
        self.fallback_matcher = FallbackMatcher()
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = []
    
    def process_file(self, filepath: str, raw_isbn: str = None, 
                    ocr_text: str = None) -> Dict:
        """
        Process a single file through the pipeline.
        
        Args:
            filepath: Path to the PDF file
            raw_isbn: Raw ISBN string (if pre-extracted)
            ocr_text: OCR text from document (if pre-extracted)
            
        Returns:
            Dictionary with processing results
        """
        result = {
            'filepath': filepath,
            'filename': Path(filepath).name,
            'raw_isbn': raw_isbn,
            'clean_isbn': None,
            'title': '',
            'author': '',
            'catalog_found': False,
            'catalog_url': '',
            'match_type': 'none'
        }
        
        # Extract metadata from filename
        filename_metadata = self.extractor.extract_from_filename(result['filename'])
        result['title'] = filename_metadata.get('title', '')
        result['author'] = filename_metadata.get('author', '')
        
        # If ISBN provided in filename, use it
        if not raw_isbn and filename_metadata.get('isbn'):
            raw_isbn = filename_metadata['isbn']
            result['raw_isbn'] = raw_isbn
        
        # Extract from OCR text if provided
        if ocr_text and not raw_isbn:
            text_metadata = self.extractor.extract_from_text(ocr_text)
            if text_metadata.get('isbn'):
                raw_isbn = text_metadata['isbn']
                result['raw_isbn'] = raw_isbn
            # Update title/author if not already set
            if not result['title']:
                result['title'] = text_metadata.get('title', '')
            if not result['author']:
                result['author'] = text_metadata.get('author', '')
        
        # Normalize ISBN
        if raw_isbn:
            clean_isbn = self.normalizer.normalize_isbn(raw_isbn)
            result['clean_isbn'] = clean_isbn
        
        # Catalog matching (if matcher available)
        if self.catalog_matcher:
            match_result = self.catalog_matcher.match_record(
                result['clean_isbn'],
                result['title'],
                result['author']
            )
            result['catalog_found'] = match_result['found']
            result['catalog_url'] = match_result.get('catalog_url', '')
            result['match_type'] = match_result.get('match_type', 'none')
        
        self.results.append(result)
        return result
    
    def process_dataset(self, input_file: str, 
                       isbn_column: str = 'raw_isbn',
                       filepath_column: str = 'filepath',
                       ocr_column: str = None) -> pd.DataFrame:
        """
        Process a complete dataset from CSV/Excel.
        
        Args:
            input_file: Path to input file (CSV or Excel)
            isbn_column: Name of column containing raw ISBNs
            filepath_column: Name of column containing file paths
            ocr_column: Name of column containing OCR text (optional)
            
        Returns:
            DataFrame with results
        """
        # Load dataset
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        elif input_file.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(input_file)
        else:
            raise ValueError("Input file must be CSV or Excel format")
        
        print(f"Processing {len(df)} records...")
        
        # Process each record
        for idx, row in tqdm(df.iterrows(), total=len(df)):
            filepath = row.get(filepath_column, f"record_{idx}")
            raw_isbn = row.get(isbn_column, None)
            ocr_text = row.get(ocr_column, None) if ocr_column else None
            
            self.process_file(filepath, raw_isbn, ocr_text)
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(self.results)
        
        return results_df
    
    def generate_report(self) -> Dict:
        """
        Generate comprehensive statistics report.
        
        Returns:
            Dictionary with statistics
        """
        total_records = len(self.results)
        
        if total_records == 0:
            return {'error': 'No records processed'}
        
        # ISBN statistics
        isbn_stats = self.normalizer.get_statistics()
        
        # Catalog matching statistics
        catalog_stats = {'isbn_matches': 0, 'fallback_matches': 0, 'no_match': 0}
        if self.catalog_matcher:
            catalog_stats = self.catalog_matcher.get_statistics()
        
        # Calculate percentages
        valid_isbn_rate = (isbn_stats['valid_isbns'] / total_records) * 100
        correction_rate = (isbn_stats['corrected_isbns'] / isbn_stats['valid_isbns'] * 100 
                          if isbn_stats['valid_isbns'] > 0 else 0)
        
        match_rate = ((catalog_stats['isbn_matches'] + catalog_stats['fallback_matches']) 
                     / total_records) * 100
        
        report = {
            'total_records': total_records,
            'isbn_extraction': {
                'valid_isbns': isbn_stats['valid_isbns'],
                'corrected_isbns': isbn_stats['corrected_isbns'],
                'failed': isbn_stats['failed_validation'],
                'valid_rate': f"{valid_isbn_rate:.1f}%",
                'correction_rate': f"{correction_rate:.1f}%"
            },
            'catalog_matching': {
                'isbn_matches': catalog_stats['isbn_matches'],
                'fallback_matches': catalog_stats['fallback_matches'],
                'no_match': catalog_stats['no_match'],
                'errors': catalog_stats.get('errors', 0),
                'match_rate': f"{match_rate:.1f}%"
            }
        }
        
        return report
    
    def save_results(self, output_format: str = 'csv'):
        """
        Save processing results to file.
        
        Args:
            output_format: Output format ('csv', 'excel', 'json')
        """
        if not self.results:
            print("No results to save")
            return
        
        df = pd.DataFrame(self.results)
        
        if output_format == 'csv':
            output_path = self.output_dir / 'isbn_pipeline_results.csv'
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
        elif output_format == 'excel':
            output_path = self.output_dir / 'isbn_pipeline_results.xlsx'
            df.to_excel(output_path, index=False)
        elif output_format == 'json':
            output_path = self.output_dir / 'isbn_pipeline_results.json'
            df.to_json(output_path, orient='records', force_ascii=False, indent=2)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        print(f"Results saved to: {output_path}")
        
        # Save report
        report = self.generate_report()
        report_path = self.output_dir / 'pipeline_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Report saved to: {report_path}")


def main():
    """Command-line interface for the pipeline."""
    parser = argparse.ArgumentParser(
        description='ISBN Extraction and Normalization Pipeline'
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input CSV or Excel file with book metadata'
    )
    
    parser.add_argument(
        '--isbn-column',
        type=str,
        default='raw_isbn',
        help='Name of column containing raw ISBNs (default: raw_isbn)'
    )
    
    parser.add_argument(
        '--filepath-column',
        type=str,
        default='filepath',
        help='Name of column containing file paths (default: filepath)'
    )
    
    parser.add_argument(
        '--ocr-column',
        type=str,
        default=None,
        help='Name of column containing OCR text (optional)'
    )
    
    parser.add_argument(
        '--catalog-url',
        type=str,
        default=None,
        help='Base URL of library catalog for matching'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Output directory for results (default: output)'
    )
    
    parser.add_argument(
        '--output-format',
        type=str,
        choices=['csv', 'excel', 'json'],
        default='csv',
        help='Output format (default: csv)'
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    print("=" * 60)
    print("ISBN Extraction and Normalization Pipeline")
    print("=" * 60)
    print(f"\nInput file: {args.input}")
    print(f"Output directory: {args.output_dir}")
    if args.catalog_url:
        print(f"Catalog URL: {args.catalog_url}")
    print()
    
    pipeline = ISBNPipeline(
        catalog_url=args.catalog_url,
        output_dir=args.output_dir
    )
    
    # Process dataset
    try:
        results_df = pipeline.process_dataset(
            args.input,
            isbn_column=args.isbn_column,
            filepath_column=args.filepath_column,
            ocr_column=args.ocr_column
        )
        
        # Save results
        pipeline.save_results(output_format=args.output_format)
        
        # Display report
        print("\n" + "=" * 60)
        print("Processing Report")
        print("=" * 60)
        report = pipeline.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
