"""
Script de pré-génération des prédictions hybrides
Génère et met en cache toutes les prédictions pour les matchs à venir
"""
import sys
import os
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.hybrid_predictor import HybridPredictor
from scripts.hybrid_cache import HybridCache

DB_PATH = '/home/ubuntu/football-api-deploy/server/database/app.db'

def get_upcoming_matches(limit=None):
    """Récupère les matchs à venir"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    today = datetime.now()
    next_week = today + timedelta(days=30)  # Chercher dans les 30 prochains jours
    
    query = """
        SELECT 
            m.id,
            m.date,
            m.status,
            m.venue,
            ht.name as home_team,
            at.name as away_team,
            l.name as league,
            l.code as league_code,
            ht.id as home_team_id,
            at.id as away_team_id,
            ht.external_id as home_external_id,
            at.external_id as away_external_id
        FROM match m
        JOIN team ht ON m.home_team_id = ht.id
        JOIN team at ON m.away_team_id = at.id
        JOIN league l ON m.league_id = l.id
        WHERE m.status IN ('SCHEDULED', 'TIMED')
        AND m.date >= ?
        AND m.date <= ?
        ORDER BY m.date
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query, (today.strftime('%Y-%m-%d %H:%M:%S'), next_week.strftime('%Y-%m-%d %H:%M:%S')))
    matches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return matches

def calculate_team_stats(team_id, is_home=True):
    """Calcule les statistiques d'une équipe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Derniers 10 matchs
    cursor.execute("""
        SELECT 
            home_team_id,
            away_team_id,
            home_score,
            away_score
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
            'goals_avg': 1.5,
            'conceded_avg': 1.5,
            'form': 'N/A'
        }
    
    goals = []
    conceded = []
    form = ''
    
    for match in matches[:5]:  # Forme sur 5 matchs
        home_id, away_id, home_score, away_score = match
        
        if home_id == team_id:
            goals.append(home_score or 0)
            conceded.append(away_score or 0)
            if home_score and away_score:
                if home_score > away_score:
                    form += 'V'
                elif home_score < away_score:
                    form += 'D'
                else:
                    form += 'N'
        else:
            goals.append(away_score or 0)
            conceded.append(home_score or 0)
            if home_score and away_score:
                if away_score > home_score:
                    form += 'V'
                elif away_score < home_score:
                    form += 'D'
                else:
                    form += 'N'
    
    return {
        'goals_avg': round(sum(goals) / len(goals), 1) if goals else 1.5,
        'conceded_avg': round(sum(conceded) / len(conceded), 1) if conceded else 1.5,
        'form': form or 'N/A'
    }

def prepare_match_data(match):
    """Prépare les données pour le prédicteur"""
    home_stats = calculate_team_stats(match['home_team_id'], is_home=True)
    away_stats = calculate_team_stats(match['away_team_id'], is_home=False)
    
    return {
        'home_team': match['home_team'],
        'away_team': match['away_team'],
        'home_team_id': match['home_team_id'],
        'away_team_id': match['away_team_id'],
        'home_external_id': match.get('home_external_id'),
        'away_external_id': match.get('away_external_id'),
        'league_code': match.get('league_code', 'PL'),
        'home_form': home_stats['form'],
        'away_form': away_stats['form'],
        'home_goals_avg': home_stats['goals_avg'],
        'away_goals_avg': away_stats['goals_avg'],
        'home_conceded_avg': home_stats['conceded_avg'],
        'away_conceded_avg': away_stats['conceded_avg'],
        'h2h_history': 'Historique H2H non disponible'
    }

def pregenerate_predictions(limit=None):
    """Pré-génère les prédictions hybrides pour tous les matchs à venir"""
    print("🚀 Démarrage de la pré-génération des prédictions hybrides...")
    
    # Initialiser
    predictor = HybridPredictor()
    cache = HybridCache()
    
    # Récupérer les matchs
    matches = get_upcoming_matches(limit=limit)
    print(f"📊 {len(matches)} matchs à traiter")
    
    success_count = 0
    error_count = 0
    cached_count = 0
    
    for i, match in enumerate(matches, 1):
        try:
            # Vérifier si déjà en cache
            cached = cache.get_cached_prediction(match['id'])
            if cached:
                print(f"✅ [{i}/{len(matches)}] Match {match['id']} déjà en cache")
                cached_count += 1
                continue
            
            print(f"🔄 [{i}/{len(matches)}] Génération pour {match['home_team']} vs {match['away_team']}...")
            
            # Préparer les données
            match_data = prepare_match_data(match)
            
            # Générer la prédiction
            prediction = predictor.predict(match_data)
            
            # Mettre en cache pour 6 heures
            cache.cache_prediction(match['id'], prediction, cache_hours=6)
            
            print(f"   ✅ Score prédit: {prediction['predicted_score']} | Confiance: {prediction['confidence']}")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            error_count += 1
    
    print("\n" + "="*80)
    print("📊 RÉSUMÉ")
    print("="*80)
    print(f"✅ Succès: {success_count}")
    print(f"💾 Déjà en cache: {cached_count}")
    print(f"❌ Erreurs: {error_count}")
    print(f"📈 Total: {len(matches)}")
    print("="*80)
    
    # Nettoyer le cache expiré
    deleted = cache.clean_expired_cache()
    if deleted > 0:
        print(f"🧹 {deleted} entrées expirées supprimées du cache")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Pré-générer les prédictions hybrides')
    parser.add_argument('--limit', type=int, help='Limiter le nombre de matchs à traiter')
    args = parser.parse_args()
    
    pregenerate_predictions(limit=args.limit)

