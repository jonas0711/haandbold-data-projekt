import sqlite3
import os
import glob
from update_match_data import get_final_score, get_team_initials, get_team_players

def get_team_name(cursor, team_initial):
    cursor.execute('SELECT official_name FROM team_mapping WHERE team_initial = ?', (team_initial,))
    result = cursor.fetchone()
    return result[0] if result else team_initial

def clean_database(db_path):
    print(f"Renser database: {db_path}")
    
    # Opret forbindelse til team_mapping databasen
    mapping_conn = sqlite3.connect('Databases/team_mapping.db')
    mapping_cursor = mapping_conn.cursor()
    
    # Opret forbindelse til den aktuelle database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Slet eksisterende data
        cursor.execute('DROP TABLE IF EXISTS match_data')
        cursor.execute('DROP TABLE IF EXISTS team_info')
        
        # Genopret tabeller
        cursor.execute('''
            CREATE TABLE match_data (
                home_team_initial TEXT,
                away_team_initial TEXT,
                home_score INTEGER,
                away_score INTEGER,
                home_team_players INTEGER,
                away_team_players INTEGER,
                home_team_goalkeepers INTEGER,
                away_team_goalkeepers INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE team_info (
                home_team_name TEXT,
                home_team_initial TEXT,
                away_team_name TEXT,
                away_team_initial TEXT,
                match_date TEXT,
                last_updated TEXT
            )
        ''')
        
        # Brug update_match_data.py funktioner til at beregne data
        home_score, away_score = get_final_score(cursor)
        home_team, away_team = get_team_initials(cursor)
        
        if not home_team or not away_team:
            print(f"Kunne ikke finde team initials i {db_path}")
            return
            
        # Hent spillere for hvert hold
        home_field_players, home_goalkeepers = get_team_players(cursor, home_team)
        away_field_players, away_goalkeepers = get_team_players(cursor, away_team)
        
        # Indsæt beregnet data i match_data
        cursor.execute('''
            INSERT INTO match_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            home_team,
            away_team,
            home_score,
            away_score,
            len(home_field_players),
            len(away_field_players),
            len(home_goalkeepers),
            len(away_goalkeepers)
        ))
        
        # Opret team_info med navne fra team_mapping
        match_date = os.path.basename(db_path).split('_')[0]  # Hent dato fra filnavn
        
        # Hent officielle navne fra team_mapping
        home_name = get_team_name(mapping_cursor, home_team)
        away_name = get_team_name(mapping_cursor, away_team)
        
        cursor.execute('''
            INSERT INTO team_info (
                home_team_name, home_team_initial,
                away_team_name, away_team_initial,
                match_date, last_updated
            ) VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', (home_name, home_team, away_name, away_team, match_date))
        
        conn.commit()
        print(f"Database renset succesfuldt: {db_path}")
        
    except Exception as e:
        print(f"Fejl ved rensning af {db_path}: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
        mapping_conn.close()

def main():
    # Find alle .db filer i Databases mappen undtagen team_mapping.db
    db_files = glob.glob('Databases/*.db')
    db_files = [f for f in db_files if 'team_mapping.db' not in f]
    
    for db_file in db_files:
        clean_database(db_file)

if __name__ == '__main__':
    main() 