import os
import sys
import requests
from datetime import datetime, timedelta
import time

sys.path.insert(0, '/home/ubuntu/football-api')
from src.main import app, db
from src.models.football import League, Team, Match

API_KEY = os.environ.get('FOOTBALL_DATA_API_KEY', '647c75a7ce7f482598c8240664bd856c')
BASE_URL = 'https://api.football-data.org/v4'

headers = {
    'X-Auth-Token': API_KEY
}

def fetch_standings(competition_id):
    """Récupérer le classement d'une compétition"""
    try:
        url = f"{BASE_URL}/competitions/{competition_id}/standings"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            print(f"⚠️  Limite de taux atteinte, pause de 60s")
            time.sleep(60)
            return None
            
        if response.status_code != 200:
            print(f"❌ Erreur {response.status_code}")
            return None
        
        data = response.json()
        standings = data.get('standings', [])
        
        if not standings:
            return None
            
        # Prendre le classement général (type TOTAL)
        for standing in standings:
            if standing.get('type') == 'TOTAL':
                return standing.get('table', [])
        
        return standings[0].get('table', []) if standings else None
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return None

def fetch_team_matches(team_id, limit=10):
    """Récupérer les derniers matchs d'une équipe"""
    try:
        # Récupérer les matchs des 90 derniers jours
        date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{BASE_URL}/teams/{team_id}/matches?dateFrom={date_from}&dateTo={date_to}&status=FINISHED"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            print(f"⚠️  Limite de taux atteinte")
            time.sleep(60)
            return []
            
        if response.status_code != 200:
            return []
        
        data = response.json()
        matches = data.get('matches', [])
        
        # Trier par date décroissante et prendre les N derniers
        matches.sort(key=lambda x: x.get('utcDate', ''), reverse=True)
        return matches[:limit]
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return []

def calculate_team_form(matches, team_id):
    """Calculer la forme d'une équipe basée sur ses derniers matchs"""
    if not matches:
        return {
            'points': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_scored': 0,
            'goals_conceded': 0,
            'form_string': 'N/A'
        }
    
    points = 0
    wins = 0
    draws = 0
    losses = 0
    goals_scored = 0
    goals_conceded = 0
    form_string = ''
    
    for match in matches[:5]:  # Derniers 5 matchs
        home_team_id = match.get('homeTeam', {}).get('id')
        away_team_id = match.get('awayTeam', {}).get('id')
        
        score = match.get('score', {}).get('fullTime', {})
        home_score = score.get('home')
        away_score = score.get('away')
        
        if home_score is None or away_score is None:
            continue
        
        is_home = (home_team_id == team_id)
        
        if is_home:
            goals_scored += home_score
            goals_conceded += away_score
            
            if home_score > away_score:
                wins += 1
                points += 3
                form_string += 'V'
            elif home_score == away_score:
                draws += 1
                points += 1
                form_string += 'N'
            else:
                losses += 1
                form_string += 'D'
        else:
            goals_scored += away_score
            goals_conceded += home_score
            
            if away_score > home_score:
                wins += 1
                points += 3
                form_string += 'V'
            elif away_score == home_score:
                draws += 1
                points += 1
                form_string += 'N'
            else:
                losses += 1
                form_string += 'D'
    
    return {
        'points': points,
        'wins': wins,
        'draws': draws,
        'losses': losses,
        'goals_scored': goals_scored,
        'goals_conceded': goals_conceded,
        'goal_difference': goals_scored - goals_conceded,
        'form_string': form_string
    }

def update_team_stats():
    """Mettre à jour les statistiques de toutes les équipes"""
    with app.app_context():
        leagues = League.query.all()
        
        for league in leagues:
            if not league.external_id:
                continue
                
            print(f"\n📊 Traitement de {league.name}...")
            
            # Récupérer le classement
            standings = fetch_standings(league.external_id)
            
            if not standings:
                print(f"⚠️  Pas de classement disponible pour {league.name}")
                time.sleep(7)
                continue
            
            # Créer un dictionnaire des stats par équipe
            team_stats = {}
            for entry in standings:
                team_data = entry.get('team', {})
                team_id = team_data.get('id')
                
                if team_id:
                    team_stats[team_id] = {
                        'position': entry.get('position'),
                        'points': entry.get('points'),
                        'played_games': entry.get('playedGames'),
                        'won': entry.get('won'),
                        'draw': entry.get('draw'),
                        'lost': entry.get('lost'),
                        'goals_for': entry.get('goalsFor'),
                        'goals_against': entry.get('goalsAgainst'),
                        'goal_difference': entry.get('goalDifference')
                    }
            
            # Mettre à jour les équipes de cette ligue
            matches = Match.query.filter_by(league_id=league.id).all()
            team_ids = set()
            
            for match in matches:
                if match.home_team.external_id:
                    team_ids.add(match.home_team.external_id)
                if match.away_team.external_id:
                    team_ids.add(match.away_team.external_id)
            
            for team_id in team_ids:
                team = Team.query.filter_by(external_id=team_id).first()
                if not team:
                    continue
                
                # Récupérer les stats du classement
                stats = team_stats.get(team_id, {})
                
                # Mettre à jour les attributs de l'équipe
                team.league_position = stats.get('position')
                team.points = stats.get('points')
                team.played_games = stats.get('played_games')
                team.wins = stats.get('won')
                team.draws = stats.get('draw')
                team.losses = stats.get('lost')
                team.goals_for = stats.get('goals_for')
                team.goals_against = stats.get('goals_against')
                team.goal_difference = stats.get('goal_difference')
                
                print(f"  ✅ {team.name}: Position {team.league_position}, {team.points} pts")
            
            db.session.commit()
            time.sleep(7)  # Pause pour respecter les limites
        
        print("\n✅ Statistiques mises à jour avec succès!")

if __name__ == '__main__':
    update_team_stats()

