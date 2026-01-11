"""
Module de tâches planifiées avec APScheduler
S'exécute automatiquement avec l'application Flask
"""

import logging
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)

def generate_predictions_task():
    """Tâche : Générer les prédictions pour les matchs à venir"""
    logger.info(f"[{datetime.now()}] Démarrage de la tâche de génération des prédictions...")
    
    try:
        from src.ai_prediction_engine.PredictionSaver import prediction_saver
        
        # Générer les prédictions pour les 7 prochains jours
        stats = prediction_saver.generate_and_save_predictions_for_upcoming_matches(days_ahead=7)
        
        logger.info(f"  - Matchs analysés: {stats['total_matches']}")
        logger.info(f"  - Prédictions créées: {stats['predictions_created']}")
        logger.info(f"  - Prédictions mises à jour: {stats['predictions_updated']}")
        
        return stats
    except Exception as e:
        logger.error(f"Erreur lors de la génération des prédictions: {e}")
        return None


def update_results_task():
    """Tâche : Mettre à jour les résultats des matchs terminés"""
    logger.info(f"[{datetime.now()}] Démarrage de la tâche de mise à jour des résultats...")
    
    try:
        from src.ai_prediction_engine.PredictionSaver import prediction_saver
        
        # Mettre à jour les résultats
        stats = prediction_saver.update_prediction_results()
        
        logger.info(f"  - Matchs vérifiés: {stats['total_checked']}")
        logger.info(f"  - Prédictions correctes: {stats['correct_predictions']}")
        logger.info(f"  - Précision: {stats['accuracy']}%")
        
        return stats
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des résultats: {e}")
        return None


def learning_task():
    """Tâche : Apprentissage continu et ajustement des poids"""
    logger.info(f"[{datetime.now()}] Démarrage de la tâche d'apprentissage continu...")
    
    try:
        from src.ai_prediction_engine.LearningEngine import learning_engine
        from src.models.football import Match, Prediction
        
        # Récupérer les matchs terminés avec prédictions
        finished_matches = Match.query.filter(Match.status == 'FINISHED').all()
        matches_data = []
        
        for match in finished_matches:
            pred = Prediction.query.filter_by(match_id=match.id).first()
            if not pred or not pred.predicted_winner:
                continue
            
            # Résultat réel
            if match.home_score > match.away_score:
                actual = 'HOME'
            elif match.away_score > match.home_score:
                actual = 'AWAY'
            else:
                actual = 'DRAW'
            
            match_info = {
                "id": match.id,
                "league": match.league.name if match.league else "Unknown",
            }
            
            prediction_info = {
                "predicted_winner": pred.predicted_winner,
            }
            
            matches_data.append((match_info, prediction_info, actual))
        
        if matches_data:
            result = learning_engine.analyze_and_learn(matches_data)
            logger.info(f"  - Matchs analysés: {result['stats']['total']}")
            logger.info(f"  - Corrections appliquées: {len(result['corrections_applied'])}")
            return result
        else:
            logger.info("  - Aucune donnée à analyser")
            return None
            
    except Exception as e:
        logger.error(f"Erreur lors de l'apprentissage: {e}")
        return None


def auto_evolution_task():
    """Tâche : Auto-évolution et ré-entraînement du modèle"""
    logger.info(f"[{datetime.now()}] Démarrage de la tâche d'auto-évolution...")
    
    try:
        from src.ai_prediction_engine.AutoEvolution import AutoEvolution, XGBoostAutoTrainer
        from src.ai_prediction_engine.PredictionSaver import prediction_saver
        from src.models.football import db
        
        evolution = AutoEvolution()
        trainer = XGBoostAutoTrainer()
        
        # Vérifier si on doit ré-entraîner
        should_train, reason = evolution.should_retrain()
        logger.info(f"  - Version actuelle: {evolution.get_version_string()}")
        logger.info(f"  - Doit ré-entraîner: {should_train} ({reason})")
        
        if should_train:
            # Collecter les données d'entraînement
            training_data = trainer.collect_training_data(db.session)
            logger.info(f"  - Données d'entraînement collectées: {len(training_data)}")
            
            if len(training_data) >= 50:
                # Entraîner le modèle
                train_result = trainer.train_model(training_data)
                
                if train_result['success']:
                    logger.info(f"  - Modèle ré-entraîné avec succès!")
                    logger.info(f"  - Précision test: {train_result['test_accuracy']*100:.1f}%")
                    
                    # Enregistrer la session d'entraînement
                    session_result = evolution.record_training_session(
                        len(training_data),
                        train_result['test_accuracy']
                    )
                    logger.info(f"  - Nouvelle version: {session_result['new_version']}")
                    return session_result
                else:
                    logger.warning(f"  - Échec du ré-entraînement: {train_result.get('error')}")
            else:
                logger.info(f"  - Pas assez de données pour ré-entraîner")
        else:
            # Mettre à jour la précision
            stats = prediction_saver.get_accuracy_stats(days=30)
            if stats['accuracy'] > 0:
                evolution.update_accuracy(stats['accuracy'] / 100)
                logger.info(f"  - Précision mise à jour: {stats['accuracy']}%")
        
        return {'version': evolution.get_version_string()}
        
    except Exception as e:
        logger.error(f"Erreur lors de l'auto-évolution: {e}")
        return None


def fetch_data_task():
    """Tâche : Récupérer les données depuis SoccerStats.com et l'API"""
    logger.info(f"[{datetime.now()}] Démarrage de la récupération automatique des données...")
    
    try:
        from src.auto_data_fetcher import AutoDataFetcher
        
        fetcher = AutoDataFetcher()
        result = fetcher.fetch_all_data()
        
        logger.info(f"  - Matchs récupérés: {result['matches_count'] if 'matches_count' in result else len(result.get('matches', []))}")
        logger.info(f"  - API disponible: {result.get('api_available', False)}")
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données: {e}")
        return None


def run_all_tasks():
    """Exécuter toutes les tâches dans l'ordre"""
    logger.info("=" * 60)
    logger.info(f"EXÉCUTION COMPLÈTE DES TÂCHES - {datetime.now()}")
    logger.info("=" * 60)
    
    results = {}
    
    # 0. Récupérer les données (API + SoccerStats)
    results['data_fetch'] = fetch_data_task()
    
    # 1. Générer les prédictions
    results['predictions'] = generate_predictions_task()
    
    # 2. Mettre à jour les résultats
    results['results'] = update_results_task()
    
    # 3. Auto-évolution
    results['evolution'] = auto_evolution_task()
    
    # 4. Apprentissage continu
    results['learning'] = learning_task()
    
    logger.info("=" * 60)
    logger.info("TÂCHES TERMINÉES")
    logger.info("=" * 60)
    
    return results
