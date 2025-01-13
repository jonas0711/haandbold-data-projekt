import sqlite3
import re
from openai import OpenAI
import os
import shutil
from typing import List, Dict
import json
from dotenv import load_dotenv
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential
from pdf import convert_pdf_to_text

# Custom exceptions
class HandballParserError(Exception):
    """Base exception for handball parser"""
    pass

class APIError(HandballParserError):
    """API related errors"""
    pass

class DatabaseError(HandballParserError):
    """Database related errors"""
    pass

def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'logs/handball_parser_{timestamp}.log'
    
    # Tilføj rotation
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

# Load environment variables
load_dotenv()
setup_logging()

# DeepSeek API setup med retry
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def init_api_client():
    logging.info("Initialiserer DeepSeek API klient")
    return OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )

client = init_api_client()

def extract_game_info(content: str) -> tuple:
    """Udtræk dato og holdnavne fra teksten"""
    logging.info("Starter udtrækning af kampinformation")
    
    # Find dato i formatet d-m-yyyy eller dd-m-yyyy eller d-mm-yyyy eller dd-mm-yyyy
    import re
    date_pattern = r'(\d{1,2})-(\d{1,2})-(\d{4})'
    date_match = re.search(date_pattern, content)
    
    if not date_match:
        logging.error("Kunne ikke finde dato i teksten")
        raise ValueError("Kunne ikke finde dato i teksten")
    
    # Konverter dato til dd-mm-yyyy format
    day = date_match.group(1).zfill(2)
    month = date_match.group(2).zfill(2)
    year = date_match.group(3)
    date = f"{day}-{month}-{year}"
    
    logging.info(f"Fundet dato: {date}")
    
    # Find holdnavne efter "KAMPHÆNDELSER"
    teams_pattern = r'KAMPHÆNDELSER\s+([^-]+)-([^0-9]+)'
    teams_match = re.search(teams_pattern, content)
    
    if not teams_match:
        logging.error("Kunne ikke finde holdnavne i teksten")
        raise ValueError("Kunne ikke finde holdnavne i teksten")
    
    home_team = teams_match.group(1).strip()
    away_team = teams_match.group(2).strip()
    
    logging.info(f"Fundet hold: {home_team} vs {away_team}")
    
    return date, home_team, away_team

