"""
Route API pour comparer les prédictions Agent IA vs ML Classique
"""
from flask import Blueprint, jsonify, request
import sys
import os

# Ajouter le chemin des scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from ai_agent_predictor import AIAgentPredictor
from ml_predictor_adapter import MLPredictorAdapter
from hybrid_predictor import HybridPredictor
import sqlite3

ai_comparison_bp = Blueprint('ai_comparison', __name__)

# Initialiser les prédicteurs
ai_agent = AIAgentPredictor()
ml_engine = MLPredictorAdapter()
hybrid_predictor = HybridPredictor()

DB_PATH = '/home/ubuntu/football-api-deploy/server/database/app.db'

@ai_comparison_bp.route('/api/ai-comparison/predict/<int:match_id>', methods=['GET'])
def compare_predictions(match_id):
    """
    Compare les prédictions de l'Agent IA et du ML Classique pour un match
    """
    try:
        # Récupérer les informations du match
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                m.*,
                ht.name as home_team,
                at.name as away_team
            FROM match m
            JOIN team ht ON m.home_team_id = ht.id
            JOIN team at ON m.away_team_id = at.id
            WHERE m.id = ?
        """, (match_id,))
        
        match = cursor.fetchone()
        
        if not match:
            return jsonify({'error': 'Match non trouvé'}), 404
        
        match = dict(match)
        
        # Récupérer les statistiques des équipes
        # Stats équipe domicile
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN m.home_team_id = ? THEN m.home_score ELSE m.away_score END) as goals_avg,
                AVG(CASE WHEN m.home_team_id = ? THEN m.away_score ELSE m.home_score END) as conceded_avg
            FROM match m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.status = 'FINISHED'
            AND m.date > datetime('now', '-60 days')
        """, (match['home_team_id'], match['home_team_id'], match['home_team_id'], match['home_team_id']))
        
        home_stats = cursor.fetchone()
        
        # Stats équipe extérieure
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN m.home_team_id = ? THEN m.home_score ELSE m.away_score END) as goals_avg,
                AVG(CASE WHEN m.home_team_id = ? THEN m.away_score ELSE m.home_score END) as conceded_avg
            FROM match m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.status = 'FINISHED'
            AND m.date > datetime('now', '-60 days')
        """, (match['away_team_id'], match['away_team_id'], match['away_team_id'], match['away_team_id']))
        
        away_stats = cursor.fetchone()
        
        # Forme récente
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN m.home_team_id = ? AND m.home_score > m.away_score THEN 'V'
                    WHEN m.away_team_id = ? AND m.away_score > m.home_score THEN 'V'
                    WHEN m.home_score = m.away_score THEN 'N'
                    ELSE 'D'
                END as result
            FROM match m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.status = 'FINISHED'
            ORDER BY m.date DESC
            LIMIT 5
        """, (match['home_team_id'], match['home_team_id'], match['home_team_id'], match['home_team_id']))
        
        home_form = ''.join([row[0] for row in cursor.fetchall()])
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN m.home_team_id = ? AND m.home_score > m.away_score THEN 'V'
                    WHEN m.away_team_id = ? AND m.away_score > m.home_score THEN 'V'
                    WHEN m.home_score = m.away_score THEN 'N'
                    ELSE 'D'
                END as result
            FROM match m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.status = 'FINISHED'
            ORDER BY m.date DESC
            LIMIT 5
        """, (match['away_team_id'], match['away_team_id'], match['away_team_id'], match['away_team_id']))
        
        away_form = ''.join([row[0] for row in cursor.fetchall()])
        
        conn.close()
        
        # Préparer les données pour les prédicteurs
        match_data = {
            'home_team': match['home_team'],
            'away_team': match['away_team'],
            'home_form': home_form or 'N/A',
            'away_form': away_form or 'N/A',
            'home_goals_avg': home_stats[0] if home_stats[0] else 1.5,
            'away_goals_avg': away_stats[0] if away_stats[0] else 1.5,
            'home_conceded_avg': home_stats[1] if home_stats[1] else 1.5,
            'away_conceded_avg': away_stats[1] if away_stats[1] else 1.5,
            'h2h_history': 'Historique H2H non disponible'
        }
        
        # Obtenir la prédiction hybride unifiée
        hybrid_prediction = hybrid_predictor.predict(match_data)
        
        return jsonify({
            'match': {
                'id': match['id'],
                'home_team': match['home_team'],
                'away_team': match['away_team'],
                'date': match['date'],
                'status': match['status']
            },
            'prediction': hybrid_prediction
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_comparison_bp.route('/api/ai-comparison/batch', methods=['GET'])
def batch_comparison():
    """
    Compare les prédictions pour plusieurs matchs à venir
    """
    try:
        limit = request.args.get('limit', 5, type=int)
        
        # Récupérer les prochains matchs
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                m.id,
                m.date,
                ht.name as home_team,
                at.name as away_team
            FROM match m
            JOIN team ht ON m.home_team_id = ht.id
            JOIN team at ON m.away_team_id = at.id
            WHERE m.status IN ('SCHEDULED', 'TIMED') 
            AND m.date > datetime('now')
            ORDER BY m.date ASC
            LIMIT ?
        """, (limit,))
        
        matches = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'count': len(matches),
            'matches': matches
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

