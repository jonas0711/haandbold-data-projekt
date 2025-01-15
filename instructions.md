# Håndbold Statistik Projekt Instruktioner

## 1. Projekt Oversigt

### Projekt Navn
Håndbold Statistik - Automatiseret Kampanalyse Platform

### Projekt Formål
Udvikle et Python-baseret system til automatisk indsamling, processering og analyse af håndboldkampe gennem:
- PDF-parsing
- Automatisk dataekstraktion
- Statistisk analyse
- Web-baseret visualisering

### Kernemål
- Automatisere indsamling af kampdata
- Standardisere og rense håndboldkampdata
- Skabe detaljerede kampstatistikker
- Levere brugervenlig web-interface til datavisning

## 2. Teknologisk Stack
```markdown
## Teknologi Oversigt
- Primært Sprog: Python 3.8+
- Backend Processering:
  - PDF Parsing: PyPDF2
  - Data Processering: Pandas, Papaparse
- Database: SQLite
- Web Interface: Flask
- AI Integration: DeepSeek API
- Web Scraping: Requests, BeautifulSoup
- Datavalidering: Lodash (via Python biblioteker)
- Deployment: Manuel installation
```

## 3. Detaljerede Funktionelle Krav

### PDF Processering
- Understøtte PDF-filer fra forskellige håndboldkampe
- Ekstrahere struktureret data fra kamprapporter
- Håndtere varierende PDF-formater
- Robust fejlhåndtering ved uventede dokumentstrukturer

### Data Standardisering
- Normalisere holdnavne
- Standardisere kampbegivenheder
- Validere datakvalitet
- Oprette konsistent database-struktur

### Web Interface
- Vise kampstatistikker
- Præsentere detaljeret kampforløb
- Understøtte sortering og filtrering
- Responsivt design

## 4. Datamodeller og Skemaer

### Game Events Tabel
```python
class GameEvent:
    Time: str  # Tidspunkt i kampen
    Score_update: str  # Løbende stillingsopdatering
    Team_initials: str  # Hold initialer
    Action_1: str  # Primær handling
    Position: str  # Spillerposition
    Player_number: str  # Spillernummer
    Player_Name: str  # Spillernavn
    Action_2: str  # Sekundær handling
    Player2_Number: str  # Nummer på anden spiller
    Player2_Name: str  # Navn på anden spiller
    Goalkeeper_Number: str  # Målmandsnummer
    Goalkeeper_Name: str  # Målmandsnavn
```

### Team Info Tabel
```python
class TeamInfo:
    home_team_name: str
    home_team_initial: str
    away_team_name: str
    away_team_initial: str
    match_date: str
```

## 5. API og Endpoint Definitioner

### Interne Processerings-Endpoints
- `process_output.py`: Hovedprocesseringsmodul
  - Input: PDF-filer
  - Output: Udfyldt SQLite database

- `scrape_matches.py`: Web scraping modul
  - Input: Håndbold kampprogram
  - Output: Downloadede PDF'er

- `standardize_actions.py`: Data standardiseringsmodul
  - Input: Rå kampdata
  - Output: Standardiseret data

## 6. Design og UI Retningslinjer

### Farvepalette
- Primær: #4267B2 (Blå)
- Sekundær: #34C759 (Grøn)
- Accent: #FF3B30 (Rød)

### Typografi
- Overskrifter: Open Sans, Bold
- Brødtekst: Open Sans, Regular
- Mobil skriftstørrelse: 14px
- Desktop skriftstørrelse: 16px

### Responsivt Design
- Mobile-first tilgang
- Bootstrap grid system
- Fleksibel layout

## 7. Ydelses- og Optimeringskrav

### Ydelsesstandarder
- Indlæsningstid for kampstatistik: < 2 sekunder
- PDF processeringstid: < 5 sekunder pr. fil
- Effektiv hukommelseshåndtering
- Batch-processering af PDF-filer

### Optimeringsstrategier
- Brug af generatorer ved store datasæt
- Indexering af SQLite databaser
- Minimering af I/O-operationer
- Caching af hyppigt forespurgte data

## 8. Fejlhåndtering og Logging

### Logningsstrategi
- Detaljeret logging i `/logs`
- Roterende logfiler
- Log vigtige processeringstrin
- Registrer advarsler og fejl

### Fejlresponse Format
```python
class ErrorResponse:
    message: str  # Brugervenlig fejlbesked
    error_code: str  # Teknisk fejlkode
    timestamp: datetime
    file_source: str  # Kildefil for fejl
```

## 9. Deployment og Miljøkonfiguration

### Deploymentopsætning
- Manuel installation via pip
- Understøtter Python 3.8+
- Kræver specifikke miljøvariabler
  - DEEPSEEK_API_KEY
  - DEBUG_MODE
  - LOG_LEVEL

### Påkrævede Miljøvariabler
- `DEEPSEEK_API_KEY`: API nøgle til DeepSeek
- `DEBUG`: Aktivér/deaktivér debug tilstand
- `LOG_LEVEL`: Sæt logningsniveau (INFO, DEBUG, ERROR)

## 10. Fremtidig Roadmap

### Planlagte Forbedringer
- Udvidelse af AI-baseret dataanalyse
- Forbedret web visualisering
- Understøttelse af flere datakilder
- Machine learning til prædiktiv analyse
- Udvidet hold- og spillerstatistik

## 11. Bidrag og Vedligeholdelse

### Kodningsstandarder
- Følg PEP 8 retningslinjer
- Anvend type hints
- Omfattende dokumentation
- Skriv unit tests
- Konsistent fejlhåndtering

### Kodningsworkflow
- Opret feature branches
- Gennemfør code reviews
- Kør tests før merge
- Opdatér dokumentation løbende

Vi har oprettet et alias kaldet autocommit. Du kan nu bruge følgende kommando hver gang du vil committe og pushe ændringer automatisk:
Dette vil:
Tilføje alle ændrede filer (git add -A)
Committe med beskeden "Automatisk commit af ændringer"
Pushe ændringerne til GitHub

## Konklusion
Dette dokument tjener som central reference for projektets arkitektur, design og implementeringsretningslinjer. Det sikrer konsistens, kvalitet og retning for Håndbold Statistik projektet.