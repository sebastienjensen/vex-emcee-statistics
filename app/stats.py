import builtins
import random

# Cache for statistics definitions to avoid repeated queries
_stats_def_cache = None
_RANK_STATS = {"EQ", "ES"}

async def _load_stats_definitions(conn):
    global _stats_def_cache
    if _stats_def_cache is not None:
        return _stats_def_cache
    
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT type, tier, priority, phrase, unit, eligibility_type, eligibility, iq, elims, matches
            FROM statistics_def
            ORDER BY type, tier
        """)
        rows = await cur.fetchall()
        _stats_def_cache = rows
        return _stats_def_cache

async def team_number(cur, team):
    await cur.execute(f"SELECT number FROM teams WHERE id = {team}")
    row = await cur.fetchone()
    return row[0] if row else None

async def team_name(cur, team):
    await cur.execute(f"SELECT name FROM teams WHERE id = {team}")
    row = await cur.fetchone()
    return row[0] if row else None

async def team_organization(cur, team):
    await cur.execute(f"SELECT organization FROM teams WHERE id = {team}")
    row = await cur.fetchone()
    return row[0] if row else None

async def team_city(cur, team):
    await cur.execute(f"SELECT city FROM teams WHERE id = {team}")
    row = await cur.fetchone()
    return row[0] if row else None

async def team_info(conn, team):
    async with conn.cursor() as cur:
        response = {
            "number": await team_number(cur, team),
            "name": await team_name(cur, team),
            "organization": await team_organization(cur, team),
            "city": await team_city(cur, team)
        }
    return response

async def team_stats_selection(conn, team, event, round, program, debug=False, recency_minutes=90):
    async with conn.cursor() as cur:
        selected_stats = []

        def format_stat_value(value, unit):
            if isinstance(value, (int, float)):
                value = builtins.round(value)
            if unit:
                return f"{value}{unit}"
            return f"{value}"
        
        # Check if this is a qualification match
        is_qualification = (round == 2)
        
        # Get all stat definitions (cached) and filter in memory
        all_defs = await _load_stats_definitions(conn)
        filtered_defs = [
            row for row in all_defs
            if (row[7] is None or not (program == 41 and row[7] is False))
            and (row[8] is None or not (not is_qualification and row[8] is False))
        ]
        
        if not filtered_defs:
            return []
        
        # Get unique stat types
        stat_types = list(set(row[0] for row in filtered_defs))
        
        # Fetch all stat values for this team
        await cur.execute("""
            SELECT type, value FROM statistics_event
            WHERE event = %s AND team = %s AND type = ANY(%s)
        """, (event, team, stat_types))
        team_stats = {row[0]: row[1] for row in await cur.fetchall()}
        
        # Get team's CM value once for min_matches checks
        team_matches = team_stats.get('CM', 0)
        
        # Fetch all event-level stats for eligibility checks
        await cur.execute("""
            SELECT type, value FROM statistics_event
            WHERE event = %s AND type = ANY(%s)
        """, (event, stat_types))
        event_stats_rows = await cur.fetchall()
        
        # Group event stats by type for efficient lookups
        event_stats = {}
        for stat_type, value in event_stats_rows:
            if stat_type in _RANK_STATS and (value is None or value <= 0):
                continue
            if stat_type not in event_stats:
                event_stats[stat_type] = []
            event_stats[stat_type].append(value)
        
        # Check statistics history for penalty (exclude CM from recency penalty)
        await cur.execute("""
            SELECT type FROM statistics_history
            WHERE team = %s AND event = %s AND type = ANY(%s)
            AND type != 'CM'
            AND shown_at > NOW() - (%s * INTERVAL '1 minute')
        """, (team, event, stat_types, recency_minutes))
        shown_stats = {row[0] for row in await cur.fetchall()}
        
        # Group tiers by stat type
        stat_tiers = {}
        for row in filtered_defs:
            stat_type = row[0]
            if stat_type not in stat_tiers:
                stat_tiers[stat_type] = []
            stat_tiers[stat_type].append(row)
        
        # Process each stat type
        for stat_type, tiers in stat_tiers.items():
            if stat_type in shown_stats:
                continue
            # Sort tiers by tier number
            tiers.sort(key=lambda x: x[1])
            
            for tier_data in tiers:
                stat_type_val, tier, priority, phrase, unit, eligibility_type, eligibility, iq, elims, min_matches = tier_data
                
                # Get team's stat value from pre-fetched data
                team_value = team_stats.get(stat_type)
                if team_value is None:
                    continue
                if stat_type in _RANK_STATS and team_value <= 0:
                    continue
                
                # Check minimum matches requirement
                if min_matches is not None and team_matches < min_matches:
                    continue
                
                qualifies = False
                
                # Check eligibility using pre-fetched data
                stat_values = event_stats.get(stat_type, [])
                
                if eligibility_type == 'top':
                    # Team must be ranked #1 (highest value)
                    if stat_type in _RANK_STATS:
                        qualifies = all(team_value <= v for v in stat_values)
                    else:
                        qualifies = all(team_value >= v for v in stat_values)
                
                elif eligibility_type == 'percentile':
                    # Team must be in top X percentile
                    if stat_values:
                        if stat_type in _RANK_STATS:
                            better_count = sum(1 for v in stat_values if v < team_value)
                        else:
                            better_count = sum(1 for v in stat_values if v > team_value)
                        percentile_rank = better_count / len(stat_values)
                        qualifies = (percentile_rank <= eligibility)
                
                elif eligibility_type == 'value':
                    # Stat value must meet or exceed threshold
                    qualifies = (team_value >= eligibility)
                
                elif eligibility_type == 'counterexamples':
                    # Stat value must be at or below threshold (inverse)
                    qualifies = (team_value <= eligibility)
                
                if qualifies:
                    selected_stats.append({
                        'type': stat_type,
                        'tier': tier,
                        'priority': priority,
                        'value': format_stat_value(team_value, unit),
                        'phrase': phrase
                    })
                    break  # Stop checking tiers for this stat type
        
        # Always append CM (current match) at the end as fallback
        if team_matches > 0:
            # Get CM definition from cache
            cm_defs = [row for row in all_defs if row[0] == 'CM' and row[1] == 1]
            if cm_defs:
                cm_priority, cm_phrase, cm_unit = cm_defs[0][2], cm_defs[0][3], cm_defs[0][4]
                selected_stats.append({
                    'type': 'CM',
                    'tier': 1,
                    'priority': cm_priority,
                    'value': format_stat_value(team_matches, cm_unit),
                    'phrase': cm_phrase
                })
        
        # If debug mode, return all stats
        if debug:
            return selected_stats
        
        # Otherwise, return only the highest priority stat(s)
        if not selected_stats:
            return []
        
        # Find highest priority efficiently
        max_priority = max(s['priority'] for s in selected_stats)
        top_stats = [s for s in selected_stats if s['priority'] == max_priority]
        
        # If multiple stats have same priority, choose randomly
        chosen_stat = random.choice(top_stats)
        
        # Record this stat as shown (don't record CM to avoid penalizing it)
        if chosen_stat['type'] != 'CM':
            await cur.execute("""
                INSERT INTO statistics_history (team, event, type, shown_at)
                VALUES (%s, %s, %s, CLOCK_TIMESTAMP())
                ON CONFLICT (team, event, type) DO UPDATE
                SET shown_at = CLOCK_TIMESTAMP()
            """, (team, event, chosen_stat['type']))
        
        return [chosen_stat]

async def team_stats_refresh(conn, team, event, match, program):
    async with conn.cursor() as cur:
        # Number of matches, season, season excluding event, event excluding current
        await cur.execute("""
            SELECT COUNT(*) FROM matches 
            WHERE (red1 = %s OR red2 = %s OR blue1 = %s OR blue2 = %s)
            AND id < %s
        """, (team, team, team, team, match))
        row = await cur.fetchone()
        season_matches = row[0] if row else 0
        await cur.execute("INSERT INTO statistics_season (season, team, type, value) VALUES ((SELECT season::INTEGER FROM events WHERE id = %s), %s, 'SM', %s) ON CONFLICT (season, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, season_matches))

        await cur.execute("""
            SELECT COUNT(*) FROM matches 
            WHERE (red1 = %s OR red2 = %s OR blue1 = %s OR blue2 = %s)
            AND event != %s
        """, (team, team, team, team, event))
        row = await cur.fetchone()
        season_matches_excl = row[0] if row else 0
        await cur.execute("INSERT INTO statistics_season (season, team, type, value) VALUES ((SELECT season::INTEGER FROM events WHERE id = %s), %s, 'SMX', %s) ON CONFLICT (season, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, season_matches_excl))

        await cur.execute("""
            SELECT COUNT(*) FROM matches 
            WHERE event = %s 
            AND round = 2 
            AND (red1 = %s OR red2 = %s OR blue1 = %s OR blue2 = %s)
            AND id < %s
        """, (event, team, team, team, team, match))
        row = await cur.fetchone()
        event_matches = row[0] if row else 0
        await cur.execute("INSERT INTO statistics_event (event, team, type, value) VALUES (%s, %s, 'CM', %s) ON CONFLICT (event, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, event_matches))

        # Total points, season, season excluding event, event
        await cur.execute("""
        SELECT SUM(total_points) AS total_score
        FROM (
            SELECT
                CASE
                    WHEN red1 = %s THEN red
                    WHEN red2 = %s THEN red
                    WHEN blue1 = %s THEN blue
                    WHEN blue2 = %s THEN blue
                    ELSE 0
                END AS total_points
            FROM matches
        ) AS combined_scores
        """, (team, team, team, team))
        row = await cur.fetchone()
        season_total = row[0] if row else 0
        await cur.execute("INSERT INTO statistics_season (season, team, type, value) VALUES ((SELECT season::INTEGER FROM events WHERE id = %s), %s, 'ST', %s) ON CONFLICT (season, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, season_total))

        await cur.execute("""
        SELECT SUM(total_points) AS total_score
        FROM (
            SELECT
                CASE
                    WHEN red1 = %s THEN red
                    WHEN red2 = %s THEN red
                    WHEN blue1 = %s THEN blue
                    WHEN blue2 = %s THEN blue
                    ELSE 0
                END AS total_points
            FROM matches
            WHERE event != %s
        ) AS combined_scores                
        """, (team, team, team, team, event))
        row = await cur.fetchone()
        season_total_excl = row[0] if row else 0
        await cur.execute("INSERT INTO statistics_season (season, team, type, value) VALUES ((SELECT season::INTEGER FROM events WHERE id = %s), %s, 'STX', %s) ON CONFLICT (season, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, season_total_excl))

        await cur.execute("""
        SELECT SUM(total_points) AS total_score
        FROM (
            SELECT
                CASE
                    WHEN red1 = %s THEN red
                    WHEN red2 = %s THEN red
                    WHEN blue1 = %s THEN blue
                    WHEN blue2 = %s THEN blue
                    ELSE 0
                END AS total_points
            FROM matches
            WHERE event = %s
        ) AS combined_scores                
        """, (team, team, team, team, event))
        row = await cur.fetchone()
        event_total = row[0] if row else 0
        await cur.execute("INSERT INTO statistics_event (event, team, type, value) VALUES (%s, %s, 'ET', %s) ON CONFLICT (event, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, event_total))

        # Average points, season, season excluding event, event
        season_avg = int(season_total / season_matches) if season_matches > 0 else 0
        await cur.execute("INSERT INTO statistics_season (season, team, type, value) VALUES ((SELECT season::INTEGER FROM events WHERE id = %s), %s, 'SA', %s) ON CONFLICT (season, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, season_avg))
        
        season_avg_excl = int(season_total_excl / season_matches_excl) if season_matches_excl > 0 else 0
        await cur.execute("INSERT INTO statistics_season (season, team, type, value) VALUES ((SELECT season::INTEGER FROM events WHERE id = %s), %s, 'SAX', %s) ON CONFLICT (season, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, season_avg_excl))

        event_avg = int(event_total / event_matches) if event_matches > 0 else 0
        await cur.execute("INSERT INTO statistics_event (event, team, type, value) VALUES (%s, %s, 'EA', %s) ON CONFLICT (event, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, event_avg))

        # Season average match score improvement
        event_improvement = int(((event_avg - season_avg_excl) / season_avg_excl) * 100) if event_matches > 0 and season_matches_excl > 0 else 0
        await cur.execute("INSERT INTO statistics_event (event, team, type, value) VALUES (%s, %s, 'SI', %s) ON CONFLICT (event, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, event_improvement))

        # Event high score
        await cur.execute("""
        SELECT MAX(total_points) AS high_score
        FROM (
            SELECT
                CASE
                    WHEN red1 = %s THEN red
                    WHEN red2 = %s THEN red
                    WHEN blue1 = %s THEN blue
                    WHEN blue2 = %s THEN blue
                    ELSE 0
                END AS total_points
            FROM matches
            WHERE event = %s
        ) AS combined_scores                
        """, (team, team, team, team, event))
        row = await cur.fetchone()
        event_high = row[0] if row else 0
        await cur.execute("INSERT INTO statistics_event (event, team, type, value) VALUES (%s, %s, 'EH', %s) ON CONFLICT (event, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, event_high))

        # Season tournament/teamwork wins
        await cur.execute("""
        SELECT COUNT(*) 
        FROM awards
        WHERE team = %s
            AND (name LIKE %s OR name LIKE %s)
        """, (team, '%Tournament Champion%', '%Teamwork Champion%'))
        row = await cur.fetchone()
        season_awards = row[0] if row else 0
        await cur.execute("INSERT INTO statistics_season (season, team, type, value) VALUES ((SELECT season::INTEGER FROM events WHERE id = %s), %s, 'TC', %s) ON CONFLICT (season, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, season_awards))

        # Qualification rank
        await cur.execute("""
        SELECT (ranking->>'rank')::INTEGER
        FROM divisions, jsonb_array_elements(rankings) AS ranking
        WHERE event = %s
            AND (ranking->'team'->>'id')::INTEGER = %s
        """, (event, team))
        row = await cur.fetchone()
        qual_rank = row[0] if row and row[0] is not None else 0
        await cur.execute("INSERT INTO statistics_event (event, team, type, value) VALUES (%s, %s, 'EQ', %s) ON CONFLICT (event, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, qual_rank))

        # Skills rank
        await cur.execute("""
        SELECT (skill->>'rank')::INTEGER
        FROM events, jsonb_array_elements(skills) AS skill
        WHERE id = %s
            AND (skill->'team'->>'id')::INTEGER = %s
        """, (event, team))
        row = await cur.fetchone()
        skills_rank = row[0] if row and row[0] is not None else 0
        await cur.execute("INSERT INTO statistics_event (event, team, type, value) VALUES (%s, %s, 'ES', %s) ON CONFLICT (event, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, skills_rank))

        # V5-exlcusive statistics
        if program == 1:
            # Win streak
            await cur.execute("""
            WITH numbered_matches AS (
                SELECT 
                    CASE 
                        WHEN red1 = %s OR red2 = %s THEN red > blue
                        WHEN blue1 = %s OR blue2 = %s THEN blue > red
                    END AS won,
                    ROW_NUMBER() OVER (ORDER BY id DESC) as rn
                FROM matches
                WHERE event = %s 
                    AND (red1 = %s OR red2 = %s OR blue1 = %s OR blue2 = %s)
                    AND id < %s
                    AND round = 2
            ),
            streak_groups AS (
                SELECT 
                    SUM(CASE WHEN NOT won THEN 1 ELSE 0 END) OVER (ORDER BY rn) as loss_group
                FROM numbered_matches
            )
            SELECT COUNT(*) 
            FROM streak_groups 
            WHERE loss_group = 0
            """, (team, team, team, team, event, team, team, team, team, match))
            row = await cur.fetchone()
            win_streak = row[0] if row else 0
            await cur.execute("INSERT INTO statistics_event (event, team, type, value) VALUES (%s, %s, 'WS', %s) ON CONFLICT (event, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, win_streak))

            # Matches lost
            await cur.execute("""
            SELECT COUNT(*) 
            FROM matches
            WHERE event = %s 
                AND (red1 = %s OR red2 = %s OR blue1 = %s OR blue2 = %s)
                AND id < %s
                AND round = 2
                AND CASE 
                    WHEN red1 = %s OR red2 = %s THEN red < blue
                    WHEN blue1 = %s OR blue2 = %s THEN blue < red
                END
            """, (event, team, team, team, team, match, team, team, team, team))
            row = await cur.fetchone()
            matches_lost = row[0] if row else 0
            await cur.execute("INSERT INTO statistics_event (event, team, type, value) VALUES (%s, %s, 'WR', %s) ON CONFLICT (event, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, matches_lost))

            # Strength of schedule
            await cur.execute("""
            SELECT (ranking->>'sp')::INTEGER
            FROM divisions, jsonb_array_elements(rankings) AS ranking
            WHERE event = %s
                AND (ranking->'team'->>'id')::INTEGER = %s
            """, (event, team))
            row = await cur.fetchone()
            strength_of_schedule = row[0] if row and row[0] is not None else 0
            await cur.execute("INSERT INTO statistics_event (event, team, type, value) VALUES (%s, %s, 'SS', %s) ON CONFLICT (event, team, type) DO UPDATE SET value = EXCLUDED.value, generated_at = CLOCK_TIMESTAMP()", (event, team, strength_of_schedule))

async def event_stats(conn, event):
    pass