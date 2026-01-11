import requests
import json

response = requests.get('http://localhost:5001/api/football/top10-hybrid')
data = response.json()

print(f'✅ {data["count"]} prédictions disponibles\n')

pred = data['predictions'][0]
print(f'Exemple: {pred["match"]["home_team"]} vs {pred["match"]["away_team"]}')
print(f'Score: {pred["prediction"]["predicted_score"]} ({pred["prediction"]["expected_goals"]} buts)')

scorers = pred['prediction'].get('probable_scorers', {})
print(f'Buteurs domicile: {len(scorers.get("home", []))}')
print(f'Buteurs extérieur: {len(scorers.get("away", []))}')

if scorers.get('away'):
    print(f'\nExemple buteur extérieur: {scorers["away"][0]["name"]} ({scorers["away"][0]["goals_season"]} buts)')
if scorers.get('home'):
    print(f'Exemple buteur domicile: {scorers["home"][0]["name"]} ({scorers["home"][0]["goals_season"]} buts)')
