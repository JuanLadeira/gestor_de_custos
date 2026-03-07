import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import OperationalError

print("Waiting for database connection...")

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL environment variable is not set")

async def check_db_connection():
    max_retries = 30
    retries = 0
    while retries < max_retries:
        try:
            engine = create_async_engine(db_url)
            async with engine.connect():
                print("Database connection successful!")
                return
        except OperationalError as e:
            print(f"Database connection failed: {e}")
            retries += 1
            print(f"Retrying in 2 seconds... ({retries}/{max_retries})")
            await asyncio.sleep(2)
    
    print("Could not connect to the database after several retries. Exiting.")
    exit(1)

if __name__ == "__main__":
    asyncio.run(check_db_connection())
