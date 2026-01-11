#!/usr/bin/env python3
"""
Script pour récupérer les arbitres des matchs historiques terminés
"""
import sqlite3
import requests
import time

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
                    'external_id': main_referee.get('id')
                }
        
        return None
        
    except Exception as e:
        print(f"  ✗ Erreur: {str(e)}")
        return None


def create_referee_tables():
    """Crée les tables pour les arbitres si elles n'existent pas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table des arbitres
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            nationality TEXT,
            total_matches INTEGER DEFAULT 0,
            total_yellow_cards INTEGER DEFAULT 0,
            total_red_cards INTEGER DEFAULT 0,
            avg_yellow_cards REAL DEFAULT 0,
            avg_red_cards REAL DEFAULT 0
        )
    """)
    
    # Table de liaison match-arbitre
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_referee (
            match_id INTEGER,
            referee_id INTEGER,
            FOREIGN KEY (match_id) REFERENCES match(id),
            FOREIGN KEY (referee_id) REFERENCES referee(id),
            PRIMARY KEY (match_id, referee_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✓ Tables arbitres créées")


def update_match_referee(match_id, referee_data):
    """Met à jour les données de l'arbitre dans la base"""
    if not referee_data:
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insérer ou mettre à jour l'arbitre
        cursor.execute("""
            INSERT OR IGNORE INTO referee (external_id, name, nationality)
            VALUES (?, ?, ?)
        """, (referee_data['external_id'], referee_data['name'], referee_data['nationality']))
        
        # Récupérer l'ID de l'arbitre
        cursor.execute("SELECT id FROM referee WHERE external_id = ?", (referee_data['external_id'],))
        result = cursor.fetchone()
        
        if result:
            referee_id = result[0]
            
            # Lier le match à l'arbitre
            cursor.execute("""
                INSERT OR IGNORE INTO match_referee (match_id, referee_id)
                VALUES (?, ?)
            """, (match_id, referee_id))
            
            # Mettre à jour le compteur de matchs de l'arbitre
            cursor.execute("""
                UPDATE referee 
                SET total_matches = (
                    SELECT COUNT(*) FROM match_referee WHERE referee_id = ?
                )
                WHERE id = ?
            """, (referee_id, referee_id))
            
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
        
    except Exception as e:
        print(f"  ✗ Erreur DB: {str(e)}")
        return False


def fetch_historical_referees():
    """Récupère les arbitres pour tous les matchs terminés"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Récupérer les matchs terminés avec external_id
    cursor.execute("""
        SELECT id, external_id, home_score, away_score
        FROM match 
        WHERE home_score IS NOT NULL 
        AND external_id IS NOT NULL
        ORDER BY date DESC
    """)
    
    matches = cursor.fetchall()
    conn.close()
    
    print(f"\n📊 {len(matches)} matchs terminés trouvés")
    print("🔍 Récupération des arbitres...\n")
    
    updated = 0
    errors = 0
    
    for i, (match_id, external_id, home_score, away_score) in enumerate(matches, 1):
        print(f"[{i}/{len(matches)}] Match {match_id} (score: {home_score}-{away_score})...", end=" ")
        
        referee_data = fetch_referee_data(external_id)
        
        if referee_data:
            if update_match_referee(match_id, referee_data):
                print(f"✓ {referee_data['name']} ({referee_data['nationality']})")
                updated += 1
            else:
                print("✗ Erreur DB")
                errors += 1
        else:
            print("✗ Pas de données")
            errors += 1
        
        # Pause pour respecter les limites de l'API (10 requêtes/minute)
        if i % 10 == 0:
            print("⏸️  Pause 60s (limite API)...")
            time.sleep(60)
        else:
            time.sleep(1)
    
    print(f"\n✅ Terminé !")
    print(f"   - {updated} arbitres récupérés")
    print(f"   - {errors} erreurs")
    
    # Afficher les statistiques
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM referee")
    total_refs = cursor.fetchone()[0]
    cursor.execute("SELECT name, total_matches FROM referee ORDER BY total_matches DESC LIMIT 5")
    top_refs = cursor.fetchall()
    conn.close()
    
    print(f"\n📈 Statistiques:")
    print(f"   - Total arbitres: {total_refs}")
    print(f"   - Top 5 arbitres:")
    for name, matches in top_refs:
        print(f"     • {name}: {matches} matchs")


if __name__ == '__main__':
    print("🚀 Récupération des arbitres historiques")
    print("=" * 50)
    
    create_referee_tables()
    fetch_historical_referees()

