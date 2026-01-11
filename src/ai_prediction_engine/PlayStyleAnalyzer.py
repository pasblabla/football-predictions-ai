"""
Module d'Analyse du Style de Jeu v1.0
-------------------------------------
Analyse le style de jeu des équipes pour améliorer les prédictions:
- Style défensif vs offensif
- Efficacité en contre-attaque
- Capacité à tenir un résultat
- Probabilité de surprise (upset)
"""

import hashlib
import random

class PlayStyleAnalyzer:
    """Analyseur du style de jeu des équipes"""
    
    def __init__(self):
        # Équipes connues pour leur style défensif solide
        self.defensive_teams = {
            # Premier League
            'Brighton': {'defense': 0.75, 'counter': 0.70, 'upset_factor': 0.65},
            'Crystal Palace': {'defense': 0.72, 'counter': 0.68, 'upset_factor': 0.60},
            'Brentford': {'defense': 0.70, 'counter': 0.75, 'upset_factor': 0.70},
            'Wolves': {'defense': 0.78, 'counter': 0.72, 'upset_factor': 0.55},
            'Wolverhampton': {'defense': 0.78, 'counter': 0.72, 'upset_factor': 0.55},
            'Bournemouth': {'defense': 0.68, 'counter': 0.65, 'upset_factor': 0.55},
            'Fulham': {'defense': 0.70, 'counter': 0.60, 'upset_factor': 0.50},
            'Everton': {'defense': 0.72, 'counter': 0.55, 'upset_factor': 0.45},
            'Newcastle': {'defense': 0.75, 'counter': 0.70, 'upset_factor': 0.60},
            'Nottingham': {'defense': 0.68, 'counter': 0.62, 'upset_factor': 0.50},
            
            # LaLiga
            'Getafe': {'defense': 0.80, 'counter': 0.65, 'upset_factor': 0.70},
            'Atletico': {'defense': 0.82, 'counter': 0.75, 'upset_factor': 0.65},
            'Villarreal': {'defense': 0.72, 'counter': 0.70, 'upset_factor': 0.55},
            'Real Sociedad': {'defense': 0.70, 'counter': 0.68, 'upset_factor': 0.55},
            'Osasuna': {'defense': 0.75, 'counter': 0.60, 'upset_factor': 0.60},
            'Rayo': {'defense': 0.72, 'counter': 0.70, 'upset_factor': 0.65},
            
            # Serie A
            'Inter': {'defense': 0.80, 'counter': 0.78, 'upset_factor': 0.40},
            'Juventus': {'defense': 0.78, 'counter': 0.72, 'upset_factor': 0.45},
            'Torino': {'defense': 0.75, 'counter': 0.65, 'upset_factor': 0.60},
            'Bologna': {'defense': 0.72, 'counter': 0.68, 'upset_factor': 0.55},
            'Udinese': {'defense': 0.74, 'counter': 0.62, 'upset_factor': 0.55},
            'Empoli': {'defense': 0.70, 'counter': 0.58, 'upset_factor': 0.50},
            
            # Bundesliga
            'Union Berlin': {'defense': 0.75, 'counter': 0.70, 'upset_factor': 0.65},
            'Freiburg': {'defense': 0.72, 'counter': 0.65, 'upset_factor': 0.55},
            'Mainz': {'defense': 0.70, 'counter': 0.62, 'upset_factor': 0.55},
            'Augsburg': {'defense': 0.68, 'counter': 0.60, 'upset_factor': 0.50},
            
            # Ligue 1
            'Reims': {'defense': 0.75, 'counter': 0.68, 'upset_factor': 0.60},
            'Lens': {'defense': 0.72, 'counter': 0.70, 'upset_factor': 0.55},
            'Brest': {'defense': 0.70, 'counter': 0.72, 'upset_factor': 0.65},
            'Montpellier': {'defense': 0.68, 'counter': 0.60, 'upset_factor': 0.50},
        }
        
        # Équipes connues pour leur style offensif (vulnérables aux contres)
        self.offensive_teams = {
            'Manchester City': {'attack': 0.92, 'defense_weakness': 0.25, 'counter_vulnerable': 0.35},
            'Liverpool': {'attack': 0.90, 'defense_weakness': 0.20, 'counter_vulnerable': 0.30},
            'Arsenal': {'attack': 0.88, 'defense_weakness': 0.22, 'counter_vulnerable': 0.32},
            'Barcelona': {'attack': 0.90, 'defense_weakness': 0.28, 'counter_vulnerable': 0.40},
            'Real Madrid': {'attack': 0.88, 'defense_weakness': 0.25, 'counter_vulnerable': 0.35},
            'Bayern': {'attack': 0.90, 'defense_weakness': 0.30, 'counter_vulnerable': 0.38},
            'PSG': {'attack': 0.88, 'defense_weakness': 0.32, 'counter_vulnerable': 0.42},
            'Napoli': {'attack': 0.85, 'defense_weakness': 0.28, 'counter_vulnerable': 0.35},
            'Dortmund': {'attack': 0.85, 'defense_weakness': 0.35, 'counter_vulnerable': 0.45},
            'Chelsea': {'attack': 0.82, 'defense_weakness': 0.30, 'counter_vulnerable': 0.38},
            'Tottenham': {'attack': 0.82, 'defense_weakness': 0.32, 'counter_vulnerable': 0.40},
            'Manchester United': {'attack': 0.80, 'defense_weakness': 0.35, 'counter_vulnerable': 0.42},
            'AC Milan': {'attack': 0.82, 'defense_weakness': 0.30, 'counter_vulnerable': 0.38},
            'Roma': {'attack': 0.78, 'defense_weakness': 0.32, 'counter_vulnerable': 0.40},
        }
    
    def _get_team_style(self, team_name):
        """Obtenir le style de jeu d'une équipe"""
        # Vérifier si c'est une équipe défensive connue
        for team, style in self.defensive_teams.items():
            if team.lower() in team_name.lower():
                return {
                    'type': 'defensive',
                    'defense_rating': style['defense'],
                    'counter_rating': style['counter'],
                    'upset_factor': style['upset_factor'],
                    'attack_rating': 0.55,  # Équipes défensives moins offensives
                }
        
        # Vérifier si c'est une équipe offensive connue
        for team, style in self.offensive_teams.items():
            if team.lower() in team_name.lower():
                return {
                    'type': 'offensive',
                    'defense_rating': 1 - style['defense_weakness'],
                    'counter_rating': 0.50,  # Équipes offensives moins bonnes en contre
                    'upset_factor': 0.30,  # Rarement surprises
                    'attack_rating': style['attack'],
                    'counter_vulnerable': style['counter_vulnerable'],
                }
        
        # Équipe inconnue - générer un style basé sur le hash
        seed = int(hashlib.md5(f"{team_name}_style".encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        return {
            'type': 'balanced',
            'defense_rating': random.uniform(0.55, 0.72),
            'counter_rating': random.uniform(0.50, 0.68),
            'upset_factor': random.uniform(0.40, 0.60),
            'attack_rating': random.uniform(0.55, 0.75),
        }
    
    def analyze_matchup(self, home_team, away_team, home_prob, away_prob, draw_prob):
        """
        Analyser le match-up entre deux équipes et ajuster les probabilités
        
        Retourne:
        - adjusted_home_prob: Probabilité ajustée pour domicile
        - adjusted_away_prob: Probabilité ajustée pour extérieur
        - adjusted_draw_prob: Probabilité ajustée pour nul
        - analysis: Analyse textuelle du match-up
        """
        home_style = self._get_team_style(home_team)
        away_style = self._get_team_style(away_team)
        
        adjustments = {
            'home': 0,
            'away': 0,
            'draw': 0,
        }
        analysis_points = []
        
        # Cas 1: Équipe offensive vs équipe défensive
        # L'équipe défensive a plus de chances de tenir le nul ou gagner en contre
        if home_style['type'] == 'offensive' and away_style['type'] == 'defensive':
            # L'équipe à l'extérieur (défensive) peut surprendre
            counter_threat = away_style['counter_rating'] * home_style.get('counter_vulnerable', 0.35)
            
            if counter_threat > 0.25:
                # Augmenter les chances de l'équipe défensive
                adjustments['away'] += counter_threat * 15  # +3 à +10%
                adjustments['draw'] += away_style['defense_rating'] * 8  # +4 à +6%
                adjustments['home'] -= (adjustments['away'] + adjustments['draw']) / 2
                
                analysis_points.append(f"{away_team} a une bonne défense et peut contrer")
        
        elif away_style['type'] == 'offensive' and home_style['type'] == 'defensive':
            # L'équipe à domicile (défensive) peut tenir et contrer
            counter_threat = home_style['counter_rating'] * away_style.get('counter_vulnerable', 0.35)
            
            if counter_threat > 0.25:
                adjustments['home'] += counter_threat * 12
                adjustments['draw'] += home_style['defense_rating'] * 6
                adjustments['away'] -= (adjustments['home'] + adjustments['draw']) / 2
                
                analysis_points.append(f"{home_team} peut tenir et contrer")
        
        # Cas 2: Deux équipes défensives = plus de chances de nul
        if home_style['type'] == 'defensive' and away_style['type'] == 'defensive':
            avg_defense = (home_style['defense_rating'] + away_style['defense_rating']) / 2
            adjustments['draw'] += avg_defense * 10  # +5 à +8%
            adjustments['home'] -= adjustments['draw'] / 2
            adjustments['away'] -= adjustments['draw'] / 2
            
            analysis_points.append("Deux équipes défensives - match fermé probable")
        
        # Cas 3: Équipe avec fort potentiel de surprise
        if away_style['upset_factor'] > 0.55 and home_prob > 55:
            # L'équipe à l'extérieur peut créer la surprise
            upset_boost = (away_style['upset_factor'] - 0.50) * 20
            adjustments['away'] += upset_boost
            adjustments['draw'] += upset_boost / 2
            adjustments['home'] -= upset_boost * 1.2
            
            analysis_points.append(f"{away_team} capable de créer la surprise")
        
        # Cas 4: Match équilibré avec bonnes défenses = nul probable
        if abs(home_prob - away_prob) < 15:
            avg_defense = (home_style['defense_rating'] + away_style['defense_rating']) / 2
            if avg_defense > 0.68:
                adjustments['draw'] += (avg_defense - 0.65) * 15
                adjustments['home'] -= adjustments['draw'] / 2
                adjustments['away'] -= adjustments['draw'] / 2
                
                analysis_points.append("Match équilibré avec bonnes défenses")
        
        # Appliquer les ajustements
        adjusted_home = home_prob + adjustments['home']
        adjusted_away = away_prob + adjustments['away']
        adjusted_draw = draw_prob + adjustments['draw']
        
        # Normaliser pour que le total = 100
        total = adjusted_home + adjusted_away + adjusted_draw
        adjusted_home = round(adjusted_home / total * 100, 1)
        adjusted_away = round(adjusted_away / total * 100, 1)
        adjusted_draw = round(100 - adjusted_home - adjusted_away, 1)
        
        # Générer l'analyse
        if analysis_points:
            analysis = ". ".join(analysis_points) + "."
        else:
            analysis = "Match standard sans facteur de style particulier."
        
        return {
            'home_prob': adjusted_home,
            'away_prob': adjusted_away,
            'draw_prob': adjusted_draw,
            'analysis': analysis,
            'home_style': home_style['type'],
            'away_style': away_style['type'],
            'adjustments': adjustments,
        }
    
    def get_upset_probability(self, favorite_team, underdog_team, favorite_prob):
        """
        Calculer la probabilité qu'une équipe moins favorite crée la surprise
        """
        underdog_style = self._get_team_style(underdog_team)
        favorite_style = self._get_team_style(favorite_team)
        
        base_upset = 100 - favorite_prob
        
        # Facteurs qui augmentent la probabilité de surprise
        upset_boost = 0
        
        # Équipe défensive avec bon contre
        if underdog_style['type'] == 'defensive':
            upset_boost += underdog_style['counter_rating'] * 10
        
        # Favori vulnérable aux contres
        if favorite_style['type'] == 'offensive':
            upset_boost += favorite_style.get('counter_vulnerable', 0.30) * 15
        
        # Facteur de surprise intrinsèque
        upset_boost += (underdog_style['upset_factor'] - 0.50) * 20
        
        return min(base_upset + upset_boost, 45)  # Max 45% de chance de surprise


# Instance globale
play_style_analyzer = PlayStyleAnalyzer()
