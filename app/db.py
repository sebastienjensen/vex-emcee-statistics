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
                    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                """, (program["id"], program["name"]))
        case "seasons":
            for season in data:
                await cur.execute("""
                    INSERT INTO seasons (id, program, name) VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET program = EXCLUDED.program, name = EXCLUDED.name
                """, (season["id"], season["program"]["id"], season["name"]))
        case "events":
            for i, event in enumerate(data):
                await cur.execute("""
                    INSERT INTO events (id, sku, name, city, country, season, divisions, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET sku = EXCLUDED.sku, name = EXCLUDED.name, city = EXCLUDED.city, country = EXCLUDED.country, season = EXCLUDED.season, divisions = EXCLUDED.divisions, date = EXCLUDED.date
                """, (event["id"], event["sku"], event["name"], event["location"]["city"], event["location"]["country"], event["season"]["id"], len(event["divisions"]), event["start"]))
                if (i + 1) % max(1, total // 10) == 0:
                    print(f"Inserted events: {i+1}/{total} ({int((i+1)/total*100)}%)")
        case "teams":
            for i, team in enumerate(data):
                await cur.execute("""
                    INSERT INTO teams (id, number, name, robot, organization, city, region, country, grade, program) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET number = EXCLUDED.number, name = EXCLUDED.name, robot = EXCLUDED.robot, organization = EXCLUDED.organization, city = EXCLUDED.city, region = EXCLUDED.region, country = EXCLUDED.country, grade = EXCLUDED.grade, program = EXCLUDED.program
                """, (team["id"], team["number"], team["team_name"], team["robot_name"], team["organization"], team["location"]["city"], team["location"]["region"], team["location"]["country"], team["grade"], team["program"]["id"]))
                if (i + 1) % max(1, total // 10) == 0:
                    print(f"Inserted teams: {i+1}/{total} ({int((i+1)/total*100)}%)")
        case "awards":
            for i, award in enumerate(data):
                await cur.execute("""
                    INSERT INTO awards (id, team, event, name) VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id, team) DO UPDATE SET event = EXCLUDED.event, name = EXCLUDED.name
                """, (award["id"], award["team"]["id"], award["event"]["id"], award["name"]))
                if (i + 1) % max(1, total // 10) == 0:
                    print(f"Inserted awards: {i+1}/{total} ({int((i+1)/total*100)}%)")
        case "matches":
            for i, match in enumerate(data):
                event = match["event"]["id"]
                await cur.execute("SELECT season FROM events WHERE id = %s", (event,))
                season_row = await cur.fetchone()
                season = season_row[0] if season_row else None
                await cur.execute("SELECT program FROM seasons WHERE id = %s", (season,))
                program_row = await cur.fetchone()
                program = program_row[0] if program_row else None
                if program == 1:
                    red1 = match["alliances"][1]["teams"][0]["team"]["id"]
                    red2 = match["alliances"][1]["teams"][1]["team"]["id"]
                    blue1 = match["alliances"][0]["teams"][0]["team"]["id"]
                    blue2 = match["alliances"][0]["teams"][1]["team"]["id"]
                else:
                    red1 = match["alliances"][0]["teams"][0]["team"]["id"]
                    red2 = None
                    blue1 = match["alliances"][1]["teams"][0]["team"]["id"]
                    blue2 = None
                await cur.execute("""
                    INSERT INTO matches (id, event, division, name, number, instance, round, season, red1, red2, blue1, blue2, red, blue) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET event = EXCLUDED.event, division = EXCLUDED.division, name = EXCLUDED.name, number = EXCLUDED.number, instance = EXCLUDED.instance, round = EXCLUDED.round, season = EXCLUDED.season, red1 = EXCLUDED.red1, red2 = EXCLUDED.red2, blue1 = EXCLUDED.blue1, blue2 = EXCLUDED.blue2, red = EXCLUDED.red, blue = EXCLUDED.blue
                """, (match["id"], event, match["division"]["id"], match["name"], match["matchnum"], match["instance"], match["round"], season, red1, red2, blue1, blue2, match["alliances"][1]["score"], match["alliances"][0]["score"]))
                if (i + 1) % max(1, total // 10) == 0:
                    print(f"Inserted matches: {i+1}/{total} ({int((i+1)/total*100)}%)")

async def event_by_sku(conn, sku):
    cur = conn.cursor()
    await cur.execute("SELECT id FROM events WHERE sku = %s", (sku,))
    row = await cur.fetchone()
    return row[0] if row else None

async def team_by_number(conn, number):
    cur = conn.cursor()
    await cur.execute("SELECT id FROM teams WHERE number = %s", (number,))
    row = await cur.fetchone()
    return row[0] if row else None