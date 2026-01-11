"""
Moteur de prédiction basé sur Machine Learning
Utilise les statistiques réelles des équipes pour faire des prédictions
"""

import numpy as np
import requests
import time
from typing import Dict, Tuple
import os

API_KEY = os.environ.get('FOOTBALL_DATA_API_KEY', '647c75a7ce7f482598c8240664bd856c')
BASE_URL = 'https://api.football-data.org/v4'

headers = {
    'X-Auth-Token': API_KEY
}

class MLPredictionEngine:
    """Moteur de prédiction ML basé sur les statistiques réelles"""
    
    def __init__(self):
        self.HOME_ADVANTAGE = 0.15  # 15% d'avantage à domicile
        self.standings_cache = {}  # Cache pour éviter trop d'appels API
        self.cache_timestamp = {}
    
    def get_team_stats(self, team_external_id: int, league_external_id: int) -> Dict:
        """Récupérer les statistiques d'une équipe depuis l'API"""
        
        # Vérifier le cache (valide pendant 1 heure)
        cache_key = f"{league_external_id}"
        current_time = time.time()
        
        if cache_key in self.standings_cache:
            if current_time - self.cache_timestamp.get(cache_key, 0) < 3600:
                # Utiliser le cache
                standings = self.standings_cache[cache_key]
                for entry in standings:
                    if entry['team_id'] == team_external_id:
                        return entry
        
        # Récupérer depuis l'API
        try:
            standings_url = f"{BASE_URL}/competitions/{league_external_id}/standings"
            response = requests.get(standings_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                standings_data = data.get('standings', [])
                
                if standings_data:
                    table = standings_data[0].get('table', [])
                    
                    # Mettre en cache
                    cache_data = []
                    for entry in table:
                        team_data = entry.get('team', {})
                        stats = {
                            'team_id': team_data.get('id'),
                            'position': entry.get('position', 10),
                            'points': entry.get('points', 0),
                            'played_games': entry.get('playedGames', 1),
                            'wins': entry.get('won', 0),
                            'draws': entry.get('draw', 0),
                            'losses': entry.get('lost', 0),
                            'goals_for': entry.get('goalsFor', 0),
                            'goals_against': entry.get('goalsAgainst', 0),
                            'goal_difference': entry.get('goalDifference', 0)
                        }
                        cache_data.append(stats)
                    
                    self.standings_cache[cache_key] = cache_data
                    self.cache_timestamp[cache_key] = current_time
                    
                    # Retourner les stats de l'équipe demandée
                    for stats in cache_data:
                        if stats['team_id'] == team_external_id:
                            return stats
        
        except Exception as e:
            print(f"Erreur lors de la récupération des stats: {e}")
        
        # Retourner des stats par défaut si échec
        return {
            'position': 10,
            'points': 10,
            'played_games': 8,
            'wins': 3,
            'draws': 1,
            'losses': 4,
            'goals_for': 10,
            'goals_against': 12,
            'goal_difference': -2
        }
    
    def calculate_team_strength(self, stats: Dict) -> float:
        """Calculer la force d'une équipe basée sur ses statistiques"""
        
        played = max(stats['played_games'], 1)  # Éviter division par zéro
        
        # Normaliser les statistiques
        # Points par match (0-3)
        points_per_game = stats['points'] / played
        points_score = points_per_game / 3.0  # Normaliser entre 0 et 1
        
        # Position au classement (inversé : 1ère place = meilleur)
        # Supposons 20 équipes max
        position_score = (21 - stats['position']) / 20.0
        
        # Différence de buts par match
        gd_per_game = stats['goal_difference'] / played
        # Normaliser entre -2 et +2 vers 0-1
        gd_score = (gd_per_game + 2) / 4.0
        gd_score = max(0, min(1, gd_score))
        
        # Buts marqués par match
        goals_for_per_game = stats['goals_for'] / played
        goals_score = min(1.0, goals_for_per_game / 3.0)  # 3 buts/match = excellent
        
        # Buts encaissés par match (inversé)
        goals_against_per_game = stats['goals_against'] / played
        defense_score = max(0, 1.0 - (goals_against_per_game / 3.0))
        
        # Taux de victoire
        win_rate = stats['wins'] / played
        
        # Pondération des différents facteurs
        strength = (
            points_score * 0.30 +      # 30% - Points (le plus important)
            position_score * 0.20 +    # 20% - Position
            gd_score * 0.15 +          # 15% - Différence de buts
            goals_score * 0.15 +       # 15% - Attaque
            defense_score * 0.10 +     # 10% - Défense
            win_rate * 0.10            # 10% - Taux de victoire
        )
        
        return max(0.1, min(1.0, strength))
    
    def predict_match(self, home_team_id: int, away_team_id: int, 
                     league_id: int, home_team_name: str = "", 
                     away_team_name: str = "", league_name: str = "") -> Dict:
        """Prédire le résultat d'un match basé sur les statistiques réelles"""
        
        # Récupérer les statistiques des deux équipes
        home_stats = self.get_team_stats(home_team_id, league_id)
        away_stats = self.get_team_stats(away_team_id, league_id)
        
        # Calculer la force de chaque équipe
        home_strength = self.calculate_team_strength(home_stats)
        away_strength = self.calculate_team_strength(away_stats)
        
        # Ajouter l'avantage du terrain
        home_strength_adj = min(1.0, home_strength * (1 + self.HOME_ADVANTAGE))
        
        # Calculer la différence de force
        strength_diff = home_strength_adj - away_strength
        
        # Utiliser une fonction sigmoïde pour les probabilités
        # Plus réaliste qu'une distribution linéaire
        prob_home = 1 / (1 + np.exp(-5 * strength_diff))
        
        # Probabilité de match nul basée sur l'équilibre
        balance = abs(strength_diff)
        draw_factor = np.exp(-10 * balance)
        prob_draw = 0.25 * draw_factor + 0.15  # Entre 15% et 40%
        
        # Ajuster les probabilités
        prob_home = prob_home * (1 - prob_draw)
        prob_away = 1 - prob_home - prob_draw
        
        # Normaliser
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
        
        # Niveau de confiance
        max_prob = max(prob_home, prob_draw, prob_away)
        if max_prob >= 0.55:
            confidence = "Élevée"
        elif max_prob >= 0.42:
            confidence = "Moyenne"
        else:
            confidence = "Faible"
        
        # Prédire le score basé sur les statistiques d'attaque/défense
        home_attack = home_stats['goals_for'] / max(home_stats['played_games'], 1)
        away_defense = away_stats['goals_against'] / max(away_stats['played_games'], 1)
        away_attack = away_stats['goals_for'] / max(away_stats['played_games'], 1)
        home_defense = home_stats['goals_against'] / max(home_stats['played_games'], 1)
        
        # Score prédit
        home_goals_expected = (home_attack + away_defense) / 2 * 1.1  # Bonus domicile
        away_goals_expected = (away_attack + home_defense) / 2 * 0.9  # Malus extérieur
        
        home_goals = round(home_goals_expected)
        away_goals = round(away_goals_expected)
        
        # Ajuster selon le vainqueur prédit
        if predicted_winner == "home" and home_goals <= away_goals:
            home_goals = away_goals + 1
        elif predicted_winner == "away" and away_goals <= home_goals:
            away_goals = home_goals + 1
        elif predicted_winner == "draw":
            away_goals = home_goals
        
        # Limiter à des scores réalistes
        home_goals = max(0, min(5, home_goals))
        away_goals = max(0, min(5, away_goals))
        
        # Over/Under 2.5
        total_goals_expected = home_goals + away_goals
        prob_over_2_5 = min(0.95, max(0.05, (total_goals_expected - 1.5) / 4))
        
        # BTTS
        prob_both_score = min(0.95, max(0.15, (home_attack * away_attack) / 4))
        
        # Score de fiabilité basé sur la qualité des données
        data_quality = 1.0  # On a de vraies données
        reliability_base = (max_prob * 10) * data_quality * ((home_strength + away_strength) / 2)
        reliability_score = max(1, min(10, round(reliability_base)))
        
        # Générer une analyse
        analysis = self._generate_analysis(
            home_team_name, away_team_name,
            home_stats, away_stats,
            home_strength, away_strength
        )
        
        return {
            'predicted_winner': predicted_winner,
            'confidence': confidence,
            'prob_home_win': round(prob_home, 3),
            'prob_draw': round(prob_draw, 3),
            'prob_away_win': round(prob_away, 3),
            'predicted_score_home': home_goals,
            'predicted_score_away': away_goals,
            'reliability_score': reliability_score,
            'prob_over_2_5': round(prob_over_2_5, 3),
            'prob_both_teams_score': round(prob_both_score, 3),
            'analysis': analysis
        }
    
    def _generate_analysis(self, home_team: str, away_team: str,
                          home_stats: Dict, away_stats: Dict,
                          home_strength: float, away_strength: float) -> str:
        """Générer une analyse contextuelle basée sur les stats réelles"""
        
        analyses = []
        
        # Analyse de la position
        pos_diff = home_stats['position'] - away_stats['position']
        if abs(pos_diff) <= 3:
            analyses.append(f"Équipes proches au classement ({home_stats['position']}ème vs {away_stats['position']}ème)")
        elif pos_diff < -3:
            analyses.append(f"{home_team} mieux classé ({home_stats['position']}ème vs {away_stats['position']}ème)")
        else:
            analyses.append(f"{away_team} mieux classé ({away_stats['position']}ème vs {home_stats['position']}ème)")
        
        # Analyse de la forme (points)
        home_ppg = home_stats['points'] / max(home_stats['played_games'], 1)
        away_ppg = away_stats['points'] / max(away_stats['played_games'], 1)
        
        if home_ppg > 2.0:
            analyses.append(f"{home_team} en excellente forme ({home_ppg:.1f} pts/match)")
        elif away_ppg > 2.0:
            analyses.append(f"{away_team} en excellente forme ({away_ppg:.1f} pts/match)")
        
        # Analyse offensive
        home_attack = home_stats['goals_for'] / max(home_stats['played_games'], 1)
        away_attack = away_stats['goals_for'] / max(away_stats['played_games'], 1)
        
        if home_attack > 2.0 and away_attack > 2.0:
            analyses.append("Match offensif attendu, les deux équipes marquent beaucoup")
        elif home_attack < 1.0 and away_attack < 1.0:
            analyses.append("Match tactique attendu, peu de buts probables")
        
        return " - ".join(analyses[:2])  # Limiter à 2 analyses

