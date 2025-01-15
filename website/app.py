from flask import Flask, render_template
import sqlite3
import os
from datetime import datetime
import re
import logging
from typing import Optional, Tuple, Dict

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_team_mapping() -> Dict[str, str]:
    """Henter team mapping fra databasen"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Databases', 'team_mapping.db')
        if not os.path.exists(db_path):
            logger.error("Team mapping database ikke fundet")
            return {}
            
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT team_initial, official_name FROM team_mapping")
            return dict(cursor.fetchall())
    except Exception as e:
        logger.error(f"Fejl ved hentning af team mapping: {str(e)}")
        return {}

def format_team_name(team_initial: str) -> str:
    """Formaterer holdnavne baseret på team mapping"""
    try:
        team_mapping = get_team_mapping()
        if team_initial in team_mapping:
            return team_mapping[team_initial]
        return team_initial
    except Exception as e:
        logger.error(f"Fejl ved formatering af holdnavn '{team_initial}': {str(e)}")
        return team_initial

def format_date(date_str: str) -> str:
    """Formaterer datoer konsistent"""
    try:
        if not date_str:
            return ""
        date = datetime.strptime(date_str, '%d. %B %Y')
        return date.strftime('%d. %B %Y')
    except Exception as e:
        logger.error(f"Fejl ved formatering af dato '{date_str}': {str(e)}")
        return date_str or ""

def get_validated_score(match: Dict) -> Optional[Tuple[int, int]]:
    """Validerer og returnerer kampscoren"""
    try:
        if not match or not match.get('score') or match['score'] == 'N/A':
            logger.debug(f"Ingen score tilgængelig for kamp: {match.get('database', 'unknown')}")
            return None
            
        parts = match['score'].split('-')
        if len(parts) != 2:
            logger.warning(f"Ugyldig score format '{match['score']}' for kamp: {match['database']}")
            return None
            
        home_score = int(parts[0])
        away_score = int(parts[1])
        
        if home_score < 0 or away_score < 0:
            logger.warning(f"Negative scores ikke tilladt: {match['score']}")
            return None
            
        return (home_score, away_score)
    except Exception as e:
        logger.error(f"Fejl ved validering af score for kamp {match.get('database', 'unknown')}: {str(e)}")
        return None

def get_match_statistics(match: Dict) -> Dict:
    """Beregner kampstatistikker dynamisk"""
    try:
        if not match or not match.get('database'):
            logger.warning("Manglende match data for statistik beregning")
            return {'duration': 0, 'player_count': 0, 'total_goals': 0}

        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Databases', match['database'])
        if not os.path.exists(db_path):
            logger.warning(f"Database ikke fundet: {db_path}")
            return {'duration': 0, 'player_count': 0, 'total_goals': 0}

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Find hjemmeholdet
            cursor.execute("""
                SELECT DISTINCT Team_initials 
                FROM game_events 
                WHERE Team_initials IS NOT NULL 
                ORDER BY Time 
                LIMIT 1
            """)
            home_team_row = cursor.fetchone()
            home_team = home_team_row[0] if home_team_row else None
            
            if not home_team:
                logger.error(f"Kunne ikke identificere hjemmeholdet i {db_path}")
                return {'duration': 0, 'player_count': 0, 'total_goals': 0}
            
            # Beregn varighed
            cursor.execute("SELECT MAX(CAST(Time AS INTEGER)) FROM game_events")
            duration = cursor.fetchone()[0] or 0
            
            # Tæl unikke spillere
            cursor.execute("""
                SELECT COUNT(DISTINCT Player_Name) 
                FROM game_events 
                WHERE Player_Name IS NOT NULL AND Player_Name != ''
            """)
            player_count = cursor.fetchone()[0] or 0
            
            # Tæl mål med samme logik som get_final_score
            cursor.execute("""
                SELECT 
                    SUM(CASE 
                        WHEN (Action_1 = 'Mål' OR Action_1 = 'Mål på straffe') 
                        THEN 1 ELSE 0 
                    END) as total_goals
                FROM game_events
                WHERE Action_1 IS NOT NULL
            """)
            total_goals = cursor.fetchone()[0] or 0
            
            stats = {
                'duration': duration,
                'player_count': player_count,
                'total_goals': total_goals
            }
            
            logger.info(f"Statistik beregnet for {match['database']}: {stats}")
            return stats
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Fejl ved beregning af statistik for {match.get('database', 'unknown')}: {str(e)}")
        return {'duration': 0, 'player_count': 0, 'total_goals': 0}

def get_all_matches():
    """
    Henter og formaterer alle kampe fra Databases mappen.
    Returns:
        list: Liste af kampe med deres detaljer
    """
    matches = []
    databases_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Databases')
    
    if not os.path.exists(databases_dir):
        logger.error(f"Databases mappe ikke fundet: {databases_dir}")
        return []
    
    for db_file in os.listdir(databases_dir):
        if not db_file.endswith('.db'):
            continue
            
        db_path = os.path.join(databases_dir, db_file)
        try:
            # Parse filnavnet for at få kampinfo
            match_info = parse_database_filename(db_file)
            if not match_info:
                continue
                
            # Hent kampdata fra databasen
            match_data = get_match_data_from_db(db_path)
            if not match_data:
                continue
                
            # Kombiner information
            match_entry = {
                'date': match_info['date'],
                'home_team': match_info['home_team'],
                'away_team': match_info['away_team'],
                'score': match_data['score'],
                'duration': match_data['duration'],
                'player_count': match_data['player_count'],
                'total_goals': match_data['total_goals'],
                'database': db_file
            }
            
            matches.append(match_entry)
            
        except Exception as e:
            logger.error(f"Fejl ved behandling af {db_file}: {str(e)}")
            continue
    
    # Sorter kampe efter dato (nyeste først)
    matches.sort(key=lambda x: datetime.strptime(x['date'], '%d. %B %Y'), reverse=True)
    return matches

def parse_database_filename(db_file: str) -> dict:
    """
    Parser database filnavn til kampinformation.
    Args:
        db_file (str): Database filnavn
    Returns:
        dict: Matchinfo eller None ved fejl
    """
    try:
        filename = db_file.replace('.db', '')
        date_str, teams = filename.split('_', 1)
        home_team, away_team = teams.replace('_vs_', ' vs ').split(' vs ')
        
        # Konverter dato til læsevenligt format
        date = datetime.strptime(date_str, '%d-%m-%Y').strftime('%d. %B %Y')
        
        return {
            'date': date,
            'home_team': format_team_name(home_team),
            'away_team': format_team_name(away_team)
        }
    except Exception as e:
        logger.error(f"Kunne ikke parse filnavn {db_file}: {str(e)}")
        return None

def get_match_data_from_db(db_path: str) -> dict:
    """
    Henter kampdata fra databasen med forbedret team information.
    """
    try:
        final_score = get_final_score(db_path)
        score_str = f"{final_score[0]}-{final_score[1]}"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Hent holdnavne fra databasen
            cursor.execute("""
                SELECT DISTINCT Team_initials 
                FROM game_events 
                WHERE Team_initials IS NOT NULL 
                ORDER BY Time 
                LIMIT 2
            """)
            teams = cursor.fetchall()
            if len(teams) == 2:
                home_team, away_team = teams[0][0], teams[1][0]
            else:
                logger.error(f"Kunne ikke finde begge hold i {db_path}")
                return None
                
            # Hent kampstatistik
            cursor.execute("""
                SELECT 
                    MAX(CAST(REPLACE(REPLACE(Time, ':', ''), '.', '') AS INTEGER)) as duration,
                    COUNT(DISTINCT CASE WHEN Player_Name IS NOT NULL AND Player_Name != '' THEN Player_Name END) as player_count,
                    COUNT(CASE WHEN Action_1 = 'Mål' OR Action_1 = 'Mål på straffe' THEN 1 END) as total_goals
                FROM game_events
            """)
            stats_row = cursor.fetchone()
            
            return {
                'score': score_str,
                'home_team': format_team_name(home_team),
                'away_team': format_team_name(away_team),
                'duration': stats_row[0] or 0,
                'player_count': stats_row[1] or 0,
                'total_goals': stats_row[2] or 0
            }
    except Exception as e:
        logger.error(f"Fejl ved hentning af kampdata fra {db_path}: {str(e)}")
        return None

def format_match_time(time_str: str) -> str:
    """Formaterer kampens tidsangivelser konsistent"""
    try:
        if not time_str:
            return "0:00"
            
        # Fjern eventuelle ekstra mellemrum
        time_str = time_str.strip()
        
        # Hvis tiden allerede er i format MM:SS
        if ':' in time_str:
            minutes, seconds = map(int, time_str.split(':'))
            return f"{minutes}:{seconds:02d}"
            
        # Konverter fra decimal format til minutter:sekunder
        try:
            minutes, seconds = time_str.split('.')
            minutes = int(minutes)
            seconds = int(float(f"0.{seconds}") * 60)
            return f"{minutes}:{seconds:02d}"
        except ValueError:
            # Hvis tiden er et helt tal
            minutes = int(time_str)
            return f"{minutes}:00"
            
    except Exception as e:
        logger.error(f"Fejl ved formatering af tid '{time_str}': {str(e)}")
        return "0:00"

def calculate_match_score(events: list) -> Tuple[int, int]:
    """Beregner og validerer kampens score baseret på målhændelser"""
    home_score = 0
    away_score = 0
    try:
        if not events:
            logger.warning("Ingen hændelser fundet for kamp")
            return (0, 0)
            
        last_score = None
        for event in events:
            if event.get('score_update'):
                try:
                    scores = event['score_update'].split('-')
                    if len(scores) == 2:
                        last_score = (int(scores[0]), int(scores[1]))
                except (ValueError, IndexError) as e:
                    logger.error(f"Ugyldig score_update format: {event.get('score_update')}")
                    continue
                    
        if last_score:
            return last_score
            
        # Fallback til manuel optælling
        for event in events:
            if event.get('Action_1') == 'Mål':
                if event.get('Team_initials') == 'TTH':
                    home_score += 1
                else:
                    away_score += 1
                    
        return (home_score, away_score)
        
    except Exception as e:
        logger.error(f"Fejl ved beregning af score: {str(e)}")
        return (0, 0)

def validate_player_name(name: str) -> str:
    """Validerer og formaterer spillernavne"""
    try:
        if not name:
            return ""
        # Fjern ekstra mellemrum
        name = " ".join(name.split())
        # Konverter til Title Case
        name = name.title()
        return name
    except Exception as e:
        logger.error(f"Fejl ved validering af spillernavn '{name}': {str(e)}")
        return name

def merge_stats(stats1: Dict, stats2: Dict) -> Dict:
    """Merger to statistik dictionaries korrekt"""
    merged = _get_empty_stats()
    
    try:
        # Merge simple counters
        merged['goals'] = stats1.get('goals', 0) + stats2.get('goals', 0)
        merged['penalties'] = stats1.get('penalties', 0) + stats2.get('penalties', 0)
        
        # Merge team goals
        for team, goals in stats1.get('team_goals', {}).items():
            merged['team_goals'][team] = merged['team_goals'].get(team, 0) + goals
        for team, goals in stats2.get('team_goals', {}).items():
            merged['team_goals'][team] = merged['team_goals'].get(team, 0) + goals
            
        # Merge player actions
        for player, actions in stats1.get('player_actions', {}).items():
            merged['player_actions'][player] = merged['player_actions'].get(player, 0) + actions
        for player, actions in stats2.get('player_actions', {}).items():
            merged['player_actions'][player] = merged['player_actions'].get(player, 0) + actions
            
        # Merge player_count sets
        merged['player_count']['home'] = stats1.get('player_count', {}).get('home', set()) | stats2.get('player_count', {}).get('home', set())
        merged['player_count']['away'] = stats1.get('player_count', {}).get('away', set()) | stats2.get('player_count', {}).get('away', set())
            
    except Exception as e:
        logger.error(f"Fejl ved merge af statistik: {str(e)}")
        
    return merged

def _get_empty_stats() -> Dict:
    """Returnerer en ny dictionary med tomme statistikker"""
    return {
        'goals': 0,
        'penalties': 0,
        'team_goals': {},
        'player_actions': {},
        'player_count': {
            'home': set(),
            'away': set()
        }
    }

def get_match_statistics_detailed(events: list) -> Dict:
    """
    Beregner og validerer detaljerede kampstatistikker.
    Håndterer fejl og validerer data gennem hele processen.
    """
    try:
        if not events:
            logger.warning("Ingen hændelser at beregne statistik fra")
            return {
                'goals': {'home': 0, 'away': 0},
                'shots': {'home': 0, 'away': 0},
                'saves': {'home': 0, 'away': 0},
                'players': {'home': 0, 'away': 0}
            }
            
        # Find hjemmeholdet (første hold der optræder)
        home_team = None
        for event in events:
            if event.get('Team_initials'):
                home_team = event.get('Team_initials')
                break
                
        if not home_team:
            logger.error("Kunne ikke identificere hjemmeholdet")
            return {
                'goals': {'home': 0, 'away': 0},
                'shots': {'home': 0, 'away': 0},
                'saves': {'home': 0, 'away': 0},
                'players': {'home': 0, 'away': 0}
            }
            
        stats = {
            'goals': {'home': 0, 'away': 0},
            'shots': {'home': 0, 'away': 0},
            'saves': {'home': 0, 'away': 0},
            'players': {'home': set(), 'away': set()}
        }
        
        shot_actions = ['Mål', 'Mål på straffe', 'Skud reddet', 'Skud forbi', 'Skud på stolpe', 'Skud blokeret']
        goal_actions = ['Mål', 'Mål på straffe']  # Inkluderer både almindelige mål og straffekast
        save_actions = ['Skud reddet']
        
        # Tæl statistik for hver event
        for event in events:
            try:
                team = event.get('Team_initials', '').strip()
                action = event.get('Action_1', '').strip()
                player_name = event.get('Player_Name', '').strip()
                
                if not team or not action:
                    continue
                    
                is_home = (team == home_team)
                team_key = 'home' if is_home else 'away'
                
                # Tæl skud
                if action in shot_actions:
                    stats['shots'][team_key] += 1
                    
                # Tæl mål (både almindelige og straffekast)
                if action in goal_actions:
                    stats['goals'][team_key] += 1
                    
                # Tæl redninger (tilhører modstanderholdet)
                if action in save_actions:
                    stats['saves']['away' if is_home else 'home'] += 1
                    
                # Tilføj spiller til spillerliste
                if player_name:
                    stats['players'][team_key].add(player_name)
                    
            except Exception as e:
                logger.error(f"Fejl ved behandling af event: {str(e)}")
                continue
        
        # Konverter spillersæt til antal
        stats['players'] = {
            'home': len(stats['players']['home']),
            'away': len(stats['players']['away'])
        }
        
        # Valider målstatistik
        total_goals = stats['goals']['home'] + stats['goals']['away']
        if total_goals == 0:
            logger.warning("Ingen mål registreret i statistikken")
        elif total_goals > 100:
            logger.warning(f"Urealistisk højt antal mål: {total_goals}")
        
        logger.info(f"Beregnet statistik: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Fejl ved beregning af detaljeret statistik: {str(e)}")
        return {
            'goals': {'home': 0, 'away': 0},
            'shots': {'home': 0, 'away': 0},
            'saves': {'home': 0, 'away': 0},
            'players': {'home': 0, 'away': 0}
        }

def _calculate_event_statistics(event: Dict) -> Dict:
    """Beregner statistik for en enkelt event med null-checks"""
    stats = _get_empty_stats()
    
    try:
        # Sikker string håndtering med null-checks
        player_name = event.get('Player_Name', '').strip() if event.get('Player_Name') else ''
        action_1 = event.get('Action_1', '').strip() if event.get('Action_1') else ''
        action_2 = event.get('Action_2', '').strip() if event.get('Action_2') else ''
        team = event.get('Team_initials', '').strip() if event.get('Team_initials') else ''
        
        if action_1 == 'Mål':
            stats['goals'] += 1
            if team:
                stats['team_goals'][team] = stats['team_goals'].get(team, 0) + 1
                
        if player_name:
            stats['player_actions'][player_name] = stats['player_actions'].get(player_name, 0) + 1
            
        if action_2 == 'Straffekast':
            stats['penalties'] += 1
            
    except Exception as e:
        logger.error(f"Fejl ved beregning af event statistik: {str(e)}")
        
    return stats

def _convert_time_to_seconds(time_str: str) -> int:
    """Konverterer tid i format MM:SS eller MM.SS til sekunder"""
    try:
        if not time_str:
            return 0
            
        # Håndter forskellige formater
        if ':' in time_str:
            minutes, seconds = map(int, time_str.split(':'))
        elif '.' in time_str:
            minutes, seconds = map(int, time_str.split('.'))
        else:
            minutes, seconds = int(time_str), 0
            
        return minutes * 60 + seconds
        
    except Exception as e:
        logger.error(f"Fejl ved konvertering af tid '{time_str}': {str(e)}")
        return 0

def get_final_score(database_path: str) -> Tuple[int, int]:
    """
    Henter og validerer kampens endelige score ved at tælle faktiske mål.
    """
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        try:
            # Find hjemmeholdet (første hold der optræder i databasen)
            cursor.execute("""
                SELECT DISTINCT Team_initials 
                FROM game_events 
                WHERE Team_initials IS NOT NULL 
                ORDER BY Time 
                LIMIT 1
            """)
            home_team_row = cursor.fetchone()
            home_team = home_team_row[0] if home_team_row else None
            
            if not home_team:
                logger.error(f"Kunne ikke identificere hjemmeholdet i {database_path}")
                return (0, 0)

            # Tæl faktiske mål for hvert hold
            cursor.execute("""
                SELECT 
                    SUM(CASE 
                        WHEN Team_initials = ? AND (Action_1 = 'Mål' OR Action_1 = 'Mål på straffe') 
                        THEN 1 ELSE 0 
                    END) as home_goals,
                    SUM(CASE 
                        WHEN Team_initials != ? AND Team_initials IS NOT NULL 
                        AND (Action_1 = 'Mål' OR Action_1 = 'Mål på straffe')
                        THEN 1 ELSE 0 
                    END) as away_goals
                FROM game_events
                WHERE Action_1 IS NOT NULL
            """, (home_team, home_team))
            
            goal_counts = cursor.fetchone()
            home_goals = goal_counts[0] if goal_counts and goal_counts[0] is not None else 0
            away_goals = goal_counts[1] if goal_counts and goal_counts[1] is not None else 0
            
            # Valider scorerne
            if home_goals == 0 and away_goals == 0:
                logger.warning(f"Ingen mål fundet i {database_path}")
                return (0, 0)
                
            if home_goals > 100 or away_goals > 100:
                logger.warning(f"Urealistisk høj score ({home_goals}-{away_goals}) i {database_path}")
                return (0, 0)
                
            logger.info(f"Score beregnet for {database_path}: {home_goals}-{away_goals}")
            return (home_goals, away_goals)
            
        finally:
            cursor.close()
            
    except Exception as e:
        logger.error(f"Database fejl ved score beregning for {database_path}: {str(e)}")
        return (0, 0)
    finally:
        if 'conn' in locals():
            conn.close()

def get_match_details(db_path: str) -> Dict:
    """
    Henter detaljerede kampinformationer fra alle relevante tabeller.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Hent grundlæggende kampinfo fra match_data
            cursor.execute("""
                SELECT 
                    home_team_initial,
                    away_team_initial,
                    home_score,
                    away_score,
                    home_team_players,
                    away_team_players,
                    home_team_goalkeepers,
                    away_team_goalkeepers
                FROM match_data
                LIMIT 1
            """)
            match_row = cursor.fetchone()
            
            if not match_row:
                raise ValueError("Ingen match_data fundet")
                
            home_team, away_team, home_score, away_score, \
            home_players, away_players, home_gk, away_gk = match_row
            
            # Hent officielle holdnavne fra team_info
            cursor.execute("""
                SELECT 
                    home_team_name,
                    away_team_name
                FROM team_info
                LIMIT 1
            """)
            team_row = cursor.fetchone()
            
            if team_row:
                home_name, away_name = team_row
            else:
                # Fallback til team_mapping hvis team_info ikke findes
                home_name = format_team_name(home_team)
                away_name = format_team_name(away_team)
            
            # Beregn skudstatistik fra game_events
            cursor.execute("""
                SELECT 
                    Team_initials,
                    COUNT(CASE WHEN Action_1 IN ('Mål', 'Mål på straffe', 
                        'Skud reddet', 'Skud forbi', 'Skud på stolpe', 'Skud blokeret')
                        THEN 1 END) as shots,
                    COUNT(CASE WHEN Action_1 = 'Skud reddet' THEN 1 END) as saves
                FROM game_events
                WHERE Team_initials IS NOT NULL
                GROUP BY Team_initials
            """)
            
            shot_stats = {'home': 0, 'away': 0}
            save_stats = {'home': 0, 'away': 0}
            
            for team, shots, saves in cursor.fetchall():
                is_home = team == home_team
                team_key = 'home' if is_home else 'away'
                shot_stats[team_key] = shots
                # Redninger tælles for det modsatte hold
                save_stats['away' if is_home else 'home'] = saves
            
            return {
                'teams': {
                    'home': {
                        'name': home_name,
                        'initial': home_team,
                        'players': home_players,
                        'goalkeepers': home_gk
                    },
                    'away': {
                        'name': away_name,
                        'initial': away_team,
                        'players': away_players,
                        'goalkeepers': away_gk
                    }
                },
                'score': {
                    'home': home_score,
                    'away': away_score
                },
                'stats': {
                    'shots': shot_stats,
                    'saves': save_stats
                }
            }
            
    except Exception as e:
        logger.error(f"Fejl ved hentning af kampdetaljer: {str(e)}")
        return None

