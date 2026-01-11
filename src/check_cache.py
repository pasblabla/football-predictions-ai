import sqlite3
import json

conn = sqlite3.connect('/home/ubuntu/football-api-deploy/server/database/app.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM hybrid_predictions_cache')
total = cursor.fetchone()[0]
print(f'Total cache: {total}')

if total > 0:
    cursor.execute('SELECT match_id, prediction_data FROM hybrid_predictions_cache LIMIT 1')
    row = cursor.fetchone()
    if row:
        data = json.loads(row[1])
        print(f'\nMatch {row[0]}:')
        print(f'Score: {data.get("predicted_score")}')
        print(f'Expected goals: {data.get("expected_goals")}')
        print(f'Buteurs: {data.get("probable_scorers")}')
        print(f'\nToutes les clés:', list(data.keys()))

conn.close()
