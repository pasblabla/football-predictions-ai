import requests
import os
from datetime import datetime, timedelta
import json

class APIFootballClient:
    def __init__(self):
        self.api_key = "6ee6aab88980fa2736e4a663796ef088"
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': self.api_key
        }
        
    def get_leagues(self):
        """Récupérer les ligues principales européennes"""
        # IDs des ligues principales selon API-Football
        league_ids = {
            'Premier League': 39,      # Angleterre
            'Ligue 1': 61,            # France
            'Bundesliga': 78,         # Allemagne
            'Serie A': 135,           # Italie
            'LaLiga': 140,            # Espagne
            'Primeira Liga': 94,      # Portugal
            'Pro League': 144,        # Belgique
            'Super League': 207,      # Suisse
            'Eredivisie': 88,         # Pays-Bas
            'Champions League': 2,     # UEFA Champions League
            'Europa League': 3,        # UEFA Europa League
            'Conference League': 848   # UEFA Europa Conference League
        }
        
        leagues_data = []
        for name, league_id in league_ids.items():
            try:
                url = f"{self.base_url}/leagues"
                params = {'id': league_id, 'season': 2024}
                
                response = requests.get(url, headers=self.headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data['results'] > 0:
                        league_info = data['response'][0]
                        leagues_data.append({
                            'id': league_info['league']['id'],
                            'name': league_info['league']['name'],
                            'country': league_info['country']['name'],
                            'logo': league_info['league']['logo'],
                            'season': 2024
                        })
                        print(f"✓ Ligue récupérée: {name}")
                    else:
                        print(f"✗ Aucune donnée pour: {name}")
                else:
                    print(f"✗ Erreur API pour {name}: {response.status_code}")
                    
            except Exception as e:
                print(f"✗ Erreur lors de la récupération de {name}: {str(e)}")
                
        return leagues_data
    
    def get_teams_by_league(self, league_id, season=2024):
        """Récupérer les équipes d'une ligue"""
        try:
            url = f"{self.base_url}/teams"
            params = {'league': league_id, 'season': season}
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                teams_data = []
                
                for team_info in data['response']:
                    teams_data.append({
                        'id': team_info['team']['id'],
                        'name': team_info['team']['name'],
                        'country': team_info['team']['country'],
                        'logo': team_info['team']['logo'],
                        'league_id': league_id
                    })
                
                print(f"✓ {len(teams_data)} équipes récupérées pour la ligue {league_id}")
                return teams_data
            else:
                print(f"✗ Erreur API pour les équipes de la ligue {league_id}: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"✗ Erreur lors de la récupération des équipes: {str(e)}")
            return []
    
    def get_fixtures(self, league_id=None, date_from=None, date_to=None, season=2024):
        """Récupérer les matchs (fixtures)"""
        try:
            url = f"{self.base_url}/fixtures"
            params = {'season': season}
            
            if league_id:
                params['league'] = league_id
            if date_from:
                params['from'] = date_from
            if date_to:
                params['to'] = date_to
                
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                fixtures_data = []
                
                for fixture in data['response']:
                    fixtures_data.append({
                        'id': fixture['fixture']['id'],
                        'date': fixture['fixture']['date'],
                        'status': fixture['fixture']['status']['short'],
                        'venue': fixture['fixture']['venue']['name'] if fixture['fixture']['venue'] else 'TBD',
                        'league_id': fixture['league']['id'],
                        'league_name': fixture['league']['name'],
                        'home_team': {
                            'id': fixture['teams']['home']['id'],
                            'name': fixture['teams']['home']['name'],
                            'logo': fixture['teams']['home']['logo']
                        },
                        'away_team': {
                            'id': fixture['teams']['away']['id'],
                            'name': fixture['teams']['away']['name'],
                            'logo': fixture['teams']['away']['logo']
                        },
                        'goals': {
                            'home': fixture['goals']['home'],
                            'away': fixture['goals']['away']
                        }
                    })
                
                print(f"✓ {len(fixtures_data)} matchs récupérés")
                return fixtures_data
            else:
                print(f"✗ Erreur API pour les matchs: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"✗ Erreur lors de la récupération des matchs: {str(e)}")
            return []
    
    def get_predictions(self, fixture_id):
        """Récupérer les prédictions API-Football pour un match"""
        try:
            url = f"{self.base_url}/predictions"
            params = {'fixture': fixture_id}
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['results'] > 0:
                    prediction = data['response'][0]
                    return {
                        'fixture_id': fixture_id,
                        'winner': prediction['predictions']['winner']['name'] if prediction['predictions']['winner'] else None,
                        'advice': prediction['predictions']['advice'] if 'advice' in prediction['predictions'] else None,
                        'percent': prediction['predictions']['percent'] if 'percent' in prediction['predictions'] else None
                    }
            return None
            
        except Exception as e:
            print(f"✗ Erreur lors de la récupération des prédictions: {str(e)}")
            return None
    
    def get_player_statistics(self, team_id, season=2024):
        """Récupérer les statistiques des joueurs d'une équipe"""
        try:
            url = f"{self.base_url}/players"
            params = {'team': team_id, 'season': season}
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                players_data = []
                
                for player_info in data['response']:
                    player = player_info['player']
                    stats = player_info['statistics'][0] if player_info['statistics'] else {}
                    
                    players_data.append({
                        'id': player['id'],
                        'name': player['name'],
                        'position': stats.get('games', {}).get('position', 'Unknown'),
                        'goals': stats.get('goals', {}).get('total', 0),
                        'assists': stats.get('goals', {}).get('assists', 0),
                        'appearances': stats.get('games', {}).get('appearences', 0),
                        'team_id': team_id
                    })
                
                print(f"✓ {len(players_data)} joueurs récupérés pour l'équipe {team_id}")
                return players_data
            else:
                print(f"✗ Erreur API pour les joueurs de l'équipe {team_id}: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"✗ Erreur lors de la récupération des joueurs: {str(e)}")
            return []

    def test_api_connection(self):
        """Tester la connexion à l'API"""
        try:
            url = f"{self.base_url}/status"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✓ Connexion API réussie!")
                # Vérifier la structure de la réponse
                if 'response' in data and isinstance(data['response'], dict):
                    if 'requests' in data['response']:
                        requests_info = data['response']['requests']
                        print(f"Requêtes restantes: {requests_info.get('current', 'N/A')}/{requests_info.get('limit_day', 'N/A')}")
                return True
            else:
                print(f"✗ Erreur de connexion API: {response.status_code}")
                print(f"Réponse: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Erreur de connexion: {str(e)}")
            return False

