import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_apscheduler import APScheduler
from src.football_new import football_bp
from src.models.football import db
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configuration
# Utiliser DATABASE_URL pour MySQL en production, ou SQLite en local
# Le format attendu pour MySQL est: mysql+pymysql://user:password@host/dbname
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:////home/ubuntu/football_app/instance/site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-key')

# Configuration APScheduler
app.config['SCHEDULER_API_ENABLED'] = True
app.config['SCHEDULER_TIMEZONE'] = 'Europe/Paris'

# Initialiser la base de données
db.init_app(app)

# Initialiser le scheduler
scheduler = APScheduler()
scheduler.init_app(app)

# Démarrer le scheduler automatiquement (pour gunicorn et autres WSGI servers)
# Utiliser un flag pour éviter le double démarrage
if not scheduler.running:
    scheduler.start()
    logger.info("[SCHEDULER] APScheduler démarré automatiquement")

# Enregistrement du Blueprint principal
app.register_blueprint(football_bp, url_prefix='/api/football')

# ============================================================================
# Routes API supplémentaires (history, ai)
# ============================================================================

@app.route('/api/history/matches/finished')
def get_finished_matches():
    """Obtenir les matchs terminés avec leurs prédictions"""
    from src.models.football import Match, Prediction, Team, League
    from datetime import datetime, timedelta
    
    # Récupérer les matchs terminés des 30 derniers jours
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    finished_matches = Match.query.filter(
        Match.home_score.isnot(None),
        Match.date >= thirty_days_ago
    ).order_by(Match.date.desc()).limit(50).all()
    
    matches_data = []
    for match in finished_matches:
        # Récupérer la prédiction associée
        prediction = Prediction.query.filter_by(match_id=match.id).first()
        
        # Déterminer le résultat réel
        if match.home_score > match.away_score:
            actual_result = 'HOME'
        elif match.away_score > match.home_score:
            actual_result = 'AWAY'
        else:
            actual_result = 'DRAW'
        
        match_info = {
            'id': match.id,
            'date': match.date.isoformat(),
            'home_team': match.home_team.name if match.home_team else 'Unknown',
            'away_team': match.away_team.name if match.away_team else 'Unknown',
            'home_score': match.home_score,
            'away_score': match.away_score,
            'league': match.league.name if match.league else 'Unknown',
            'actual_result': actual_result
        }
        
        if prediction:
            predicted_score = f"{prediction.predicted_score_home or 0}-{prediction.predicted_score_away or 0}"
            match_info['prediction'] = {
                'predicted_winner': prediction.predicted_winner,
                'predicted_score': predicted_score,
                'confidence': prediction.confidence,
                'is_correct': prediction.predicted_winner == actual_result
            }
        else:
            match_info['prediction'] = None
        
        matches_data.append(match_info)
    
    return jsonify({"matches": matches_data})

