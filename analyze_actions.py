import sqlite3
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Set, Dict, List
from collections import defaultdict

def setup_logging():
    """Konfigurerer logging med rotation"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'logs/action_analysis_{timestamp}.log'
    
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

def get_unique_actions(db_path: str) -> Dict[str, Set[str]]:
    """Henter unikke værdier for Action_1, Position og Action_2 fra en database"""
    unique_values = {
        'Action_1': set(),
        'Position': set(),
        'Action_2': set()
    }
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            for column in ['Action_1', 'Position', 'Action_2']:
                cursor.execute(f"""
                    SELECT DISTINCT {column}
                    FROM game_events
                    WHERE {column} IS NOT NULL
                    AND {column} != ''
                """)
                
                results = cursor.fetchall()
                unique_values[column].update(row[0] for row in results)
                
        return unique_values
        
    except sqlite3.Error as e:
        logging.error(f"Database fejl for {db_path}: {str(e)}")
        return unique_values
        
    except Exception as e:
        logging.error(f"Uventet fejl ved behandling af {db_path}: {str(e)}")
        return unique_values

def analyze_all_databases():
    """Analyserer alle databaser i Databases mappen"""
    setup_logging()
    logging.info("Starter analyse af handlinger på tværs af databaser")
    
    databases_dir = 'Databases'
    if not os.path.exists(databases_dir):
        logging.error(f"Databases mappe ikke fundet: {databases_dir}")
        return
    
    # Samlede unikke værdier på tværs af alle databaser
    all_unique_values = {
        'Action_1': set(),
        'Position': set(),
        'Action_2': set()
    }
    
    # Tæl forekomster af hver værdi
    value_counts = {
        'Action_1': defaultdict(int),
        'Position': defaultdict(int),
        'Action_2': defaultdict(int)
    }
    
    processed_dbs = 0
    db_files = [f for f in os.listdir(databases_dir) if f.endswith('.db')]
    
    for db_file in db_files:
        db_path = os.path.join(databases_dir, db_file)
        logging.info(f"Analyserer database: {db_file}")
        
        try:
            db_values = get_unique_actions(db_path)
            
            # Opdater samlede unikke værdier og tæl forekomster
            for category, values in db_values.items():
                all_unique_values[category].update(values)
                for value in values:
                    value_counts[category][value] += 1
            
            processed_dbs += 1
            
        except Exception as e:
            logging.error(f"Fejl ved analyse af {db_file}: {str(e)}")
            continue
    
    # Print resultater
    print("\n=== Unikke handlinger fundet på tværs af alle databaser ===")
    
    for category in ['Action_1', 'Position', 'Action_2']:
        print(f"\n{category}:")
        print("-" * 50)
        sorted_values = sorted(all_unique_values[category])
        for value in sorted_values:
            count = value_counts[category][value]
            print(f"- {value:<30} (Findes i {count} databaser)")
    
    logging.info(f"Analyse afsluttet. Behandlet {processed_dbs} af {len(db_files)} databaser")

if __name__ == "__main__":
    analyze_all_databases()