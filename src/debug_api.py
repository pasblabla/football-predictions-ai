#!/usr/bin/env python3
"""
Script de debug pour comprendre la structure de l'API-Football
"""

import requests
import json

def test_api_structure():
    api_key = "6ee6aab88980fa2736e4a663796ef088"
    base_url = "https://v3.football.api-sports.io"
    headers = {
        'x-rapidapi-host': 'v3.football.api-sports.io',
        'x-rapidapi-key': api_key
    }
    
    print("🔍 Debug API-Football")
    print("=" * 50)
    
    # Test 1: Status
    print("\n1. Test /status")
    try:
        response = requests.get(f"{base_url}/status", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Réponse /status:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Erreur: {response.text}")
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test 2: Leagues sans paramètres
    print("\n2. Test /leagues (sans paramètres)")
    try:
        response = requests.get(f"{base_url}/leagues", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Nombre de ligues: {data.get('results', 0)}")
            if data.get('results', 0) > 0:
                print("Première ligue:")
                print(json.dumps(data['response'][0], indent=2))
        else:
            print(f"Erreur: {response.text}")
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test 3: Leagues avec saison courante
    print("\n3. Test /leagues (saison 2024)")
    try:
        response = requests.get(f"{base_url}/leagues", headers=headers, params={'season': 2024})
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Nombre de ligues pour 2024: {data.get('results', 0)}")
            if data.get('results', 0) > 0:
                print("Première ligue 2024:")
                print(json.dumps(data['response'][0], indent=2))
        else:
            print(f"Erreur: {response.text}")
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test 4: Premier League spécifique
    print("\n4. Test Premier League (ID 39)")
    try:
        response = requests.get(f"{base_url}/leagues", headers=headers, params={'id': 39})
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Résultats Premier League: {data.get('results', 0)}")
            if data.get('results', 0) > 0:
                print("Premier League:")
                print(json.dumps(data['response'][0], indent=2))
        else:
            print(f"Erreur: {response.text}")
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    test_api_structure()

