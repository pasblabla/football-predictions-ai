"""
Module de scraping pour récupérer les données statistiques depuis FlashScore et SoccerStats.
Ce module récupère:
- Joueurs absents/blessés
- Forme récente des équipes
- Statistiques détaillées
- Historique des confrontations (H2H)
- Top buteurs
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timedelta
import time

class FlashScoreScraper:
    """Scraper pour FlashScore - récupère les absences et compositions"""
    
    BASE_URL = "https://www.flashscore.fr"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    # Mapping des équipes vers leurs IDs FlashScore
    TEAM_IDS = {
        'Manchester City FC': 'manchester-city-Wtn9Stg0',
        'Manchester United FC': 'manchester-utd-ppjDR086',
        'Liverpool FC': 'liverpool-lId5jAQg',
        'Arsenal FC': 'arsenal-WOnh52Ae',
        'Chelsea FC': 'chelsea-lDKMrpCl',
        'Aston Villa FC': 'aston-villa-W00wmLO0',
        'Newcastle United FC': 'newcastle-utd-p6ahwuwJ',
        'Tottenham Hotspur FC': 'tottenham-xCKvhqBJ',
        'Brighton & Hove Albion FC': 'brighton-AJvPmqRK',
        'West Ham United FC': 'west-ham-Qn0bMYF0',
        'Brentford FC': 'brentford-QDYjz9og',
        'Wolverhampton Wanderers FC': 'wolverhampton-4Z3iAs7S',
        'Crystal Palace FC': 'crystal-palace-KPFpK6Ek',
        'Fulham FC': 'fulham-xvXqXqxq',
        'Everton FC': 'everton-SjH1hbGf',
        'Nottingham Forest FC': 'nottm-forest-Yqij7hQG',
        'AFC Bournemouth': 'bournemouth-KbpbLv0B',
        'Burnley FC': 'burnley-WjSbKQhD',
        # Bundesliga
        'FC Bayern München': 'bayern-munich-SKbpVP5K',
        'Borussia Dortmund': 'dortmund-IKwvYKcA',
        'RB Leipzig': 'rb-leipzig-W0xOa9C5',
        'Bayer 04 Leverkusen': 'leverkusen-tpIHnOMe',
        # Serie A
        'Juventus FC': 'juventus-xYmwlz7A',
        'AC Milan': 'ac-milan-xVfzqwpU',
        'FC Internazionale Milano': 'inter-milan-ACz9ZHYB',
        'SSC Napoli': 'napoli-hMGvsSa0',
        'AS Roma': 'roma-4KQ1dY0B',
        # LaLiga
        'Real Madrid CF': 'real-madrid-Lsb9hYX0',
        'FC Barcelona': 'barcelona-ltB4N5Ul',
        'Atlético de Madrid': 'atl-madrid-Wjp9Yjxq',
        # Ligue 1
        'Paris Saint-Germain FC': 'paris-sg-lQqrP7CK',
        'Olympique de Marseille': 'marseille-4SFVhSCl',
        'AS Monaco FC': 'monaco-8FHvJzLf',
        'Olympique Lyonnais': 'lyon-GxWPH1Yl',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_match_absences(self, home_team: str, away_team: str) -> dict:
        """
        Récupère les joueurs absents pour un match donné.
        
        Returns:
            dict: {
                'home_absences': [{'name': str, 'reason': str, 'type': str}],
                'away_absences': [{'name': str, 'reason': str, 'type': str}],
                'home_uncertain': [{'name': str, 'reason': str}],
                'away_uncertain': [{'name': str, 'reason': str}]
            }
        """
        result = {
            'home_absences': [],
            'away_absences': [],
            'home_uncertain': [],
            'away_uncertain': []
        }
        
        # Construire l'URL du match
        home_id = self.TEAM_IDS.get(home_team, '')
        away_id = self.TEAM_IDS.get(away_team, '')
        
        if not home_id or not away_id:
            print(f"IDs non trouvés pour {home_team} ou {away_team}")
            return result
        
        # Note: FlashScore utilise JavaScript pour charger les données
        # Une approche plus robuste serait d'utiliser Selenium ou Playwright
        # Pour l'instant, on retourne des données basées sur l'API football-data.org
        
        return result
    
    def get_team_form(self, team_name: str) -> list:
        """
        Récupère la forme récente d'une équipe (5 derniers matchs).
        
        Returns:
            list: ['V', 'V', 'N', 'D', 'V'] (V=Victoire, N=Nul, D=Défaite)
        """
        # Placeholder - à implémenter avec scraping réel
        return []


class SoccerStatsScraper:
    """Scraper pour SoccerStats - récupère les statistiques détaillées"""
    
    BASE_URL = "https://www.soccerstats.com"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    # Mapping des ligues vers leurs codes SoccerStats
    LEAGUE_CODES = {
        'PL': 'england',
        'BL1': 'germany',
        'SA': 'italy',
        'PD': 'spain',
        'FL1': 'france',
        'DED': 'netherlands',
        'PPL': 'portugal',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_match_stats(self, home_team: str, away_team: str, league_code: str) -> dict:
        """
        Récupère les statistiques détaillées pour un match.
        
        Returns:
            dict: {
                'home_stats': {...},
                'away_stats': {...},
                'h2h': [...],
                'trends': {...}
            }
        """
        league = self.LEAGUE_CODES.get(league_code, 'england')
        
        result = {
            'home_stats': {},
            'away_stats': {},
            'h2h': [],
            'trends': {
                'home_positive': [],
                'home_negative': [],
                'away_positive': [],
                'away_negative': []
            }
        }
        
        try:
            # Récupérer la page des matchs
            url = f"{self.BASE_URL}/matches.asp?matchday=1&league={league}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Parser les statistiques...
                # Note: Implémentation complète nécessite analyse détaillée du HTML
                
        except Exception as e:
            print(f"Erreur lors du scraping SoccerStats: {e}")
        
        return result
    
    def get_team_statistics(self, team_name: str, league_code: str) -> dict:
        """
        Récupère les statistiques complètes d'une équipe.
        
        Returns:
            dict: {
                'ppg_home': float,
                'ppg_away': float,
                'ppg_total': float,
                'goals_scored_avg': float,
                'goals_conceded_avg': float,
                'clean_sheet_rate': float,
                'scoring_rate': float,
                'win_rate': float,
                'form': list
            }
        """
        return {
            'ppg_home': 0.0,
            'ppg_away': 0.0,
            'ppg_total': 0.0,
            'goals_scored_avg': 0.0,
            'goals_conceded_avg': 0.0,
            'clean_sheet_rate': 0.0,
            'scoring_rate': 0.0,
            'win_rate': 0.0,
            'form': []
        }


class FootballDataEnricher:
    """
    Classe principale qui combine les données de l'API football-data.org
    avec les données scrapées de FlashScore et SoccerStats.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_base_url = "https://api.football-data.org/v4"
        self.flashscore = FlashScoreScraper()
        self.soccerstats = SoccerStatsScraper()
        
        self.headers = {
            'X-Auth-Token': api_key
        }
    
    def get_team_squad(self, team_id: int) -> list:
        """Récupère l'effectif complet d'une équipe depuis l'API."""
        try:
            url = f"{self.api_base_url}/teams/{team_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                squad = data.get('squad', [])
                return [
                    {
                        'id': player.get('id'),
                        'name': player.get('name'),
                        'position': player.get('position'),
                        'nationality': player.get('nationality')
                    }
                    for player in squad
                ]
        except Exception as e:
            print(f"Erreur lors de la récupération de l'effectif: {e}")
        
        return []
    
    def get_top_scorers(self, competition_code: str, limit: int = 10) -> list:
        """Récupère les meilleurs buteurs d'une compétition."""
        try:
            url = f"{self.api_base_url}/competitions/{competition_code}/scorers?limit={limit}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                scorers = data.get('scorers', [])
                return [
                    {
                        'player_name': s['player']['name'],
                        'team_name': s['team']['name'],
                        'goals': s.get('goals', 0),
                        'assists': s.get('assists', 0),
                        'penalties': s.get('penalties', 0)
                    }
                    for s in scorers
                ]
        except Exception as e:
            print(f"Erreur lors de la récupération des buteurs: {e}")
        
        return []
    
    def enrich_match_data(self, match: dict) -> dict:
        """
        Enrichit les données d'un match avec les informations scrapées.
        
        Args:
            match: dict contenant les infos de base du match (de l'API)
        
        Returns:
            dict: Match enrichi avec absences, stats, etc.
        """
        home_team = match.get('homeTeam', {}).get('name', '')
        away_team = match.get('awayTeam', {}).get('name', '')
        competition = match.get('competition', {}).get('code', 'PL')
        
        # Récupérer les absences depuis FlashScore
        absences = self.flashscore.get_match_absences(home_team, away_team)
        
        # Récupérer les statistiques depuis SoccerStats
        stats = self.soccerstats.get_match_stats(home_team, away_team, competition)
        
        # Récupérer les effectifs depuis l'API
        home_team_id = match.get('homeTeam', {}).get('id')
        away_team_id = match.get('awayTeam', {}).get('id')
        
        home_squad = self.get_team_squad(home_team_id) if home_team_id else []
        away_squad = self.get_team_squad(away_team_id) if away_team_id else []
        
        # Récupérer les buteurs de la compétition
        top_scorers = self.get_top_scorers(competition)
        
        # Identifier les buteurs probables pour chaque équipe
        home_scorers = [s for s in top_scorers if s['team_name'] == home_team][:3]
        away_scorers = [s for s in top_scorers if s['team_name'] == away_team][:3]
        
        # Enrichir le match
        enriched = match.copy()
        enriched['absences'] = absences
        enriched['statistics'] = stats
        enriched['home_squad'] = home_squad
        enriched['away_squad'] = away_squad
        enriched['probable_scorers'] = {
            'home': home_scorers,
            'away': away_scorers
        }
        
        return enriched