# Registrer template utilities
app.jinja_env.filters['format_team_name'] = format_team_name
app.jinja_env.filters['format_date'] = format_date
app.jinja_env.globals['get_validated_score'] = get_validated_score
app.jinja_env.globals['get_match_statistics'] = get_match_statistics

@app.route('/')
def index():
    """
    Hovedsiden med forbedret datahåndtering og team mapping
    """
    try:
        matches = []
        databases_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Databases')
        
        if not os.path.exists(databases_dir):
            logger.error(f"Databases mappe ikke fundet: {databases_dir}")
            return render_template('index.html', matches=[])
        
        for db_file in os.listdir(databases_dir):
            if not db_file.endswith('.db') or db_file == 'team_mapping.db':
                continue
                
            db_path = os.path.join(databases_dir, db_file)
            try:
                match_data = get_match_data_from_db(db_path)
                if not match_data:
                    continue
                    
                # Parse dato fra filnavn
                date_str = db_file.split('_')[0]
                date = datetime.strptime(date_str, '%d-%m-%Y').strftime('%d. %B %Y')
                
                match_entry = {
                    'date': date,
                    'home_team': match_data['home_team'],
                    'away_team': match_data['away_team'],
                    'score': match_data['score'],
                    'duration': match_data['duration'],
                    'player_count': match_data['player_count'],
                    'total_goals': match_data['total_goals'],
                    'database': db_file
                }
                
                matches.append(match_entry)
                
            except Exception as e:
                logger.error(f"Fejl ved behandling af {db_file}: {str(e)}")
                continue
        
        # Sorter kampe efter dato (nyeste først)
        matches.sort(key=lambda x: datetime.strptime(x['date'], '%d. %B %Y'), reverse=True)
        return render_template('index.html', matches=matches)
        
    except Exception as e:
        logger.error(f"Generel fejl i index route: {str(e)}")
        return render_template('index.html', matches=[])

