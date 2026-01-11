"""
Adaptateur pour le moteur ML classique
Convertit les données au format attendu
"""

class MLPredictorAdapter:
    """Adaptateur simple pour le ML classique"""
    
    def predict_match(self, match_data):
        """
        Prédiction basée sur les statistiques simples
        
        Args:
            match_data: Dict avec home_goals_avg, away_goals_avg, etc.
        """
        
        # Calcul simple basé sur les moyennes
        home_expected = (match_data['home_goals_avg'] + match_data['away_conceded_avg']) / 2
        away_expected = (match_data['away_goals_avg'] + match_data['home_conceded_avg']) / 2
        
        total_goals = home_expected + away_expected
        
        # Probabilités basées sur les moyennes
        if home_expected > away_expected * 1.3:
            win_home = 60
            win_away = 20
            draw = 20
        elif away_expected > home_expected * 1.3:
            win_home = 20
            win_away = 60
            draw = 20
        else:
            win_home = 40
            win_away = 30
            draw = 30
        
        # BTTS si les deux équipes ont une bonne moyenne
        btts = 70 if (home_expected > 1.0 and away_expected > 1.0) else 40
        
        # Score prédit (arrondi)
        score_home = round(home_expected)
        score_away = round(away_expected)
        
        return {
            'method': 'ML_CLASSIQUE',
            'home_team': match_data['home_team'],
            'away_team': match_data['away_team'],
            'predicted_score': f"{score_home}-{score_away}",
            'expected_goals': round(total_goals, 1),
            'win_probability_home': win_home,
            'win_probability_away': win_away,
            'draw_probability': draw,
            'btts_probability': btts,
            'confidence': 'Moyenne',
            'reasoning': f"Basé sur les moyennes: {match_data['home_team']} ({match_data['home_goals_avg']:.1f} buts/match) vs {match_data['away_team']} ({match_data['away_goals_avg']:.1f} buts/match)"
        }

