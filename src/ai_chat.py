"""
Routes API pour le chat avec l'IA de prédictions
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from src.models.football import db, Match, League, Team, Prediction
import os
import json

ai_chat_bp = Blueprint("ai_chat", __name__)

# Clé API OpenAI (déjà configurée dans l'environnement)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def get_context_for_ai():
    """Récupérer le contexte actuel pour l'IA"""
    
    # Statistiques générales
    total_matches = Match.query.count()
    finished_matches = Match.query.filter_by(status='FINISHED').count()
    upcoming_matches = Match.query.filter(Match.status.in_(['SCHEDULED', 'TIMED'])).count()
    
    # Précision récente
    recent_finished = Match.query.filter(
        Match.status == 'FINISHED',
        Match.home_score.isnot(None),
        Match.away_score.isnot(None)
    ).order_by(Match.date.desc()).limit(20).all()
    
    correct_predictions = 0
    total_with_predictions = 0
    
    for match in recent_finished:
        if match.prediction:
            total_with_predictions += 1
            if match.home_score > match.away_score:
                actual = 'home'
            elif match.away_score > match.home_score:
                actual = 'away'
            else:
                actual = 'draw'
            
            if match.prediction.predicted_winner == actual:
                correct_predictions += 1
    
    accuracy = (correct_predictions / total_with_predictions * 100) if total_with_predictions > 0 else 0
    
    # Ligues disponibles
    leagues = League.query.all()
    league_names = [l.name for l in leagues]
    
    context = {
        'total_matches': total_matches,
        'finished_matches': finished_matches,
        'upcoming_matches': upcoming_matches,
        'recent_accuracy': round(accuracy, 2),
        'leagues': league_names,
        'model': 'Machine Learning (Random Forest)',
        'features': [
            'Statistiques historiques des équipes',
            'Forme récente (5 derniers matchs)',
            'Confrontations directes',
            'Performance domicile/extérieur',
            'Buts marqués/encaissés'
        ]
    }
    
    return context

def get_match_details(match_query):
    """Rechercher des matchs selon une requête"""
    
    # Rechercher par nom d'équipe
    matches = Match.query.join(Match.home_team).join(Match.away_team).filter(
        (Team.name.ilike(f'%{match_query}%')) | 
        (Team.name.ilike(f'%{match_query}%'))
    ).filter(Match.status.in_(['SCHEDULED', 'TIMED'])).limit(5).all()
    
    results = []
    for match in matches:
        if match.prediction:
            results.append({
                'home_team': match.home_team.name,
                'away_team': match.away_team.name,
                'date': match.date.strftime('%Y-%m-%d %H:%M'),
                'league': match.league.name,
                'prediction': {
                    'winner': match.prediction.predicted_winner,
                    'confidence': match.prediction.confidence,
                    'prob_home': round(match.prediction.prob_home_win * 100, 1),
                    'prob_draw': round(match.prediction.prob_draw * 100, 1),
                    'prob_away': round(match.prediction.prob_away_win * 100, 1),
                    'reliability': match.prediction.reliability_score
                }
            })
    
    return results

