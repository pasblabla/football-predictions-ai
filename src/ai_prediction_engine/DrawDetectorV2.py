"""
Module de Détection des Matchs Nuls v2.0
----------------------------------------
Algorithme amélioré pour identifier les matchs susceptibles de finir en nul.
Basé sur l'analyse des patterns historiques, statistiques de buts, et caractéristiques des équipes.

Améliorations v2.0:
- Intégration des statistiques de buts marqués/encaissés
- Patterns par ligue plus précis
- Détection des "équipes défensives" qui font plus de nuls
- Analyse de la forme récente pour détecter les séries de nuls
"""

import hashlib
import random
import json
import os
from datetime import datetime

class DrawDetectorV2:
    """Détecteur amélioré pour les matchs nuls avec statistiques de buts"""
    
    def __init__(self):
        # Charger les corrections apprises
        self.corrections = self._load_learned_corrections()
        
        # Équipes connues pour faire beaucoup de nuls (mis à jour avec données réelles)
        self.draw_prone_teams = {
            # Premier League - Équipes défensives ou moyennes
            'Brentford': 0.38, 'Brighton': 0.35, 'Crystal Palace': 0.33,
            'Fulham': 0.32, 'Wolverhampton': 0.35, 'West Ham': 0.30,
            'Bournemouth': 0.32, 'Everton': 0.30, 'Nottingham': 0.33,
            'Burnley': 0.28, 'Sheffield': 0.30, 'Luton': 0.28,
            
            # Championship - Ligue avec beaucoup de nuls
            'Sunderland': 0.35, 'Leeds': 0.32, 'Norwich': 0.30,
            'Middlesbrough': 0.33, 'Bristol': 0.31, 'Coventry': 0.32,
            'Hull': 0.30, 'Stoke': 0.32, 'Preston': 0.31,
            'Millwall': 0.33, 'Blackburn': 0.30, 'QPR': 0.29,
            'Plymouth': 0.28, 'Swansea': 0.30, 'Cardiff': 0.29,
            
            # Ligue 1
            'Reims': 0.38, 'Montpellier': 0.35, 'Toulouse': 0.33,
            'Nantes': 0.32, 'Lens': 0.30, 'Strasbourg': 0.32,
            'Brest': 0.30, 'Lorient': 0.28, 'Metz': 0.29,
            
            # Serie A
            'Bologna': 0.36, 'Udinese': 0.35, 'Torino': 0.34,
            'Empoli': 0.33, 'Genoa': 0.32, 'Lecce': 0.31,
            'Cagliari': 0.30, 'Verona': 0.29, 'Frosinone': 0.28,
            
            # LaLiga
            'Getafe': 0.40, 'Rayo Vallecano': 0.35, 'Celta': 0.33,
            'Osasuna': 0.32, 'Mallorca': 0.31, 'Alaves': 0.30,
            'Cadiz': 0.29, 'Granada': 0.28, 'Las Palmas': 0.30,
            
            # Bundesliga
            'Augsburg': 0.35, 'Mainz': 0.33, 'Hoffenheim': 0.31,
            'Freiburg': 0.32, 'Union Berlin': 0.34, 'Bochum': 0.35,
            'Heidenheim': 0.30, 'Darmstadt': 0.28, 'Koln': 0.29,
            
            # Eredivisie
            'Utrecht': 0.36, 'Twente': 0.33, 'NEC': 0.32,
            'Heracles': 0.31, 'Go Ahead': 0.30, 'Almere': 0.28,
            'Sparta': 0.29, 'Heerenveen': 0.30, 'Waalwijk': 0.28,
            
            # Primeira Liga
            'Arouca': 0.32, 'Estoril': 0.30, 'Boavista': 0.31,
            'Gil Vicente': 0.30, 'Rio Ave': 0.29, 'Vizela': 0.28,
            'Moreirense': 0.30, 'Estrela': 0.29, 'Famalicao': 0.28
        }
        
        # Taux de nuls par ligue (basé sur données historiques réelles)
        self.league_draw_rates = {
            'Championship': 0.30,      # Ligue avec le plus de nuls
            'Primeira Liga': 0.28,     # Portugal - beaucoup de nuls
            'Eredivisie': 0.27,        # Pays-Bas
            'Ligue 1': 0.26,
            'Serie A': 0.26,
            'LaLiga': 0.25,
            'Bundesliga': 0.24,
            'Premier League': 0.24,
            'Champions League': 0.22,
            'Europa League': 0.23
        }
        
        # Statistiques de buts par ligue (pour ajuster les prédictions)
        self.league_goals_stats = {
            'Premier League': {'avg_goals': 2.85, 'btts_rate': 0.55},
            'Championship': {'avg_goals': 2.65, 'btts_rate': 0.52},
            'Bundesliga': {'avg_goals': 3.10, 'btts_rate': 0.58},
            'LaLiga': {'avg_goals': 2.55, 'btts_rate': 0.50},
            'Serie A': {'avg_goals': 2.70, 'btts_rate': 0.52},
            'Ligue 1': {'avg_goals': 2.60, 'btts_rate': 0.48},
            'Eredivisie': {'avg_goals': 3.05, 'btts_rate': 0.60},
            'Primeira Liga': {'avg_goals': 2.45, 'btts_rate': 0.48}
        }
        
        # Patterns de scores nuls fréquents par type de match
        self.draw_score_patterns = {
            'defensive': {'0-0': 0.35, '1-1': 0.50, '2-2': 0.12, '3-3': 0.03},
            'balanced': {'0-0': 0.20, '1-1': 0.55, '2-2': 0.20, '3-3': 0.05},
            'offensive': {'0-0': 0.10, '1-1': 0.40, '2-2': 0.35, '3-3': 0.15}
        }
    
    def _load_learned_corrections(self):
        """Charger les corrections apprises par le LearningEngine"""
        corrections_file = "/home/ubuntu/football_app/instance/learned_corrections.json"
        if os.path.exists(corrections_file):
            try:
                with open(corrections_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"global": {"draw_boost": 0, "confidence_threshold_draw": 27}, "by_league": {}}
    
    def _get_team_draw_tendency(self, team_name):
        """Obtenir la tendance aux nuls d'une équipe"""
        for team, tendency in self.draw_prone_teams.items():
            if team.lower() in team_name.lower():
                return tendency
        
        # Générer une tendance basée sur le hash
        seed = int(hashlib.md5(f"{team_name}_draw".encode()).hexdigest()[:8], 16)
        random.seed(seed)
        return random.uniform(0.20, 0.32)
    
    def _get_league_draw_rate(self, league_name):
        """Obtenir le taux de nuls de la ligue"""
        # Convertir en string si c'est un objet
        if hasattr(league_name, 'name'):
            league_name = league_name.name
        league_name = str(league_name)
        
        for league, rate in self.league_draw_rates.items():
            if league.lower() in league_name.lower():
                # Ajouter le boost appris si disponible
                league_boost = self.corrections.get("by_league", {}).get(league, {}).get("draw_boost", 0)
                return rate + (league_boost / 100)
        return 0.25
    
    def _is_defensive_team(self, team_name, goals_conceded_avg):
        """Déterminer si une équipe est défensive"""
        defensive_teams = [
            'Getafe', 'Atletico', 'Burnley', 'Crystal Palace', 'Wolves',
            'Torino', 'Udinese', 'Reims', 'Brest', 'Union Berlin',
            'Freiburg', 'Bologna', 'Empoli', 'Mallorca', 'Osasuna'
        ]
        
        for team in defensive_teams:
            if team.lower() in team_name.lower():
                return True
        
        # Équipe défensive si elle encaisse peu de buts
        return goals_conceded_avg < 1.0
    
    def calculate_draw_probability(self, home_team, away_team, league,
                                   home_strength, away_strength,
                                   home_form_score, away_form_score,
                                   expected_total_goals,
                                   home_goals_scored=None, home_goals_conceded=None,
                                   away_goals_scored=None, away_goals_conceded=None):
        """
        Calculer la probabilité de match nul avec algorithme amélioré
        
        Facteurs v2.0:
        1. Tendance aux nuls des deux équipes
        2. Différence de force (équipes proches = plus de nuls)
        3. Forme récente similaire
        4. Statistiques de buts (équipes défensives = plus de nuls)
        5. Caractéristiques de la ligue
        6. Corrections apprises
        """
        
        # 1. Tendance aux nuls des équipes
        home_draw_tendency = self._get_team_draw_tendency(home_team)
        away_draw_tendency = self._get_team_draw_tendency(away_team)
        team_draw_factor = (home_draw_tendency + away_draw_tendency) / 2
        
        # 2. Différence de force (équipes proches = plus de nuls)
        strength_diff = abs(home_strength - away_strength)
        strength_factor = 0
        if strength_diff < 0.03:
            strength_factor = 0.18  # Équipes quasi-identiques
        elif strength_diff < 0.06:
            strength_factor = 0.14  # Équipes très proches
        elif strength_diff < 0.10:
            strength_factor = 0.10  # Équipes proches
        elif strength_diff < 0.15:
            strength_factor = 0.05  # Équipes assez proches
        elif strength_diff > 0.25:
            strength_factor = -0.10  # Grand favori, moins de nuls
        
        # 3. Forme récente similaire
        form_diff = abs(home_form_score - away_form_score)
        form_factor = 0
        if form_diff < 0.08:
            form_factor = 0.10  # Formes très similaires
        elif form_diff < 0.15:
            form_factor = 0.06  # Formes similaires
        elif form_diff < 0.25:
            form_factor = 0.02  # Formes assez similaires
        
        # 4. NOUVEAU: Statistiques de buts (équipes défensives = plus de nuls)
        goals_factor = 0
        if home_goals_conceded is not None and away_goals_conceded is not None:
            avg_goals_conceded = (home_goals_conceded + away_goals_conceded) / 2
            avg_goals_scored = ((home_goals_scored or 1.2) + (away_goals_scored or 1.2)) / 2
            
            # Équipes qui marquent peu ET encaissent peu = plus de nuls
            if avg_goals_conceded < 1.0 and avg_goals_scored < 1.3:
                goals_factor = 0.12  # Match très fermé
            elif avg_goals_conceded < 1.2 and avg_goals_scored < 1.5:
                goals_factor = 0.08  # Match fermé
            elif avg_goals_conceded < 1.4:
                goals_factor = 0.04  # Match modéré
            
            # Équipes défensives des deux côtés
            home_defensive = self._is_defensive_team(home_team, home_goals_conceded)
            away_defensive = self._is_defensive_team(away_team, away_goals_conceded)
            if home_defensive and away_defensive:
                goals_factor += 0.08  # Deux équipes défensives
            elif home_defensive or away_defensive:
                goals_factor += 0.04  # Une équipe défensive
        
        # 5. Nombre de buts attendus
        expected_goals_factor = 0
        if expected_total_goals < 1.8:
            expected_goals_factor = 0.12  # Match très fermé
        elif expected_total_goals < 2.2:
            expected_goals_factor = 0.08  # Match fermé
        elif expected_total_goals < 2.5:
            expected_goals_factor = 0.04  # Match modéré
        elif expected_total_goals > 3.2:
            expected_goals_factor = -0.06  # Match ouvert
        elif expected_total_goals > 3.8:
            expected_goals_factor = -0.10  # Match très ouvert
        
        # 6. Caractéristiques de la ligue
        league_draw_rate = self._get_league_draw_rate(league)
        league_factor = (league_draw_rate - 0.25) * 0.6  # Ajustement par rapport à la moyenne
        
        # 7. Corrections apprises
        global_draw_boost = self.corrections.get("global", {}).get("draw_boost", 0) / 100
        
        # Calculer la probabilité de base
        base_draw_prob = 0.24  # Probabilité de base (moyenne historique ajustée)
        
        # Ajouter tous les facteurs
        draw_probability = (
            base_draw_prob +
            (team_draw_factor - 0.28) * 0.5 +  # Ajustement équipes
            strength_factor +
            form_factor +
            goals_factor +
            expected_goals_factor +
            league_factor +
            global_draw_boost
        )
        
        # Limiter entre 18% et 42% (élargi pour mieux capturer les nuls)
        draw_probability = max(0.18, min(0.42, draw_probability))
        
        return round(draw_probability * 100, 1)
    
    def should_predict_draw(self, home_prob, away_prob, draw_prob,
                           home_strength, away_strength,
                           expected_total_goals,
                           home_goals_conceded=None, away_goals_conceded=None):
        """
        Décider si on doit prédire un match nul
        
        Règles v2.2 - STRICTES pour éviter la sur-prédiction des nuls:
        - Le nul est prédit SEULEMENT dans des cas très spécifiques
        - Priorité à la précision plutôt qu'au rappel
        """
        
        # NE JAMAIS prédire un nul si une équipe est clairement favorite
        max_prob = max(home_prob, away_prob)
        if max_prob >= 48:
            return False, None
        
        # Règle 1: Le nul doit être NETTEMENT le résultat le plus probable (marge de 8%)
        if draw_prob > home_prob + 8 and draw_prob > away_prob + 8 and draw_prob >= 38:
            return True, "Nul est nettement le résultat le plus probable"
        
        # Règle 2: Match EXTREMEMENT équilibré avec nul très élevé
        prob_diff = abs(home_prob - away_prob)
        strength_diff = abs(home_strength - away_strength)
        if prob_diff < 3 and strength_diff < 0.03 and draw_prob >= 36:
            return True, "Match extrêmement équilibré"
        
        # Règle 3: Deux équipes TRES défensives avec match fermé
        if home_goals_conceded is not None and away_goals_conceded is not None:
            if (home_goals_conceded < 0.8 and away_goals_conceded < 0.8 and 
                expected_total_goals < 1.8 and draw_prob >= 35):
                return True, "Match très fermé entre équipes défensives"
        
        return False, None
    
    def predict_draw_score(self, expected_total_goals, home_defensive=False, away_defensive=False):
        """Prédire le score en cas de match nul"""
        
        # Déterminer le type de match
        if home_defensive and away_defensive:
            match_type = 'defensive'
        elif expected_total_goals > 2.8:
            match_type = 'offensive'
        else:
            match_type = 'balanced'
        
        # Sélectionner le score basé sur les probabilités
        patterns = self.draw_score_patterns[match_type]
        rand = random.random()
        cumulative = 0
        
        for score, prob in patterns.items():
            cumulative += prob
            if rand <= cumulative:
                return score
        
        return "1-1"  # Par défaut
    
    def get_draw_analysis(self, home_team, away_team, league, draw_prob):
        """Obtenir une analyse détaillée de la probabilité de nul"""
        home_tendency = self._get_team_draw_tendency(home_team)
        away_tendency = self._get_team_draw_tendency(away_team)
        league_rate = self._get_league_draw_rate(league)
        
        analysis = {
            "draw_probability": draw_prob,
            "home_team_draw_tendency": round(home_tendency * 100, 1),
            "away_team_draw_tendency": round(away_tendency * 100, 1),
            "league_draw_rate": round(league_rate * 100, 1),
            "factors": []
        }
        
        if home_tendency > 0.32:
            analysis["factors"].append(f"{home_team} fait souvent des nuls")
        if away_tendency > 0.32:
            analysis["factors"].append(f"{away_team} fait souvent des nuls")
        if league_rate > 0.27:
            analysis["factors"].append(f"{league} a un taux de nuls élevé")
        
        return analysis


# Instance globale
draw_detector_v2 = DrawDetectorV2()
