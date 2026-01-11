"""
Routes API pour le chat avec l'IA de prédictions - Version réparée avec API Forge
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from models.football import db, Match, League, Team
import os
import requests

ai_chat_bp = Blueprint("ai_chat", __name__)

# Utiliser l'API Forge fournie par Manus
FORGE_API_KEY = os.getenv('BUILT_IN_FORGE_API_KEY')
FORGE_API_URL = os.getenv('BUILT_IN_FORGE_API_URL', 'https://forge.manus.ai')

def get_context_for_ai():
    """Récupérer le contexte actuel pour l'IA"""
    
    try:
        # Statistiques générales
        total_matches = Match.query.count()
        finished_matches = Match.query.filter_by(status='FINISHED').count()
        upcoming_matches = Match.query.filter(Match.status.in_(['SCHEDULED', 'TIMED'])).count()
        
        # Ligues disponibles
        leagues = League.query.all()
        league_names = [l.name for l in leagues]
        
        # Matchs récents avec prédictions
        recent_matches = Match.query.filter(
            Match.status.in_(['SCHEDULED', 'TIMED'])
        ).order_by(Match.date.asc()).limit(10).all()
        
        upcoming_list = []
        for match in recent_matches:
            upcoming_list.append({
                'home_team': match.home_team.name if match.home_team else 'N/A',
                'away_team': match.away_team.name if match.away_team else 'N/A',
                'date': match.date.strftime('%Y-%m-%d %H:%M') if match.date else 'N/A',
                'league': match.league.name if match.league else 'N/A'
            })
        
        context = {
            'total_matches': total_matches,
            'finished_matches': finished_matches,
            'upcoming_matches': upcoming_matches,
            'leagues': league_names,
            'upcoming_list': upcoming_list
        }
        
        return context
    except Exception as e:
        print(f"Erreur lors de la récupération du contexte: {e}")
        return {
            'total_matches': 0,
            'finished_matches': 0,
            'upcoming_matches': 0,
            'leagues': [],
            'upcoming_list': []
        }

@ai_chat_bp.route("/chat", methods=["POST"])
def chat_with_ai():
    """Converser avec l'IA de prédictions en utilisant GPT-4"""
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message vide'}), 400
        
        # Obtenir le contexte
        context = get_context_for_ai()
        
        # Construire le prompt système
        system_prompt = f"""Tu es un assistant IA spécialisé dans les prédictions de matchs de football.

CONTEXTE ACTUEL:
- {context['total_matches']} matchs dans la base de données
- {context['finished_matches']} matchs terminés
- {context['upcoming_matches']} matchs à venir
- Ligues couvertes: {', '.join(context['leagues'][:5])}

Tu utilises un système hybride qui combine:
1. Agent IA (GPT-4) pour l'analyse contextuelle
2. Machine Learning pour l'apprentissage continu
3. Données réelles de l'API football-data.org

Réponds de manière naturelle, professionnelle et en français. Sois précis et utile."""

        # Ajouter des informations sur les matchs à venir si pertinent
        if context['upcoming_list']:
            system_prompt += f"\n\nPROCHAINS MATCHS:\n"
            for m in context['upcoming_list'][:5]:
                system_prompt += f"- {m['home_team']} vs {m['away_team']} ({m['league']}, {m['date']})\n"
        
        # Appeler l'API Forge (GPT-4)
        response = requests.post(
            f"{FORGE_API_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {FORGE_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            return jsonify({
                'message': user_message,
                'response': ai_response,
                'timestamp': datetime.now().isoformat(),
                'context': {
                    'upcoming_matches': context['upcoming_matches'],
                    'leagues': len(context['leagues'])
                }
            })
        else:
            print(f"Erreur API Forge: {response.status_code}")
            return jsonify({'error': 'Erreur lors de la communication avec l\'IA'}), 500
            
    except Exception as e:
        print(f"Erreur dans chat_with_ai: {e}")
        return jsonify({'error': str(e)}), 500

@ai_chat_bp.route("/suggestions", methods=["GET"])
def get_suggestions():
    """Obtenir des suggestions de questions pour l'utilisateur"""
    
    suggestions = [
        "Quels sont les prochains matchs ?",
        "Comment fonctionne ton système de prédiction ?",
        "Quelle est ta précision ?",
        "Montre-moi les matchs de Premier League",
        "Donne-moi tes meilleurs pronostics",
        "Parle-moi du système hybride",
        "Quelles ligues couvres-tu ?"
    ]
    
    return jsonify({'suggestions': suggestions})

