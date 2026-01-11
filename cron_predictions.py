#!/usr/bin/env python3
"""
Script de tâche planifiée pour la génération automatique des prédictions
Ce script s'exécute automatiquement via cron pour :
1. Générer et sauvegarder les prédictions pour les matchs à venir
2. Mettre à jour les résultats des matchs terminés
3. Calculer et logger la précision du modèle
"""

import os
import sys
import logging
from datetime import datetime

# Ajouter le chemin du projet
sys.path.insert(0, '/home/ubuntu/football_app')

# Configurer le logging
log_file = '/home/ubuntu/football_app/logs/cron_predictions.log'
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_predictions_task():
    """Exécuter la tâche de génération et mise à jour des prédictions"""
    logger.info("=" * 60)
    logger.info(f"Démarrage de la tâche planifiée - {datetime.now()}")
    logger.info("=" * 60)
    
    try:
        # Importer l'application Flask
        from wsgi import app
        from src.ai_prediction_engine.PredictionSaver import prediction_saver
        from src.ai_prediction_engine.LearningEngine import learning_engine
        from src.models.football import db, Match, Prediction
        
        with app.app_context():
            # Étape 1 : Générer les prédictions pour les matchs à venir
            logger.info("Étape 1: Génération des prédictions pour les 7 prochains jours...")
            stats_generate = prediction_saver.generate_and_save_predictions_for_upcoming_matches(days_ahead=7)
            logger.info(f"  - Matchs analysés: {stats_generate['total_matches']}")
            logger.info(f"  - Prédictions créées: {stats_generate['predictions_created']}")
            logger.info(f"  - Prédictions mises à jour: {stats_generate['predictions_updated']}")
            logger.info(f"  - Erreurs: {stats_generate['errors']}")
            
            # Étape 2 : Mettre à jour les résultats des matchs terminés
            logger.info("\nÉtape 2: Mise à jour des résultats des matchs terminés...")
            stats_update = prediction_saver.update_prediction_results()
            logger.info(f"  - Matchs vérifiés: {stats_update['total_checked']}")
            logger.info(f"  - Prédictions correctes: {stats_update['correct_predictions']}")
            logger.info(f"  - Prédictions incorrectes: {stats_update['incorrect_predictions']}")
            logger.info(f"  - Sans prédiction: {stats_update['no_prediction']}")
            logger.info(f"  - Précision: {stats_update['accuracy']}%")
            
            # Étape 3 : Obtenir les statistiques de précision détaillées
            logger.info("\nÉtape 3: Statistiques de précision (30 derniers jours)...")
            stats_accuracy = prediction_saver.get_accuracy_stats(days=30)
            logger.info(f"  - Total prédictions: {stats_accuracy['total_predictions']}")
            logger.info(f"  - Précision globale: {stats_accuracy['accuracy']}%")
            logger.info(f"  - Victoires domicile: {stats_accuracy['home_wins']['accuracy']}% ({stats_accuracy['home_wins']['correct']}/{stats_accuracy['home_wins']['total']})")
            logger.info(f"  - Victoires extérieur: {stats_accuracy['away_wins']['accuracy']}% ({stats_accuracy['away_wins']['correct']}/{stats_accuracy['away_wins']['total']})")
            logger.info(f"  - Matchs nuls: {stats_accuracy['draws']['accuracy']}% ({stats_accuracy['draws']['correct']}/{stats_accuracy['draws']['total']})")
            
            # Étape 4 : AUTO-ÉVOLUTION - Ré-entraînement automatique du modèle
            logger.info("\nÉtape 4: Auto-évolution du modèle...")
            try:
                from src.ai_prediction_engine.AutoEvolution import AutoEvolution, XGBoostAutoTrainer, run_auto_evolution
                
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
                            logger.info(f"  - Précision train: {train_result['train_accuracy']*100:.1f}%")
                            logger.info(f"  - Précision test: {train_result['test_accuracy']*100:.1f}%")
                            
                            # Enregistrer la session d'entraînement
                            session_result = evolution.record_training_session(
                                len(training_data),
                                train_result['test_accuracy']
                            )
                            logger.info(f"  - Nouvelle version: {session_result['new_version']}")
                        else:
                            logger.warning(f"  - Échec du ré-entraînement: {train_result.get('error')}")
                    else:
                        logger.info(f"  - Pas assez de données pour ré-entraîner ({len(training_data)} < 50)")
                else:
                    # Mettre à jour la précision même sans ré-entraînement
                    if stats_accuracy['accuracy'] > 0:
                        evolution.update_accuracy(stats_accuracy['accuracy'] / 100)
                        logger.info(f"  - Précision mise à jour: {stats_accuracy['accuracy']}%")
                
            except Exception as e:
                logger.warning(f"  - Erreur lors de l'auto-évolution: {e}")
            
            # Étape 5 : APPRENTISSAGE CONTINU - Analyser les erreurs et ajuster les poids
            logger.info("\nÉtape 5: Apprentissage continu (analyse des erreurs)...")
            try:
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
                    logger.info(f"  - Précision estimée après corrections: {result['new_accuracy_target']}%")
                    for corr in result['corrections_applied']:
                        logger.info(f"    [{corr['type']}] {corr['action']}")
                else:
                    logger.info("  - Aucune donnée à analyser")
            except Exception as e:
                logger.warning(f"  - Erreur lors de l'apprentissage: {e}")
            
            # Sauvegarder un résumé dans un fichier
            summary_file = '/home/ubuntu/football_app/logs/last_run_summary.txt'
            try:
                from src.ai_prediction_engine.AutoEvolution import get_current_version
                current_version = get_current_version()
            except:
                current_version = "v7.4.0"
            
            with open(summary_file, 'w') as f:
                f.write(f"Dernière exécution: {datetime.now()}\n")
                f.write(f"Version IA: {current_version}\n")
                f.write(f"Prédictions générées: {stats_generate['predictions_created']}\n")
                f.write(f"Prédictions mises à jour: {stats_generate['predictions_updated']}\n")
                f.write(f"Précision actuelle: {stats_accuracy['accuracy']}%\n")
                f.write(f"Matchs nuls détectés: {stats_accuracy['draws']['correct']}/{stats_accuracy['draws']['total']}\n")
            
            logger.info("\n" + "=" * 60)
            logger.info("Tâche terminée avec succès!")
            logger.info("=" * 60)
            
            return True
            
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la tâche: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = run_predictions_task()
    sys.exit(0 if success else 1)
