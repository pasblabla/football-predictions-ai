"""
Route d'historique utilisant les prédictions hybrides (Agent IA + ML)
"""
from flask import Blueprint, jsonify, request
import sqlite3
import json

history_hybrid_bp = Blueprint('history_hybrid', __name__)

DB_PATH = '/home/ubuntu/football-api-deploy/server/database/app.db'

@history_hybrid_bp.route('/matches/finished/hybrid', methods=['GET'])
def get_finished_matches_hybrid():
    """Récupère les matchs terminés avec leurs prédictions HYBRIDES"""
    try:
        per_page = int(request.args.get('per_page', 20))
        page = int(request.args.get('page', 1))
        offset = (page - 1) * per_page
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Récupérer les matchs terminés avec leurs prédictions HYBRIDES
        cursor.execute("""
            SELECT 
                m.id, m.date, m.status, m.home_score, m.away_score,
                ht.name as home_team_name, at.name as away_team_name,
                l.name as league_name,
                hpc.prediction_data
            FROM match m
            LEFT JOIN team ht ON m.home_team_id = ht.id
            LEFT JOIN team at ON m.away_team_id = at.id
            LEFT JOIN league l ON m.league_id = l.id
            LEFT JOIN hybrid_predictions_cache hpc ON m.id = hpc.match_id
            WHERE m.home_score IS NOT NULL AND m.away_score IS NOT NULL
            ORDER BY m.date DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        
        matches = []
        for row in cursor.fetchall():
            # Déterminer le gagnant réel
            if row['home_score'] > row['away_score']:
                actual_winner = 'home'
            elif row['away_score'] > row['home_score']:
                actual_winner = 'away'
            else:
                actual_winner = 'draw'
            
            # Parser les données de prédiction hybride
            prediction_data = None
            predicted_winner = None
            is_correct = None
            
            if row['prediction_data']:
                try:
                    pred = json.loads(row['prediction_data'])
                    prediction_data = pred
                    
                    # Extraire le score prédit
                    predicted_score = pred.get('predicted_score', '').split('-')
                    if len(predicted_score) == 2:
                        pred_home = int(predicted_score[0])
                        pred_away = int(predicted_score[1])
                        
                        if pred_home > pred_away:
                            predicted_winner = 'home'
                        elif pred_away > pred_home:
                            predicted_winner = 'away'
                        else:
                            predicted_winner = 'draw'
                        
                        is_correct = (predicted_winner == actual_winner)
                except:
                    pass
            
            match_data = {
                'id': row['id'],
                'date': row['date'],
                'home_team': {'name': row['home_team_name']},
                'away_team': {'name': row['away_team_name']},
                'league': {'name': row['league_name']},
                'home_score': row['home_score'],
                'away_score': row['away_score'],
                'prediction_analysis': {
                    'predicted_winner': predicted_winner,
                    'actual_winner': actual_winner,
                    'is_correct': is_correct,
                    'hybrid_data': prediction_data
                } if prediction_data else None
            }
            matches.append(match_data)
        
        # Compter le total
        cursor.execute("SELECT COUNT(*) FROM match WHERE home_score IS NOT NULL")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'matches': matches,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'has_next': offset + per_page < total,
                'has_prev': page > 1
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@history_hybrid_bp.route('/stats/accuracy/hybrid', methods=['GET'])
def get_accuracy_stats_hybrid():
    """Calcule les statistiques de précision du système HYBRIDE"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = cursor.cursor()
        
        # Compter les prédictions hybrides correctes
        cursor.execute("""
            SELECT 
                m.id, m.home_score, m.away_score, hpc.prediction_data
            FROM match m
            JOIN hybrid_predictions_cache hpc ON m.id = hpc.match_id
            WHERE m.home_score IS NOT NULL
        """)
        
        total = 0
        correct = 0
        
        for row in cursor.fetchall():
            total += 1
            
            # Déterminer le gagnant réel
            if row[1] > row[2]:
                actual_winner = 'home'
            elif row[2] > row[1]:
                actual_winner = 'away'
            else:
                actual_winner = 'draw'
            
            # Parser la prédiction
            try:
                pred = json.loads(row[3])
                predicted_score = pred.get('predicted_score', '').split('-')
                
                if len(predicted_score) == 2:
                    pred_home = int(predicted_score[0])
                    pred_away = int(predicted_score[1])
                    
                    if pred_home > pred_away:
                        predicted_winner = 'home'
                    elif pred_away > pred_home:
                        predicted_winner = 'away'
                    else:
                        predicted_winner = 'draw'
                    
                    if predicted_winner == actual_winner:
                        correct += 1
            except:
                pass
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        conn.close()
        
        return jsonify({
            'total_matches': total,
            'correct_predictions': correct,
            'accuracy_percentage': round(accuracy, 2)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
