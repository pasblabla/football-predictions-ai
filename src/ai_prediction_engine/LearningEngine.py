"""
Module d'Apprentissage Continu v1.0
-----------------------------------
Ce module analyse les erreurs passées et génère des facteurs de correction
pour améliorer les prédictions SANS modifier l'IA hybride existante.

Les corrections sont sauvegardées dans un fichier JSON et lues par l'IA hybride.
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

class LearningEngine:
    """Moteur d'apprentissage qui analyse les erreurs et génère des corrections"""
    
    def __init__(self):
        self.corrections_file = "/home/ubuntu/football_app/instance/learned_corrections.json"
        self.history_file = "/home/ubuntu/football_app/instance/learning_history.json"
        os.makedirs(os.path.dirname(self.corrections_file), exist_ok=True)
        
        # Charger les corrections existantes
        self.corrections = self._load_corrections()
        self.learning_history = self._load_history()
    
    def _load_corrections(self):
        """Charger les corrections apprises"""
        default_corrections = {
            "version": "1.0",
            "last_updated": None,
            "global": {
                "home_advantage_boost": 0.0,      # Ajustement avantage domicile
                "away_penalty": 0.0,               # Pénalité extérieur
                "draw_boost": 0.0,                 # Boost pour les nuls
                "confidence_threshold_home": 55,   # Seuil pour prédire domicile
                "confidence_threshold_away": 45,   # Seuil pour prédire extérieur
                "confidence_threshold_draw": 30,   # Seuil pour prédire nul
            },
            "by_league": {},
            "by_team_strength_diff": {
                "large_diff": {"home_boost": 0, "away_boost": 0},    # Diff > 20%
                "medium_diff": {"home_boost": 0, "away_boost": 0},   # Diff 10-20%
                "small_diff": {"draw_boost": 0},                      # Diff < 10%
            },
            "patterns": {
                "high_scoring_leagues": [],
                "low_scoring_leagues": [],
                "draw_prone_leagues": [],
                "home_dominant_leagues": [],
                "upset_prone_leagues": [],
            }
        }
        
        if os.path.exists(self.corrections_file):
            try:
                with open(self.corrections_file, 'r') as f:
                    loaded = json.load(f)
                    # Fusionner avec les valeurs par défaut
                    for key in default_corrections:
                        if key not in loaded:
                            loaded[key] = default_corrections[key]
                    return loaded
            except:
                pass
        
        return default_corrections
    
    def _load_history(self):
        """Charger l'historique d'apprentissage"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"sessions": [], "total_improvements": 0}
    
    def _save_corrections(self):
        """Sauvegarder les corrections"""
        self.corrections["last_updated"] = datetime.now().isoformat()
        with open(self.corrections_file, 'w') as f:
            json.dump(self.corrections, f, indent=2)
    
    def _save_history(self):
        """Sauvegarder l'historique"""
        with open(self.history_file, 'w') as f:
            json.dump(self.learning_history, f, indent=2)
    
    def analyze_and_learn(self, matches_with_predictions):
        """
        Analyser les matchs terminés et apprendre des erreurs
        
        Args:
            matches_with_predictions: Liste de tuples (match, prediction, actual_result)
        
        Returns:
            dict: Rapport d'apprentissage
        """
        if not matches_with_predictions:
            return {"status": "no_data", "message": "Aucune donnée à analyser"}
        
        # Statistiques d'analyse
        stats = {
            "total": len(matches_with_predictions),
            "correct": 0,
            "incorrect": 0,
            "by_prediction_type": {
                "HOME": {"total": 0, "correct": 0},
                "AWAY": {"total": 0, "correct": 0},
                "DRAW": {"total": 0, "correct": 0},
            },
            "by_league": defaultdict(lambda: {"total": 0, "correct": 0, "draws": 0, "missed_draws": 0}),
            "missed_draws": 0,
            "false_favorites": 0,
            "upsets_missed": 0,
        }
        
        # Analyser chaque match
        for match, prediction, actual in matches_with_predictions:
            predicted = prediction.get("predicted_winner", "HOME")
            
            stats["by_prediction_type"][predicted]["total"] += 1
            
            league = match.get("league", "Unknown")
            stats["by_league"][league]["total"] += 1
            
            if actual == "DRAW":
                stats["by_league"][league]["draws"] += 1
            
            if predicted == actual:
                stats["correct"] += 1
                stats["by_prediction_type"][predicted]["correct"] += 1
                stats["by_league"][league]["correct"] += 1
            else:
                stats["incorrect"] += 1
                
                # Analyser le type d'erreur
                if actual == "DRAW" and predicted != "DRAW":
                    stats["missed_draws"] += 1
                    stats["by_league"][league]["missed_draws"] += 1
                
                if predicted == "HOME" and actual == "AWAY":
                    stats["upsets_missed"] += 1
                
                if predicted in ["HOME", "AWAY"] and actual != predicted:
                    stats["false_favorites"] += 1
        
        # Calculer les corrections basées sur l'analyse
        corrections_applied = self._calculate_corrections(stats)
        
        # Sauvegarder les corrections
        self._save_corrections()
        
        # Enregistrer la session d'apprentissage
        session = {
            "date": datetime.now().isoformat(),
            "matches_analyzed": stats["total"],
            "accuracy_before": round(stats["correct"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
            "corrections_applied": corrections_applied,
        }
        self.learning_history["sessions"].append(session)
        self._save_history()
        
        return {
            "status": "success",
            "stats": stats,
            "corrections_applied": corrections_applied,
            "new_accuracy_target": self._estimate_new_accuracy(stats, corrections_applied),
        }
    
    def _calculate_corrections(self, stats):
        """Calculer les corrections basées sur les statistiques d'erreurs"""
        corrections_applied = []
        
        # 1. Correction pour les matchs nuls manqués
        if stats["total"] > 0:
            missed_draw_rate = stats["missed_draws"] / stats["total"]
            if missed_draw_rate > 0.15:  # Plus de 15% de nuls manqués
                # Augmenter le boost pour les nuls
                old_boost = self.corrections["global"]["draw_boost"]
                new_boost = min(old_boost + 5, 15)  # Max +15%
                self.corrections["global"]["draw_boost"] = new_boost
                
                # Baisser le seuil de détection des nuls
                old_threshold = self.corrections["global"]["confidence_threshold_draw"]
                new_threshold = max(old_threshold - 3, 22)  # Min 22%
                self.corrections["global"]["confidence_threshold_draw"] = new_threshold
                
                corrections_applied.append({
                    "type": "draw_detection",
                    "reason": f"{stats['missed_draws']} matchs nuls manqués ({round(missed_draw_rate*100, 1)}%)",
                    "action": f"draw_boost: {old_boost} → {new_boost}, threshold: {old_threshold} → {new_threshold}"
                })
        
        # 2. Correction pour les victoires extérieur
        away_stats = stats["by_prediction_type"]["AWAY"]
        if away_stats["total"] > 5:
            away_accuracy = away_stats["correct"] / away_stats["total"]
            if away_accuracy < 0.35:  # Moins de 35% de précision
                # Augmenter le seuil pour prédire extérieur
                old_threshold = self.corrections["global"]["confidence_threshold_away"]
                new_threshold = min(old_threshold + 5, 55)  # Max 55%
                self.corrections["global"]["confidence_threshold_away"] = new_threshold
                
                corrections_applied.append({
                    "type": "away_prediction",
                    "reason": f"Précision extérieur faible: {round(away_accuracy*100, 1)}%",
                    "action": f"confidence_threshold_away: {old_threshold} → {new_threshold}"
                })
        
        # 3. Correction pour les victoires domicile
        home_stats = stats["by_prediction_type"]["HOME"]
        if home_stats["total"] > 5:
            home_accuracy = home_stats["correct"] / home_stats["total"]
            if home_accuracy < 0.50:  # Moins de 50% de précision
                # Augmenter le seuil pour prédire domicile
                old_threshold = self.corrections["global"]["confidence_threshold_home"]
                new_threshold = min(old_threshold + 3, 65)  # Max 65%
                self.corrections["global"]["confidence_threshold_home"] = new_threshold
                
                corrections_applied.append({
                    "type": "home_prediction",
                    "reason": f"Précision domicile faible: {round(home_accuracy*100, 1)}%",
                    "action": f"confidence_threshold_home: {old_threshold} → {new_threshold}"
                })
        
        # 4. Corrections par ligue
        for league, league_stats in stats["by_league"].items():
            if league_stats["total"] < 5:
                continue
            
            league_accuracy = league_stats["correct"] / league_stats["total"]
            draw_rate = league_stats["draws"] / league_stats["total"]
            missed_draw_rate = league_stats["missed_draws"] / league_stats["total"] if league_stats["total"] > 0 else 0
            
            if league not in self.corrections["by_league"]:
                self.corrections["by_league"][league] = {
                    "draw_boost": 0,
                    "home_boost": 0,
                    "away_boost": 0,
                    "accuracy": league_accuracy,
                }
            
            # Ligue avec beaucoup de nuls
            if draw_rate > 0.30:
                old_boost = self.corrections["by_league"][league].get("draw_boost", 0)
                new_boost = min(old_boost + 5, 15)
                self.corrections["by_league"][league]["draw_boost"] = new_boost
                
                if league not in self.corrections["patterns"]["draw_prone_leagues"]:
                    self.corrections["patterns"]["draw_prone_leagues"].append(league)
                
                corrections_applied.append({
                    "type": "league_draw",
                    "reason": f"{league}: {round(draw_rate*100, 1)}% de nuls",
                    "action": f"draw_boost pour {league}: {old_boost} → {new_boost}"
                })
            
            # Mettre à jour la précision de la ligue
            self.corrections["by_league"][league]["accuracy"] = round(league_accuracy * 100, 1)
        
        return corrections_applied
    
    def _estimate_new_accuracy(self, stats, corrections_applied):
        """Estimer la nouvelle précision après corrections"""
        current_accuracy = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        
        # Estimer l'amélioration basée sur les corrections
        estimated_improvement = 0
        
        for correction in corrections_applied:
            if correction["type"] == "draw_detection":
                # Chaque correction de nul peut améliorer de 2-5%
                estimated_improvement += min(stats["missed_draws"] * 0.5, 5)
            elif correction["type"] == "away_prediction":
                estimated_improvement += 2
            elif correction["type"] == "home_prediction":
                estimated_improvement += 1.5
            elif correction["type"] == "league_draw":
                estimated_improvement += 1
        
        return round(min(current_accuracy + estimated_improvement, 75), 1)
    
    def get_corrections(self):
        """Retourner les corrections actuelles pour l'IA hybride"""
        return self.corrections
    
    def get_league_correction(self, league_name):
        """Obtenir les corrections spécifiques à une ligue"""
        return self.corrections["by_league"].get(league_name, {
            "draw_boost": 0,
            "home_boost": 0,
            "away_boost": 0,
        })
    
    def should_predict_draw(self, home_prob, away_prob, draw_prob, league=None):
        """
        Décider si on devrait prédire un nul basé sur les corrections apprises
        
        Returns:
            tuple: (should_predict_draw, adjusted_draw_prob)
        """
        # Appliquer le boost global (réduit pour éviter la sur-prédiction)
        adjusted_draw = draw_prob + (self.corrections["global"]["draw_boost"] * 0.5)
        
        # Appliquer le boost de ligue si disponible (réduit aussi)
        if league and league in self.corrections["by_league"]:
            adjusted_draw += self.corrections["by_league"][league].get("draw_boost", 0) * 0.5
        
        # Vérifier si la ligue est prone aux nuls
        if league in self.corrections["patterns"].get("draw_prone_leagues", []):
            adjusted_draw += 2
        
        threshold = self.corrections["global"]["confidence_threshold_draw"]
        
        # Conditions TRÈS STRICTES pour prédire un nul (pour éviter la sur-prédiction)
        # On prédit un nul SEULEMENT si:
        # 1. La probabilité ajustée de nul est >= seuil + 10 ET
        # 2. Les équipes sont VRAIMENT très proches (diff < 3%)
        # 3. Aucune équipe n'est clairement favorite (< 55%)
        should_draw = (
            adjusted_draw >= threshold + 10 and  # Seuil très strict
            abs(home_prob - away_prob) < 3 and  # Différence très faible
            home_prob < 55 and  # Domicile pas trop favori
            away_prob < 45  # Extérieur pas trop favori
        )
        
        return should_draw, min(adjusted_draw, 35)  # Cap à 35%
    
    def adjust_probabilities(self, home_prob, draw_prob, away_prob, league=None):
        """
        Ajuster les probabilités basées sur les corrections apprises
        
        Returns:
            tuple: (adjusted_home, adjusted_draw, adjusted_away)
        """
        # Corrections globales
        adj_home = home_prob + self.corrections["global"]["home_advantage_boost"]
        adj_away = away_prob + self.corrections["global"]["away_penalty"]
        adj_draw = draw_prob + self.corrections["global"]["draw_boost"]
        
        # Corrections par ligue
        if league and league in self.corrections["by_league"]:
            league_corr = self.corrections["by_league"][league]
            adj_home += league_corr.get("home_boost", 0)
            adj_away += league_corr.get("away_boost", 0)
            adj_draw += league_corr.get("draw_boost", 0)
        
        # Normaliser pour que le total = 100
        total = adj_home + adj_draw + adj_away
        if total > 0:
            adj_home = adj_home / total * 100
            adj_draw = adj_draw / total * 100
            adj_away = adj_away / total * 100
        
        return round(adj_home, 1), round(adj_draw, 1), round(adj_away, 1)
    
    def get_prediction_thresholds(self):
        """Retourner les seuils de confiance ajustés"""
        return {
            "home": self.corrections["global"]["confidence_threshold_home"],
            "away": self.corrections["global"]["confidence_threshold_away"],
            "draw": self.corrections["global"]["confidence_threshold_draw"],
        }


# Instance globale
learning_engine = LearningEngine()
