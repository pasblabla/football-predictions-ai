#!/usr/bin/env python3
"""
SoccerStats.com Scraper
Récupère les données manquantes de l'API (compositions, suspensions, blessures, tendances)
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional
import sys
import os

# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

class SoccerStatsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.base_url = "https://www.soccerstats.com"
        
    def get_league_code(self, competition_name: str) -> Optional[str]:
        """Convertit le nom de compétition en code SoccerStats"""
        mapping = {
            "Premier League": "england",
            "La Liga": "spain",
            "Serie A": "italy",
            "Bundesliga": "germany",
            "Ligue 1": "france",
            "Eredivisie": "holland",
            "UEFA Champions League": "champions-league",
            "UEFA Europa League": "europa-league"
        }
        return mapping.get(competition_name)
    
    def get_team_slug(self, team_name: str) -> str:
        """Convertit le nom d'équipe en slug pour l'URL"""
        # Simplifier le nom (enlever FC, AFC, etc.)
        team_name = re.sub(r'\b(FC|AFC|CF|United|City)\b', '', team_name, flags=re.IGNORECASE)
        team_name = team_name.strip()
        
        # Mapper les noms spéciaux
        special_names = {
            "Manchester": "man-utd",
            "Liverpool": "liverpool",
            "Arsenal": "arsenal",
            "Chelsea": "chelsea",
            "Tottenham": "tottenham",
            "Newcastle": "newcastle",
            "Sunderland": "sunderland"
        }
        
        for key, value in special_names.items():
            if key.lower() in team_name.lower():
                return value
        
        # Slug par défaut
        return team_name.lower().replace(' ', '-')
    
    def scrape_match_preview(self, home_team: str, away_team: str, competition: str) -> Dict:
        """Récupère les données d'un match depuis SoccerStats"""
        league_code = self.get_league_code(competition)
        if not league_code:
            print(f"❌ Compétition non supportée: {competition}")
            return {}
        
        home_slug = self.get_team_slug(home_team)
        away_slug = self.get_team_slug(away_team)
        
        # URL du match preview
        url = f"{self.base_url}/pmatch.asp?league={league_code}&stats={home_slug}-{away_slug}"
        
        try:
            print(f"🔍 Scraping: {home_team} vs {away_team}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = {
                'home_team': home_team,
                'away_team': away_team,
                'competition': competition,
                'trends': self.extract_trends(soup),
                'stats': self.extract_stats(soup),
                'analysis': self.extract_analysis(soup),
                'form': self.extract_form(soup)
            }
            
            print(f"✅ Données récupérées: {len(data['trends'])} tendances, {len(data['stats'])} stats")
            return data
            
        except Exception as e:
            print(f"❌ Erreur scraping {home_team} vs {away_team}: {e}")
            return {}
    
    def extract_trends(self, soup: BeautifulSoup) -> Dict:
        """Extrait les tendances (Up/Down trends, Points of Interest)"""
        trends = {
            'home': {'up': [], 'down': [], 'points': []},
            'away': {'up': [], 'down': [], 'points': []}
        }
        
        # Chercher les sections de tendances
        trend_sections = soup.find_all('div', class_=re.compile(r'trend'))
        
        for section in trend_sections:
            # Identifier si c'est home ou away
            team_type = 'home' if 'home' in section.get('class', []) else 'away'
            
            # Up trends (▲)
            up_items = section.find_all('li', class_='up-trend')
            trends[team_type]['up'] = [item.get_text(strip=True) for item in up_items]
            
            # Down trends (▼)
            down_items = section.find_all('li', class_='down-trend')
            trends[team_type]['down'] = [item.get_text(strip=True) for item in down_items]
            
            # Points of Interest (★)
            poi_items = section.find_all('li', class_='point-interest')
            trends[team_type]['points'] = [item.get_text(strip=True) for item in poi_items]
        
        return trends
    
    def extract_stats(self, soup: BeautifulSoup) -> Dict:
        """Extrait les statistiques détaillées"""
        stats = {}
        
        # Points Per Game (PPG)
        ppg_section = soup.find('div', string=re.compile(r'Points Per Game'))
        if ppg_section:
            ppg_values = ppg_section.find_all('span', class_='stat-value')
            if len(ppg_values) >= 2:
                stats['ppg_home'] = float(ppg_values[0].get_text(strip=True))
                stats['ppg_away'] = float(ppg_values[1].get_text(strip=True))
        
        # Performance Rating (PR)
        pr_section = soup.find('div', string=re.compile(r'Performance Rating'))
        if pr_section:
            pr_values = pr_section.find_all('span', class_='stat-value')
            if len(pr_values) >= 2:
                stats['pr_home'] = float(pr_values[0].get_text(strip=True).replace('%', ''))
                stats['pr_away'] = float(pr_values[1].get_text(strip=True).replace('%', ''))
        
        return stats
    
    def extract_analysis(self, soup: BeautifulSoup) -> str:
        """Extrait l'analyse textuelle du match"""
        analysis_section = soup.find('div', class_='match-analysis')
        if analysis_section:
            paragraphs = analysis_section.find_all('p')
            return ' '.join([p.get_text(strip=True) for p in paragraphs])
        return ""
    
    def extract_form(self, soup: BeautifulSoup) -> Dict:
        """Extrait la forme récente (derniers résultats)"""
        form = {'home': [], 'away': []}
        
        # Chercher les résultats récents
        results_section = soup.find('div', class_='recent-results')
        if results_section:
            home_results = results_section.find_all('span', class_='home-result')
            away_results = results_section.find_all('span', class_='away-result')
            
            form['home'] = [r.get_text(strip=True) for r in home_results[:5]]
            form['away'] = [r.get_text(strip=True) for r in away_results[:5]]
        
        return form

def main():
    """Test du scraper sur quelques matchs"""
    scraper = SoccerStatsScraper()
    
    # Matchs de test
    test_matches = [
        ("Sunderland", "Arsenal", "Premier League"),
        ("Liverpool", "Manchester City", "Premier League"),
        ("Chelsea", "Tottenham", "Premier League")
    ]
    
    for home, away, comp in test_matches:
        data = scraper.scrape_match_preview(home, away, comp)
        if data:
            print(f"\n📊 {home} vs {away}:")
            print(f"  Tendances home: {len(data['trends']['home']['up'])} up, {len(data['trends']['home']['down'])} down")
            print(f"  Tendances away: {len(data['trends']['away']['up'])} up, {len(data['trends']['away']['down'])} down")
            if data['stats']:
                print(f"  Stats: PPG {data['stats'].get('ppg_home', 'N/A')} vs {data['stats'].get('ppg_away', 'N/A')}")
        
        # Pause entre les requêtes pour ne pas surcharger le serveur
        time.sleep(3)

if __name__ == "__main__":
    main()

