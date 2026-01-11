"""
Système de mise à jour incrémentale des données
- Garde les données existantes
- Ajoute seulement les nouveaux matchs
- Met à jour les statistiques sans tout supprimer
"""

import os
import sys
import requests
from datetime import datetime, timedelta
import time
import shutil

sys.path.insert(0, '/home/ubuntu/football-api')
from src.main import app, db
from src.models.football import League, Team, Match, Prediction
from src.smart_prediction_engine import SmartPredictionEngine

API_KEY = os.environ.get('FOOTBALL_DATA_API_KEY', '647c75a7ce7f482598c8240664bd856c')
BASE_URL = 'https://api.football-data.org/v4'

headers = {
    'X-Auth-Token': API_KEY
}

COMPETITIONS = {
    'PL': 2021,    # Premier League
    'FL1': 2015,   # Ligue 1
    'BL1': 2002,   # Bundesliga
    'SA': 2019,    # Serie A
    'PD': 2014,    # La Liga
    'PPL': 2017,   # Primeira Liga
    'DED': 2003,   # Eredivisie
    'CL': 2001,    # Champions League
}

def backup_database():
    """Créer une sauvegarde de la base de données"""
    db_path = '/home/ubuntu/football-api/src/database/app.db'
    if os.path.exists(db_path):
        backup_path = f'/home/ubuntu/football-api/backups/database_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        os.makedirs('/home/ubuntu/football-api/backups', exist_ok=True)
        shutil.copy2(db_path, backup_path)
        print(f"💾 Sauvegarde créée: {backup_path}")
        return backup_path
    else:
        print(f"⚠️  Base de données non trouvée: {db_path}")
    return None

def update_matches():
    """Mettre à jour les matchs sans supprimer les données existantes"""
    
    with app.app_context():
        # Créer une sauvegarde avant la mise à jour
        backup_path = backup_database()
        
        engine = SmartPredictionEngine()
        new_matches = 0
        updated_matches = 0
        
        for code, comp_id in COMPETITIONS.items():
            try:
                print(f"\n📥 Mise à jour de {code}...")
                
                # Vérifier si la ligue existe
                league = League.query.filter_by(code=code).first()
                
                if not league:
                    # Créer la ligue si elle n'existe pas
                    comp_url = f"{BASE_URL}/competitions/{comp_id}"
                    comp_response = requests.get(comp_url, headers=headers)
                    
                    if comp_response.status_code == 429:
                        print(f"⚠️  Limite de taux atteinte, pause de 70s...")
                        time.sleep(70)
                        comp_response = requests.get(comp_url, headers=headers)
                    
                    if comp_response.status_code != 200:
                        print(f"❌ Erreur {comp_response.status_code} pour {code}")
                        continue
                    
                    comp_data = comp_response.json()
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
                    print(f"✅ Ligue créée: {league.name}")
                    time.sleep(7)
                
                # Récupérer les matchs des 30 prochains jours
                date_from = datetime.now().strftime('%Y-%m-%d')
                date_to = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                
                matches_url = f"{BASE_URL}/competitions/{comp_id}/matches?dateFrom={date_from}&dateTo={date_to}"
                matches_response = requests.get(matches_url, headers=headers)
                
                if matches_response.status_code == 429:
                    print(f"⚠️  Limite de taux atteinte, pause de 70s...")
                    time.sleep(70)
                    matches_response = requests.get(matches_url, headers=headers)
                
                if matches_response.status_code != 200:
                    print(f"❌ Erreur {matches_response.status_code} pour les matchs de {code}")
                    continue
                
                matches_data = matches_response.json()
                matches_list = matches_data.get('matches', [])
                
                league_new = 0
                league_updated = 0
                
                for match_data in matches_list:
                    external_match_id = match_data.get('id')
                    
                    # Vérifier si le match existe déjà
                    existing_match = Match.query.filter_by(external_id=external_match_id).first()
                    
                    if existing_match:
                        # Mettre à jour le statut du match existant
                        old_status = existing_match.status
                        new_status = match_data.get('status', 'SCHEDULED')
                        
                        if old_status != new_status:
                            existing_match.status = new_status
                            
                            # Si le match est terminé, enregistrer le score
                            if new_status == 'FINISHED':
                                score = match_data.get('score', {}).get('fullTime', {})
                                existing_match.home_score = score.get('home')
                                existing_match.away_score = score.get('away')
                            
                            db.session.commit()
                            league_updated += 1
                            updated_matches += 1
                        
                        continue
                    
                    # Créer un nouveau match
                    home_team_data = match_data.get('homeTeam', {})
                    away_team_data = match_data.get('awayTeam', {})
                    
                    home_team_id = home_team_data.get('id')
                    away_team_id = away_team_data.get('id')
                    
                    if not home_team_id or not away_team_id:
                        continue
                    
                    # Créer ou récupérer les équipes
                    home_team = Team.query.filter_by(external_id=home_team_id).first()
                    if not home_team:
                        home_team = Team(
                            name=home_team_data.get('name'),
                            country=league.country,
                            external_id=home_team_id
                        )
                        db.session.add(home_team)
                    
                    away_team = Team.query.filter_by(external_id=away_team_id).first()
                    if not away_team:
                        away_team = Team(
                            name=away_team_data.get('name'),
                            country=league.country,
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
                        external_id=external_match_id
                    )
                    
                    db.session.add(match)
                    db.session.commit()
                    
                    # Générer une prédiction pour les matchs à venir
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
                    
                    league_new += 1
                    new_matches += 1
                
                db.session.commit()
                
                if league_new > 0 or league_updated > 0:
                    print(f"✅ {code}: +{league_new} nouveaux, {league_updated} mis à jour")
                else:
                    print(f"✓ {code}: Aucune mise à jour nécessaire")
                
                time.sleep(7)
                
            except Exception as e:
                print(f"❌ Erreur pour {code}: {str(e)}")
                db.session.rollback()
                continue
        
        print(f"\n✅ Mise à jour terminée:")
        print(f"  📊 {new_matches} nouveaux matchs ajoutés")
        print(f"  🔄 {updated_matches} matchs mis à jour")
        
        # Statistiques globales
        total_matches = Match.query.count()
        total_teams = Team.query.count()
        total_leagues = League.query.count()
        
        print(f"\n📈 Base de données:")
        print(f"  Ligues: {total_leagues}")
        print(f"  Équipes: {total_teams}")
        print(f"  Matchs: {total_matches}")
        
        # Répartition par ligue
        print(f"\n📋 Matchs à venir par ligue:")
        for league in League.query.all():
            upcoming = Match.query.filter_by(league_id=league.id).filter(
                Match.status.in_(['SCHEDULED', 'TIMED'])
            ).count()
            print(f"  {league.code:6} | {league.name:40} | {upcoming:3} matchs")

if __name__ == '__main__':
    print("🔄 Démarrage de la mise à jour incrémentale...")
    update_matches()
    print("\n✅ Mise à jour terminée avec succès!")