def create_database(content: str) -> tuple:
    logging.info("Starter oprettelse af database")
    try:
        # Udtræk kampinformation
        logging.debug("Udtrækker kampinformation")
        date, home_team, away_team = extract_game_info(content)
        
        # Opret database navn
        db_name = f"{date}_{home_team}_vs_{away_team}.db"
        logging.debug(f"Oprindeligt database navn: {db_name}")
        
        # Erstat ugyldige filnavns karakterer
        db_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', db_name)
        logging.info(f"Renset database navn: {db_name}")
        
        # Sikr at Databases mappen eksisterer
        if not os.path.exists('Databases'):
            logging.info("Opretter Databases mappe")
            os.makedirs('Databases')
        
        # Opret fuld sti til databasen
        db_path = os.path.join('Databases', db_name)
        logging.info(f"Fuld database sti: {db_path}")
        
        # Tjek om databasen allerede eksisterer
        if os.path.exists(db_path):
            logging.warning(f"Database eksisterer allerede: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        logging.debug("Database forbindelse oprettet")
        
        logging.debug("Opretter tabel struktur")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_events (
            Time TEXT NOT NULL,
            Score_update TEXT,
            Team_initials TEXT,
            Action_1 TEXT,
            Position TEXT,
            Player_number TEXT,
            Player_Name TEXT,
            Action_2 TEXT,
            Player2_Number TEXT,
            Player2_Name TEXT,
            Goalkeeper_Number TEXT,
            Goalkeeper_Name TEXT,
            Section_number INTEGER
        )
        ''')
        
        logging.debug("Opretter indekser")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time ON game_events(Time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_team ON game_events(Team_initials)')
        
        conn.commit()
        logging.info("Database struktur oprettet succesfuldt")
        return conn, cursor
    except Exception as e:
        logging.error(f"Fejl ved oprettelse af database: {str(e)}", exc_info=True)
        raise DatabaseError(f"Database fejl: {str(e)}")

def extract_sections(content: str) -> List[str]:
    """Udtræk sektioner fra Tid til KAMPHÆNDELSER eller Software og opdel i mindre sektioner"""
    logging.info("Starter udtrækning af sektioner")
    main_sections = []
    lines = content.split('\n')
    current_section = []
    in_section = False
    
    for i, line in enumerate(lines, 1):
        if "Tid" in line and not in_section:
            logging.debug(f"Fandt hovedsektion start på linje {i}: {line}")
            in_section = True
            current_section = [line]
        elif in_section:
            if "KAMPHÆNDELSER" in line or "Software" in line:
                logging.debug(f"Fandt hovedsektion slut på linje {i}: {line}")
                if current_section:
                    main_sections.append(current_section)
                    logging.info(f"Gemte hovedsektion med {len(current_section)} linjer")
                current_section = []
                in_section = False
            else:
                current_section.append(line)
    
    if current_section:
        main_sections.append(current_section)
        logging.info(f"Gemte sidste hovedsektion med {len(current_section)} linjer")
    
    final_sections = []
    for section_num, main_section in enumerate(main_sections, 1):
        header = main_section[0]
        content_lines = main_section[1:]
        
        for i in range(0, len(content_lines), 24):
            subsection = [header] + content_lines[i:i+24]
            final_sections.append('\n'.join(subsection))
            logging.info(f"Oprettet delsektion {len(final_sections)} fra hovedsektion {section_num} "
                        f"med {len(subsection)} linjer")
    
    return final_sections

def get_system_prompt() -> str:
    """
    Returnerer system prompten der bruges til at instruere AI modellen.
    """
    logging.debug("Henter system prompt")
    return """Du er en assistent der hjælper med at analysere håndboldkampe.
Din opgave er at konvertere kampbegivenheder til et struktureret JSON format.

Outputtet skal være i følgende format:
{
    "events": [
        {
            "Time": "mm.ss",
            "ScoreUpdate": "score hvis relevant",
            "TeamInitials": "holdets initialer",
            "Action1": "primær handling",
            "Position": "position hvis relevant",
            "PlayerNumber": "spillernummer",
            "PlayerName": "spillernavn",
            "Action2": "sekundær handling hvis relevant",
            "Player2Number": "andet spillernummer hvis relevant",
            "Player2Name": "andet spillernavn hvis relevant",
            "GoalkeeperNumber": "målmandsnummer hvis relevant",
            "GoalkeeperName": "målmandsnavn hvis relevant"
        }
    ]
}

Regler:
1. Tid skal altid være i formatet "mm.ss"
2. Alle felter er valgfrie undtagen Time
3. Kun inkluder felter der er relevante for begivenheden
4. Bevar de originale navne og numre præcist som de står
5. Konverter alle handlinger til samme format som i inputtet
"""

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def process_section_with_deepseek(section_text: str, section_number: int) -> List[Dict]:
    """Process section with retry capability"""
    logging.debug(f"Starter behandling af sektion {section_number} med DeepSeek API")
    try:
        logging.debug("Sender anmodning til DeepSeek API")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": section_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.1  # Lav temperatur for mere konsistente resultater
        )
        
        content = response.choices[0].message.content
        logging.debug("Modtog svar fra DeepSeek API")
        
        try:
            parsed_data = json.loads(content)
            events = parsed_data.get("events", [])
            
            # Valider events
            valid_events = []
            for event in events:
                if validate_event(event):
                    valid_events.append(event)
                else:
                    logging.warning(f"Ugyldig begivenhed fundet i sektion {section_number}: {event}")
            
            logging.info(f"Behandlet sektion {section_number}: {len(valid_events)} gyldige begivenheder fundet")
            return valid_events
            
        except json.JSONDecodeError as je:
            logging.error(f"JSON parsing fejl i sektion {section_number}: {str(je)}")
            raise APIError(f"Kunne ikke parse API svar som JSON: {str(je)}")
            
    except Exception as e:
        logging.error(f"API fejl i sektion {section_number}: {str(e)}", exc_info=True)
        raise APIError(f"API fejl: {str(e)}")

def validate_event(event: Dict) -> bool:
    """
    Validerer en enkelt begivenhed.
    
    Returns:
        bool: True hvis begivenheden er gyldig, ellers False
    """
    logging.debug(f"Validerer begivenhed: {event}")
    
    if not isinstance(event, dict):
        logging.warning("Begivenhed er ikke et dictionary")
        return False
        
    # Tjek for påkrævet Time felt
    time = event.get("Time", "")
    if not time or not isinstance(time, str):
        logging.warning("Manglende eller ugyldig Time værdi")
        return False
        
    # Valider time format (mm.ss)
    if not re.match(r'^\d{1,2}\.\d{2}$', time):
        logging.warning(f"Ugyldigt tidsformat: {time}")
        return False
    
    # Valider at alle værdier er strings eller None
    for key, value in event.items():
        if value is not None and not isinstance(value, str):
            logging.warning(f"Ugyldig værdi type for {key}: {type(value)}")
            return False
    
    logging.debug("Begivenhed valideret succesfuldt")
    return True

def save_events_batch(cursor: sqlite3.Cursor, events: List[Dict], section_number: int):
    """Gem events i batches for bedre performance"""
    if not events:
        return
    
    try:
        cursor.executemany('''
            INSERT INTO game_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [(
            event.get('Time'),
            event.get('ScoreUpdate'),
            event.get('TeamInitials'),
            event.get('Action1'),
            event.get('Position'),
            event.get('PlayerNumber'),
            event.get('PlayerName'),
            event.get('Action2'),
            event.get('Player2Number'),
            event.get('Player2Name'),
            event.get('GoalkeeperNumber'),
            event.get('GoalkeeperName'),
            section_number
        ) for event in events])
    except Exception as e:
        logging.error(f"Database fejl ved batch insert: {str(e)}", exc_info=True)
        raise DatabaseError(f"Database fejl: {str(e)}")

