#!/usr/bin/env python3
"""Simple test script for the ingestion pipeline."""

import asyncio
from pathlib import Path

from backend.services.csv_parser import CSVMetadataParser


async def test_csv_parsing():
    """Test CSV parsing functionality."""
    print("🔍 Testing CSV parsing...")
    
    parser = CSVMetadataParser()
    
    # Test with inventario file
    csv_path = Path("source_data/inventario_Artom_Prandi.csv")
    if csv_path.exists():
        print(f"📄 Parsing {csv_path}")
        documents, errors = parser.parse_csv(csv_path)
        
        print(f"✅ Parsed {len(documents)} documents")
        print(f"⚠️  {len(errors)} errors")
        
        if documents:
            doc = documents[0]
            print(f"📖 First document: {doc.title}")
            print(f"👤 Author: {doc.author}")
            print(f"📅 Year: {doc.publication_year}")
            print(f"🏷️  Class: {doc.document_class}")
            print(f"📁 Content files: {doc.extra_metadata.get('content_files', [])}")
        
        if errors:
            print("❌ Errors:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"   {error}")
    else:
        print(f"❌ CSV file not found: {csv_path}")
    
    print()


async def test_text_chunking():
    """Test text chunking functionality."""
    print("✂️  Testing text chunking...")
    
    from backend.services.text_chunker import TextChunker
    
    # Create sample text
    sample_text = """
    This is a sample document for testing text chunking functionality.
    
    It contains multiple paragraphs with different content to test how the chunker
    handles various text structures and boundaries.
    
    The chunker should be able to split this text into meaningful chunks while
    preserving context and avoiding awkward breaks in the middle of sentences.
    
    This paragraph contains some additional content to make the text longer
    and test the chunking algorithm with more realistic content.
    """
    
    chunker = TextChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.chunk_text(sample_text)
    
    print(f"✅ Created {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        print(f"📄 Chunk {i + 1}: {len(chunk.text)} chars, {chunk.token_count} tokens")
        print(f"   Preview: {chunk.text[:100]}...")
        print()


async def main():
    """Run all tests."""
    print("🚀 Testing RAG Unito Ingestion Pipeline")
    print("=" * 50)
    
    await test_csv_parsing()
    await test_text_chunking()
    
    print("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main()) 