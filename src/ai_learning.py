Système d'apprentissage de l'IA
Analyse les erreurs et succès pour améliorer les prédictions
"""
import json
import logging
from datetime import datetime
from models.football import Match, Prediction, LearningData

logger = logging.getLogger(__name__)

class AILearningSystem:
    """Système d'apprentissage automatique pour l'IA"""
    
    def __init__(self, session):
        self.session = session
    
    def analyze_and_learn(self):
        """Analyse tous les matchs terminés et met à jour les données d'apprentissage"""
        logger.info("🧠 Analyse des matchs terminés pour l'apprentissage...")
        
        # Récupérer tous les matchs terminés avec prédictions
        finished_matches = self.session.query(Match).filter(
            Match.status == 'FINISHED',
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).all()
        
        total = 0
        correct = 0
        league_stats = {}
        confidence_stats = {'Élevée': {'correct': 0, 'total': 0},
                           'Moyenne': {'correct': 0, 'total': 0},
                           'Faible': {'correct': 0, 'total': 0}}
        
        for match in finished_matches:
            prediction = self.session.query(Prediction).filter_by(match_id=match.id).first()
            
            if not prediction:
                continue
            
            total += 1
            
            # Déterminer le résultat réel
            if match.home_score > match.away_score:
                actual_result = 'home'
            elif match.away_score > match.home_score:
                actual_result = 'away'
            else:
                actual_result = 'draw'