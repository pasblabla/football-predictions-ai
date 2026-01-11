"""
Récupérer les statistiques réelles des équipes depuis l'API
- Classement actuel
- Forme récente (5 derniers matchs)
- Statistiques de la saison
"""

import os
import sys
import requests
import time
from datetime import datetime

sys.path.insert(0, '/home/ubuntu/football-api')
from src.main import app, db
from src.models.football import League, Team, Match

API_KEY = os.environ.get('FOOTBALL_DATA_API_KEY', '647c75a7ce7f482598c8240664bd856c')
BASE_URL = 'https://api.football-data.org/v4'

headers = {
    'X-Auth-Token': API_KEY
}

def fetch_team_statistics():
    """Récupérer les statistiques de toutes les équipes"""
    
    with app.app_context():
        leagues = League.query.filter(League.code != 'EC').all()  # Exclure European Championship
        
        print(f"📊 Récupération des statistiques pour {len(leagues)} ligues...\n")
        
        total_teams_updated = 0
        
        for league in leagues:
            try:
                print(f"📥 {league.name} ({league.code})...")
                
                # Récupérer le classement
                standings_url = f"{BASE_URL}/competitions/{league.external_id}/standings"
                response = requests.get(standings_url, headers=headers)
                
                if response.status_code == 429:
                    print(f"⚠️  Limite de taux, pause de 70s...")
                    time.sleep(70)
                    response = requests.get(standings_url, headers=headers)
                
                if response.status_code != 200:
                    print(f"❌ Erreur {response.status_code}")
                    time.sleep(7)
                    continue
                
                data = response.json()
                standings = data.get('standings', [])
                
                if not standings:
                    print(f"⚠️  Pas de classement disponible")
                    time.sleep(7)
                    continue
                
                table = standings[0].get('table', [])
                teams_updated = 0
                
                for entry in table:
                    team_data = entry.get('team', {})
                    team_id = team_data.get('id')
                    
                    if not team_id:
                        continue
                    
                    # Trouver l'équipe dans notre base
                    team = Team.query.filter_by(external_id=team_id).first()
                    
                    if team:
                        # Stocker les statistiques dans un champ JSON ou créer des colonnes
                        # Pour l'instant, on va créer un dictionnaire qu'on utilisera pour l'IA
                        stats = {
                            'position': entry.get('position'),
                            'points': entry.get('points'),
                            'played_games': entry.get('playedGames'),
                            'wins': entry.get('won'),
                            'draws': entry.get('draw'),
                            'losses': entry.get('lost'),
                            'goals_for': entry.get('goalsFor'),
                            'goals_against': entry.get('goalsAgainst'),
                            'goal_difference': entry.get('goalDifference'),
                            'form': entry.get('form', '')  # Ex: "W,W,D,L,W"
                        }
                        
                        # Sauvegarder dans le champ country temporairement (on créera un champ stats plus tard)
                        # Pour l'instant, on va juste afficher
                        teams_updated += 1
                        
                        print(f"  ✓ {team.name:30} | Pos: {stats['position']:2} | Pts: {stats['points']:2} | Forme: {stats['form']}")
                
                print(f"✅ {teams_updated} équipes mises à jour\n")
                total_teams_updated += teams_updated
                
                time.sleep(7)  # Respecter la limite de taux
                
            except Exception as e:
                print(f"❌ Erreur pour {league.name}: {str(e)}\n")
                continue
        
        print(f"\n✅ Statistiques récupérées pour {total_teams_updated} équipes")
        
        return True

if __name__ == '__main__':
    fetch_team_statistics()

