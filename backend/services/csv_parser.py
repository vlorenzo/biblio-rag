"""CSV metadata parser service."""

import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from loguru import logger

from backend.models import DocumentClass, DocumentCreate


class CSVMetadataParser:
    """Parser for CSV metadata files."""

    # Column mapping for different CSV formats
    COLUMN_MAPPINGS = {
        "inventario": {
            "title": "Titolo",
            "author": "Autore", 
            "publication_year": "Anno",
            "publisher": "Editore",
            "description": "Note",
            "content_file": "File",
            "physical_description": "Descrizione fisica",
            "imprint": "Impronta",
        },
        "opera": {
            "title": "Titolo",
            "author": "Autore",
            "publication_year": "Anno", 
            "publisher": "Editore",
            "description": "Note",
            "content_file": "File",
            "editor": "Curatore",
            "place": "Luogo",
            "series": "Collana / Periodico",
            "volume": "Volume / Fascicolo",
            "pages": "Pagine / Dimensioni",
            "isbn": "ISBN",
        },
        "su": {
            "title": "Titolo",
            "author": "Autore",
            "publication_year": "Anno",
            "publisher": "Editore", 
            "description": "Note",
            "content_file": "File",
            "editor": "Curatore",
            "place": "Luogo",
            "series": "Collana / Periodico",
            "volume": "Volume / Fascicolo",
            "pages": "Pagine / Dimensioni",
            "isbn": "ISBN",
        },
    }

    def __init__(self, content_base_path: Optional[Path] = None):
        """Initialize parser with optional content base path."""
        self.content_base_path = content_base_path or Path("source_data/content")

    def detect_csv_type(self, csv_path: Path) -> str:
        """Detect CSV type from filename."""
        filename = csv_path.stem.lower()
        
        if "inventario" in filename:
            return "inventario"
        elif "opera" in filename:
            return "opera"
        elif filename.startswith("su"):
            return "su"
        else:
            logger.warning(f"Unknown CSV type for {csv_path}, defaulting to 'inventario'")
            return "inventario"

    def detect_document_class(self, csv_path: Path) -> DocumentClass:
        """Detect document class from CSV filename."""
        filename = csv_path.stem.lower()
        
        if "inventario" in filename:
            return DocumentClass.SUBJECT_LIBRARY
        elif "opera" in filename:
            return DocumentClass.AUTHORED_BY_SUBJECT
        elif filename.startswith("su"):
            return DocumentClass.ABOUT_SUBJECT
        else:
            logger.warning(f"Unknown document class for {csv_path}, defaulting to SUBJECT_LIBRARY")
            return DocumentClass.SUBJECT_LIBRARY

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if pd.isna(text) or text is None:
            return ""
        
        # Convert to string and strip
        text = str(text).strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove quotes if they wrap the entire string
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        return text

    def parse_year(self, year_str: str) -> Optional[int]:
        """Parse publication year from string."""
        if pd.isna(year_str) or not year_str:
            return None
            
        year_str = str(year_str).strip()
        
        # Look for a 4-digit year even if it is prefixed by a letter like "c" (circa)
        year_match = re.search(r'(1[5-9]\d{2}|20\d{2})', year_str)
        if year_match:
            return int(year_match.group(1))
        
        # Handle special cases like "s.d." (sine data)
        if year_str.lower() in ['s.d.', 'sd', 'n.d.', 'nd', '']:
            return None
            
        logger.warning(f"Could not parse year: {year_str}")
        return None

    def parse_content_files(self, file_str: str) -> List[str]:
        """Parse content file references."""
        if pd.isna(file_str) or not file_str:
            return []
        
        file_str = self.clean_text(file_str)
        
        # Handle multiple files separated by commas
        files = [f.strip() for f in file_str.split(',')]
        
        # Filter out empty strings
        files = [f for f in files if f]
        
        return files

    def build_metadata_dict(self, row: pd.Series, csv_type: str) -> Dict[str, str]:
        """Build additional metadata dictionary from row."""
        mapping = self.COLUMN_MAPPINGS[csv_type]
        metadata = {}
        
        # Add all non-standard fields to metadata
        for col in row.index:
            if col not in mapping.values() and pd.notna(row[col]) and row[col] != "":
                metadata[col] = self.clean_text(str(row[col]))
        
        # Add specific fields based on CSV type
        if csv_type in ["opera", "su"]:
            for field in ["editor", "place", "series", "volume", "pages", "isbn"]:
                if field in mapping and mapping[field] in row.index:
                    value = self.clean_text(str(row[mapping[field]]))
                    if value:
                        metadata[field] = value
        
        if csv_type == "inventario":
            for field in ["physical_description", "imprint"]:
                if field in mapping and mapping[field] in row.index:
                    value = self.clean_text(str(row[mapping[field]]))
                    if value:
                        metadata[field] = value
        
        return metadata

    def parse_csv(self, csv_path: Path) -> Tuple[List[DocumentCreate], List[str]]:
        """Parse CSV file and return documents and errors."""
        logger.info(f"Parsing CSV file: {csv_path}")
        
        try:
            # Read CSV with proper encoding detection
            df = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_path, encoding='latin-1')
            except Exception as e:
                return [], [f"Failed to read CSV file: {e}"]
        
        csv_type = self.detect_csv_type(csv_path)
        document_class = self.detect_document_class(csv_path)
        mapping = self.COLUMN_MAPPINGS[csv_type]
        
        documents = []
        errors = []
        
        logger.info(f"Processing {len(df)} rows from {csv_path}")
        
        for idx, row in df.iterrows():
            try:
                # Skip empty rows
                if row.isna().all():
                    continue
                
                # Extract basic fields
                title = self.clean_text(str(row.get(mapping["title"], "")))
                if not title:
                    errors.append(f"Row {idx + 1}: Missing title")
                    continue
                
                author = self.clean_text(str(row.get(mapping["author"], "")))
                if not author:
                    author = None
                
                publisher = self.clean_text(str(row.get(mapping["publisher"], "")))
                if not publisher:
                    publisher = None
                
                description = self.clean_text(str(row.get(mapping["description"], "")))
                if not description:
                    description = None
                
                # Parse year
                year_str = row.get(mapping["publication_year"], "")
                publication_year = self.parse_year(str(year_str))
                
                # Parse content files
                file_str = row.get(mapping["content_file"], "")
                content_files = self.parse_content_files(str(file_str))
                
                # Build additional metadata
                metadata = self.build_metadata_dict(row, csv_type)
                metadata["csv_source"] = csv_path.name
                metadata["csv_row"] = idx + 1
                metadata["content_files"] = content_files
                
                # Create document
                document = DocumentCreate(
                    title=title,
                    author=author,
                    document_class=document_class,
                    publication_year=publication_year,
                    publisher=publisher,
                    description=description,
                    extra_metadata=metadata,
                )
                
                documents.append(document)
                
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
                logger.error(f"Error processing row {idx + 1}: {e}")
        
        logger.info(f"Successfully parsed {len(documents)} documents with {len(errors)} errors")
        return documents, errors

    def find_content_files(self, content_file_refs: List[str]) -> List[Tuple[str, Path]]:
        """Find actual content files from references."""
        found_files = []
        
        for ref in content_file_refs:
            if not ref:
                continue
            
            # --- New rule: search for files starting with base name and .md/.txt ---
            base_name = Path(ref).stem
            candidates = list(self.content_base_path.glob(f"{base_name}*.md")) + \
                         list(self.content_base_path.glob(f"{base_name}*.txt"))
            if candidates:
                logger.info(f"[find_content_files] Using new rule: found {candidates[0]} for ref {ref}")
                found_files.append((ref, candidates[0]))
                continue
            
            # Try different extensions and paths (existing logic)
            possible_paths = [
                self.content_base_path / ref,
                self.content_base_path / f"{Path(ref).stem}.txt",
                self.content_base_path / f"{Path(ref).stem}.md",
            ]
            
            for path in possible_paths:
                if path.exists() and path.is_file():
                    found_files.append((ref, path))
                    break
            else:
                logger.warning(f"Content file not found: {ref}")
        
        return found_files

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


def parse_csv_metadata(csv_path: Path, content_base_path: Optional[Path] = None) -> Tuple[List[DocumentCreate], List[str]]:
    """Convenience function to parse CSV metadata."""
    parser = CSVMetadataParser(content_base_path)
    return parser.parse_csv(csv_path) 