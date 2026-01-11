"""
Script d'entraînement de l'IA sur les matchs passés
Objectif: Améliorer la précision vers 80%
"""

import os
import sys
import json
from datetime import datetime

# Ajouter le chemin du projet
sys.path.insert(0, '/home/ubuntu/football_app')
os.chdir('/home/ubuntu/football_app')

from src.ai_prediction_engine.ImprovedHybridAI import improved_ai

def load_finished_matches():
    """Charger les matchs terminés depuis la base de données"""
    from wsgi import app
    from src.models.football import db, Match
    
    with app.app_context():
        matches = Match.query.filter(Match.status == "FINISHED").all()
        return [m.to_dict() for m in matches]

def train_on_historical_data():
    """Entraîner l'IA sur les données historiques"""
    print("=" * 60)
    print("ENTRAÎNEMENT DE L'IA SUR LES MATCHS PASSÉS")
    print("=" * 60)
    print(f"Date: {datetime.now().isoformat()}")
    print()
    
    # Charger les matchs terminés
    print("Chargement des matchs terminés...")
    matches = load_finished_matches()
    print(f"Nombre de matchs terminés: {len(matches)}")
    print()
    
    if not matches:
        print("Aucun match terminé trouvé. Impossible d'entraîner l'IA.")
        return
    
    # Statistiques d'entraînement
    correct = 0
    total = 0
    errors_by_type = {"home_win_missed": 0, "draw_missed": 0, "away_win_missed": 0}
    
    print("Entraînement en cours...")
    for match in matches:
        home_team = match.get('home_team', {})
        away_team = match.get('away_team', {})
        league = match.get('league', {})
        
        home_name = home_team.get('name', '') if isinstance(home_team, dict) else str(home_team)
        away_name = away_team.get('name', '') if isinstance(away_team, dict) else str(away_team)
        league_name = league.get('name', '') if isinstance(league, dict) else str(league)
        
        if not home_name or not away_name:
            continue
        
        # Générer la prédiction
        prediction = improved_ai.predict_match(home_name, away_name, league_name, match)
        
        # Récupérer le résultat réel
        home_score = match.get('home_score', 0)
        away_score = match.get('away_score', 0)
        
        actual_result = {
            "home_score": home_score,
            "away_score": away_score
        }
        
        # Faire apprendre l'IA
        is_correct = improved_ai.learn_from_result(
            match.get('id', 0),
            prediction,
            actual_result
        )
        
        total += 1
        if is_correct:
            correct += 1
        else:
            # Analyser le type d'erreur
            actual_outcome = improved_ai.get_actual_outcome(actual_result)
            if actual_outcome == "1":
                errors_by_type["home_win_missed"] += 1
            elif actual_outcome == "X":
                errors_by_type["draw_missed"] += 1
            else:
                errors_by_type["away_win_missed"] += 1
    
    # Afficher les résultats
    print()
    print("=" * 60)
    print("RÉSULTATS DE L'ENTRAÎNEMENT")
    print("=" * 60)
    print(f"Matchs analysés: {total}")
    print(f"Prédictions correctes: {correct}")
    print(f"Précision: {(correct/total*100):.1f}%" if total > 0 else "N/A")
    print()
    print("Analyse des erreurs:")
    print(f"  - Victoires domicile manquées: {errors_by_type['home_win_missed']}")
    print(f"  - Matchs nuls manqués: {errors_by_type['draw_missed']}")
    print(f"  - Victoires extérieur manquées: {errors_by_type['away_win_missed']}")
    print()
    
    # Afficher les poids du modèle après entraînement
    print("Poids du modèle après entraînement:")
    model_stats = improved_ai.get_model_stats()
    print(f"  - Version: {model_stats['version']}")
    print(f"  - Précision: {model_stats['accuracy']:.1f}%")
    print(f"  - Avantage domicile: {model_stats['home_advantage']:.1f}%")
    print(f"  - Patterns appris:")
    for pattern, value in model_stats['learned_patterns'].items():
        print(f"    - {pattern}: {value*100:.1f}%")
    print()
    
    # Sauvegarder le modèle
    improved_ai.save_model()
    print("Modèle sauvegardé avec succès!")
    print()
    
    return {
        "total": total,
        "correct": correct,
        "accuracy": (correct/total*100) if total > 0 else 0,
        "errors_by_type": errors_by_type,
        "model_stats": model_stats
    }

