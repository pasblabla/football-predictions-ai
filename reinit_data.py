from wsgi import app
from src.models.football import db, League, Team, Match, Prediction
from datetime import datetime, timedelta
import random
import json

# Joueurs par équipe (pour les buteurs probables)
PLAYERS = {
    "Liverpool": ["Mohamed Salah", "Darwin Núñez", "Luis Díaz", "Diogo Jota"],
    "Manchester City": ["Erling Haaland", "Phil Foden", "Julian Alvarez", "Kevin De Bruyne"],
    "Arsenal": ["Bukayo Saka", "Gabriel Jesus", "Martin Ødegaard", "Leandro Trossard"],
    "Chelsea": ["Nicolas Jackson", "Cole Palmer", "Raheem Sterling", "Noni Madueke"],
    "Manchester United": ["Marcus Rashford", "Bruno Fernandes", "Rasmus Højlund", "Alejandro Garnacho"],
    "Tottenham": ["Son Heung-min", "Richarlison", "Dejan Kulusevski", "James Maddison"],
    "Paris Saint-Germain": ["Kylian Mbappé", "Ousmane Dembélé", "Randal Kolo Muani", "Bradley Barcola"],
    "Marseille": ["Pierre-Emerick Aubameyang", "Vitinha", "Amine Harit", "Jonathan Clauss"],
    "Lyon": ["Alexandre Lacazette", "Rayan Cherki", "Saïd Benrahma", "Gift Orban"],
    "Monaco": ["Wissam Ben Yedder", "Folarin Balogun", "Takumi Minamino", "Breel Embolo"],
    "Lille": ["Jonathan David", "Rémy Cabella", "Mohamed Bayo", "Edon Zhegrova"],
    "Nice": ["Terem Moffi", "Gaëtan Laborde", "Ross Barkley", "Sofiane Diop"],
    "Bayern Munich": ["Harry Kane", "Leroy Sané", "Jamal Musiala", "Serge Gnabry"],
    "Borussia Dortmund": ["Niclas Füllkrug", "Julian Brandt", "Karim Adeyemi", "Donyell Malen"],
    "RB Leipzig": ["Loïs Openda", "Benjamin Šeško", "Xavi Simons", "Dani Olmo"],
    "Bayer Leverkusen": ["Victor Boniface", "Florian Wirtz", "Moussa Diaby", "Amine Adli"],
    "Juventus": ["Dušan Vlahović", "Federico Chiesa", "Arkadiusz Milik", "Moise Kean"],
    "Inter Milan": ["Lautaro Martínez", "Marcus Thuram", "Hakan Çalhanoğlu", "Henrikh Mkhitaryan"],
    "AC Milan": ["Olivier Giroud", "Rafael Leão", "Christian Pulisic", "Samuel Chukwueze"],
    "Napoli": ["Victor Osimhen", "Khvicha Kvaratskhelia", "Giacomo Raspadori", "Matteo Politano"],
    "Roma": ["Romelu Lukaku", "Paulo Dybala", "Lorenzo Pellegrini", "Stephan El Shaarawy"],
    "Real Madrid": ["Vinícius Jr.", "Jude Bellingham", "Rodrygo", "Joselu"],
    "Barcelona": ["Robert Lewandowski", "Lamine Yamal", "Raphinha", "Ferran Torres"],
    "Atletico Madrid": ["Antoine Griezmann", "Álvaro Morata", "Memphis Depay", "Ángel Correa"],
    "Sevilla": ["Youssef En-Nesyri", "Lucas Ocampos", "Erik Lamela", "Rafa Mir"],
    "Porto": ["Mehdi Taremi", "Evanilson", "Galeno", "Pepê"],
    "Benfica": ["Ángel Di María", "Gonçalo Ramos", "Rafa Silva", "João Mário"],
    "Sporting CP": ["Viktor Gyökeres", "Pedro Gonçalves", "Francisco Trincão", "Paulinho"],
    "Club Brugge": ["Igor Thiago", "Andreas Skov Olsen", "Ferran Jutglà", "Tajon Buchanan"],
    "Anderlecht": ["Kasper Dolberg", "Francis Amuzu", "Anders Dreyer", "Luis Vázquez"],
    "Young Boys": ["Cedric Itten", "Meschack Elia", "Filip Ugrinic", "Kastriot Imeri"],
    "Basel": ["Thierno Barry", "Darian Males", "Bradley Fink", "Zeki Amdouni"],
    "Ajax": ["Brian Brobbey", "Steven Bergwijn", "Mohammed Kudus", "Dusan Tadic"],
    "PSV Eindhoven": ["Luuk de Jong", "Johan Bakayoko", "Hirving Lozano", "Xavi Simons"],
    "Feyenoord": ["Santiago Giménez", "Igor Paixão", "Yankuba Minteh", "Calvin Stengs"]
}

