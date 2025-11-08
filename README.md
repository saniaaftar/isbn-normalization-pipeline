
# ISBN Extraction and Normalization Pipeline

An automated pipeline for extracting, normalizing, and validating ISBNs from multilingual digital library metadata, with special focus on Arabic-script documents and OCR noise handling.

## 📄 Paper Reference

This implementation accompanies the paper:

**"The Codes Talk: Automated Extraction and Normalization of ISBNs for Metadata Integration"**  
Published at: JCDL (ACM/IEEE Joint Conference on Digital Libraries)

## 🎯 Features

- **Multilingual Support**: Handles Arabic-Indic and Persian numerals alongside Western numerals
- **OCR Error Correction**: Character-level substitution with checksum validation
- **Bidirectionality Handling**: Corrects direction issues in mixed Arabic-Latin text
- **ISBN Validation**: MOD11 (ISBN-10) and MOD10 (ISBN-13) checksum algorithms
- **Fallback Matching**: Title and author-based matching when ISBNs are missing
- **Catalog Integration**: Automated querying against library catalogs
- **Scalable Design**: Processes large datasets with progress tracking

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/isbn-normalization-pipeline.git
cd isbn-normalization-pipeline

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from isbn_pipeline import ISBNNormalizer

# Initialize normalizer
normalizer = ISBNNormalizer()

# Normalize an ISBN
raw_isbn = "ردمك: ٩٧٨٦٠٠١٠٠٢٥٤٠"
clean_isbn = normalizer.normalize_isbn(raw_isbn)
print(clean_isbn)  # Output: 9786001002540
```

### Command-Line Interface

```bash
# Process a dataset
python pipeline_main.py \
    --input data/books.csv \
    --isbn-column raw_isbn \
    --output-dir output \
    --output-format csv

# With catalog matching
python pipeline_main.py \
    --input data/books.csv \
    --catalog-url https://library-catalog.org \
    --output-format excel
```

## 📊 Pipeline Architecture

```
┌─────────────────┐
│ Book Metadata   │
│ (PDF/Text)      │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Metadata Extraction │
│ - Title             │
│ - Author            │
│ - ISBN Candidate    │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ ISBN Normalization  │
│ - Numeral Conversion│
│ - Prefix Removal    │
│ - Character Cleaning│
│ - Bidirectionality  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Validation          │
│ - Length Check      │
│ - Checksum (MOD11)  │
│ - Checksum (MOD10)  │
└────────┬────────────┘
         │
         ▼
    ┌───┴────┐
    │ Valid? │
    └───┬────┘
        │
    No  │  Yes
    ┌───┼────┐
    │   │    │
    ▼   │    ▼
┌───────┴──┐ ┌──────────────┐
│ Character│ │ Catalog      │
│ Correction│ │ Matching     │
└───────┬──┘ └──────┬───────┘
        │           │
        └─────┬─────┘
              │
              ▼
     ┌────────────────┐
     │ Fallback       │
     │ Title/Author   │
     │ Matching       │
     └────────┬───────┘
              │
              ▼
     ┌────────────────┐
     │ Final Results  │
     └────────────────┘
```

## 🔧 Core Components

### 1. ISBN Normalizer (`isbn_pipeline.py`)

Handles the core ISBN normalization logic:

- **Numeral Conversion**: Converts Arabic-Indic (٠-٩) and Persian (۰-۹) to ASCII (0-9)
- **Prefix Removal**: Strips "ISBN", "ردمك", and variations
- **Character Cleaning**: Removes hyphens, spaces, and non-digit characters
- **Validation**: MOD11 and MOD10 checksum algorithms
- **Error Correction**: Character-level substitution for OCR errors

**Example:**

```python
from isbn_pipeline import ISBNNormalizer

normalizer = ISBNNormalizer()

# Handle OCR errors
noisy_isbn = "978600100254ه"  # 'ه' mistaken for '0'
clean = normalizer.normalize_isbn(noisy_isbn)
# Output: 9786001002540 (corrected and validated)

# Handle Arabic-Indic numerals
arabic_isbn = "٩٧٨٦٠٠١٠٠٢٥٤٠"
clean = normalizer.normalize_isbn(arabic_isbn)
# Output: 9786001002540
```

### 2. Catalog Matcher (`catalog_matcher.py`)

Implements catalog querying and fallback strategies:

- **ISBN Search**: Direct lookup in library catalogs
- **Fallback Matching**: Title and author-based similarity matching
- **Rate Limiting**: Configurable delays to avoid overwhelming servers
- **Anti-bot Bypass**: Uses cloudscraper for protected catalogs

**Example:**

```python
from catalog_matcher import CatalogMatcher

matcher = CatalogMatcher("https://library-catalog.org")

result = matcher.match_record(
    isbn="9780195153071",
    title="Islamic Philosophy",
    author="Ibn Sina"
)

if result['found']:
    print(f"Match found: {result['catalog_url']}")
