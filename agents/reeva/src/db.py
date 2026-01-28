import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def get_db_pool():
    return await asyncpg.create_pool(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", 5432),
    )

async def run_query(sql: str, params=None):
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        return await connection.fetch(sql, *params if params else [])
