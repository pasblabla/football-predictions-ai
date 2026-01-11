
import os
from src.data_sources.football_data_org import FootballDataOrgClient

def test_api_connection():
    client = FootballDataOrgClient()
    try:
        competitions = client.get_competitions()
        print("Connexion API réussie. Premières compétitions:")
        for comp in competitions["competitions"][:5]:
            print(f"- {comp['name']} ({comp['area']['name']})")
        return True
    except Exception as e:
        print(f"Erreur de connexion API: {e}")
        return False

if __name__ == "__main__":
    # Assurez-vous que la variable d'environnement est définie
    if "FOOTBALL_DATA_API_KEY" not in os.environ:
        print("La variable d'environnement FOOTBALL_DATA_API_KEY n'est pas définie.")
        print("Veuillez l'ajouter à votre ~/.bashrc ou la définir manuellement.")
    else:
        print("Test de la connexion à football-data.org...")
        test_api_connection()


