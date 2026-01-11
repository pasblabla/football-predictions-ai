#!/usr/bin/env python3.11
"""
Script pour entraîner l'IA sur les matchs passés de la saison en cours
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.main import app, db
from src.models.football import League, Team, Match, Prediction
import requests
import time
from datetime import datetime, timedelta

API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', '647c75a7ce7f482598c8240664bd856c')
BASE_URL = 'https://api.football-data.org/v4'
headers = {'X-Auth-Token': API_KEY}

# Compétitions à analyser
COMPETITIONS = {
    'PL': 2021,    # Premier League
    'FL1': 2015,   # Ligue 1
    'BL1': 2002,   # Bundesliga
    'SA': 2019,    # Serie A
    'PD': 2014,    # La Liga
    'PPL': 2017,   # Primeira Liga
    'DED': 2003,   # Eredivisie
    'CL': 2001,    # Champions League
    'ELC': 2016,   # Championship
}

def fetch_finished_matches():
    """Récupérer tous les matchs terminés depuis le début de la saison"""
    
    # Date de début de saison (1er août)
    season_start = datetime(2024, 8, 1)
    today = datetime.now()
    
    all_finished_matches = []
    
    with app.app_context():
        for code, comp_id in COMPETITIONS.items():
            try:
                print(f"\n📥 Récupération des matchs terminés pour {code}...")
                
                # Récupérer la ligue
                league = League.query.filter_by(code=code).first()
                if not league:
                    print(f"⚠️  Ligue {code} non trouvée")
                    continue
                
                # Appel API pour les matchs terminés
                date_from = season_start.strftime('%Y-%m-%d')
                date_to = today.strftime('%Y-%m-%d')
                
                matches_url = f"{BASE_URL}/competitions/{comp_id}/matches?dateFrom={date_from}&dateTo={date_to}&status=FINISHED"
                
                response = requests.get(matches_url, headers=headers)
                
                if response.status_code == 429:
                    print(f"⚠️  Limite de taux, pause de 70s...")
                    time.sleep(70)
                    response = requests.get(matches_url, headers=headers)
                
                if response.status_code != 200:
                    print(f"❌ Erreur {response.status_code}")
                    time.sleep(7)
                    continue
                
                data = response.json()
                matches = data.get('matches', [])
                
                print(f"✅ {len(matches)} matchs terminés trouvés")
                
                # Traiter chaque match
                for match_data in matches:
                    home_team_data = match_data.get('homeTeam', {})
                    away_team_data = match_data.get('awayTeam', {})
                    score = match_data.get('score', {}).get('fullTime', {})
                    
                    home_score = score.get('home')
                    away_score = score.get('away')
                    
                    if home_score is None or away_score is None:
                        continue
                    
                    match_info = {
                        'league_code': code,
                        'league_name': league.name,
                        'home_team': home_team_data.get('name'),
                        'away_team': away_team_data.get('name'),
                        'home_team_id': home_team_data.get('id'),
                        'away_team_id': away_team_data.get('id'),
                        'home_score': home_score,
                        'away_score': away_score,
                        'date': match_data.get('utcDate'),
                        'external_id': match_data.get('id')
                    }
                    
                    all_finished_matches.append(match_info)
                    
                    # Enregistrer dans la base de données
                    existing_match = Match.query.filter_by(external_id=match_info['external_id']).first()
                    
                    if existing_match:
                        # Mettre à jour le score
                        existing_match.home_score = home_score
                        existing_match.away_score = away_score
                        existing_match.status = 'FINISHED'
                    else:
                        # Créer le match
                        home_team = Team.query.filter_by(external_id=match_info['home_team_id']).first()
                        away_team = Team.query.filter_by(external_id=match_info['away_team_id']).first()
                        
                        if not home_team or not away_team:
                            continue
                        
                        match_date = datetime.fromisoformat(match_info['date'].replace('Z', '+00:00'))
                        
                        new_match = Match(
                            date=match_date,
                            status='FINISHED',
                            league_id=league.id,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            home_score=home_score,
                            away_score=away_score,
                            external_id=match_info['external_id']
                        )
                        db.session.add(new_match)
                
                db.session.commit()
                print(f"✅ {code}: Données sauvegardées")
                
                time.sleep(7)  # Respecter la limite de taux
                
            except Exception as e:
                print(f"❌ Erreur pour {code}: {str(e)}")
                db.session.rollback()
                continue
    
    return all_finished_matches

def analyze_results(finished_matches):
    """Analyser les résultats pour identifier les tendances"""
    
    print(f"\n📊 Analyse de {len(finished_matches)} matchs terminés...")
    
    # Statistiques par ligue
    league_stats = {}
    
    for match in finished_matches:
        league = match['league_code']
        
        if league not in league_stats:
            league_stats[league] = {
                'total': 0,
                'home_wins': 0,
                'draws': 0,
                'away_wins': 0,
                'avg_goals': 0,
                'total_goals': 0
            }
        
        stats = league_stats[league]
        stats['total'] += 1
        
        home_score = match['home_score']
        away_score = match['away_score']
        
        stats['total_goals'] += home_score + away_score
        
        if home_score > away_score:
            stats['home_wins'] += 1
        elif home_score < away_score:
            stats['away_wins'] += 1
        else:
            stats['draws'] += 1
    
    # Calculer les moyennes
    for league, stats in league_stats.items():
        if stats['total'] > 0:
            stats['avg_goals'] = stats['total_goals'] / stats['total']
            stats['home_win_pct'] = (stats['home_wins'] / stats['total']) * 100
            stats['draw_pct'] = (stats['draws'] / stats['total']) * 100
            stats['away_win_pct'] = (stats['away_wins'] / stats['total']) * 100
    
    # Afficher les statistiques
    print(f"\n{'Ligue':<10} | {'Matchs':<7} | {'Dom%':<6} | {'Nul%':<6} | {'Ext%':<6} | {'Moy Buts'}")
    print("-" * 70)
    
    for league, stats in sorted(league_stats.items()):
        print(f"{league:<10} | {stats['total']:<7} | {stats['home_win_pct']:<6.1f} | {stats['draw_pct']:<6.1f} | {stats['away_win_pct']:<6.1f} | {stats['avg_goals']:.2f}")
    
    return league_stats

def save_learning_data(league_stats):
    """Sauvegarder les données d'apprentissage pour améliorer les prédictions futures"""
    
    import json
    
    learning_file = '/home/ubuntu/football-api/learning_data.json'
    
    learning_data = {
        'last_update': datetime.now().isoformat(),
        'league_statistics': league_stats,
        'global_stats': {
            'total_matches': sum(s['total'] for s in league_stats.values()),
            'avg_home_advantage': sum(s['home_win_pct'] for s in league_stats.values()) / len(league_stats),
            'avg_draw_rate': sum(s['draw_pct'] for s in league_stats.values()) / len(league_stats),
        }
    }
    
    with open(learning_file, 'w') as f:
        json.dump(learning_data, f, indent=2)
    
    print(f"\n💾 Données d'apprentissage sauvegardées: {learning_file}")
    print(f"📊 {learning_data['global_stats']['total_matches']} matchs analysés")
    print(f"🏠 Avantage domicile moyen: {learning_data['global_stats']['avg_home_advantage']:.1f}%")
    print(f"🤝 Taux de match nul moyen: {learning_data['global_stats']['avg_draw_rate']:.1f}%")

if __name__ == '__main__':
    print("🎓 Démarrage de l'apprentissage de l'IA sur les matchs passés...")
    print("=" * 70)
    
    # Récupérer les matchs terminés
    finished_matches = fetch_finished_matches()
    
    if not finished_matches:
        print("\n⚠️  Aucun match terminé trouvé")
        sys.exit(1)
    
    # Analyser les résultats
    league_stats = analyze_results(finished_matches)
    
    # Sauvegarder les données d'apprentissage
    save_learning_data(league_stats)
    
    print("\n✅ Apprentissage terminé avec succès!")
    print("🚀 L'IA peut maintenant utiliser ces données pour améliorer ses prédictions")

