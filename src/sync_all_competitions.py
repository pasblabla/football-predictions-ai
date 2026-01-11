import os
import sys
import requests
from datetime import datetime, timedelta
import time

sys.path.insert(0, '/home/ubuntu/football-api')
from src.main import app, db
from src.models.football import League, Team, Match, Prediction
from src.smart_prediction_engine import SmartPredictionEngine

API_KEY = os.environ.get('FOOTBALL_DATA_API_KEY', '647c75a7ce7f482598c8240664bd856c')
BASE_URL = 'https://api.football-data.org/v4'

headers = {
    'X-Auth-Token': API_KEY
}

# Toutes les compétitions disponibles
COMPETITIONS = {
    'PL': 2021,    # Premier League
    'FL1': 2015,   # Ligue 1
    'BL1': 2002,   # Bundesliga
    'SA': 2019,    # Serie A
    'PD': 2014,    # La Liga
    'PPL': 2017,   # Primeira Liga
    'DED': 2003,   # Eredivisie
    'CL': 2001,    # Champions League
    'ELC': 2016,   # Championship (England)
    'EC': 2018,    # European Championship
    'WC': 2000,    # FIFA World Cup
}

def sync_all_competitions():
    """Synchroniser toutes les compétitions disponibles"""
    
    with app.app_context():
        # Supprimer les anciennes données
        print("🗑️  Suppression des anciennes données...")
        Match.query.delete()
        Prediction.query.delete()
        Team.query.delete()
        League.query.delete()
        db.session.commit()
        
        engine = SmartPredictionEngine()
        total_matches = 0
        total_leagues = 0
        
        for code, comp_id in COMPETITIONS.items():
            try:
                print(f"\n📥 Synchronisation de {code}...")
                
                # Récupérer les infos de la compétition
                comp_url = f"{BASE_URL}/competitions/{comp_id}"
                comp_response = requests.get(comp_url, headers=headers)
                
                if comp_response.status_code == 429:
                    wait_time = 70
                    print(f"⚠️  Limite de taux atteinte, pause de {wait_time}s...")
                    time.sleep(wait_time)
                    comp_response = requests.get(comp_url, headers=headers)
                
                if comp_response.status_code != 200:
                    print(f"❌ Erreur {comp_response.status_code} pour {code}")
                    continue
                
                comp_data = comp_response.json()
                
                # Créer la ligue
                current_season = comp_data.get('currentSeason', {})
                league = League(
                    name=comp_data.get('name'),
                    country=comp_data.get('area', {}).get('name', 'Unknown'),
                    code=code,
                    season=f"{current_season.get('startDate', '2024')[:4]}-{current_season.get('endDate', '2025')[:4][-2:]}",
                    external_id=comp_id
                )
                db.session.add(league)
                db.session.commit()
                total_leagues += 1
                
                print(f"✅ Ligue: {league.name}")
                
                # Pause pour éviter la limite de taux
                time.sleep(7)
                
                # Récupérer les matchs des 30 prochains jours
                date_from = datetime.now().strftime('%Y-%m-%d')
                date_to = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                
                matches_url = f"{BASE_URL}/competitions/{comp_id}/matches?dateFrom={date_from}&dateTo={date_to}"
                matches_response = requests.get(matches_url, headers=headers)
                
                if matches_response.status_code == 429:
                    wait_time = 70
                    print(f"⚠️  Limite de taux atteinte, pause de {wait_time}s...")
                    time.sleep(wait_time)
                    matches_response = requests.get(matches_url, headers=headers)
                
                if matches_response.status_code != 200:
                    print(f"❌ Erreur {matches_response.status_code} pour les matchs de {code}")
                    continue
                
                matches_data = matches_response.json()
                matches_list = matches_data.get('matches', [])
                
                print(f"📊 {len(matches_list)} matchs trouvés")
                
                match_count = 0
                for match_data in matches_list:
                    # Créer ou récupérer les équipes
                    home_team_data = match_data.get('homeTeam', {})
                    away_team_data = match_data.get('awayTeam', {})
                    
                    home_team_id = home_team_data.get('id')
                    away_team_id = away_team_data.get('id')
                    
                    if not home_team_id or not away_team_id:
                        continue
                    
                    home_team = Team.query.filter_by(external_id=home_team_id).first()
                    if not home_team:
                        home_team = Team(
                            name=home_team_data.get('name'),
                            country=comp_data.get('area', {}).get('name', 'Unknown'),
                            external_id=home_team_id
                        )
                        db.session.add(home_team)
                    
                    away_team = Team.query.filter_by(external_id=away_team_id).first()
                    if not away_team:
                        away_team = Team(
                            name=away_team_data.get('name'),
                            country=comp_data.get('area', {}).get('name', 'Unknown'),
                            external_id=away_team_id
                        )
                        db.session.add(away_team)
                    
                    db.session.commit()
                    
                    # Créer le match
                    match_date_str = match_data.get('utcDate')
                    if match_date_str:
                        match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
                    else:
                        continue
                    
                    match = Match(
                        date=match_date,
                        status=match_data.get('status', 'SCHEDULED'),
                        venue=match_data.get('venue'),
                        league_id=league.id,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        external_id=match_data.get('id')
                    )
                    
                    db.session.add(match)
                    db.session.commit()
                    
                    # Générer une prédiction
                    if match.status in ['SCHEDULED', 'TIMED']:
                        prediction_data = engine.predict_match(
                            home_team.name,
                            away_team.name,
                            league.name
                        )
                        
                        prediction = Prediction(
                            match_id=match.id,
                            predicted_winner=prediction_data['predicted_winner'],
                            confidence=prediction_data['confidence'],
                            prob_home_win=prediction_data['prob_home_win'],
                            prob_draw=prediction_data['prob_draw'],
                            prob_away_win=prediction_data['prob_away_win'],
                            predicted_score_home=prediction_data['predicted_score_home'],
                            predicted_score_away=prediction_data['predicted_score_away'],
                            reliability_score=prediction_data['reliability_score'],
                            prob_over_2_5=prediction_data['prob_over_2_5'],
                            prob_both_teams_score=prediction_data['prob_both_teams_score']
                        )
                        db.session.add(prediction)
                    
                    match_count += 1
                    total_matches += 1
                
                db.session.commit()
                print(f"✅ {code} synchronisé: {match_count} matchs")
                
                # Pause entre chaque compétition
                time.sleep(7)
                
            except Exception as e:
                print(f"❌ Erreur pour {code}: {str(e)}")
                db.session.rollback()
                continue
        
        print(f"\n✅ Synchronisation terminée:")
        print(f"  📊 {total_leagues} ligues")
        print(f"  ⚽ {total_matches} matchs")
        print(f"  🎯 {total_matches} prédictions")
        
        # Afficher quelques exemples
        print(f"\n📋 Répartition par ligue:")
        leagues = League.query.all()
        for league in leagues:
            match_count = Match.query.filter_by(league_id=league.id).count()
            print(f"  {league.code:6} | {league.name:40} | {match_count:3} matchs")

if __name__ == '__main__':
    sync_all_competitions()

