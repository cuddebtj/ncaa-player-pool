-- Migration 002: Fix v_game_stats_export view to include missing columns
-- This adds player_id, position, eliminated, steals, blocks, turnovers, fouls

-- Drop the existing view first to allow column reordering
DROP VIEW IF EXISTS v_game_stats_export;

-- Recreate with all required columns
CREATE VIEW v_game_stats_export AS
SELECT
    pgs.player_id,
    t.eliminated,
    p.full_name AS player_name,
    p.position,
    COALESCE(t.market, t.name) AS player_team,
    t.seed,
    g.id AS game_id,
    g.round_name,
    COALESCE(ht.market, ht.name) AS home_team,
    COALESCE(at.market, at.name) AS away_team,
    g.scheduled_date,
    pgs.points,
    pgs.assists,
    pgs.rebounds,
    pgs.steals,
    pgs.blocks,
    pgs.turnovers,
    pgs.fouls,
    pgs.minutes_played,
    pgs.total_score,
    g.year AS tournament_year
FROM player_game_stats pgs
JOIN players p ON pgs.player_id = p.id AND pgs.year = p.year
JOIN teams t ON pgs.team_id = t.id AND pgs.year = t.year
JOIN games g ON pgs.game_id = g.id AND pgs.year = g.year
JOIN teams ht ON g.home_team_id = ht.id AND g.year = ht.year
JOIN teams at ON g.away_team_id = at.id AND g.year = at.year
WHERE pgs.did_not_play = FALSE
ORDER BY g.year DESC, g.scheduled_date DESC, g.id, pgs.total_score DESC;

COMMENT ON VIEW v_game_stats_export IS 'Game-by-game player statistics for detailed export - fixed to include all required columns';
