#!/usr/bin/env python3
"""
Script simple pour remplir l'historique des matchs terminés
"""
import sqlite3
import requests
from datetime import datetime, timedelta

API_KEY = '647c75a7ce7f482598c8240664bd856c'
DB_PATH = '/home/ubuntu/football-api-deploy/server/database/app.db'

LEAGUES = {
    'PL': 2021,   # Premier League
    'FL1': 2015,  # Ligue 1
    'BL1': 2002,  # Bundesliga
    'SA': 2019,   # Serie A
    'PD': 2014,   # La Liga
    'PPL': 2017,  # Primeira Liga
    'DED': 2003,  # Eredivisie
    'CL': 2001    # Champions League
}

def get_finished_matches():
    """Récupère les matchs terminés des 7 derniers jours"""
    date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    all_matches = []
    
    for league_code, league_id in LEAGUES.items():
        try:
            url = f'https://api.football-data.org/v4/competitions/{league_code}/matches'
            params = {
                'dateFrom': date_from,
                'dateTo': date_to,
                'status': 'FINISHED'
            }
            headers = {'X-Auth-Token': API_KEY}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                print(f"✓ {league_code}: {len(matches)} matchs terminés")
                all_matches.extend(matches)
            else:
                print(f"✗ {league_code}: Erreur {response.status_code}")
                
        except Exception as e:
            print(f"✗ {league_code}: {str(e)}")
    
    return all_matches

def update_database(matches):
    """Met à jour la base de données avec les résultats"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updated = 0
    
    for match in matches:
        try:
            match_id = match['id']
            home_score = match['score']['fullTime']['home']
            away_score = match['score']['fullTime']['away']
            
            # Chercher le match dans la base
            cursor.execute("""
                SELECT id FROM match 
                WHERE external_id = ? OR (
                    date LIKE ? AND 
                    home_team_id IN (SELECT id FROM team WHERE name LIKE ?) AND
                    away_team_id IN (SELECT id FROM team WHERE name LIKE ?)
                )
            """, (
                match_id,
                match['utcDate'][:10] + '%',
                '%' + match['homeTeam']['name'][:10] + '%',
                '%' + match['awayTeam']['name'][:10] + '%'
            ))
            
            result = cursor.fetchone()
            
            if result:
                db_match_id = result[0]
                cursor.execute("""
                    UPDATE match 
                    SET home_score = ?, away_score = ?, status = 'FINISHED'
                    WHERE id = ?
                """, (home_score, away_score, db_match_id))
                updated += 1
                
        except Exception as e:
            print(f"Erreur match {match_id}: {str(e)}")
            continue
    
    conn.commit()
    conn.close()
    
    return updated

if __name__ == '__main__':
    print("🚀 Récupération des matchs terminés...")
    matches = get_finished_matches()
    print(f"\n📊 Total: {len(matches)} matchs récupérés")
    
    print("\n💾 Mise à jour de la base de données...")
    updated = update_database(matches)
    print(f"✅ {updated} matchs mis à jour dans la base")