@app.route('/api/history/stats')
def get_history_stats():
    """Obtenir les statistiques réelles de l'historique"""
    from src.models.football import Match, Prediction
    from datetime import datetime, timedelta
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Récupérer toutes les prédictions avec résultats
    preds = Prediction.query.join(Match).filter(
        Match.home_score.isnot(None),
        Match.date >= thirty_days_ago
    ).all()
    
    total = len(preds)
    correct = 0
    
    # Compteurs par niveau de confiance
    high_conf = {'correct': 0, 'total': 0}
    med_conf = {'correct': 0, 'total': 0}
    low_conf = {'correct': 0, 'total': 0}
    
    for p in preds:
        m = p.match
        if m.home_score is None:
            continue
        
        # Résultat réel
        if m.home_score > m.away_score:
            actual = 'HOME'
        elif m.away_score > m.home_score:
            actual = 'AWAY'
        else:
            actual = 'DRAW'
        
        is_correct = p.predicted_winner == actual
        if is_correct:
            correct += 1
        
        # Par niveau de confiance
        try:
            conf = float(p.confidence) if p.confidence else 50
        except (ValueError, TypeError):
            conf = 50
        if conf >= 70:
            high_conf['total'] += 1
            if is_correct:
                high_conf['correct'] += 1
        elif conf >= 50:
            med_conf['total'] += 1
            if is_correct:
                med_conf['correct'] += 1
        else:
            low_conf['total'] += 1
            if is_correct:
                low_conf['correct'] += 1
    
    overall_accuracy = round(correct / total * 100, 1) if total > 0 else 0
    
    return jsonify({
        "overall_accuracy": overall_accuracy,
        "total_matches": total,
        "correct_predictions": correct,
        "matches_with_predictions": total,
        "period_days": 30,
        "accuracy_by_confidence": {
            "Élevée": {
                "accuracy": round(high_conf['correct'] / high_conf['total'] * 100, 1) if high_conf['total'] > 0 else 0,
                "count": high_conf['total']
            },
            "Moyenne": {
                "accuracy": round(med_conf['correct'] / med_conf['total'] * 100, 1) if med_conf['total'] > 0 else 0,
                "count": med_conf['total']
            },
            "Faible": {
                "accuracy": round(low_conf['correct'] / low_conf['total'] * 100, 1) if low_conf['total'] > 0 else 0,
                "count": low_conf['total']
            }
        }
    })

@app.route('/api/history/learning')
def get_learning_data():
    """Obtenir les données d'apprentissage"""
    return jsonify({
        "learning_progress": 72,
        "total_samples": 1500,
        "model_version": "v2.1"
    })

@app.route('/api/ai/suggestions')
def get_ai_suggestions():
    """Obtenir les suggestions de l'IA"""
    return jsonify([
        "Quelle est la précision de l'IA ?",
        "Quels sont les matchs les plus fiables ?",
        "Comment fonctionne le système de prédiction ?"
    ])

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Chat avec l'IA"""
    return jsonify({
        "response": "Je suis l'IA de prédictions de matchs de football. Comment puis-je vous aider ?"
    })

# ============================================================================
# Route de partage de prédiction
# ============================================================================

@app.route('/share/<match_id>')
def share_prediction(match_id):
    """Page de partage d'une prédiction spécifique"""
    return send_from_directory(app.static_folder, 'share.html')

