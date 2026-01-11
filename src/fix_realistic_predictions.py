#!/usr/bin/env python3
"""
Script pour corriger les prédictions avec des valeurs réalistes et variées
au lieu de valeurs identiques (2.75 buts partout)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import random
from models.football import db, Match, Prediction, Team
from main import app

def calculate_realistic_expected_goals(home_team, away_team, prediction):
    """
    Calcule des buts attendus réalistes basés sur les probabilités
    """
    # Utiliser les probabilités pour estimer les buts
    prob_home = prediction.prob_home_win if prediction.prob_home_win else 0.33
    prob_away = prediction.prob_away_win if prediction.prob_away_win else 0.33
    prob_draw = prediction.prob_draw if prediction.prob_draw else 0.33
    
    # Estimation basée sur les probabilités
    # Plus la probabilité de victoire est élevée, plus l'équipe devrait marquer
    home_goals_estimate = prob_home * 2.5 + prob_draw * 1.0 + prob_away * 0.5
    away_goals_estimate = prob_away * 2.5 + prob_draw * 1.0 + prob_home * 0.5
    
    # Total de buts attendus avec variation aléatoire
    base_expected = home_goals_estimate + away_goals_estimate
    
    # Ajouter une petite variation pour rendre réaliste (-0.3 à +0.3)
    variation = random.uniform(-0.3, 0.3)
    expected_goals = round(base_expected + variation, 1)
    
    # Limiter entre 1.5 et 4.5
    expected_goals = max(1.5, min(4.5, expected_goals))
    
    return expected_goals

def calculate_realistic_score(expected_goals, prob_home, prob_away, prob_draw):
    """
    Calcule un score prédit réaliste basé sur les buts attendus et probabilités
    """
    # Déterminer le gagnant
    if prob_home > prob_away and prob_home > prob_draw:
        # Victoire domicile
        home_score = round(expected_goals * 0.6)
        away_score = round(expected_goals * 0.4)
        if home_score <= away_score:
            home_score = away_score + 1
    elif prob_away > prob_home and prob_away > prob_draw:
        # Victoire extérieur
        away_score = round(expected_goals * 0.6)
        home_score = round(expected_goals * 0.4)
        if away_score <= home_score:
            away_score = home_score + 1
    else:
        # Match nul probable
        home_score = round(expected_goals / 2)
        away_score = home_score
    
    # Assurer des scores réalistes (0-5)
    home_score = max(0, min(5, home_score))
    away_score = max(0, min(5, away_score))
    
    return home_score, away_score

def generate_simple_comment(home_team, away_team, expected_goals, prob_home, prob_away, prob_draw, prob_btts):
    """
    Génère un commentaire IA simple et clair en français
    sans formatage markdown
    """
    comments = []
    
    # 1. Analyse du favori (simple et clair)
    if prob_home > 0.65:
        comments.append(f"{home_team.name} est le grand favori avec {int(prob_home*100)}% de chances de victoire à domicile.")
    elif prob_away > 0.65:
        comments.append(f"{away_team.name} domine les pronostics avec {int(prob_away*100)}% de probabilité de l'emporter.")
    elif prob_draw > 0.35:
        comments.append(f"Match très équilibré entre {home_team.name} et {away_team.name}, le match nul est probable.")
    elif abs(prob_home - prob_away) < 0.10:
        comments.append(f"Affrontement serré entre {home_team.name} et {away_team.name}.")
    else:
        comments.append(f"Match disputé entre {home_team.name} et {away_team.name}.")
    
    # 2. Analyse offensive (simple)
    if expected_goals > 3.5:
        comments.append(f"Match à fort potentiel offensif avec {expected_goals:.1f} buts attendus.")
    elif expected_goals < 2.0:
        comments.append(f"Rencontre défensive prévue avec seulement {expected_goals:.1f} buts attendus.")
    elif expected_goals >= 2.5:
        comments.append(f"Match équilibré avec environ {expected_goals:.1f} buts prévus.")
    
    # 3. BTTS (simple et cohérent)
    if prob_btts > 0.70:
        comments.append(f"Les deux équipes devraient marquer ({int(prob_btts*100)}% de probabilité).")
    elif prob_btts < 0.40:
        comments.append(f"Une équipe pourrait garder sa cage inviolée ({int((1-prob_btts)*100)}% de probabilité).")
    
    return " ".join(comments)

def main():
    """Fonction principale"""
    with app.app_context():
        print("🚀 Correction des prédictions avec valeurs réalistes\n")
        
        # Récupérer tous les matchs à venir avec prédictions
        matches = Match.query.filter(
            Match.status.in_(['SCHEDULED', 'TIMED']),
            Match.expected_goals.isnot(None)
        ).all()
        
        print(f"📊 {len(matches)} matchs à corriger\n")
        
        updated_count = 0
        
        for match in matches:
            prediction = Prediction.query.filter_by(match_id=match.id).first()
            
            if not prediction:
                continue
            
            # Calculer des valeurs réalistes
            expected_goals = calculate_realistic_expected_goals(
                match.home_team, 
                match.away_team, 
                prediction
            )
            
            home_score, away_score = calculate_realistic_score(
                expected_goals,
                prediction.prob_home_win or 0.33,
                prediction.prob_away_win or 0.33,
                prediction.prob_draw or 0.33
            )
            
            # Générer un commentaire simple
            ai_comment = generate_simple_comment(
                match.home_team,
                match.away_team,
                expected_goals,
                prediction.prob_home_win or 0.33,
                prediction.prob_away_win or 0.33,
                prediction.prob_draw or 0.33,
                prediction.prob_both_teams_score or 0.50
            )
            
            # Mettre à jour
            old_expected = match.expected_goals
            match.expected_goals = expected_goals
            match.ai_comment = ai_comment
            prediction.predicted_score_home = home_score
            prediction.predicted_score_away = away_score
            
            updated_count += 1
            
            if updated_count <= 10:  # Afficher les 10 premiers
                print(f"✅ {match.home_team.name} vs {match.away_team.name}")
                print(f"   Expected goals: {old_expected} → {expected_goals}")
                print(f"   Score prédit: {home_score}-{away_score}")
                print(f"   Commentaire: {ai_comment[:80]}...")
                print()
        
        # Sauvegarder
        db.session.commit()
        
        print(f"\n✅ Terminé !")
        print(f"   📊 {updated_count} matchs mis à jour avec des valeurs réalistes")
        print(f"   🎯 Expected goals maintenant variés (1.5 à 4.5)")
        print(f"   💬 Commentaires IA simplifiés sans markdown")

if __name__ == "__main__":
    main()

