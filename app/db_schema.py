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
    event INTEGER REFERENCES events(id) ON DELETE CASCADE,
    id INTEGER,
    name TEXT,
    rankings JSONB NULL,
    PRIMARY KEY (event, id)
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
    division INTEGER,
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

CREATE TABLE IF NOT EXISTS statistics_def (
    id TEXT PRIMARY KEY,
    priority INTEGER,
    matches INTEGER NULL,
    eligibility_type TEXT NULL,
    eligibility FLOAT NULL,
    phrase TEXT NULL,
    elims BOOLEAN NULL,
    iq BOOLEAN NULL
);

CREATE TABLE IF NOT EXISTS statistics_season (
    season INTEGER REFERENCES seasons(id) ON DELETE CASCADE,
    team INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    type TEXT REFERENCES statistics_def(id) ON DELETE CASCADE,
    value FLOAT,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (season, team, type)
); 

CREATE TABLE IF NOT EXISTS statistics_event (
    event INTEGER REFERENCES events(id) ON DELETE CASCADE,
    team INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    type TEXT REFERENCES statistics_def(id) ON DELETE CASCADE,
    value FLOAT,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (event, team, type)
);

INSERT INTO statistics_def (id, priority, matches, eligibility_type, eligibility, phrase, elims, iq)
VALUES
    ('AC1', 70, 4, 'counterexamples', 0, 'Always converts autonomous wins to match wins', NULL, FALSE),
    ('AC2', 60, 5, 'counterexamples', 1, 'If they win autonomous, they''ll likely win the match', NULL, FALSE),
    ('AC3', 40, 6, 'counterexamples', 2, 'Often goes onto win the match after winning autonomous', NULL, FALSE),
    ('AW1', 65, 4, 'counterexamples', 0, 'Flawless autonomous performance', NULL, FALSE),
    ('AW2', 50, 5, 'counterexamples', 1, 'Very strong autonomous performance', NULL, FALSE),
    ('AW3', 40, 6, 'counterexamples', 2, 'Reliable autonomous performance', NULL, FALSE),
    ('CM', 20, NULL, NULL, NULL, 'Their Xth match', FALSE, NULL),
    ('EA1', 90, 3, 'top', 1, 'Highest average score at the event', NULL, NULL),
    ('EA2', 75, 3, 'percentile', 0.10, 'One of the strongest average scorers', NULL, NULL),
    ('EA3', 65, 3, 'percentile', 0.20, 'Strong average scoring', NULL, NULL),
    ('EH1', 90, 3, 'top', 1, 'Set the highest score', NULL, NULL),
    ('EH2', 75, 3, 'percentile', 0.10, 'One of the highest scores', NULL, NULL),
    ('EH3', 60, 3, 'percentile', 0.20, 'Capable of big scores', NULL, NULL),
    ('EQ1', 100, 3, 'top', 1, 'Leading the qualification rankings', FALSE, NULL),
    ('EQ2', 80, 3, 'percentile', 0.10, 'Near the top of the rankings', FALSE, NULL),
    ('EQ3', 75, 3, 'percentile', 0.20, 'Well-placed in qualification', FALSE, NULL),
    ('ES1', 80, NULL, 'top', 1, 'Top-ranked in skills', FALSE, NULL),
    ('ES2', 70, NULL, 'percentile', 0.10, 'One of the strongest teams in skills', FALSE, NULL),
    ('ES3', 60, NULL, 'percentile', 0.20, 'Strong in skills challenge', FALSE, NULL),
    ('ET1', 50, 3, 'top', 1, 'The highest-scoring team at the event', NULL, NULL),
    ('ET2', 45, 3, 'percentile', 0.10, 'One of the top-scoring teams', NULL, NULL),
    ('ET3', 35, 3, 'percentile', 0.20, 'Consistently high-scoring', NULL, NULL),
    ('SA1', 50, NULL, 'value', 3, 'Highly awarded this season', NULL, NULL),
    ('SA2', 45, NULL, 'value', 2, 'Multiple awards this season', NULL, NULL),
    ('SA3', 25, NULL, 'value', 1, 'Award-winning this season', NULL, NULL),
    ('SI1', 85, 3, 'value', 0.50, 'Scoring far above their season average', NULL, NULL),
    ('SI2', 75, 3, 'value', 0.25, 'Scoring well above their season average', NULL, NULL),
    ('SI3', 65, 3, 'value', 0.10, 'Scoring above their season average', NULL, NULL),
    ('SM1', 70, NULL, 'top', 1, 'The most experienced team at this event', NULL, NULL),
    ('SM2', 65, NULL, 'percentile', 0.10, 'One of the most experienced teams here', NULL, NULL),
    ('SM3', 55, NULL, 'percentile', 0.20, 'Among the more experienced teams', NULL, NULL),
    ('SM4', 45, NULL, 'value', 20, 'Extensive match experience this season', NULL, NULL),
    ('SM5', 35, NULL, 'value', 10, 'Significant match experience', NULL, NULL),
    ('SS1', 70, 3, 'top', 1, 'Toughest schedule so far', FALSE, FALSE),
    ('SS2', 55, 3, 'percentile', 0.10, 'Very tough schedule so far', FALSE, FALSE),
    ('SS3', 30, 3, 'percentile', 0.20, 'Challenging schedule so far', FALSE, FALSE),
    ('ST1', 45, NULL, 'top', 1, 'The most points scored this season', NULL, NULL),
    ('ST2', 40, NULL, 'percentile', 0.10, 'Very high scorer throughout the season', NULL, NULL),
    ('ST3', 30, NULL, 'percentile', 0.20, 'Some of the most points scored this season', NULL, NULL),
    ('WR1', 95, 4, 'counterexamples', 0, 'Undefeated so far', FALSE, FALSE),
    ('WR2', 85, 6, 'counterexamples', 1, 'Lost just one match', FALSE, FALSE),
    ('WR3', 75, 7, 'counterexamples', 2, 'Lost only two matches', FALSE, FALSE),
    ('WS1', 95, 4, 'value', 4, 'On an X-match win streak', FALSE, FALSE),
    ('WS2', 80, 3, 'value', 3, 'On a 3-match win streak', FALSE, FALSE),
    ('WS3', 70, 2, 'value', 2, 'On a 2-match win streak', FALSE, FALSE),
    ('WS4', 60, 1, 'value', 1, 'Won their last match', FALSE, FALSE)
