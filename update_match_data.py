import sqlite3
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Dict, List, Tuple, Set

def setup_logging():
    """Konfigurerer logging med rotation"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'logs/update_match_data_{timestamp}.log'
    
    handler = RotatingFileHandler(
        log_filename,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # Console output
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    logging.info(f"Logger oprettet. Log fil: {log_filename}")

def get_final_score(cursor: sqlite3.Cursor) -> Tuple[int, int]:
    """Henter sidste score_update og parser det til home/away score"""
    try:
        cursor.execute("""
            SELECT Score_update 
            FROM game_events 
            WHERE Score_update IS NOT NULL 
            ORDER BY CAST(REPLACE(REPLACE(Time, ':', ''), '.', '') AS INTEGER) DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result and result[0]:
            scores = result[0].split('-')
            if len(scores) == 2:
                return int(scores[0]), int(scores[1])
        
        return 0, 0
    except Exception as e:
        logging.error(f"Fejl ved hentning af slutscore: {str(e)}")
        return 0, 0

def get_team_initials(cursor: sqlite3.Cursor) -> Tuple[str, str]:
    """Finder home og away team initials"""
    try:
        cursor.execute("""
            SELECT DISTINCT Team_initials 
            FROM game_events 
            WHERE Team_initials IS NOT NULL 
            ORDER BY Time 
            LIMIT 2
        """)
        
        teams = cursor.fetchall()
        if len(teams) == 2:
            return teams[0][0], teams[1][0]
        return "", ""
    except Exception as e:
        logging.error(f"Fejl ved hentning af team initials: {str(e)}")
        return "", ""

def get_team_players(cursor: sqlite3.Cursor, team_initial: str) -> Tuple[Set[str], Set[str]]:
    """Finder field players og goalkeepers for et hold"""
    try:
        field_players = set()
        
        # 1. Primære spillere fra Player_Name
        cursor.execute("""
            SELECT DISTINCT Player_Name 
            FROM game_events 
            WHERE Team_initials = ? AND Player_Name IS NOT NULL AND Player_Name != ''
        """, (team_initial,))
        field_players.update(row[0] for row in cursor.fetchall())
        
        # 2. Spillere fra samme hold (Player2_Name)
        cursor.execute("""
            SELECT DISTINCT Player2_Name
            FROM game_events 
            WHERE Team_initials = ? 
            AND Action_2 IN ('Assist', 'Mål')
            AND Player2_Name IS NOT NULL 
            AND Player2_Name != ''
        """, (team_initial,))
        field_players.update(row[0] for row in cursor.fetchall())
        
        # 3. Spillere fra modstanderholdet ved defensive aktioner
        cursor.execute("""
            SELECT DISTINCT Player2_Name
            FROM game_events 
            WHERE Team_initials != ? 
            AND Action_2 IN (
                'Blok af (ret)',
                'Blokeret af',
                'Bold erobret',
                'Forårs. str.'
            )
            AND Player2_Name IS NOT NULL 
            AND Player2_Name != ''
        """, (team_initial,))
        field_players.update(row[0] for row in cursor.fetchall())
        
        # 4. Find målmænd (fra Goalkeeper_Name hvor Team_initials IKKE er holdets)
        cursor.execute("""
            SELECT DISTINCT Goalkeeper_Name 
            FROM game_events 
            WHERE Team_initials != ? 
            AND Goalkeeper_Name IS NOT NULL 
            AND Goalkeeper_Name != ''
        """, (team_initial,))
        goalkeepers = {row[0] for row in cursor.fetchall()}
        
        # Log statistik for debugging
        logging.debug(f"""
            Hold {team_initial}:
            - Antal markspillere: {len(field_players)}
            - Antal målmænd: {len(goalkeepers)}
        """)
        
        return field_players, goalkeepers
        
    except Exception as e:
        logging.error(f"Fejl ved hentning af spillere for {team_initial}: {str(e)}")
        return set(), set()

def create_match_data_table(cursor: sqlite3.Cursor):
    """Opretter match_data tabel"""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS match_data (
        home_team_initial TEXT NOT NULL,
        away_team_initial TEXT NOT NULL,
        home_score INTEGER NOT NULL,
        away_score INTEGER NOT NULL,
        home_team_players INTEGER NOT NULL,
        away_team_players INTEGER NOT NULL,
        home_team_goalkeepers INTEGER NOT NULL,
        away_team_goalkeepers INTEGER NOT NULL
    )
    ''')

def create_players_table(cursor: sqlite3.Cursor):
    """Opretter players tabel"""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        team_initial TEXT NOT NULL,
        player_name TEXT NOT NULL,
        player_type TEXT NOT NULL,
        PRIMARY KEY (team_initial, player_name)
    )
    ''')

def update_database(db_path: str):
    """Opdaterer en enkelt database med match_data og players"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Opret tabeller
            create_match_data_table(cursor)
            create_players_table(cursor)
            
            # Hent nødvendig data
            home_score, away_score = get_final_score(cursor)
            home_team, away_team = get_team_initials(cursor)
            
            if not home_team or not away_team:
                logging.error(f"Kunne ikke finde team initials i {db_path}")
                return False
            
            # Hent spillere for hvert hold
            home_field_players, home_goalkeepers = get_team_players(cursor, home_team)
            away_field_players, away_goalkeepers = get_team_players(cursor, away_team)
            
            # Opdater match_data tabel
            cursor.execute('''
                INSERT OR REPLACE INTO match_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                home_team,
                away_team,
                home_score,
                away_score,
                len(home_field_players),
                len(away_field_players),
                len(home_goalkeepers),
                len(away_goalkeepers)
            ))
            
            # Opdater players tabel
            # Home team players
            for player in home_field_players:
                cursor.execute('''
                    INSERT OR REPLACE INTO players VALUES (?, ?, ?)
                ''', (home_team, player, 'Field player'))
            
            for player in home_goalkeepers:
                cursor.execute('''
                    INSERT OR REPLACE INTO players VALUES (?, ?, ?)
                ''', (home_team, player, 'Goalkeeper'))
            
            # Away team players
            for player in away_field_players:
                cursor.execute('''
                    INSERT OR REPLACE INTO players VALUES (?, ?, ?)
                ''', (away_team, player, 'Field player'))
            
            for player in away_goalkeepers:
                cursor.execute('''
                    INSERT OR REPLACE INTO players VALUES (?, ?, ?)
                ''', (away_team, player, 'Goalkeeper'))
            
            conn.commit()
            logging.info(f"Database {db_path} opdateret succesfuldt")
            return True
            
    except Exception as e:
        logging.error(f"Fejl ved opdatering af {db_path}: {str(e)}")
        return False

def main():
    """Hovedfunktion der opdaterer alle databaser"""
    setup_logging()
    logging.info("Starter opdatering af match data")
    
    databases_dir = 'Databases'
    if not os.path.exists(databases_dir):
        logging.error(f"Databases mappe ikke fundet: {databases_dir}")
        return
    
    successful_updates = 0
    failed_updates = 0
    
    for db_file in os.listdir(databases_dir):
        if db_file.endswith('.db'):
            db_path = os.path.join(databases_dir, db_file)
            logging.info(f"Behandler database: {db_file}")
            
            if update_database(db_path):
                successful_updates += 1
            else:
                failed_updates += 1
    
    logging.info(f"Opdatering afsluttet. Succes: {successful_updates}, Fejl: {failed_updates}")

if __name__ == "__main__":
    main()