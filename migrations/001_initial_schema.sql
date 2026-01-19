-- ============================================
-- NCAA Player Pool Database Schema
-- Minimal schema for tournament data extraction
-- Designed for ESPN API data
-- ============================================

-- Set search path
SET search_path TO ncaa_pool, public;

-- ============================================
-- 1. TOURNAMENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS tournaments (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'upcoming', -- 'upcoming', 'in_progress', 'completed'
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, name)
);

CREATE INDEX idx_tournaments_year ON tournaments(year);
CREATE INDEX idx_tournaments_status ON tournaments(status);

COMMENT ON TABLE tournaments IS 'NCAA tournament information';
COMMENT ON COLUMN tournaments.id IS 'ESPN tournament ID';
COMMENT ON COLUMN tournaments.year IS 'Tournament year';
COMMENT ON COLUMN tournaments.raw_data IS 'Full ESPN API response for reference';

-- ============================================
-- 2. TEAMS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS teams (
    id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    market VARCHAR(255), -- School name (e.g., "Duke", "UConn")
    abbreviation VARCHAR(10),
    seed INTEGER, -- 1-16, NULL for regular season teams
    year INTEGER NOT NULL,
    eliminated BOOLEAN DEFAULT FALSE,
    eliminated_round VARCHAR(50),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, year)
);

CREATE INDEX idx_teams_id ON teams(id);
CREATE INDEX idx_teams_year ON teams(year);
CREATE INDEX idx_teams_seed ON teams(year, seed);
CREATE INDEX idx_teams_eliminated ON teams(year, eliminated);

COMMENT ON TABLE teams IS 'Team information per year';
COMMENT ON COLUMN teams.id IS 'ESPN team ID';
COMMENT ON COLUMN teams.seed IS 'Tournament seed (1-16), NULL if not in tournament';
COMMENT ON COLUMN teams.year IS 'Season/tournament year';

-- ============================================
-- 3. PLAYERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS players (
    id VARCHAR(255) NOT NULL,
    team_id VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    short_name VARCHAR(255),
    position VARCHAR(50),
    jersey_number VARCHAR(10),
    year INTEGER NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, year),
    FOREIGN KEY (team_id, year) REFERENCES teams(id, year) ON DELETE CASCADE
);

CREATE INDEX idx_players_id ON players(id);
CREATE INDEX idx_players_team ON players(team_id, year);
CREATE INDEX idx_players_year ON players(year);
CREATE INDEX idx_players_name ON players(full_name);

COMMENT ON TABLE players IS 'Player roster information per year';
COMMENT ON COLUMN players.id IS 'ESPN player/athlete ID';
COMMENT ON COLUMN players.year IS 'Season/tournament year';
COMMENT ON COLUMN players.active IS 'Whether player is still active on team';

-- ============================================
-- 4. GAMES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS games (
    id VARCHAR(255) NOT NULL,
    home_team_id VARCHAR(255) NOT NULL,
    away_team_id VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    round_name VARCHAR(100), -- 'First Four', 'Round of 64', etc.
    scheduled_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'in_progress', 'completed', 'cancelled'
    home_score INTEGER,
    away_score INTEGER,
    winner_team_id VARCHAR(255),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, year),
    FOREIGN KEY (home_team_id, year) REFERENCES teams(id, year),
    FOREIGN KEY (away_team_id, year) REFERENCES teams(id, year)
);

CREATE INDEX idx_games_id ON games(id);
CREATE INDEX idx_games_year ON games(year);
CREATE INDEX idx_games_home_team ON games(home_team_id, year);
CREATE INDEX idx_games_away_team ON games(away_team_id, year);
CREATE INDEX idx_games_round ON games(year, round_name);
CREATE INDEX idx_games_status ON games(year, status);
CREATE INDEX idx_games_scheduled_date ON games(scheduled_date);

COMMENT ON TABLE games IS 'Game/event information';
COMMENT ON COLUMN games.id IS 'ESPN game/event ID';
COMMENT ON COLUMN games.round_name IS 'Tournament round name';

