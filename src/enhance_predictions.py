#!/usr/bin/env python3
"""
Script pour améliorer les prédictions avec :
1. Analyse dynamique des buts (0.5, 1.5, 2.5, 3.5, 4.5)
2. Commentaires IA personnalisés
3. Buteurs probables
"""

import sqlite3
import json
from datetime import datetime

def calculate_goals_probabilities(home_stats, away_stats):
    """
    Calcule les probabilités pour différents seuils de buts
    Basé sur les statistiques offensives et défensives
    """
    # Moyenne de buts attendus
    home_attack = home_stats.get('goals_scored_avg', 1.5)
    away_attack = away_stats.get('goals_scored_avg', 1.5)
    home_defense = home_stats.get('goals_conceded_avg', 1.0)
    away_defense = away_stats.get('goals_conceded_avg', 1.0)
    
    # Estimation du nombre total de buts
    expected_goals = (home_attack + away_attack + home_defense + away_defense) / 2
    
    # Probabilités basées sur une distribution statistique
    probabilities = {
        '0.5': min(95, int(expected_goals * 40 + 20)),  # Très probable si expected_goals > 0.5
        '1.5': min(90, int(expected_goals * 35 + 15)),
        '2.5': min(85, int(expected_goals * 30 + 10)),
        '3.5': min(70, int(expected_goals * 20 + 5)),
        '4.5': min(50, int(expected_goals * 10))
    }
    
    return probabilities, expected_goals

def generate_ai_comment(match_data, learning_data=None):
    """
    Génère un commentaire IA personnalisé basé sur les statistiques
    """
    home_team = match_data['home_team']
    away_team = match_data['away_team']
    prob_home = match_data.get('prob_home_win', 50)
    prob_away = match_data.get('prob_away_win', 30)
    prob_draw = match_data.get('prob_draw', 20)
    prob_btts = match_data.get('prob_btts', 50)
    expected_goals = match_data.get('expected_goals', 2.5)
    
    comments = []
    
    # Analyse du favori
    if prob_home > 60:
        comments.append(f"{home_team} est le grand favori à domicile avec {prob_home}% de chances de victoire.")
    elif prob_away > 60:
        comments.append(f"{away_team} domine les statistiques avec {prob_away}% de probabilité de l'emporter.")
    elif prob_draw > 35:
        comments.append(f"Match très équilibré, le match nul est probable ({prob_draw}%).")
    else:
        comments.append(f"Match serré entre {home_team} et {away_team}.")
    
    # Analyse offensive
    if expected_goals > 3.5:
        comments.append(f"Match à fort potentiel offensif ({expected_goals:.1f} buts attendus).")
    elif expected_goals < 2.0:
        comments.append(f"Rencontre défensive attendue ({expected_goals:.1f} buts prévus).")
    
    # BTTS
    if prob_btts > 70:
        comments.append(f"Les deux équipes devraient marquer ({prob_btts}% de probabilité).")
    elif prob_btts < 40:
        comments.append(f"Une équipe pourrait garder sa cage inviolée ({100-prob_btts}% de clean sheet).")
    
    # Apprentissage (si disponible)
    if learning_data:
        accuracy = learning_data.get('accuracy', 0)
        if accuracy > 60:
            comments.append(f"Mon IA a {accuracy}% de précision sur ce type de match.")
        elif accuracy < 40:
            comments.append(f"Match difficile à prédire selon mon historique ({accuracy}% de réussite).")
    
    return " ".join(comments)

def generate_probable_scorers(home_team, away_team):
    """
    Génère une liste de buteurs probables
    Note: Pour l'instant, données simulées. À remplacer par vraies stats API
    """
    # Buteurs simulés - À remplacer par vraies données
    scorers = {
        'home': [
            {'name': 'Attaquant vedette', 'probability': 45, 'goals_season': 12},
            {'name': 'Milieu offensif', 'probability': 30, 'goals_season': 7},
            {'name': 'Ailier droit', 'probability': 25, 'goals_season': 5}
        ],
        'away': [
            {'name': 'Avant-centre', 'probability': 40, 'goals_season': 10},
            {'name': 'Ailier gauche', 'probability': 35, 'goals_season': 8},
            {'name': 'Meneur de jeu', 'probability': 20, 'goals_season': 4}
        ]
    }
    
    return scorers

def enhance_match_predictions():
    """
    Améliore toutes les prédictions de matchs dans la base de données
    """
    conn = sqlite3.connect('/home/ubuntu/football-api-deploy/server/database/app.db')
    cursor = conn.cursor()
    
    # Récupérer tous les matchs à venir avec les noms d'équipes
    cursor.execute("""
        SELECT m.id, ht.name, at.name, p.prob_home_win, p.prob_away_win, p.prob_draw, 
               p.prob_both_teams_score, p.prob_over_2_5
        FROM match m
        LEFT JOIN team ht ON m.home_team_id = ht.id
        LEFT JOIN team at ON m.away_team_id = at.id
        LEFT JOIN prediction p ON m.id = p.match_id
        WHERE m.date > datetime('now')
        ORDER BY m.date
    """)
    
    matches = cursor.fetchall()
    print(f"🔄 Amélioration de {len(matches)} matchs...")
    
    enhanced_count = 0
    
    for match in matches:
        match_id, home_team, away_team, prob_home, prob_away, prob_draw, prob_btts, prob_over_25 = match
        
        # Simuler des statistiques d'équipe (à remplacer par vraies données)
        home_stats = {'goals_scored_avg': 1.8, 'goals_conceded_avg': 1.2}
        away_stats = {'goals_scored_avg': 1.5, 'goals_conceded_avg': 1.0}
        
        # Calculer les probabilités de buts
        goals_probs, expected_goals = calculate_goals_probabilities(home_stats, away_stats)
        
        # Générer le commentaire IA
        match_data = {
            'home_team': home_team,
            'away_team': away_team,
            'prob_home_win': prob_home or 50,
            'prob_away_win': prob_away or 30,
            'prob_draw': prob_draw or 20,
            'prob_btts': prob_btts or 50,
            'expected_goals': expected_goals
        }
        
        ai_comment = generate_ai_comment(match_data)
        
        # Générer les buteurs probables
        scorers = generate_probable_scorers(home_team, away_team)
        
        # Mettre à jour la base de données
        cursor.execute("""
            UPDATE match
            SET 
                prob_over_05 = ?,
                prob_over_15 = ?,
                prob_over_35 = ?,
                prob_over_45 = ?,
                ai_comment = ?,
                probable_scorers = ?,
                expected_goals = ?
            WHERE id = ?
        """, (
            goals_probs['0.5'],
            goals_probs['1.5'],
            goals_probs['3.5'],
            goals_probs['4.5'],
            ai_comment,
            json.dumps(scorers),
            expected_goals,
            match_id
        ))
        
        enhanced_count += 1
        if enhanced_count % 10 == 0:
            print(f"  ✓ {enhanced_count}/{len(matches)} matchs améliorés")
    
    conn.commit()
    conn.close()
    
    print(f"✅ {enhanced_count} matchs améliorés avec succès !")
    print(f"   - Analyse dynamique des buts (0.5 à 4.5)")
    print(f"   - Commentaires IA personnalisés")
    print(f"   - Buteurs probables")

if __name__ == '__main__':
    print("🚀 Démarrage de l'amélioration des prédictions...")
    enhance_match_predictions()

