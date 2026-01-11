"""
Script pour récupérer plus de matchs historiques depuis l'API football-data.org
Objectif: Avoir au moins 500-1000 matchs pour l'entraînement
"""

import os
import sys
import requests
from datetime import datetime, timedelta
import time

sys.path.insert(0, '/home/ubuntu/football_app')
os.chdir('/home/ubuntu/football_app')

API_KEY = "647c75a7ce7f482598c8240664bd856c"
BASE_URL = "https://api.football-data.org/v4"

HEADERS = {
    "X-Auth-Token": API_KEY
}

# Compétitions à récupérer
COMPETITIONS = {
    "PL": "Premier League",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    "PD": "LaLiga",
    "FL1": "Ligue 1",
    "ELC": "Championship",
    "PPL": "Primeira Liga",
    "DED": "Eredivisie"
}

def fetch_matches_for_competition(competition_code, date_from, date_to):
    """Récupérer les matchs terminés pour une compétition"""
    url = f"{BASE_URL}/competitions/{competition_code}/matches"
    params = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "status": "FINISHED"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("matches", [])
        elif response.status_code == 429:
            print(f"  Rate limit atteint, attente de 60 secondes...")
            time.sleep(60)
            return fetch_matches_for_competition(competition_code, date_from, date_to)
        else:
            print(f"  Erreur {response.status_code}: {response.text[:100]}")
            return []
    except Exception as e:
        print(f"  Erreur: {e}")
        return []

def get_or_create_team(db, team_name, league_id):
    """Récupérer ou créer une équipe"""
    from src.models.football import Team
    
    team = Team.query.filter_by(name=team_name).first()
    if not team:
        team = Team(
            name=team_name,
            country="Unknown",
            league_id=league_id
        )
        db.session.add(team)
        db.session.commit()
    return team

def insert_matches_to_db(matches, competition_name):
    """Insérer les matchs dans la base de données"""
    from wsgi import app
    from src.models.football import db, Match, League, Team
    
    inserted = 0
    
    with app.app_context():
        # Récupérer ou créer la ligue
        league = League.query.filter_by(name=competition_name).first()
        if not league:
            league = League(
                name=competition_name,
                country="Unknown",
                code=competition_name[:3].upper(),
                season="2024"
            )
            db.session.add(league)
            db.session.commit()
        
        for match in matches:
            home_team_name = match["homeTeam"]["name"]
            away_team_name = match["awayTeam"]["name"]
            match_date = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))
            
            # Récupérer ou créer les équipes
            home_team = get_or_create_team(db, home_team_name, league.id)
            away_team = get_or_create_team(db, away_team_name, league.id)
            
            # Vérifier si le match existe déjà (par date et équipes)
            existing = Match.query.filter_by(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                date=match_date
            ).first()
            
            if existing:
                continue
            
            # Créer le match
            home_score = match.get("score", {}).get("fullTime", {}).get("home", 0) or 0
            away_score = match.get("score", {}).get("fullTime", {}).get("away", 0) or 0
            
            new_match = Match(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                league_id=league.id,
                date=match_date,
                status="FINISHED",
                home_score=home_score,
                away_score=away_score,
                venue=match.get("venue", "TBD")
            )
            
            db.session.add(new_match)
            inserted += 1
        
        db.session.commit()
    
    return inserted

def main():
    print("=" * 60)
    print("RÉCUPÉRATION DES MATCHS HISTORIQUES")
    print("=" * 60)
    print(f"Date: {datetime.now().isoformat()}")
    print()
    
    # Définir la période (3 mois en arrière)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    date_from = start_date.strftime("%Y-%m-%d")
    date_to = end_date.strftime("%Y-%m-%d")
    
    print(f"Période: {date_from} à {date_to}")
    print()
    
    total_matches = 0
    total_inserted = 0
    
    for code, name in COMPETITIONS.items():
        print(f"Récupération de {name} ({code})...")
        
        matches = fetch_matches_for_competition(code, date_from, date_to)
        print(f"  Matchs récupérés: {len(matches)}")
        
        if matches:
            inserted = insert_matches_to_db(matches, name)
            print(f"  Matchs insérés: {inserted}")
            total_inserted += inserted
        
        total_matches += len(matches)
        
        # Pause pour éviter le rate limit
        time.sleep(2)
    
    print()
    print("=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"Total matchs récupérés: {total_matches}")
    print(f"Total matchs insérés: {total_inserted}")
    
    # Vérifier le nombre total de matchs dans la base
    from wsgi import app
    from src.models.football import Match
    
    with app.app_context():
        total_in_db = Match.query.filter_by(status="FINISHED").count()
        print(f"Total matchs terminés dans la base: {total_in_db}")

if __name__ == "__main__":
    main()
