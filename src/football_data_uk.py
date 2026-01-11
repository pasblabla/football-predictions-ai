"""
Module d'intégration avec football-data.co.uk
Télécharge et traite les données CSV de résultats de football historiques
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import logging

# Configuration des URLs pour les principales ligues
LEAGUE_URLS = {
    'Premier League': 'https://www.football-data.co.uk/mmz4281/2425/E0.csv',  # Angleterre Premier League
    'Championship': 'https://www.football-data.co.uk/mmz4281/2425/E1.csv',   # Angleterre Championship
    'Ligue 1': 'https://www.football-data.co.uk/mmz4281/2425/F1.csv',        # France Ligue 1
    'Bundesliga': 'https://www.football-data.co.uk/mmz4281/2425/D1.csv',     # Allemagne Bundesliga
    'Serie A': 'https://www.football-data.co.uk/mmz4281/2425/I1.csv',        # Italie Serie A
    'La Liga': 'https://www.football-data.co.uk/mmz4281/2425/SP1.csv',       # Espagne La Liga
}

# Mapping des colonnes CSV vers notre format
COLUMN_MAPPING = {
    'Date': 'date',
    'HomeTeam': 'home_team',
    'AwayTeam': 'away_team',
    'FTHG': 'home_score',
    'FTAG': 'away_score',
    'FTR': 'result',
    'HTHG': 'ht_home_score',
    'HTAG': 'ht_away_score',
    'HTR': 'ht_result',
    'HS': 'home_shots',
    'AS': 'away_shots',
    'HST': 'home_shots_target',
    'AST': 'away_shots_target',
    'HC': 'home_corners',
    'AC': 'away_corners',
    'HF': 'home_fouls',
    'AF': 'away_fouls',
    'HY': 'home_yellow',
    'AY': 'away_yellow',
    'HR': 'home_red',
    'AR': 'away_red'
}

class FootballDataUKIntegration:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_cache = {}
        
    def download_league_data(self, league_name):
        """Télécharge les données d'une ligue spécifique"""
        if league_name not in LEAGUE_URLS:
            raise ValueError(f"Ligue non supportée: {league_name}")
            
        url = LEAGUE_URLS[league_name]
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Sauvegarde temporaire du fichier CSV
            temp_file = f"/tmp/{league_name.replace(' ', '_')}.csv"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            # Lecture avec pandas
            df = pd.read_csv(temp_file)
            
            # Nettoyage
            os.remove(temp_file)
            
            self.logger.info(f"Données téléchargées pour {league_name}: {len(df)} matchs")
            return df
            
        except Exception as e:
            self.logger.error(f"Erreur lors du téléchargement de {league_name}: {e}")
            return None
    
    def process_match_data(self, df, league_name):
        """Traite les données de matchs pour les convertir au format de notre API"""
        processed_matches = []
        
        for _, row in df.iterrows():
            try:
                # Conversion de la date
                match_date = pd.to_datetime(row['Date'], format='%d/%m/%Y')
                
                # Création du match
                match = {
                    'date': match_date.isoformat(),
                    'league': league_name,
                    'home_team': row['HomeTeam'],
                    'away_team': row['AwayTeam'],
                    'home_score': int(row['FTHG']) if pd.notna(row['FTHG']) else None,
                    'away_score': int(row['FTAG']) if pd.notna(row['FTAG']) else None,
                    'status': 'FINISHED' if pd.notna(row['FTHG']) else 'SCHEDULED',
                    'venue': f"{row['HomeTeam']} Stadium",
                    'statistics': self._extract_statistics(row)
                }
                
                processed_matches.append(match)
                
            except Exception as e:
                self.logger.warning(f"Erreur lors du traitement d'un match: {e}")
                continue
                
        return processed_matches
    
    def _extract_statistics(self, row):
        """Extrait les statistiques de match"""
        stats = {}
        
        # Statistiques de base
        for csv_col, api_col in COLUMN_MAPPING.items():
            if csv_col in row and pd.notna(row[csv_col]):
                if csv_col in ['FTHG', 'FTAG', 'HTHG', 'HTAG', 'HS', 'AS', 'HST', 'AST', 'HC', 'AC', 'HF', 'AF', 'HY', 'AY', 'HR', 'AR']:
                    stats[api_col] = int(row[csv_col])
                else:
                    stats[api_col] = row[csv_col]
        
        return stats
    
    def get_recent_matches(self, league_name, days_back=7):
        """Récupère les matchs récents d'une ligue"""
        df = self.download_league_data(league_name)
        if df is None:
            return []
            
        # Filtrer les matchs récents
        cutoff_date = datetime.now() - timedelta(days=days_back)
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        recent_df = df[df['Date'] >= cutoff_date]
        
        return self.process_match_data(recent_df, league_name)
    
    def get_upcoming_matches(self, league_name):
        """Récupère les matchs à venir d'une ligue"""
        df = self.download_league_data(league_name)
        if df is None:
            return []
            
        # Filtrer les matchs sans résultat (à venir)
        upcoming_df = df[pd.isna(df['FTHG'])]
        
        return self.process_match_data(upcoming_df, league_name)
    
    def update_all_leagues(self):
        """Met à jour toutes les ligues supportées"""
        all_matches = []
        
        for league_name in LEAGUE_URLS.keys():
            try:
                matches = self.get_recent_matches(league_name, days_back=30)
                all_matches.extend(matches)
                self.logger.info(f"Récupéré {len(matches)} matchs pour {league_name}")
            except Exception as e:
                self.logger.error(f"Erreur lors de la mise à jour de {league_name}: {e}")
                
        return all_matches

# Instance globale
football_data_uk = FootballDataUKIntegration()

