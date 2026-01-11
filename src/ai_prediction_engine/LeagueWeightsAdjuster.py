"""
Module d'Ajustement des Poids par Ligue v1.0
--------------------------------------------
Ajuste automatiquement les poids de prédiction selon les caractéristiques
spécifiques de chaque ligue.

Basé sur l'analyse des patterns historiques:
- Taux de victoires à domicile
- Taux de matchs nuls
- Tendance aux surprises (upsets)
- Nombre moyen de buts
"""

import json
import os
from datetime import datetime

class LeagueWeightsAdjuster:
    """Ajusteur de poids par ligue pour améliorer les prédictions"""
    
    def __init__(self):
        self.weights_file = "/home/ubuntu/football_app/instance/league_weights.json"
        self.weights = self._load_weights()
        
        # Caractéristiques par défaut des ligues (basées sur données historiques)
        self.default_league_profiles = {
            'Premier League': {
                'home_win_rate': 0.42,
                'draw_rate': 0.24,
                'away_win_rate': 0.34,
                'upset_rate': 0.18,  # Taux de surprises
                'goals_per_match': 2.85,
                'competitiveness': 0.75,  # Plus c'est élevé, plus la ligue est compétitive
                'home_advantage_factor': 1.10,
                'draw_boost': 0,
                'away_boost': 2,
                'confidence_adjustment': 0
            },
            'Championship': {
                'home_win_rate': 0.40,
                'draw_rate': 0.30,
                'away_win_rate': 0.30,
                'upset_rate': 0.25,
                'goals_per_match': 2.65,
                'competitiveness': 0.85,
                'home_advantage_factor': 1.08,
                'draw_boost': 8,  # Beaucoup de nuls
                'away_boost': 0,
                'confidence_adjustment': -5  # Réduire la confiance
            },
            'Bundesliga': {
                'home_win_rate': 0.44,
                'draw_rate': 0.24,
                'away_win_rate': 0.32,
                'upset_rate': 0.15,
                'goals_per_match': 3.10,
                'competitiveness': 0.65,
                'home_advantage_factor': 1.15,
                'draw_boost': 0,
                'away_boost': 0,
                'confidence_adjustment': 3
            },
            'LaLiga': {
                'home_win_rate': 0.45,
                'draw_rate': 0.25,
                'away_win_rate': 0.30,
                'upset_rate': 0.12,
                'goals_per_match': 2.55,
                'competitiveness': 0.60,
                'home_advantage_factor': 1.18,
                'draw_boost': 3,
                'away_boost': -3,
                'confidence_adjustment': 5
            },
            'Serie A': {
                'home_win_rate': 0.43,
                'draw_rate': 0.26,
                'away_win_rate': 0.31,
                'upset_rate': 0.14,
                'goals_per_match': 2.70,
                'competitiveness': 0.68,
                'home_advantage_factor': 1.12,
                'draw_boost': 4,
                'away_boost': 0,
                'confidence_adjustment': 2
            },
            'Ligue 1': {
                'home_win_rate': 0.44,
                'draw_rate': 0.26,
                'away_win_rate': 0.30,
                'upset_rate': 0.13,
                'goals_per_match': 2.60,
                'competitiveness': 0.55,  # PSG domine
                'home_advantage_factor': 1.14,
                'draw_boost': 4,
                'away_boost': -2,
                'confidence_adjustment': 4
            },
            'Eredivisie': {
                'home_win_rate': 0.42,
                'draw_rate': 0.27,
                'away_win_rate': 0.31,
                'upset_rate': 0.20,
                'goals_per_match': 3.05,
                'competitiveness': 0.72,
                'home_advantage_factor': 1.08,
                'draw_boost': 5,
                'away_boost': 2,
                'confidence_adjustment': -3
            },
            'Primeira Liga': {
                'home_win_rate': 0.43,
                'draw_rate': 0.28,
                'away_win_rate': 0.29,
                'upset_rate': 0.16,
                'goals_per_match': 2.45,
                'competitiveness': 0.65,
                'home_advantage_factor': 1.12,
                'draw_boost': 6,
                'away_boost': -2,
                'confidence_adjustment': 0
            },
            'Champions League': {
                'home_win_rate': 0.48,
                'draw_rate': 0.22,
                'away_win_rate': 0.30,
                'upset_rate': 0.10,
                'goals_per_match': 2.90,
                'competitiveness': 0.50,
                'home_advantage_factor': 1.20,
                'draw_boost': -2,
                'away_boost': 0,
                'confidence_adjustment': 8
            },
            'Europa League': {
                'home_win_rate': 0.45,
                'draw_rate': 0.23,
                'away_win_rate': 0.32,
                'upset_rate': 0.15,
                'goals_per_match': 2.75,
                'competitiveness': 0.60,
                'home_advantage_factor': 1.15,
                'draw_boost': 0,
                'away_boost': 2,
                'confidence_adjustment': 3
            }
        }
    
    def _load_weights(self):
        """Charger les poids sauvegardés"""
        if os.path.exists(self.weights_file):
            try:
                with open(self.weights_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"leagues": {}, "last_updated": None}
    
    def _save_weights(self):
        """Sauvegarder les poids"""
        self.weights["last_updated"] = datetime.now().isoformat()
        with open(self.weights_file, 'w') as f:
            json.dump(self.weights, f, indent=2)
    
    def get_league_profile(self, league_name):
        """Obtenir le profil d'une ligue"""
        # Convertir en string si c'est un objet
        if hasattr(league_name, 'name'):
            league_name = league_name.name
        league_name = str(league_name)
        
        # Chercher dans les profils par défaut
        for league, profile in self.default_league_profiles.items():
            if league.lower() in league_name.lower():
                # Fusionner avec les ajustements appris
                learned = self.weights.get("leagues", {}).get(league, {})
                merged = profile.copy()
                merged.update(learned)
                return merged
        
        # Profil par défaut si ligue inconnue
        return {
            'home_win_rate': 0.43,
            'draw_rate': 0.25,
            'away_win_rate': 0.32,
            'upset_rate': 0.15,
            'goals_per_match': 2.70,
            'competitiveness': 0.70,
            'home_advantage_factor': 1.10,
            'draw_boost': 0,
            'away_boost': 0,
            'confidence_adjustment': 0
        }
    
    def adjust_probabilities(self, home_prob, draw_prob, away_prob, league_name):
        """
        Ajuster les probabilités selon les caractéristiques de la ligue
        
        Args:
            home_prob: Probabilité de victoire domicile (%)
            draw_prob: Probabilité de nul (%)
            away_prob: Probabilité de victoire extérieur (%)
            league_name: Nom de la ligue
        
        Returns:
            dict: Probabilités ajustées
        """
        profile = self.get_league_profile(league_name)
        
        # Appliquer les ajustements
        adjusted_home = home_prob * profile['home_advantage_factor']
        adjusted_draw = draw_prob + profile['draw_boost']
        adjusted_away = away_prob + profile['away_boost']
        
        # Normaliser pour que le total fasse 100%
        total = adjusted_home + adjusted_draw + adjusted_away
        if total > 0:
            adjusted_home = (adjusted_home / total) * 100
            adjusted_draw = (adjusted_draw / total) * 100
            adjusted_away = (adjusted_away / total) * 100
        
        return {
            'home_prob': round(adjusted_home, 1),
            'draw_prob': round(adjusted_draw, 1),
            'away_prob': round(adjusted_away, 1),
            'confidence_adjustment': profile['confidence_adjustment'],
            'league_profile': profile
        }
    
    def should_predict_upset(self, favorite_prob, underdog_prob, league_name, strength_diff):
        """
        Déterminer si on devrait considérer une surprise (upset)
        
        Args:
            favorite_prob: Probabilité du favori
            underdog_prob: Probabilité de l'outsider
            league_name: Nom de la ligue
            strength_diff: Différence de force entre les équipes
        
        Returns:
            bool, str: (devrait considérer upset, raison)
        """
        profile = self.get_league_profile(league_name)
        
        # Ligues avec beaucoup de surprises
        if profile['upset_rate'] > 0.20:
            if favorite_prob < 60 and underdog_prob > 20:
                return True, f"Ligue avec beaucoup de surprises ({profile['upset_rate']*100:.0f}%)"
        
        # Ligues très compétitives
        if profile['competitiveness'] > 0.75:
            if strength_diff < 0.15 and underdog_prob > 25:
                return True, "Ligue très compétitive"
        
        # Faible différence de force
        if strength_diff < 0.08 and underdog_prob > 30:
            return True, "Équipes de niveau similaire"
        
        return False, None
    
    def get_recommended_bet_type(self, home_prob, draw_prob, away_prob, league_name):
        """
        Recommander le type de pari selon la ligue
        
        Returns:
            dict: Type de pari recommandé avec confiance
        """
        profile = self.get_league_profile(league_name)
        
        # Analyser les probabilités
        max_prob = max(home_prob, draw_prob, away_prob)
        prob_diff = max_prob - min(home_prob, draw_prob, away_prob)
        
        recommendations = []
        
        # Ligue avec beaucoup de nuls
        if profile['draw_rate'] > 0.26:
            if draw_prob > 28:
                recommendations.append({
                    'type': '1X ou X2',
                    'reason': f"Ligue avec {profile['draw_rate']*100:.0f}% de nuls",
                    'confidence': 'medium'
                })
        
        # Ligue avec fort avantage domicile
        if profile['home_advantage_factor'] > 1.15:
            if home_prob > 45:
                recommendations.append({
                    'type': '1 ou 1X',
                    'reason': f"Fort avantage domicile dans cette ligue",
                    'confidence': 'high'
                })
        
        # Ligue compétitive - éviter les paris simples
        if profile['competitiveness'] > 0.75 and prob_diff < 25:
            recommendations.append({
                'type': 'Double chance',
                'reason': "Ligue très compétitive, résultat incertain",
                'confidence': 'medium'
            })
        
        # Match ouvert dans une ligue avec beaucoup de buts
        if profile['goals_per_match'] > 2.8:
            recommendations.append({
                'type': 'Over 2.5',
                'reason': f"Ligue avec {profile['goals_per_match']:.1f} buts/match en moyenne",
                'confidence': 'medium'
            })
        
        # Pari simple si favori clair
        if max_prob > 55 and prob_diff > 30:
            winner = 'Domicile' if home_prob == max_prob else ('Extérieur' if away_prob == max_prob else 'Nul')
            recommendations.append({
                'type': f'Victoire {winner}',
                'reason': "Favori clair",
                'confidence': 'high'
            })
        
        if not recommendations:
            recommendations.append({
                'type': 'Double chance',
                'reason': "Match équilibré",
                'confidence': 'low'
            })
        
        return recommendations[0]  # Retourner la meilleure recommandation
    
    def update_league_weights(self, league_name, actual_results):
        """
        Mettre à jour les poids d'une ligue basé sur les résultats réels
        
        Args:
            league_name: Nom de la ligue
            actual_results: dict avec home_wins, draws, away_wins
        """
        total = actual_results.get('total', 0)
        if total < 10:
            return  # Pas assez de données
        
        # Calculer les nouveaux taux
        new_home_rate = actual_results.get('home_wins', 0) / total
        new_draw_rate = actual_results.get('draws', 0) / total
        new_away_rate = actual_results.get('away_wins', 0) / total
        
        # Obtenir le profil actuel
        profile = self.get_league_profile(league_name)
        
        # Calculer les ajustements nécessaires
        draw_diff = new_draw_rate - profile['draw_rate']
        if abs(draw_diff) > 0.03:
            # Ajuster le boost de nul
            new_draw_boost = profile['draw_boost'] + (draw_diff * 30)
            
            if league_name not in self.weights["leagues"]:
                self.weights["leagues"][league_name] = {}
            
            self.weights["leagues"][league_name]['draw_boost'] = round(new_draw_boost, 1)
            self.weights["leagues"][league_name]['draw_rate'] = round(new_draw_rate, 3)
            self.weights["leagues"][league_name]['last_updated'] = datetime.now().isoformat()
            
            self._save_weights()
    
    def get_league_analysis(self, league_name):
        """Obtenir une analyse complète d'une ligue"""
        profile = self.get_league_profile(league_name)
        
        analysis = {
            'league': league_name,
            'profile': profile,
            'characteristics': [],
            'betting_tips': []
        }
        
        # Caractéristiques
        if profile['draw_rate'] > 0.27:
            analysis['characteristics'].append("Beaucoup de matchs nuls")
        if profile['home_advantage_factor'] > 1.15:
            analysis['characteristics'].append("Fort avantage à domicile")
        if profile['competitiveness'] > 0.75:
            analysis['characteristics'].append("Ligue très compétitive")
        if profile['upset_rate'] > 0.18:
            analysis['characteristics'].append("Beaucoup de surprises")
        if profile['goals_per_match'] > 2.9:
            analysis['characteristics'].append("Beaucoup de buts")
        elif profile['goals_per_match'] < 2.5:
            analysis['characteristics'].append("Peu de buts")
        
        # Conseils de paris
        if profile['draw_rate'] > 0.27:
            analysis['betting_tips'].append("Privilégier les doubles chances (1X, X2)")
        if profile['competitiveness'] > 0.75:
            analysis['betting_tips'].append("Éviter les paris simples sur les matchs équilibrés")
        if profile['goals_per_match'] > 2.9:
            analysis['betting_tips'].append("Les Over 2.5 sont souvent gagnants")
        
        return analysis


# Instance globale
league_weights_adjuster = LeagueWeightsAdjuster()
