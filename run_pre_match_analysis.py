#!/usr/bin/env python3
"""
Script d'automatisation pour le scraping et la réanalyse 50 minutes avant chaque match.
Ce script doit être exécuté en tant que tâche cron ou service.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta

# Ajouter le chemin du projet
sys.path.insert(0, '/home/ubuntu/football_app')
os.chdir('/home/ubuntu/football_app')

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/pre_match_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_upcoming_matches():
    """Récupérer les matchs à venir dans les 60 prochaines minutes"""
    from src.models.football import Match, db
    from wsgi import app
    
    with app.app_context():
        now = datetime.now()
        soon = now + timedelta(minutes=60)
        
        matches = Match.query.filter(
            Match.status == 'SCHEDULED',
            Match.date >= now,
            Match.date <= soon
        ).all()
        
        return [m.to_dict() for m in matches]

def run_pre_match_analysis(match):
    """Exécuter l'analyse pré-match pour un match spécifique"""
    from src.automation.pre_match_analyzer import pre_match_analyzer
    
    logger.info(f"Analyse pré-match pour: {match.get('home_team')} vs {match.get('away_team')}")
    
    try:
        # Récupérer les absences
        absences = pre_match_analyzer.get_match_absences(
            match.get('home_team'),
            match.get('away_team')
        )
        
        # Réanalyser le match avec les nouvelles données
        analysis = pre_match_analyzer.analyze_match(match, absences)
        
        logger.info(f"Analyse terminée - Meilleur pari: {analysis.get('best_bet', {}).get('type')}")
        
        return analysis
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {e}")
        return None

def update_predictions(match_id, analysis):
    """Mettre à jour les prédictions dans la base de données"""
    from src.models.football import Prediction, db
    from wsgi import app
    
    with app.app_context():
        prediction = Prediction.query.filter_by(match_id=match_id).first()
        
        if prediction:
            prediction.prob_home_win = analysis.get('win_probability_home', prediction.prob_home_win)
            prediction.prob_draw = analysis.get('draw_probability', prediction.prob_draw)
            prediction.prob_away_win = analysis.get('win_probability_away', prediction.prob_away_win)
            prediction.prob_over_2_5 = analysis.get('prob_over_2_5', prediction.prob_over_2_5)
            prediction.prob_btts = analysis.get('btts_probability', prediction.prob_btts)
            prediction.updated_at = datetime.now()
            
            db.session.commit()
            logger.info(f"Prédictions mises à jour pour le match {match_id}")
        else:
            logger.warning(f"Aucune prédiction trouvée pour le match {match_id}")

def main():
    """Fonction principale"""
    logger.info("=== Démarrage de l'analyse pré-match ===")
    
    # Récupérer les matchs à venir
    matches = get_upcoming_matches()
    logger.info(f"Matchs à analyser: {len(matches)}")
    
    for match in matches:
        # Calculer le temps avant le match
        match_time = datetime.fromisoformat(match.get('date').replace('Z', '+00:00'))
        time_until_match = (match_time - datetime.now()).total_seconds() / 60
        
        # Analyser si le match est dans 50-60 minutes
        if 45 <= time_until_match <= 60:
            logger.info(f"Match dans {time_until_match:.0f} minutes - Lancement de l'analyse")
            
            analysis = run_pre_match_analysis(match)
            
            if analysis:
                update_predictions(match.get('id'), analysis)
        else:
            logger.info(f"Match dans {time_until_match:.0f} minutes - Pas encore le moment")
    
    logger.info("=== Analyse pré-match terminée ===")

if __name__ == '__main__':
    main()
