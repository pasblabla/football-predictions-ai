#!/usr/bin/env python3
"""
Script pour récupérer les détails des matchs (arbitres, joueurs absents)
"""
import sqlite3
import requests
from datetime import datetime

API_KEY = '647c75a7ce7f482598c8240664bd856c'
DB_PATH = '/home/ubuntu/football-api-deploy/server/database/app.db'

def fetch_referee_data(match_external_id):
    """Récupère les données de l'arbitre depuis l'API"""
    try:
        url = f'https://api.football-data.org/v4/matches/{match_external_id}'
        headers = {'X-Auth-Token': API_KEY}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            referees = data.get('referees', [])
            
            # Trouver l'arbitre principal
            main_referee = next((r for r in referees if r.get('type') == 'REFEREE'), None)
            
            if main_referee:
                return {
                    'name': main_referee.get('name'),
                    'nationality': main_referee.get('nationality'),
                    'id': main_referee.get('id')
                }
        
        return None
        
    except Exception as e:
        print(f"Erreur récupération arbitre: {str(e)}")
        return None


def update_match_referee(match_id, referee_data):
    """Met à jour les données de l'arbitre dans la base"""
    if not referee_data:
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Vérifier si la table referee existe, sinon la créer
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referee (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                nationality TEXT,
                total_matches INTEGER DEFAULT 0,
                avg_yellow_cards REAL DEFAULT 0,
                avg_red_cards REAL DEFAULT 0,
                avg_penalties REAL DEFAULT 0
            )
        """)
        
        # Insérer ou mettre à jour l'arbitre
        cursor.execute("""
            INSERT OR IGNORE INTO referee (external_id, name, nationality)
            VALUES (?, ?, ?)
        """, (referee_data['id'], referee_data['name'], referee_data['nationality']))
        
        # Créer la table de liaison match-arbitre si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_referee (
                match_id INTEGER,
                referee_id INTEGER,
                FOREIGN KEY (match_id) REFERENCES match(id),
                FOREIGN KEY (referee_id) REFERENCES referee(id),
                PRIMARY KEY (match_id, referee_id)
            )
        """)
        
        # Récupérer l'ID de l'arbitre
        cursor.execute("SELECT id FROM referee WHERE external_id = ?", (referee_data['id'],))
        referee_id = cursor.fetchone()[0]
        
        # Lier le match à l'arbitre
        cursor.execute("""
            INSERT OR IGNORE INTO match_referee (match_id, referee_id)
            VALUES (?, ?)
        """, (match_id, referee_id))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Erreur mise à jour arbitre: {str(e)}")
        return False


def fetch_and_update_referees():
    """Récupère et met à jour les arbitres pour tous les matchs à venir"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Récupérer les matchs à venir qui ont un external_id
    cursor.execute("""
        SELECT id, external_id 
        FROM match 
        WHERE status IN ('SCHEDULED', 'TIMED') 
        AND external_id IS NOT NULL
        AND date > datetime('now')
        LIMIT 50
    """)
    
    matches = cursor.fetchall()
    conn.close()
    
    updated = 0
    
    for match_id, external_id in matches:
        print(f"Traitement match {match_id} (external_id: {external_id})...")
        
        referee_data = fetch_referee_data(external_id)
        
        if referee_data:
            if update_match_referee(match_id, referee_data):
                print(f"  ✓ Arbitre: {referee_data['name']}")
                updated += 1
        else:
            print(f"  ✗ Pas de données arbitre")
    
    print(f"\n✅ {updated} matchs mis à jour avec les arbitres")


if __name__ == '__main__':
    print("🚀 Récupération des données arbitres...")
    fetch_and_update_referees()

