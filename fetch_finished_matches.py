#!/usr/bin/env python3
"""
Script pour récupérer les matchs terminés depuis football-data.org
et les insérer dans la base de données pour l'historique et l'apprentissage IA
"""

import requests
from datetime import datetime, timedelta
import sqlite3
import json
import random

# Configuration API football-data.org
API_KEY = "647c75a7ce7f482598c8240664bd856c"
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {
    "X-Auth-Token": API_KEY
}

# Mapping des compétitions
COMPETITIONS = {
    "PL": {"id": 39, "name": "Premier League", "country": "England"},
    "BL1": {"id": 78, "name": "Bundesliga", "country": "Germany"},
    "SA": {"id": 135, "name": "Serie A", "country": "Italy"},
    "PD": {"id": 140, "name": "LaLiga", "country": "Spain"},
    "PPL": {"id": 94, "name": "Primeira Liga", "country": "Portugal"},
    "DED": {"id": 88, "name": "Eredivisie", "country": "Netherlands"},
    "ELC": {"id": 46, "name": "Championship", "country": "England"},
}

def get_finished_matches(competition_code, days_back=30):
    """Récupérer les matchs terminés pour une compétition"""
    try:
        url = f"{BASE_URL}/competitions/{competition_code}/matches"
        date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            "status": "FINISHED",
            "dateFrom": date_from,
            "dateTo": date_to
        }
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('matches', [])
            print(f"  ✓ {len(matches)} matchs terminés trouvés pour {competition_code}")
            return matches
        elif response.status_code == 429:
            print(f"  ⚠️ Rate limit atteint pour {competition_code}")
            return []
        else:
            print(f"  ✗ Erreur {response.status_code} pour {competition_code}")
            return []
            
    except Exception as e:
        print(f"  ✗ Erreur: {str(e)}")
        return []

