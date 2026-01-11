"""
Script de comparaison entre l'Agent IA et le ML Classique
"""
import sys
import os
import json
import sqlite3
from datetime import datetime

# Ajouter le chemin du serveur
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.ai_agent_predictor import AIAgentPredictor
from scripts.ml_predictor_adapter import MLPredictorAdapter

class PredictionComparator:
    """Compare les prédictions de l'Agent IA vs ML Classique"""
    
    def __init__(self, db_path='/home/ubuntu/football-api-deploy/server/database/app.db'):
        self.db_path = db_path
        self.ai_agent = AIAgentPredictor()
        self.ml_engine = MLPredictorAdapter()
        
    def get_upcoming_matches(self, limit=5):
        """Récupère les prochains matchs à prédire"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                m.*,
                ht.name as home_team,
                at.name as away_team
            FROM match m
            JOIN team ht ON m.home_team_id = ht.id
            JOIN team at ON m.away_team_id = at.id
            WHERE m.status IN ('SCHEDULED', 'TIMED') 
            AND m.date > datetime('now')
            ORDER BY m.date ASC
            LIMIT ?
        """, (limit,))
        
        matches = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return matches
    
    def prepare_match_data(self, match):
        """Prépare les données du match pour l'analyse"""
        # Récupérer les statistiques des équipes depuis la DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Stats équipe domicile (derniers 10 matchs)
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN m.home_team_id = ? THEN m.home_score ELSE m.away_score END) as goals_avg,
                AVG(CASE WHEN m.home_team_id = ? THEN m.away_score ELSE m.home_score END) as conceded_avg
            FROM match m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.status = 'FINISHED'
            AND m.date > datetime('now', '-60 days')
        """, (match['home_team_id'], match['home_team_id'], match['home_team_id'], match['home_team_id']))
        
        home_stats = cursor.fetchone()
        
        # Stats équipe extérieure
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN m.home_team_id = ? THEN m.home_score ELSE m.away_score END) as goals_avg,
                AVG(CASE WHEN m.home_team_id = ? THEN m.away_score ELSE m.home_score END) as conceded_avg
            FROM match m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.status = 'FINISHED'
            AND m.date > datetime('now', '-60 days')
        """, (match['away_team_id'], match['away_team_id'], match['away_team_id'], match['away_team_id']))
        
        away_stats = cursor.fetchone()
        
        # Forme récente (derniers 5 matchs)
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN m.home_team_id = ? AND m.home_score > m.away_score THEN 'V'
                    WHEN m.away_team_id = ? AND m.away_score > m.home_score THEN 'V'
                    WHEN m.home_score = m.away_score THEN 'N'
                    ELSE 'D'
                END as result
            FROM match m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.status = 'FINISHED'
            ORDER BY m.date DESC
            LIMIT 5
        """, (match['home_team_id'], match['home_team_id'], match['home_team_id'], match['home_team_id']))
        
        home_form = ''.join([row[0] for row in cursor.fetchall()])
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN m.home_team_id = ? AND m.home_score > m.away_score THEN 'V'
                    WHEN m.away_team_id = ? AND m.away_score > m.home_score THEN 'V'
                    WHEN m.home_score = m.away_score THEN 'N'
                    ELSE 'D'
                END as result
            FROM match m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.status = 'FINISHED'
            ORDER BY m.date DESC
            LIMIT 5
        """, (match['away_team_id'], match['away_team_id'], match['away_team_id'], match['away_team_id']))
        
        away_form = ''.join([row[0] for row in cursor.fetchall()])
        
        conn.close()
        
        return {
            'home_team': match['home_team'],
            'away_team': match['away_team'],
            'home_form': home_form or 'N/A',
            'away_form': away_form or 'N/A',
            'home_goals_avg': home_stats[0] if home_stats[0] else 1.5,
            'away_goals_avg': away_stats[0] if away_stats[0] else 1.5,
            'home_conceded_avg': home_stats[1] if home_stats[1] else 1.5,
            'away_conceded_avg': away_stats[1] if away_stats[1] else 1.5,
            'h2h_history': 'Historique H2H non disponible'
        }
    
    def compare_match(self, match):
        """Compare les prédictions des deux systèmes pour un match"""
        
        print(f"\n{'='*80}")
        print(f"🏟️  {match['home_team']} vs {match['away_team']}")
        print(f"📅 {match['date']}")
        print(f"{'='*80}")
        
        # Préparer les données
        match_data = self.prepare_match_data(match)
        
        # Prédiction Agent IA
        print("\n🤖 AGENT IA (GPT-4) - Analyse en cours...")
        ai_prediction = self.ai_agent.analyze_match(match_data)
        
        # Prédiction ML Classique
        print("📊 ML CLASSIQUE - Calcul en cours...")
        ml_prediction = self.ml_engine.predict_match(match_data)
        
        # Afficher les résultats
        self._display_comparison(ai_prediction, ml_prediction)
        
        return {
            'match': match,
            'ai_prediction': ai_prediction,
            'ml_prediction': ml_prediction
        }
    
    def _display_comparison(self, ai_pred, ml_pred):
        """Affiche la comparaison des deux prédictions"""
        
        print("\n" + "─"*80)
        print("📊 COMPARAISON DES PRÉDICTIONS")
        print("─"*80)
        
        # Tableau de comparaison
        print(f"\n{'Métrique':<30} {'Agent IA':<25} {'ML Classique':<25}")
        print("─"*80)
        
        if ai_pred and ml_pred:
            print(f"{'Score prédit':<30} {ai_pred.get('predicted_score', 'N/A'):<25} {ml_pred.get('predicted_score', 'N/A'):<25}")
            print(f"{'Buts attendus':<30} {ai_pred.get('expected_goals', 'N/A'):<25} {ml_pred.get('expected_goals', 'N/A'):<25}")
            print(f"{'Prob. victoire domicile':<30} {ai_pred.get('win_probability_home', 'N/A')}%{'':<22} {ml_pred.get('win_probability_home', 'N/A')}%")
            print(f"{'Prob. victoire extérieur':<30} {ai_pred.get('win_probability_away', 'N/A')}%{'':<22} {ml_pred.get('win_probability_away', 'N/A')}%")
            print(f"{'Prob. match nul':<30} {ai_pred.get('draw_probability', 'N/A')}%{'':<22} {ml_pred.get('draw_probability', 'N/A')}%")
            print(f"{'Prob. BTTS':<30} {ai_pred.get('btts_probability', 'N/A')}%{'':<22} {ml_pred.get('btts_probability', 'N/A')}%")
            print(f"{'Confiance':<30} {ai_pred.get('confidence', 'N/A'):<25} {ml_pred.get('confidence', 'N/A'):<25}")
            
            if 'reasoning' in ai_pred:
                print(f"\n💡 Raisonnement Agent IA:")
                print(f"   {ai_pred['reasoning']}")
            
            if 'reasoning' in ml_pred:
                print(f"\n📊 Raisonnement ML Classique:")
                print(f"   {ml_pred['reasoning']}")
        
        print("\n" + "─"*80)
    
    def run_comparison(self, num_matches=5):
        """Lance la comparaison sur plusieurs matchs"""
        
        print("\n" + "="*80)
        print("🔬 COMPARAISON AGENT IA vs ML CLASSIQUE")
        print("="*80)
        
        matches = self.get_upcoming_matches(num_matches)
        
        if not matches:
            print("\n❌ Aucun match à venir trouvé dans la base de données")
            return
        
        print(f"\n✅ {len(matches)} matchs trouvés pour la comparaison\n")
        
        results = []
        for match in matches:
            result = self.compare_match(match)
            results.append(result)
        
        # Résumé final
        self._display_summary(results)
        
        return results
    
    def _display_summary(self, results):
        """Affiche un résumé de la comparaison"""
        
        print("\n" + "="*80)
        print("📈 RÉSUMÉ DE LA COMPARAISON")
        print("="*80)
        
        ai_avg_goals = sum([r['ai_prediction']['expected_goals'] for r in results if r['ai_prediction']]) / len(results)
        ml_avg_goals = sum([r['ml_prediction']['expected_goals'] for r in results if r['ml_prediction']]) / len(results)
        
        print(f"\n🎯 Buts attendus moyens:")
        print(f"   Agent IA: {ai_avg_goals:.2f}")
        print(f"   ML Classique: {ml_avg_goals:.2f}")
        
        print(f"\n💡 Observations:")
        print(f"   - L'Agent IA fournit un raisonnement détaillé pour chaque prédiction")
        print(f"   - Le ML Classique est plus rapide mais moins explicatif")
        print(f"   - Les deux systèmes peuvent être combinés pour une meilleure précision")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    comparator = PredictionComparator()
    comparator.run_comparison(num_matches=3)

