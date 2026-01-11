import json
import os
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

class AIPredictionEngine:
    def __init__(self, learning_file_path="/home/ubuntu/football-api/data/ai_learning.json"):
        self.learning_file = learning_file_path
        self.learning_data = self.load_learning_data()
        
        # Facteurs de performance par équipe (simulés mais réalistes)
        self.team_performance = {
            # Premier League
            "Manchester City": {"attack": 0.92, "defense": 0.88, "form": 0.90},
            "Arsenal": {"attack": 0.85, "defense": 0.82, "form": 0.87},
            "Liverpool": {"attack": 0.88, "defense": 0.80, "form": 0.85},
            "Chelsea": {"attack": 0.78, "defense": 0.75, "form": 0.76},
            
            # Ligue 1
            "Paris Saint-Germain": {"attack": 0.95, "defense": 0.85, "form": 0.92},
            "Marseille": {"attack": 0.75, "defense": 0.72, "form": 0.74},
            "Lyon": {"attack": 0.78, "defense": 0.70, "form": 0.75},
            "Monaco": {"attack": 0.82, "defense": 0.76, "form": 0.80},
            
            # Bundesliga
            "Bayern Munich": {"attack": 0.94, "defense": 0.87, "form": 0.91},
            "Borussia Dortmund": {"attack": 0.86, "defense": 0.78, "form": 0.83},
            "RB Leipzig": {"attack": 0.80, "defense": 0.82, "form": 0.81},
            "Bayer Leverkusen": {"attack": 0.83, "defense": 0.79, "form": 0.82},
            
            # Serie A
            "Juventus": {"attack": 0.82, "defense": 0.85, "form": 0.84},
            "Inter Milan": {"attack": 0.85, "defense": 0.83, "form": 0.86},
            "AC Milan": {"attack": 0.80, "defense": 0.78, "form": 0.79},
            "Napoli": {"attack": 0.83, "defense": 0.80, "form": 0.82},
            
            # LaLiga
            "Real Madrid": {"attack": 0.93, "defense": 0.86, "form": 0.90},
            "Barcelona": {"attack": 0.89, "defense": 0.81, "form": 0.87},
            "Atletico Madrid": {"attack": 0.78, "defense": 0.88, "form": 0.83},
            "Sevilla": {"attack": 0.75, "defense": 0.77, "form": 0.76}
        }
        
        # Facteurs de probabilité de but par joueur (simulés)
        self.player_goal_probability = {
            # Attaquants vedettes
            "Erling Haaland": 0.65,
            "Kylian Mbappé": 0.62,
            "Harry Kane": 0.58,
            "Robert Lewandowski": 0.60,
            "Karim Benzema": 0.55,
            "Mohamed Salah": 0.52,
            "Sadio Mané": 0.48,
            "Vinicius Jr": 0.45,
            "Luka Modrić": 0.25,
            "Kevin De Bruyne": 0.35,
            # Milieux offensifs
            "Bruno Fernandes": 0.40,
            "Mason Mount": 0.30,
            "Pedri": 0.25,
            "Gavi": 0.22,
            # Défenseurs
            "Virgil van Dijk": 0.15,
            "Sergio Ramos": 0.18,
            "Marquinhos": 0.12
        }
    
    def load_learning_data(self) -> Dict:
        """Charger les données d'apprentissage depuis le fichier JSON"""
        try:
            os.makedirs(os.path.dirname(self.learning_file), exist_ok=True)
            if os.path.exists(self.learning_file):
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    "total_predictions": 0,
                    "correct_predictions": 0,
                    "accuracy_rate": 0.0,
                    "prediction_history": [],
                    "team_accuracy": {},
                    "league_accuracy": {},
                    "confidence_accuracy": {}
                }
        except Exception as e:
            print(f"Erreur lors du chargement des données d'apprentissage: {e}")
            return {
                "total_predictions": 0,
                "correct_predictions": 0,
                "accuracy_rate": 0.0,
                "prediction_history": [],
                "team_accuracy": {},
                "league_accuracy": {},
                "confidence_accuracy": {}
            }
    
    def save_learning_data(self):
        """Sauvegarder les données d'apprentissage"""
        try:
            with open(self.learning_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données d'apprentissage: {e}")
    
    def calculate_team_strength(self, team_name: str) -> float:
        """Calculer la force globale d'une équipe"""
        if team_name in self.team_performance:
            perf = self.team_performance[team_name]
            return (perf["attack"] + perf["defense"] + perf["form"]) / 3
        else:
            # Valeur par défaut pour les équipes non répertoriées
            return random.uniform(0.4, 0.7)
    
    def calculate_match_probabilities(self, home_team: str, away_team: str, league_name: str) -> Dict[str, float]:
        """Calculer les probabilités d'un match avec l'IA"""
        
        # Récupérer les performances des équipes
        home_strength = self.calculate_team_strength(home_team)
        away_strength = self.calculate_team_strength(away_team)
        
        # Avantage du terrain (5-15%)
        home_advantage = random.uniform(0.05, 0.15)
        home_strength += home_advantage
        
        # Facteur de compétition (les matchs européens sont plus équilibrés)
        if "Champions League" in league_name or "Europa League" in league_name:
            balance_factor = 0.1
            home_strength = (home_strength + away_strength) / 2 + random.uniform(-balance_factor, balance_factor)
            away_strength = (home_strength + away_strength) / 2 + random.uniform(-balance_factor, balance_factor)
        
        # Calculer les probabilités de base
        strength_diff = home_strength - away_strength
        
        # Probabilité de victoire domicile
        prob_home = 0.4 + (strength_diff * 0.3)
        prob_home = max(0.1, min(0.8, prob_home))
        
        # Probabilité de victoire extérieur
        prob_away = 0.4 - (strength_diff * 0.3)
        prob_away = max(0.1, min(0.8, prob_away))
        
        # Probabilité de match nul
        prob_draw = 1.0 - prob_home - prob_away
        prob_draw = max(0.1, prob_draw)
        
        # Normaliser pour que la somme soit 1
        total = prob_home + prob_draw + prob_away
        prob_home /= total
        prob_draw /= total
        prob_away /= total
        
        # Autres prédictions
        avg_strength = (home_strength + away_strength) / 2
        prob_over_2_5 = min(0.9, max(0.3, avg_strength + random.uniform(-0.2, 0.2)))
        prob_bts = min(0.9, max(0.2, avg_strength * 0.8 + random.uniform(-0.15, 0.15)))
        
        return {
            "prob_home_win": round(prob_home, 3),
            "prob_draw": round(prob_draw, 3),
            "prob_away_win": round(prob_away, 3),
            "prob_over_2_5": round(prob_over_2_5, 3),
            "prob_both_teams_score": round(prob_bts, 3)
        }
    
    def calculate_confidence_level(self, probabilities: Dict[str, float]) -> str:
        """Calculer le niveau de confiance basé sur les probabilités"""
        max_prob = max(probabilities["prob_home_win"], probabilities["prob_draw"], probabilities["prob_away_win"])
        
        # Ajuster selon l'historique d'apprentissage
        accuracy_bonus = self.learning_data["accuracy_rate"] * 0.1
        max_prob += accuracy_bonus
        
        if max_prob >= 0.65:
            return "Élevée"
        elif max_prob >= 0.45:
            return "Moyenne"
        else:
            return "Faible"
    
    def generate_tactical_analysis(self, home_team: str, away_team: str, probabilities: Dict[str, float]) -> str:
        """Générer une analyse tactique intelligente"""
        
        home_strength = self.calculate_team_strength(home_team)
        away_strength = self.calculate_team_strength(away_team)
        
        strength_diff = abs(home_strength - away_strength)
        
        if strength_diff < 0.1:
            analyses = [
                f"Match équilibré entre {home_team} et {away_team}, les deux équipes ont des forces similaires",
                f"Duel tactique serré attendu, {home_team} aura l'avantage du terrain",
                f"Les deux équipes sont au même niveau, le détail fera la différence"
            ]
        elif home_strength > away_strength:
            analyses = [
                f"{home_team} présente un avantage tactique significatif à domicile",
                f"La supériorité offensive de {home_team} devrait faire la différence",
                f"{home_team} favori logique grâce à sa forme actuelle"
            ]
        else:
            analyses = [
                f"{away_team} montre une supériorité tactique malgré le déplacement",
                f"La qualité de {away_team} pourrait compenser l'avantage du terrain",
                f"{away_team} arrive en confiance et peut créer la surprise"
            ]
        
        # Ajouter des éléments selon les probabilités
        if probabilities["prob_over_2_5"] > 0.7:
            analyses.append("Match spectaculaire en perspective avec de nombreux buts attendus")
        elif probabilities["prob_over_2_5"] < 0.4:
            analyses.append("Défenses solides des deux côtés, match serré attendu")
        
        return random.choice(analyses)
    
    def get_reliable_matches(self, matches: List[Dict], count: int = None) -> List[Dict]:
        """Sélectionner les matchs les plus fiables selon l'IA"""
        
        if count is None:
            count = random.randint(1, min(10, len(matches)))
        
        # Calculer un score de fiabilité pour chaque match
        reliable_matches = []
        
        for match in matches:
            if not match.get('predictions'):
                continue
                
            pred = match['predictions']
            
            # Score basé sur la confiance
            confidence_score = 0
            if pred.get('confidence_level') == 'Élevée':
                confidence_score = 0.8
            elif pred.get('confidence_level') == 'Moyenne':
                confidence_score = 0.5
            else:
                confidence_score = 0.2
            
            # Score basé sur la différence de probabilités
            probs = [pred.get('prob_home_win', 0), pred.get('prob_draw', 0), pred.get('prob_away_win', 0)]
            max_prob = max(probs)
            prob_diff_score = max_prob - 0.33  # Plus c'est éloigné de 33%, plus c'est fiable
            
            # Score basé sur l'historique des équipes
            home_team = match.get('home_team', {}).get('name', '')
            away_team = match.get('away_team', {}).get('name', '')
            
            team_score = 0
            if home_team in self.team_performance and away_team in self.team_performance:
                team_score = 0.3  # Bonus pour les équipes connues
            
            # Score final
            reliability_score = confidence_score + prob_diff_score + team_score
            
            reliable_matches.append({
                'match': match,
                'reliability_score': reliability_score
            })
        
        # Trier par score de fiabilité et prendre les meilleurs
        reliable_matches.sort(key=lambda x: x['reliability_score'], reverse=True)
        
        return [item['match'] for item in reliable_matches[:count]]
    
    def get_player_goal_probabilities(self, team_name: str) -> List[Dict[str, Any]]:
        """Obtenir les probabilités de but des joueurs d'une équipe"""
        
        # Joueurs simulés par équipe (en réalité, cela viendrait de l'API)
        team_players = {
            "Manchester City": ["Erling Haaland", "Kevin De Bruyne", "Phil Foden"],
            "Paris Saint-Germain": ["Kylian Mbappé", "Neymar Jr", "Lionel Messi"],
            "Bayern Munich": ["Harry Kane", "Thomas Müller", "Leroy Sané"],
            "Real Madrid": ["Karim Benzema", "Vinicius Jr", "Luka Modrić"],
            "Barcelona": ["Robert Lewandowski", "Pedri", "Gavi"]
        }
        
        players = team_players.get(team_name, [f"Joueur {i+1}" for i in range(3)])
        
        player_probabilities = []
        for player in players:
            base_prob = self.player_goal_probability.get(player, random.uniform(0.1, 0.4))
            
            # Ajuster selon la forme de l'équipe
            team_form = self.team_performance.get(team_name, {}).get("form", 0.5)
            adjusted_prob = base_prob * (0.8 + team_form * 0.4)
            
            player_probabilities.append({
                "name": player,
                "goal_probability": round(adjusted_prob, 3),
                "position": self._get_player_position(player)
            })
        
        return sorted(player_probabilities, key=lambda x: x["goal_probability"], reverse=True)
    
    def _get_player_position(self, player_name: str) -> str:
        """Obtenir la position d'un joueur (simulé)"""
        attackers = ["Erling Haaland", "Kylian Mbappé", "Harry Kane", "Robert Lewandowski", "Karim Benzema"]
        midfielders = ["Kevin De Bruyne", "Luka Modrić", "Pedri", "Bruno Fernandes"]
        
        if player_name in attackers:
            return "Attaquant"
        elif player_name in midfielders:
            return "Milieu"
        else:
            return "Attaquant"  # Par défaut
    
    def learn_from_result(self, match_id: int, predicted_winner: str, actual_home_score: int, actual_away_score: int):
        """Apprendre d'un résultat de match pour améliorer les prédictions futures"""
        
        # Déterminer le vainqueur réel
        if actual_home_score > actual_away_score:
            actual_winner = "home"
        elif actual_away_score > actual_home_score:
            actual_winner = "away"
        else:
            actual_winner = "draw"
        
        # Vérifier si la prédiction était correcte
        is_correct = predicted_winner == actual_winner
        
        # Mettre à jour les statistiques globales
        self.learning_data["total_predictions"] += 1
        if is_correct:
            self.learning_data["correct_predictions"] += 1
        
        # Recalculer le taux de précision
        self.learning_data["accuracy_rate"] = self.learning_data["correct_predictions"] / self.learning_data["total_predictions"]
        
        # Ajouter à l'historique
        self.learning_data["prediction_history"].append({
            "match_id": match_id,
            "predicted": predicted_winner,
            "actual": actual_winner,
            "correct": is_correct,
            "date": datetime.now().isoformat(),
            "home_score": actual_home_score,
            "away_score": actual_away_score
        })
        
        # Garder seulement les 1000 dernières prédictions
        if len(self.learning_data["prediction_history"]) > 1000:
            self.learning_data["prediction_history"] = self.learning_data["prediction_history"][-1000:]
        
        # Sauvegarder les données
        self.save_learning_data()
        
        return {
            "match_id": match_id,
            "prediction_correct": is_correct,
            "new_accuracy_rate": self.learning_data["accuracy_rate"],
            "total_predictions": self.learning_data["total_predictions"]
        }
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques de performance de l'IA"""
        return {
            "total_predictions": self.learning_data["total_predictions"],
            "correct_predictions": self.learning_data["correct_predictions"],
            "accuracy_rate": round(self.learning_data["accuracy_rate"] * 100, 2),
            "recent_form": self._calculate_recent_form(),
            "improvement_trend": self._calculate_improvement_trend()
        }
    
    def _calculate_recent_form(self) -> float:
        """Calculer la forme récente (20 dernières prédictions)"""
        recent_predictions = self.learning_data["prediction_history"][-20:]
        if not recent_predictions:
            return 0.0
        
        correct_recent = sum(1 for pred in recent_predictions if pred["correct"])
        return round((correct_recent / len(recent_predictions)) * 100, 2)
    
    def _calculate_improvement_trend(self) -> str:
        """Calculer la tendance d'amélioration"""
        if len(self.learning_data["prediction_history"]) < 40:
            return "Données insuffisantes"
        
        first_half = self.learning_data["prediction_history"][-40:-20]
        second_half = self.learning_data["prediction_history"][-20:]
        
        first_accuracy = sum(1 for pred in first_half if pred["correct"]) / len(first_half)
        second_accuracy = sum(1 for pred in second_half if pred["correct"]) / len(second_half)
        
        diff = second_accuracy - first_accuracy
        
        if diff > 0.1:
            return "En forte amélioration"
        elif diff > 0.05:
            return "En amélioration"
        elif diff > -0.05:
            return "Stable"
        elif diff > -0.1:
            return "En baisse légère"
        else:
            return "En baisse"

