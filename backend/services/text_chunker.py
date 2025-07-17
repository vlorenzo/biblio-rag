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
        logger.info(f"[chunker] Loading text file: {file_path}")
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info(f"[chunker] File loaded successfully: {len(content)} characters")
                return content
        except UnicodeDecodeError:
            logger.info(f"[chunker] UTF-8 failed, trying latin-1 encoding")
            try:
                # Fallback to latin-1
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                    logger.info(f"[chunker] File loaded with latin-1: {len(content)} characters")
                    return content
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                raise
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text before chunking."""
        logger.info(f"[chunker] Preprocessing text: {len(text)} characters")
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = text.strip()
        
        logger.info(f"[chunker] Text preprocessed: {len(text)} characters")
        return text
    

    
    def find_word_boundary_near(self, text: str, position: int, window: int = 50) -> int:
        """Find the nearest word boundary within a small window."""
        if position >= len(text):
            return len(text)
        
        # Look for whitespace within ±window characters
        start_search = max(0, position - window)
        end_search = min(len(text), position + window)
        
        # Find last whitespace before position
        for i in range(position, start_search - 1, -1):
            if text[i].isspace():
                return i + 1
        
        # If no whitespace found before, look after
        for i in range(position, end_search):
            if text[i].isspace():
                return i + 1
        
        return position  # Fallback to exact position
    
    def chunk_by_sliding_window(self, text: str) -> List[TextChunk]:
        """Simple and robust sliding window chunking."""
        logger.info(f"[chunker] Starting sliding window chunking: {len(text)} chars, chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")
        
        if len(text) <= self.chunk_size:
            logger.info(f"[chunker] Text fits in single chunk")
            return [TextChunk(text, 0, 0, len(text))]
        
        chunks = []
        start = 0
        sequence_number = 0
        
        # Calculate expected number of chunks for progress tracking
        expected_chunks = max(1, (len(text) - self.chunk_overlap) // (self.chunk_size - self.chunk_overlap))
        logger.info(f"[chunker] Expected to create approximately {expected_chunks} chunks")
        
        while start < len(text):
            # Calculate basic end position
            end = min(start + self.chunk_size, len(text))
            
            # Try to end at a word boundary for better readability (optional smart boundary)
            if end < len(text):
                word_boundary_end = self.find_word_boundary_near(text, end)
                # Only use word boundary if it's not too far from target
                if abs(word_boundary_end - end) <= 100:  # Within 100 chars is acceptable
                    end = word_boundary_end
            
            # Extract chunk text
            chunk_text = text[start:end].strip()
            
            # Create chunk if it's substantial enough
            if len(chunk_text) >= self.min_chunk_size or end >= len(text):
                chunk = TextChunk(
                    text=chunk_text,
                    sequence_number=sequence_number,
                    start_char=start,
                    end_char=end,
                )
                chunks.append(chunk)
                sequence_number += 1
                
                # Progress logging every 100 chunks
                if len(chunks) % 100 == 0:
                    progress = (len(chunks) / expected_chunks) * 100
                    logger.info(f"[chunker] Progress: {len(chunks)} chunks created (~{progress:.1f}%)")
            
            # Check if we've reached the end
            if end >= len(text):
                break
            
            # Calculate next start position with overlap
            next_start = end - self.chunk_overlap
            
            # Ensure we always make progress (critical for preventing infinite loops)
            if next_start <= start:
                next_start = start + 1
            
            start = next_start
        
        logger.info(f"[chunker] Sliding window chunking complete: created {len(chunks)} chunks from {len(text)} characters")
        return chunks
    
    def chunk_by_paragraphs(self, text: str) -> List[TextChunk]:
        """Chunk text by paragraphs, combining small ones."""
        logger.info(f"[chunker] Starting paragraph-based chunking: {len(text)} characters")
        
        paragraphs = re.split(r'\n\s*\n', text)
        logger.info(f"[chunker] Found {len(paragraphs)} paragraphs")
        
        chunks = []
        sequence_number = 0
        current_chunk = ""
        start_char = 0
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Progress logging every 500 paragraphs
            if i % 500 == 0 and i > 0:
                logger.info(f"[chunker] Processing paragraph {i}/{len(paragraphs)}, chunks_created={len(chunks)}")
            
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
        
        logger.info(f"[chunker] Paragraph chunking complete: created {len(chunks)} chunks")
        return chunks
    
    def chunk_text(self, text: str, method: str = "sliding_window") -> List[TextChunk]:
        """Chunk text using specified method."""
        logger.info(f"[chunker] Starting text chunking with method: {method}")
        
        text = self.preprocess_text(text)
        
        if not text or len(text) < self.min_chunk_size:
            logger.warning(f"[chunker] Text too short for chunking: {len(text)} chars")
            return []
        
        if method == "sliding_window":
            return self.chunk_by_sliding_window(text)
        elif method == "paragraphs":
            return self.chunk_by_paragraphs(text)
        else:
            raise ValueError(f"Unknown chunking method: {method}")
    
    def _log_chunking_summary(self, file_path: Path, text_length: int, chunks: List[TextChunk], method: str) -> None:
        """Log a summary of the chunking task."""
        if not chunks:
            logger.info(f"[chunker] SUMMARY: No chunks created from {file_path}")
            return
        
        chunk_sizes = [len(chunk.text) for chunk in chunks]
        avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes)
        min_chunk_size = min(chunk_sizes)
        max_chunk_size = max(chunk_sizes)
        
        logger.info(f"[chunker] SUMMARY: {file_path.name}")
        logger.info(f"[chunker]   - Input: {text_length:,} characters")
        logger.info(f"[chunker]   - Method: {method}")
        logger.info(f"[chunker]   - Output: {len(chunks)} chunks")
        logger.info(f"[chunker]   - Chunk sizes: avg={avg_chunk_size:.0f}, min={min_chunk_size}, max={max_chunk_size}")
        logger.info(f"[chunker]   - Settings: chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")
    
    def chunk_file(self, file_path: Path, method: str = "sliding_window") -> List[TextChunk]:
        """Chunk a text file."""
        logger.info(f"[chunker] Starting file chunking: {file_path} with method: {method}")
        
        text = self.load_text_file(file_path)
        result = self.chunk_text(text, method)
        
        self._log_chunking_summary(file_path, len(text), result, method)
        return result
    
    def create_full_document_chunk(self, text: str) -> TextChunk:
        """Create a single chunk from the entire document."""
        logger.info(f"[chunker] Creating full document chunk: {len(text)} characters")
        text = self.preprocess_text(text)
        chunk = TextChunk(
            text=text,
            sequence_number=0,
            start_char=0,
            end_char=len(text),
        )
        logger.info(f"[chunker] Full document chunk created: {len(text)} characters")
        return chunk
    
    def create_full_document_chunk_from_file(self, file_path: Path) -> TextChunk:
        """Create a single chunk from an entire file."""
        logger.info(f"[chunker] Creating full document chunk from file: {file_path}")
        
        text = self.load_text_file(file_path)
        result = self.create_full_document_chunk(text)
        
        logger.info(f"[chunker] Full document chunk from file complete: {file_path}")
        return result


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