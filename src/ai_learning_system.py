#!/usr/bin/env python3.11
"""
Système d'apprentissage de l'IA pour améliorer les prédictions
Analyse les erreurs et succès passés pour ajuster les algorithmes
"""

import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.football import Match, Prediction, Team, League
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_PATH = 'src/database/app.db'
LEARNING_DATA_FILE = 'learning_data.json'

# Créer la session de base de données
engine = create_engine(f'sqlite:///{DATABASE_PATH}')
Session = sessionmaker(bind=engine)

class AILearningSystem:
    """Système d'apprentissage pour améliorer les prédictions"""
    
    def __init__(self, session):
        self.session = session
        self.learning_data = self.load_learning_data()
    
    def load_learning_data(self):
        """Charge les données d'apprentissage depuis le fichier JSON"""
        if os.path.exists(LEARNING_DATA_FILE):
            try:
                with open(LEARNING_DATA_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erreur lors du chargement des données: {e}")
        
        # Données par défaut
        return {
            'total_predictions': 0,
            'correct_predictions': 0,
            'accuracy_by_league': {},
            'accuracy_by_confidence': {
                'Élevée': {'correct': 0, 'total': 0},
                'Moyenne': {'correct': 0, 'total': 0},
                'Faible': {'correct': 0, 'total': 0}
            },
            'common_errors': [],
            'improvement_suggestions': [],
            'last_update': None
        }
    
    def save_learning_data(self):
        """Sauvegarde les données d'apprentissage"""
        try:
            with open(LEARNING_DATA_FILE, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
            logger.info("✅ Données d'apprentissage sauvegardées")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
    
    def analyze_finished_matches(self):
        """Analyse tous les matchs terminés pour apprendre"""
        logger.info("=== Analyse des matchs terminés ===")
        
        finished_matches = self.session.query(Match).filter(
            Match.status == 'FINISHED',
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).all()
        
        total_analyzed = 0
        correct_count = 0
        errors_analysis = []
        
        for match in finished_matches:
            prediction = self.session.query(Prediction).filter_by(match_id=match.id).first()
            
            if not prediction:
                continue
            
            total_analyzed += 1
            
            # Déterminer le résultat réel
            if match.home_score > match.away_score:
                actual_result = 'home'
            elif match.away_score > match.home_score:
                actual_result = 'away'
            else:
                actual_result = 'draw'
            
            # Vérifier si la prédiction était correcte
            is_correct = (prediction.predicted_winner == actual_result)
            
            if is_correct:
                correct_count += 1
            else:
                # Analyser l'erreur
                error_info = {
                    'match_id': match.id,
                    'league': match.league.name,
                    'home_team': match.home_team.name,
                    'away_team': match.away_team.name,
                    'predicted': prediction.predicted_winner,
                    'actual': actual_result,
                    'confidence': prediction.confidence,
                    'score': f"{match.home_score}-{match.away_score}",
                    'prob_home': prediction.prob_home_win,
                    'prob_draw': prediction.prob_draw,
                    'prob_away': prediction.prob_away_win
                }
                errors_analysis.append(error_info)
            
            # Mettre à jour les stats par championnat
            league_name = match.league.name
            if league_name not in self.learning_data['accuracy_by_league']:
                self.learning_data['accuracy_by_league'][league_name] = {
                    'correct': 0,
                    'total': 0
                }
            
            self.learning_data['accuracy_by_league'][league_name]['total'] += 1
            if is_correct:
                self.learning_data['accuracy_by_league'][league_name]['correct'] += 1
            
            # Mettre à jour les stats par confiance
            confidence = prediction.confidence
            if confidence in self.learning_data['accuracy_by_confidence']:
                self.learning_data['accuracy_by_confidence'][confidence]['total'] += 1
                if is_correct:
                    self.learning_data['accuracy_by_confidence'][confidence]['correct'] += 1
        
        # Mettre à jour les totaux
        self.learning_data['total_predictions'] = total_analyzed
        self.learning_data['correct_predictions'] = correct_count
        self.learning_data['last_update'] = datetime.now().isoformat()
        
        # Analyser les erreurs communes
        self.analyze_common_errors(errors_analysis)
        
        # Générer des suggestions d'amélioration
        self.generate_improvement_suggestions()
        
        # Sauvegarder
        self.save_learning_data()
        
        # Afficher le rapport
        self.display_learning_report()
        
        return {
            'total': total_analyzed,
            'correct': correct_count,
            'accuracy': (correct_count / total_analyzed * 100) if total_analyzed > 0 else 0
        }
    
    def analyze_common_errors(self, errors):
        """Identifie les patterns d'erreurs communes"""
        logger.info("\n=== Analyse des erreurs communes ===")
        
        common_errors = []
        
        # Erreur 1: Favoris qui perdent
        favorites_lost = [e for e in errors if e['predicted'] == 'home' and e['actual'] == 'away' and e['prob_home'] > 0.6]
        if len(favorites_lost) > 5:
            common_errors.append({
                'type': 'favorite_upset',
                'count': len(favorites_lost),
                'description': f"L'IA surestime souvent les favoris à domicile ({len(favorites_lost)} cas)",
                'suggestion': "Réduire le coefficient d'avantage à domicile de 5%"
            })
            logger.info(f"⚠️ Favoris à domicile surestimés: {len(favorites_lost)} cas")
        
        # Erreur 2: Match nuls non prédits
        missed_draws = [e for e in errors if e['actual'] == 'draw' and e['prob_draw'] < 0.25]
        if len(missed_draws) > 5:
            common_errors.append({
                'type': 'missed_draws',
                'count': len(missed_draws),
                'description': f"L'IA manque souvent les matchs nuls ({len(missed_draws)} cas)",
                'suggestion': "Augmenter la probabilité de match nul pour les équipes équilibrées"
            })
            logger.info(f"⚠️ Matchs nuls manqués: {len(missed_draws)} cas")
        
        # Erreur 3: Surprises en Champions League
        cl_errors = [e for e in errors if 'Champions' in e['league']]
        if len(cl_errors) > 10:
            common_errors.append({
                'type': 'champions_league_volatility',
                'count': len(cl_errors),
                'description': f"Moins bonne précision en Champions League ({len(cl_errors)} erreurs)",
                'suggestion': "Ajuster les coefficients pour les compétitions européennes"
            })
            logger.info(f"⚠️ Erreurs en Champions League: {len(cl_errors)} cas")
        
        # Erreur 4: Confiance élevée mais erreur
        high_confidence_errors = [e for e in errors if e['confidence'] == 'Élevée']
        if len(high_confidence_errors) > 0:
            common_errors.append({
                'type': 'overconfident_predictions',
                'count': len(high_confidence_errors),
                'description': f"Prédictions avec confiance élevée mais incorrectes ({len(high_confidence_errors)} cas)",
                'suggestion': "Revoir les seuils de confiance élevée"
            })
            logger.info(f"⚠️ Confiance élevée mais erreur: {len(high_confidence_errors)} cas")
        
        self.learning_data['common_errors'] = common_errors
        
        return common_errors
    
    def generate_improvement_suggestions(self):
        """Génère des suggestions pour améliorer les prédictions"""
        logger.info("\n=== Suggestions d'amélioration ===")
        
        suggestions = []
        
        # Analyser la précision par championnat
        for league, stats in self.learning_data['accuracy_by_league'].items():
            if stats['total'] >= 5:
                accuracy = (stats['correct'] / stats['total']) * 100
                if accuracy < 35:
                    suggestions.append({
                        'priority': 'high',
                        'category': 'league_specific',
                        'description': f"{league}: Précision faible ({accuracy:.1f}%)",
                        'action': f"Collecter plus de données historiques pour {league}"
                    })
                    logger.info(f"🔴 {league}: {accuracy:.1f}% - Nécessite amélioration")
                elif accuracy > 55:
                    logger.info(f"🟢 {league}: {accuracy:.1f}% - Bonne performance")
        
        # Analyser la précision par confiance
        for level, stats in self.learning_data['accuracy_by_confidence'].items():
            if stats['total'] >= 5:
                accuracy = (stats['correct'] / stats['total']) * 100
                expected_accuracy = {'Élevée': 60, 'Moyenne': 45, 'Faible': 30}
                
                if accuracy < expected_accuracy[level]:
                    suggestions.append({
                        'priority': 'medium',
                        'category': 'confidence_calibration',
                        'description': f"Confiance {level}: {accuracy:.1f}% (attendu: {expected_accuracy[level]}%)",
                        'action': f"Recalibrer les seuils de confiance {level}"
                    })
                    logger.info(f"⚠️ Confiance {level}: {accuracy:.1f}% (objectif: {expected_accuracy[level]}%)")
        
        # Suggestion générale
        overall_accuracy = (self.learning_data['correct_predictions'] / 
                          self.learning_data['total_predictions'] * 100) if self.learning_data['total_predictions'] > 0 else 0
        
        if overall_accuracy < 45:
            suggestions.append({
                'priority': 'high',
                'category': 'overall_improvement',
                'description': f"Précision globale: {overall_accuracy:.1f}% (objectif: 50%+)",
                'action': "Intégrer des données de forme récente et confrontations directes"
            })
        
        self.learning_data['improvement_suggestions'] = suggestions
        
        return suggestions
    
    def display_learning_report(self):
        """Affiche un rapport complet d'apprentissage"""
        logger.info("\n" + "="*60)
        logger.info("📊 RAPPORT D'APPRENTISSAGE DE L'IA")
        logger.info("="*60)
        
        total = self.learning_data['total_predictions']
        correct = self.learning_data['correct_predictions']
        accuracy = (correct / total * 100) if total > 0 else 0
        
        logger.info(f"\n📈 Performance Globale:")
        logger.info(f"   Total de prédictions: {total}")
        logger.info(f"   Prédictions correctes: {correct}")
        logger.info(f"   Précision: {accuracy:.2f}%")
        
        logger.info(f"\n🏆 Précision par Championnat:")
        for league, stats in sorted(self.learning_data['accuracy_by_league'].items(), 
                                    key=lambda x: (x[1]['correct']/x[1]['total'] if x[1]['total'] > 0 else 0), 
                                    reverse=True):
            if stats['total'] >= 3:
                league_accuracy = (stats['correct'] / stats['total']) * 100
                logger.info(f"   {league}: {league_accuracy:.1f}% ({stats['correct']}/{stats['total']})")
        
        logger.info(f"\n⭐ Précision par Niveau de Confiance:")
        for level, stats in self.learning_data['accuracy_by_confidence'].items():
            if stats['total'] > 0:
                level_accuracy = (stats['correct'] / stats['total']) * 100
                logger.info(f"   {level}: {level_accuracy:.1f}% ({stats['correct']}/{stats['total']})")
        
        if self.learning_data['common_errors']:
            logger.info(f"\n⚠️  Erreurs Communes Identifiées:")
            for error in self.learning_data['common_errors']:
                logger.info(f"   • {error['description']}")
                logger.info(f"     → {error['suggestion']}")
        
        if self.learning_data['improvement_suggestions']:
            logger.info(f"\n💡 Suggestions d'Amélioration:")
            for suggestion in self.learning_data['improvement_suggestions']:
                priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                icon = priority_icon.get(suggestion['priority'], '•')
                logger.info(f"   {icon} {suggestion['description']}")
                logger.info(f"      → {suggestion['action']}")
        
        logger.info("\n" + "="*60)
        logger.info(f"Dernière mise à jour: {self.learning_data['last_update']}")
        logger.info("="*60 + "\n")

def main():
    """Fonction principale"""
    logger.info("🤖 Démarrage du système d'apprentissage de l'IA")
    
    session = Session()
    
    try:
        learning_system = AILearningSystem(session)
        results = learning_system.analyze_finished_matches()
        
        logger.info(f"\n✅ Analyse terminée:")
        logger.info(f"   {results['total']} matchs analysés")
        logger.info(f"   {results['correct']} prédictions correctes")
        logger.info(f"   {results['accuracy']:.2f}% de précision")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    main()

