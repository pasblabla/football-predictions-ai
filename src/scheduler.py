"""
Scheduler Flask pour automatiser les tâches
Remplace le cron dans l'environnement sandbox
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_predictions_job():
    """Génère les prédictions hybrides"""
    try:
        logger.info("🤖 [SCHEDULER] Génération des prédictions hybrides...")
        from scripts.pregenerate_predictions import pregenerate_predictions
        pregenerate_predictions(limit=30)
        logger.info("✅ [SCHEDULER] Prédictions générées avec succès")
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Erreur génération prédictions: {e}")

def fetch_matches_job():
    """Récupère les nouveaux matchs"""
    try:
        logger.info("📥 [SCHEDULER] Récupération des nouveaux matchs...")
        from scripts.fetch_upcoming_matches import fetch_upcoming_matches
        total, new = fetch_upcoming_matches(days_ahead=90)
        logger.info(f"✅ [SCHEDULER] {total} matchs récupérés, {new} nouveaux")
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Erreur récupération matchs: {e}")

def clean_cache_job():
    """Nettoie le cache expiré"""
    try:
        logger.info("🧹 [SCHEDULER] Nettoyage du cache...")
        import sqlite3
        conn = sqlite3.connect('/home/ubuntu/football-api-deploy/server/database/app.db')
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM hybrid_predictions_cache
            WHERE expires_at < datetime('now')
        """)
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        logger.info(f"✅ [SCHEDULER] {deleted} entrées expirées supprimées")
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Erreur nettoyage cache: {e}")

def continuous_learning_job():
    """Apprentissage automatique sur les matchs terminés"""
    try:
        logger.info("🤖 [SCHEDULER] Apprentissage automatique en cours...")
        from scripts.auto_learning import run_auto_learning
        run_auto_learning()
        logger.info("✅ [SCHEDULER] Apprentissage automatique terminé")
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Erreur apprentissage: {e}")

def init_scheduler():
    """Initialise le scheduler"""
    scheduler = BackgroundScheduler()
    
    # Générer les prédictions toutes les 30 minutes
    scheduler.add_job(
        func=generate_predictions_job,
        trigger="interval",
        minutes=30,
        id='scheduled_generate_predictions',
        name='Génération prédictions hybrides',
        replace_existing=True
    )
    
    # Récupérer les matchs toutes les 6 heures
    scheduler.add_job(
        func=fetch_matches_job,
        trigger="interval",
        hours=6,
        id='scheduled_fetch_matches',
        name='Récupération nouveaux matchs',
        replace_existing=True
    )
    
    # Nettoyer le cache toutes les heures
    scheduler.add_job(
        func=clean_cache_job,
        trigger="interval",
        hours=1,
        id='scheduled_clean_cache',
        name='Nettoyage cache',
        replace_existing=True
    )
    
    # Apprentissage continu toutes les heures
    scheduler.add_job(
        func=continuous_learning_job,
        trigger="interval",
        hours=1,
        id='scheduled_continuous_learning',
        name='Apprentissage continu IA',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler démarré avec succès")
    logger.info("   - Génération prédictions: toutes les 30 minutes")
    logger.info("   - Récupération matchs: toutes les 6 heures")
    logger.info("   - Nettoyage cache: toutes les heures")
    logger.info("   - Apprentissage continu: toutes les heures")
    
    # Génération initiale désactivée pour démarrage rapide
    # Le scheduler générera automatiquement toutes les 30 minutes
    logger.info("✅ Scheduler prêt - Prochaine génération dans 30 minutes")
    
    return scheduler

