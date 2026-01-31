import asyncio
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from app.fetch import fetch
from app.db import pool, insert, event_by_sku, team_by_number
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

@app.get("/refresh/events/all", response_model=RefreshResponse, tags=["Refresh"])
async def refresh_events():
    async with pool.connection() as conn:
        await insert(conn, "events", await fetch("events", {"season[]": [196, 197]}))
        print("Events refreshed")
    
    return {"status": "ok"}

@app.get("/refresh/events/{id}", response_model=RefreshResponse, tags=["Refresh"])
async def refresh_event(id: int):
    async with pool.connection() as conn:
        # Fetch and insert event data
        event_data_list = await fetch(f"events/{id}", {})
        await asyncio.sleep(1)
        event_data = event_data_list[0] if event_data_list else {}
        
        # Extract and insert divisions for current event
        divisions_data = event_data.get("divisions") or []
        if divisions_data:
            # Add event ID to each division
            for division in divisions_data:
                division["event"] = {"id": id}
            await insert(conn, "divisions", divisions_data)
        
        teams = await fetch(f"events/{id}/teams", {"id": id})
        await asyncio.sleep(1)
        await insert(conn, "teams", teams)
        print(f"Event {id} teams refreshed")
        
        divisions = len(divisions_data)
        for division in range(1, divisions + 1):
            matches = await fetch(f"events/{id}/divisions/{division}/matches", {})
            await asyncio.sleep(1)
            await insert(conn, "matches", matches)
        inserted_teams = {team["id"] for team in teams}
        events = []
        for team in teams:
            team_events = await fetch(f"teams/{team['id']}/events", {"season[]": [196, 197]})
            await asyncio.sleep(1)
            for event in team_events:
                if event["id"] == id:
                    continue  # Skip the current event
                if event["id"] not in events:
                    events.append(event["id"])
        print(f"To fetch teams, awards, matches from: {events}")
        for i, event in enumerate(events, start=1):
            event_data_list = await fetch(f"events/{event}", {})
            await asyncio.sleep(1)
            event_data = event_data_list[0] if event_data_list else {}
            divisions = len(divisions_data)
            event_teams = await fetch(f"events/{event}/teams", {})
            await asyncio.sleep(1)
            if event_teams:
                new_event_teams = [team for team in event_teams if team["id"] not in inserted_teams]
                if new_event_teams:
                    await insert(conn, "teams", new_event_teams)
                    inserted_teams.update(team["id"] for team in new_event_teams)
            awards = await fetch(f"events/{event}/awards", {})
            await asyncio.sleep(1)
            if awards:
                await insert(conn, "awards", awards)
            for division in range(1, divisions + 1):
                matches = await fetch(f"events/{event}/divisions/{division}/matches", {})
                await asyncio.sleep(1)
                await insert(conn, "matches", matches)
            print(f"Processed tangential event {event} ({i}/{len(events)})")

    return {"status": "ok"}

@app.get("/refresh/rankings/events/{id}", response_model=RefreshResponse, tags=["Refresh"])
async def refresh_rankings(id: int):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            # Get the number of divisions for this event
            await cur.execute("SELECT divisions FROM events WHERE id = %s", (id,))
            row = await cur.fetchone()
            divisions = row[0] if row else 0
            
            if divisions == 0:
                print(f"Event {id} has no divisions")
                return {"status": "ok"}
            
            # Fetch and insert rankings for each division
            for division in range(1, divisions + 1):
                rankings = await fetch(f"events/{id}/divisions/{division}/rankings", {})
                await asyncio.sleep(1)
                if rankings:
                    await insert(conn, "rankings", rankings)
                    print(f"Refreshed rankings for event {id} division {division}")
    
    return {"status": "ok"}

@app.get("/refresh/teams", response_model=RefreshResponse, tags=["Refresh"])
async def refresh_teams():
    async with pool.connection() as conn:
        await insert(conn, "teams", await fetch("teams", {"registered": True, "program[]": [1, 41]}))
        print("Teams refreshed")
    
    return {"status": "ok"}

@app.get("/utilities/events/{sku}", response_model=UtilityResponse, tags=["Utilities"])
async def get_id_from_sku(sku: str):
    async with pool.connection() as conn:
        id = await event_by_sku(conn, sku)

    if id is None:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    return {"id": id}

@app.get("/utilities/teams/{number}", response_model=UtilityResponse, tags=["Utilities"])
async def get_id_from_number(number: str):
    async with pool.connection() as conn:
        id = await team_by_number(conn, number)

    if id is None:
        raise HTTPException(status_code=404, detail="Team number not found")
    
    return {"id": id}