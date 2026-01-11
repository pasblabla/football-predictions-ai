#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_sources.football_data_uk import football_data_uk

def test_football_data():
    print("Test de téléchargement des données football-data.co.uk...")
    
    # Test de téléchargement Premier League
    print("\n1. Test Premier League...")
    df = football_data_uk.download_league_data('Premier League')
    if df is not None:
        print(f"✓ Données téléchargées: {len(df)} lignes")
        print(f"✓ Colonnes disponibles: {list(df.columns)[:10]}...")  # Afficher les 10 premières colonnes
        
        # Test de traitement des données
        matches = football_data_uk.process_match_data(df.head(5), 'Premier League')
        print(f"✓ Matchs traités: {len(matches)}")
        if matches:
            print(f"✓ Exemple de match: {matches[0]['home_team']} vs {matches[0]['away_team']}")
    else:
        print("✗ Échec du téléchargement")
    
    # Test de récupération des matchs récents
    print("\n2. Test matchs récents...")
    try:
        recent_matches = football_data_uk.get_recent_matches('Premier League', days_back=30)
        print(f"✓ Matchs récents trouvés: {len(recent_matches)}")
    except Exception as e:
        print(f"✗ Erreur: {e}")
    
    print("\nTest terminé.")

if __name__ == "__main__":
    test_football_data()