-- ============================================
-- 5. PLAYER GAME STATISTICS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS player_game_stats (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(255) NOT NULL,
    player_id VARCHAR(255) NOT NULL,
    team_id VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,

    -- Primary scoring stats
    points INTEGER DEFAULT 0,
    rebounds INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    total_score INTEGER GENERATED ALWAYS AS (points + rebounds + assists) STORED,

    -- Additional stats
    minutes_played INTEGER,
    field_goals_made INTEGER,
    field_goals_attempted INTEGER,
    three_pointers_made INTEGER,
    three_pointers_attempted INTEGER,
    free_throws_made INTEGER,
    free_throws_attempted INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    fouls INTEGER,

    -- Game context
    starter BOOLEAN DEFAULT FALSE,
    did_not_play BOOLEAN DEFAULT FALSE,

    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(game_id, player_id, year),
    FOREIGN KEY (game_id, year) REFERENCES games(id, year) ON DELETE CASCADE,
    FOREIGN KEY (player_id, year) REFERENCES players(id, year) ON DELETE CASCADE,
    FOREIGN KEY (team_id, year) REFERENCES teams(id, year)
);

CREATE INDEX idx_player_game_stats_year ON player_game_stats(year);
CREATE INDEX idx_player_game_stats_game ON player_game_stats(game_id, year);
CREATE INDEX idx_player_game_stats_player ON player_game_stats(player_id, year);
CREATE INDEX idx_player_game_stats_team ON player_game_stats(team_id, year);
CREATE INDEX idx_player_game_stats_total_score ON player_game_stats(year, total_score DESC);
CREATE INDEX idx_player_game_stats_points ON player_game_stats(year, points DESC);

COMMENT ON TABLE player_game_stats IS 'Player statistics for each game';
COMMENT ON COLUMN player_game_stats.total_score IS 'Sum of points + rebounds + assists (computed)';

-- ============================================
-- 6. UPDATE TIMESTAMP TRIGGER
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_tournaments_updated_at BEFORE UPDATE ON tournaments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_game_stats_updated_at BEFORE UPDATE ON player_game_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 7. HELPER VIEWS FOR GOOGLE SHEETS EXPORT
-- ============================================

-- View: All players with their team info and tournament year
CREATE OR REPLACE VIEW v_players_export AS
SELECT
    p.id AS player_id,
    p.full_name AS player_name,
    p.position,
    p.jersey_number,
    t.id AS team_id,
    COALESCE(t.market, t.name) AS team_name,
    t.seed,
    t.eliminated,
    p.year AS tournament_year,
    p.active
FROM players p
JOIN teams t ON p.team_id = t.id AND p.year = t.year
ORDER BY p.year DESC, t.seed NULLS LAST, t.market, p.full_name;

COMMENT ON VIEW v_players_export IS 'Player roster export view for Google Sheets';

-- View: Player tournament stats aggregated for export
CREATE OR REPLACE VIEW v_player_stats_export AS
SELECT
    p.id AS player_id,
    p.full_name AS player_name,
    COALESCE(t.market, t.name) AS team_name,
    t.seed,
    p.year AS tournament_year,
    COUNT(DISTINCT pgs.game_id) AS games_played,
    COALESCE(SUM(pgs.points), 0) AS total_points,
    COALESCE(SUM(pgs.rebounds), 0) AS total_rebounds,
    COALESCE(SUM(pgs.assists), 0) AS total_assists,
    COALESCE(SUM(pgs.total_score), 0) AS total_score,
    ROUND(COALESCE(AVG(pgs.points), 0), 2) AS avg_points,
    ROUND(COALESCE(AVG(pgs.rebounds), 0), 2) AS avg_rebounds,
    ROUND(COALESCE(AVG(pgs.assists), 0), 2) AS avg_assists,
    t.eliminated
