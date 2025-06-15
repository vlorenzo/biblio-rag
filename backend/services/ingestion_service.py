"""Main ingestion service that orchestrates the entire pipeline."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    Batch,
    BatchStatus,
    Chunk,
    ContentFile,
    Document,
    DocumentCreate,
    PreparedChunk,
    PreparedContentFile,
)
from backend.services.csv_parser import CSVMetadataParser
from backend.services.embedding_service import get_embedding_service
from backend.services.text_chunker import TextChunker


class IngestionService:
    """Service for ingesting documents from CSV metadata files."""
    
    def __init__(self, session: AsyncSession):
        """Initialize ingestion service."""
        self.session = session
        self.csv_parser = CSVMetadataParser()
        self.embedding_service = get_embedding_service()
    
    async def create_batch(
        self,
        name: str,
        parameters: Dict,
    ) -> Batch:
        """Create a new ingestion batch."""
        batch = Batch(
            name=name,
            parameters=parameters,
            status=BatchStatus.PENDING,
        )
        
        self.session.add(batch)
        await self.session.commit()
        await self.session.refresh(batch)
        
        logger.info(f"Created batch {batch.id}: {name}")
        return batch
    
    async def update_batch_status(
        self,
        batch: Batch,
        status: BatchStatus,
        error_message: Optional[str] = None,
    ) -> None:
        """Update batch status."""
        batch.status = status
        
        if status == BatchStatus.PROCESSING and not batch.started_at:
            batch.started_at = datetime.utcnow()
        elif status in [BatchStatus.COMPLETED, BatchStatus.FAILED]:
            batch.completed_at = datetime.utcnow()
        
        if error_message:
            batch.error_message = error_message
        
        await self.session.commit()
        logger.info(f"Updated batch {batch.id} status to {status}")
    
    async def save_document(self, document_data: DocumentCreate) -> Document:
        """Save document to database."""
        document = Document(**document_data.model_dump())
        
        self.session.add(document)
        await self.session.flush()  # Get ID without committing
        
        return document
    
    async def save_content_file(
        self,
        document: Document,
        filename: str,
        file_path: Path,
        checksum: str,
    ) -> ContentFile:
        """Save content file record."""
        content_file = ContentFile(
            document_id=document.id,
            filename=filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            checksum=checksum,
            content_type=file_path.suffix.lower().lstrip('.') or 'txt',
        )
        
        self.session.add(content_file)
        await self.session.flush()
        
        return content_file
    
    async def save_chunks(
        self,
        document: Document,
        batch: Batch,
        prepared_chunks: List[PreparedChunk],
        embeddings: List[Optional[List[float]]],
    ) -> List[Chunk]:
        """Save a list of prepared chunks to the database."""
        if not prepared_chunks:
            return []

        chunks_to_create = []
        for i, p_chunk in enumerate(prepared_chunks):
            embedding = embeddings[i] if i < len(embeddings) else None
            if embedding is None:
                logger.warning(f"Missing embedding for chunk {i} of doc {document.id}")

            chunks_to_create.append(
                Chunk(
                    document_id=document.id,
                    batch_id=batch.id,
                    sequence_number=i,
                    text=p_chunk.text,
                    text_hash=p_chunk.text_hash,
                    token_count=p_chunk.token_count,
                    embedding=embedding, # Can be None
                    start_char=p_chunk.start_char,
                    end_char=p_chunk.end_char,
                )
            )
        
        self.session.add_all(chunks_to_create)
        await self.session.commit()
        
        # Refresh to get DB-assigned values
        for chunk in chunks_to_create:
            await self.session.refresh(chunk)
            
        return chunks_to_create
    
    def _prepare_data_for_ingestion(
        self,
        csv_path: Path,
        chunk_size: int,
        chunk_overlap: int,
        no_chunking: bool,
        content_base_path: Optional[Path],
    ) -> Tuple[List[Tuple[DocumentCreate, List[PreparedContentFile], List[PreparedChunk]]], List[str]]:
        """
        Synchronous method to handle all file I/O and data preparation.
        This method does NOT interact with the database or any async operations.
        """
        logger.info("Starting synchronous data preparation phase...")

        if content_base_path:
            self.csv_parser.content_base_path = content_base_path

        documents_data, parse_errors = self.csv_parser.parse_csv(csv_path)

        if not documents_data:
            logger.error("No documents found in CSV during preparation.")
            return [], parse_errors

        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        prepared_data = []

        for doc_data in documents_data:
            content_file_refs = doc_data.extra_metadata.get("content_files", [])
            prepared_chunks = []
            prepared_files = []

            if not content_file_refs:
                logger.warning(f"No content files listed for document: {doc_data.title}")
                prepared_data.append((doc_data, prepared_files, prepared_chunks))
                continue

            for file_ref in content_file_refs:
                found_files = self.csv_parser.find_content_files([file_ref])
                if not found_files:
                    logger.warning(f"Content file not found during preparation: {file_ref}")
                    continue
                
                _, file_path = found_files[0]

                # Prepare content file metadata
                prepared_files.append(
                    PreparedContentFile(
                        filename=file_ref,
                        file_path=file_path,
                        file_size=file_path.stat().st_size,
                        checksum=self.csv_parser.calculate_file_hash(file_path),
                        content_type=file_path.suffix,
                    )
                )

                # Prepare chunks
                if no_chunking:
                    chunks = [chunker.create_full_document_chunk_from_file(file_path)]
                else:
                    chunks = chunker.chunk_file(file_path)
                
                prepared_chunks.extend([PreparedChunk.model_validate(c) for c in chunks])

            prepared_data.append((doc_data, prepared_files, prepared_chunks))
        
        logger.info(f"Data preparation complete. Found {len(prepared_data)} documents.")
        return prepared_data, parse_errors

    async def ingest_csv(
        self,
        csv_path: Path,
        batch_name: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        no_chunking: bool = False,
        content_base_path: Optional[Path] = None,
    ) -> Batch:
        """
        Orchestrates the ingestion process by separating file I/O from DB I/O.
        """
        logger.info(f"Starting ingestion process for CSV: {csv_path}")

        # --- Phase 1: Synchronous Data Preparation (run in thread pool) ---
        loop = asyncio.get_event_loop()
        prepared_data, parse_errors = await loop.run_in_executor(
            None,
            self._prepare_data_for_ingestion,
            csv_path,
            chunk_size,
            chunk_overlap,
            no_chunking,
            content_base_path,
        )

        if parse_errors:
            logger.warning(f"Encountered {len(parse_errors)} errors during CSV parsing.")
        
        if not prepared_data:
            raise Exception("No valid documents could be prepared from the CSV file.")

        # --- Phase 2: Asynchronous Database and Network I/O ---
        batch_name = batch_name or f"csv_ingestion_{csv_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        parameters = {
            "csv_file": str(csv_path), "chunk_size": chunk_size, "chunk_overlap": chunk_overlap,
            "no_chunking": no_chunking, "content_base_path": str(content_base_path),
        }
        
        batch = await self.create_batch(batch_name, parameters)
        batch.total_documents = len(prepared_data)
        await self.update_batch_status(batch, BatchStatus.PROCESSING)

        total_chunks_processed = 0
        
        try:
            for doc_data, prepared_files, prepared_chunks in prepared_data:
                # Save the main document metadata
                document = await self.save_document(doc_data)

                # Save associated content file records
                for p_file in prepared_files:
                    await self.save_content_file(document, p_file.filename, p_file.file_path, p_file.checksum)

                if prepared_chunks:
                    # Fetch embeddings for all chunks of this document at once
                    chunk_texts = [p_chunk.text for p_chunk in prepared_chunks]
                    
                    # Run the synchronous embedding call in a thread pool
                    embeddings = await loop.run_in_executor(
                        None, self.embedding_service.get_embeddings_batch, chunk_texts
                    )
                    
                    # Save chunk records with their embeddings
                    chunks_saved = await self.save_chunks(document, batch, prepared_chunks, embeddings)
                    total_chunks_processed += len(chunks_saved)
                
                batch.processed_documents += 1
            
            batch.total_chunks = total_chunks_processed
            await self.update_batch_status(batch, BatchStatus.COMPLETED)
            logger.info(f"Ingestion completed for batch {batch.id}. Processed {batch.processed_documents} documents and {batch.total_chunks} chunks.")

        except Exception as e:
            logger.error(f"Asynchronous processing failed for batch {batch.id}: {e}", exc_info=True)
            await self.update_batch_status(batch, BatchStatus.FAILED, str(e))
            raise
        
        return batch
    
    async def get_batch_status(self, batch_id: str) -> Optional[Batch]:
        """Get batch status by ID."""
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Batch).where(Batch.id == batch_id)
        )
        return result.scalar_one_or_none()
    
    async def list_batches(self, limit: int = 50) -> List[Batch]:
        """List recent batches."""
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Batch)
            .order_by(Batch.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def ingest_csv_file(
    session: AsyncSession,
    csv_path: Path,
    batch_name: Optional[str] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    no_chunking: bool = False,
    content_base_path: Optional[Path] = None,
) -> Batch:
    """Convenience function to ingest a CSV file."""
    service = IngestionService(session)
    return await service.ingest_csv(
        csv_path=csv_path,
        batch_name=batch_name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        no_chunking=no_chunking,
        content_base_path=content_base_path,
    ) 