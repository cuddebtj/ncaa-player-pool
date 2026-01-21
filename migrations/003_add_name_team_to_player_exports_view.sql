DROP VIEW IF EXISTS v_players_export;

CREATE VIEW v_players_export AS
SELECT
    p.id AS player_id,
    p.full_name AS player_name,
    p.position,
    p.jersey_number,
    t.id AS team_id,
    COALESCE(t.market, t.name) AS team_name,
    p.full_name || ' (' || COALESCE(t.market, t.name) || ')' AS player_team,
    t.seed,
    t.eliminated,
    p.year AS tournament_year,
    p.active
FROM players p
JOIN teams t ON p.team_id = t.id AND p.year = t.year
ORDER BY p.year DESC, t.seed NULLS LAST, t.market, p.full_name;

COMMENT ON VIEW v_players_export IS 'Player roster export view for Google Sheets';