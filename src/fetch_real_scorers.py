    }
    
    # Buteurs domicile
    for scorer in home_scorers[:3]:
        player = scorer.get("player", {})
        goals = scorer.get("goals", 0)
        probability = calculate_scorer_probability(goals, home_total_goals)
        
        probable_scorers["home"].append({
            "name": player.get("name", "Joueur inconnu"),
            "probability": probability,
            "goals_season": goals
        })
    
    # Buteurs extérieur
    for scorer in away_scorers[:3]:
        player = scorer.get("player", {})
        goals = scorer.get("goals", 0)
        probability = calculate_scorer_probability(goals, away_total_goals)
        
        probable_scorers["away"].append({
            "name": player.get("name", "Joueur inconnu"),
            "probability": probability,
            "goals_season": goals
        })
    
    # Mettre à jour le match
    match.probable_scorers = json.dumps(probable_scorers)
    
    return probable_scorers

def main():
    """Fonction principale"""
    with app.app_context():
        print("🚀 Récupération des vrais buteurs depuis l'API football-data.org\n")
        
        # Récupérer tous les matchs à venir
        matches = Match.query.filter(
            Match.status.in_(['SCHEDULED', 'TIMED'])
        ).all()