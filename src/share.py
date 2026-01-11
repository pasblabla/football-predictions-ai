"""
Routes pour le partage de prédictions
"""
from flask import Blueprint, jsonify, request, render_template_string
from models.football import Match, Team, League
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from hybrid_cache import HybridCache

share_bp = Blueprint('share', __name__)
hybrid_cache = HybridCache()

@share_bp.route('/api/share/prediction/<int:match_id>', methods=['GET'])
def get_shared_prediction(match_id):
    """Obtenir une prédiction pour le partage"""
    try:
        # Récupérer le match
        match = Match.query.get_or_404(match_id)
        
        # Récupérer la prédiction hybride depuis le cache
        cached_prediction = hybrid_cache.get_cached_prediction(match_id)
        
        if not cached_prediction:
            return jsonify({
                'error': 'Prédiction non disponible pour ce match'
            }), 404
        
        # Formater la réponse
        return jsonify({
            'match': {
                'id': match.id,
                'home_team': match.home_team.name,
                'away_team': match.away_team.name,
                'date': match.date.isoformat(),
                'league': match.league.name,
                'venue': match.venue
            },
            'prediction': cached_prediction,
            'share_url': f"{request.host_url}share/{match_id}"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@share_bp.route('/share/<int:match_id>', methods=['GET'])
def share_prediction_page(match_id):
    """Page de prévisualisation d'une prédiction partagée"""
    try:
        # Récupérer le match
        match = Match.query.get_or_404(match_id)
        
        # Récupérer la prédiction hybride
        cached_prediction = hybrid_cache.get_cached_prediction(match_id)
        
        if not cached_prediction:
            return "Prédiction non disponible", 404
        
        # Template HTML avec Open Graph
        html_template = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ home_team }} vs {{ away_team }} - Prédiction IA</title>
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{{ share_url }}">
    <meta property="og:title" content="{{ home_team }} vs {{ away_team }} - Prédiction IA">
    <meta property="og:description" content="Score prédit: {{ predicted_score }} | Victoire {{ home_team }}: {{ win_prob_home }}% | Nul: {{ draw_prob }}% | Victoire {{ away_team }}: {{ win_prob_away }}% | Confiance: {{ confidence }}">
    <meta property="og:image" content="{{ request.host_url }}static/og-image.png">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="{{ share_url }}">
    <meta property="twitter:title" content="{{ home_team }} vs {{ away_team }} - Prédiction IA">
    <meta property="twitter:description" content="Score prédit: {{ predicted_score }} | {{ home_team }} {{ win_prob_home }}% vs {{ away_team }} {{ win_prob_away }}% | Confiance: {{ confidence }}">
    <meta property="twitter:image" content="{{ request.host_url }}static/og-image.png">
    
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .prediction-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            padding: 40px;
        }
        .team-name {
            font-size: 24px;
            font-weight: bold;
            color: #1a202c;
        }
        .score-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 32px;
            font-weight: bold;
            padding: 20px 40px;
            border-radius: 15px;
            display: inline-block;
        }
        .confidence-badge {
            background: #48bb78;
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: bold;
        }
        .reasoning-box {
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }

    </style>
</head>
<body>
    <div class="prediction-card">
        <div class="text-center mb-6">
            <h1 class="text-3xl font-bold text-gray-800 mb-2">⚽ Prédiction IA</h1>
            <p class="text-gray-600">{{ league }}</p>
        </div>
        
        <div class="flex items-center justify-between mb-6">
            <div class="team-name text-center flex-1">{{ home_team }}</div>
            <div class="px-4">
                <div class="score-badge">{{ predicted_score }}</div>
            </div>
            <div class="team-name text-center flex-1">{{ away_team }}</div>
        </div>
        
        <div class="text-center mb-4">
            <span class="confidence-badge">{{ confidence_icon }} Confiance: {{ confidence }}</span>
        </div>
        
        <div class="grid grid-cols-3 gap-4 mb-4">
            <div class="text-center p-4 bg-green-50 rounded-lg border-2 border-green-200">
                <div class="text-sm text-gray-600 mb-1">Victoire {{ home_team }}</div>
                <div class="text-3xl font-bold text-green-600">{{ win_prob_home }}%</div>
            </div>
            <div class="text-center p-4 bg-gray-50 rounded-lg border-2 border-gray-200">
                <div class="text-sm text-gray-600 mb-1">Match Nul</div>
                <div class="text-3xl font-bold text-gray-600">{{ draw_prob }}%</div>
            </div>
            <div class="text-center p-4 bg-blue-50 rounded-lg border-2 border-blue-200">
                <div class="text-sm text-gray-600 mb-1">Victoire {{ away_team }}</div>
                <div class="text-3xl font-bold text-blue-600">{{ win_prob_away }}%</div>
            </div>
        </div>
        
        <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="text-center p-3 bg-purple-50 rounded-lg">
                <div class="text-xs text-gray-600">Buts attendus</div>
                <div class="text-xl font-bold text-purple-600">{{ expected_goals }} buts</div>
            </div>
            <div class="text-center p-3 bg-orange-50 rounded-lg">
                <div class="text-xs text-gray-600">Les deux marquent</div>
                <div class="text-xl font-bold text-orange-600">{{ btts_prob }}%</div>
            </div>
        </div>
        
        <div class="reasoning-box">
            <div class="text-sm font-semibold text-purple-800 mb-2">💡 Analyse de l'IA:</div>
            <div class="text-sm text-gray-700">{{ reasoning }}</div>
        </div>
        
        <div class="text-center mt-6 text-sm text-gray-500">
            Système Hybride Unifié (Agent IA + ML)
        </div>
    </div>
</body>
</html>
        """
        
        # Préparer les données pour le template
        reasoning_short = cached_prediction['reasoning'][:100] + "..." if len(cached_prediction['reasoning']) > 100 else cached_prediction['reasoning']
        
        return render_template_string(
            html_template,
            home_team=match.home_team.name,
            away_team=match.away_team.name,
            league=match.league.name,
            predicted_score=cached_prediction['predicted_score'],
            confidence=cached_prediction['confidence'],
            confidence_icon=cached_prediction['confidence_icon'],
            win_prob_home=cached_prediction['win_probability_home'],
            draw_prob=cached_prediction['draw_probability'],
            win_prob_away=cached_prediction['win_probability_away'],
            expected_goals=cached_prediction.get('expected_goals', 2.5),
            btts_prob=cached_prediction.get('btts_probability', 50),
            reasoning=cached_prediction['reasoning'],
            reasoning_short=reasoning_short,
            share_url=f"{request.host_url}share/{match_id}",
            request=request
        )
        
    except Exception as e:
        return f"Erreur: {str(e)}", 500

