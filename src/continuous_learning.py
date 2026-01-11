"""
Système d'Apprentissage Automatique Continu
Analyse les matchs terminés et ajuste automatiquement les coefficients de prédiction
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Ajouter le chemin parent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

# Configuration
DB_PATH = "/home/ubuntu/football-api-deploy/server/database/football.db"
COEFFICIENTS_FILE = "/home/ubuntu/football-api-deploy/server/data/learning_coefficients.json"

class ContinuousLearning:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.coefficients = self.load_coefficients()
        
    def load_coefficients(self) -> Dict:
        """Charge les coefficients d'apprentissage"""
        default_coefficients = {
            "home_advantage": 0.3,
            "form_weight": 0.6,
            "h2h_weight": 0.4,
            "goals_base": 2.75,
            "draw_probability_boost": 0.0,
            "btts_threshold": 0.5,
            "defensive_factor": 1.0,
            "offensive_factor": 1.0,
            "learning_rate": 0.05,  # Taux d'apprentissage
            "precision_history": [],
            "last_update": None
        }
        
        try:
            os.makedirs(os.path.dirname(COEFFICIENTS_FILE), exist_ok=True)
            with open(COEFFICIENTS_FILE, 'r') as f:
                loaded = json.load(f)
                default_coefficients.update(loaded)
        except FileNotFoundError:
            print("📝 Création des coefficients initiaux")
            self.save_coefficients(default_coefficients)
        
        return default_coefficients
    
    def save_coefficients(self, coefficients: Dict):
        """Sauvegarde les coefficients"""
        os.makedirs(os.path.dirname(COEFFICIENTS_FILE), exist_ok=True)
        with open(COEFFICIENTS_FILE, 'w') as f:
            json.dump(coefficients, f, indent=2)
    
    def analyze_finished_matches(self, days_back: int = 1) -> List[Dict]:
        """Analyse les matchs terminés récents"""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        query = """
        SELECT 
            m.id, ht.name as home_team, at.name as away_team,
            m.home_score, m.away_score,
            p.prob_home_win, p.prob_draw, p.prob_away_win,
            p.prob_both_teams_score, p.predicted_score_home, p.predicted_score_away,
            m.date, p.prob_over_2_5
        FROM matches m
        JOIN predictions p ON p.match_id = m.id
        JOIN teams ht ON ht.id = m.home_team_id
        JOIN teams at ON at.id = m.away_team_id
        WHERE m.status = 'FINISHED'
        AND m.date >= ?
        AND m.home_score IS NOT NULL
        ORDER BY m.date DESC
        """