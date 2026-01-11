"""
Script d'initialisation de la base de données
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.football import Base, League

# Configuration de la base de données
DATABASE_URL = 'sqlite:///database/football.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_database():
    """Initialise la base de données avec les tables"""
    print("🔧 Création des tables...")
    Base.metadata.create_all(engine)
    print("✅ Tables créées avec succès!")
    
    # Ajouter les championnats
    session = Session()
    
    leagues_data = [
        {'name': 'Premier League', 'code': 'PL', 'country': 'England'},
        {'name': 'Ligue 1', 'code': 'FL1', 'country': 'France'},
        {'name': 'Bundesliga', 'code': 'BL1', 'country': 'Germany'},
        {'name': 'Serie A', 'code': 'SA', 'country': 'Italy'},
        {'name': 'Primera Division', 'code': 'PD', 'country': 'Spain'},
        {'name': 'Primeira Liga', 'code': 'PPL', 'country': 'Portugal'},
        {'name': 'Eredivisie', 'code': 'DED', 'country': 'Netherlands'},
        {'name': 'UEFA Champions League', 'code': 'CL', 'country': 'Europe'},
    ]
    
    print("📊 Ajout des championnats...")
    for league_data in leagues_data:
        existing = session.query(League).filter_by(code=league_data['code']).first()
        if not existing:
            league = League(**league_data)
            session.add(league)
            print(f"  ✓ {league_data['name']}")
    
    session.commit()
    session.close()
    print("✅ Base de données initialisée!")

if __name__ == '__main__':
    init_database()

