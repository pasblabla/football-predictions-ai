"""
Système d'apprentissage automatique pour l'IA hybride
Analyse automatiquement les erreurs et ajuste les coefficients
"""
import sys
import os
import sqlite3
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

DB_PATH = '/home/ubuntu/football-api-deploy/server/database/app.db'
LEARNING_FILE = '/home/ubuntu/football-api-deploy/server/learning_coefficients.json'

class AutoLearningSystem:
    """Système d'apprentissage automatique"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.load_coefficients()
    
    def load_coefficients(self):
        """Charge les coefficients d'apprentissage"""
        if os.path.exists(LEARNING_FILE):
            with open(LEARNING_FILE, 'r') as f:
                self.coefficients = json.load(f)
        else:
            # Coefficients par défaut
            self.coefficients = {
                'home_advantage': 1.0,
                'form_weight': 1.0,
                'goals_weight': 1.0,
                'btts_threshold': 0.5,
                'precision': 0.0,
                'total_analyzed': 0,
                'correct_predictions': 0,
                'errors_by_type': {
                    'wrong_winner': 0,
                    'wrong_score': 0,
                    'wrong_btts': 0,
                    'wrong_goals': 0
                },
                'last_update': datetime.now().isoformat()
            }
    
    def save_coefficients(self):
        """Sauvegarde les coefficients"""
        self.coefficients['last_update'] = datetime.now().isoformat()
        with open(LEARNING_FILE, 'w') as f:
            json.dump(self.coefficients, f, indent=2)
        print(f"✅ Coefficients sauvegardés")
    
    def analyze_finished_matches(self, days_back=7):
        """Analyse les matchs terminés récents"""
        print(f"\n🔍 Analyse des matchs terminés (derniers {days_back} jours)...")
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Récupérer les matchs terminés avec prédictions
        self.cursor.execute("""
            SELECT 
                m.id,
                m.home_score,
                m.away_score,
                ht.name as home_team,
                at.name as away_team,
                p.predicted_score_home,
                p.predicted_score_away,
                p.predicted_winner,
                p.prob_home_win,
                p.prob_draw,
                p.prob_away_win,
                p.prob_both_teams_score,
                m.date
            FROM match m
            JOIN team ht ON m.home_team_id = ht.id
            JOIN team at ON m.away_team_id = at.id
            LEFT JOIN prediction p ON m.id = p.match_id
            WHERE m.status = 'FINISHED'
            AND m.home_score IS NOT NULL
            AND m.away_score IS NOT NULL
            AND m.date >= ?
            ORDER BY m.date DESC
        """, (cutoff_date,))
        
        matches = [dict(row) for row in self.cursor.fetchall()]
        
        if not matches:
            print("⚠️  Aucun match terminé trouvé")
            return
        
        print(f"📊 {len(matches)} matchs à analyser")
        
        analyzed = 0
        correct = 0
        errors = {
            'wrong_winner': [],
            'wrong_score': [],
            'wrong_btts': [],
            'wrong_goals': []
        }
        
        for match in matches:
            if not match['predicted_winner']:
                continue  # Pas de prédiction
            
            analyzed += 1
            
            # Résultat réel
            real_home = match['home_score']
            real_away = match['away_score']
            
            if real_home > real_away:
                real_winner = 'home'
            elif real_away > real_home:
                real_winner = 'away'
            else:
                real_winner = 'draw'
            
            real_btts = (real_home > 0 and real_away > 0)
            real_total_goals = real_home + real_away
            
            # Prédiction
            pred_winner = match['predicted_winner']
            pred_home = match['predicted_score_home'] or 0
            pred_away = match['predicted_score_away'] or 0
            pred_total_goals = pred_home + pred_away
            
            # Analyse des erreurs
            is_correct = True
            
            # 1. Vainqueur
            if pred_winner != real_winner:
                is_correct = False
                errors['wrong_winner'].append({
                    'match': f"{match['home_team']} vs {match['away_team']}",
                    'predicted': pred_winner,
                    'actual': real_winner,
                    'score': f"{real_home}-{real_away}",
                    'prob_home': match['prob_home_win'],
                    'prob_draw': match['prob_draw'],
                    'prob_away': match['prob_away_win']
                })
            
            # 2. Score exact
            if pred_home != real_home or pred_away != real_away:
                errors['wrong_score'].append({
                    'match': f"{match['home_team']} vs {match['away_team']}",
                    'predicted': f"{pred_home}-{pred_away}",
                    'actual': f"{real_home}-{real_away}",
                    'diff_goals': abs(pred_total_goals - real_total_goals)
                })
            
            # 3. BTTS
            pred_btts = match['prob_both_teams_score'] > 0.5 if match['prob_both_teams_score'] else False
            if pred_btts != real_btts:
                errors['wrong_btts'].append({
                    'match': f"{match['home_team']} vs {match['away_team']}",
                    'predicted_btts': pred_btts,
                    'actual_btts': real_btts,
                    'score': f"{real_home}-{real_away}"
                })
            
            # 4. Nombre de buts
            if abs(pred_total_goals - real_total_goals) >= 2:
                errors['wrong_goals'].append({
                    'match': f"{match['home_team']} vs {match['away_team']}",
                    'predicted_goals': pred_total_goals,
                    'actual_goals': real_total_goals,
                    'diff': abs(pred_total_goals - real_total_goals)
                })
            
            if is_correct:
                correct += 1
        
        # Calculer la précision
        precision = (correct / analyzed * 100) if analyzed > 0 else 0
        
        print(f"\n📈 RÉSULTATS D'ANALYSE")
        print(f"="*60)
        print(f"Matchs analysés: {analyzed}")
        print(f"Prédictions correctes: {correct}")
        print(f"Précision: {precision:.1f}%")
        print(f"\n❌ ERREURS PAR TYPE:")
        print(f"  - Mauvais vainqueur: {len(errors['wrong_winner'])}")
        print(f"  - Mauvais score: {len(errors['wrong_score'])}")
        print(f"  - Mauvais BTTS: {len(errors['wrong_btts'])}")
        print(f"  - Mauvais nombre de buts: {len(errors['wrong_goals'])}")
        
        # Mettre à jour les coefficients
        self.coefficients['precision'] = precision
        self.coefficients['total_analyzed'] = analyzed
        self.coefficients['correct_predictions'] = correct
        self.coefficients['errors_by_type'] = {
            'wrong_winner': len(errors['wrong_winner']),
            'wrong_score': len(errors['wrong_score']),
            'wrong_btts': len(errors['wrong_btts']),
            'wrong_goals': len(errors['wrong_goals'])
        }
        
        # Ajuster les coefficients selon les erreurs
        self.adjust_coefficients(errors, analyzed)
        
        # Sauvegarder
        self.save_coefficients()
        
        return {
            'analyzed': analyzed,
            'correct': correct,
            'precision': precision,
            'errors': errors
        }
    
    def adjust_coefficients(self, errors, total):
        """Ajuste automatiquement les coefficients selon les erreurs"""
        print(f"\n🔧 AJUSTEMENT DES COEFFICIENTS...")
        
        # 1. Ajuster l'avantage domicile
        wrong_winner = errors['wrong_winner']
        if wrong_winner:
            home_errors = sum(1 for e in wrong_winner if e['predicted'] == 'home' and e['actual'] != 'home')
            away_errors = sum(1 for e in wrong_winner if e['predicted'] == 'away' and e['actual'] != 'away')
            
            if home_errors > away_errors:
                # Trop d'avantage domicile
                self.coefficients['home_advantage'] *= 0.95
                print(f"  ↓ Avantage domicile réduit: {self.coefficients['home_advantage']:.3f}")
            elif away_errors > home_errors:
                # Pas assez d'avantage domicile
                self.coefficients['home_advantage'] *= 1.05
                print(f"  ↑ Avantage domicile augmenté: {self.coefficients['home_advantage']:.3f}")
        
        # 2. Ajuster le poids de la forme
        if len(errors['wrong_winner']) > total * 0.4:
            # Trop d'erreurs sur le vainqueur, augmenter le poids de la forme
            self.coefficients['form_weight'] *= 1.1
            print(f"  ↑ Poids de la forme augmenté: {self.coefficients['form_weight']:.3f}")
        
        # 3. Ajuster le poids des buts
        if len(errors['wrong_goals']) > total * 0.3:
            # Trop d'erreurs sur les buts
            self.coefficients['goals_weight'] *= 1.1
            print(f"  ↑ Poids des buts augmenté: {self.coefficients['goals_weight']:.3f}")
        
        # 4. Ajuster le seuil BTTS
        if len(errors['wrong_btts']) > total * 0.3:
            btts_errors_too_high = sum(1 for e in errors['wrong_btts'] if e['predicted_btts'] and not e['actual_btts'])
            btts_errors_too_low = sum(1 for e in errors['wrong_btts'] if not e['predicted_btts'] and e['actual_btts'])
            
            if btts_errors_too_high > btts_errors_too_low:
                # Trop optimiste sur BTTS
                self.coefficients['btts_threshold'] += 0.05
                print(f"  ↑ Seuil BTTS augmenté: {self.coefficients['btts_threshold']:.2f}")
            elif btts_errors_too_low > btts_errors_too_high:
                # Pas assez optimiste sur BTTS
                self.coefficients['btts_threshold'] -= 0.05
                print(f"  ↓ Seuil BTTS réduit: {self.coefficients['btts_threshold']:.2f}")
        
        print(f"✅ Coefficients ajustés automatiquement")
    
    def close(self):
        """Ferme la connexion"""
        self.conn.close()

def run_auto_learning():
    """Lance l'apprentissage automatique"""
    print("🤖 SYSTÈME D'APPRENTISSAGE AUTOMATIQUE")
    print("="*60)
    
    system = AutoLearningSystem()
    
    try:
        # Analyser les 7 derniers jours
        results = system.analyze_finished_matches(days_back=7)
        
        if results:
            print(f"\n✅ Apprentissage terminé")
            print(f"📊 Précision actuelle: {results['precision']:.1f}%")
            print(f"🎯 Objectif: 85%+")
            
            if results['precision'] < 70:
                print(f"⚠️  Précision faible, l'IA continue d'apprendre...")
            elif results['precision'] >= 85:
                print(f"🎉 Excellente précision atteinte !")
        
    finally:
        system.close()

if __name__ == "__main__":
    run_auto_learning()
