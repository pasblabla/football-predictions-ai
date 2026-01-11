#!/usr/bin/env python3.11
"""
Script pour initialiser la base de données avec des données de démonstration réalistes
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['FOOTBALL_DATA_API_KEY'] = '647c75a7ce7f482598c8240664bd856c'

from src.main import app, db
from src.models.football import League, Team, Match, Prediction
from src.ai_prediction_engine import AIPredictionEngine
from datetime import datetime, timedelta
import random

ai_engine = AIPredictionEngine()

def init_demo_data():
    """Initialiser avec des données de démonstration réalistes"""
    with app.app_context():
        print("🚀 Initialisation des données de démonstration...")
        
        # Créer les ligues
        print("\n📋 Création des ligues...")
        leagues_data = [
            {"name": "Premier League", "country": "England", "code": "PL", "season": "2024-25"},
            {"name": "Ligue 1", "country": "France", "code": "FL1", "season": "2024-25"},
            {"name": "Bundesliga", "country": "Germany", "code": "BL1", "season": "2024-25"},
            {"name": "Serie A", "country": "Italy", "code": "SA", "season": "2024-25"},
            {"name": "LaLiga", "country": "Spain", "code": "PD", "season": "2024-25"},
            {"name": "Primeira Liga", "country": "Portugal", "code": "PPL", "season": "2024-25"},
            {"name": "Eredivisie", "country": "Netherlands", "code": "DED", "season": "2024-25"},
            {"name": "UEFA Champions League", "country": "Europe", "code": "CL", "season": "2024-25"},
            {"name": "UEFA Europa League", "country": "Europe", "code": "EL", "season": "2024-25"},
        ]
        
        leagues = {}
        for league_data in leagues_data:
            league = League(**league_data)
            db.session.add(league)
            db.session.flush()
            leagues[league_data["code"]] = league
            print(f"  ✓ {league.name}")
        
        # Créer les équipes par pays
        print("\n⚽ Création des équipes...")
        teams_data = {
            "England": [
                "Manchester City", "Arsenal", "Liverpool", "Chelsea", 
                "Manchester United", "Tottenham", "Newcastle", "Brighton",
                "Aston Villa", "West Ham"
            ],
            "France": [
                "Paris Saint-Germain", "Marseille", "Lyon", "Monaco",
                "Lille", "Nice", "Lens", "Rennes"
            ],
            "Germany": [
                "Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Bayer Leverkusen",
                "Union Berlin", "Eintracht Frankfurt", "Freiburg", "Wolfsburg"
            ],
            "Italy": [
                "Inter Milan", "AC Milan", "Juventus", "Napoli",
                "Roma", "Lazio", "Atalanta", "Fiorentina"
            ],
            "Spain": [
                "Real Madrid", "Barcelona", "Atletico Madrid", "Real Sociedad",
                "Athletic Bilbao", "Real Betis", "Villarreal", "Sevilla"
            ],
            "Portugal": [
                "Benfica", "Porto", "Sporting CP", "Braga",
                "Vitoria Guimaraes", "Boavista"
            ],
            "Netherlands": [
                "Ajax", "PSV Eindhoven", "Feyenoord", "AZ Alkmaar",
                "FC Twente", "FC Utrecht"
            ]
        }
        
        teams = {}
        for country, team_names in teams_data.items():
            teams[country] = []
            for team_name in team_names:
                team = Team(name=team_name, country=country)
                db.session.add(team)
                db.session.flush()
                teams[country].append(team)
            print(f"  ✓ {country}: {len(team_names)} équipes")
        
        # Créer des matchs pour les 7 prochains jours
        print("\n📅 Création des matchs à venir...")
        total_matches = 0
        
        # Mapping ligues -> pays
        league_country_map = {
            "PL": "England",
            "FL1": "France",
            "BL1": "Germany",
            "SA": "Italy",
            "PD": "Spain",
            "PPL": "Portugal",
            "DED": "Netherlands"
        }
        
        for i in range(7):
            match_date = datetime.now() + timedelta(days=i)
            
            # Matchs de championnats nationaux (3-4 par jour)
            for league_code, country in league_country_map.items():
                if random.random() > 0.3:  # 70% de chance d'avoir un match
                    league = leagues[league_code]
                    country_teams = teams[country]
                    
                    if len(country_teams) >= 2:
                        home_team = random.choice(country_teams)
                        away_team = random.choice([t for t in country_teams if t.id != home_team.id])
                        
                        match = Match(
                            date=match_date.replace(hour=random.randint(15, 21), minute=random.choice([0, 30])),
                            status="SCHEDULED",
                            venue=f"{home_team.name} Stadium",
                            league_id=league.id,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id
                        )
                        db.session.add(match)
                        db.session.flush()
                        
                        # Générer une prédiction
                        prediction_data = ai_engine.predict_match(
                            home_team.name, 
                            away_team.name, 
                            league.name
                        )
                        
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
                            prob_over_2_5=prediction_data.get('prob_over_2_5'),
                            prob_both_teams_score=prediction_data.get('prob_both_teams_score')
                        )
                        db.session.add(prediction)
                        total_matches += 1
            
            # Matchs européens (1-2 par jour)
            if i % 2 == 0 and random.random() > 0.3:  # Matchs européens tous les 2 jours
                for comp_code in ["CL", "EL"]:
                    if random.random() > 0.5:
                        league = leagues[comp_code]
                        
                        # Sélectionner des équipes de pays différents
                        country1 = random.choice(list(teams.keys()))
                        country2 = random.choice([c for c in teams.keys() if c != country1])
                        
                        home_team = random.choice(teams[country1])
                        away_team = random.choice(teams[country2])
                        
                        match = Match(
                            date=match_date.replace(hour=21, minute=0),
                            status="SCHEDULED",
                            venue=f"{home_team.name} Stadium",
                            league_id=league.id,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id
                        )
                        db.session.add(match)
                        db.session.flush()
                        
                        # Générer une prédiction
                        prediction_data = ai_engine.predict_match(
                            home_team.name, 
                            away_team.name, 
                            league.name
                        )
                        
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
                            prob_over_2_5=prediction_data.get('prob_over_2_5'),
                            prob_both_teams_score=prediction_data.get('prob_both_teams_score')
                        )
                        db.session.add(prediction)
                        total_matches += 1
        
        db.session.commit()
        print(f"  ✓ {total_matches} matchs créés avec prédictions")
        
        # Statistiques finales
        print("\n📊 Statistiques:")
        print(f"  - Ligues: {League.query.count()}")
        print(f"  - Équipes: {Team.query.count()}")
        print(f"  - Matchs: {Match.query.count()}")
        print(f"  - Prédictions: {Prediction.query.count()}")
        
        print("\n✅ Initialisation terminée avec succès!")

if __name__ == "__main__":
    init_demo_data()