@app.route('/api/share/<match_id>')
def get_share_prediction(match_id):
    """API pour récupérer les données d'une prédiction à partager"""
    from src.models.football import Match, Prediction, Team, League
    
    try:
        # Chercher le match par ID
        match = Match.query.get(match_id)
        
        if not match:
            return jsonify({'error': 'Match non trouvé'}), 404
        
        # Récupérer la prédiction sauvegardée
        prediction = Prediction.query.filter_by(match_id=match.id).first()
        
        # Récupérer les infos des équipes
        home_team = Team.query.get(match.home_team_id)
        away_team = Team.query.get(match.away_team_id)
        league = League.query.get(match.league_id)
        
        # Construire la réponse
        response = {
            'match': {
                'id': match.id,
                'home_team': home_team.name if home_team else 'Équipe A',
                'away_team': away_team.name if away_team else 'Équipe B',
                'league': league.name if league else 'Ligue',
                'date': match.date.strftime('%d/%m/%Y %H:%M') if match.date else 'N/A',
                'home_score': match.home_score,
                'away_score': match.away_score
            },
            'prediction': None
        }
        
        if prediction:
            response['prediction'] = {
                'predicted_winner': prediction.predicted_winner,
                'predicted_score_home': prediction.predicted_score_home,
                'predicted_score_away': prediction.predicted_score_away,
                'prob_home_win': prediction.prob_home_win,
                'prob_draw': prediction.prob_draw,
                'prob_away_win': prediction.prob_away_win,
                'confidence': prediction.confidence,
                'confidence_level': prediction.confidence_level
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Route de base pour servir l'index.html et les fichiers statiques
# ============================================================================

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# ============================================================================
# Configuration des tâches planifiées avec APScheduler
# ============================================================================

@scheduler.task('cron', id='task_6h', hour=6, minute=0)
def scheduled_task_6h():
    """Tâche à 6h : Générer les prédictions pour les matchs à venir"""
    with app.app_context():
        logger.info("[SCHEDULER] Exécution de la tâche de 6h...")
        try:
            from src.scheduler.tasks import generate_predictions_task
            result = generate_predictions_task()
            logger.info(f"[SCHEDULER] Tâche 6h terminée: {result}")
        except Exception as e:
            logger.error(f"[SCHEDULER] Erreur tâche 6h: {e}")

@scheduler.task('cron', id='task_18h', hour=18, minute=0)
def scheduled_task_18h():
    """Tâche à 18h : Mettre à jour les prédictions et résultats"""
    with app.app_context():
        logger.info("[SCHEDULER] Exécution de la tâche de 18h...")
        try:
            from src.scheduler.tasks import generate_predictions_task, update_results_task
            generate_predictions_task()
            update_results_task()
            logger.info("[SCHEDULER] Tâche 18h terminée")
        except Exception as e:
            logger.error(f"[SCHEDULER] Erreur tâche 18h: {e}")

@scheduler.task('cron', id='task_midnight', hour=0, minute=0)
def scheduled_task_midnight():
    """Tâche à minuit : Mise à jour complète, apprentissage et évolution"""
    with app.app_context():
        logger.info("[SCHEDULER] Exécution de la tâche de minuit...")
        try:
            from src.scheduler.tasks import run_all_tasks
            result = run_all_tasks()
            logger.info(f"[SCHEDULER] Tâche minuit terminée: {result}")
        except Exception as e:
            logger.error(f"[SCHEDULER] Erreur tâche minuit: {e}")

@scheduler.task('cron', id='task_data_fetch', hour='*/4', minute=30)
def scheduled_data_fetch():
    """Tâche toutes les 4 heures : Récupérer les données (API + SoccerStats)"""
    with app.app_context():
        logger.info("[SCHEDULER] Exécution de la récupération de données...")
        try:
            from src.scheduler.tasks import fetch_data_task
            result = fetch_data_task()
            logger.info(f"[SCHEDULER] Récupération terminée: {result}")
        except Exception as e:
            logger.error(f"[SCHEDULER] Erreur récupération: {e}")

# Route pour déclencher manuellement les tâches (utile pour les tests)
@app.route('/api/scheduler/run-now', methods=['POST'])
def run_scheduler_now():
    """Déclencher manuellement toutes les tâches planifiées"""
    try:
        from src.scheduler.tasks import run_all_tasks
        result = run_all_tasks()
        return jsonify({'success': True, 'result': str(result)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler/status')
def scheduler_status():
    """Obtenir le statut du scheduler"""
    jobs = []
    try:
        for job in scheduler.get_jobs():
            job_info = {
                'id': job.id,
                'name': getattr(job, 'name', job.id),
            }
            # Essayer d'obtenir next_run_time (peut varier selon la version)
            if hasattr(job, 'next_run_time'):
                job_info['next_run'] = str(job.next_run_time) if job.next_run_time else None
            # Essayer d'obtenir le trigger
            if hasattr(job, 'trigger'):
                job_info['trigger'] = str(job.trigger)
            jobs.append(job_info)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des jobs: {e}")
    
    return jsonify({
        'running': scheduler.running,
        'jobs': jobs,
        'scheduled_times': ['06:00', '18:00', '00:00']
    })

# ============================================================================
# Démarrage de l'application
# ============================================================================

if __name__ == '__main__':
    # Démarrer le scheduler
    scheduler.start()
    logger.info("[SCHEDULER] APScheduler démarré avec succès")
    
    # Démarrer l'application Flask
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

@app.route('/api/scheduler/fetch-data', methods=['POST'])
def fetch_data_now():
    """Déclencher manuellement la récupération de données"""
    try:
        from src.scheduler.tasks import fetch_data_task
        result = fetch_data_task()
        return jsonify({'success': True, 'result': str(result)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
