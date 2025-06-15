"""OpenAI embedding service (Synchronous)."""

import time
from typing import List, Optional

import openai
from loguru import logger
from openai import OpenAI

from backend.config import settings


class EmbeddingService:
    """Service for generating embeddings using OpenAI (Synchronous)."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 5,
        initial_delay: float = 1.0,
    ):
        """Initializes the synchronous OpenAI client."""
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = model or settings.openai_embedding_model
        self.max_retries = max_retries
        self.initial_delay = initial_delay
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Getting embedding for text (length: {len(text)})")
                
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text,
                    encoding_format="float"
                )
                
                embedding = response.data[0].embedding
                logger.debug(f"Successfully generated embedding (dimension: {len(embedding)})")
                return embedding
                
            except openai.RateLimitError as e:
                delay = self.initial_delay * (2 ** attempt)
                logger.warning(f"Rate limit exceeded. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{self.max_retries})")
                time.sleep(delay)
                
            except openai.APIError as e:
                logger.error(f"OpenAI API error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"OpenAI API error after {self.max_retries} attempts: {e}")
                    raise
                
            except Exception as e:
                logger.error(f"Unexpected error getting embedding: {e}")
                raise
        
        raise Exception(f"Failed to get embedding after {self.max_retries} attempts")
    
    def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generates embeddings for a batch of texts using the synchronous client.
        This is a blocking I/O operation and should be run in a thread pool.
        """
        if not texts:
            return []
        
        # OpenAI API errors on empty strings, so we replace them with a space.
        texts = [text or " " for text in texts]

        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings.create(input=texts, model=self.model)
                return [embedding.embedding for embedding in response.data]
            except openai.RateLimitError as e:
                delay = self.initial_delay * (2 ** attempt)
                logger.warning(f"Rate limit exceeded. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{self.max_retries})")
                time.sleep(delay)
            except openai.APIError as e:
                logger.error(f"OpenAI API error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"OpenAI API error after {self.max_retries} attempts: {e}")
                    return [None] * len(texts) # Return None for all if final attempt fails
        
        logger.error("Failed to get embeddings after all retries.")
        return [None] * len(texts)
    
    def get_embeddings_with_progress(
        self, 
        texts: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[Optional[List[float]]]:
        """Get embeddings with progress callback."""
        logger.info(f"Getting embeddings for {len(texts)} texts with progress tracking")
        
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                embedding = self.get_embedding(text)
                embeddings.append(embedding)
                
                if progress_callback:
                    progress_callback(i + 1, len(texts))
                    
            except Exception as e:
                logger.error(f"Failed to get embedding for text {i}: {e}")
                embeddings.append(None)
        
        successful_count = sum(1 for e in embeddings if e is not None)
        logger.info(f"Completed embeddings: {successful_count}/{len(texts)}")
        
        return embeddings
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate embedding format and dimensions."""
        if not isinstance(embedding, list):
            return False
        
        if len(embedding) == 0:
            return False
        
        # Check if all elements are numbers
        if not all(isinstance(x, (int, float)) for x in embedding):
            return False
        
        # For text-embedding-3-small, expect 1536 dimensions
        expected_dim = 1536
        if len(embedding) != expected_dim:
            logger.warning(f"Unexpected embedding dimension: {len(embedding)}, expected {expected_dim}")
        
        return True
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        logger.info("Testing OpenAI API connection...")
        try:
            test_embedding = self.get_embeddings_batch(["test"])
            if test_embedding and test_embedding[0] is not None:
                logger.info("OpenAI API connection successful")
                return True
            else:
                logger.error("Invalid embedding received from OpenAI API")
                return False
        except Exception as e:
            logger.error(f"OpenAI API connection failed: {e}")
            return False


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> "EmbeddingService":
    """Provides a singleton instance of the EmbeddingService."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_text_embedding(text: str) -> List[float]:
    """Convenience function to get embedding for text."""
    service = get_embedding_service()
    return service.get_embedding(text)


def get_text_embeddings(texts: List[str]) -> List[Optional[List[float]]]:
    """Convenience function to get embeddings for multiple texts."""
    service = get_embedding_service()
    return service.get_embeddings_batch(texts) 