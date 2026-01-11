Script pour récupérer les matchs à venir depuis l'API football-data.org
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
from models.football import Match, Team, League, db

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = '647c75a7ce7f482598c8240664bd856c'
API_BASE_URL = 'https://api.football-data.org/v4'
DATABASE_PATH = '/home/ubuntu/football-api-deploy/server/database/app.db'

# Ligues à récupérer
LEAGUES = {
    'PL': 2021,    # Premier League
    'FL1': 2015,   # Ligue 1
    'BL1': 2002,   # Bundesliga
    'SA': 2019,    # Serie A
    'PD': 2014,    # La Liga
    'PPL': 2017,   # Primeira Liga
    'DED': 2003,   # Eredivisie
    'CL': 2001     # Champions League
}

def get_or_create_team(session, team_data):
    """Récupère ou crée une équipe"""
    team = session.query(Team).filter_by(external_id=team_data['id']).first()
    if not team:
        team = Team(
            name=team_data['name'],
            short_name=team_data.get('shortName', team_data['name'][:20]),
            tla=team_data.get('tla', team_data['name'][:3].upper()),
            external_id=team_data['id']
        )