def generate_probable_scorers(home_team_name, away_team_name):
    """Générer les buteurs probables pour un match"""
    home_players = PLAYERS.get(home_team_name, ["Joueur 1", "Joueur 2"])
    away_players = PLAYERS.get(away_team_name, ["Joueur 1", "Joueur 2"])
    
    scorers = {
        "home": [
            {"name": home_players[0] if len(home_players) > 0 else "Joueur 1", "probability": random.randint(35, 55), "goals_season": random.randint(5, 20)},
            {"name": home_players[1] if len(home_players) > 1 else "Joueur 2", "probability": random.randint(25, 45), "goals_season": random.randint(3, 15)}
        ],
        "away": [
            {"name": away_players[0] if len(away_players) > 0 else "Joueur 1", "probability": random.randint(35, 55), "goals_season": random.randint(5, 20)},
            {"name": away_players[1] if len(away_players) > 1 else "Joueur 2", "probability": random.randint(25, 45), "goals_season": random.randint(3, 15)}
        ]
    }
    return json.dumps(scorers)

def generate_prediction_for_match(match):
    """Générer une prédiction pour un match"""
    # Probabilités aléatoires mais réalistes
    prob_home = random.uniform(0.25, 0.55)
    prob_draw = random.uniform(0.15, 0.35)
    prob_away = 1 - prob_home - prob_draw
    
    # Déterminer le gagnant prédit
    max_prob = max(prob_home, prob_draw, prob_away)
    if max_prob == prob_home:
        predicted_winner = "home"
    elif max_prob == prob_away:
        predicted_winner = "away"
    else:
        predicted_winner = "draw"
    
    confidence_value = max_prob + random.uniform(-0.05, 0.1)
    confidence_value = max(0.4, min(0.95, confidence_value))
    
    # Déterminer le niveau de confiance
    if confidence_value >= 0.7:
        confidence = "Élevée"
    elif confidence_value >= 0.5:
        confidence = "Moyenne"
    else:
        confidence = "Faible"
    
    # Scores prédits
    predicted_score_home = random.randint(0, 4)
    predicted_score_away = random.randint(0, 3)
    
    return Prediction(
        match_id=match.id,
        predicted_winner=predicted_winner,
        confidence=confidence,
        confidence_level=confidence_value,
        prob_home_win=round(prob_home, 3),
        prob_draw=round(prob_draw, 3),
        prob_away_win=round(prob_away, 3),
        prob_over_2_5=round(random.uniform(0.4, 0.9), 3),
        prob_both_teams_score=round(random.uniform(0.3, 0.8), 3),
        predicted_score_home=predicted_score_home,
        predicted_score_away=predicted_score_away,
        reliability_score=round(confidence_value * 10, 1)
    )

def generate_ai_comment(home_team, away_team):
    """Générer un commentaire IA pour un match"""
    comments = [
        f"Affrontement serré entre {home_team} et {away_team}. {home_team} est en excellente forme.",
        f"Match prometteur entre {home_team} et {away_team}. Les deux équipes ont des statistiques similaires.",
        f"{home_team} reçoit {away_team} dans un match qui s'annonce passionnant.",
        f"Duel tactique attendu entre {home_team} et {away_team}. L'avantage du terrain pourrait être décisif.",
        f"{away_team} se déplace chez {home_team} avec l'ambition de créer la surprise."
    ]
    return random.choice(comments)

