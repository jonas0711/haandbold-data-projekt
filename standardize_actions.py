import sqlite3
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import re
from typing import Tuple, Optional, Dict

def setup_logging():
    """Konfigurerer logging med rotation"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'logs/standardize_actions_{timestamp}.log'
    
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
    logger.setLevel(logging.DEBUG)  # Ændret til DEBUG for mere detaljeret logging
    logger.addHandler(handler)
    
    # Console output
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    logging.info(f"Logger oprettet. Log fil: {log_filename}")

# Definér konstanter for handlinger og positioner
VALID_POSITIONS = {
    'Gbr', 'HB', 'HF', 'PL', 'ST', 'VB', 'VF', '1:e', '2:e'
}

VALID_ACTION1 = {
    'Advarsel', 'Fejlaflevering', 'Fuld tid', 'Halvleg', 'Kamp slut',
    'Mål', 'Mål på straffe', 'Passivt spil', 'Regelfejl', 'Rødt kort, direkte',
    'Skud blokeret', 'Skud forbi', 'Skud på stolpe', 'Skud reddet',
    'Start', 'Start 1:e halvleg', 'Start 2:e halvleg',
    'Straffekast forbi', 'Straffekast på stolpe', 'Straffekast reddet',
    'Tabt bold', 'Tilkendt straffe', 'Time out', 'Udvisning',
    'Video Proof', 'Video Proof slut'
}

VALID_ACTION2 = {
    'Assist', 'Blok af (ret)', 'Blokeret af', 'Bold erobret',
    'Forårs. str.', 'Retur'
}

def extract_position_from_action(action: str) -> Tuple[str, Optional[str]]:
    """Udtrækker position fra en handling hvis den findes."""
    if not action:
        return "", None

    # Special håndtering for Start 1:e/2:e halvleg
    if action.startswith("Start") and ("1:e halvleg" in action or "2:e halvleg" in action):
        return action, None

    # Find position i slutningen af strengen
    for pos in VALID_POSITIONS:
        pattern = f" {pos}$"
        if re.search(pattern, action):
            base_action = action[:-(len(pos)+1)].strip()
            logging.debug(f"Fandt position '{pos}' i '{action}', base_action: '{base_action}'")
            return base_action, pos

    return action, None

def extract_number_from_action2(action2: str) -> Tuple[str, Optional[str]]:
    """Udtrækker spillernummer fra Action_2."""
    if not action2:
        return "", None

    # Find numeriske værdier
    match = re.match(r'^(\d+)$', action2.strip())
    if match:
        return "", match.group(1)

    return action2, None

def handle_uppercase_name(current_name: str, uppercase_name: str) -> str:
    """Håndterer UPPERCASE navne (efternavne)."""
    if not current_name:
        return uppercase_name
    return f"{current_name} {uppercase_name}"

def standardize_event(event: Dict) -> Dict:
    """Standardiserer en enkelt event."""
    updated_event = event.copy()
    changes = []

    # Håndter Action_1 og Position
    if event['Action_1']:
        base_action, position = extract_position_from_action(event['Action_1'])
        if base_action != event['Action_1']:
            changes.append(f"Action_1: '{event['Action_1']}' -> '{base_action}'")
            updated_event['Action_1'] = base_action
        
        if position:
            changes.append(f"Position: '{event['Position']}' -> '{position}'")
            updated_event['Position'] = position

    # Håndter numeriske positioner (skal til Player_number)
    if event['Position'] and event['Position'].isdigit():
        changes.append(f"Flytter position '{event['Position']}' til Player_number")
        updated_event['Player_number'] = event['Position']
        updated_event['Position'] = ''

    # Håndter Action_2
    if event['Action_2']:
        # Special håndtering for "1:e halvleg"
        if event['Action_2'] == "1:e halvleg":
            updated_event['Action_1'] = "Start 1:e halvleg"
            updated_event['Action_2'] = ''
            changes.append("Flyttet '1:e halvleg' til Action_1")
        else:
            action2, player_number = extract_number_from_action2(event['Action_2'])
            if player_number:
                updated_event['Action_2'] = ''
                updated_event['Player2_Number'] = player_number
                changes.append(f"Flyttet nummer '{player_number}' til Player2_Number")
            elif event['Action_2'].isupper():
                # Håndter UPPERCASE navne
                updated_name = handle_uppercase_name(event['Player_Name'], event['Action_2'])
                updated_event['Player_Name'] = updated_name
                updated_event['Action_2'] = ''
                changes.append(f"Flyttet efternavn '{event['Action_2']}' til Player_Name")

    if changes:
        logging.debug(f"Ændringer i event: {', '.join(changes)}")

    return updated_event

def update_database(db_path: str) -> bool:
    """Opdaterer en enkelt database med standardiserede handlinger"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Hent alle rækker med deres kolonnenavne
            cursor.execute("PRAGMA table_info(game_events)")
            columns = [col[1] for col in cursor.fetchall()]
            
            cursor.execute("SELECT rowid, * FROM game_events")
            rows = cursor.fetchall()
            
            # Tilføj rowid til kolonner
            all_columns = ['rowid'] + columns
            
            updates = 0
            for row in rows:
                # Konverter række til dictionary
                event = dict(zip(all_columns, row))
                
                # Standardiser event
                updated_event = standardize_event(event)
                
                # Tjek om der er ændringer
                if event != updated_event:
                    # Byg UPDATE query dynamisk
                    set_clauses = []
                    values = []
                    for col in columns:
                        if col in updated_event and updated_event[col] != event[col]:
                            set_clauses.append(f"{col} = ?")
                            values.append(updated_event[col])
                    
                    if set_clauses and values:
                        # Log detaljeret information om ændringer
                        changes_description = []
                        for col, val in zip(set_clauses, values):
                            col_name = col.split('=')[0].strip()
                            old_val = event.get(col_name, 'None')
                            changes_description.append(f"{col_name}: '{old_val}' -> '{val}'")
                        
                        logging.debug(f"Række {event['rowid']} ændringer: {', '.join(changes_description)}")
                        
                        query = f"""
                            UPDATE game_events 
                            SET {', '.join(set_clauses)}
                            WHERE rowid = ?
                        """
                        values.append(event['rowid'])
                        
                        cursor.execute(query, values)
                        updates += 1
                        
                        logging.debug(f"Opdateret række {event['rowid']}: {', '.join(set_clauses)}")
            
            conn.commit()
            logging.info(f"Opdateret {updates} rækker i {os.path.basename(db_path)}")
            return True
            
    except Exception as e:
        logging.error(f"Fejl ved opdatering af {db_path}: {str(e)}", exc_info=True)
        return False

def main():
    """Hovedfunktion der opdaterer alle databaser"""
    setup_logging()
    logging.info("Starter standardisering af handlinger og positioner")
    
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