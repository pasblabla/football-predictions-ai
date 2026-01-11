"""
Script d'automatisation pour :
1. Récupérer les matchs terminés depuis l'API
2. Mettre à jour les scores dans la base de données
3. Transférer automatiquement vers l'historique
4. Lancer l'apprentissage de l'IA
"""
import sys
import os
import requests
from datetime import datetime, timedelta
import logging

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.football import Match, Prediction, Team, League

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv('FOOTBALL_API_KEY', '647c75a7ce7f482598c8240664bd856c')
API_BASE_URL = 'https://api.football-data.org/v4'
DATABASE_URL = 'sqlite:///database/app.db'

# Créer la session de base de données
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class MatchAutomation:
    """Classe pour automatiser la mise à jour des matchs"""
    
    def __init__(self):
        self.session = Session()
        self.headers = {'X-Auth-Token': API_KEY}
        self.updated_count = 0
        self.new_finished_count = 0
    
    def get_finished_matches_from_api(self, days_back=7):
        """Récupère les matchs terminés des N derniers jours depuis l'API"""
        logger.info(f"🔍 Récupération des matchs terminés des {days_back} derniers jours...")
        
        date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')
        
        competitions = ['PL', 'FL1', 'BL1', 'SA', 'PD', 'PPL', 'DED', 'CL']
        all_finished_matches = []
        
        for comp_code in competitions:
            try:
                url = f"{API_BASE_URL}/competitions/{comp_code}/matches"
                params = {
                    'dateFrom': date_from,
                    'dateTo': date_to
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get('matches', [])
                    all_finished_matches.extend(matches)
                    logger.info(f"  ✓ {comp_code}: {len(matches)} matchs terminés")
                elif response.status_code == 429:
                    logger.warning(f"  ⚠️ {comp_code}: Limite API atteinte, pause...")
                    continue
                else:
                    logger.warning(f"  ⚠️ {comp_code}: Erreur {response.status_code}")