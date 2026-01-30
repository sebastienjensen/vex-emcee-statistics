from psycopg_pool import AsyncConnectionPool
from app.config import DATABASE_URL

pool = AsyncConnectionPool(
    DATABASE_URL,
    min_size = 1,
    max_size = 5,
    timeout = 10,
    kwargs = {"prepare_threshold": 0},
    open = False
)

async def insert(conn, table, data):
    cur = conn.cursor()
    total = len(data)
    match table:
        case "programs":
            for program in data:
                await cur.execute("""
                    INSERT INTO programs (id, name) VALUES (%s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (program["id"], program["name"]))
        case "seasons":
            for i, season in data:
                await cur.execute("""
                    INSERT INTO seasons (id, program, name) VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (season["id"], season["program"]["id"], season["name"]))
        case "events":
            for i, event in enumerate(data):
                await cur.execute("""
                    INSERT INTO events (id, sku, name, city, country, season, divisions, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (event["id"], event["sku"], event["name"], event["location"]["city"], event["location"]["country"], event["season"]["id"], len(event["divisions"]), event["start"]))
                if (i + 1) % max(1, total // 10) == 0:
                    print(f"Inserted events: {i+1}/{total} ({int((i+1)/total*100)}%)")

async def event_by_sku(conn, sku):
    cur = conn.cursor()
    await cur.execute("SELECT id FROM events WHERE sku = %s", (sku,))
    row = await cur.fetchone()
    return row[0] if row else None