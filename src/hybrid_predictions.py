"""
Routes API pour les prédictions hybrides (Agent IA + ML)
"""
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
from models.football import db, Match, Team
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from hybrid_predictor import HybridPredictor
from hybrid_cache import HybridCache

hybrid_predictions_bp = Blueprint('hybrid_predictions', __name__)

# Initialiser le prédicteur hybride et le cache
hybrid_predictor = HybridPredictor()
hybrid_cache = HybridCache()

@hybrid_predictions_bp.route('/api/football/top10-hybrid', methods=['GET'])
def get_top10_hybrid():
    """Obtenir le Top 10 avec prédictions hybrides (Agent IA + ML)"""
    try:
        # Obtenir la date d'aujourd'hui et de demain
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        day_after = tomorrow + timedelta(days=1)
        
        # Récupérer les matchs d'aujourd'hui et demain
        matches = Match.query.filter(
            Match.date >= today,
            Match.date < day_after,
            Match.status.in_(['SCHEDULED', 'TIMED'])
        ).order_by(Match.date).all()
        
        # Si moins de 10 matchs, étendre la recherche aux 30 prochains jours
        if len(matches) < 10:
            extended_date = today + timedelta(days=30)
            matches = Match.query.filter(
                Match.date >= today,
                Match.date < extended_date,
                Match.status.in_(['SCHEDULED', 'TIMED'])
            ).order_by(Match.date).limit(50).all()  # Limiter à 50 pour performances
        
        # Générer les prédictions hybrides
        predictions_list = []
        
        for match in matches[:10]:  # Limiter à 10 matchs
            try:
                # Vérifier le cache d'abord
                cached_prediction = hybrid_cache.get_cached_prediction(match.id)
                
                if cached_prediction:
                    hybrid_prediction = cached_prediction
                    print(f"✅ Prédiction depuis le cache pour match {match.id}")
                else:
                    # NE JAMAIS GÉNÉRER EN TEMPS RÉEL (trop lent)
                    # Le cron génère les prédictions en arrière-plan
                    print(f"⚠️  Pas de prédiction en cache pour match {match.id}, skip")
                    continue
                
                # Formater la réponse
                predictions_list.append({
                    'match': {
                        'id': match.id,
                        'home_team': match.home_team.name if match.home_team else 'N/A',
                        'away_team': match.away_team.name if match.away_team else 'N/A',
                        'date': match.date.isoformat() if match.date else None,
                        'league': match.league.name if match.league else 'N/A',
                        'venue': match.venue
                    },
                    'prediction': {
                        'method': 'HYBRID_UNIFIED',
                        'predicted_score': hybrid_prediction['predicted_score'],
                        'expected_goals': hybrid_prediction['expected_goals'],
                        'win_probability_home': hybrid_prediction['win_probability_home'],
                        'win_probability_away': hybrid_prediction['win_probability_away'],
                        'draw_probability': hybrid_prediction['draw_probability'],
                        'btts_probability': hybrid_prediction['btts_probability'],
                        'confidence': hybrid_prediction['confidence'],
                        'confidence_icon': hybrid_prediction['confidence_icon'],
                        'convergence': hybrid_prediction['convergence'],
                        'reasoning': hybrid_prediction['reasoning'],
                        'probable_scorers': hybrid_prediction.get('probable_scorers')
                    }
                })
                
            except Exception as e:
                print(f"❌ Erreur lors de la prédiction pour le match {match.id}: {e}")
                continue
        
        return jsonify({
            'count': len(predictions_list),
            'predictions': predictions_list,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Erreur dans get_top10_hybrid: {e}")
        return jsonify({'error': str(e)}), 500


def prepare_match_data(match):
    """Prépare les données d'un match pour le prédicteur hybride"""
    
    # Récupérer les statistiques des équipes
    home_team_id = match.home_team_id
    away_team_id = match.away_team_id
    
    # Stats équipe domicile (derniers 10 matchs)
    home_matches = Match.query.filter(
        ((Match.home_team_id == home_team_id) | (Match.away_team_id == home_team_id)),
        Match.status == 'FINISHED',
        Match.date > datetime.now() - timedelta(days=60)
    ).order_by(Match.date.desc()).limit(10).all()
    
    # Stats équipe extérieure
    away_matches = Match.query.filter(
        ((Match.home_team_id == away_team_id) | (Match.away_team_id == away_team_id)),
        Match.status == 'FINISHED',
        Match.date > datetime.now() - timedelta(days=60)
    ).order_by(Match.date.desc()).limit(10).all()
    
    # Calculer les moyennes
    home_goals_avg = calculate_goals_avg(home_matches, home_team_id, 'scored')
    home_conceded_avg = calculate_goals_avg(home_matches, home_team_id, 'conceded')
    away_goals_avg = calculate_goals_avg(away_matches, away_team_id, 'scored')
    away_conceded_avg = calculate_goals_avg(away_matches, away_team_id, 'conceded')
    
    # Forme récente (derniers 5 matchs)
    home_form = calculate_form(home_matches[:5], home_team_id)
    away_form = calculate_form(away_matches[:5], away_team_id)
    
    return {
        'home_team': match.home_team.name if match.home_team else 'N/A',
        'away_team': match.away_team.name if match.away_team else 'N/A',
        'home_team_id': home_team_id,
        'away_team_id': away_team_id,
        'home_external_id': match.home_team.external_id if match.home_team else None,
        'away_external_id': match.away_team.external_id if match.away_team else None,
        'home_form': home_form or 'N/A',
        'away_form': away_form or 'N/A',
        'home_goals_avg': home_goals_avg,
        'away_goals_avg': away_goals_avg,
        'home_conceded_avg': home_conceded_avg,
        'away_conceded_avg': away_conceded_avg,
        'h2h_history': 'Historique H2H non disponible'
    }


def calculate_goals_avg(matches, team_id, stat_type):
    """Calcule la moyenne de buts marqués ou encaissés"""
    if not matches:
        return 1.5
    
    total = 0
    for match in matches:
        if stat_type == 'scored':
            if match.home_team_id == team_id:
                total += match.home_score if match.home_score is not None else 0
            else:
                total += match.away_score if match.away_score is not None else 0
        else:  # conceded
            if match.home_team_id == team_id:
                total += match.away_score if match.away_score is not None else 0
            else:
                total += match.home_score if match.home_score is not None else 0
    
    return round(total / len(matches), 1)


def calculate_form(matches, team_id):
    """Calcule la forme récente (V/N/D)"""
    if not matches:
        return ''
    
    form = ''
    for match in matches:
        if match.home_score is None or match.away_score is None:
            continue
            
        if match.home_team_id == team_id:
            if match.home_score > match.away_score:
                form += 'V'
            elif match.home_score < match.away_score:
                form += 'D'
            else:
                form += 'N'
        else:
            if match.away_score > match.home_score:
                form += 'V'
            elif match.away_score < match.home_score:
                form += 'D'
            else:
                form += 'N'
    
    return form

