"""
Routes API pour l'historique des matchs terminés
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from src.models.football import db, Match, Prediction
from sqlalchemy import desc

history_bp = Blueprint("history", __name__)

@history_bp.route("/matches/finished", methods=["GET"])
def get_finished_matches():
    """Obtenir l'historique des matchs terminés avec leurs prédictions"""
    
    # Paramètres de pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    league_id = request.args.get("league_id", type=int)
    
    # Construire la requête
    query = Match.query.filter(Match.status == 'FINISHED')
    
    if league_id:
        query = query.filter(Match.league_id == league_id)
    
    # Trier par date décroissante (plus récents en premier)
    query = query.order_by(desc(Match.date))
    
    # Paginer
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    matches = pagination.items
    
    # Calculer les statistiques pour chaque match
    matches_with_stats = []
    for match in matches:
        match_dict = match.to_dict()
        
        if match.predictions and match.home_score is not None and match.away_score is not None:
            pred = match.predictions
            
            # Déterminer le résultat réel
            if match.home_score > match.away_score:
                actual_result = 'home'
            elif match.away_score > match.home_score:
                actual_result = 'away'
            else:
                actual_result = 'draw'
            
            # Vérifier si la prédiction était correcte
            prediction_correct = (pred.predicted_winner == actual_result)
            
            # Ajouter les statistiques de prédiction
            match_dict['prediction_analysis'] = {
                'predicted_winner': pred.predicted_winner,
                'actual_winner': actual_result,
                'is_correct': prediction_correct,
                'confidence': pred.confidence,
                'reliability_score': pred.reliability_score,
                'prob_home_win': pred.prob_home_win,
                'prob_draw': pred.prob_draw,
                'prob_away_win': pred.prob_away_win,
                'predicted_score_home': pred.predicted_score_home,
                'predicted_score_away': pred.predicted_score_away
            }
        
        matches_with_stats.append(match_dict)
    
    return jsonify({
        'matches': matches_with_stats,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })

@history_bp.route("/stats/accuracy", methods=["GET"])
def get_prediction_accuracy():
    """Obtenir les statistiques de précision des prédictions"""
    
    # Paramètres optionnels
    league_id = request.args.get("league_id", type=int)
    days = request.args.get("days", 30, type=int)
    
    # Date limite
    date_limit = datetime.now() - timedelta(days=days)
    
    # Construire la requête
    query = Match.query.filter(
        Match.status == 'FINISHED',
        Match.date >= date_limit,
        Match.home_score.isnot(None),
        Match.away_score.isnot(None)
    )
    
    if league_id:
        query = query.filter(Match.league_id == league_id)
    
    matches = query.all()
    
    # Calculer les statistiques
    total_matches = len(matches)
    correct_predictions = 0
    total_with_predictions = 0
    
    accuracy_by_confidence = {
        'Élevée': {'correct': 0, 'total': 0},
        'Moyenne': {'correct': 0, 'total': 0},
        'Faible': {'correct': 0, 'total': 0}
    }
    
    for match in matches:
        if match.predictions:
            total_with_predictions += 1
            
            # Déterminer le résultat réel
            if match.home_score > match.away_score:
                actual_result = 'home'
            elif match.away_score > match.home_score:
                actual_result = 'away'
            else:
                actual_result = 'draw'
            
            # Vérifier si la prédiction était correcte
            if match.predictions.predicted_winner == actual_result:
                correct_predictions += 1
                
                # Par niveau de confiance
                confidence = match.predictions.confidence
                if confidence in accuracy_by_confidence:
                    accuracy_by_confidence[confidence]['correct'] += 1
            
            # Compter le total par confiance
            confidence = match.predictions.confidence
            if confidence in accuracy_by_confidence:
                accuracy_by_confidence[confidence]['total'] += 1
    
    # Calculer les pourcentages
    overall_accuracy = (correct_predictions / total_with_predictions * 100) if total_with_predictions > 0 else 0
    
    accuracy_percentages = {}
    for level, stats in accuracy_by_confidence.items():
        if stats['total'] > 0:
            accuracy_percentages[level] = {
                'accuracy': stats['correct'] / stats['total'] * 100,
                'correct': stats['correct'],
                'total': stats['total']
            }
        else:
            accuracy_percentages[level] = {
                'accuracy': 0,
                'correct': 0,
                'total': 0
            }
    
    return jsonify({
        'period_days': days,
        'total_matches': total_matches,
        'matches_with_predictions': total_with_predictions,
        'correct_predictions': correct_predictions,
        'overall_accuracy': round(overall_accuracy, 2),
        'accuracy_by_confidence': accuracy_percentages
    })

@history_bp.route("/stats/recent", methods=["GET"])
def get_recent_stats():
    """Obtenir les statistiques récentes (derniers 10 matchs)"""
    
    matches = Match.query.filter(
        Match.status == 'FINISHED',
        Match.home_score.isnot(None),
        Match.away_score.isnot(None)
    ).order_by(desc(Match.date)).limit(10).all()
    
    results = []
    correct_count = 0
    
    for match in matches:
        if match.predictions:
            # Déterminer le résultat réel
            if match.home_score > match.away_score:
                actual_result = 'home'
            elif match.away_score > match.home_score:
                actual_result = 'away'
            else:
                actual_result = 'draw'
            
            is_correct = (match.predictions.predicted_winner == actual_result)
            if is_correct:
                correct_count += 1
            
            results.append({
                'match': f"{match.home_team.name} vs {match.away_team.name}",
                'score': f"{match.home_score}-{match.away_score}",
                'predicted': match.predictions.predicted_winner,
                'actual': actual_result,
                'correct': is_correct,
                'confidence': match.predictions.confidence,
                'date': match.date.isoformat()
            })
    
    accuracy = (correct_count / len(results) * 100) if results else 0
    
    return jsonify({
        'recent_matches': results,
        'accuracy': round(accuracy, 2),
        'correct': correct_count,
        'total': len(results)
    })