@ai_chat_bp.route("/chat", methods=["POST"])
def chat_with_ai():
    """Converser avec l'IA de prédictions"""
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message vide'}), 400
    
    # Obtenir le contexte
    context = get_context_for_ai()
    
    # Détecter l'intention de l'utilisateur
    user_message_lower = user_message.lower()
    
    # Réponses basées sur les intentions
    if any(word in user_message_lower for word in ['bonjour', 'salut', 'hello', 'hi']):
        response = f"Bonjour ! Je suis l'IA de prédictions de matchs de football. J'analyse actuellement {context['upcoming_matches']} matchs à venir dans {len(context['leagues'])} ligues différentes. Ma précision récente est de {context['recent_accuracy']}%. Comment puis-je vous aider ?"
    
    elif any(word in user_message_lower for word in ['précision', 'fiable', 'accuracy', 'performance']):
        response = f"Ma précision actuelle sur les 20 derniers matchs analysés est de {context['recent_accuracy']}%. J'utilise un modèle de Machine Learning (Random Forest) qui prend en compte plusieurs facteurs : les statistiques historiques, la forme récente des équipes, les confrontations directes, et la performance à domicile/extérieur. J'ai analysé {context['finished_matches']} matchs terminés pour améliorer mes prédictions."
    
    elif any(word in user_message_lower for word in ['comment', 'fonctionnement', 'marche', 'algorithme']):
        response = f"Je fonctionne grâce à un modèle de Machine Learning de type Random Forest. J'analyse plusieurs facteurs clés :\n\n" + "\n".join([f"• {feature}" for feature in context['features']]) + f"\n\nJ'ai été entraîné sur {context['finished_matches']} matchs historiques et je continue d'apprendre de chaque nouveau résultat pour améliorer mes prédictions."
    
    elif any(word in user_message_lower for word in ['ligue', 'championnat', 'compétition']):
        response = f"Je couvre actuellement {len(context['leagues'])} compétitions majeures :\n\n" + "\n".join([f"• {league}" for league in context['leagues']]) + f"\n\nJe peux vous donner des prédictions pour n'importe quel match de ces championnats."
    
    elif any(word in user_message_lower for word in ['match', 'pronostic', 'prédiction', 'prediction']):
        # Essayer de trouver des matchs mentionnés
        words = user_message_lower.split()
        potential_teams = [w for w in words if len(w) > 3]
        
        if potential_teams:
            matches = get_match_details(potential_teams[0])
            if matches:
                response = "Voici les matchs à venir que j'ai trouvés :\n\n"
                for m in matches:
                    pred = m['prediction']
                    winner_text = {
                        'home': f"Victoire de {m['home_team']}",
                        'away': f"Victoire de {m['away_team']}",
                        'draw': "Match nul"
                    }.get(pred['winner'], 'Incertain')
                    
                    response += f"**{m['home_team']} vs {m['away_team']}**\n"
                    response += f"📅 {m['date']} - {m['league']}\n"
                    response += f"🎯 Prédiction : {winner_text}\n"
                    response += f"📊 Probabilités : {pred['prob_home']}% / {pred['prob_draw']}% / {pred['prob_away']}%\n"
                    response += f"⭐ Confiance : {pred['confidence']} (Score : {pred['reliability']}/10)\n\n"
            else:
                response = f"Je n'ai pas trouvé de matchs à venir correspondant à votre recherche. Vous pouvez me demander des informations sur les matchs de : {', '.join(context['leagues'][:5])}..."
        else:
            response = f"J'ai actuellement {context['upcoming_matches']} matchs à venir avec des prédictions. Pouvez-vous me préciser quelle équipe ou quel championnat vous intéresse ?"
    
    elif any(word in user_message_lower for word in ['aide', 'help', 'que peux-tu', 'what can']):
        response = "Je peux vous aider de plusieurs façons :\n\n" \
                   "• 📊 Vous donner des prédictions sur les matchs à venir\n" \
                   "• 📈 Expliquer comment je fais mes prédictions\n" \
                   "• 🎯 Vous informer sur ma précision actuelle\n" \
                   "• ⚽ Discuter des différentes ligues que je couvre\n" \
                   "• 🔍 Analyser des matchs spécifiques\n\n" \
                   "N'hésitez pas à me poser vos questions !"
    
    elif any(word in user_message_lower for word in ['merci', 'thank', 'super', 'génial', 'parfait']):
        response = "Je vous en prie ! N'hésitez pas si vous avez d'autres questions sur les prédictions de matchs. Bonne chance avec vos pronostics ! ⚽"
    
    else:
        # Réponse par défaut
        response = f"Je suis l'IA de prédictions de matchs de football. J'analyse {context['upcoming_matches']} matchs à venir dans {len(context['leagues'])} ligues. Vous pouvez me demander :\n\n" \
                   "• Des prédictions sur un match ou une équipe\n" \
                   "• Ma précision actuelle\n" \
                   "• Comment je fonctionne\n" \
                   "• Les ligues que je couvre\n\n" \
                   "Comment puis-je vous aider ?"
    
    return jsonify({
        'message': user_message,
        'response': response,
        'timestamp': datetime.now().isoformat(),
        'context': {
            'accuracy': context['recent_accuracy'],
            'upcoming_matches': context['upcoming_matches']
        }
    })

@ai_chat_bp.route("/suggestions", methods=["GET"])
def get_suggestions():
    """Obtenir des suggestions de questions pour l'utilisateur"""
    
    suggestions = [
        "Quelle est ta précision actuelle ?",
        "Comment fais-tu tes prédictions ?",
        "Quelles ligues couvres-tu ?",
        "Montre-moi les matchs de Premier League",
        "Donne-moi tes meilleurs pronostics",
        "Parle-moi du match PSG",
        "Quelle est ta fiabilité ?"
    ]
    
    return jsonify({'suggestions': suggestions})

