#!/usr/bin/env python3
"""Simple Typer CLI (synchronous) to test ingestion without async Typer helpers."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from loguru import logger

# Reuse the async runner from the official CLI
from backend.cli import run_ingestion

app = typer.Typer(help="Sync wrapper CLI for ingestion test")


@app.command()
def ingest(
    csv_file: str = typer.Argument(..., help="Path to CSV metadata file"),
    chunk_size: int = typer.Option(1000, help="Chunk size for text splitting"),
    chunk_overlap: int = typer.Option(100, help="Overlap between chunks"),
    no_chunking: bool = typer.Option(False, help="Disable chunking (embed full documents)"),
    batch_name: Optional[str] = typer.Option(None, help="Batch name"),
    content_path: Optional[str] = typer.Option(None, help="Base path for content files"),
):
    """Ingest documents using synchronous Typer command."""
    logger.info("Launching ingestion via sync Typer wrapper …")
    asyncio.run(
        run_ingestion(
            csv_file=csv_file,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            no_chunking=no_chunking,
            batch_name=batch_name,
            content_path=content_path,
        )
    )


if __name__ == "__main__":
    app() 