# Håndbold Statistik

Et Python-baseret system til at processere og analysere håndboldhændelser fra PDF-filer og gemme dem i SQLite-databaser med en webbaseret brugergrænseflade til visning af statistikker.

## Indholdsfortegnelse
- [Funktioner](#funktioner)
- [Installation](#installation)
- [Brug](#brug)
- [Projektstruktur](#projektstruktur)
- [System Komponenter](#system-komponenter)
- [Konfiguration](#konfiguration)
- [Udvikling](#udvikling)
- [Tests](#tests)
- [Fejlfinding](#fejlfinding)

## Funktioner

- PDF processering og tekstudtrækning
- Automatisk hændelsesanalyse med AI
- SQLite database lagring
- Webbaseret statistik visning
- Detaljeret kampanalyse
- Automatisk datakvalitetsvalidering
- Omfattende fejlhåndtering og logging

## Installation

### Forudsætninger
- Python 3.8 eller nyere
- DeepSeek API nøgle
- Pip (Python package manager)

### Trin-for-trin Installation
1. Klon projektet:
```bash
git clone [repository-url]
cd Data-Handball
```

2. Installér afhængigheder:
```bash
pip install -r requirements.txt
```

3. Opret nødvendige mapper:
```bash
mkdir Not_Processed Processed Error_Appeared Databases logs
```

4. Konfigurér API nøgle:
```bash
export DEEPSEEK_API_KEY=din_api_nøgle_her
```

## Brug

### PDF Processering
1. Placér PDF-filer i `Not_Processed` mappen
2. Kør processeringen:
```bash
python process_output.py
```

### Web Interface
1. Start webserveren:
```bash
cd website
python app.py
```
2. Åbn `http://localhost:5000` i en browser

## Projektstruktur

```
Data-Handball/
├── Not_Processed/    # PDF filer der venter på processering
├── Processed/        # Færdigbehandlede PDF filer
├── Error_Appeared/   # PDF filer med fejl under processering
├── Databases/        # SQLite databaser med kampdata
├── logs/            # Log filer
├── website/         # Web interface
│   ├── templates/   # HTML templates
│   ├── static/      # CSS, JS, og andre statiske filer
│   └── app.py      # Flask application
├── pdf.py          # PDF processering
├── process_output.py # Hovedprocessering
└── requirements.txt # Python afhængigheder
```

## System Komponenter

### Hovedkomponenter

#### 1. PDF Processor (`pdf.py`)
- **Formål**: Konverterer PDF-filer til tekstformat
- **Hovedfunktioner**:
  - `convert_pdf_to_text(pdf_path, output_path)`: Konverterer PDF til tekst
  - Håndterer forskellige PDF-formater og kodninger
  - Fejlhåndtering for korrupte eller ugyldige PDF'er
- **Afhængigheder**: PyPDF2, logging

#### 2. Processeringsmotor (`process_output.py`)
- **Formål**: Hovedmotor for databehandling
- **Hovedfunktioner**:
  - `process_pdf_files()`: Styrer hele processeringsflowet
  - `process_handball_file(text_content)`: Analyserer kampdata
  - `create_database(content)`: Opretter og populerer SQLite database
- **Nøglefunktionalitet**:
  - Overvåger `Not_Processed` mappen
  - Kalder AI-modellen for tekstanalyse
  - Håndterer filflytning mellem mapper
  - Opretter og vedligeholder databaser

#### 3. Web Interface (`website/app.py`)
- **Formål**: Flask-baseret webapplikation
- **Hovedfunktioner**:
  - `get_all_matches()`: Henter alle kampe fra databasen
  - `match_details(database)`: Viser detaljeret kampinformation
- **Hjælpefunktioner**:
  - `format_team_name(name)`: Formaterer holdnavne konsistent
  - `format_date(date_str)`: Standardiserer datoformater
  - `get_validated_score(match)`: Validerer og returnerer kampscores
  - `get_match_statistics(match)`: Beregner kampstatistikker

### Templates og Frontend

#### 1. Hovedside (`templates/index.html`)
- Viser oversigt over alle kampe
- Implementerer filtrerbar liste
- Responsivt design med Bootstrap
- Dynamisk sortering af kampe

#### 2. Kampdetaljer (`templates/match.html`)
- Detaljeret kampvisning
- Tidslinje over hændelser
- Statistik visualiseringer
- Interaktive elementer

### Dataflow

1. **PDF til Tekst**:
   ```
   PDF File -> pdf.py -> Text File
   ```

2. **Tekstanalyse**:
   ```
   Text File -> process_output.py -> AI Analysis -> Structured Data
   ```

3. **Database Håndtering**:
   ```
   Structured Data -> SQLite Database -> Web Interface
   ```

### Database Struktur

#### game_events Tabel
```sql
CREATE TABLE game_events (
    id INTEGER PRIMARY KEY,
    Time TEXT,          -- Tidspunkt i kampen (MM:SS)
    Team_initials TEXT, -- Holdets initialer
    Action_1 TEXT,      -- Primær handling (Mål, Skud, etc.)
    Player_Name TEXT,   -- Navn på primær spiller
    Action_2 TEXT,      -- Sekundær handling
    Player2_Name TEXT,  -- Navn på sekundær spiller
    score_update TEXT   -- Løbende stilling
);
```

### Datakvalitet og Validering

#### 1. Input Validering
- PDF filformat og indhold
- Tekstkvalitet og formatering
- AI-analysens pålidelighedsgrad

#### 2. Datavalidering
- Score validering og konsistens
- Spillernavne normalisering
- Tidspunkt formatering og rækkefølge

#### 3. Output Validering
- Database integritet
- Statistik beregninger
- Web interface præsentation

### Systemintegration

#### 1. AI Integration
- DeepSeek API kommunikation
- Prompt engineering og formatering
- Fejlhåndtering og retries

#### 2. Database Integration
- SQLite connection pooling
- Transaktion håndtering
- Concurrent access håndtering

#### 3. Web Integration
- Flask routing og templating
- Asset management
- Cache håndtering

## Konfiguration

### Database Struktur
```

### Logging Konfiguration
- **Placering**: `logs/` mappe
- **Logniveauer**:
  - INFO: Standard operationer
  - WARNING: Potentielle problemer
  - ERROR: Kritiske fejl
  - DEBUG: Detaljeret debugging
- **Logrotation**:
  - Maksimal filstørrelse: 10MB
  - Backup count: 5
  - Tidsstempel format: ISO 8601

### Miljøvariabler
```bash
DEEPSEEK_API_KEY=din_api_nøgle    # Påkrævet for AI-analyse
DEBUG=True/False                   # Aktiverer debug mode
LOG_LEVEL=INFO                     # Sætter logniveau
DATABASE_PATH=path/to/db           # Database placering
```

## Udvikling

### Kodestruktur
- **Modulær Design**:
  - Separate moduler for hver hovedfunktion
  - Løs kobling mellem komponenter
  - Dependency injection hvor muligt

- **Kodestandard**:
  - PEP 8 formatering
  - Type hints på alle funktioner
  - Docstrings i Google format
  - Omfattende kommentering

- **Fejlhåndtering**:
  - Try-except blokke
  - Graceful degradation
  - Detaljeret fejllogging
  - Brugervenlige fejlbeskeder

### Tilføj Nye Features
1. **Planlægning**:
   - Definer feature scope
   - Identificer påvirkede moduler
   - Planlæg tests

2. **Implementering**:
   - Følg kodestandard
   - Skriv tests først (TDD)
   - Dokumenter ændringer
   - Håndter edge cases

3. **Test og Review**:
   - Kør alle tests
   - Peer review
   - Performance test
   - Sikkerhedscheck

4. **Deployment**:
   - Opdater dokumentation
   - Merge til main branch
   - Deploy ændringer
   - Monitorer for fejl

## Tests

### Test Struktur
```
tests/
├── unit/                 # Unit tests
│   ├── test_pdf.py      # PDF processor tests
│   ├── test_process.py  # Processing tests
│   └── test_web.py      # Web interface tests
├── integration/          # Integration tests
│   ├── test_flow.py     # End-to-end flow
│   └── test_api.py      # API integration
└── fixtures/            # Test data
    ├── sample.pdf       # Test PDF
    └── expected.json    # Expected output
```

### Test Kommandoer
```bash
# Kør alle tests
python -m pytest

# Kør specifikke tests
python -m pytest tests/unit/
python -m pytest tests/integration/

# Kør med coverage
python -m pytest --cov=.

# Generer coverage rapport
python -m pytest --cov=. --cov-report=html
```

## Fejlfinding

### Almindelige Problemer

#### 1. PDF Processering
- **Problem**: PDF kan ikke læses
  ```python
  # Check PDF læsbarhed
  from PyPDF2 import PdfReader
  try:
      reader = PdfReader("file.pdf")
      text = reader.pages[0].extract_text()
  except Exception as e:
      print(f"PDF Error: {str(e)}")
  ```

#### 2. Database
- **Problem**: Database låst
  ```python
  # Proper connection handling
  import sqlite3
  from contextlib import contextmanager

  @contextmanager
  def get_db_connection():
      conn = sqlite3.connect('database.db')
      try:
          yield conn
      finally:
          conn.close()
  ```

#### 3. Web Interface
- **Problem**: Template fejl
  ```python
  # Debug template context
  @app.route('/')
  def index():
      context = {'matches': get_all_matches()}
      app.logger.debug(f"Template context: {context}")
      return render_template('index.html', **context)
  ```

### Performance Optimering

#### 1. Database Queries
```python
# Brug indeks for ofte søgte felter
CREATE INDEX idx_time ON game_events(Time);
CREATE INDEX idx_team ON game_events(Team_initials);
```

#### 2. Caching
```python
# Implementer caching for hyppige queries
from functools import lru_cache

@lru_cache(maxsize=128)
def get_match_statistics(match_id):
    # ... beregn statistik
    return stats
```

#### 3. Batch Processing
```python
# Batch inserts for bedre performance
def batch_insert_events(events, batch_size=100):
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        cursor.executemany(
            "INSERT INTO game_events VALUES (?,?,?,?,?,?,?)",
            batch
        )
```

### Sikkerhed

#### 1. Input Validering
```python
# Valider user input
def validate_input(data):
    if not isinstance(data, dict):
        raise ValueError("Invalid input format")
    required = ['date', 'team', 'score']
    if not all(k in data for k in required):
        raise ValueError("Missing required fields")
```

#### 2. SQL Injection Prevention
```python
# Brug parameteriserede queries
def get_match(match_id):
    cursor.execute(
        "SELECT * FROM game_events WHERE id = ?",
        (match_id,)
    )
```

#### 3. API Sikkerhed
```python
# Verificer API nøgle
def verify_api_key():
    api_key = request.headers.get('X-API-Key')
    if not api_key or not is_valid_key(api_key):
        abort(401)
```

## Support

### Kontakt
- GitHub Issues
- Email support
- Discord kanal

### Ressourcer
- API Dokumentation
- Tutorial videoer
- FAQ sektion

### Community
- Bidragsguide
- Code of Conduct
- License information
