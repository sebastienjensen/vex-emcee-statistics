CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS programs (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE IF NOT EXISTS seasons (
    id INTEGER PRIMARY KEY,
    name TEXT,
    program INTEGER REFERENCES programs(id)
);

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    number TEXT,
    name TEXT,
    robot TEXT NULL,
    organization TEXT,
    city TEXT,
    region TEXT NULL,
    country TEXT,
    grade TEXT,
    program INTEGER REFERENCES programs(id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    sku TEXT,
    name TEXT,
    city TEXT,
    country TEXT,
    season TEXT,
    divisions INTEGER,
    skills JSONB NULL,
    date TEXT
);

CREATE TABLE IF NOT EXISTS divisions (
    id INTEGER PRIMARY KEY,
    name TEXT,
    event INTEGER REFERENCES events(id) ON DELETE CASCADE,
    rankings JSONB NULL
);

CREATE TABLE IF NOT EXISTS awards (
    id INTEGER,
    team INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    event INTEGER REFERENCES events(id) ON DELETE CASCADE,
    name TEXT,
    PRIMARY KEY (id, team)
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY,
    event INTEGER REFERENCES events(id) ON DELETE CASCADE,
    division TEXT,
    name TEXT,
    number INTEGER,
    instance INTEGER,
    round INTEGER,
    season INTEGER REFERENCES seasons(id) ON DELETE CASCADE,
    red1 INTEGER NULL REFERENCES teams(id) ON DELETE CASCADE,
    red2 INTEGER NULL REFERENCES teams(id) ON DELETE CASCADE,
    blue1 INTEGER NULL REFERENCES teams(id) ON DELETE CASCADE,
    blue2 INTEGER NULL REFERENCES teams(id) ON DELETE CASCADE,
    red INTEGER NULL,
    blue INTEGER NULL,
    auton TEXT NULL
);

ALTER TABLE programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE seasons ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE divisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE awards ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow read access to all" ON programs;
DROP POLICY IF EXISTS "Allow read access to all" ON seasons;
DROP POLICY IF EXISTS "Allow read access to all" ON teams;
DROP POLICY IF EXISTS "Allow read access to all" ON events;
DROP POLICY IF EXISTS "Allow read access to all" ON divisions;
DROP POLICY IF EXISTS "Allow read access to all" ON awards;
DROP POLICY IF EXISTS "Allow read access to all" ON matches;

CREATE POLICY "Allow read access to all" ON programs FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON seasons FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON teams FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON events FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON divisions FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON awards FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON matches FOR SELECT TO public USING (true);
"""