import json
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging():
    """Konfigurerer logging med rotation"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'logs/create_mapping_{timestamp}.log'
    
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

def create_team_mapping():
    """Opretter team mapping JSON fil"""
    team_mapping = {
        "teams": {
            "AAH": {
                "full_name": "Aalborg Håndbold",
                "variations": [
                    "Aalborg_H_ndbold",
                    "Aalborg Håndbold"
                ]
            },
            "BSH": {
                "full_name": "Bjerringbro-Silkeborg",
                "variations": [
                    "Bjerringbro-Silkeborg",
                    "Bjerringbro",
                    "Bjerringbro vs Silkeborg",
                    "Bjerringbro_vs_Silkeborg",
                    "Silkeborg"
                ]
            },
            "FHK": {
                "full_name": "Fredericia Håndbold Klub",
                "variations": [
                    "Fredericia_H_ndbold_Klub",
                    "Fredericia Håndbold Klub"
                ]
            },
            "GIF": {
                "full_name": "Grindsted GIF Håndbold",
                "variations": [
                    "Grindsted_GIF__H_ndbold",
                    "Grindsted GIF Håndbold"
                ]
            },
            "GOG": {
                "full_name": "GOG",
                "variations": [
                    "GOG"
                ]
            },
            "KIF": {
                "full_name": "KIF Kolding",
                "variations": [
                    "KIF_Kolding",
                    "KIF Kolding",
                    "Kolding"
                ]
            },
            "MTH": {
                "full_name": "Mors-Thy Håndbold",
                "variations": [
                    "Mors-Thy_H_ndbold",
                    "Mors-Thy Håndbold",
                    "Mors",
                    "Thy_H_ndbold",
                    "Mors vs Thy H_ndbold",
                    "Mors_vs_Thy"
                ]
            },
            "NSH": {
                "full_name": "Nordsjælland Håndbold",
                "variations": [
                    "Nordsj_lland_H_ndbold",
                    "Nordsjælland Håndbold",
                    "Nordsjælland"
                ]
            },
            "REH": {
                "full_name": "Ribe-Esbjerg HH",
                "variations": [
                    "Ribe-Esbjerg_HH",
                    "Ribe-Esbjerg HH",
                    "Ribe",
                    "Ribe vs Esbjerg",
                    "Ribe vs Esbjerg HH",
                    "Ribe_vs_Esbjerg",
                    "Esbjerg"
                ]
            },
            "SAH": {
                "full_name": "Skanderborg Aarhus Håndbold",
                "variations": [
                    "SAH___Skanderborg_AGF",
                    "Skanderborg Aarhus",
                    "Skanderborg AGF",
                    "Skanderborg"
                ]
            },
            "SJE": {
                "full_name": "Sønderjyske Herrehåndbold",
                "variations": [
                    "S_nderjyske_Herreh_ndbold",
                    "Sønderjyske",
                    "SønderjyskE"
                ]
            },
            "SKH": {
                "full_name": "Skjern Håndbold",
                "variations": [
                    "Skjern_H_ndbold",
                    "Skjern Håndbold",
                    "Skjern"
                ]
            },
            "TMS": {
                "full_name": "TMS Ringsted",
                "variations": [
                    "TMS_Ringsted",
                    "TMS Ringsted",
                    "Ringsted"
                ]
            },
            "TTH": {
                "full_name": "TTH Holstebro",
                "variations": [
                    "TTH_Holstebro",
                    "TTH Holstebro",
                    "Holstebro"
                ]
            }
        },
        "metadata": {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "total_teams": 14,
            "source": "game_events and database filenames analysis",
            "encoding": "UTF-8"
        }
    }

    try:
        with open('team_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(team_mapping, f, ensure_ascii=False, indent=4)
        logging.info("Team mapping fil oprettet succesfuldt")
        return True
    except Exception as e:
        logging.error(f"Fejl ved oprettelse af team mapping fil: {str(e)}")
        return False

if __name__ == "__main__":
    setup_logging()
    create_team_mapping()