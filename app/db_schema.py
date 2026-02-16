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
    type TEXT,
    tier INTEGER,
    priority INTEGER,
    matches INTEGER NULL,
    eligibility_type TEXT NULL,
    eligibility FLOAT NULL,
    phrase TEXT NULL,
    unit TEXT NULL,
    elims BOOLEAN NULL,
    iq BOOLEAN NULL,
    PRIMARY KEY (type, tier)
);

CREATE TABLE IF NOT EXISTS statistics_season (
    season INTEGER REFERENCES seasons(id) ON DELETE CASCADE,
    team INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    type TEXT,
    value FLOAT,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (season, team, type)
); 

CREATE TABLE IF NOT EXISTS statistics_event (
    event INTEGER REFERENCES events(id) ON DELETE CASCADE,
    team INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    type TEXT,
    value FLOAT,
    generated_at TIMESTAMPTZ DEFAULT CLOCK_TIMESTAMP(),
    PRIMARY KEY (event, team, type)
);

CREATE TABLE IF NOT EXISTS statistics_history (
    team INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    event INTEGER REFERENCES events(id) ON DELETE CASCADE,
    type TEXT,
    shown_at TIMESTAMPTZ DEFAULT CLOCK_TIMESTAMP(),
    PRIMARY KEY (team, event, type)
);

INSERT INTO statistics_def (type, tier, priority, matches, eligibility_type, eligibility, phrase, unit, elims, iq)
VALUES
    ('CM', 1, 10, NULL, NULL, NULL, 'Current match for %team%', '', FALSE, NULL),
    ('EA', 1, 80, 3, 'top', 1, '%team% has the highest average score at the event', ' points', NULL, NULL),
    ('EA', 2, 70, 3, 'percentile', 0.10, '%team% has an impressive average match score', ' points', NULL, NULL),
    ('EA', 3, 60, 3, 'percentile', 0.20, '%team% consistently scores well', ' points', NULL, NULL),
    ('EH', 1, 90, 3, 'top', 1, '%team% set the highest score at the event', ' points', NULL, NULL),
    ('EH', 2, 80, 3, 'percentile', 0.10, '%team% set one of the highest scores at the event', ' points', NULL, NULL),
    ('EH', 3, 70, 3, 'percentile', 0.20, '%team% has shown they''re capable of big scores in earlier matches', ' points', NULL, NULL),
    ('EQ', 1, 70, 3, 'top', 1, '%team% is leading the qualification rankings', '', FALSE, NULL),
    ('EQ', 2, 50, 3, 'percentile', 0.10, '%team% is near the top of the qualification rankings', '', FALSE, NULL),
    ('EQ', 3, 30, 3, 'percentile', 0.20, '%team% is well-placed in the qualification rankings', '', FALSE, NULL),
    ('ES', 1, 60, NULL, 'top', 1, '%team% is leading the Robot Skills Challenge rankings', '', FALSE, NULL),
    ('ES', 2, 40, NULL, 'percentile', 0.10, '%team% is one of the strongest teams in the Robot Skills Challenge', '', FALSE, NULL),
    ('ES', 3, 30, NULL, 'percentile', 0.20, '%team% is strong in the Robot Skills Challenge', '', FALSE, NULL),
    ('TC', 1, 90, NULL, 'value', 3, '%team% has won several tournaments this season', ' TCs', NULL, NULL),
    ('TC', 2, 40, NULL, 'value', 1, '%team% has already won tournaments this season', ' TCs', NULL, NULL),
    ('TC', 3, 30, NULL, 'value', 1, '%team% has already won a tournament this season', ' TCs', NULL, NULL),
    ('SI', 1, 60, 3, 'value', 50, '%team% is scoring far above their season average', '% up', NULL, NULL),
    ('SI', 2, 50, 3, 'value', 25, '%team% is scoring well above their season average', '% up', NULL, NULL),
    ('SI', 3, 40, 3, 'value', 10, '%team% is scoring above their season average', '% up', NULL, NULL),
    ('SM', 1, 50, NULL, 'top', 1, '%team% is the most experienced team at this event', ' matches', NULL, NULL),
    ('SM', 2, 40, NULL, 'percentile', 0.10, '%team% is one of the most experienced teams at this event', ' matches', NULL, NULL),
    ('SM', 3, 30, NULL, 'percentile', 0.20, '%team% is among the more experienced teams at this event', ' matches', NULL,NULL),
    ('SM', 4, 20, NULL, 'value', 20, '%team% has extensive match experience this season', ' matches', NULL, NULL),
    ('SM', 5, 10, NULL, 'value', 10, '%team% has a good amount of match experience this season', ' matches', NULL, NULL),
    ('SS', 1, 60, 3, 'top', 1, '%team% has faced the toughest schedule so far at this event', ' SPs', FALSE, FALSE),
    ('SS', 2, 50, 3, 'percentile', 0.10, '%team% has had a very tough schedule so far at this event', ' SPs',  FALSE,FALSE),
    ('SS', 3, 40, 3, 'percentile', 0.20, '%team% has had a challenging schedule so far at this event', ' SPs', FALSE,FALSE),
    ('ST', 1, 80, NULL, 'top', 1, 'Of all the teams at the event, %team% has scored the most across the season', ' points', NULL, NULL),
    ('ST', 2, 60, NULL, 'percentile', 0.10, '%team% has been a very high scorer throughout the season', ' points', NULL, NULL),
    ('ST', 3, 40, NULL, 'percentile', 0.20, '%team% is among the highest scorers this season', ' points', NULL, NULL),
    ('WR', 1, 100, 4, 'counterexamples', 0, '%team% is undefeated so far', ' losses', FALSE, FALSE),
    ('WR', 2, 70, 6, 'counterexamples', 1, '%team% has lost just one match at this event', ' losses', FALSE, FALSE),
    ('WR', 3, 40, 7, 'counterexamples', 2, '%team% has lost only two matches at this event', ' losses', FALSE, FALSE),
    ('WS', 1, 90, 4, 'value', 4, '%team% is on a win streak', ' wins', FALSE, FALSE),
    ('WS', 2, 80, 3, 'value', 3, '%team% is on a win streak', ' wins', FALSE, FALSE),
    ('WS', 3, 40, 2, 'value', 2, '%team% is on a win streak', ' wins', FALSE, FALSE),
    ('WS', 4, 20, 1, 'value', 1, '%team% won their last match', '', FALSE, FALSE)
ON CONFLICT (type, tier) DO UPDATE
SET priority = EXCLUDED.priority,
    matches = EXCLUDED.matches,
    eligibility_type = EXCLUDED.eligibility_type,
    eligibility = EXCLUDED.eligibility,
    phrase = EXCLUDED.phrase,
    unit = EXCLUDED.unit,
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
ALTER TABLE statistics_history ENABLE ROW LEVEL SECURITY;

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
DROP POLICY IF EXISTS "Allow read access to all" ON statistics_history;

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
CREATE POLICY "Allow read access to all" ON statistics_history FOR SELECT TO public USING (true);
"""