def optimize_model_weights():
    """Optimiser les poids du modèle pour améliorer la précision"""
    print()
    print("=" * 60)
    print("OPTIMISATION DES POIDS DU MODÈLE")
    print("=" * 60)
    
    # Charger les matchs terminés
    matches = load_finished_matches()
    
    if len(matches) < 50:
        print("Pas assez de matchs pour l'optimisation (minimum 50 requis)")
        return
    
    # Analyser les patterns dans les données
    home_wins = 0
    draws = 0
    away_wins = 0
    high_scoring = 0  # Plus de 2.5 buts
    btts = 0  # Les deux équipes marquent
    
    for match in matches:
        home_score = match.get('home_score', 0)
        away_score = match.get('away_score', 0)
        
        if home_score > away_score:
            home_wins += 1
        elif home_score < away_score:
            away_wins += 1
        else:
            draws += 1
        
        if home_score + away_score > 2.5:
            high_scoring += 1
        
        if home_score > 0 and away_score > 0:
            btts += 1
    
    total = len(matches)
    
    # Mettre à jour les patterns appris
    improved_ai.weights["learned_patterns"]["home_win_rate"] = home_wins / total
    improved_ai.weights["learned_patterns"]["draw_rate"] = draws / total
    improved_ai.weights["learned_patterns"]["away_win_rate"] = away_wins / total
    improved_ai.weights["learned_patterns"]["over_2_5_rate"] = high_scoring / total
    improved_ai.weights["learned_patterns"]["btts_rate"] = btts / total
    
    print(f"Patterns mis à jour basés sur {total} matchs:")
    print(f"  - Victoires domicile: {home_wins/total*100:.1f}%")
    print(f"  - Matchs nuls: {draws/total*100:.1f}%")
    print(f"  - Victoires extérieur: {away_wins/total*100:.1f}%")
    print(f"  - Over 2.5 buts: {high_scoring/total*100:.1f}%")
    print(f"  - BTTS: {btts/total*100:.1f}%")
    print()
    
    # Ajuster l'avantage domicile basé sur les données réelles
    real_home_advantage = (home_wins / total) - 0.33  # 0.33 = probabilité aléatoire
    improved_ai.weights["home_advantage"] = max(0.05, min(0.25, real_home_advantage + 0.10))
    
    print(f"Avantage domicile ajusté: {improved_ai.weights['home_advantage']*100:.1f}%")
    
    # Sauvegarder le modèle optimisé
    improved_ai.save_model()
    print()
    print("Modèle optimisé et sauvegardé!")

def simulate_predictions():
    """Simuler des prédictions sur les matchs terminés pour évaluer la précision"""
    print()
    print("=" * 60)
    print("SIMULATION DE PRÉDICTIONS")
    print("=" * 60)
    
    matches = load_finished_matches()
    
    correct = 0
    total = 0
    
    for match in matches:
        home_team = match.get('home_team', {})
        away_team = match.get('away_team', {})
        league = match.get('league', {})
        
        home_name = home_team.get('name', '') if isinstance(home_team, dict) else str(home_team)
        away_name = away_team.get('name', '') if isinstance(away_team, dict) else str(away_team)
        league_name = league.get('name', '') if isinstance(league, dict) else str(league)
        
        if not home_name or not away_name:
            continue
        
        # Générer la prédiction
        prediction = improved_ai.predict_match(home_name, away_name, league_name, match)
        
        # Récupérer le résultat réel
        home_score = match.get('home_score', 0)
        away_score = match.get('away_score', 0)
        
        actual_result = {"home_score": home_score, "away_score": away_score}
        
        # Comparer
        predicted_outcome = improved_ai.get_predicted_outcome(prediction)
        actual_outcome = improved_ai.get_actual_outcome(actual_result)
        
        total += 1
        if predicted_outcome == actual_outcome:
            correct += 1
    
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"Matchs simulés: {total}")
    print(f"Prédictions correctes: {correct}")
    print(f"Précision simulée: {accuracy:.1f}%")
    print()
    
    return accuracy

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DÉMARRAGE DE L'ENTRAÎNEMENT DU MODÈLE IA")
    print("=" * 60 + "\n")
    
    # Étape 1: Entraîner sur les données historiques
    results = train_on_historical_data()
    
    # Étape 2: Optimiser les poids du modèle
    optimize_model_weights()
    
    # Étape 3: Simuler des prédictions pour évaluer
    final_accuracy = simulate_predictions()
    
    print("\n" + "=" * 60)
    print("RÉSUMÉ FINAL")
    print("=" * 60)
    print(f"Précision finale: {final_accuracy:.1f}%")
    print(f"Objectif: 80%")
    print(f"Écart: {80 - final_accuracy:.1f}%")
    print()
    
    if final_accuracy >= 80:
        print("✅ OBJECTIF ATTEINT!")
    else:
        print("⚠️ Objectif non atteint. Continuez à collecter des données et à entraîner le modèle.")
