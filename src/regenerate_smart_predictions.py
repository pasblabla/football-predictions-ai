import sys
sys.path.insert(0, '/home/ubuntu/football-api')

from src.main import app, db
from src.models.football import Match, Prediction
from src.smart_prediction_engine import SmartPredictionEngine

def regenerate_predictions():
    """Régénérer toutes les prédictions avec le moteur intelligent"""
    
    with app.app_context():
        engine = SmartPredictionEngine()
        
        # Supprimer les anciennes prédictions
        Prediction.query.delete()
        db.session.commit()
        print("🗑️  Anciennes prédictions supprimées")
        
        # Récupérer tous les matchs à venir
        matches = Match.query.filter(Match.status.in_(['SCHEDULED', 'TIMED'])).all()
        
        print(f"\n📊 Régénération des prédictions pour {len(matches)} matchs...")
        
        count = 0
        for match in matches:
            # Générer la prédiction
            prediction_data = engine.predict_match(
                match.home_team.name,
                match.away_team.name,
                match.league.name
            )
            
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
        print("\n📊 Exemples de prédictions améliorées:")
        
        # Afficher quelques exemples
        sample_matches = Match.query.join(Prediction).limit(10).all()
        for match in sample_matches:
            pred = match.predictions
            print(f"\n{match.home_team.name} vs {match.away_team.name}")
            print(f"  Pronostic: {pred.predicted_winner} ({pred.confidence})")
            print(f"  Probabilités: {int(pred.prob_home_win*100)}% - {int(pred.prob_draw*100)}% - {int(pred.prob_away_win*100)}%")
            print(f"  Score prédit: {pred.predicted_score_home}-{pred.predicted_score_away}")
            print(f"  Fiabilité: {pred.reliability_score}/10")
        
        # Afficher les stats globales
        print(f"\n📈 Statistiques:")
        high_conf = Prediction.query.filter_by(confidence='Élevée').count()
        med_conf = Prediction.query.filter_by(confidence='Moyenne').count()
        low_conf = Prediction.query.filter_by(confidence='Faible').count()
        
        print(f"  Confiance élevée: {high_conf}")
        print(f"  Confiance moyenne: {med_conf}")
        print(f"  Confiance faible: {low_conf}")
        
        avg_reliability = db.session.query(db.func.avg(Prediction.reliability_score)).scalar()
        print(f"  Fiabilité moyenne: {avg_reliability:.1f}/10")

if __name__ == '__main__':
    regenerate_predictions()

