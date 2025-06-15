#!/usr/bin/env python3
"""Standalone script to ingest documents without Typer.

Usage example:
    uv run python ingest.py source_data/inventario_Artom_Prandi.csv \
        --no-chunking --batch-name first_batch

This script avoids the Click/Typer stack entirely; it simply parses command-line
arguments with argparse and then runs the existing `run_ingestion` coroutine
inside a single `asyncio.run` call, ensuring a single consistent event-loop.
"""

import argparse
import asyncio
from pathlib import Path
from typing import Optional

from loguru import logger

from backend.cli import run_ingestion  # Reuse the well-tested coroutine


def parse_args() -> argparse.Namespace:
    """Parse CLI options."""
    parser = argparse.ArgumentParser(description="Document ingestion utility")

    parser.add_argument("csv_file", help="Path to the CSV metadata file")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size for text splitting (default: 1000)")
    parser.add_argument("--chunk-overlap", type=int, default=100, help="Overlap between chunks (default: 100)")
    parser.add_argument("--no-chunking", action="store_true", help="Disable chunking: embed full documents")
    parser.add_argument("--batch-name", type=str, default=None, help="Optional name for the ingestion batch")
    parser.add_argument("--content-path", type=str, default=None, help="Base directory for content files referenced in CSV")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        raise SystemExit(1)

    logger.info("Ingestion script started")
    logger.info(f"CSV file        : {csv_path}")
    logger.info(f"Chunk size      : {args.chunk_size}")
    logger.info(f"Chunk overlap   : {args.chunk_overlap}")
    logger.info(f"Chunking active : {not args.no_chunking}")
    logger.info(f"Batch name      : {args.batch_name or '[auto]'}")
    logger.info(f"Content base    : {args.content_path or '[default]'}")

    # Run the existing async ingestion coroutine
    asyncio.run(
        run_ingestion(
            csv_file=str(csv_path),
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            no_chunking=args.no_chunking,
            batch_name=args.batch_name,
            content_path=args.content_path,
        )
    )

    logger.success("Ingestion script completed successfully 🎉")


if __name__ == "__main__":
    main() 