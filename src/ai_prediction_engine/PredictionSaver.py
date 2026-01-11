"""
Module de sauvegarde automatique des prédictions
Permet de sauvegarder les prédictions générées pour chaque match
et de calculer la précision réelle du modèle après les matchs
"""

from datetime import datetime, timedelta
from src.models.football import db, Match, Prediction, Team
from src.ai_prediction_engine.AdvancedHybridAI import advanced_ai

class PredictionSaver:
    """Classe pour sauvegarder et gérer les prédictions"""
    
    def __init__(self):
        self.model_version = "7.0"
    
    def save_prediction(self, match_id, prediction_data):
        """
        Sauvegarder une prédiction pour un match
        
        Args:
            match_id: ID du match
            prediction_data: Dictionnaire contenant les données de prédiction
        
        Returns:
            Prediction: L'objet Prediction créé ou mis à jour
        """
        # Vérifier si une prédiction existe déjà
        existing = Prediction.query.filter_by(match_id=match_id).first()
        
        if existing:
            # Mettre à jour la prédiction existante
            existing.predicted_winner = prediction_data.get('predicted_winner', 'HOME')
            existing.confidence = prediction_data.get('confidence', 'Moyenne')
            existing.confidence_level = prediction_data.get('confidence_level', 0.5)
            existing.prob_home_win = prediction_data.get('prob_home_win', 0.33)
            existing.prob_draw = prediction_data.get('prob_draw', 0.33)
            existing.prob_away_win = prediction_data.get('prob_away_win', 0.33)
            existing.prob_over_2_5 = prediction_data.get('prob_over_2_5', 0.5)
            existing.prob_both_teams_score = prediction_data.get('prob_btts', 0.5)
            existing.predicted_score_home = prediction_data.get('predicted_score_home', 1)
            existing.predicted_score_away = prediction_data.get('predicted_score_away', 1)
            existing.reliability_score = prediction_data.get('reliability_score', 5.0)
            existing.analysis_date = datetime.utcnow()
            existing.tactical_analysis = prediction_data.get('tactical_analysis', '')
            existing.updated_at = datetime.utcnow()
            
            db.session.commit()
            return existing
        else:
            # Créer une nouvelle prédiction
            prediction = Prediction(
                match_id=match_id,
                predicted_winner=prediction_data.get('predicted_winner', 'HOME'),
                confidence=prediction_data.get('confidence', 'Moyenne'),
                confidence_level=prediction_data.get('confidence_level', 0.5),
                prob_home_win=prediction_data.get('prob_home_win', 0.33),
                prob_draw=prediction_data.get('prob_draw', 0.33),
                prob_away_win=prediction_data.get('prob_away_win', 0.33),
                prob_over_2_5=prediction_data.get('prob_over_2_5', 0.5),
                prob_both_teams_score=prediction_data.get('prob_btts', 0.5),
                predicted_score_home=prediction_data.get('predicted_score_home', 1),
                predicted_score_away=prediction_data.get('predicted_score_away', 1),
                reliability_score=prediction_data.get('reliability_score', 5.0),
                analysis_date=datetime.utcnow(),
                tactical_analysis=prediction_data.get('tactical_analysis', ''),
                created_at=datetime.utcnow()
            )
            
            db.session.add(prediction)
            db.session.commit()
            return prediction
    
    def generate_and_save_predictions_for_upcoming_matches(self, days_ahead=7):
        """
        Générer et sauvegarder les prédictions pour tous les matchs à venir
        
        Args:
            days_ahead: Nombre de jours à l'avance pour générer les prédictions
        
        Returns:
            dict: Statistiques sur les prédictions générées
        """
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)
        
        # Récupérer les matchs programmés sans prédiction
        matches = Match.query.filter(
            Match.status == 'SCHEDULED',
            Match.date >= now,
            Match.date <= end_date
        ).all()
        
        stats = {
            'total_matches': len(matches),
            'predictions_created': 0,
            'predictions_updated': 0,
            'errors': 0
        }
        
        for match in matches:
            try:
                # Vérifier si une prédiction existe déjà
                existing = Prediction.query.filter_by(match_id=match.id).first()
                
                # Générer la prédiction avec le modèle avancé
                home_team_name = match.home_team.name if match.home_team else "Home"
                away_team_name = match.away_team.name if match.away_team else "Away"
                
                # Préparer les données du match
                match_data = {
                    'home_team': home_team_name,
                    'away_team': away_team_name,
                    'league': match.league.name if match.league else "Unknown"
                }
                
                prediction_result = advanced_ai.predict_match(match_data)
                
                # Préparer les données de prédiction
                # Convertir la prédiction 1/X/2 en HOME/DRAW/AWAY
                pred_mapping = {'1': 'HOME', 'X': 'DRAW', '2': 'AWAY'}
                predicted_winner = pred_mapping.get(prediction_result.get('prediction', '1'), 'HOME')
                
                # Extraire le score prédit (format "X-Y")
                predicted_score_str = prediction_result.get('predicted_score', '1-1')
                try:
                    score_parts = predicted_score_str.split('-')
                    pred_score_home = int(score_parts[0])
                    pred_score_away = int(score_parts[1])
                except:
                    pred_score_home = 1
                    pred_score_away = 1
                
                prediction_data = {
                    'predicted_winner': predicted_winner,
                    'confidence': prediction_result.get('confidence', 'Moyenne'),
                    'confidence_level': prediction_result.get('reliability_score', 5.0) / 10,
                    'prob_home_win': prediction_result.get('win_probability_home', 33) / 100,
                    'prob_draw': prediction_result.get('draw_probability', 33) / 100,
                    'prob_away_win': prediction_result.get('win_probability_away', 33) / 100,
                    'prob_over_2_5': prediction_result.get('prob_over_2_5', 50) / 100,
                    'prob_btts': prediction_result.get('btts_probability', 50) / 100,
                    'predicted_score_home': pred_score_home,
                    'predicted_score_away': pred_score_away,
                    'reliability_score': prediction_result.get('reliability_score', 5.0),
                    'tactical_analysis': prediction_result.get('analysis', '')
                }
                
                # Sauvegarder la prédiction
                self.save_prediction(match.id, prediction_data)
                
                if existing:
                    stats['predictions_updated'] += 1
                else:
                    stats['predictions_created'] += 1
                    
            except Exception as e:
                print(f"Erreur lors de la génération de prédiction pour match {match.id}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def update_prediction_results(self):
        """
        Mettre à jour les résultats des prédictions après les matchs terminés
        
        Returns:
            dict: Statistiques sur les mises à jour
        """
        # Récupérer les matchs terminés avec des prédictions non vérifiées
        finished_matches = Match.query.filter(
            Match.status == 'FINISHED',
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).all()
        
        stats = {
            'total_checked': 0,
            'correct_predictions': 0,
            'incorrect_predictions': 0,
            'no_prediction': 0
        }
        
        for match in finished_matches:
            prediction = Prediction.query.filter_by(match_id=match.id).first()
            
            if not prediction:
                stats['no_prediction'] += 1
                continue
            
            # Déterminer le résultat réel
            if match.home_score > match.away_score:
                actual_winner = 'HOME'
            elif match.away_score > match.home_score:
                actual_winner = 'AWAY'
            else:
                actual_winner = 'DRAW'
            
            # Vérifier si la prédiction est correcte
            is_correct = prediction.predicted_winner == actual_winner
            
            # Mettre à jour la prédiction
            prediction.is_correct_winner = is_correct
            prediction.updated_at = datetime.utcnow()
            
            stats['total_checked'] += 1
            if is_correct:
                stats['correct_predictions'] += 1
            else:
                stats['incorrect_predictions'] += 1
        
        db.session.commit()
        
        # Calculer la précision
        if stats['total_checked'] > 0:
            stats['accuracy'] = round(stats['correct_predictions'] / stats['total_checked'] * 100, 1)
        else:
            stats['accuracy'] = 0
        
        return stats
    
    def get_accuracy_stats(self, days=30):
        """
        Obtenir les statistiques de précision sur une période donnée
        
        Args:
            days: Nombre de jours à analyser
        
        Returns:
            dict: Statistiques de précision
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Récupérer les prédictions avec résultats
        predictions = Prediction.query.join(Match).filter(
            Match.status == 'FINISHED',
            Match.date >= cutoff_date,
            Prediction.is_correct_winner.isnot(None)
        ).all()
        
        total = len(predictions)
        correct = sum(1 for p in predictions if p.is_correct_winner)
        
        # Stats par type de prédiction
        home_wins = [p for p in predictions if p.predicted_winner == 'HOME']
        away_wins = [p for p in predictions if p.predicted_winner == 'AWAY']
        draws = [p for p in predictions if p.predicted_winner == 'DRAW']
        
        return {
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy': round(correct / total * 100, 1) if total > 0 else 0,
            'home_wins': {
                'total': len(home_wins),
                'correct': sum(1 for p in home_wins if p.is_correct_winner),
                'accuracy': round(sum(1 for p in home_wins if p.is_correct_winner) / len(home_wins) * 100, 1) if home_wins else 0
            },
            'away_wins': {
                'total': len(away_wins),
                'correct': sum(1 for p in away_wins if p.is_correct_winner),
                'accuracy': round(sum(1 for p in away_wins if p.is_correct_winner) / len(away_wins) * 100, 1) if away_wins else 0
            },
            'draws': {
                'total': len(draws),
                'correct': sum(1 for p in draws if p.is_correct_winner),
                'accuracy': round(sum(1 for p in draws if p.is_correct_winner) / len(draws) * 100, 1) if draws else 0
            },
            'period_days': days
        }

# Instance globale
prediction_saver = PredictionSaver()
