import os
import sys
import requests
from datetime import datetime, timedelta
import time

sys.path.insert(0, '/home/ubuntu/football-api')
from src.main import app, db
from src.models.football import League, Team, Match, Prediction
from src.improved_prediction_engine import ImprovedPredictionEngine

API_KEY = os.environ.get('FOOTBALL_DATA_API_KEY', '647c75a7ce7f482598c8240664bd856c')
BASE_URL = 'https://api.football-data.org/v4'

headers = {
    'X-Auth-Token': API_KEY
}

COMPETITIONS = {
    'PL': 2021,   # Premier League
    'FL1': 2015,  # Ligue 1
    'BL1': 2002,  # Bundesliga
    'SA': 2019,   # Serie A
    'PD': 2014,   # La Liga
}

def init_complete_system():
    """Initialiser complètement le système avec vraies données et prédictions améliorées"""
    
    with app.app_context():
        # NE PAS appeler db.create_all() car les tables sont déjà créées manuellement
        # avec les bonnes colonnes
        
        # Supprimer les anciennes données
        try:
            Match.query.delete()
            Prediction.query.delete()
            Team.query.delete()
            League.query.delete()
            db.session.commit()
            print("🗑️  Anciennes données supprimées")
        except:
            db.session.rollback()
            print("✅ Base de données prête")
        
        engine = ImprovedPredictionEngine()
        total_matches = 0
        
        for code, comp_id in COMPETITIONS.items():
            try:
                print(f"\n📥 Synchronisation de {code}...")
                
                # Récupérer les infos de la compétition
                comp_url = f"{BASE_URL}/competitions/{comp_id}"
                comp_response = requests.get(comp_url, headers=headers)
                
                if comp_response.status_code == 429:
                    print(f"⚠️  Limite de taux atteinte pour {code}, pause de 60s")
                    time.sleep(60)
                    continue
                    
                if comp_response.status_code != 200:
                    print(f"❌ Erreur {comp_response.status_code} pour {code}")
                    continue
                
                comp_data = comp_response.json()
                
                # Créer la ligue
                current_season = comp_data.get('currentSeason', {})
                league = League(
                    name=comp_data.get('name'),
                    country=comp_data.get('area', {}).get('name', 'Unknown'),
                    code=code,
                    season=f"{current_season.get('startDate', '2024')[:4]}-{current_season.get('endDate', '2025')[:4][-2:]}",
                    external_id=comp_id
                )
                db.session.add(league)
                db.session.commit()
                
                print(f"✅ Ligue: {league.name}")
                
                # Récupérer le classement
                standings_url = f"{BASE_URL}/competitions/{comp_id}/standings"
                standings_response = requests.get(standings_url, headers=headers)
                
                team_stats = {}
                if standings_response.status_code == 200:
                    standings_data = standings_response.json()
                    standings = standings_data.get('standings', [])
                    
                    if standings:
                        table = standings[0].get('table', [])
                        for entry in table:
                            team_data = entry.get('team', {})
                            team_id = team_data.get('id')
                            
                            if team_id:
                                team_stats[team_id] = {
                                    'position': entry.get('position'),
                                    'points': entry.get('points'),
                                    'played': entry.get('playedGames'),
                                    'wins': entry.get('won'),
                                    'draws': entry.get('draw'),
                                    'losses': entry.get('lost'),
                                    'goals_for': entry.get('goalsFor'),
                                    'goals_against': entry.get('goalsAgainst'),
                                    'goal_difference': entry.get('goalDifference')
                                }
                        print(f"📊 Classement récupéré: {len(team_stats)} équipes")
                
                time.sleep(7)
                
                # Récupérer les matchs des 14 prochains jours
                date_from = datetime.now().strftime('%Y-%m-%d')
                date_to = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
                
                matches_url = f"{BASE_URL}/competitions/{comp_id}/matches?dateFrom={date_from}&dateTo={date_to}"
                matches_response = requests.get(matches_url, headers=headers)
                
                if matches_response.status_code == 429:
                    print(f"⚠️  Limite de taux atteinte pour les matchs de {code}")
                    time.sleep(60)
                    continue
                
                if matches_response.status_code != 200:
                    print(f"❌ Erreur {matches_response.status_code} pour les matchs de {code}")
                    continue
                
                matches_data = matches_response.json()
                matches_list = matches_data.get('matches', [])
                
                print(f"📊 {len(matches_list)} matchs trouvés")
                
                for match_data in matches_list:
                    # Créer ou récupérer les équipes
                    home_team_data = match_data.get('homeTeam', {})
                    away_team_data = match_data.get('awayTeam', {})
                    
                    home_team_id = home_team_data.get('id')
                    away_team_id = away_team_data.get('id')
                    
                    home_team = Team.query.filter_by(external_id=home_team_id).first()
                    if not home_team:
                        home_team = Team(
                            name=home_team_data.get('name'),
                            country=comp_data.get('area', {}).get('name', 'Unknown'),
                            external_id=home_team_id
                        )
                        # Ajouter les stats si disponibles
                        if home_team_id in team_stats:
                            stats = team_stats[home_team_id]
                            home_team.league_position = stats['position']
                            home_team.points = stats['points']
                            home_team.played_games = stats['played']
                            home_team.wins = stats['wins']
                            home_team.draws = stats['draws']
                            home_team.losses = stats['losses']
                            home_team.goals_for = stats['goals_for']
                            home_team.goals_against = stats['goals_against']
                            home_team.goal_difference = stats['goal_difference']
                        
                        db.session.add(home_team)
                    
                    away_team = Team.query.filter_by(external_id=away_team_id).first()
                    if not away_team:
                        away_team = Team(
                            name=away_team_data.get('name'),
                            country=comp_data.get('area', {}).get('name', 'Unknown'),
                            external_id=away_team_id
                        )
                        # Ajouter les stats si disponibles
                        if away_team_id in team_stats:
                            stats = team_stats[away_team_id]
                            away_team.league_position = stats['position']
                            away_team.points = stats['points']
                            away_team.played_games = stats['played']
                            away_team.wins = stats['wins']
                            away_team.draws = stats['draws']
                            away_team.losses = stats['losses']
                            away_team.goals_for = stats['goals_for']
                            away_team.goals_against = stats['goals_against']
                            away_team.goal_difference = stats['goal_difference']
                        
                        db.session.add(away_team)
                    
                    db.session.commit()
                    
                    # Créer le match
                    match_date_str = match_data.get('utcDate')
                    if match_date_str:
                        match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
                    else:
                        continue
                    
                    match = Match(
                        date=match_date,
                        status=match_data.get('status', 'SCHEDULED'),
                        venue=match_data.get('venue'),
                        league_id=league.id,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        external_id=match_data.get('id')
                    )
                    
                    db.session.add(match)
                    db.session.commit()
                    
                    # Générer une prédiction avec le moteur amélioré
                    if match.status in ['SCHEDULED', 'TIMED']:
                        home_stats = {
                            'position': home_team.league_position,
                            'points': home_team.points,
                            'played': home_team.played_games,
                            'wins': home_team.wins,
                            'draws': home_team.draws,
                            'losses': home_team.losses,
                            'goals_for': home_team.goals_for,
                            'goals_against': home_team.goals_against,
                            'goal_difference': home_team.goal_difference
                        }
                        
                        away_stats = {
                            'position': away_team.league_position,
                            'points': away_team.points,
                            'played': away_team.played_games,
                            'wins': away_team.wins,
                            'draws': away_team.draws,
                            'losses': away_team.losses,
                            'goals_for': away_team.goals_for,
                            'goals_against': away_team.goals_against,
                            'goal_difference': away_team.goal_difference
                        }
                        
                        prediction_data = engine.predict_match(home_stats, away_stats, league.name)
                        
                        prediction = Prediction(
                            match_id=match.id,
                            predicted_winner=prediction_data['predicted_winner'],
                            confidence=prediction_data['confidence'],
                            prob_home_win=prediction_data['prob_home_win'],
                            prob_draw=prediction_data['prob_draw'],
                            prob_away_win=prediction_data['prob_away_win'],
                            predicted_score_home=prediction_data['predicted_score_home'],
                            predicted_score_away=prediction_data['predicted_score_away'],
                            reliability_score=prediction_data['reliability_score'],
                            prob_over_2_5=prediction_data['prob_over_2_5'],
                            prob_both_teams_score=prediction_data['prob_both_teams_score']
                        )
                        db.session.add(prediction)
                    
                    total_matches += 1
                
                db.session.commit()
                print(f"✅ {code} synchronisé: {len(matches_list)} matchs")
                
                time.sleep(7)
                
            except Exception as e:
                print(f"❌ Erreur pour {code}: {str(e)}")
                db.session.rollback()
                continue
        
        print(f"\n✅ Système initialisé: {total_matches} matchs avec prédictions améliorées")
        
        # Afficher quelques exemples
        print("\n📊 Exemples de prédictions améliorées:")
        sample_matches = Match.query.join(Prediction).limit(5).all()
        for match in sample_matches:
            pred = match.predictions
            print(f"\n{match.home_team.name} vs {match.away_team.name}")
            print(f"  Position: {match.home_team.league_position or 'N/A'} vs {match.away_team.league_position or 'N/A'}")
            print(f"  Pronostic: {pred.predicted_winner} ({pred.confidence})")
            print(f"  Probabilités: {int(pred.prob_home_win*100)}% - {int(pred.prob_draw*100)}% - {int(pred.prob_away_win*100)}%")
            print(f"  Score prédit: {pred.predicted_score_home}-{pred.predicted_score_away}")
            print(f"  Fiabilité: {pred.reliability_score}/10")

if __name__ == '__main__':
    init_complete_system()