```

### 3. Main Pipeline (`pipeline_main.py`)

Orchestrates the complete workflow:

- **Batch Processing**: Handles large datasets efficiently
- **Progress Tracking**: Real-time progress bars
- **Multiple Formats**: Supports CSV, Excel, and JSON input/output
- **Comprehensive Reporting**: Detailed statistics and metrics

## 📈 Performance Metrics

Based on evaluation with 2,470 Arabic-script book records:

| Metric | Baseline | Our Pipeline |
|--------|----------|--------------|
| Precision | 61.0% | **90.4%** |
| Recall | 58.0% | **92.5%** |
| F1-Score | 59.3% | **87.9%** |
| Accuracy | 65.0% | **84.9%** |

### Key Improvements

- **+29.4%** precision improvement through numeral conversion and error correction
- **+34.5%** recall improvement via fallback matching strategies
- **+28.6%** F1-score improvement overall
- **504 records** recovered that lacked valid ISBNs

## 📋 Input Data Format

The pipeline expects CSV or Excel files with the following columns:

```csv
filepath,raw_isbn,title,author
/path/to/book1.pdf,ISBN: 978-0-19-515307-1,Islamic Philosophy,Ibn Sina
/path/to/book2.pdf,ردمك: ٩٧٨٦٠٠١٠٠٢٥٤٠,مجموعة الحديث,المؤلف
/path/to/book3.pdf,978600100254ه,Arabic Text,,,
```

**Required Columns:**
- `filepath`: Path to the PDF file
- `raw_isbn`: Raw ISBN string (can contain noise)

**Optional Columns:**
- `title`: Book title (for fallback matching)
- `author`: Author name (for fallback matching)
- `ocr_text`: Full OCR text if available

## 📤 Output Format

### Results File

```csv
filepath,filename,raw_isbn,clean_isbn,title,author,catalog_found,catalog_url,match_type
/data/book1.pdf,book1.pdf,ISBN: 978-0-19-515307-1,9780195153071,Islamic Philosophy,Ibn Sina,true,https://catalog.org/book/123,isbn
/data/book2.pdf,book2.pdf,٩٧٨٦٠٠١٠٠٢٥٤٠,9786001002540,Arabic Book,Author,true,https://catalog.org/book/456,isbn
/data/book3.pdf,book3.pdf,,,,Unknown Title,,false,,none
```

### Statistics Report

```json
{
  "total_records": 2470,
  "isbn_extraction": {
    "valid_isbns": 1850,
    "corrected_isbns": 342,
    "failed": 150,
    "valid_rate": "74.9%",
    "correction_rate": "18.5%"
  },
  "catalog_matching": {
    "isbn_matches": 739,
    "fallback_matches": 104,
    "no_match": 504,
    "errors": 0,
    "match_rate": "34.1%"
  }
}
```

## 🛠️ Advanced Configuration

### Custom Confusion Dictionary

Extend the OCR error correction dictionary:

```python
from isbn_pipeline import ISBNNormalizer

normalizer = ISBNNormalizer()

# Add custom confusions
normalizer.CONFUSION_DICT.update({
    '৫': '5',  # Bengali digit
    'б': '6',  # Cyrillic character
})

isbn = normalizer.normalize_isbn("978б001002540")
```

### Custom Catalog Implementation

Implement your own catalog interface:

```python
from catalog_matcher import CatalogMatcher

class CustomCatalogMatcher(CatalogMatcher):
    def search_by_isbn(self, isbn: str):
        # Your custom implementation
        # Connect to your specific catalog system
        pass
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run specific test
python -m pytest tests/test_isbn_normalizer.py
```

## 📊 Sample Dataset

A sample dataset is included for testing:

```python
# Run demo
python isbn_pipeline.py

# Run catalog matcher demo
python catalog_matcher.py
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Citation

If you use this code in your research, please cite our paper:

```bibtex
@inproceedings{aftar2025,
  title={The Codes Talk: Automated Extraction and Normalization of ISBNs for Metadata Integration},
  author={Sania Aftar, Riccardo Amerigo Vigliermo and Sonia Bergamaschi},
  booktitle={ACM/IEEE Joint Conference on Digital Libraries (JCDL)},
  year={2025}
}
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Digital Maktaba Project and ITSERR Infrastructure
- La Pira Library Catalog for evaluation dataset
- Anthropic's Claude for development assistance

## 📧 Contact

- **Author**: Sania Aftar
- **Email**: sania.aftar@unimore.it
- **Project Link**: https://github.com/saniaaftar/isbn-normalization-pipeline

## 🔗 Related Projects

- [Qwen2-VL](https://github.com/QwenLM/Qwen-VL) - Vision-Language Model for page selection
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Open-source OCR engine
- [cloudscraper](https://github.com/VeNoMouS/cloudscraper) - Bypass anti-bot protection

---

**Note**: This implementation is part of ongoing research in digital humanities and cultural heritage preservation. For questions about the underlying methodology, please refer to the published paper.