@app.route('/match/<database>')
def match_details(database):
    """
    Viser detaljerede kampstatistikker med data fra alle relevante tabeller.
    """
    try:
        if not database or not database.endswith('.db'):
            logger.error(f"Ugyldig database parameter: {database}")
            return "Ugyldig forespørgsel", 400
            
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Databases', database)
        if not os.path.exists(db_path):
            logger.warning(f"Database ikke fundet: {db_path}")
            return "Kamp ikke fundet", 404
        
        # Hent alle kampdetaljer
        match_details = get_match_details(db_path)
        if not match_details:
            return "Kunne ikke hente kampdetaljer", 500
        
        # Hent kampbegivenheder
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM game_events 
                ORDER BY CAST(REPLACE(REPLACE(Time, ':', ''), '.', '') AS INTEGER)
            """)
            columns = [col[0] for col in cursor.description]
            events = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Parse dato fra filnavn
        date_str = database.split('_')[0]
        date = datetime.strptime(date_str, '%d-%m-%Y').strftime('%d. %B %Y')
        
        return render_template('match.html',
                             events=events,
                             date=date,
                             home_team=match_details['teams']['home']['name'],
                             away_team=match_details['teams']['away']['name'],
                             score=(match_details['score']['home'], match_details['score']['away']),
                             stats={
                                 'goals': match_details['score'],
                                 'shots': match_details['stats']['shots'],
                                 'saves': match_details['stats']['saves'],
                                 'players': {
                                     'home': match_details['teams']['home']['players'],
                                     'away': match_details['teams']['away']['players']
                                 },
                                 'goalkeepers': {
                                     'home': match_details['teams']['home']['goalkeepers'],
                                     'away': match_details['teams']['away']['goalkeepers']
                                 }
                             })
                             
    except Exception as e:
        logger.error(f"Fejl ved visning af kamp {database}: {str(e)}")
        return "Der opstod en fejl", 500

if __name__ == '__main__':
    app.run(debug=True) 