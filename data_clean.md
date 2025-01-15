# Datarensning og Standardisering for Håndbold Database

Dette dokument beskriver reglerne og procedurerne for standardisering af data i håndbold databasen. Det er vigtigt at følge disse regler for at sikre konsistent data på tværs af alle kampe.

## Indholdsfortegnelse
1. [Position Standardisering](#position-standardisering)
2. [Action_1 Standardisering](#action_1-standardisering)
3. [Action_2 Standardisering](#action_2-standardisering)
4. [Håndtering af Specielle Tilfælde](#håndtering-af-specielle-tilfælde)
5. [Proces for Nye Databaser](#proces-for-nye-databaser)

## Position Standardisering

### Gyldige Positioner
Kun følgende positionsværdier er tilladt:
- `Gbr` (Gennembrud)
- `HB` (Højre Back)
- `HF` (Højre Fløj)
- `PL` (Playmaker)
- `ST` (Streg)
- `VB` (Venstre Back)
- `VF` (Venstre Fløj)
- `1:e` (Første Bølge)
- `2:e` (Anden Bølge)

### Regler for Position
1. Hvis en position er indlejret i Action_1 (f.eks. "Mål HB"), skal positionen flyttes til Position-kolonnen
2. Numeriske værdier i Position-kolonnen skal flyttes til Player_number
3. Position må kun indeholde en af de gyldige positionsværdier
4. Vær opmærksom på at "Start 1:e halvleg" og "Start 2:e halvleg" ikke er positioner

## Action_1 Standardisering

### Gyldige Action_1 Værdier
Følgende handlinger er de eneste tilladte værdier i Action_1:
```
- Advarsel
- Fejlaflevering
- Fuld tid
- Halvleg
- Kamp slut
- Mål
- Mål på straffe
- Passivt spil
- Regelfejl
- Rødt kort, direkte
- Skud blokeret
- Skud forbi
- Skud på stolpe
- Skud reddet
- Start 1:e halvleg
- Start 2:e halvleg
- Straffekast forbi
- Straffekast på stolpe
- Straffekast reddet
- Tabt bold
- Tilkendt straffe
- Time out
- Udvisning
- Video Proof
- Video Proof slut
```

### Regler for Action_1
1. Hvis en handling indeholder en position (f.eks. "Mål HB"), skal den opdeles:
   - Handlingen ("Mål") gemmes i Action_1
   - Positionen ("HB") gemmes i Position-kolonnen
2. Start-handlinger skal standardiseres til enten "Start 1:e halvleg" eller "Start 2:e halvleg"
3. Handlinger må ikke indeholde spillernumre eller andre numeriske værdier

## Action_2 Standardisering

### Gyldige Action_2 Værdier
Kun følgende sekundære handlinger er tilladt:
```
- Assist
- Blok af (ret)
- Blokeret af
- Bold erobret
- Forårs. str.
- Retur
```

### Regler for Action_2
1. Numeriske værdier skal flyttes til Player2_number
2. UPPERCASE navne (efternavne) skal tilføjes til eksisterende Player_Name
3. "1:e halvleg" skal flyttes til Action_1 som "Start 1:e halvleg"
4. Alle andre værdier end de listede gyldige handlinger skal fjernes eller flyttes

## Håndtering af Specielle Tilfælde

### Efternavne i CAPS
- Hvis Action_2 indeholder et navn i CAPS (f.eks. "STANKIEWICZ"), skal det:
  1. Tilføjes til det eksisterende Player_Name
  2. Fjernes fra Action_2

### Numeriske Værdier
- Numeriske værdier skal flyttes til de korrekte kolonner:
  * Fra Position -> Player_number
  * Fra Action_2 -> Player2_number

### Periodemarkører
- "1:e halvleg" og "2:e halvleg" i Action_2 skal konverteres til korrekt Start-handling i Action_1

## Proces for Nye Databaser

### Trin for Datarensning
1. Kør standardize_actions.py på den nye database
2. Verificer ændringer ved at køre analyze_actions.py
3. Tjek at alle kolonner kun indeholder tilladte værdier

### Validering
Efter standardisering bør du verificere at:
1. Position kun indeholder gyldige positionsværdier
2. Action_1 kun indeholder gyldige handlinger
3. Action_2 kun indeholder gyldige sekundære handlinger
4. Spillernumre er i de korrekte kolonner
5. Efternavne er korrekt tilføjet til Player_Name

### Fejlfinding
Hvis der opstår uventede værdier:
1. Tjek logfilen for detaljer om ændringer
2. Verificer at alle regler er blevet anvendt korrekt
3. Opdater standardiseringsreglerne hvis nødvendigt

## Eksempel på Brug
```bash
# Standardiser ny database
python standardize_actions.py

# Verificer resultater
python analyze_actions.py
```

