"""
Setup script for ISBN Normalization Pipeline
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="isbn-normalization-pipeline",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@institution.edu",
    description="Automated extraction and normalization of ISBNs for multilingual digital libraries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/isbn-normalization-pipeline",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "requests>=2.26.0",
        "beautifulsoup4>=4.10.0",
        "cloudscraper>=1.2.58",
        "lxml>=4.6.3",
        "tqdm>=4.62.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
        "excel": [
            "openpyxl>=3.0.9",
            "xlrd>=2.0.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "isbn-pipeline=pipeline_main:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/isbn-normalization-pipeline/issues",
        "Source": "https://github.com/yourusername/isbn-normalization-pipeline",
        "Paper": "https://doi.org/your-paper-doi",
    },
)
