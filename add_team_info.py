import sqlite3
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Dict, Tuple, Optional
from pathlib import Path

# Custom exceptions
class TeamInfoError(Exception):
    """Base exception for team info handling"""
    pass

def setup_logging():
    """Konfigurerer logging med rotation"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'logs/team_info_{timestamp}.log'
    
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

def load_team_mapping() -> Dict:
    """Indlæser team mapping fra JSON filen"""
    try:
        with open('team_mapping.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Kunne ikke læse team_mapping.json: {str(e)}")
        raise TeamInfoError("Fejl ved indlæsning af team mapping")

def clean_team_name(name: str) -> str:
    """Renser holdnavn for specielle karakterer"""
    # Fjern underscores og standardiser mellemrum
    name = name.replace('_', ' ')
    # Fjern dobbelte mellemrum
    name = ' '.join(name.split())
    return name.strip()

def normalize_team_name(name: str) -> str:
    """Normaliserer holdnavne til standard format"""
    name = clean_team_name(name)
    
    # Håndter specielle tilfælde
    if "Bjerringbro" in name and "Silkeborg" in name:
        return "Bjerringbro-Silkeborg"
    elif "Ribe" in name and "Esbjerg" in name:
        return "Ribe-Esbjerg HH"
    elif "Mors" in name and "Thy" in name:
        return "Mors-Thy Håndbold"
        
    return name

def extract_teams_from_filename(db_name: str) -> Tuple[str, str]:
    """Udtrækker holdnavne fra database filnavn"""
    try:
        # Format: date_hometeam_vs_awayteam.db
        filename = db_name.replace('.db', '')
        _, teams = filename.split('_', 1)

        # Special cases for specific match-ups
        if "Bjerringbro_vs_Silkeborg_-_SAH___Skanderborg_AGF" in teams:
            return "Bjerringbro-Silkeborg", "SAH___Skanderborg_AGF"
        elif "Mors_vs_Thy_H_ndbold_-_TTH_Holstebro" in teams:
            return "Mors-Thy_H_ndbold", "TTH_Holstebro"
        elif "Ribe_vs_Esbjerg_HH_-_KIF_Kolding" in teams:
            return "Ribe-Esbjerg_HH", "KIF_Kolding"
        elif "Ribe_vs_Esbjerg_HH_-_Nordsj_lland_H_ndbold" in teams:
            return "Ribe-Esbjerg_HH", "Nordsj_lland_H_ndbold"
        elif "Bjerringbro_vs_Silkeborg_-_Skjern_H_ndbold" in teams:
            return "Bjerringbro-Silkeborg", "Skjern_H_ndbold"
        
        # Standard handling for other cases
        if ' - ' in teams:
            first_part, second_part = teams.split(' - ')
            
            if '_vs_' in first_part:
                home_team = first_part.split('_vs_')[0]
                away_team = second_part
            elif 'vs' in first_part:
                home_team = first_part.split('vs')[0]
                away_team = second_part
            else:
                home_team = first_part
                away_team = second_part
        else:
            if '_vs_' in teams:
                home_team, away_team = teams.split('_vs_')
            elif 'vs' in teams:
                home_team, away_team = teams.split('vs')
            else:
                raise ValueError(f"Ugyldigt filnavnformat: {teams}")
        
        # Rens og normaliser navne
        home_team = normalize_team_name(home_team)
        away_team = normalize_team_name(away_team)
        
        logging.debug(f"Udtrukket holdnavne: '{home_team}' vs '{away_team}'")
        return home_team, away_team
        
    except Exception as e:
        logging.error(f"Kunne ikke udtrække holdnavne fra {db_name}: {str(e)}")
        return None, None

def find_team_initial(team_name: str, team_mapping: Dict) -> Optional[str]:
    """Finder team initial baseret på navnet"""
    normalized_name = normalize_team_name(team_name)
    
    for initial, team_data in team_mapping['teams'].items():
        # Check mod normaliserede variationer
        variations = [normalize_team_name(var) for var in team_data['variations']]
        if normalized_name in variations or normalized_name == normalize_team_name(team_data['full_name']):
            return initial
    return None

def analyze_failed_matches(db_path: str, team_mapping: Dict):
    """Analyserer og printer detaljeret information om fejlede matches"""
    try:
        db_name = os.path.basename(db_path)
        home_team, away_team = extract_teams_from_filename(db_name)
        
        print(f"\nFejlanalyse for {db_name}:")
        print("=" * 50)
        print(f"Original filnavn: {db_name}")
        print(f"Udtrukket hjemmehold: '{home_team}'")
        print(f"Udtrukket udehold: '{away_team}'")
        
        if home_team and away_team:
            home_initial = find_team_initial(home_team, team_mapping)
            away_initial = find_team_initial(away_team, team_mapping)
            
            print("\nInitial matching:")
            print(f"Hjemmehold '{home_team}' -> {home_initial if home_initial else 'IKKE FUNDET'}")
            print(f"Udehold '{away_team}' -> {away_initial if away_initial else 'IKKE FUNDET'}")
            
            if not home_initial:
                print("\nMulige matches for hjemmeholdet:")
                for initial, data in team_mapping['teams'].items():
                    print(f"- {initial}: {data['variations']}")
                    
            if not away_initial:
                print("\nMulige matches for udeholdet:")
                for initial, data in team_mapping['teams'].items():
                    print(f"- {initial}: {data['variations']}")
        else:
            print("FEJL: Kunne ikke udtrække holdnavne fra filnavnet")
            
    except Exception as e:
        print(f"Fejl under analyse: {str(e)}")

def create_team_info_table(cursor: sqlite3.Cursor):
    """Opretter team_info tabel hvis den ikke eksisterer"""
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_info (
            home_team_name TEXT NOT NULL,
            home_team_initial TEXT NOT NULL,
            away_team_name TEXT NOT NULL,
            away_team_initial TEXT NOT NULL,
            match_date TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (home_team_name, away_team_name, match_date)
        )
        ''')
    except sqlite3.Error as e:
        logging.error(f"Fejl ved oprettelse af team_info tabel: {str(e)}")
        raise TeamInfoError("Kunne ikke oprette team_info tabel")

def update_database(db_path: str, team_mapping: Dict):
    """Opdaterer en enkelt database med team information"""
    try:
        db_name = os.path.basename(db_path)
        home_team, away_team = extract_teams_from_filename(db_name)
        
        if not home_team or not away_team:
            logging.error(f"Kunne ikke udtrække holdnavne fra {db_name}")
            analyze_failed_matches(db_path, team_mapping)
            return False
            
        # Find team initials
        home_initial = find_team_initial(home_team, team_mapping)
        away_initial = find_team_initial(away_team, team_mapping)
        
        if not home_initial or not away_initial:
            logging.error(f"Kunne ikke finde initials for hold i {db_name}")
            analyze_failed_matches(db_path, team_mapping)
            return False
            
        # Find match dato fra filnavn
        match_date = db_name.split('_')[0]  # Format: dd-mm-yyyy
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Opret team_info tabel
            create_team_info_table(cursor)
            
            # Indsæt eller opdater team information
            cursor.execute('''
                INSERT OR REPLACE INTO team_info 
                (home_team_name, home_team_initial, away_team_name, away_team_initial, match_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (home_team, home_initial, away_team, away_initial, match_date))
            
            conn.commit()
            logging.info(f"Team info opdateret for {db_name}")
            return True
            
    except Exception as e:
        logging.error(f"Fejl ved opdatering af {db_path}: {str(e)}")
        return False

def main():
    """Hovedfunktion der opdaterer alle databaser"""
    setup_logging()
    logging.info("Starter tilføjelse af team information")
    
    try:
        team_mapping = load_team_mapping()
    except TeamInfoError:
        logging.error("Kunne ikke fortsætte uden team mapping")
        return
    
    databases_dir = 'Databases'
    if not os.path.exists(databases_dir):
        logging.error(f"Databases mappe ikke fundet: {databases_dir}")
        return
    
    db_files = [f for f in os.listdir(databases_dir) if f.endswith('.db')]
    logging.info(f"Fundet {len(db_files)} databaser at opdatere")
    
    successful_updates = 0
    failed_updates = 0
    failed_files = []
    
    for db_file in db_files:
        db_path = os.path.join(databases_dir, db_file)
        logging.info(f"Behandler database: {db_file}")
        
        try:
            if update_database(db_path, team_mapping):
                successful_updates += 1
            else:
                failed_updates += 1
                failed_files.append(db_file)
                
        except Exception as e:
            logging.error(f"Fejl ved behandling af {db_file}: {str(e)}")
            failed_updates += 1
            failed_files.append(db_file)
    
    # Print samlet statistik
    print("\nOpdatering afsluttet")
    print("=" * 50)
    print(f"Succesfulde opdateringer: {successful_updates}")
    print(f"Fejlede opdateringer: {failed_updates}")
    
    if failed_files:
        print("\nFejlede filer:")
        for file in failed_files:
            print(f"- {file}")

if __name__ == "__main__":
    main()