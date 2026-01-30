from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from app.fetch import fetch
from app.db import pool, insert, event_by_sku
from datetime import datetime
from pydantic import BaseModel

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

# RESPONSE MODELS

class PingResponse(BaseModel):
    api: str
    time: datetime

class DatabaseStatusResponse(BaseModel):
    database: str
    time: datetime

class RefreshResponse(BaseModel):
    status: str

class UtilityResponse(BaseModel):
    id: int

# ROUTES

@app.get("/", response_model=PingResponse, tags=["Status"])
async def root():
    return {"api": "ok", "time": datetime.now().isoformat()}

@app.get("/status", response_model=DatabaseStatusResponse, tags=["Status"])
async def status():
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
            await cur.fetchone()

    return {"database": "ok", "time": datetime.now().isoformat()}

@app.get("/refresh/events", response_model=RefreshResponse, tags=["Refresh"])
async def refresh_events():
    async with pool.connection() as conn:
        await insert(conn, "events", await fetch("events", {"season[]": [196, 197]}))
        print("Events refreshed")
    
    return {"status": "ok"}

@app.get("/refresh/events/{id}", response_model=RefreshResponse, tags=["Refresh"])
async def refresh_event(id: int):
    async with pool.connection() as conn:
        pass

@app.get("/utilities/events/{sku}", response_model=UtilityResponse, tags=["Utilities"])
async def get_id_from_sku(sku: str):
    async with pool.connection() as conn:
        id = await event_by_sku(conn, sku)

    if id is None:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    return {"id": id}