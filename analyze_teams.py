import sqlite3
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Set, Dict, Tuple
from pathlib import Path

# Custom exceptions
class TeamAnalysisError(Exception):
    """Base exception for team analysis"""
    pass

def setup_logging():
    """Konfigurerer logging med rotation"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'logs/team_analysis_{timestamp}.log'
    
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

def extract_teams_from_filename(db_name: str) -> Tuple[str, str]:
    """Udtrækker holdnavne fra database filnavn"""
    try:
        # Format: date_hometeam_vs_awayteam.db
        filename = db_name.replace('.db', '')
        _, teams = filename.split('_', 1)
        home_team, away_team = teams.replace('_vs_', ' vs ').split(' vs ')
        
        return home_team.strip(), away_team.strip()
    except Exception as e:
        logging.error(f"Kunne ikke udtrække holdnavne fra {db_name}: {str(e)}")
        return None, None

def get_team_initials_from_db(db_path: str) -> Set[str]:
    """Henter alle unikke Team_initials fra en database"""
    team_initials = set()
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT Team_initials 
                FROM game_events 
                WHERE Team_initials IS NOT NULL 
                AND Team_initials != ''
            """)
            
            for row in cursor.fetchall():
                team_initials.add(row[0])
                
        return team_initials
        
    except sqlite3.Error as e:
        logging.error(f"Database fejl for {db_path}: {str(e)}")
        return set()

def analyze_teams():
    """Analyserer alle hold på tværs af databaser"""
    setup_logging()
    logging.info("Starter team analyse")
    
    databases_dir = 'Databases'
    if not os.path.exists(databases_dir):
        logging.error(f"Databases mappe ikke fundet: {databases_dir}")
        return
    
    # Initialiser samlinger til resultater
    all_team_initials = set()  # Til Team_initials fra game_events
    all_team_names = set()     # Til holdnavne fra filnavne
    team_mapping = {}          # Mapper team_initials til fulde navne
    
    db_files = [f for f in os.listdir(databases_dir) if f.endswith('.db')]
    logging.info(f"Fundet {len(db_files)} databaser at analysere")
    
    # Gennemgå hver database
    for db_file in db_files:
        db_path = os.path.join(databases_dir, db_file)
        logging.info(f"Analyserer database: {db_file}")
        
        try:
            # Udtræk holdnavne fra filnavn
            home_team, away_team = extract_teams_from_filename(db_file)
            if home_team and away_team:
                all_team_names.add(home_team)
                all_team_names.add(away_team)
            
            # Hent team initials fra databasen
            db_team_initials = get_team_initials_from_db(db_path)
            all_team_initials.update(db_team_initials)
            
            # Forsøg at mappe initials til fulde navne
            if home_team and away_team and len(db_team_initials) == 2:
                sorted_initials = sorted(db_team_initials)
                sorted_names = sorted([home_team, away_team])
                
                for initial, name in zip(sorted_initials, sorted_names):
                    if initial not in team_mapping:
                        team_mapping[initial] = set()
                    team_mapping[initial].add(name)
                
        except Exception as e:
            logging.error(f"Fejl ved analyse af {db_file}: {str(e)}")
            continue
    
    # Print resultater
    print("\n=== Team Initials fra game_events ===")
    print(f"Antal unikke team initials: {len(all_team_initials)}")
    for initial in sorted(all_team_initials):
        print(f"- {initial}")
    
    print("\n=== Klubnavne fra database filnavne ===")
    print(f"Antal unikke klubnavne: {len(all_team_names)}")
    for name in sorted(all_team_names):
        print(f"- {name}")
    
    print("\n=== Mulig mapping mellem initials og klubnavne ===")
    for initial, names in sorted(team_mapping.items()):
        print(f"{initial}:")
        for name in sorted(names):
            print(f"  - {name}")
    
    # Log statistik
    logging.info(f"Analyse afsluttet. Fundet {len(all_team_initials)} unikke team initials og {len(all_team_names)} unikke klubnavne")

if __name__ == "__main__":
    analyze_teams()