# Database Dokumentation for Håndboldstatistik

Dette dokument beskriver strukturen og indholdet af håndbolddatabaserne, herunder alle kolonner, værdier og deres betydning for statistisk analyse.

## Indholdsfortegnelse
1. [Hovedtabel: game_events](#hovedtabel-game_events)
2. [Supplerende Tabeller](#supplerende-tabeller)
3. [Datarelationer](#datarelationer)
4. [Statistiske Muligheder](#statistiske-muligheder)

## Hovedtabel: game_events

### Time (Tidspunkt)
- Format: "MM.SS" (minutter.sekunder)
- Beskriver tidspunktet i kampen
- Anvendes til:
  * Kronologisk ordning af hændelser
  * Beregning af perioder og intensitet
  * Identificering af kritiske kampperioder

### Score_update (Stillingsopdatering)
- Format: "X-Y" (hjemmehold-udehold)
- Viser den løbende stilling
- Anvendes til:
  * Følge scoringsudvikling
  * Analysere comebacks
  * Identificere afgørende perioder

### Team_initials (Holdinitialer)
- Identificerer det aktive hold i hændelsen
- Eksempler: "AAH", "BSH", "GOG", etc.
- Reference for:
  * Hvilke spillere der tilhører holdet
  * Om holdet er hjemme- eller udehold
  * Kobling til team_mapping

### Action_1 (Primær handling)
Mulige værdier:
- Kampflow:
  * Start 1:e halvleg
  * Start 2:e halvleg
  * Halvleg
  * Fuld tid
  * Kamp slut
  * Time out
  * Video Proof/Video Proof slut

- Scoring:
  * Mål
  * Mål på straffe
  * Skud reddet
  * Skud forbi
  * Skud på stolpe
  * Skud blokeret
  * Straffekast reddet
  * Straffekast forbi
  * Straffekast på stolpe

- Fejl/Straffe:
  * Advarsel
  * Udvisning
  * Rødt kort, direkte
  * Regelfejl
  * Tilkendt straffe
  * Fejlaflevering
  * Tabt bold
  * Passivt spil

### Position (Spilleposition)
Angiver hvor på banen handlingen udføres:
- Gbr (Gennembrud)
- HB (Højre Back)
- HF (Højre Fløj)
- PL (Playmaker)
- ST (Streg)
- VB (Venstre Back)
- VF (Venstre Fløj)
- 1:e (Første Bølge)
- 2:e (Anden Bølge)

### Player_number (Spillernummer)
- Nummeret på spilleren der udfører Action_1
- Bruges til identifikation af spillere

### Player_Name (Spillernavn)
- Navnet på spilleren der udfører Action_1
- Tilhører Team_initials holdet

### Action_2 (Sekundær handling)
Supplerende handlinger:
- Assist (medspiller fra samme hold)
- Blok af (ret) (modstanderhold)
- Blokeret af (modstanderhold)
- Bold erobret (modstanderhold)
- Forårs. str. (modstanderhold)
- Retur (kan være begge hold)

### Player2_Number (Sekundær spillernummer)
- Nummeret på spilleren involveret i Action_2
- Holdtilhørsforhold afhænger af Action_2 typen

### Player2_Name (Sekundær spillernavn)
- Navnet på spilleren involveret i Action_2
- Holdtilhørsforhold bestemmes af Action_2:
  * Ved 'Assist': Samme hold som Team_initials
  * Ved defensive aktioner: Modstanderholdet

### Goalkeeper_Number (Målmandsnummer)
- Nummeret på målmanden involveret i hændelsen
- Tilhører typisk modstanderholdet ved skud/scoringer

### Goalkeeper_Name (Målmandsnavn)
- Navnet på målmanden involveret i hændelsen
- Tilhører modstanderholdet ved skud/scoringer

## Supplerende Tabeller

### match_data
Indeholder kampspecifik information:
- home_team_initial/away_team_initial: Holdidentifikation
- home_score/away_score: Slutresultat
- home_team_players/away_team_players: Antal spillere
- home_team_goalkeepers/away_team_goalkeepers: Antal målmænd

### players
Registrerer spillerinformation:
- team_initial: Holdtilhørsforhold
- player_name: Spillernavn
- player_type: 'Field player' eller 'Goalkeeper'

### team_info
Grundlæggende kampinformation:
- home_team_name/away_team_name: Holdnavne
- home_team_initial/away_team_initial: Holdinitialer
- match_date: Kampdato

## Datarelationer

Alle tabeller er forbundet gennem team_initials og kan kobles for at skabe komplette kampanalyser. Dette muliggør både overordnede kampstatistikker og detaljerede spilleranalyser.

## Statistiske Muligheder

Databasestrukturen tillader analyse af:
1. Kampstatistik
   - Scoringseffektivitet
   - Målmandsredninger
   - Udvisningsminutter
   - Angrebseffektivitet

2. Spillerstatistik
   - Scoringer pr. position
   - Assist-statistik
   - Defensive aktioner
   - Spilletid og involvering

3. Taktisk analyse
   - Scoringsmønstre
   - Defensive formationer
   - Udnyttelse af overtal
   - Temposkift i kampen