ON CONFLICT (id) DO UPDATE
SET priority = EXCLUDED.priority,
    matches = EXCLUDED.matches,
    eligibility_type = EXCLUDED.eligibility_type,
    eligibility = EXCLUDED.eligibility,
    phrase = EXCLUDED.phrase,
    elims = EXCLUDED.elims,
    iq = EXCLUDED.iq;

ALTER TABLE programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE seasons ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE divisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE awards ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE statistics_def ENABLE ROW LEVEL SECURITY;
ALTER TABLE statistics_season ENABLE ROW LEVEL SECURITY;
ALTER TABLE statistics_event ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow read access to all" ON programs;
DROP POLICY IF EXISTS "Allow read access to all" ON seasons;
DROP POLICY IF EXISTS "Allow read access to all" ON teams;
DROP POLICY IF EXISTS "Allow read access to all" ON events;
DROP POLICY IF EXISTS "Allow read access to all" ON divisions;
DROP POLICY IF EXISTS "Allow read access to all" ON awards;
DROP POLICY IF EXISTS "Allow read access to all" ON matches;
DROP POLICY IF EXISTS "Allow read access to all" ON statistics_def;
DROP POLICY IF EXISTS "Allow read access to all" ON statistics_season;
DROP POLICY IF EXISTS "Allow read access to all" ON statistics_event;

CREATE POLICY "Allow read access to all" ON programs FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON seasons FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON teams FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON events FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON divisions FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON awards FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON matches FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON statistics_def FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON statistics_season FOR SELECT TO public USING (true);
CREATE POLICY "Allow read access to all" ON statistics_event FOR SELECT TO public USING (true);
"""