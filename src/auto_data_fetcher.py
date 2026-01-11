#!/usr/bin/env python3
"""
Auto Data Fetcher - Module d'automatisation pour récupérer les données
Combine l'API football-data.org et le scraping SoccerStats.com
"""

import os
import sys
import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime, timedelta
import logging
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration API football-data.org
FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY', '')
FOOTBALL_API_URL = 'https://api.football-data.org/v4'

# Configuration SoccerStats
SOCCERSTATS_URL = 'https://www.soccerstats.com'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Mapping des ligues
LEAGUES = {
    'england': {'name': 'Premier League', 'api_code': 'PL', 'api_id': 39},
    'england2': {'name': 'Championship', 'api_code': 'ELC', 'api_id': 46},
    'france': {'name': 'Ligue 1', 'api_code': 'FL1', 'api_id': 61},
    'germany': {'name': 'Bundesliga', 'api_code': 'BL1', 'api_id': 78},
    'italy': {'name': 'Serie A', 'api_code': 'SA', 'api_id': 135},
    'spain': {'name': 'LaLiga', 'api_code': 'PD', 'api_id': 140},
    'netherlands': {'name': 'Eredivisie', 'api_code': 'DED', 'api_id': 88},
    'portugal': {'name': 'Primeira Liga', 'api_code': 'PPL', 'api_id': 94},
}


