import asyncio
import os
from dotenv import load_dotenv
from nutrition_tracker.db import engine
from nutrition_tracker.models import Base

async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created.")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(create_all())
