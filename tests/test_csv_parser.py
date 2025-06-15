"""Test CSV parser service."""

from pathlib import Path

import pytest

from backend.models import DocumentClass
from backend.services.csv_parser import CSVMetadataParser


@pytest.fixture
def csv_parser():
    """Create CSV parser instance."""
    return CSVMetadataParser()


def test_detect_csv_type(csv_parser):
    """Test CSV type detection."""
    assert csv_parser.detect_csv_type(Path("inventario_Artom_Prandi.csv")) == "inventario"
    assert csv_parser.detect_csv_type(Path("operaartom.csv")) == "opera"
    assert csv_parser.detect_csv_type(Path("suartom.csv")) == "su"
    assert csv_parser.detect_csv_type(Path("unknown.csv")) == "inventario"  # default


def test_detect_document_class(csv_parser):
    """Test document class detection."""
    assert csv_parser.detect_document_class(Path("inventario_Artom_Prandi.csv")) == DocumentClass.SUBJECT_LIBRARY
    assert csv_parser.detect_document_class(Path("operaartom.csv")) == DocumentClass.AUTHORED_BY_SUBJECT
    assert csv_parser.detect_document_class(Path("suartom.csv")) == DocumentClass.ABOUT_SUBJECT


def test_clean_text(csv_parser):
    """Test text cleaning."""
    assert csv_parser.clean_text("  hello world  ") == "hello world"
    assert csv_parser.clean_text('"quoted text"') == "quoted text"
    assert csv_parser.clean_text("multiple   spaces") == "multiple spaces"
    assert csv_parser.clean_text(None) == ""
    assert csv_parser.clean_text("") == ""


def test_parse_year(csv_parser):
    """Test year parsing."""
    assert csv_parser.parse_year("1920") == 1920
    assert csv_parser.parse_year("c1920") == 1920
    assert csv_parser.parse_year("1920-1925") == 1920
    assert csv_parser.parse_year("s.d.") is None
    assert csv_parser.parse_year("") is None
    assert csv_parser.parse_year("invalid") is None


def test_parse_content_files(csv_parser):
    """Test content file parsing."""
    assert csv_parser.parse_content_files("file1.pdf") == ["file1.pdf"]
    assert csv_parser.parse_content_files("file1.pdf, file2.pdf") == ["file1.pdf", "file2.pdf"]
    assert csv_parser.parse_content_files("") == []
    assert csv_parser.parse_content_files(None) == []


@pytest.mark.asyncio
async def test_parse_csv_inventario():
    """Test parsing inventario CSV file."""
    csv_path = Path("source_data/inventario_Artom_Prandi.csv")
    
    if not csv_path.exists():
        pytest.skip("CSV file not found")
    
    parser = CSVMetadataParser()
    documents, errors = parser.parse_csv(csv_path)
    
    assert len(documents) > 0
    assert isinstance(errors, list)
    
    # Check first document
    doc = documents[0]
    assert doc.title
    assert doc.document_class == DocumentClass.SUBJECT_LIBRARY
    assert "csv_source" in doc.extra_metadata
    assert "content_files" in doc.extra_metadata


@pytest.mark.asyncio
async def test_parse_csv_opera():
    """Test parsing opera CSV file."""
    csv_path = Path("source_data/operaartom.csv")
    
    if not csv_path.exists():
        pytest.skip("CSV file not found")
    
    parser = CSVMetadataParser()
    documents, errors = parser.parse_csv(csv_path)
    
    assert len(documents) > 0
    
    # Check first document
    doc = documents[0]
    assert doc.title
    assert doc.document_class == DocumentClass.AUTHORED_BY_SUBJECT 