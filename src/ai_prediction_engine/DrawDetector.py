"""
Module de Détection des Matchs Nuls v1.0
- Algorithme spécialisé pour identifier les matchs susceptibles de finir en nul
- Basé sur l'analyse des patterns historiques et des caractéristiques des équipes
"""

import hashlib
import random
from datetime import datetime

class DrawDetector:
    """Détecteur spécialisé pour les matchs nuls"""
    
    def __init__(self):
        # Équipes connues pour faire beaucoup de nuls
        self.draw_prone_teams = {
            # Premier League
            'Brentford': 0.35, 'Brighton': 0.32, 'Crystal Palace': 0.30,
            'Fulham': 0.28, 'Wolverhampton': 0.30, 'West Ham': 0.28,
            'Bournemouth': 0.28, 'Everton': 0.27, 'Nottingham': 0.29,
            
            # Ligue 1
            'Reims': 0.35, 'Montpellier': 0.32, 'Toulouse': 0.30,
            'Nantes': 0.28, 'Lens': 0.27, 'Strasbourg': 0.29,
            
            # Serie A
            'Bologna': 0.33, 'Udinese': 0.32, 'Torino': 0.31,
            'Empoli': 0.30, 'Genoa': 0.29, 'Lecce': 0.28,
            
            # LaLiga
            'Getafe': 0.35, 'Rayo Vallecano': 0.32, 'Celta': 0.30,
            'Osasuna': 0.29, 'Mallorca': 0.28, 'Alaves': 0.27,
            
            # Bundesliga
            'Augsburg': 0.32, 'Mainz': 0.30, 'Hoffenheim': 0.28,
            'Freiburg': 0.29, 'Union Berlin': 0.30, 'Bochum': 0.31,
            
            # Eredivisie
            'Utrecht': 0.33, 'Twente': 0.30, 'NEC': 0.29,
            'Heracles': 0.28, 'Go Ahead': 0.27
        }
        
        # Ligues avec plus de nuls
        self.draw_prone_leagues = {
            'Championship': 0.28,
            'Ligue 1': 0.26,
            'Serie A': 0.25,
            'LaLiga': 0.24,
            'Bundesliga': 0.23,
            'Premier League': 0.22,
            'Eredivisie': 0.25
        }
        
        # Patterns de scores nuls fréquents
        self.common_draw_scores = {
            '1-1': 0.45,  # Le plus fréquent
            '0-0': 0.25,
            '2-2': 0.20,
            '3-3': 0.07,
            '4-4': 0.03
        }
    
    def _get_team_draw_tendency(self, team_name):
        """Obtenir la tendance aux nuls d'une équipe"""
        # Vérifier si l'équipe est connue pour faire des nuls
        for team, tendency in self.draw_prone_teams.items():
            if team.lower() in team_name.lower():
                return tendency
        
        # Sinon, générer une tendance basée sur le hash
        seed = int(hashlib.md5(f"{team_name}_draw".encode()).hexdigest()[:8], 16)
        random.seed(seed)
        return random.uniform(0.18, 0.30)
    
    def _get_league_draw_rate(self, league_name):
        """Obtenir le taux de nuls de la ligue"""
        for league, rate in self.draw_prone_leagues.items():
            if league.lower() in league_name.lower():
                return rate
        return 0.24  # Taux moyen par défaut
    
    def calculate_draw_probability(self, home_team, away_team, league,
                                   home_strength, away_strength,
                                   home_form_score, away_form_score,
                                   expected_total_goals):
        """
        Calculer la probabilité de match nul avec un algorithme spécialisé
        
        Facteurs pris en compte:
        1. Tendance aux nuls des deux équipes
        2. Différence de force entre les équipes (équipes proches = plus de nuls)
        3. Forme récente similaire
        4. Nombre de buts attendus (moins de buts = plus de nuls)
        5. Caractéristiques de la ligue
        """
        
        # 1. Tendance aux nuls des équipes
        home_draw_tendency = self._get_team_draw_tendency(home_team)
        away_draw_tendency = self._get_team_draw_tendency(away_team)
        team_draw_factor = (home_draw_tendency + away_draw_tendency) / 2
        
        # 2. Différence de force (équipes proches = plus de nuls)
        strength_diff = abs(home_strength - away_strength)
        strength_factor = 0
        if strength_diff < 0.05:
            strength_factor = 0.15  # Équipes très proches
        elif strength_diff < 0.10:
            strength_factor = 0.10  # Équipes proches
        elif strength_diff < 0.15:
            strength_factor = 0.05  # Équipes assez proches
        elif strength_diff > 0.25:
            strength_factor = -0.08  # Grand favori, moins de nuls
        
        # 3. Forme récente similaire
        form_diff = abs(home_form_score - away_form_score)
        form_factor = 0
        if form_diff < 0.1:
            form_factor = 0.08  # Formes très similaires
        elif form_diff < 0.2:
            form_factor = 0.04  # Formes similaires
        
        # 4. Nombre de buts attendus (moins de buts = plus de nuls)
        goals_factor = 0
        if expected_total_goals < 2.0:
            goals_factor = 0.10  # Match fermé, plus de 0-0 ou 1-1
        elif expected_total_goals < 2.5:
            goals_factor = 0.05  # Match modéré
        elif expected_total_goals > 3.5:
            goals_factor = -0.05  # Match ouvert, moins de nuls
        
        # 5. Caractéristiques de la ligue
        league_draw_rate = self._get_league_draw_rate(league)
        league_factor = (league_draw_rate - 0.24) * 0.5  # Ajustement par rapport à la moyenne
        
        # Calculer la probabilité de base
        base_draw_prob = 0.22  # Probabilité de base (moyenne historique)
        
        # Ajouter tous les facteurs
        draw_probability = (
            base_draw_prob +
            (team_draw_factor - 0.25) * 0.4 +  # Ajustement équipes
            strength_factor +
            form_factor +
            goals_factor +
            league_factor
        )
        
        # Limiter entre 18% et 35% (plus réaliste)
        draw_probability = max(0.18, min(0.35, draw_probability))
        
        return round(draw_probability * 100, 1)
    
    def should_predict_draw(self, home_prob, away_prob, draw_prob,
                           home_strength, away_strength,
                           expected_total_goals):
        """
        Décider si on doit prédire un match nul
        
        Règles TRÈS STRICTES pour éviter la sur-prédiction des nuls:
        - Un nul est prédit SEULEMENT si les conditions sont très spécifiques
        - Le nul doit être le résultat le PLUS probable ou très proche
        """
        
        # NE JAMAIS prédire un nul si une équipe est clairement favorite
        max_prob = max(home_prob, away_prob)
        if max_prob >= 50:
            return False, None
        
        # Règle 1: Le nul doit être le résultat le plus probable
        if draw_prob > home_prob and draw_prob > away_prob and draw_prob >= 35:
            return True, "Nul est le résultat le plus probable"
        
        # Règle 2: Match VRAIMENT équilibré (diff < 5%)
        prob_diff = abs(home_prob - away_prob)
        if prob_diff < 5 and draw_prob >= 32:
            return True, "Match extrêmement équilibré"
        
        # Règle 3: Équipes de force TRÈS similaire avec match fermé
        strength_diff = abs(home_strength - away_strength)
        if strength_diff < 0.05 and expected_total_goals < 2.0 and draw_prob >= 30:
            return True, "Équipes très similaires, match fermé"
        
        return False, None
    
    def predict_draw_score(self, expected_total_goals):
        """Prédire le score en cas de match nul"""
        if expected_total_goals < 1.5:
            return "0-0"
        elif expected_total_goals < 2.5:
            return "1-1"
        elif expected_total_goals < 3.5:
            # 1-1 ou 2-2
            return random.choice(["1-1", "1-1", "2-2"])
        else:
            # Match ouvert
            return random.choice(["1-1", "2-2", "2-2", "3-3"])


# Instance globale
draw_detector = DrawDetector()
