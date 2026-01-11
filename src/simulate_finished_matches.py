#!/usr/bin/env python3.11
"""
Script pour simuler des matchs terminés (pour tester l'historique)
En production, ce script sera remplacé par une vraie récupération de résultats
"""

import sqlite3
import random
from datetime import datetime, timedelta

DATABASE_PATH = 'src/database/app.db'

def simulate_match_result(home_win_prob, draw_prob, away_win_prob):
    """Simule un résultat de match basé sur les probabilités"""
    rand = random.random() * 100
    
    if rand < home_win_prob:
        # Victoire domicile
        home_score = random.randint(2, 4)
        away_score = random.randint(0, home_score - 1)
    elif rand < home_win_prob + draw_prob:
        # Match nul
        score = random.randint(0, 3)
        home_score = away_score = score
    else:
        # Victoire extérieur
        away_score = random.randint(2, 4)
        home_score = random.randint(0, away_score - 1)
    
    return home_score, away_score

def main():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Prendre les 20 matchs les plus anciens qui sont TIMED ou SCHEDULED
    cursor.execute("""
        SELECT m.id, m.date, p.prob_home_win, p.prob_draw, p.prob_away_win
        FROM match m
        LEFT JOIN prediction p ON m.id = p.match_id
        WHERE m.status IN ('TIMED', 'SCHEDULED')
        ORDER BY m.date ASC
        LIMIT 20
    """)
    
    matches = cursor.fetchall()
    updated_count = 0
    
    print(f"Simulation de {len(matches)} matchs terminés...")
    print()
    
    for match_id, date, home_prob, draw_prob, away_prob in matches:
        # Utiliser les probabilités ou des valeurs par défaut
        home_prob = home_prob or 50
        draw_prob = draw_prob or 25
        away_prob = away_prob or 25
        
        # Simuler le résultat
        home_score, away_score = simulate_match_result(home_prob, draw_prob, away_prob)
        
        # Mettre à jour le match
        cursor.execute("""
            UPDATE match 
            SET status = 'FINISHED', 
                home_score = ?, 
                away_score = ?
            WHERE id = ?
        """, (home_score, away_score, match_id))
        
        updated_count += 1
        print(f"✅ Match {match_id}: {home_score}-{away_score} (Date: {date})")
    
    conn.commit()
    conn.close()
    
    print()
    print(f"✅ {updated_count} matchs simulés avec succès!")
    print()
    print("Ces matchs apparaîtront maintenant dans l'historique.")

if __name__ == '__main__':
    main()