def process_handball_file(filename: str):
    logging.info(f"Starter behandling af fil: {filename}")
    
    if not os.path.exists(filename):
        logging.error(f"Filen findes ikke: {filename}")
        raise FileNotFoundError(f"Filen findes ikke: {filename}")
    
    if not os.getenv("DEEPSEEK_API_KEY"):
        logging.error("DEEPSEEK_API_KEY mangler i .env filen")
        raise ValueError("DEEPSEEK_API_KEY er ikke sat i .env filen")
    
    try:
        logging.debug(f"Åbner fil: {filename}")
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
            logging.info(f"Læste {len(content)} tegn fra filen")
        
        logging.debug("Opretter database")
        conn, cursor = create_database(content)
        
        logging.debug("Udtrækker sektioner")
        sections = extract_sections(content)
        logging.info(f"Fandt {len(sections)} sektioner at behandle")
        
        total_events = 0
        
        with tqdm(total=len(sections), desc="Behandler sektioner") as pbar:
            for section_num, section in enumerate(sections, 1):
                logging.debug(f"Behandler sektion {section_num}/{len(sections)}")
                try:
                    events = process_section_with_deepseek(section, section_num)
                    if events:
                        logging.debug(f"Gemmer {len(events)} begivenheder fra sektion {section_num}")
                        save_events_batch(cursor, events, section_num)
                        total_events += len(events)
                        
                    conn.commit()
                    logging.debug(f"Sektion {section_num} behandlet succesfuldt")
                    pbar.update(1)
                    pbar.set_description(f"Sektion {section_num}/{len(sections)}")
                except (APIError, DatabaseError) as e:
                    logging.error(f"Fejl i sektion {section_num}: {str(e)}", exc_info=True)
                    continue
        
        conn.close()
        logging.info(f"Database forbindelse lukket")
        logging.info(f"Behandling afsluttet. I alt {total_events} begivenheder gemt i databasen!")
    except Exception as e:
        logging.error(f"Kritisk fejl under behandling af fil: {str(e)}", exc_info=True)
        raise

