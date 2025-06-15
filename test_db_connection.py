#!/usr/bin/env python3
"""Test database connection."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from backend.config import settings

async def test_connection():
    """Test database connection."""
    print(f"Testing connection to: {settings.database_url}")
    
    try:
        engine = create_async_engine(settings.database_url)
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ Connection successful!")
            print(f"PostgreSQL version: {version[0]}")
            
            # Test if we can create extension
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                print("✅ pgvector extension available")
            except Exception as e:
                print(f"⚠️  Extension issue: {e}")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 