class AutoDataFetcher:
    """Récupérateur automatique de données football"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or self._find_database()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.api_available = bool(FOOTBALL_API_KEY)
        
    def _find_database(self):
        """Trouve le chemin de la base de données"""
        paths = [
            '/home/ubuntu/football_app/instance/football.db',
            '/home/ubuntu/football_app/site.db',
            '/home/ubuntu/football_app/database/app.db',
        ]
        for path in paths:
            if os.path.exists(path):
                logger.info(f"Base de données trouvée: {path}")
                return path
        return paths[0]
    
    def check_api_status(self):
        """Vérifie si l'API football-data.org est disponible"""
        if not FOOTBALL_API_KEY:
            logger.warning("Clé API football-data.org non configurée")
            return False
        
        try:
            headers = {'X-Auth-Token': FOOTBALL_API_KEY}
            response = requests.get(f"{FOOTBALL_API_URL}/competitions", headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info("✓ API football-data.org disponible")
                return True
            else:
                logger.warning(f"API indisponible: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erreur API: {e}")
            return False
    
    def fetch_from_api(self, league_code, days=30):
        """Récupère les matchs depuis l'API football-data.org"""
        if not self.api_available:
            return []
        
        headers = {'X-Auth-Token': FOOTBALL_API_KEY}
        date_from = datetime.now().strftime('%Y-%m-%d')
        date_to = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        
        url = f"{FOOTBALL_API_URL}/competitions/{league_code}/matches"
        params = {'dateFrom': date_from, 'dateTo': date_to}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                logger.info(f"API {league_code}: {len(matches)} matchs")
                return matches
            elif response.status_code == 429:
                logger.warning(f"Rate limit API atteint pour {league_code}")
                time.sleep(60)
                return []
            else:
                logger.warning(f"API erreur {league_code}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Erreur API {league_code}: {e}")
            return []
    
    def scrape_soccerstats_matches(self, league_key):
        """Scrape les matchs depuis SoccerStats.com"""
        if league_key not in LEAGUES:
            return []
        
        url = f"{SOCCERSTATS_URL}/results.asp?league={league_key}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            matches = []
            league_info = LEAGUES[league_key]
            
            # Parser les lignes de matchs
            rows = soup.find_all('tr')
            current_date = None
            
            for row in rows:
                cells = row.find_all('td')
                if not cells:
                    continue
                
                text = row.get_text()
                
                # Détecter la date
                date_match = re.search(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(\d+)\s+(\w+)', text)
                if date_match:
                    current_date = date_match.group(0)
                
                # Chercher les équipes (liens)
                links = row.find_all('a')
                teams = []
                for link in links:
                    team_name = link.get_text(strip=True)
                    if team_name and len(team_name) > 2 and not team_name.startswith('stats'):
                        teams.append(team_name)
                
                if len(teams) >= 2:
                    # Chercher le score ou l'heure
                    score_match = re.search(r'(\d+)\s*-\s*(\d+)', text)
                    time_match = re.search(r'(\d{1,2}:\d{2})', text)
                    
                    match_data = {
                        'home_team': teams[0],
                        'away_team': teams[1],
                        'league_id': league_info['api_id'],
                        'league_name': league_info['name'],
                        'date_text': current_date,
                        'source': 'soccerstats'
                    }
                    
                    if score_match:
                        match_data['home_score'] = int(score_match.group(1))
                        match_data['away_score'] = int(score_match.group(2))
                        match_data['status'] = 'FINISHED'
                    elif time_match:
                        match_data['match_time'] = time_match.group(1)
                        match_data['status'] = 'SCHEDULED'
                    
                    matches.append(match_data)
            
            logger.info(f"SoccerStats {league_key}: {len(matches)} matchs")
            return matches
            
        except Exception as e:
            logger.error(f"Erreur scraping {league_key}: {e}")
            return []
    
    def scrape_soccerstats_standings(self, league_key):
        """Scrape le classement depuis SoccerStats.com"""
        if league_key not in LEAGUES:
            return []
        
        url = f"{SOCCERSTATS_URL}/latest.asp?league={league_key}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            standings = []
            league_info = LEAGUES[league_key]
            
            # Chercher le tableau de classement
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 8:
                        team_link = row.find('a')
                        if team_link:
                            team_name = team_link.get_text(strip=True)
                            if team_name and len(team_name) > 2:
                                try:
                                    # Extraire les stats
                                    stats = [c.get_text(strip=True) for c in cells]
                                    
                                    standing = {
                                        'team_name': team_name,
                                        'league_id': league_info['api_id'],
                                        'played': self._parse_int(stats[1]) if len(stats) > 1 else 0,
                                        'won': self._parse_int(stats[2]) if len(stats) > 2 else 0,
                                        'drawn': self._parse_int(stats[3]) if len(stats) > 3 else 0,
                                        'lost': self._parse_int(stats[4]) if len(stats) > 4 else 0,
                                        'goals_for': self._parse_int(stats[5]) if len(stats) > 5 else 0,
                                        'goals_against': self._parse_int(stats[6]) if len(stats) > 6 else 0,
                                        'points': self._parse_int(stats[8]) if len(stats) > 8 else 0,
                                    }
                                    standings.append(standing)
                                except:
                                    continue
            
            logger.info(f"SoccerStats classement {league_key}: {len(standings)} équipes")
            return standings
            
        except Exception as e:
            logger.error(f"Erreur classement {league_key}: {e}")
            return []
    
    def _parse_int(self, value):
        """Parse une valeur en entier"""
        try:
            return int(re.sub(r'[^\d-]', '', str(value)))
        except:
            return 0
    
    def update_database_with_matches(self, matches):
        """Met à jour la base de données avec les matchs"""
        if not os.path.exists(self.db_path):
            logger.error(f"Base de données non trouvée: {self.db_path}")
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        updated = 0
        
        for match in matches:
            try:
                # Vérifier si le match existe déjà
                cursor.execute('''
                    SELECT id FROM matches 
                    WHERE home_team_id IN (SELECT id FROM teams WHERE name LIKE ?)
                    AND away_team_id IN (SELECT id FROM teams WHERE name LIKE ?)
                    AND league_id = ?
                ''', (f"%{match['home_team']}%", f"%{match['away_team']}%", match['league_id']))
                
                existing = cursor.fetchone()
                
                if existing and match.get('status') == 'FINISHED':
                    # Mettre à jour le score
                    cursor.execute('''
                        UPDATE matches 
                        SET home_score = ?, away_score = ?, status = 'FINISHED'
                        WHERE id = ?
                    ''', (match.get('home_score', 0), match.get('away_score', 0), existing[0]))
                    updated += 1
                    
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        
        logger.info(f"Base de données: {updated} matchs mis à jour")
        return updated
    
    def fetch_all_data(self):
        """Récupère toutes les données (API + scraping)"""
        logger.info("🚀 Démarrage de la récupération automatique des données...")
        
        all_matches = []
        all_standings = []
        
        # Vérifier l'API
        api_ok = self.check_api_status()
        
        for league_key, league_info in LEAGUES.items():
            logger.info(f"\n📊 Traitement: {league_info['name']}")
            
            # Essayer l'API d'abord
            if api_ok:
                api_matches = self.fetch_from_api(league_info['api_code'])
                if api_matches:
                    all_matches.extend(api_matches)
                time.sleep(1)
            
            # Compléter avec SoccerStats
            ss_matches = self.scrape_soccerstats_matches(league_key)
            all_matches.extend(ss_matches)
            
            ss_standings = self.scrape_soccerstats_standings(league_key)
            all_standings.extend(ss_standings)
            
            time.sleep(2)  # Rate limiting
        
        # Mettre à jour la base de données
        self.update_database_with_matches(all_matches)
        
        logger.info(f"""
        ✅ Récupération terminée:
        - Matchs: {len(all_matches)}
        - Classements: {len(all_standings)} équipes
        - API disponible: {api_ok}
        """)
        
        return {
            'matches': all_matches,
            'standings': all_standings,
            'api_available': api_ok
        }
    
    def run_scheduled_update(self):
        """Exécute une mise à jour planifiée"""
        logger.info(f"⏰ Mise à jour planifiée: {datetime.now().isoformat()}")
        return self.fetch_all_data()


def main():
    """Point d'entrée principal"""
    fetcher = AutoDataFetcher()
    data = fetcher.fetch_all_data()
    
    # Sauvegarder un résumé
    summary = {
        'timestamp': datetime.now().isoformat(),
        'matches_count': len(data['matches']),
        'standings_count': len(data['standings']),
        'api_available': data['api_available']
    }
    
    with open('/home/ubuntu/football_app/logs/last_update.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Mise à jour terminée: {summary}")


if __name__ == '__main__':
    main()
