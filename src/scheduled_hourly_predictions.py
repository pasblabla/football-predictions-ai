#!/usr/bin/env python3.11
"""
Script de mise à jour horaire des prédictions du Top 10
- Recalcule les prédictions toutes les heures
- Ajuste si les statistiques des équipes changent
- Met à jour le Top 10 en conséquence
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from src.main import app, db
from src.models.football import Match, Prediction
from src.ml_prediction_engine import MLPredictionEngine

def update_top_predictions():
    """Mettre à jour les prédictions des matchs à venir dans les prochaines 48h"""
    
    print(f"🔄 Mise à jour des prédictions - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    engine = MLPredictionEngine()
    updated_count = 0
    
    with app.app_context():
        # Récupérer les matchs à venir dans les 48 prochaines heures
        now = datetime.now()
        in_48h = now + timedelta(hours=48)
        
        upcoming_matches = Match.query.filter(
            Match.date >= now,
            Match.date <= in_48h,
            Match.status.in_(['SCHEDULED', 'TIMED'])
        ).all()
        
        print(f"📊 {len(upcoming_matches)} matchs à venir dans les 48h")
        
        for match in upcoming_matches:
            try:
                # Récupérer les équipes
                home_team = match.home_team
                away_team = match.away_team
                league = match.league
                
                if not home_team or not away_team or not league:
                    continue
                
                # Générer une nouvelle prédiction
                prediction_data = engine.predict_match(
                    home_team_id=home_team.external_id,
                    away_team_id=away_team.external_id,
                    league_id=league.external_id,
                    home_team_name=home_team.name,
                    away_team_name=away_team.name,
                    league_name=league.name
                )
                
                # Mettre à jour ou créer la prédiction
                if match.prediction:
                    pred = match.prediction
                    
                    # Vérifier si la prédiction a changé
                    old_winner = pred.predicted_winner
                    new_winner = prediction_data['predicted_winner']
                    
                    if old_winner != new_winner:
                        print(f"  🔄 {home_team.name} vs {away_team.name}: {old_winner} → {new_winner}")
                    
                    pred.predicted_winner = new_winner
                    pred.confidence = prediction_data['confidence']
                    pred.prob_home_win = prediction_data['prob_home_win']
                    pred.prob_draw = prediction_data['prob_draw']
                    pred.prob_away_win = prediction_data['prob_away_win']
                    pred.predicted_score_home = prediction_data['predicted_score_home']
                    pred.predicted_score_away = prediction_data['predicted_score_away']
                    pred.reliability_score = prediction_data['reliability_score']
                    pred.prob_over_2_5 = prediction_data['prob_over_2_5']
                    pred.prob_both_teams_score = prediction_data['prob_both_teams_score']
                    
                else:
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
                
                updated_count += 1
                
            except Exception as e:
                print(f"❌ Erreur pour le match {match.id}: {str(e)}")
                continue
        
        db.session.commit()
        
        # Afficher le nouveau Top 10
        print(f"\n✅ {updated_count} prédictions mises à jour")
        print("\n🏆 TOP 10 MATCHS LES PLUS FIABLES:")
        print("-" * 70)
        
        top_matches = Match.query.join(Prediction).filter(
            Match.date >= now,
            Match.status.in_(['SCHEDULED', 'TIMED'])
        ).order_by(Prediction.reliability_score.desc()).limit(10).all()
        
        for i, match in enumerate(top_matches, 1):
            pred = match.prediction
            print(f"{i:2d}. {match.home_team.name} vs {match.away_team.name}")
            print(f"    Fiabilité: {pred.reliability_score}/10 | Prédiction: {pred.predicted_winner} | Confiance: {pred.confidence}")
            print(f"    Date: {match.date.strftime('%d/%m %H:%M')}")
        
        print("-" * 70)

def main():
    """Fonction principale de mise à jour horaire"""
    update_top_predictions()

if __name__ == '__main__':
    main()

