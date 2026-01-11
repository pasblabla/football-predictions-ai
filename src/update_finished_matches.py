#!/usr/bin/env python3.11
"""
Script pour mettre à jour les résultats des matchs terminés
S'exécute automatiquement toutes les heures
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.football import Match, Prediction
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv('FOOTBALL_API_KEY', '647c75a7ce7f482598c8240664bd856c')
API_BASE_URL = 'https://api.football-data.org/v4'
DATABASE_PATH = 'src/database/app.db'

# Créer la session de base de données
engine = create_engine(f'sqlite:///{DATABASE_PATH}')
Session = sessionmaker(bind=engine)

def get_finished_matches_from_api():
    """Récupère les matchs terminés des 7 derniers jours depuis l'API"""
    headers = {'X-Auth-Token': API_KEY}
    
    # Date de début (7 jours en arrière)
    date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    competitions = ['PL', 'FL1', 'BL1', 'SA', 'PD', 'PPL', 'DED', 'CL']
    all_finished_matches = []
    
    for comp_code in competitions:
        try:
            url = f"{API_BASE_URL}/competitions/{comp_code}/matches"
            params = {
                'status': 'FINISHED',
                'dateFrom': date_from,
                'dateTo': date_to
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                all_finished_matches.extend(matches)
                logger.info(f"{comp_code}: {len(matches)} matchs terminés")
            else:
                logger.warning(f"{comp_code}: Erreur {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erreur pour {comp_code}: {e}")
            continue
    
    return all_finished_matches

def update_match_results(session):
    """Met à jour les résultats des matchs terminés dans la base de données"""
    finished_matches = get_finished_matches_from_api()
    updated_count = 0
    
    for api_match in finished_matches:
        try:
            external_id = api_match['id']
            
            # Trouver le match dans la base de données
            match = session.query(Match).filter_by(external_id=external_id).first()
            
            if match:
                # Mettre à jour le statut et les scores
                match.status = 'FINISHED'
                match.home_score = api_match['score']['fullTime']['home']
                match.away_score = api_match['score']['fullTime']['away']
                
                updated_count += 1
                
                logger.info(f"Mis à jour: {match.home_team_id} {match.home_score}-{match.away_score} {match.away_team_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du match {external_id}: {e}")
            continue
    
    session.commit()
    return updated_count

def analyze_predictions_accuracy(session):
    """Analyse la précision des prédictions pour les matchs terminés"""
    finished_matches = session.query(Match).filter_by(status='FINISHED').all()
    
    total = 0
    correct_winner = 0
    correct_btts = 0
    correct_over25 = 0
    
    for match in finished_matches:
        if not match.home_score is None and not match.away_score is None:
            total += 1
            
            # Récupérer la prédiction
            prediction = session.query(Prediction).filter_by(match_id=match.id).first()
            
            if prediction:
                # Vérifier la prédiction du vainqueur
                if match.home_score > match.away_score:
                    actual_result = 'home'
                elif match.away_score > match.home_score:
                    actual_result = 'away'
                else:
                    actual_result = 'draw'
                    
                if prediction.predicted_winner == actual_result:
                    correct_winner += 1
                
                # Vérifier BTTS (Both Teams To Score)
                actual_btts = match.home_score > 0 and match.away_score > 0
                if prediction.prob_both_teams_score:
                    prob_btts = prediction.prob_both_teams_score * 100
                    if (prob_btts > 50 and actual_btts) or (prob_btts <= 50 and not actual_btts):
                        correct_btts += 1
                
                # Vérifier +2.5 buts
                total_goals = match.home_score + match.away_score
                actual_over25 = total_goals > 2.5
                if prediction.prob_over_2_5:
                    prob_over = prediction.prob_over_2_5 * 100
                    if (prob_over > 50 and actual_over25) or (prob_over <= 50 and not actual_over25):
                        correct_over25 += 1
    
    if total > 0:
        logger.info(f"\n=== Statistiques de Précision ===")
        logger.info(f"Matchs analysés: {total}")
        logger.info(f"Précision vainqueur: {(correct_winner/total)*100:.1f}%")
        logger.info(f"Précision BTTS: {(correct_btts/total)*100:.1f}%")
        logger.info(f"Précision +2.5 buts: {(correct_over25/total)*100:.1f}%")
    
    return {
        'total': total,
        'correct_winner': correct_winner,
        'correct_btts': correct_btts,
        'correct_over25': correct_over25
    }

def main():
    """Fonction principale"""
    logger.info("=== Mise à jour des résultats des matchs terminés ===")
    
    session = Session()
    
    try:
        # Mettre à jour les résultats
        updated = update_match_results(session)
        logger.info(f"\n✅ {updated} matchs mis à jour")
        
        # Analyser la précision
        stats = analyze_predictions_accuracy(session)
        
        if stats['total'] > 0:
            logger.info(f"\n📊 Précision globale: {(stats['correct_winner']/stats['total'])*100:.1f}%")
        else:
            logger.info("\n⚠️ Aucun match terminé à analyser")
        
    except Exception as e:
        logger.error(f"Erreur: {e}")
        session.rollback()
    finally:
        session.close()
    
    logger.info("\n=== Terminé ===")

if __name__ == '__main__':
    main()

