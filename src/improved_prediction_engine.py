import random
import math
from typing import Dict, Tuple

class ImprovedPredictionEngine:
    """Moteur de prédiction amélioré utilisant les vraies statistiques des équipes"""
    
    def __init__(self):
        # Facteurs de pondération
        self.HOME_ADVANTAGE = 0.15  # 15% d'avantage à domicile
        self.POSITION_WEIGHT = 0.35  # Importance de la position au classement
        self.FORM_WEIGHT = 0.30  # Importance de la forme (buts marqués/encaissés)
        self.POINTS_WEIGHT = 0.20  # Importance des points
        self.GOAL_DIFF_WEIGHT = 0.15  # Importance de la différence de buts
    
    def calculate_team_strength(self, team_stats: Dict) -> float:
        """Calculer la force d'une équipe basée sur ses vraies statistiques"""
        if not team_stats:
            return 0.5  # Valeur par défaut
        
        # Normaliser la position (1er = 1.0, dernier = 0.0)
        position_score = 1.0 - ((team_stats.get('position', 10) - 1) / 20)
        position_score = max(0.0, min(1.0, position_score))
        
        # Score basé sur les points (normaliser sur 90 points max)
        points_score = min(1.0, team_stats.get('points', 0) / 90)
        
        # Score basé sur la différence de buts (normaliser sur +/- 50)
        goal_diff = team_stats.get('goal_difference', 0)
        goal_diff_score = (goal_diff + 50) / 100
        goal_diff_score = max(0.0, min(1.0, goal_diff_score))
        
        # Score basé sur l'efficacité offensive et défensive
        played = team_stats.get('played', 1)
        if played > 0:
            goals_per_game = team_stats.get('goals_for', 0) / played
            conceded_per_game = team_stats.get('goals_against', 0) / played
            
            # Normaliser (0-3 buts par match)
            attack_score = min(1.0, goals_per_game / 3)
            defense_score = max(0.0, 1.0 - (conceded_per_game / 3))
            
            form_score = (attack_score + defense_score) / 2
        else:
            form_score = 0.5
        
        # Calculer le score final pondéré
        strength = (
            position_score * self.POSITION_WEIGHT +
            points_score * self.POINTS_WEIGHT +
            goal_diff_score * self.GOAL_DIFF_WEIGHT +
            form_score * self.FORM_WEIGHT
        )
        
        return min(1.0, max(0.0, strength))
    
    def predict_match(self, home_team_stats: Dict, away_team_stats: Dict, league_name: str = "") -> Dict:
        """Prédire le résultat d'un match basé sur les vraies statistiques"""
        
        # Calculer les forces des équipes
        home_strength = self.calculate_team_strength(home_team_stats)
        away_strength = self.calculate_team_strength(away_team_stats)
        
        # Ajouter l'avantage du terrain
        home_strength_adj = home_strength + self.HOME_ADVANTAGE
        
        # Calculer la différence de force
        strength_diff = home_strength_adj - away_strength
        
        # Calculer les probabilités avec une distribution plus réaliste
        # Utiliser une fonction sigmoïde pour une transition douce
        prob_home = 1 / (1 + math.exp(-5 * strength_diff))
        
        # Ajuster pour tenir compte des matchs nuls
        # Les matchs équilibrés ont plus de chances de match nul
        balance = abs(strength_diff)
        draw_factor = math.exp(-10 * balance)  # Plus équilibré = plus de chance de nul
        
        # Probabilités de base
        prob_draw = 0.25 * draw_factor + 0.15  # Entre 15% et 40%
        prob_home = prob_home * (1 - prob_draw)
        prob_away = (1 - prob_draw - prob_home)
        
        # Normaliser pour s'assurer que la somme = 1
        total = prob_home + prob_draw + prob_away
        prob_home /= total
        prob_draw /= total
        prob_away /= total
        
        # Déterminer le vainqueur prédit
        if prob_home > prob_draw and prob_home > prob_away:
            predicted_winner = "home"
        elif prob_away > prob_draw and prob_away > prob_home:
            predicted_winner = "away"
        else:
            predicted_winner = "draw"
        
        # Calculer le niveau de confiance
        max_prob = max(prob_home, prob_draw, prob_away)
        if max_prob >= 0.55:
            confidence = "Élevée"
        elif max_prob >= 0.40:
            confidence = "Moyenne"
        else:
            confidence = "Faible"
        
        # Prédire le score basé sur les moyennes de buts
        home_goals_avg = home_team_stats.get('goals_for', 0) / max(1, home_team_stats.get('played', 1))
        away_goals_avg = away_team_stats.get('goals_for', 0) / max(1, away_team_stats.get('played', 1))
        home_conceded_avg = home_team_stats.get('goals_against', 0) / max(1, home_team_stats.get('played', 1))
        away_conceded_avg = away_team_stats.get('goals_against', 0) / max(1, away_team_stats.get('played', 1))
        
        # Prédire les buts en tenant compte de l'attaque et de la défense
        predicted_home_goals = round((home_goals_avg + away_conceded_avg) / 2)
        predicted_away_goals = round((away_goals_avg + home_conceded_avg) / 2)
        
        # Ajuster selon le vainqueur prédit
        if predicted_winner == "home" and predicted_home_goals <= predicted_away_goals:
            predicted_home_goals = predicted_away_goals + 1
        elif predicted_winner == "away" and predicted_away_goals <= predicted_home_goals:
            predicted_away_goals = predicted_home_goals + 1
        elif predicted_winner == "draw":
            predicted_away_goals = predicted_home_goals
        
        # Limiter les scores à des valeurs réalistes
        predicted_home_goals = max(0, min(5, predicted_home_goals))
        predicted_away_goals = max(0, min(5, predicted_away_goals))
        
        # Calculer les probabilités pour over/under et BTTS
        total_goals_avg = home_goals_avg + away_goals_avg
        prob_over_2_5 = min(0.95, max(0.05, (total_goals_avg - 1.5) / 3))
        
        # BTTS basé sur les moyennes de buts marqués
        prob_both_score = min(0.95, max(0.05, (home_goals_avg * away_goals_avg) / 4))
        
        # Calculer le score de fiabilité (1-10)
        # Basé sur la qualité des données et la confiance
        data_quality = 1.0
        if home_team_stats.get('played', 0) < 5:
            data_quality *= 0.7
        if away_team_stats.get('played', 0) < 5:
            data_quality *= 0.7
        
        reliability_base = max_prob * 10 * data_quality
        reliability_score = max(1, min(10, round(reliability_base)))
        
        return {
            'predicted_winner': predicted_winner,
            'confidence': confidence,
            'prob_home_win': round(prob_home, 3),
            'prob_draw': round(prob_draw, 3),
            'prob_away_win': round(prob_away, 3),
            'predicted_score_home': predicted_home_goals,
            'predicted_score_away': predicted_away_goals,
            'reliability_score': reliability_score,
            'prob_over_2_5': round(prob_over_2_5, 3),
            'prob_both_teams_score': round(prob_both_score, 3),
            'home_strength': round(home_strength, 3),
            'away_strength': round(away_strength, 3)
        }

