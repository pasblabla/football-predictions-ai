"""
Script pour pré-charger les buteurs de toutes les compétitions dans un fichier JSON.
Cela évite de faire des appels API à chaque requête.
"""

import requests
import json
import os

API_KEY = "647c75a7ce7f482598c8240664bd856c"
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {'X-Auth-Token': API_KEY}

# Compétitions à récupérer
COMPETITIONS = {
    'PL': 'Premier League',
    'BL1': 'Bundesliga',
    'SA': 'Serie A',
    'PD': 'LaLiga',
    'FL1': 'Ligue 1',
    'ELC': 'Championship',
    'PPL': 'Primeira Liga',
    'DED': 'Eredivisie'
}

def get_top_scorers(competition_code, limit=30):
    """Récupère les meilleurs buteurs d'une compétition."""
    try:
        url = f"{BASE_URL}/competitions/{competition_code}/scorers?limit={limit}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    'player_name': s['player']['name'],
                    'team_id': s['team']['id'],
                    'team_name': s['team']['name'],
                    'goals': s.get('goals', 0),
                    'assists': s.get('assists', 0)
                }
                for s in data.get('scorers', [])
            ]
        else:
            print(f"Erreur {response.status_code} pour {competition_code}")
    except Exception as e:
        print(f"Erreur récupération buteurs {competition_code}: {e}")
    
    return []

def main():
    """Pré-charge tous les buteurs et les sauvegarde dans un fichier JSON."""
    all_scorers = {}
    
    for code, name in COMPETITIONS.items():
        print(f"Récupération des buteurs de {name} ({code})...")
        scorers = get_top_scorers(code)
        all_scorers[code] = scorers
        print(f"  -> {len(scorers)} buteurs trouvés")
    
    # Sauvegarder dans un fichier JSON
    output_path = os.path.join(os.path.dirname(__file__), 'instance', 'scorers_cache.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_scorers, f, ensure_ascii=False, indent=2)
    
    print(f"\nButeurs sauvegardés dans {output_path}")
    
    # Afficher un résumé
    total = sum(len(s) for s in all_scorers.values())
    print(f"Total: {total} buteurs dans {len(all_scorers)} compétitions")

if __name__ == "__main__":
    main()
