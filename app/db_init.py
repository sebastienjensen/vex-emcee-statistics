import asyncio
from app.db import pool
from app.db_schema import CREATE_TABLES_SQL

async def init_db():    
    async with pool.connection() as conn:
        # Split SQL statements; execute them separately
        statements = [statement.strip() for statement in CREATE_TABLES_SQL.split(';') if statement.strip()]
        
        for statement in statements:
            await conn.execute(statement)
        
        print("Database initialised")

async def main():
    await pool.open()
    try:
        await init_db()
    finally:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(main())