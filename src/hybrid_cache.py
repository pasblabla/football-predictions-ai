Système de cache pour les prédictions hybrides
Génère et met en cache les prédictions pour répondre rapidement
"""
import sqlite3
import json
from datetime import datetime, timedelta
from hybrid_predictor import HybridPredictor

class HybridCache:
    """Gère le cache des prédictions hybrides"""
    
    def __init__(self, db_path='/home/ubuntu/football-api-deploy/server/database/app.db'):
        self.db_path = db_path
        self.predictor = HybridPredictor()
        self._create_cache_table()
    
    def _create_cache_table(self):
        """Crée la table de cache si elle n'existe pas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hybrid_predictions_cache (
                match_id INTEGER PRIMARY KEY,
                prediction_data TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (match_id) REFERENCES match(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_expires 
            ON hybrid_predictions_cache(expires_at)
        """)
        
        conn.commit()
        conn.close()
    
    def get_cached_prediction(self, match_id):
        """Récupère une prédiction depuis le cache si elle est valide"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT prediction_data, expires_at
            FROM hybrid_predictions_cache
            WHERE match_id = ?