#!/usr/bin/env python3
"""
Script pour corriger et régénérer les commentaires IA de manière cohérente
avec les prédictions réelles (score, BTTS, probabilités de buts)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.football import db, Match, Prediction
from main import app

def generate_intelligent_comment(match, prediction):
    """
    Génère un commentaire IA cohérent basé sur TOUTES les statistiques du match
    """
    home_team = match.home_team.name
    away_team = match.away_team.name
    
    # Récupérer toutes les statistiques
    prob_home = prediction.prob_home_win * 100
    prob_draw = prediction.prob_draw * 100
    prob_away = prediction.prob_away_win * 100
    prob_btts = prediction.prob_both_teams_score * 100 if prediction.prob_both_teams_score else 50
    prob_over_25 = prediction.prob_over_2_5 * 100 if prediction.prob_over_2_5 else 50
    expected_goals = match.expected_goals if match.expected_goals else 2.5
    
    # Calculer le score prédit basé sur les probabilités
    if prob_home > prob_draw and prob_home > prob_away:
        predicted_winner = home_team
        predicted_home = 2 if prob_home > 60 else 1
        predicted_away = 0 if prob_home > 60 else 1
    elif prob_away > prob_draw and prob_away > prob_home:
        predicted_winner = away_team
        predicted_home = 0 if prob_away > 60 else 1
        predicted_away = 2 if prob_away > 60 else 1
    else:
        predicted_winner = "Match nul"
        predicted_home = 1
        predicted_away = 1
    
    comments = []
    
    # 1. Analyse du favori
    if prob_home > 65:
        comments.append(f"**{home_team}** est le grand favori avec {prob_home:.0f}% de chances de victoire à domicile.")
    elif prob_away > 65:
        comments.append(f"**{away_team}** domine les pronostics avec {prob_away:.0f}% de probabilité de l'emporter.")
    elif prob_draw > 35:
        comments.append(f"Match très équilibré entre **{home_team}** et **{away_team}**, le match nul est probable ({prob_draw:.0f}%).")
    elif abs(prob_home - prob_away) < 10:
        comments.append(f"Affrontement serré entre **{home_team}** et **{away_team}**, les deux équipes ont des chances similaires.")
    else:
        comments.append(f"Match disputé entre **{home_team}** et **{away_team}**.")
    
    # 2. Analyse offensive basée sur expected_goals ET prob_over_25
    if expected_goals > 3.5 and prob_over_25 > 70:
        comments.append(f"🔥 Spectacle offensif attendu avec **{expected_goals:.1f} buts** prévus ({prob_over_25:.0f}% de chances de +2.5 buts).")
    elif expected_goals > 3.0 and prob_over_25 > 60:
        comments.append(f"Match à fort potentiel offensif (**{expected_goals:.1f} buts** attendus).")
    elif expected_goals < 2.0 and prob_over_25 < 40:
        comments.append(f"Rencontre défensive prévue avec seulement **{expected_goals:.1f} buts** attendus.")
    elif expected_goals >= 2.0 and expected_goals <= 3.0:
        comments.append(f"Match équilibré avec environ **{expected_goals:.1f} buts** prévus.")
    
    # 3. BTTS - Cohérent avec le score prédit
    total_predicted_goals = predicted_home + predicted_away
    if prob_btts > 70 and total_predicted_goals >= 2:
        comments.append(f"⚽ Les deux équipes devraient marquer ({prob_btts:.0f}% de probabilité BTTS).")
    elif prob_btts < 40 and (predicted_home == 0 or predicted_away == 0):
        comments.append(f"🛡️ Une équipe pourrait garder sa cage inviolée ({100-prob_btts:.0f}% de probabilité).")
    elif prob_btts >= 40 and prob_btts <= 70:
        comments.append(f"Probabilité modérée que les deux équipes marquent ({prob_btts:.0f}%).")
    
    # 4. Score prédit cohérent
    if predicted_home > predicted_away:
        comments.append(f"📊 Score prédit : **{home_team} {predicted_home}-{predicted_away}**")
    elif predicted_away > predicted_home:
        comments.append(f"📊 Score prédit : **{away_team} {predicted_away}-{predicted_home}**")
    else:
        comments.append(f"📊 Score prédit : **Match nul {predicted_home}-{predicted_away}**")
    
    return " ".join(comments)

def main():
    """Fonction principale"""
    with app.app_context():
        print("🚀 Correction des commentaires IA incohérents\n")
        
        # Récupérer tous les matchs avec commentaires IA
        matches = Match.query.filter(
            Match.ai_comment.isnot(None),
            Match.status.in_(['SCHEDULED', 'TIMED'])
        ).all()
        
        print(f"📊 {len(matches)} matchs à corriger\n")
        
        corrected_count = 0
        
        for match in matches:
            # Récupérer la prédiction associée
            prediction = Prediction.query.filter_by(match_id=match.id).first()
            
            if not prediction:
                print(f"⚠️  Pas de prédiction pour {match.home_team.name} vs {match.away_team.name}")
                continue
            
            # Générer le nouveau commentaire intelligent
            new_comment = generate_intelligent_comment(match, prediction)
            
            # Mettre à jour
            match.ai_comment = new_comment
            corrected_count += 1
            
            print(f"✅ {match.home_team.name} vs {match.away_team.name}")
            print(f"   Ancien: {match.ai_comment[:80] if len(match.ai_comment) > 80 else match.ai_comment}")
            print(f"   Nouveau: {new_comment[:80]}...\n")
        
        # Sauvegarder
        db.session.commit()
        
        print(f"\n✅ Terminé !")
        print(f"   📊 {corrected_count} commentaires corrigés")
        print(f"   🎯 Commentaires maintenant cohérents avec les prédictions")

if __name__ == "__main__":
    main()