def process_pdf_files():
    """Håndterer PDF-filer fra Not_Processed mappen"""
    logging.info("Starter behandling af PDF-filer")
    
    not_processed_dir = "Not_Processed"
    processed_dir = "Processed"
    error_dir = "Error_Appeared"
    
    # Tjek om alle nødvendige mapper eksisterer
    for dir_name in [not_processed_dir, processed_dir, error_dir]:
        if not os.path.exists(dir_name):
            logging.info(f"Opretter manglende mappe: {dir_name}")
            os.makedirs(dir_name)
    
    # Tjek om der er PDF-filer at behandle
    pdf_files = [f for f in os.listdir(not_processed_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logging.info("Ingen PDF-filer at behandle i Not_Processed mappen")
        return
    
    logging.info(f"Fandt {len(pdf_files)} PDF-filer at behandle")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(not_processed_dir, pdf_file)
        txt_path = os.path.join(not_processed_dir, f"{os.path.splitext(pdf_file)[0]}.txt")
        
        logging.info(f"Starter behandling af PDF-fil: {pdf_file}")
        logging.debug(f"PDF sti: {pdf_path}")
        logging.debug(f"Midlertidig TXT sti: {txt_path}")
        
        try:
            # Konverter PDF til tekst
            logging.debug("Starter PDF til tekst konvertering")
            if not convert_pdf_to_text(pdf_path, txt_path):
                logging.error(f"PDF konvertering fejlede for {pdf_file}")
                raise Exception("Kunne ikke konvertere PDF til tekst")
            logging.info("PDF konverteret succesfuldt til tekst")
            
            # Behandl tekstfilen
            logging.debug("Starter behandling af tekstfil")
            process_handball_file(txt_path)
            
            # Flyt PDF-fil til Processed mappen ved succes
            logging.debug(f"Flytter {pdf_file} til {processed_dir}")
            shutil.move(pdf_path, os.path.join(processed_dir, pdf_file))
            logging.info(f"Succesfuldt behandlet og flyttet {pdf_file} til {processed_dir}")
            
        except Exception as e:
            logging.error(f"Fejl under behandling af {pdf_file}: {str(e)}", exc_info=True)
            # Flyt PDF-fil til Error mappen ved fejl
            try:
                logging.debug(f"Flytter {pdf_file} til {error_dir} pga. fejl")
                shutil.move(pdf_path, os.path.join(error_dir, pdf_file))
                logging.info(f"Flyttet {pdf_file} til {error_dir} pga. fejl")
            except Exception as move_error:
                logging.error(f"Kunne ikke flytte fejlet fil til {error_dir}: {str(move_error)}", exc_info=True)
        
        finally:
            # Slet den midlertidige tekstfil hvis den eksisterer
            if os.path.exists(txt_path):
                logging.debug(f"Sletter midlertidig tekstfil: {txt_path}")
                try:
                    os.remove(txt_path)
                    logging.debug("Midlertidig tekstfil slettet")
                except Exception as e:
                    logging.error(f"Kunne ikke slette midlertidig tekstfil: {str(e)}", exc_info=True)

if __name__ == "__main__":
    logging.info("Program starter")
    try:
        process_pdf_files()
        logging.info("Program afsluttet succesfuldt")
    except Exception as e:
        logging.error("Program afsluttet med fejl", exc_info=True) 