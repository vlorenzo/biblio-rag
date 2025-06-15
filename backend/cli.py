"""CLI for document ingestion and management."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from backend.database import get_session, create_tables
from backend.services.ingestion_service import IngestionService

app = typer.Typer(
    name="rag-ingest",
    help="RAG Unito document ingestion and management CLI",
)


async def run_ingestion(
    csv_file: str,
    chunk_size: int,
    chunk_overlap: int,
    no_chunking: bool,
    batch_name: Optional[str],
    content_path: Optional[str],
) -> None:
    """Run the ingestion process."""
    csv_path = Path(csv_file)
    if not csv_path.exists():
        typer.echo(f"Error: CSV file not found: {csv_file}", err=True)
        raise typer.Exit(1)
    
    content_base_path = Path(content_path) if content_path else None
    
    async for session in get_session():
        try:
            service = IngestionService(session)
            
            typer.echo(f"Starting ingestion from {csv_file}")
            typer.echo(f"Chunk size: {chunk_size}")
            typer.echo(f"Chunk overlap: {chunk_overlap}")
            typer.echo(f"No chunking: {no_chunking}")
            typer.echo(f"Batch name: {batch_name}")
            typer.echo(f"Content path: {content_path}")
            
            batch = await service.ingest_csv(
                csv_path=csv_path,
                batch_name=batch_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                no_chunking=no_chunking,
                content_base_path=content_base_path,
            )
            
            typer.echo(f"✅ Ingestion completed successfully!")
            typer.echo(f"Batch ID: {batch.id}")
            typer.echo(f"Documents processed: {batch.processed_documents}/{batch.total_documents}")
            typer.echo(f"Total chunks: {batch.total_chunks}")
            
        except Exception as e:
            typer.echo(f"❌ Ingestion failed: {e}", err=True)
            raise typer.Exit(1)


async def check_batch_status(batch_id: Optional[str]) -> None:
    """Check batch status."""
    async for session in get_session():
        try:
            service = IngestionService(session)
            
            if batch_id:
                batch = await service.get_batch_status(batch_id)
                if not batch:
                    typer.echo(f"Batch not found: {batch_id}", err=True)
                    raise typer.Exit(1)
                
                typer.echo(f"Batch: {batch.name}")
                typer.echo(f"ID: {batch.id}")
                typer.echo(f"Status: {batch.status}")
                typer.echo(f"Created: {batch.created_at}")
                typer.echo(f"Documents: {batch.processed_documents}/{batch.total_documents}")
                typer.echo(f"Chunks: {batch.total_chunks}")
                
                if batch.error_message:
                    typer.echo(f"Error: {batch.error_message}")
            else:
                batches = await service.list_batches()
                if not batches:
                    typer.echo("No batches found")
                    return
                
                typer.echo("Recent batches:")
                for batch in batches:
                    typer.echo(f"  {batch.id}: {batch.name} ({batch.status})")
                    
        except Exception as e:
            typer.echo(f"Error checking status: {e}", err=True)
            raise typer.Exit(1)


async def list_all_batches() -> None:
    """List all batches."""
    async for session in get_session():
        try:
            service = IngestionService(session)
            batches = await service.list_batches(limit=100)
            
            if not batches:
                typer.echo("No batches found")
                return
            
            typer.echo(f"Found {len(batches)} batches:")
            typer.echo()
            
            for batch in batches:
                status_emoji = {
                    "pending": "⏳",
                    "processing": "🔄", 
                    "completed": "✅",
                    "failed": "❌"
                }.get(batch.status, "❓")
                
                typer.echo(f"{status_emoji} {batch.name}")
                typer.echo(f"   ID: {batch.id}")
                typer.echo(f"   Status: {batch.status}")
                typer.echo(f"   Created: {batch.created_at}")
                typer.echo(f"   Documents: {batch.processed_documents}/{batch.total_documents}")
                typer.echo(f"   Chunks: {batch.total_chunks}")
                typer.echo()
                
        except Exception as e:
            typer.echo(f"Error listing batches: {e}", err=True)
            raise typer.Exit(1)


async def initialize_database() -> None:
    """Initialize database tables."""
    try:
        typer.echo("Initializing database tables...")
        await create_tables()
        typer.echo("✅ Database initialized successfully!")
    except Exception as e:
        typer.echo(f"❌ Database initialization failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
async def ingest(
    csv_file: str = typer.Argument(..., help="Path to CSV metadata file"),
    chunk_size: int = typer.Option(1000, help="Chunk size for text splitting"),
    chunk_overlap: int = typer.Option(100, help="Overlap between chunks"),
    no_chunking: bool = typer.Option(False, help="Disable chunking (embed full documents)"),
    batch_name: Optional[str] = typer.Option(None, help="Name for this batch"),
    content_path: Optional[str] = typer.Option(None, help="Base path for content files"),
) -> None:
    """Ingest documents from CSV metadata file."""
    await run_ingestion(csv_file, chunk_size, chunk_overlap, no_chunking, batch_name, content_path)


@app.command()
async def status(
    batch_id: Optional[str] = typer.Option(None, help="Batch ID to check status"),
) -> None:
    """Check ingestion batch status."""
    await check_batch_status(batch_id)


@app.command()
async def list_batches() -> None:
    """List all ingestion batches."""
    await list_all_batches()


@app.command()
async def init_db() -> None:
    """Initialize database tables."""
    await initialize_database()


if __name__ == "__main__":
    app() 