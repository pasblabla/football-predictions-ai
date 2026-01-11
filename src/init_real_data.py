#!/usr/bin/env python3.11
"""
Script pour initialiser la base de données avec des données réelles depuis football-data.org
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['FOOTBALL_DATA_API_KEY'] = '647c75a7ce7f482598c8240664bd856c'

from src.main import app
import requests

def init_data():
    """Initialiser les données via les endpoints de synchronisation"""
    base_url = "http://localhost:5001"
    
    print("🚀 Démarrage de l'initialisation des données...")
    
    # 1. Synchroniser les compétitions
    print("\n📋 Synchronisation des compétitions...")
    try:
        response = requests.post(f"{base_url}/api/sync/sync-competitions")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Erreur: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation des compétitions: {e}")
        return False
    
    # 2. Synchroniser tous les matchs
    print("\n⚽ Synchronisation de tous les matchs...")
    try:
        response = requests.post(f"{base_url}/api/sync/sync-all-matches")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            for league_result in result['results']:
                if 'error' in league_result:
                    print(f"  ⚠️  {league_result['league']}: {league_result['error']}")
                else:
                    print(f"  ✓ {league_result['league']}: {league_result['synced']} matchs")
        else:
            print(f"❌ Erreur: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation des matchs: {e}")
        return False
    
    # 3. Vérifier le statut
    print("\n📊 Vérification du statut...")
    try:
        response = requests.get(f"{base_url}/api/sync/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Statut de la synchronisation:")
            print(f"  - Ligues: {status['leagues']['synced']}/{status['leagues']['total']}")
            print(f"  - Matchs: {status['matches']['total']} (dont {status['matches']['upcoming']} à venir)")
            print(f"  - Équipes: {status['teams']}")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du statut: {e}")
    
    print("\n✅ Initialisation terminée!")
    return True

if __name__ == "__main__":
    # Démarrer l'application Flask en arrière-plan
    print("⏳ Démarrage du serveur Flask...")
    
    import threading
    import time
    
    def run_app():
        with app.app_context():
            app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_app, daemon=True)
    server_thread.start()
    
    # Attendre que le serveur démarre
    time.sleep(3)
    print("✅ Serveur démarré\n")
    
    # Initialiser les données
    init_data()

