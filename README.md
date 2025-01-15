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
- Automatisk standardisering af holdnavne og aktioner
- Avanceret holdanalyse og statistik
- Web scraping af kampdata
- CSV eksport funktionalitet
- Team mapping system

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

2. Installér hovedafhængigheder:
```bash
pip install -r requirements.txt
```

3. Installér scraper afhængigheder (valgfrit):
```bash
pip install -r scraper_requirements.txt
```

4. Installér website afhængigheder:
```bash
cd website
pip install -r requirements.txt
cd ..
```

5. Opret nødvendige mapper:
```bash
mkdir Not_Processed Processed Error_Appeared Databases logs CSV Downloads
```

6. Konfigurér miljøvariabler i .env fil:
```bash
DEEPSEEK_API_KEY=din_api_nøgle_her
```

## Brug

### PDF Processering
1. Placér PDF-filer i `Not_Processed` mappen
2. Kør processeringen:
```bash
python process_output.py
```

### Web Scraping
1. Hent nye kampe:
```bash
python scrape_matches.py
```

### Data Standardisering
1. Standardiser holdnavne:
```bash
python create_team_mapping.py
python add_team_info.py
```

2. Standardiser aktioner:
```bash
python standardize_actions.py
```

### Analyse
1. Analysér aktioner:
```bash
python analyze_actions.py
```

2. Analysér hold:
```bash
python analyze_teams.py
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
├── Not_Processed/     # PDF filer der venter på processering
├── Processed/         # Færdigbehandlede PDF filer
├── Error_Appeared/    # PDF filer med fejl under processering
├── Databases/         # SQLite databaser med kampdata
├── CSV/              # Eksporterede CSV filer
├── Downloads/        # Downloaded filer fra web scraping
├── logs/             # Log filer
├── website/          # Web interface
│   ├── templates/    # HTML templates
│   ├── static/       # CSS, JS, og andre statiske filer
│   └── app.py       # Flask application
├── pdf.py           # PDF processering
├── process_output.py # Hovedprocessering
├── scrape_matches.py # Web scraping funktionalitet
├── create_team_mapping.py # Opret hold mapping
├── add_team_info.py  # Tilføj holdinfo til database
├── standardize_actions.py # Standardiser aktioner
├── analyze_actions.py # Analysér aktioner
├── analyze_teams.py  # Analysér hold
├── update_match_data.py # Opdater kampdata
├── team_mapping.json # Hold mapping konfiguration
├── requirements.txt  # Hoved Python afhængigheder
└── scraper_requirements.txt # Scraper afhængigheder
```

## System Komponenter

### Hovedkomponenter

#### 1. PDF Processor (`pdf.py`)
- **Formål**: Konverterer PDF-filer til tekstformat
- **Hovedfunktioner**:
  - PDF til tekst konvertering
  - Fejlhåndtering
  - Kodningshåndtering

#### 2. Processeringsmotor (`process_output.py`)
- **Formål**: Hovedmotor for databehandling
- **Hovedfunktioner**:
  - PDF processering
  - AI-baseret tekstanalyse
  - Database oprettelse og opdatering
  - Filhåndtering

#### 3. Web Scraper (`scrape_matches.py`)
- **Formål**: Automatisk indhentning af kampdata
- **Hovedfunktioner**:
  - Download af kampdata
  - Filtrering af relevante kampe
  - Automatisk download håndtering

#### 4. Team Mapping System
- **Komponenter**:
  - `create_team_mapping.py`: Opretter hold mapping
  - `add_team_info.py`: Tilføjer holdinfo til database
  - `team_mapping.json`: Konfigurationsfil

#### 5. Analyse Moduler
- **Aktionsanalyse** (`analyze_actions.py`):
  - Statistik over aktioner
  - Trendanalyse
  - Performance metrics
- **Holdanalyse** (`analyze_teams.py`):
  - Holdstatistikker
  - Performance sammenligning
  - Historisk analyse

#### 6. Web Interface (`website/app.py`)
- **Formål**: Flask-baseret webapplikation
- **Hovedfunktioner**:
  - Kampvisning og statistik
  - Holdoversigt
  - Detaljeret kampanalyse
  - Interaktive grafer og visualiseringer
