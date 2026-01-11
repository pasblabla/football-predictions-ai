"""\nAgent IA utilisant Claude 3.5 Sonnet pour l'analyse approfondie des matchs de football\n"""
import os
import json
import requests
from datetime import datetime

# Utiliser la clé API Forge fournie par Manus
FORGE_API_KEY = os.getenv('BUILT_IN_FORGE_API_KEY')
FORGE_API_URL = os.getenv('BUILT_IN_FORGE_API_URL', 'https://forge.manus.ai')

class AIAgentPredictor:
    """Agent IA qui raisonne pour prédire les matchs"""
    
    def __init__(self):
        self.api_key = FORGE_API_KEY
        self.api_url = FORGE_API_URL
        
    def analyze_match(self, match_data):
        """
        Analyse un match avec l'agent IA
        
        Args:
            match_data: Dict contenant les données du match
                - home_team: nom équipe domicile
                - away_team: nom équipe extérieure
                - home_form: forme récente domicile (ex: "VVNDD")
                - away_form: forme récente extérieur
                - home_goals_avg: moyenne buts marqués domicile
                - away_goals_avg: moyenne buts marqués extérieur
                - home_conceded_avg: moyenne buts encaissés domicile
                - away_conceded_avg: moyenne buts encaissés extérieur
                - h2h_history: historique confrontations directes
                
        Returns:
            Dict avec la prédiction de l'agent IA
        """
        
        # Construire le prompt pour l'agent IA
        prompt = self._build_analysis_prompt(match_data)
        
        # Appeler l'API Forge (GPT-4)
        try:
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Tu es un expert en analyse de matchs de football. Tu dois analyser les données fournies et faire une prédiction précise et argumentée."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3  # Faible température pour plus de cohérence
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = json.loads(result['choices'][0]['message']['content'])
                return self._format_prediction(ai_response, match_data)
            else:
                print(f"❌ Erreur API Forge: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de l'appel à l'agent IA: {e}")
            return None
    
    def _build_analysis_prompt(self, match_data):
        """Construit le prompt d'analyse pour l'agent IA"""
        
        prompt = f"""
Analyse ce match de football et fournis une prédiction détaillée.

**MATCH:** {match_data['home_team']} vs {match_data['away_team']}

**FORME RÉCENTE:**
- {match_data['home_team']}: {match_data.get('home_form', 'N/A')} ({match_data.get('home_goals_avg', 0):.1f} buts/match, {match_data.get('home_conceded_avg', 0):.1f} encaissés/match)
- {match_data['away_team']}: {match_data.get('away_form', 'N/A')} ({match_data.get('away_goals_avg', 0):.1f} buts/match, {match_data.get('away_conceded_avg', 0):.1f} encaissés/match)

**HISTORIQUE H2H:**
{match_data.get('h2h_history', 'Aucun historique disponible')}

**INSTRUCTIONS:**
Analyse ces données et fournis une prédiction au format JSON avec:
- predicted_score_home: score prédit équipe domicile (entier)
- predicted_score_away: score prédit équipe extérieure (entier)
- expected_goals: nombre total de buts attendus (float, 1 décimale)
- win_probability_home: probabilité victoire domicile (0-100)
- win_probability_away: probabilité victoire extérieure (0-100)
- draw_probability: probabilité match nul (0-100)
- btts_probability: probabilité que les deux équipes marquent (0-100)
- confidence: niveau de confiance (Élevée/Moyenne/Faible)
- reasoning: explication détaillée de ton raisonnement (2-3 phrases)

Sois précis et base-toi sur les statistiques réelles fournies.
"""
        return prompt
    
    def _format_prediction(self, ai_response, match_data):
        """Formate la réponse de l'IA"""
        
        return {
            'method': 'AI_AGENT',
            'home_team': match_data['home_team'],
            'away_team': match_data['away_team'],
            'predicted_score': f"{ai_response['predicted_score_home']}-{ai_response['predicted_score_away']}",
            'expected_goals': ai_response['expected_goals'],
            'win_probability_home': ai_response['win_probability_home'],
            'win_probability_away': ai_response['win_probability_away'],
            'draw_probability': ai_response['draw_probability'],
            'btts_probability': ai_response['btts_probability'],
            'confidence': ai_response['confidence'],
            'reasoning': ai_response['reasoning'],
            'timestamp': datetime.now().isoformat()
        }


# Test de l'agent IA
if __name__ == "__main__":
    agent = AIAgentPredictor()
    
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
    
    print("🤖 Test de l'agent IA...")
    prediction = agent.analyze_match(test_match)
    
    if prediction:
        print("\n✅ Prédiction de l'agent IA:")
        print(json.dumps(prediction, indent=2, ensure_ascii=False))
    else:
        print("\n❌ Échec de la prédiction")

