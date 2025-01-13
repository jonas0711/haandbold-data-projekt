# Håndbold Kamp Parser

Et Python-program til at behandle og analysere håndboldkampe fra PDF-filer og gemme dem i SQLite-databaser.

## Beskrivelse

Dette program automatiserer processen med at:
1. Læse håndboldkamp-PDF'er
2. Konvertere dem til tekst
3. Analysere kampbegivenheder
4. Gemme struktureret data i SQLite-databaser

## Mappestruktur

Programmet bruger følgende mappestruktur:
- `Not_Processed/`: PDF-filer der venter på at blive behandlet
- `Processed/`: Succesfuldt behandlede PDF-filer
- `Error_Appeared/`: PDF-filer der fejlede under behandling
- `Databases/`: De genererede SQLite-databaser
- `logs/`: Logfiler med information om programkørsler

## Forudsætninger

- Python 3.8 eller nyere
- DeepSeek API-nøgle

## Installation

1. Klon projektet
2. Installer de nødvendige pakker:
```bash
pip install PyPDF2 python-dotenv openai tqdm tenacity
```

3. Opret en `.env` fil i rodmappen med din DeepSeek API-nøgle:
```
DEEPSEEK_API_KEY=din_api_nøgle_her
```

## Brug

1. Placer dine håndboldkamp-PDF'er i `Not_Processed` mappen

2. Kør programmet:
```bash
python process_output.py
```

3. Programmet vil:
   - Behandle alle PDF'er i `Not_Processed` mappen
   - Flytte succesfuldt behandlede filer til `Processed` mappen
   - Flytte fejlede filer til `Error_Appeared` mappen
   - Gemme databaser i `Databases` mappen
   - Generere logfiler i `logs` mappen

## Database Struktur

Hver kamp gemmes i sin egen SQLite-database med følgende struktur:

```sql
CREATE TABLE game_events (
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
```

## Fejlfinding

1. Tjek logfilerne i `logs` mappen for detaljerede fejlbeskeder
2. Sikr at DeepSeek API-nøglen er korrekt sat i `.env` filen
3. Verificer at PDF'erne er i det korrekte format

## Logning

Programmet logger alle handlinger til både konsol og logfiler:
- Logfiler roteres ved 10MB
- Der gemmes op til 5 backup-filer
- Logfiler navngives med tidsstempel

## Fejlhåndtering

- PDF'er der ikke kan behandles flyttes til `Error_Appeared` mappen
- Alle fejl logges med fuld stack trace
- Midlertidige filer ryddes op automatisk 