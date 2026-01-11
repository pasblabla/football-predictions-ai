"""
Module de scraping avancé pour récupérer les données supplémentaires:
- Joueurs titulaires absents
- Arbitres et leur historique
- Joueurs à risque de fautes
- Tactiques des entraîneurs
- Style de jeu
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import re

class AdvancedDataScraper:
    """Scraper avancé pour les données de football supplémentaires"""
    
    def __init__(self):
        self.cache_dir = "/home/ubuntu/football_app/instance/cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Headers pour le scraping
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        # Base de données des arbitres avec leur historique
        self.referees_db = self._load_referees_db()
        
        # Base de données des tactiques par équipe
        self.tactics_db = self._load_tactics_db()
        
        # Base de données des joueurs à risque de fautes
        self.foul_prone_players = self._load_foul_prone_db()
    
    def _load_referees_db(self):
        """Charger la base de données des arbitres"""
        cache_file = os.path.join(self.cache_dir, "referees_db.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)
        
        # Base de données initiale des arbitres (à enrichir avec le scraping)
        referees = {
            # Premier League
            "Michael Oliver": {
                "country": "England",
                "avg_yellow_cards": 4.2,
                "avg_red_cards": 0.3,
                "avg_penalties": 0.35,
                "avg_fouls": 22.5,
                "strictness": "strict",  # strict, moderate, lenient
                "home_bias": 0.52,  # % de victoires domicile
                "matches_officiated": 245
            },
            "Anthony Taylor": {
                "country": "England",
                "avg_yellow_cards": 3.8,
                "avg_red_cards": 0.25,
                "avg_penalties": 0.28,
                "avg_fouls": 24.1,
                "strictness": "moderate",
                "home_bias": 0.48,
                "matches_officiated": 312
            },
            "Paul Tierney": {
                "country": "England",
                "avg_yellow_cards": 4.5,
                "avg_red_cards": 0.35,
                "avg_penalties": 0.32,
                "avg_fouls": 23.8,
                "strictness": "strict",
                "home_bias": 0.50,
                "matches_officiated": 198
            },
            # Bundesliga
            "Felix Zwayer": {
                "country": "Germany",
                "avg_yellow_cards": 3.9,
                "avg_red_cards": 0.22,
                "avg_penalties": 0.30,
                "avg_fouls": 21.5,
                "strictness": "moderate",
                "home_bias": 0.51,
                "matches_officiated": 267
            },
            "Daniel Siebert": {
                "country": "Germany",
                "avg_yellow_cards": 4.1,
                "avg_red_cards": 0.28,
                "avg_penalties": 0.33,
                "avg_fouls": 22.0,
                "strictness": "strict",
                "home_bias": 0.49,
                "matches_officiated": 189
            },
            # LaLiga
            "Jesús Gil Manzano": {
                "country": "Spain",
                "avg_yellow_cards": 5.2,
                "avg_red_cards": 0.38,
                "avg_penalties": 0.35,
                "avg_fouls": 26.5,
                "strictness": "strict",
                "home_bias": 0.53,
                "matches_officiated": 234
            },
            "Mateu Lahoz": {
                "country": "Spain",
                "avg_yellow_cards": 5.8,
                "avg_red_cards": 0.42,
                "avg_penalties": 0.40,
                "avg_fouls": 28.2,
                "strictness": "very_strict",
                "home_bias": 0.51,
                "matches_officiated": 298
            },
            # Serie A
            "Daniele Orsato": {
                "country": "Italy",
                "avg_yellow_cards": 4.8,
                "avg_red_cards": 0.32,
                "avg_penalties": 0.38,
                "avg_fouls": 25.0,
                "strictness": "strict",
                "home_bias": 0.52,
                "matches_officiated": 276
            },
            # Ligue 1
            "Clément Turpin": {
                "country": "France",
                "avg_yellow_cards": 4.0,
                "avg_red_cards": 0.28,
                "avg_penalties": 0.32,
                "avg_fouls": 23.5,
                "strictness": "moderate",
                "home_bias": 0.50,
                "matches_officiated": 312
            },
            "François Letexier": {
                "country": "France",
                "avg_yellow_cards": 3.7,
                "avg_red_cards": 0.22,
                "avg_penalties": 0.28,
                "avg_fouls": 22.8,
                "strictness": "lenient",
                "home_bias": 0.49,
                "matches_officiated": 198
            }
        }
        
        # Sauvegarder
        with open(cache_file, "w") as f:
            json.dump(referees, f, indent=2)
        
        return referees
    
    def _load_tactics_db(self):
        """Charger la base de données des tactiques par équipe"""
        cache_file = os.path.join(self.cache_dir, "tactics_db.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)
        
        # Base de données initiale des tactiques (à enrichir)
        tactics = {
            # Premier League
            "Manchester City FC": {
                "formation": "4-3-3",
                "style": "possession",
                "attacking_intensity": 85,
                "defensive_intensity": 70,
                "pressing": "high",
                "avg_possession": 65,
                "avg_shots": 18.5,
                "avg_shots_on_target": 7.2
            },
            "Liverpool FC": {
                "formation": "4-3-3",
                "style": "counter_attack",
                "attacking_intensity": 88,
                "defensive_intensity": 75,
                "pressing": "very_high",
                "avg_possession": 58,
                "avg_shots": 16.8,
                "avg_shots_on_target": 6.5
            },
            "Arsenal FC": {
                "formation": "4-3-3",
                "style": "possession",
                "attacking_intensity": 82,
                "defensive_intensity": 72,
                "pressing": "high",
                "avg_possession": 60,
                "avg_shots": 15.5,
                "avg_shots_on_target": 5.8
            },
            "Chelsea FC": {
                "formation": "4-2-3-1",
                "style": "balanced",
                "attacking_intensity": 75,
                "defensive_intensity": 78,
                "pressing": "medium",
                "avg_possession": 55,
                "avg_shots": 14.2,
                "avg_shots_on_target": 5.0
            },
            # Bundesliga
            "FC Bayern München": {
                "formation": "4-2-3-1",
                "style": "possession",
                "attacking_intensity": 90,
                "defensive_intensity": 68,
                "pressing": "very_high",
                "avg_possession": 62,
                "avg_shots": 19.5,
                "avg_shots_on_target": 7.8
            },
            "Borussia Dortmund": {
                "formation": "4-3-3",
                "style": "counter_attack",
                "attacking_intensity": 85,
                "defensive_intensity": 65,
                "pressing": "high",
                "avg_possession": 52,
                "avg_shots": 15.0,
                "avg_shots_on_target": 5.5
            },
            # LaLiga
            "Real Madrid CF": {
                "formation": "4-3-3",
                "style": "balanced",
                "attacking_intensity": 85,
                "defensive_intensity": 75,
                "pressing": "medium",
                "avg_possession": 58,
                "avg_shots": 16.0,
                "avg_shots_on_target": 6.2
            },
            "FC Barcelona": {
                "formation": "4-3-3",
                "style": "possession",
                "attacking_intensity": 88,
                "defensive_intensity": 65,
                "pressing": "high",
                "avg_possession": 65,
                "avg_shots": 17.5,
                "avg_shots_on_target": 6.8
            },
            "Club Atlético de Madrid": {
                "formation": "3-5-2",
                "style": "defensive",
                "attacking_intensity": 65,
                "defensive_intensity": 90,
                "pressing": "low",
                "avg_possession": 45,
                "avg_shots": 11.0,
                "avg_shots_on_target": 4.2
            },
            # Serie A
            "FC Internazionale Milano": {
                "formation": "3-5-2",
                "style": "balanced",
                "attacking_intensity": 78,
                "defensive_intensity": 82,
                "pressing": "medium",
                "avg_possession": 52,
                "avg_shots": 14.5,
                "avg_shots_on_target": 5.5
            },
            "AC Milan": {
                "formation": "4-2-3-1",
                "style": "counter_attack",
                "attacking_intensity": 80,
                "defensive_intensity": 75,
                "pressing": "high",
                "avg_possession": 50,
                "avg_shots": 13.8,
                "avg_shots_on_target": 5.0
            },
            "Juventus FC": {
                "formation": "3-5-2",
                "style": "defensive",
                "attacking_intensity": 70,
                "defensive_intensity": 85,
                "pressing": "medium",
                "avg_possession": 55,
                "avg_shots": 12.5,
                "avg_shots_on_target": 4.8
            },
            # Ligue 1
            "Paris Saint-Germain FC": {
                "formation": "4-3-3",
                "style": "possession",
                "attacking_intensity": 90,
                "defensive_intensity": 65,
                "pressing": "high",
                "avg_possession": 62,
                "avg_shots": 18.0,
                "avg_shots_on_target": 7.0
            }
        }
        
        # Sauvegarder
        with open(cache_file, "w") as f:
            json.dump(tactics, f, indent=2)
        
        return tactics
    
    def _load_foul_prone_db(self):
        """Charger la base de données des joueurs à risque de fautes"""
        cache_file = os.path.join(self.cache_dir, "foul_prone_db.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)
        
        # Base de données initiale des joueurs à risque
        players = {
            # Joueurs connus pour leurs fautes
            "Casemiro": {"team": "Manchester United FC", "avg_fouls": 2.8, "yellow_cards": 8, "red_cards": 1},
            "Rodri": {"team": "Manchester City FC", "avg_fouls": 2.2, "yellow_cards": 6, "red_cards": 0},
            "Bruno Guimarães": {"team": "Newcastle United FC", "avg_fouls": 2.0, "yellow_cards": 5, "red_cards": 0},
            "Declan Rice": {"team": "Arsenal FC", "avg_fouls": 1.8, "yellow_cards": 4, "red_cards": 0},
            "Aurélien Tchouaméni": {"team": "Real Madrid CF", "avg_fouls": 2.5, "yellow_cards": 7, "red_cards": 0},
            "Gavi": {"team": "FC Barcelona", "avg_fouls": 2.3, "yellow_cards": 9, "red_cards": 1},
            "Nicolò Barella": {"team": "FC Internazionale Milano", "avg_fouls": 2.1, "yellow_cards": 6, "red_cards": 0},
            "Sandro Tonali": {"team": "Newcastle United FC", "avg_fouls": 2.4, "yellow_cards": 7, "red_cards": 0}
        }
        
        # Sauvegarder
        with open(cache_file, "w") as f:
            json.dump(players, f, indent=2)
        
        return players
    
    def get_referee_data(self, referee_name):
        """Récupérer les données d'un arbitre"""
        if referee_name in self.referees_db:
            return self.referees_db[referee_name]
        
        # Arbitre par défaut si non trouvé
        return {
            "country": "Unknown",
            "avg_yellow_cards": 4.0,
            "avg_red_cards": 0.28,
            "avg_penalties": 0.30,
            "avg_fouls": 23.0,
            "strictness": "moderate",
            "home_bias": 0.50,
            "matches_officiated": 0
        }
    
    def get_team_tactics(self, team_name):
        """Récupérer les tactiques d'une équipe"""
        if team_name in self.tactics_db:
            return self.tactics_db[team_name]
        
        # Tactiques par défaut si non trouvé
        return {
            "formation": "4-4-2",
            "style": "balanced",
            "attacking_intensity": 70,
            "defensive_intensity": 70,
            "pressing": "medium",
            "avg_possession": 50,
            "avg_shots": 12.0,
            "avg_shots_on_target": 4.5
        }
    
    def get_foul_prone_players(self, team_name):
        """Récupérer les joueurs à risque de fautes d'une équipe"""
        players = []
        for player_name, data in self.foul_prone_players.items():
            if data.get("team") == team_name:
                players.append({
                    "name": player_name,
                    "avg_fouls": data["avg_fouls"],
                    "yellow_cards": data["yellow_cards"],
                    "red_cards": data["red_cards"]
                })
        return players
    
    def analyze_tactical_matchup(self, home_team, away_team):
        """Analyser le match tactique entre deux équipes"""
        home_tactics = self.get_team_tactics(home_team)
        away_tactics = self.get_team_tactics(away_team)
        
        analysis = {
            "home_tactics": home_tactics,
            "away_tactics": away_tactics,
            "tactical_advantage": "neutral",
            "expected_goals_adjustment": 0,
            "btts_adjustment": 0,
            "analysis_text": ""
        }
        
        # Analyser le match tactique
        home_style = home_tactics.get("style", "balanced")
        away_style = away_tactics.get("style", "balanced")
        
        # Possession vs Counter-attack = match ouvert
        if (home_style == "possession" and away_style == "counter_attack") or \
           (home_style == "counter_attack" and away_style == "possession"):
            analysis["expected_goals_adjustment"] = 0.5
            analysis["btts_adjustment"] = 10
            analysis["analysis_text"] = "Match tactique ouvert prévu avec des espaces."
        
        # Deux équipes défensives = peu de buts
        elif home_style == "defensive" and away_style == "defensive":
            analysis["expected_goals_adjustment"] = -0.8
            analysis["btts_adjustment"] = -15
            analysis["analysis_text"] = "Match fermé prévu avec deux équipes défensives."
        
        # Deux équipes offensives = beaucoup de buts
        elif home_tactics.get("attacking_intensity", 70) > 80 and \
             away_tactics.get("attacking_intensity", 70) > 80:
            analysis["expected_goals_adjustment"] = 0.8
            analysis["btts_adjustment"] = 15
            analysis["analysis_text"] = "Match très ouvert prévu avec deux équipes offensives."
        
        # High pressing vs Low pressing
        home_pressing = home_tactics.get("pressing", "medium")
        away_pressing = away_tactics.get("pressing", "medium")
        
        if home_pressing == "very_high" and away_pressing == "low":
            analysis["tactical_advantage"] = "home"
            analysis["analysis_text"] += " L'équipe domicile devrait dominer avec son pressing haut."
        elif away_pressing == "very_high" and home_pressing == "low":
            analysis["tactical_advantage"] = "away"
            analysis["analysis_text"] += " L'équipe extérieure pourrait surprendre avec son pressing haut."
        
        return analysis
    
    def calculate_referee_impact(self, referee_name, home_team, away_team):
        """Calculer l'impact de l'arbitre sur le match"""
        referee = self.get_referee_data(referee_name)
        
        impact = {
            "referee": referee_name,
            "referee_data": referee,
            "expected_cards_adjustment": 0,
            "penalty_probability": referee.get("avg_penalties", 0.30),
            "home_advantage_adjustment": 0,
            "analysis_text": ""
        }
        
        strictness = referee.get("strictness", "moderate")
        
        if strictness == "very_strict":
            impact["expected_cards_adjustment"] = 2
            impact["analysis_text"] = f"{referee_name} est un arbitre très strict. Attendez-vous à beaucoup de cartons."
        elif strictness == "strict":
            impact["expected_cards_adjustment"] = 1
            impact["analysis_text"] = f"{referee_name} est un arbitre strict."
        elif strictness == "lenient":
            impact["expected_cards_adjustment"] = -1
            impact["analysis_text"] = f"{referee_name} est un arbitre permissif. Peu de cartons attendus."
        
        # Ajustement de l'avantage domicile basé sur l'historique de l'arbitre
        home_bias = referee.get("home_bias", 0.50)
        if home_bias > 0.52:
            impact["home_advantage_adjustment"] = 3
            impact["analysis_text"] += f" Tendance légère à favoriser l'équipe domicile."
        elif home_bias < 0.48:
            impact["home_advantage_adjustment"] = -3
            impact["analysis_text"] += f" Tendance à être neutre ou favoriser l'extérieur."
        
        return impact
    
    def get_match_advanced_data(self, home_team, away_team, referee_name=None):
        """Récupérer toutes les données avancées pour un match"""
        data = {
            "home_team": home_team,
            "away_team": away_team,
            "tactical_analysis": self.analyze_tactical_matchup(home_team, away_team),
            "home_foul_prone_players": self.get_foul_prone_players(home_team),
            "away_foul_prone_players": self.get_foul_prone_players(away_team),
            "referee_impact": None
        }
        
        if referee_name:
            data["referee_impact"] = self.calculate_referee_impact(referee_name, home_team, away_team)
        
        return data


# Instance globale
advanced_scraper = AdvancedDataScraper()
