"""
Moteur de Fusion Hybride - Combine Agent IA (GPT-4) et ML Classique
Produit UNE SEULE prédiction optimale en fusionnant les deux approches
"""
import sys
import os
import sqlite3
import requests
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.ai_agent_predictor import AIAgentPredictor
from scripts.ml_predictor_adapter import MLPredictorAdapter
from scripts.complete_match_analyzer import CompleteMatchAnalyzer

class HybridPredictor:
    """
    Système Hybride Unifié qui combine:
    - Agent IA (GPT-4): Analyse contextuelle + raisonnement
    - ML Classique: Apprentissage continu + ajustements historiques
    
    Produit UNE SEULE prédiction optimale
    """
    
    def __init__(self, db_path='/home/ubuntu/football-api-deploy/server/database/app.db'):
        self.db_path = db_path
        self.ai_agent = AIAgentPredictor()
        self.ml_engine = MLPredictorAdapter()
        self.analyzer = CompleteMatchAnalyzer()  # Analyseur complet
        self.learning_coefficients = self._load_learning_coefficients()
    
    def _load_learning_coefficients(self):
        """
        Charge les coefficients d'apprentissage depuis la base de données
        Ces coefficients sont ajustés automatiquement par le ML
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier si la table learning_history existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='learning_history'
            """)
            
            if not cursor.fetchone():
                conn.close()
                return self._default_coefficients()
            
            # Récupérer les derniers coefficients
            cursor.execute("""
                SELECT 
                    home_win_adjustment,
                    away_win_adjustment,
                    draw_adjustment,
                    goals_adjustment
                FROM learning_history
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'home_win': result[0] or 0,
                    'away_win': result[1] or 0,
                    'draw': result[2] or 0,
                    'goals': result[3] or 0
                }
            else:
                return self._default_coefficients()
                
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement des coefficients: {e}")
            return self._default_coefficients()
    
    def _default_coefficients(self):
        """Coefficients par défaut si pas d'historique d'apprentissage"""
        return {
            'home_win': 0,
            'away_win': 0,
            'draw': 0,
            'goals': 0
        }
    
    def predict(self, match_data):
        """
        Produit UNE prédiction hybride unifiée
        
        Args:
            match_data: Dict avec les données du match
            
        Returns:
            Dict avec la prédiction hybride unifiée
        """
        
        print(f"\n🔄 PRÉDICTION HYBRIDE: {match_data['home_team']} vs {match_data['away_team']}")
        
        # 0. ANALYSE COMPLÈTE (H2H, forme, absences, conditions)
        print("   🔍 Analyse complète: H2H + Forme + Conditions...")
        try:
            complete_analysis = self.analyzer.analyze_match(match_data)
            # Enrichir match_data avec l'analyse complète
            match_data['complete_analysis'] = complete_analysis
            match_data['h2h_analysis'] = complete_analysis.get('h2h', {})
            match_data['impact_summary'] = complete_analysis.get('impact_summary', {})
        except Exception as e:
            print(f"   ⚠️  Erreur analyse complète: {e}")
            match_data['complete_analysis'] = None
        
        # 1. Obtenir la prédiction de l'Agent IA (analyse contextuelle)
        print("   🤖 Agent IA: Analyse en cours...")
        ai_prediction = self.ai_agent.analyze_match(match_data)
        
        # 2. Obtenir la prédiction du ML (basée sur les moyennes)
        print("   📊 ML Classique: Calcul en cours...")
        ml_prediction = self.ml_engine.predict_match(match_data)
        
        # 3. FUSION: Combiner les deux prédictions
        print("   🔄 Fusion: Combinaison des deux approches...")
        hybrid_prediction = self._fuse_predictions(ai_prediction, ml_prediction, match_data)
        
        print(f"   ✅ Prédiction hybride: {hybrid_prediction['predicted_score']} ({hybrid_prediction['expected_goals']} buts)")
        
        return hybrid_prediction
    
    def _fuse_predictions(self, ai_pred, ml_pred, match_data):
        """
        Fusionne les prédictions de l'Agent IA et du ML
        
        Stratégie:
        1. Utiliser le raisonnement de l'Agent IA (plus riche)
        2. Ajuster les probabilités avec les coefficients du ML
        3. Calculer la confiance selon la convergence des deux systèmes
        """
        
        # Appliquer les ajustements d'apprentissage du ML
        adjusted_home = ai_pred['win_probability_home'] + self.learning_coefficients['home_win']
        adjusted_away = ai_pred['win_probability_away'] + self.learning_coefficients['away_win']
        adjusted_draw = ai_pred['draw_probability'] + self.learning_coefficients['draw']
        
        # Normaliser pour que la somme = 100%
        total = adjusted_home + adjusted_away + adjusted_draw
        if total > 0:
            adjusted_home = round((adjusted_home / total) * 100)
            adjusted_away = round((adjusted_away / total) * 100)
            adjusted_draw = 100 - adjusted_home - adjusted_away
        else:
            adjusted_home = ai_pred['win_probability_home']
            adjusted_away = ai_pred['win_probability_away']
            adjusted_draw = ai_pred['draw_probability']
        
        # Ajuster les buts attendus
        adjusted_goals = ai_pred['expected_goals'] + self.learning_coefficients['goals']
        adjusted_goals = max(0.5, min(6.0, adjusted_goals))  # Limiter entre 0.5 et 6.0
        
        # Calculer la convergence (similarité entre IA et ML)
        convergence = self._calculate_convergence(ai_pred, ml_pred)
        
        # Déterminer la confiance
        if convergence > 80:
            confidence = "Très Élevée"
            confidence_icon = "🎯"
        elif convergence > 60:
            confidence = "Élevée"
            confidence_icon = "✅"
        elif convergence > 40:
            confidence = "Moyenne"
            confidence_icon = "⚖️"
        else:
            confidence = "Faible"
            confidence_icon = "⚠️"
        
        # Enrichir le raisonnement avec les ajustements ML
        enhanced_reasoning = self._enhance_reasoning(
            ai_pred['reasoning'],
            self.learning_coefficients,
            convergence
        )
        
        # Calculer le score prédit basé sur les probabilités ajustées
        predicted_score = self._calculate_predicted_score(
            adjusted_home,
            adjusted_away,
            adjusted_draw,
            adjusted_goals,
            match_data
        )
        
        # Générer les buteurs probables
        probable_scorers = self._generate_probable_scorers(match_data)
        
        result = {
            'method': 'HYBRID_UNIFIED',
            'home_team': match_data['home_team'],
            'away_team': match_data['away_team'],
            'predicted_score': predicted_score,
            'expected_goals': round(adjusted_goals, 1),
            'win_probability_home': adjusted_home,
            'win_probability_away': adjusted_away,
            'draw_probability': adjusted_draw,
            'btts_probability': ai_pred['btts_probability'],  # Garder l'analyse IA
            'confidence': confidence,
            'confidence_icon': confidence_icon,
            'convergence': convergence,
            'reasoning': enhanced_reasoning,
            'ai_analysis': ai_pred['reasoning'],  # Garder l'analyse originale de l'IA
            'ml_adjustments': self.learning_coefficients,
            'timestamp': datetime.now().isoformat()
        }
        
        # Ajouter les buteurs probables si disponibles
        if probable_scorers:
            result['probable_scorers'] = probable_scorers
        
        return result
    
    def _calculate_convergence(self, ai_pred, ml_pred):
        """
        Calcule le taux de convergence entre les deux prédictions
        Plus les deux systèmes sont d'accord, plus la confiance est élevée
        """
        
        # Différences sur les probabilités
        home_diff = abs(ai_pred['win_probability_home'] - ml_pred['win_probability_home'])
        away_diff = abs(ai_pred['win_probability_away'] - ml_pred['win_probability_away'])
        draw_diff = abs(ai_pred['draw_probability'] - ml_pred['draw_probability'])
        
        # Différence sur les buts
        goals_diff = abs(ai_pred['expected_goals'] - ml_pred['expected_goals'])
        
        # Score de convergence (100 = accord parfait, 0 = désaccord total)
        prob_convergence = 100 - ((home_diff + away_diff + draw_diff) / 3)
        goals_convergence = 100 - (goals_diff * 20)  # 1 but de diff = -20%
        
        # Moyenne pondérée
        convergence = (prob_convergence * 0.7 + goals_convergence * 0.3)
        
        return round(convergence)
    
    def _enhance_reasoning(self, ai_reasoning, coefficients, convergence):
        """
        Enrichit le raisonnement de l'IA avec les ajustements du ML
        """
        
        enhanced = ai_reasoning
        
        # Ajouter une note sur la confiance
        if convergence > 70:
            enhanced += f" Les deux systèmes (IA + ML) convergent fortement ({convergence}%), ce qui renforce la fiabilité de cette prédiction."
        elif convergence < 50:
            enhanced += f" Attention: divergence entre les systèmes ({convergence}%), prédiction moins fiable."
        
        # Mentionner les ajustements ML si significatifs
        if abs(coefficients['goals']) > 0.2:
            direction = "à la hausse" if coefficients['goals'] > 0 else "à la baisse"
            enhanced += f" Le système d'apprentissage a ajusté les buts attendus {direction} basé sur l'historique."
        
        return enhanced
    
    def _calculate_predicted_score(self, prob_home, prob_away, prob_draw, expected_goals, match_data):
        """
        Calcule le score prédit basé sur les probabilités et les buts attendus
        """
        
        # Répartir les buts selon les probabilités
        home_ratio = prob_home / (prob_home + prob_away + 0.01)
        away_ratio = prob_away / (prob_home + prob_away + 0.01)
        
        # Calculer les buts pour chaque équipe
        if prob_home > prob_away + 15:  # Victoire domicile claire
            home_goals = round(expected_goals * 0.6)
            away_goals = round(expected_goals * 0.4)
        elif prob_away > prob_home + 15:  # Victoire extérieur claire
            home_goals = round(expected_goals * 0.4)
            away_goals = round(expected_goals * 0.6)
        elif prob_draw > max(prob_home, prob_away):  # Match nul probable
            goals_each = expected_goals / 2
            home_goals = round(goals_each)
            away_goals = round(goals_each)
        else:  # Match équilibré
            home_goals = round(expected_goals * home_ratio)
            away_goals = round(expected_goals * away_ratio)
        
        # Assurer qu'il y a au moins quelques buts si expected_goals > 2
        if expected_goals > 2 and home_goals + away_goals < 2:
            home_goals = 1
            away_goals = 1
        
        return f"{home_goals}-{away_goals}"
    
    def _generate_probable_scorers(self, match_data):
        """
        Génère les buteurs probables pour un match
        Utilise l'API football-data.org pour récupérer les VRAIS meilleurs buteurs avec statistiques réelles
        """
        API_KEY = '647c75a7ce7f482598c8240664bd856c'
        BASE_URL = 'https://api.football-data.org/v4'
        
        probable_scorers = {
            'home': [],
            'away': []
        }
        
        try:
            # Récupérer le code de la ligue depuis match_data
            league_code = match_data.get('league_code', 'PL')  # Par défaut Premier League
            
            headers = {'X-Auth-Token': API_KEY}
            
            # Récupérer les meilleurs buteurs de la compétition
            scorers_response = requests.get(
                f"{BASE_URL}/competitions/{league_code}/scorers?limit=50",
                headers=headers,
                timeout=10
            )
            
            if scorers_response.status_code != 200:
                print(f"⚠️  Erreur API buteurs ({league_code}): {scorers_response.status_code}")
                return None
            
            all_scorers = scorers_response.json().get('scorers', [])
            
            if not all_scorers:
                print(f"⚠️  Aucun buteur trouvé pour {league_code}")
                return None
            
            # Récupérer les external_id des équipes
            home_external_id = match_data.get('home_external_id')
            away_external_id = match_data.get('away_external_id')
            
            if not home_external_id or not away_external_id:
                print(f"⚠️  External IDs manquants: home={home_external_id}, away={away_external_id}")
                return None
            
            # Filtrer les buteurs de l'équipe domicile
            home_scorers = [s for s in all_scorers if s.get('team', {}).get('id') == home_external_id]
            away_scorers = [s for s in all_scorers if s.get('team', {}).get('id') == away_external_id]
            
            # Calculer les probabilités basées sur les buts réels
            def calculate_probability(goals, total_goals):
                if total_goals == 0:
                    return 30
                return min(int((goals / total_goals) * 100), 95)
            
            # Buteurs domicile (top 3)
            home_total_goals = sum(s.get('goals', 0) for s in home_scorers[:3])
            for scorer in home_scorers[:3]:
                player = scorer.get('player', {})
                goals = scorer.get('goals', 0)
                prob = calculate_probability(goals, home_total_goals) if home_total_goals > 0 else 35
                
                probable_scorers['home'].append({
                    'name': player.get('name', 'Joueur inconnu'),
                    'probability': prob,
                    'goals_season': goals
                })
            
            # Buteurs extérieur (top 3)
            away_total_goals = sum(s.get('goals', 0) for s in away_scorers[:3])
            for scorer in away_scorers[:3]:
                player = scorer.get('player', {})
                goals = scorer.get('goals', 0)
                prob = calculate_probability(goals, away_total_goals) if away_total_goals > 0 else 30
                
                probable_scorers['away'].append({
                    'name': player.get('name', 'Joueur inconnu'),
                    'probability': prob,
                    'goals_season': goals
                })
            
            # Si pas de buteurs trouvés, retourner None
            if not probable_scorers['home'] and not probable_scorers['away']:
                print(f"⚠️  Aucun buteur trouvé pour les équipes {home_external_id} vs {away_external_id}")
                return None
            
            print(f"✅ Buteurs récupérés: {len(probable_scorers['home'])} domicile, {len(probable_scorers['away'])} extérieur")
            return probable_scorers
            
        except Exception as e:
            print(f"⚠️  Erreur génération buteurs: {e}")
            import traceback
            traceback.print_exc()
            return None


# Test du système hybride
if __name__ == "__main__":
    predictor = HybridPredictor()
    
    # Test avec un match exemple
    test_match = {
        'home_team': 'Manchester City',
        'away_team': 'Liverpool',
        'home_form': 'VVVNV',
        'away_form': 'VVDVN',
        'home_goals_avg': 2.4,
        'away_goals_avg': 2.1,
        'home_conceded_avg': 0.8,
        'away_conceded_avg': 1.0,
        'h2h_history': 'Derniers 5 matchs: Man City 3-1, Liverpool 2-2, Man City 1-0, Liverpool 3-0, Man City 4-1'
    }
    
    print("🔄 Test du système hybride unifié...")
    prediction = predictor.predict(test_match)
    
    print("\n" + "="*80)
    print("📊 PRÉDICTION HYBRIDE UNIFIÉE")
    print("="*80)
    print(f"Match: {prediction['home_team']} vs {prediction['away_team']}")
    print(f"Score prédit: {prediction['predicted_score']}")
    print(f"Buts attendus: {prediction['expected_goals']}")
    print(f"Probabilités: {prediction['win_probability_home']}% - {prediction['draw_probability']}% - {prediction['win_probability_away']}%")
    print(f"Confiance: {prediction['confidence_icon']} {prediction['confidence']} (convergence: {prediction['convergence']}%)")
    print(f"\n💡 Raisonnement:")
    print(f"   {prediction['reasoning']}")
    print("="*80)

