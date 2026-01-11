import sys
sys.path.insert(0, '/home/ubuntu/football-api')

from src.main import app, db
from src.models.football import Match, Prediction, Team
from src.improved_prediction_engine import ImprovedPredictionEngine

def regenerate_all_predictions():
    """Régénérer toutes les prédictions avec le moteur amélioré"""
    
    with app.app_context():
        engine = ImprovedPredictionEngine()
        
        # Supprimer les anciennes prédictions
        Prediction.query.delete()
        db.session.commit()
        
        print("🗑️  Anciennes prédictions supprimées")
        
        # Récupérer tous les matchs à venir
        matches = Match.query.filter(Match.status.in_(['SCHEDULED', 'TIMED'])).all()
        
        print(f"📊 Régénération des prédictions pour {len(matches)} matchs...")
        
        count = 0
        for match in matches:
            # Récupérer les statistiques des équipes
            home_stats = {
                'position': match.home_team.league_position,
                'points': match.home_team.points,
                'played': match.home_team.played_games,
                'wins': match.home_team.wins,
                'draws': match.home_team.draws,
                'losses': match.home_team.losses,
                'goals_for': match.home_team.goals_for,
                'goals_against': match.home_team.goals_against,
                'goal_difference': match.home_team.goal_difference
            }
            
            away_stats = {
                'position': match.away_team.league_position,
                'points': match.away_team.points,
                'played': match.away_team.played_games,
                'wins': match.away_team.wins,
                'draws': match.away_team.draws,
                'losses': match.away_team.losses,
                'goals_for': match.away_team.goals_for,
                'goals_against': match.away_team.goals_against,
                'goal_difference': match.away_team.goal_difference
            }
            
            # Générer la prédiction
            prediction_data = engine.predict_match(home_stats, away_stats, match.league.name)
            
            # Créer la prédiction
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
            count += 1
            
            if count % 10 == 0:
                print(f"  ✅ {count} prédictions générées...")
        
        db.session.commit()
        
        print(f"\n✅ {count} prédictions régénérées avec succès!")
        print("\n📊 Exemples de prédictions:")
        
        # Afficher quelques exemples
        sample_matches = Match.query.join(Prediction).limit(5).all()
        for match in sample_matches:
            pred = match.predictions
            print(f"\n{match.home_team.name} vs {match.away_team.name}")
            print(f"  Pronostic: {pred.predicted_winner} ({pred.confidence})")
            print(f"  Probabilités: {int(pred.prob_home_win*100)}% - {int(pred.prob_draw*100)}% - {int(pred.prob_away_win*100)}%")
            print(f"  Score prédit: {pred.predicted_score_home}-{pred.predicted_score_away}")
            print(f"  Fiabilité: {pred.reliability_score}/10")

if __name__ == '__main__':
    regenerate_all_predictions()

