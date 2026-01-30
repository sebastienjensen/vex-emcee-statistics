from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db import pool
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    await pool.open()
    yield
    await pool.close()

app = FastAPI(
    title = "MCDb API",
    version = "0.1.0",
    lifespan = lifespan
)

# ROUTES

@app.get("/")
async def root():
    return {"api": "ok", "time": datetime.now().isoformat()}

@app.get("/status")
async def status():
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
            await cur.fetchone()

    return {"database": "ok", "time": datetime.now().isoformat()}