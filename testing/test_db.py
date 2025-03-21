from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import asyncio
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Ensure DATABASE_URL is set
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the .env file")

engine = create_async_engine(DATABASE_URL, echo=True)

async def test_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("Connection successful:", result.fetchone())

asyncio.run(test_connection())
