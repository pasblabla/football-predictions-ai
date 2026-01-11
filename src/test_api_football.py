#!/usr/bin/env python3
"""
Script de test pour l'API-Football
Teste la connexion et récupère quelques données de base
"""

import sys
import os
sys.path.append('/home/ubuntu/football-api/src')

from api_football_client import APIFootballClient

def main():
    print("🚀 Test de l'API-Football")
    print("=" * 50)
    
    # Initialiser le client
    client = APIFootballClient()
    
    # Test de connexion
    print("\n1. Test de connexion...")
    if not client.test_api_connection():
        print("❌ Impossible de se connecter à l'API")
        return
    
    # Test récupération des ligues
    print("\n2. Récupération des ligues principales...")
    leagues = client.get_leagues()
    print(f"✅ {len(leagues)} ligues récupérées")
    
    for league in leagues[:3]:  # Afficher les 3 premières
        print(f"   - {league['name']} ({league['country']})")
    
    # Test récupération des matchs pour une ligue
    if leagues:
        print(f"\n3. Test récupération des matchs pour {leagues[0]['name']}...")
        from datetime import datetime, timedelta
        
        today = datetime.now().strftime('%Y-%m-%d')
        next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        fixtures = client.get_fixtures(
            league_id=leagues[0]['id'],
            date_from=today,
            date_to=next_week
        )
        
        print(f"✅ {len(fixtures)} matchs récupérés pour la semaine prochaine")
        
        for fixture in fixtures[:3]:  # Afficher les 3 premiers
            print(f"   - {fixture['home_team']['name']} vs {fixture['away_team']['name']} ({fixture['date']})")
    
    # Test récupération des équipes
    if leagues:
        print(f"\n4. Test récupération des équipes pour {leagues[0]['name']}...")
        teams = client.get_teams_by_league(leagues[0]['id'])
        print(f"✅ {len(teams)} équipes récupérées")
        
        for team in teams[:5]:  # Afficher les 5 premières
            print(f"   - {team['name']} ({team['country']})")
    
    print("\n" + "=" * 50)
    print("✅ Test terminé avec succès!")

if __name__ == "__main__":
    main()

