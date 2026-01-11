#!/usr/bin/env python3.11
"""
Script de mise à jour des statistiques pré-match
Exécuté 1 heure avant chaque match pour mettre à jour les prédictions
avec les dernières statistiques disponibles
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.main import app, db
from src.models.football import Match, Prediction, Team, League
from src.ml_prediction_engine import MLPredictionEngine
import requests
from datetime import datetime, timedelta

API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', '647c75a7ce7f482598c8240664bd856c')
BASE_URL = 'https://api.football-data.org/v4'
headers = {'X-Auth-Token': API_KEY}

def get_upcoming_matches_in_1h():
    """Récupérer les matchs qui commencent dans environ 1 heure"""
    with app.app_context():
        now = datetime.now()
        one_hour_from_now = now + timedelta(hours=1)
        two_hours_from_now = now + timedelta(hours=2)
        
        # Matchs entre 1h et 2h à partir de maintenant
        matches = Match.query.filter(
            Match.date >= one_hour_from_now,
            Match.date <= two_hours_from_now,
            Match.status.in_(['SCHEDULED', 'TIMED'])
        ).all()
        
        return matches

def update_team_statistics(team):
    """Mettre à jour les statistiques d'une équipe depuis l'API"""
    if not team.external_id:
        return False
    
    try:
        # Récupérer les infos de l'équipe
        team_url = f"{BASE_URL}/teams/{team.external_id}"
        response = requests.get(team_url, headers=headers)
        
        if response.status_code == 429:
            print(f"⏸️  Limite de taux, pause...")
            import time
            time.sleep(70)
            response = requests.get(team_url, headers=headers)
        
        if response.status_code != 200:
            return False
        
        team_data = response.json()
        
        # Mettre à jour les informations
        if 'crest' in team_data:
            team.logo = team_data['crest']
        
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"❌ Erreur pour {team.name}: {str(e)}")
        return False

def update_match_prediction(match, engine):
    """Régénérer la prédiction d'un match avec les dernières stats"""
    try:
        # Générer une nouvelle prédiction
        prediction_data = engine.predict_match(
            home_team_id=match.home_team.external_id,
            away_team_id=match.away_team.external_id,
            league_id=match.league.external_id,
            home_team_name=match.home_team.name,
            away_team_name=match.away_team.name,
            league_name=match.league.name
        )
        
        # Mettre à jour la prédiction existante
        if match.prediction:
            pred = match.prediction
            pred.predicted_winner = prediction_data['predicted_winner']
            pred.confidence = prediction_data['confidence']
            pred.prob_home_win = prediction_data['prob_home_win']
            pred.prob_draw = prediction_data['prob_draw']
            pred.prob_away_win = prediction_data['prob_away_win']
            pred.predicted_score_home = prediction_data['predicted_score_home']
            pred.predicted_score_away = prediction_data['predicted_score_away']
            pred.reliability_score = prediction_data['reliability_score']
            pred.prob_over_2_5 = prediction_data['prob_over_2_5']
            pred.prob_both_teams_score = prediction_data['prob_both_teams_score']
            pred.updated_at = datetime.now()
        else:
            # Créer une nouvelle prédiction
            pred = Prediction(
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
            db.session.add(pred)
        
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"❌ Erreur prédiction: {str(e)}")
        db.session.rollback()
        return False

def main():
    print("=" * 70)
    print(f"🔄 MISE À JOUR PRÉ-MATCH - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Récupérer les matchs qui commencent dans 1h
    matches = get_upcoming_matches_in_1h()
    
    if not matches:
        print("\n✅ Aucun match dans l'heure à venir")
        print("=" * 70)
        return
    
    print(f"\n⚽ {len(matches)} match(s) dans l'heure à venir\n")
    
    engine = MLPredictionEngine()
    updated_count = 0
    
    with app.app_context():
        for match in matches:
            print(f"📊 {match.home_team.name} vs {match.away_team.name}")
            print(f"   Heure: {match.date.strftime('%H:%M')}")
            print(f"   Ligue: {match.league.name}")
            
            # Mettre à jour les statistiques des équipes
            print(f"   🔄 Mise à jour des statistiques...")
            update_team_statistics(match.home_team)
            update_team_statistics(match.away_team)
            
            # Régénérer la prédiction
            print(f"   🎯 Régénération de la prédiction...")
            if update_match_prediction(match, engine):
                updated_count += 1
                print(f"   ✅ Prédiction mise à jour")
            else:
                print(f"   ⚠️  Erreur lors de la mise à jour")
            
            print()
    
    print("=" * 70)
    print(f"✅ MISE À JOUR TERMINÉE")
    print(f"Matchs mis à jour: {updated_count}/{len(matches)}")
    print("=" * 70)

if __name__ == '__main__':
    main()

