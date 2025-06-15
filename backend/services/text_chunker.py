"""Text chunking service for document processing."""

import hashlib
import re
from pathlib import Path
from typing import List, Optional, Tuple

from loguru import logger


class TextChunk:
    """Represents a text chunk."""
    
    def __init__(
        self,
        text: str,
        sequence_number: int,
        start_char: int = 0,
        end_char: int = 0,
        token_count: Optional[int] = None,
    ):
        self.text = text
        self.sequence_number = sequence_number
        self.start_char = start_char
        self.end_char = end_char
        self.token_count = token_count or self.estimate_tokens()
        self.text_hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of cleaned text."""
        cleaned_text = self.clean_text(self.text)
        return hashlib.sha256(cleaned_text.encode('utf-8')).hexdigest()
    
    def estimate_tokens(self) -> int:
        """Estimate token count (rough approximation)."""
        # Simple approximation: ~4 characters per token for English text
        return max(1, len(self.text) // 4)
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text for consistent hashing."""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        return text


class TextChunker:
    """Service for chunking text documents."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        min_chunk_size: int = 50,
    ):
        """Initialize chunker with parameters."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def load_text_file(self, file_path: Path) -> str:
        """Load text from file with encoding detection."""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                raise
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text before chunking."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = text.strip()
        
        return text
    
    def find_sentence_boundaries(self, text: str) -> List[int]:
        """Find sentence boundaries in text."""
        # Simple sentence boundary detection
        sentence_endings = re.finditer(r'[.!?]+\s+', text)
        boundaries = [0]  # Start of text
        
        for match in sentence_endings:
            boundaries.append(match.end())
        
        boundaries.append(len(text))  # End of text
        return sorted(set(boundaries))
    
    def find_paragraph_boundaries(self, text: str) -> List[int]:
        """Find paragraph boundaries in text."""
        paragraph_breaks = re.finditer(r'\n\s*\n', text)
        boundaries = [0]  # Start of text
        
        for match in paragraph_breaks:
            boundaries.append(match.end())
        
        boundaries.append(len(text))  # End of text
        return sorted(set(boundaries))
    
    def chunk_by_sliding_window(self, text: str) -> List[TextChunk]:
        """Chunk text using sliding window approach."""
        if len(text) <= self.chunk_size:
            return [TextChunk(text, 0, 0, len(text))]
        
        chunks = []
        sequence_number = 0
        start = 0
        
        # Find sentence boundaries for better chunking
        sentence_boundaries = self.find_sentence_boundaries(text)
        
        while start < len(text):
            # Calculate end position
            end = min(start + self.chunk_size, len(text))
            
            # Try to end at a sentence boundary if possible
            if end < len(text):
                # Find the last sentence boundary before or at the end position
                suitable_boundaries = [b for b in sentence_boundaries if start < b <= end]
                if suitable_boundaries:
                    end = suitable_boundaries[-1]
            
            # Extract chunk text
            chunk_text = text[start:end].strip()
            
            # Skip chunks that are too small (unless it's the last chunk)
            if len(chunk_text) >= self.min_chunk_size or end >= len(text):
                chunk = TextChunk(
                    text=chunk_text,
                    sequence_number=sequence_number,
                    start_char=start,
                    end_char=end,
                )
                chunks.append(chunk)
                sequence_number += 1
            
            # Move start position with overlap
            if end >= len(text):
                break
            
            # Calculate next start position with overlap
            overlap_start = max(start, end - self.chunk_overlap)
            
            # Try to start at a sentence boundary if possible
            suitable_start_boundaries = [b for b in sentence_boundaries if overlap_start <= b < end]
            if suitable_start_boundaries:
                start = suitable_start_boundaries[0]
            else:
                start = overlap_start
            
            # Ensure we make progress
            if start <= chunks[-1].start_char:
                start = chunks[-1].end_char
        
        logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
        return chunks
    
    def chunk_by_paragraphs(self, text: str) -> List[TextChunk]:
        """Chunk text by paragraphs, combining small ones."""
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        sequence_number = 0
        current_chunk = ""
        start_char = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed chunk size, finalize current chunk
            if current_chunk and len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                if len(current_chunk) >= self.min_chunk_size:
                    chunk = TextChunk(
                        text=current_chunk.strip(),
                        sequence_number=sequence_number,
                        start_char=start_char,
                        end_char=start_char + len(current_chunk),
                    )
                    chunks.append(chunk)
                    sequence_number += 1
                
                # Start new chunk
                current_chunk = paragraph
                start_char = text.find(paragraph, start_char)
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                    start_char = text.find(paragraph, start_char)
        
        # Add final chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunk = TextChunk(
                text=current_chunk.strip(),
                sequence_number=sequence_number,
                start_char=start_char,
                end_char=start_char + len(current_chunk),
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} paragraph-based chunks")
        return chunks
    
    def chunk_text(self, text: str, method: str = "sliding_window") -> List[TextChunk]:
        """Chunk text using specified method."""
        text = self.preprocess_text(text)
        
        if not text or len(text) < self.min_chunk_size:
            logger.warning("Text too short for chunking")
            return []
        
        if method == "sliding_window":
            return self.chunk_by_sliding_window(text)
        elif method == "paragraphs":
            return self.chunk_by_paragraphs(text)
        else:
            raise ValueError(f"Unknown chunking method: {method}")
    
    def chunk_file(self, file_path: Path, method: str = "sliding_window") -> List[TextChunk]:
        """Chunk a text file."""
        logger.info(f"Chunking file: {file_path}")
        
        text = self.load_text_file(file_path)
        return self.chunk_text(text, method)
    
    def create_full_document_chunk(self, text: str) -> TextChunk:
        """Create a single chunk from the entire document."""
        text = self.preprocess_text(text)
        return TextChunk(
            text=text,
            sequence_number=0,
            start_char=0,
            end_char=len(text),
        )
    
    def create_full_document_chunk_from_file(self, file_path: Path) -> TextChunk:
        """Create a single chunk from an entire file."""
        logger.info(f"Creating full document chunk from: {file_path}")
        
        text = self.load_text_file(file_path)
        return self.create_full_document_chunk(text)


def chunk_text_file(
    file_path: Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    method: str = "sliding_window",
    no_chunking: bool = False,
) -> List[TextChunk]:
    """Convenience function to chunk a text file."""
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    if no_chunking:
        return [chunker.create_full_document_chunk_from_file(file_path)]
    else:
        return chunker.chunk_file(file_path, method) 