with app.app_context():
    # Supprimer les anciennes données
    Prediction.query.delete()
    Match.query.delete()
    Team.query.delete()
    League.query.delete()
    db.session.commit()
    
    # Créer les ligues
    leagues_data = [
        {"name": "Premier League", "country": "England", "code": "PL", "season": "2024-25"},
        {"name": "Ligue 1", "country": "France", "code": "FL1", "season": "2024-25"},
        {"name": "Bundesliga", "country": "Germany", "code": "BL1", "season": "2024-25"},
        {"name": "Serie A", "country": "Italy", "code": "SA", "season": "2024-25"},
        {"name": "LaLiga", "country": "Spain", "code": "PD", "season": "2024-25"},
        {"name": "Primeira Liga", "country": "Portugal", "code": "PPL", "season": "2024-25"},
        {"name": "Pro League", "country": "Belgium", "code": "BPL", "season": "2024-25"},
        {"name": "Super League", "country": "Switzerland", "code": "SSL", "season": "2024-25"},
        {"name": "Eredivisie", "country": "Netherlands", "code": "ED", "season": "2024-25"},
        {"name": "Champions League", "country": "Europe", "code": "CL", "season": "2024-25"},
        {"name": "Europa League", "country": "Europe", "code": "EL", "season": "2024-25"},
        {"name": "Conference League", "country": "Europe", "code": "ECL", "season": "2024-25"}
    ]
    
    leagues = {}
    for league_data in leagues_data:
        league = League(**league_data)
        db.session.add(league)
        db.session.flush()
        leagues[league_data["name"]] = league
    
    # Créer les équipes
    teams_data = [
        {"name": "Liverpool", "country": "England"},
        {"name": "Manchester City", "country": "England"},
        {"name": "Arsenal", "country": "England"},
        {"name": "Chelsea", "country": "England"},
        {"name": "Manchester United", "country": "England"},
        {"name": "Tottenham", "country": "England"},
        {"name": "Paris Saint-Germain", "country": "France"},
        {"name": "Marseille", "country": "France"},
        {"name": "Lyon", "country": "France"},
        {"name": "Monaco", "country": "France"},
        {"name": "Lille", "country": "France"},
        {"name": "Nice", "country": "France"},
        {"name": "Bayern Munich", "country": "Germany"},
        {"name": "Borussia Dortmund", "country": "Germany"},
        {"name": "RB Leipzig", "country": "Germany"},
        {"name": "Bayer Leverkusen", "country": "Germany"},
        {"name": "Juventus", "country": "Italy"},
        {"name": "Inter Milan", "country": "Italy"},
        {"name": "AC Milan", "country": "Italy"},
        {"name": "Napoli", "country": "Italy"},
        {"name": "Roma", "country": "Italy"},
        {"name": "Real Madrid", "country": "Spain"},
        {"name": "Barcelona", "country": "Spain"},
        {"name": "Atletico Madrid", "country": "Spain"},
        {"name": "Sevilla", "country": "Spain"},
        {"name": "Porto", "country": "Portugal"},
        {"name": "Benfica", "country": "Portugal"},
        {"name": "Sporting CP", "country": "Portugal"},
        {"name": "Club Brugge", "country": "Belgium"},
        {"name": "Anderlecht", "country": "Belgium"},
        {"name": "Young Boys", "country": "Switzerland"},
        {"name": "Basel", "country": "Switzerland"},
        {"name": "Ajax", "country": "Netherlands"},
        {"name": "PSV Eindhoven", "country": "Netherlands"},
        {"name": "Feyenoord", "country": "Netherlands"}
    ]
    
    teams_by_country = {}
    for team_data in teams_data:
        team = Team(**team_data)
        db.session.add(team)
        db.session.flush()
        if team_data["country"] not in teams_by_country:
            teams_by_country[team_data["country"]] = []
        teams_by_country[team_data["country"]].append(team)
    
    db.session.commit()
    
    # Créer des matchs pour les 7 prochains jours
    country_to_league = {
        "England": "Premier League",
        "France": "Ligue 1",
        "Germany": "Bundesliga",
        "Italy": "Serie A",
        "Spain": "LaLiga",
        "Portugal": "Primeira Liga",
        "Belgium": "Pro League",
        "Switzerland": "Super League",
        "Netherlands": "Eredivisie"
    }
    
    for i in range(7):
        match_date = datetime.now() + timedelta(days=i)
        
        for country, teams in teams_by_country.items():
            if len(teams) < 2:
                continue
            
            # Trouver la ligue correspondante
            league_name = country_to_league.get(country)
            if not league_name:
                continue
            
            league = leagues.get(league_name)
            if not league:
                continue
            
            # Créer 1-2 matchs par ligue par jour
            num_matches = random.randint(1, 2)
            used_teams = set()
            
            for j in range(num_matches):
                available_teams = [t for t in teams if t.id not in used_teams]
                if len(available_teams) < 2:
                    break
                
                home_team = random.choice(available_teams)
                used_teams.add(home_team.id)
                away_team = random.choice([t for t in available_teams if t.id != home_team.id])
                used_teams.add(away_team.id)
                
                match = Match(
                    date=match_date.replace(hour=random.randint(15, 21), minute=random.choice([0, 30, 45])),
                    status="SCHEDULED",
                    venue=f"{home_team.name} Stadium",
                    league_id=league.id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    ai_comment=generate_ai_comment(home_team.name, away_team.name),
                    expected_goals=round(random.uniform(2.0, 4.5), 1),
                    probable_scorers=generate_probable_scorers(home_team.name, away_team.name)
                )
                db.session.add(match)
                db.session.flush()
                
                prediction = generate_prediction_for_match(match)
                db.session.add(prediction)
    
    db.session.commit()
    
    # Compter les résultats
    total_leagues = League.query.count()
    total_teams = Team.query.count()
    total_matches = Match.query.count()
    total_predictions = Prediction.query.count()
    
    print(f"Données initialisées avec succès:")
    print(f"- {total_leagues} ligues")
    print(f"- {total_teams} équipes")
    print(f"- {total_matches} matchs")
    print(f"- {total_predictions} prédictions")