FROM players p
JOIN teams t ON p.team_id = t.id AND p.year = t.year
LEFT JOIN player_game_stats pgs ON p.id = pgs.player_id AND p.year = pgs.year
GROUP BY p.id, p.full_name, t.market, t.name, t.seed, p.year, t.eliminated
ORDER BY total_score DESC, games_played DESC;

COMMENT ON VIEW v_player_stats_export IS 'Player statistics aggregated by tournament year for export';

-- View: Game-by-game stats for detailed export
CREATE OR REPLACE VIEW v_game_stats_export AS
SELECT
    g.id AS game_id,
    g.year AS tournament_year,
    g.round_name,
    g.scheduled_date,
    g.status AS game_status,
    COALESCE(ht.market, ht.name) AS home_team,
    COALESCE(at.market, at.name) AS away_team,
    g.home_score,
    g.away_score,
    p.full_name AS player_name,
    COALESCE(t.market, t.name) AS player_team,
    t.seed,
    pgs.points,
    pgs.rebounds,
    pgs.assists,
    pgs.total_score,
    pgs.minutes_played
FROM games g
JOIN teams ht ON g.home_team_id = ht.id AND g.year = ht.year
JOIN teams at ON g.away_team_id = at.id AND g.year = at.year
JOIN player_game_stats pgs ON g.id = pgs.game_id AND g.year = pgs.year
JOIN players p ON pgs.player_id = p.id AND pgs.year = p.year
JOIN teams t ON pgs.team_id = t.id AND pgs.year = t.year
WHERE pgs.did_not_play = FALSE
ORDER BY g.year DESC, g.scheduled_date DESC, g.id, pgs.total_score DESC;

COMMENT ON VIEW v_game_stats_export IS 'Game-by-game player statistics for detailed export';

-- ============================================
-- 8. HELPER FUNCTIONS
-- ============================================

-- Function to mark team as eliminated
CREATE OR REPLACE FUNCTION eliminate_team(team_uuid VARCHAR, tournament_year INTEGER, round VARCHAR)
RETURNS void AS $$
BEGIN
    UPDATE teams
    SET eliminated = TRUE,
        eliminated_round = round,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = team_uuid AND year = tournament_year;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION eliminate_team IS 'Mark a team as eliminated from the tournament';

-- Function to get player stats for a specific year
CREATE OR REPLACE FUNCTION get_player_stats_by_year(tournament_year INTEGER)
RETURNS TABLE (
    player_id VARCHAR,
    player_name VARCHAR,
    team_name VARCHAR,
    seed INTEGER,
    games_played BIGINT,
    total_points BIGINT,
    total_rebounds BIGINT,
    total_assists BIGINT,
    total_score BIGINT,
    eliminated BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        v.player_id::VARCHAR,
        v.player_name::VARCHAR,
        v.team_name::VARCHAR,
        v.seed,
        v.games_played,
        v.total_points,
        v.total_rebounds,
        v.total_assists,
        v.total_score,
        v.eliminated
    FROM v_player_stats_export v
    WHERE v.tournament_year = get_player_stats_by_year.tournament_year;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_player_stats_by_year IS 'Get aggregated player statistics for a specific tournament year';

-- Function to get top players by total score
CREATE OR REPLACE FUNCTION get_top_players(tournament_year INTEGER, limit_count INTEGER DEFAULT 50)
RETURNS TABLE (
    player_id VARCHAR,
    player_name VARCHAR,
    team_name VARCHAR,
    seed INTEGER,
    games_played BIGINT,
    total_score BIGINT,
    total_points BIGINT,
    total_rebounds BIGINT,
    total_assists BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        v.player_id::VARCHAR,
        v.player_name::VARCHAR,
        v.team_name::VARCHAR,
        v.seed,
        v.games_played,
        v.total_score,
        v.total_points,
        v.total_rebounds,
        v.total_assists
    FROM v_player_stats_export v
    WHERE v.tournament_year = get_top_players.tournament_year
    ORDER BY v.total_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_top_players IS 'Get top N players by total score for a tournament year';
