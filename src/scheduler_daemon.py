#!/usr/bin/env python3
"""
Scheduler Daemon - Alternative au cron job
Exécute l'automatisation toutes les heures en arrière-plan
"""
import schedule
import time
import logging
import os
import sys
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_automation():
    """Exécute le script d'automatisation"""
    logger.info("="*60)
    logger.info(f"🕐 Exécution programmée - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    try:
        # Importer et exécuter l'automatisation
        from scripts.auto_update_matches import MatchAutomation
        
        automation = MatchAutomation()
        automation.run()
        
        logger.info("✅ Automatisation terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'automatisation: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Point d'entrée principal du scheduler"""
    logger.info("🚀 Démarrage du Scheduler Daemon")
    logger.info("⏰ Automatisation configurée: Toutes les heures")
    logger.info("📝 Logs: ../logs/scheduler.log")
    logger.info("-"*60)
    
    # Configurer l'exécution toutes les heures
    schedule.every().hour.at(":00").do(run_automation)
    
    # Exécution immédiate au démarrage (optionnel)
    logger.info("🎬 Exécution initiale...")
    run_automation()
    
    # Boucle principale
    logger.info("♻️ Scheduler en attente des prochaines exécutions...")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Vérifier toutes les minutes
            
        except KeyboardInterrupt:
            logger.info("⏹️ Arrêt du scheduler demandé")
            break
        except Exception as e:
            logger.error(f"❌ Erreur dans la boucle principale: {e}")
            time.sleep(300)  # Attendre 5 minutes avant de réessayer

if __name__ == '__main__':
    # Créer le dossier logs s'il n'existe pas
    os.makedirs('../logs', exist_ok=True)
    main()

