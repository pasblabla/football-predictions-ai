"""
Système d'analyse complète de match intégrant TOUS les facteurs :
- Forme récente
- H2H (Head-to-Head)
- Joueurs absents
- Conditions du match (domicile/extérieur, enjeu)
- Statistiques détaillées
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from player_absence_detector import PlayerAbsenceDetector
import sqlite3
from datetime import datetime, timedelta

DB_PATH = '/home/ubuntu/football-api-deploy/server/database/app.db'

class CompleteMatchAnalyzer:
    """Analyse complète d'un match avec tous les facteurs"""
    
    def __init__(self):
        self.absence_detector = PlayerAbsenceDetector()
    
    def get_external_id(self, team_id):
        """Récupère l'external_id d'une équipe"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT external_id FROM team WHERE id = ?", (team_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else team_id
    
    def analyze_match(self, match_data):
        """Analyse complète d'un match"""
        analysis = {
            'home_team': match_data['home_team'],
            'away_team': match_data['away_team'],
            'home_team_id': match_data['home_team_id'],
            'away_team_id': match_data['away_team_id'],
            'date': match_data.get('date', 'N/A'),
            
            # Forme récente
            'home_form': self.get_team_form(match_data['home_team_id'], is_home=True),
            'away_form': self.get_team_form(match_data['away_team_id'], is_home=False),
            
            # H2H
            'h2h': self.get_h2h_analysis(match_data['home_team_id'], match_data['away_team_id']),
            
            # Joueurs absents (si disponible)
            'home_absences': self.absence_detector.detect_key_absences(match_data.get('home_external_id')),
            'away_absences': self.absence_detector.detect_key_absences(match_data.get('away_external_id')),
            
            # Conditions du match
            'conditions': self.analyze_match_conditions(match_data),
            
            # Statistiques détaillées
            'home_stats': self.get_detailed_stats(match_data['home_team_id'], is_home=True),
            'away_stats': self.get_detailed_stats(match_data['away_team_id'], is_home=False),
        }
        
        # Calculer l'impact global
        analysis['impact_summary'] = self.calculate_global_impact(analysis)
        
        return analysis
    
    def get_team_form(self, team_id, is_home=True):
        """Récupère la forme récente d'une équipe"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                home_team_id,
                away_team_id,
                home_score,
                away_score,
                date
            FROM match
            WHERE (home_team_id = ? OR away_team_id = ?)
            AND status = 'FINISHED'
            AND date > datetime('now', '-60 days')
            ORDER BY date DESC
            LIMIT 10
        """, (team_id, team_id))
        
        matches = cursor.fetchall()
        conn.close()
        
        if not matches:
            return {
                'form_string': 'N/A',
                'points': 0,
                'goals_avg': 1.5,
                'conceded_avg': 1.5,
                'win_rate': 0.0
            }
        
        form = ''
        points = 0
        goals = []
        conceded = []
        wins = 0
        
        for match in matches:
            home_id, away_id, home_score, away_score, date = match
            
            if home_id == team_id:
                goals.append(home_score or 0)
                conceded.append(away_score or 0)
                if home_score and away_score:
                    if home_score > away_score:
                        form += 'V'
                        points += 3
                        wins += 1
                    elif home_score < away_score:
                        form += 'D'
                    else:
                        form += 'N'
                        points += 1
            else:
                goals.append(away_score or 0)
                conceded.append(home_score or 0)
                if home_score and away_score:
                    if away_score > home_score:
                        form += 'V'
                        points += 3
                        wins += 1
                    elif away_score < home_score:
                        form += 'D'
                    else:
                        form += 'N'
                        points += 1
        
        return {
            'form_string': form or 'N/A',
            'points': points,
            'goals_avg': round(sum(goals) / len(goals), 2) if goals else 1.5,
            'conceded_avg': round(sum(conceded) / len(conceded), 2) if conceded else 1.5,
            'win_rate': round(wins / len(matches), 2) if matches else 0.0
        }
    
    def get_h2h_analysis(self, home_team_id, away_team_id):
        """Analyse H2H entre deux équipes"""
        # Récupérer les external_id pour l'API
        home_external_id = self.get_external_id(home_team_id)
        away_external_id = self.get_external_id(away_team_id)
        
        # Utiliser l'API pour récupérer les H2H
        h2h_matches = self.absence_detector.get_h2h_history(home_external_id, away_external_id, limit=5)
        
        if not h2h_matches:
            return {
                'available': False,
                'message': 'Pas d\'historique H2H disponible'
            }
        
        analysis = self.absence_detector.analyze_h2h(h2h_matches, home_team_id)
        analysis['available'] = True
        
        return analysis
    
    def analyze_match_conditions(self, match_data):
        """Analyse les conditions du match"""
        conditions = {
            'venue': match_data.get('venue', 'Unknown'),
            'is_home_advantage': True,  # Par défaut
            'importance': 'normal'
        }
        
        # Analyser l'importance du match (basé sur la date et la ligue)
        # Pour l'instant, on considère tous les matchs comme normaux
        # On pourrait ajouter une logique pour détecter les derbys, finales, etc.
        
        return conditions
    
    def get_detailed_stats(self, team_id, is_home=True):
        """Statistiques détaillées d'une équipe"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Stats domicile/extérieur séparées
        if is_home:
            cursor.execute("""
                SELECT 
                    COUNT(*) as matches,
                    AVG(home_score) as goals_avg,
                    AVG(away_score) as conceded_avg,
                    SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) as draws,
                    SUM(CASE WHEN home_score < away_score THEN 1 ELSE 0 END) as losses
                FROM match
                WHERE home_team_id = ?
                AND status = 'FINISHED'
                AND date > datetime('now', '-90 days')
            """, (team_id,))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as matches,
                    AVG(away_score) as goals_avg,
                    AVG(home_score) as conceded_avg,
                    SUM(CASE WHEN away_score > home_score THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN away_score = home_score THEN 1 ELSE 0 END) as draws,
                    SUM(CASE WHEN away_score < home_score THEN 1 ELSE 0 END) as losses
                FROM match
                WHERE away_team_id = ?
                AND status = 'FINISHED'
                AND date > datetime('now', '-90 days')
            """, (team_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or result[0] == 0:
            return {
                'matches': 0,
                'goals_avg': 1.5,
                'conceded_avg': 1.5,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'win_rate': 0.0
            }
        
        matches, goals_avg, conceded_avg, wins, draws, losses = result
        
        return {
            'matches': matches,
            'goals_avg': round(goals_avg or 1.5, 2),
            'conceded_avg': round(conceded_avg or 1.5, 2),
            'wins': wins or 0,
            'draws': draws or 0,
            'losses': losses or 0,
            'win_rate': round((wins or 0) / matches, 2) if matches > 0 else 0.0
        }
    
    def calculate_global_impact(self, analysis):
        """Calcule l'impact global de tous les facteurs"""
        impact = {
            'home_advantage': 0.0,
            'form_advantage': 0.0,
            'h2h_advantage': 0.0,
            'absence_impact': 0.0,
            'total_adjustment': 0.0,
            'confidence_modifier': 1.0
        }
        
        # Avantage domicile (environ +0.3 buts)
        impact['home_advantage'] = 0.3
        
        # Avantage de forme
        home_points = analysis['home_form']['points']
        away_points = analysis['away_form']['points']
        
        if home_points > away_points + 5:
            impact['form_advantage'] = 0.2
        elif away_points > home_points + 5:
            impact['form_advantage'] = -0.2
        
        # Avantage H2H
        if analysis['h2h']['available']:
            h2h = analysis['h2h']
            if h2h.get('trend') == 'home_advantage':
                impact['h2h_advantage'] = 0.15
            elif h2h.get('trend') == 'away_advantage':
                impact['h2h_advantage'] = -0.15
        
        # Impact des absences
        home_absences = len(analysis['home_absences']['injured']) + len(analysis['home_absences']['suspended'])
        away_absences = len(analysis['away_absences']['injured']) + len(analysis['away_absences']['suspended'])
        
        if home_absences > away_absences:
            impact['absence_impact'] = -0.1 * (home_absences - away_absences)
        elif away_absences > home_absences:
            impact['absence_impact'] = 0.1 * (away_absences - home_absences)
        
        # Total
        impact['total_adjustment'] = (
            impact['home_advantage'] +
            impact['form_advantage'] +
            impact['h2h_advantage'] +
            impact['absence_impact']
        )
        
        # Modificateur de confiance
        if abs(impact['total_adjustment']) > 0.5:
            impact['confidence_modifier'] = 1.1  # Plus confiant
        elif abs(impact['total_adjustment']) < 0.2:
            impact['confidence_modifier'] = 0.9  # Moins confiant
        
        return impact
    
    def generate_detailed_reasoning(self, analysis):
        """Génère un raisonnement détaillé basé sur l'analyse complète"""
        reasoning_parts = []
        
        # Forme récente
        home_form = analysis['home_form']
        away_form = analysis['away_form']
        
        reasoning_parts.append(
            f"{analysis['home_team']} affiche une forme récente de {home_form['form_string'][:5]} "
            f"({home_form['points']} points sur 10 matchs), "
            f"avec {home_form['goals_avg']} buts marqués et {home_form['conceded_avg']} encaissés en moyenne."
        )
        
        reasoning_parts.append(
            f"{analysis['away_team']} présente une forme de {away_form['form_string'][:5]} "
            f"({away_form['points']} points), "
            f"avec {away_form['goals_avg']} buts marqués et {away_form['conceded_avg']} encaissés."
        )
        
        # H2H
        if analysis['h2h']['available']:
            h2h = analysis['h2h']
            reasoning_parts.append(
                f"Historiquement, sur {h2h['total_matches']} confrontations récentes, "
                f"{analysis['home_team']} a gagné {h2h['home_wins']} fois, "
                f"{analysis['away_team']} {h2h['away_wins']} fois, "
                f"avec {h2h['draws']} nuls."
            )
        
        # Statistiques domicile/extérieur
        home_stats = analysis['home_stats']
        away_stats = analysis['away_stats']
        
        reasoning_parts.append(
            f"À domicile, {analysis['home_team']} affiche un taux de victoire de {home_stats['win_rate']*100:.0f}%. "
            f"À l'extérieur, {analysis['away_team']} gagne {away_stats['win_rate']*100:.0f}% du temps."
        )
        
        # Impact global
        impact = analysis['impact_summary']
        if impact['total_adjustment'] > 0.3:
            reasoning_parts.append(
                f"L'avantage global penche nettement en faveur de {analysis['home_team']}."
            )
        elif impact['total_adjustment'] < -0.3:
            reasoning_parts.append(
                f"Malgré l'avantage du terrain, {analysis['away_team']} semble favori."
            )
        else:
            reasoning_parts.append(
                "Le match s'annonce équilibré avec peu d'écart entre les deux équipes."
            )
        
        return " ".join(reasoning_parts)


def test_analyzer():
    """Tester l'analyseur complet"""
    analyzer = CompleteMatchAnalyzer()
    
    print("🧪 Test de l'analyseur complet de match")
    print("=" * 80)
    
    # Match test: Manchester City vs Liverpool
    match_data = {
        'home_team': 'Manchester City',
        'away_team': 'Liverpool FC',
        'home_team_id': 1,  # ID dans notre DB
        'away_team_id': 2,
        'home_external_id': 65,  # ID API
        'away_external_id': 64,
        'date': '2025-11-20',
        'venue': 'Etihad Stadium'
    }
    
    print(f"\n⚽ Analyse: {match_data['home_team']} vs {match_data['away_team']}")
    print("=" * 80)
    
    analysis = analyzer.analyze_match(match_data)
    
    print(f"\n📊 FORME RÉCENTE:")
    print(f"   {analysis['home_team']}: {analysis['home_form']['form_string'][:5]} ({analysis['home_form']['points']} pts)")
    print(f"   {analysis['away_team']}: {analysis['away_form']['form_string'][:5]} ({analysis['away_form']['points']} pts)")
    
    print(f"\n📈 H2H:")
    if analysis['h2h']['available']:
        print(f"   Matchs: {analysis['h2h']['total_matches']}")
        print(f"   Victoires domicile: {analysis['h2h']['home_wins']}")
        print(f"   Victoires extérieur: {analysis['h2h']['away_wins']}")
        print(f"   Tendance: {analysis['h2h']['trend']}")
    else:
        print(f"   {analysis['h2h']['message']}")
    
    print(f"\n🏠 STATISTIQUES DOMICILE/EXTÉRIEUR:")
    print(f"   {analysis['home_team']} (domicile): {analysis['home_stats']['win_rate']*100:.0f}% victoires")
    print(f"   {analysis['away_team']} (extérieur): {analysis['away_stats']['win_rate']*100:.0f}% victoires")
    
    print(f"\n⚖️ IMPACT GLOBAL:")
    impact = analysis['impact_summary']
    print(f"   Avantage domicile: {impact['home_advantage']:+.2f}")
    print(f"   Avantage forme: {impact['form_advantage']:+.2f}")
    print(f"   Avantage H2H: {impact['h2h_advantage']:+.2f}")
    print(f"   Impact absences: {impact['absence_impact']:+.2f}")
    print(f"   TOTAL: {impact['total_adjustment']:+.2f}")
    print(f"   Modificateur confiance: {impact['confidence_modifier']:.2f}x")
    
    print(f"\n💡 RAISONNEMENT DÉTAILLÉ:")
    reasoning = analyzer.generate_detailed_reasoning(analysis)
    print(f"   {reasoning}")


if __name__ == "__main__":
    test_analyzer()

