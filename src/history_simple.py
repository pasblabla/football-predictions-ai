                actual_winner = 'home'
            elif row['away_score'] > row['home_score']:
                actual_winner = 'away'
            else:
                actual_winner = 'draw'
            
            # Vérifier si la prédiction était correcte
            is_correct = (row['predicted_winner'] == actual_winner) if row['predicted_winner'] else None
            
            match_data = {
                'id': row['id'],
                'date': row['date'],
                'home_team': {'name': row['home_team_name']},
                'away_team': {'name': row['away_team_name']},
                'league': {'name': row['league_name']},
                'home_score': row['home_score'],
                'away_score': row['away_score'],
                'referee': {
                    'name': row['referee_name'],
                    'nationality': row['referee_nationality'],
                    'total_matches': row['referee_total_matches']
                } if row['referee_name'] else None,
                'prediction_analysis': {
                    'predicted_winner': row['predicted_winner'],
                    'predicted_score_home': row['predicted_score_home'],
                    'predicted_score_away': row['predicted_score_away'],
                    'actual_winner': actual_winner,
                    'is_correct': is_correct,
                    'confidence': row['confidence'],
                    'reliability_score': row['reliability_score'],
                    'prob_home_win': round(row['prob_home_win'] * 100) if row['prob_home_win'] else None,
                    'prob_draw': round(row['prob_draw'] * 100) if row['prob_draw'] else None,
                    'prob_away_win': round(row['prob_away_win'] * 100) if row['prob_away_win'] else None,
                    'prob_btts': round(row['prob_both_teams_score'] * 100) if row['prob_both_teams_score'] else None,
                    'prob_over_25': round(row['prob_over_2_5'] * 100) if row['prob_over_2_5'] else None,
                }
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


@history_simple_bp.route('/stats/accuracy', methods=['GET'])
def get_accuracy_stats():
    """Calcule les statistiques de précision de l'IA"""
    try:
        days = int(request.args.get('days', 30))
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Compter les prédictions correctes
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE 
                    WHEN (m.home_score > m.away_score AND p.predicted_winner = 'home') OR
                         (m.away_score > m.home_score AND p.predicted_winner = 'away') OR
                         (m.home_score = m.away_score AND p.predicted_winner = 'draw')
                    THEN 1 ELSE 0 END) as correct
            FROM match m
            JOIN prediction p ON m.id = p.match_id
            WHERE m.home_score IS NOT NULL
        """)
        
        row = cursor.fetchone()
        total = row[0]
        correct = row[1]
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        conn.close()
        
        return jsonify({
            'total_matches': total,
            'correct_predictions': correct,
            'accuracy_percentage': round(accuracy, 2),
            'period_days': days
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500




@history_simple_bp.route('/stats', methods=['GET'])
def get_stats():
    """Récupère toutes les statistiques de l'historique"""
    try:
        days = int(request.args.get('days', 30))
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Statistiques globales
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE 
                    WHEN (m.home_score > m.away_score AND p.predicted_winner = 'home') OR
                         (m.away_score > m.home_score AND p.predicted_winner = 'away') OR
                         (m.home_score = m.away_score AND p.predicted_winner = 'draw')
                    THEN 1 ELSE 0 END) as correct
            FROM match m
            JOIN prediction p ON m.id = p.match_id
            WHERE m.home_score IS NOT NULL
        """)
        
        row = cursor.fetchone()
        total = row[0] if row else 0
        correct = row[1] if row else 0
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Statistiques par niveau de confiance
        accuracy_by_confidence = {}
        for confidence in ['Élevée', 'Moyenne', 'Faible']:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE 
                        WHEN (m.home_score > m.away_score AND p.predicted_winner = 'home') OR
                             (m.away_score > m.home_score AND p.predicted_winner = 'away') OR
                             (m.home_score = m.away_score AND p.predicted_winner = 'draw')
                        THEN 1 ELSE 0 END) as correct
                FROM match m
                JOIN prediction p ON m.id = p.match_id
                WHERE m.home_score IS NOT NULL AND p.confidence = ?
            """, (confidence,))
            
            row = cursor.fetchone()
            conf_total = row[0] if row else 0
            conf_correct = row[1] if row else 0
            conf_accuracy = (conf_correct / conf_total * 100) if conf_total > 0 else 0
            
            accuracy_by_confidence[confidence] = {
                'total': conf_total,
                'correct': conf_correct,
                'accuracy': round(conf_accuracy, 2)
            }
        
        conn.close()
        
        return jsonify({
            'total_matches': total,
            'correct_predictions': correct,
            'accuracy_percentage': round(accuracy, 2),
            'period_days': days,
            'accuracy_by_confidence': accuracy_by_confidence
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500




@history_simple_bp.route('/learning', methods=['GET'])
def get_learning_data():
    """Récupère les données d'apprentissage automatique de l'IA"""
    try:
        import json
        import os
        
        learning_file = '/home/ubuntu/football-api-deploy/server/data/ai_learning.json'
        
        if not os.path.exists(learning_file):
            return jsonify({'error': 'Données d\'apprentissage non disponibles'}), 404
        
        with open(learning_file, 'r', encoding='utf-8') as f:
            learning_data = json.load(f)
        
        return jsonify(learning_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

