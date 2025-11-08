#!/bin/bash

# ISBN Normalization Pipeline - Quick Start Script
# This script sets up the environment and runs a demo

echo "=============================================="
echo "ISBN Normalization Pipeline - Quick Start"
echo "=============================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.8"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "Error: Python $required_version or higher is required"
    echo "Current version: $python_version"
    exit 1
fi
echo "✓ Python $python_version detected"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p data output tests examples
echo "✓ Directories created"
echo ""

# Run demo
echo "=============================================="
echo "Running Demo"
echo "=============================================="
echo ""

# Run the pipeline demo
echo "1. Testing ISBN Normalization..."
python3 isbn_pipeline.py
echo ""

echo "2. Testing Catalog Matching..."
python3 catalog_matcher.py
echo ""

# Run tests
echo "=============================================="
echo "Running Tests"
echo "=============================================="
echo ""
pytest tests/ -v --tb=short

# Display next steps
echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Prepare your input CSV file with columns: filepath, raw_isbn, title, author"
echo "2. Run the pipeline:"
echo "   python pipeline_main.py --input your_data.csv --output-dir output"
echo ""
echo "3. For catalog matching, add --catalog-url:"
echo "   python pipeline_main.py --input your_data.csv --catalog-url https://catalog.org"
echo ""
echo "4. View results in the output/ directory"
echo ""
echo "For more information, see README.md"
echo "=============================================="
