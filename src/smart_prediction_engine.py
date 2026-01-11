import random
import math
from typing import Dict, Tuple

class SmartPredictionEngine:
    """Moteur de prédiction intelligent basé sur la réputation des équipes"""
    
    def __init__(self):
        # Base de données de réputation des équipes (0.0 à 1.0)
        # Basé sur les performances historiques et la réputation
        self.team_ratings = {
            # Premier League - Top équipes
            "Manchester City": 0.95, "Arsenal FC": 0.90, "Liverpool FC": 0.92,
            "Chelsea FC": 0.85, "Manchester United": 0.83, "Tottenham Hotspur FC": 0.82,
            "Newcastle United FC": 0.78, "Brighton & Hove Albion FC": 0.75,
            "Aston Villa FC": 0.74, "West Ham United FC": 0.72,
            "Fulham FC": 0.68, "Brentford FC": 0.67, "Crystal Palace FC": 0.66,
            "Nottingham Forest FC": 0.65, "AFC Bournemouth": 0.63,
            "Wolverhampton Wanderers FC": 0.62, "Everton FC": 0.60,
            "Leicester City FC": 0.61, "Leeds United FC": 0.59,
            "Burnley FC": 0.57, "Luton Town FC": 0.55, "Sheffield United FC": 0.54,
            "Sunderland AFC": 0.58, "Ipswich Town FC": 0.56,
            
            # Ligue 1
            "Paris Saint-Germain FC": 0.96, "AS Monaco FC": 0.82, "Olympique de Marseille": 0.81,
            "Olympique Lyonnais": 0.79, "Lille OSC": 0.78, "OGC Nice": 0.75,
            "RC Lens": 0.74, "Stade Rennais FC 1901": 0.73, "RC Strasbourg Alsace": 0.70,
            "Montpellier HSC": 0.68, "Stade de Reims": 0.67, "FC Nantes": 0.66,
            "Toulouse FC": 0.65, "AJ Auxerre": 0.63, "Angers SCO": 0.62,
            "Le Havre AC": 0.60, "FC Lorient": 0.59, "FC Metz": 0.58,
            
            # Bundesliga
            "FC Bayern München": 0.97, "Borussia Dortmund": 0.88, "RB Leipzig": 0.85,
            "Bayer 04 Leverkusen": 0.84, "VfL Wolfsburg": 0.76, "Eintracht Frankfurt": 0.75,
            "SC Freiburg": 0.73, "1. FC Union Berlin": 0.72, "Borussia Mönchengladbach": 0.71,
            "VfB Stuttgart": 0.74, "TSG 1899 Hoffenheim": 0.70, "1. FSV Mainz 05": 0.68,
            "FC Augsburg": 0.66, "SV Werder Bremen": 0.67, "VfL Bochum 1848": 0.62,
            "1. FC Köln": 0.64, "1. FC Heidenheim 1846": 0.61, "SV Darmstadt 98": 0.58,
            
            # Serie A
            "FC Internazionale Milano": 0.90, "SSC Napoli": 0.89, "AC Milan": 0.87,
            "Juventus FC": 0.88, "Atalanta BC": 0.83, "AS Roma": 0.82,
            "SS Lazio": 0.81, "ACF Fiorentina": 0.78, "Bologna FC 1909": 0.76,
            "Torino FC": 0.73, "Hellas Verona FC": 0.70, "Genoa CFC": 0.69,
            "Empoli FC": 0.67, "Udinese Calcio": 0.68, "US Lecce": 0.65,
            "Cagliari Calcio": 0.64, "Frosinone Calcio": 0.61, "US Salernitana 1919": 0.60,
            "US Sassuolo Calcio": 0.66, "AC Pisa 1909": 0.63,
            
            # LaLiga
            "Real Madrid CF": 0.96, "FC Barcelona": 0.94, "Atlético de Madrid": 0.87,
            "Real Sociedad de Fútbol": 0.80, "Real Betis Balompié": 0.78,
            "Villarreal CF": 0.79, "Athletic Club": 0.77, "Valencia CF": 0.75,
            "Sevilla FC": 0.76, "RC Celta de Vigo": 0.71, "Getafe CF": 0.70,
            "CA Osasuna": 0.69, "Rayo Vallecano de Madrid": 0.68, "RCD Mallorca": 0.67,
            "Girona FC": 0.72, "UD Almería": 0.62, "Cádiz CF": 0.61,
            "Granada CF": 0.63, "Real Valladolid CF": 0.64, "Elche CF": 0.60,
            "UD Las Palmas": 0.65, "Deportivo Alavés": 0.66, "Real Oviedo": 0.64,
            "SD Eibar": 0.63, "Espanyol": 0.67, "CD Leganés": 0.62,
            
            # Primeira Liga
            "SL Benfica": 0.89, "FC Porto": 0.88, "Sporting Clube de Portugal": 0.87,
            "SC Braga": 0.78, "Vitória SC": 0.72, "GD Estoril Praia": 0.68,
            "Rio Ave FC": 0.67, "FC Famalicão": 0.66, "Casa Pia AC": 0.64,
            "Portimonense SC": 0.63, "Gil Vicente FC": 0.65, "FC Arouca": 0.62,
        }
        
        self.HOME_ADVANTAGE = 0.12  # 12% d'avantage à domicile
    
    def get_team_rating(self, team_name: str) -> float:
        """Obtenir la note d'une équipe"""
        # Chercher une correspondance exacte ou partielle
        for known_team, rating in self.team_ratings.items():
            if known_team.lower() in team_name.lower() or team_name.lower() in known_team.lower():
                return rating
        
        # Si l'équipe n'est pas connue, retourner une valeur moyenne
        return 0.65
    
    def predict_match(self, home_team: str, away_team: str, league_name: str = "") -> Dict:
        """Prédire le résultat d'un match"""
        
        # Obtenir les notes des équipes
        home_rating = self.get_team_rating(home_team)
        away_rating = self.get_team_rating(away_team)
        
        # Ajouter l'avantage du terrain
        home_rating_adj = min(1.0, home_rating + self.HOME_ADVANTAGE)
        
        # Calculer la différence de force
        strength_diff = home_rating_adj - away_rating
        
        # Utiliser une fonction sigmoïde pour calculer les probabilités
        # Plus réaliste qu'une distribution linéaire
        prob_home = 1 / (1 + math.exp(-6 * strength_diff))
        
        # Calculer la probabilité de match nul
        # Les matchs équilibrés ont plus de chances de match nul
        balance = abs(strength_diff)
        draw_factor = math.exp(-12 * balance)
        prob_draw = 0.22 * draw_factor + 0.18  # Entre 18% et 40%
        
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
        
        # Calculer le niveau de confiance
        max_prob = max(prob_home, prob_draw, prob_away)
        if max_prob >= 0.55:
            confidence = "Élevée"
        elif max_prob >= 0.42:
            confidence = "Moyenne"
        else:
            confidence = "Faible"
        
        # Prédire le score basé sur les notes
        avg_rating = (home_rating + away_rating) / 2
        
        # Les équipes fortes marquent plus de buts
        home_goals_base = 1 + (home_rating * 2)
        away_goals_base = 1 + (away_rating * 2)
        
        # Ajuster selon la différence de force
        if strength_diff > 0.15:
            home_goals = round(home_goals_base + 0.5)
            away_goals = round(away_goals_base - 0.3)
        elif strength_diff < -0.15:
            home_goals = round(home_goals_base - 0.3)
            away_goals = round(away_goals_base + 0.5)
        else:
            home_goals = round(home_goals_base)
            away_goals = round(away_goals_base)
        
        # Ajuster selon le vainqueur prédit
        if predicted_winner == "home" and home_goals <= away_goals:
            home_goals = away_goals + 1
        elif predicted_winner == "away" and away_goals <= home_goals:
            away_goals = home_goals + 1
        elif predicted_winner == "draw":
            away_goals = home_goals
        
        # Limiter à des scores réalistes
        home_goals = max(0, min(4, home_goals))
        away_goals = max(0, min(4, away_goals))
        
        # Calculer over/under 2.5 et BTTS
        total_goals_expected = home_goals + away_goals
        prob_over_2_5 = min(0.95, max(0.05, (total_goals_expected - 1.5) / 4))
        
        # BTTS basé sur la force offensive des deux équipes
        prob_both_score = min(0.95, max(0.15, (home_rating * away_rating) * 1.2))
        
        # Calculer le score de fiabilité (1-10)
        # Basé sur la différence de force et la qualité des équipes
        reliability_base = (max_prob * 10) * ((home_rating + away_rating) / 2)
        reliability_score = max(1, min(10, round(reliability_base)))
        
        # Générer une analyse contextuelle
        analysis = self._generate_analysis(home_team, away_team, home_rating, away_rating, strength_diff)
        
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
    
    def _generate_analysis(self, home_team: str, away_team: str, home_rating: float, 
                          away_rating: float, strength_diff: float) -> str:
        """Générer une analyse contextuelle du match"""
        
        if abs(strength_diff) < 0.08:
            analyses = [
                "Match équilibré entre deux équipes de niveau similaire",
                "Duel serré attendu, l'avantage du terrain pourrait faire la différence",
                "Les deux formations sont au même niveau, match indécis"
            ]
        elif strength_diff > 0.15:
            analyses = [
                f"{home_team} présente un avantage significatif à domicile",
                f"La supériorité de {home_team} devrait se faire sentir",
                f"{home_team} favori logique face à {away_team}"
            ]
        elif strength_diff < -0.15:
            analyses = [
                f"{away_team} arrive en position de force malgré le déplacement",
                f"La qualité de {away_team} pourrait compenser l'avantage du terrain",
                f"{away_team} favori pour ce déplacement"
            ]
        else:
            analyses = [
                "Légère faveur pour l'équipe à domicile",
                "Match ouvert avec un petit avantage pour les locaux",
                "L'avantage du terrain pourrait être décisif"
            ]
        
        # Ajouter des commentaires sur l'intensité offensive
        avg_rating = (home_rating + away_rating) / 2
        if avg_rating > 0.85:
            analyses.append("Match de haut niveau avec du spectacle attendu")
        elif avg_rating < 0.65:
            analyses.append("Rencontre tactique entre deux équipes prudentes")
        
        return random.choice(analyses)