# Fonction utilitaire pour récupérer les données enrichies
def get_enriched_matches(api_key: str, competition_codes: list = None) -> list:
    """
    Récupère et enrichit tous les matchs à venir.
    
    Args:
        api_key: Clé API football-data.org
        competition_codes: Liste des codes de compétition (ex: ['PL', 'BL1'])
    
    Returns:
        list: Liste des matchs enrichis
    """
    if competition_codes is None:
        competition_codes = ['PL', 'BL1', 'SA', 'PD', 'FL1']
    
    enricher = FootballDataEnricher(api_key)
    enriched_matches = []
    
    for code in competition_codes:
        try:
            url = f"https://api.football-data.org/v4/competitions/{code}/matches?status=SCHEDULED"
            response = requests.get(url, headers={'X-Auth-Token': api_key}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                
                for match in matches[:5]:  # Limiter pour éviter trop de requêtes
                    enriched = enricher.enrich_match_data(match)
                    enriched_matches.append(enriched)
                    time.sleep(0.5)  # Respecter les limites de taux
                    
        except Exception as e:
            print(f"Erreur pour la compétition {code}: {e}")
    
    return enriched_matches


if __name__ == "__main__":
    # Test du scraper
    API_KEY = "647c75a7ce7f482598c8240664bd856c"
    
    enricher = FootballDataEnricher(API_KEY)
    
    # Test récupération des buteurs
    print("=== Top Buteurs Premier League ===")
    scorers = enricher.get_top_scorers('PL', 5)
    for s in scorers:
        print(f"{s['player_name']} ({s['team_name']}) - {s['goals']} buts")
    
    # Test récupération de l'effectif
    print("\n=== Effectif Manchester City ===")
    squad = enricher.get_team_squad(65)  # ID de Man City
    for player in squad[:10]:
        print(f"{player['name']} - {player['position']}")