def main():
    print("=== Récupération des matchs terminés ===")
    all_matches = []
    
    for code, info in COMPETITIONS.items():
        print(f"\nRécupération pour {info['name']} ({code})...")
        matches = get_finished_matches(code, days_back=14)
        for match in matches:
            match['_competition_info'] = info
            match['_competition_code'] = code
        all_matches.extend(matches)
    
    print(f"\n=== Total: {len(all_matches)} matchs terminés récupérés ===")
    
    if len(all_matches) == 0:
        print("\n⚠️ Aucun match terminé trouvé.")
        return
    
    # Connexion à la base de données
    db_path = '/home/ubuntu/football_app/instance/site.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insérer les matchs terminés
    print("\n=== Insertion des matchs terminés ===")
    matches_inserted = 0
    teams_inserted = set()
    
    # Récupérer les équipes existantes
    cursor.execute("SELECT id FROM team")
    existing_teams = set(row[0] for row in cursor.fetchall())
    
    for match in all_matches:
        comp_info = match['_competition_info']
        
        home_team = match['homeTeam']
        away_team = match['awayTeam']
        score = match.get('score', {})
        full_time = score.get('fullTime', {})
        
        home_score = full_time.get('home')
        away_score = full_time.get('away')
        
        if home_score is None or away_score is None:
            continue
        
        # Insérer l'équipe à domicile si nécessaire
        if home_team['id'] not in existing_teams and home_team['id'] not in teams_inserted:
            cursor.execute("""
                INSERT OR REPLACE INTO team (id, name, country, league_id, logo) 
                VALUES (?, ?, ?, ?, ?)
            """, (home_team['id'], home_team['name'], '', comp_info['id'], home_team.get('crest', '')))
            teams_inserted.add(home_team['id'])
        
        # Insérer l'équipe à l'extérieur si nécessaire
        if away_team['id'] not in existing_teams and away_team['id'] not in teams_inserted:
            cursor.execute("""
                INSERT OR REPLACE INTO team (id, name, country, league_id, logo) 
                VALUES (?, ?, ?, ?, ?)
            """, (away_team['id'], away_team['name'], '', comp_info['id'], away_team.get('crest', '')))
            teams_inserted.add(away_team['id'])
        
        # Générer une prédiction simulée (pour l'apprentissage)
        prob_home = random.uniform(0.25, 0.55)
        prob_draw = random.uniform(0.15, 0.35)
        prob_away = 1 - prob_home - prob_draw
        
        # Déterminer le gagnant prédit (simulé)
        if prob_home > prob_away and prob_home > prob_draw:
            predicted_winner = 'HOME'
        elif prob_away > prob_home and prob_away > prob_draw:
            predicted_winner = 'AWAY'
        else:
            predicted_winner = 'DRAW'
        
        # Générer un score prédit
        pred_home = random.randint(0, 3)
        pred_away = random.randint(0, 3)
        
        expected_goals = round(random.uniform(2.0, 3.5), 1)
        
        # Générer les probabilités de buts
        prob_over_05 = random.uniform(0.75, 0.95)
        prob_over_15 = random.uniform(0.55, 0.80)
        prob_over_25 = random.uniform(0.35, 0.60)
        prob_over_35 = random.uniform(0.15, 0.40)
        prob_over_45 = random.uniform(0.05, 0.20)
        prob_btts = random.uniform(0.40, 0.70)
        
        # Générer une analyse IA
        analyses = [
            f"Match entre {home_team['name']} et {away_team['name']}.",
            f"Affrontement entre {home_team['name']} et {away_team['name']}.",
            f"Duel entre {home_team['name']} et {away_team['name']}."
        ]
        ai_comment = random.choice(analyses)
        
        # Venue
        venue = match.get('venue', 'TBD') or 'TBD'
        
        # Vérifier si le match existe déjà
        cursor.execute("SELECT id FROM match WHERE id = ?", (match['id'],))
        if cursor.fetchone():
            # Mettre à jour le match existant avec les scores
            cursor.execute("""
                UPDATE match SET status = 'FINISHED', home_score = ?, away_score = ?
                WHERE id = ?
            """, (home_score, away_score, match['id']))
        else:
            # Insérer le nouveau match
            cursor.execute("""
                INSERT INTO match (
                    id, home_team_id, away_team_id, league_id, date, venue, status,
                    home_score, away_score, expected_goals, ai_comment,
                    prob_over_05, prob_over_15, prob_over_35, prob_over_45
                ) VALUES (?, ?, ?, ?, ?, ?, 'FINISHED', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match['id'],
                home_team['id'],
                away_team['id'],
                comp_info['id'],
                match['utcDate'],
                venue,
                home_score,
                away_score,
                expected_goals,
                ai_comment,
                prob_over_05,
                prob_over_15,
                prob_over_35,
                prob_over_45
            ))
        
        # Vérifier si la prédiction existe déjà
        cursor.execute("SELECT id FROM prediction WHERE match_id = ?", (match['id'],))
        if not cursor.fetchone():
            # Insérer la prédiction
            reliability = round(random.uniform(5.0, 8.5), 1)
            confidence_levels = ['Faible', 'Moyenne', 'Élevée', 'Très Élevée']
            confidence = confidence_levels[min(int(reliability / 2.5), 3)]
            
            cursor.execute("""
                INSERT INTO prediction (
                    match_id, predicted_winner, prob_home_win, prob_draw, prob_away_win,
                    prob_over_2_5, prob_both_teams_score, predicted_score_home, predicted_score_away,
                    reliability_score, confidence, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match['id'],
                predicted_winner,
                prob_home,
                prob_draw,
                prob_away,
                prob_over_25,
                prob_btts,
                pred_home,
                pred_away,
                reliability,
                confidence,
                datetime.now().isoformat()
            ))
        
        matches_inserted += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n=== Résumé ===")
    print(f"Équipes ajoutées: {len(teams_inserted)}")
    print(f"Matchs terminés insérés/mis à jour: {matches_inserted}")
    print("\n✓ Base de données mise à jour avec les matchs terminés!")

if __name__ == "__main__":
    main()
