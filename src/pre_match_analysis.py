#!/usr/bin/env python3
"""
Analyse Pré-Match Automatique
Vérifie les matchs dans l'heure suivante et analyse:
- Joueurs clés absents/blessés/suspendus
- Composition réelle des équipes
- Tactique mise en place
- Ajuste les prédictions en dernière minute
"""

import sys
import os
import requests
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Optional

# Configuration
DB_PATH = "/home/ubuntu/football-api-deploy/server/database/football.db"
API_KEY = "647c75a7ce7f482598c8240664bd856c"
API_BASE = "https://api.football-data.org/v4"

class PreMatchAnalyzer:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.api_key = API_KEY
        self.headers = {"X-Auth-Token": self.api_key}
    
    def get_upcoming_matches(self, hours_ahead: int = 1) -> List[Dict]:
        """Récupère les matchs dans les prochaines heures"""
        now = datetime.utcnow()
        time_window_start = now + timedelta(minutes=50)  # 50min avant pour avoir le temps
        time_window_end = now + timedelta(hours=hours_ahead, minutes=10)
        
        query = """
        SELECT 
            m.id, m.external_id, m.date,
            ht.name as home_team, at.name as away_team,
            l.name as league
        FROM matches m
        JOIN teams ht ON ht.id = m.home_team_id
        JOIN teams at ON at.id = m.away_team_id
        JOIN leagues l ON l.id = m.league_id
        WHERE m.status = 'SCHEDULED'
        AND m.date BETWEEN ? AND ?
        ORDER BY m.date ASC
        """
        
        self.cursor.execute(query, (
            time_window_start.strftime('%Y-%m-%d %H:%M:%S'),
            time_window_end.strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        matches = []
        for row in self.cursor.fetchall():
            matches.append({
                'id': row[0],
                'external_id': row[1],
                'date': row[2],
                'home_team': row[3],
                'away_team': row[4],
                'league': row[5]
            })
        
        return matches
    
    def fetch_match_details(self, external_id: int) -> Optional[Dict]:
        """Récupère les détails d'un match depuis l'API"""
        try:
            url = f"{API_BASE}/matches/{external_id}"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Erreur API pour match {external_id}: {e}")
            return None
    
    def analyze_lineup(self, match_data: Dict) -> Dict:
        """Analyse la composition d'équipe"""
        analysis = {
            'home_formation': None,
            'away_formation': None,
            'home_lineup': [],
            'away_lineup': [],
            'home_bench': [],
            'away_bench': [],
            'key_absences': []
        }
        
        if not match_data:
            return analysis
        
        home_team = match_data.get('homeTeam', {})
        away_team = match_data.get('awayTeam', {})
        
        # Formations
        analysis['home_formation'] = home_team.get('formation')
        analysis['away_formation'] = away_team.get('formation')
        
        # Lineup
        analysis['home_lineup'] = home_team.get('lineup', [])
        analysis['away_lineup'] = away_team.get('lineup', [])
        
        # Bench
        analysis['home_bench'] = home_team.get('bench', [])
        analysis['away_bench'] = away_team.get('bench', [])
        
        return analysis
    
    def detect_tactical_changes(self, analysis: Dict) -> List[str]:
        """Détecte les changements tactiques importants"""
        changes = []
        
        # Formation défensive vs offensive
        defensive_formations = ['5-4-1', '5-3-2', '4-5-1', '4-4-2']
        offensive_formations = ['4-3-3', '4-2-3-1', '3-4-3', '3-5-2']
        
        home_form = analysis['home_formation']
        away_form = analysis['away_formation']
        
        if home_form in defensive_formations:
            changes.append(f"🛡️ Équipe domicile: formation défensive ({home_form})")
        elif home_form in offensive_formations:
            changes.append(f"⚔️ Équipe domicile: formation offensive ({home_form})")
        
        if away_form in defensive_formations:
            changes.append(f"🛡️ Équipe extérieure: formation défensive ({away_form})")
        elif away_form in offensive_formations:
            changes.append(f"⚔️ Équipe extérieure: formation offensive ({away_form})")
        
        return changes
    
    def calculate_impact(self, analysis: Dict) -> float:
        """Calcule l'impact des changements sur les prédictions"""
        impact = 0.0
        
        # Si lineup vide, pas d'impact calculable
        if not analysis['home_lineup'] and not analysis['away_lineup']:
            return 0.0
        
        # Formation défensive = moins de buts attendus
        defensive_formations = ['5-4-1', '5-3-2', '4-5-1', '4-4-2']
        
        if analysis['home_formation'] in defensive_formations:
            impact -= 0.3  # -0.3 buts
        if analysis['away_formation'] in defensive_formations:
            impact -= 0.3
        
        # Si les deux équipes sont défensives
        if (analysis['home_formation'] in defensive_formations and 
            analysis['away_formation'] in defensive_formations):
            impact -= 0.5  # Match très fermé
        
        return impact
    
    def update_prediction(self, match_id: int, impact: float, notes: str):
        """Met à jour la prédiction avec les nouvelles informations"""
        if abs(impact) < 0.1:
            return  # Impact négligeable
        
        # Récupérer la prédiction actuelle
        self.cursor.execute("""
            SELECT predicted_score_home, predicted_score_away, ai_recommendation
            FROM predictions
            WHERE match_id = ?
        """, (match_id,))
        
        result = self.cursor.fetchone()
        if not result:
            return
        
        pred_home, pred_away, old_recommendation = result
        
        # Ajuster le score prédit
        total_goals = (pred_home or 0) + (pred_away or 0)
        new_total = max(0, total_goals + impact)
        
        # Redistribuer proportionnellement
        if total_goals > 0:
            ratio_home = pred_home / total_goals
            ratio_away = pred_away / total_goals
            new_pred_home = round(new_total * ratio_home)
            new_pred_away = round(new_total * ratio_away)
        else:
            new_pred_home = round(new_total / 2)
            new_pred_away = round(new_total / 2)
        
        # Mettre à jour
        new_recommendation = f"⚠️ ANALYSE PRÉ-MATCH: {notes}\n\n{old_recommendation or ''}"
        
        self.cursor.execute("""
            UPDATE predictions
            SET predicted_score_home = ?,
                predicted_score_away = ?,
                ai_recommendation = ?
            WHERE match_id = ?
        """, (new_pred_home, new_pred_away, new_recommendation, match_id))
        
        self.conn.commit()
        
        print(f"  ✅ Prédiction mise à jour: {pred_home}-{pred_away} → {new_pred_home}-{new_pred_away}")
    
    def run_analysis(self):
        """Exécute l'analyse pré-match pour tous les matchs à venir"""
        print(f"\n⚽ Analyse Pré-Match - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)
        
        # Récupérer les matchs dans l'heure suivante
        matches = self.get_upcoming_matches(hours_ahead=1)
        
        if not matches:
            print("✅ Aucun match dans l'heure suivante")
            return
        
        print(f"\n📊 {len(matches)} match(s) à analyser:\n")
        
        for match in matches:
            match_time = datetime.strptime(match['date'], '%Y-%m-%d %H:%M:%S')
            time_until = match_time - datetime.utcnow()
            minutes_until = int(time_until.total_seconds() / 60)
            
            print(f"🏟️  {match['home_team']} vs {match['away_team']}")
            print(f"   Coup d'envoi dans {minutes_until} minutes")
            
            # Récupérer les détails depuis l'API
            match_data = self.fetch_match_details(match['external_id'])
            
            if not match_data:
                print("   ⚠️ Données non disponibles\n")
                continue
            
            # Analyser la composition
            analysis = self.analyze_lineup(match_data)
            
            if analysis['home_formation'] or analysis['away_formation']:
                print(f"   📋 Formations: {analysis['home_formation']} vs {analysis['away_formation']}")
            
            # Détecter les changements tactiques
            changes = self.detect_tactical_changes(analysis)
            if changes:
                for change in changes:
                    print(f"   {change}")
            
            # Calculer l'impact
            impact = self.calculate_impact(analysis)
            
            if abs(impact) > 0.1:
                print(f"   📊 Impact sur buts attendus: {impact:+.1f}")
                
                # Mettre à jour la prédiction
                notes = " | ".join(changes) if changes else "Formations analysées"
                self.update_prediction(match['id'], impact, notes)
            else:
                print("   ✅ Pas d'ajustement nécessaire")
            
            print()
    
    def close(self):
        """Ferme la connexion"""
        self.conn.close()

def main():
    """Point d'entrée principal"""
    analyzer = PreMatchAnalyzer()
    try:
        analyzer.run_analysis()
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()

