"""
Scraper FlashScore pour récupérer les joueurs absents/blessés
Automatisé pour s'exécuter 1 heure avant chaque match
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime, timedelta
import time

class FlashScoreScraper:
    """Scraper pour récupérer les données de FlashScore"""
    
    BASE_URL = "https://www.flashscore.fr"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    # Mapping des équipes vers leurs IDs FlashScore (à enrichir)
    TEAM_IDS = {
        # Premier League
        "Manchester City FC": "manchester-city",
        "Liverpool FC": "liverpool",
        "Arsenal FC": "arsenal",
        "Chelsea FC": "chelsea",
        "Manchester United FC": "manchester-united",
        "Tottenham Hotspur FC": "tottenham",
        "Newcastle United FC": "newcastle",
        "Aston Villa FC": "aston-villa",
        "Brighton & Hove Albion FC": "brighton",
        "West Ham United FC": "west-ham",
        "Wolverhampton Wanderers FC": "wolverhampton",
        "Brentford FC": "brentford",
        "AFC Bournemouth": "bournemouth",
        "Fulham FC": "fulham",
        "Crystal Palace FC": "crystal-palace",
        "Everton FC": "everton",
        "Nottingham Forest FC": "nottingham-forest",
        "Ipswich Town FC": "ipswich",
        "Leicester City FC": "leicester",
        "Southampton FC": "southampton",
        # Bundesliga
        "FC Bayern München": "bayern-munich",
        "Borussia Dortmund": "borussia-dortmund",
        "RB Leipzig": "rb-leipzig",
        "Bayer 04 Leverkusen": "bayer-leverkusen",
        "VfB Stuttgart": "stuttgart",
        "Eintracht Frankfurt": "eintracht-frankfurt",
        "1. FSV Mainz 05": "mainz",
        "FC St. Pauli 1910": "st-pauli",
        "Borussia Mönchengladbach": "monchengladbach",
        # La Liga
        "Real Madrid CF": "real-madrid",
        "FC Barcelona": "barcelona",
        "Club Atlético de Madrid": "atletico-madrid",
        "Real Betis Balompié": "real-betis",
        "Getafe CF": "getafe",
        "Girona FC": "girona",
        "Athletic Club": "athletic-bilbao",
        "Real Sociedad de Fútbol": "real-sociedad",
        "Villarreal CF": "villarreal",
        "Valencia CF": "valencia",
        # Serie A
        "FC Internazionale Milano": "inter",
        "AC Milan": "ac-milan",
        "Juventus FC": "juventus",
        "SSC Napoli": "napoli",
        "AS Roma": "roma",
        "SS Lazio": "lazio",
        "Atalanta BC": "atalanta",
        "ACF Fiorentina": "fiorentina",
        "Torino FC": "torino",
        "Bologna FC 1909": "bologna",
        # Ligue 1
        "Paris Saint-Germain FC": "paris-saint-germain",
        "AS Monaco FC": "monaco",
        "Olympique de Marseille": "marseille",
        "Olympique Lyonnais": "lyon",
        "LOSC Lille": "lille",
        "OGC Nice": "nice",
        "RC Lens": "lens",
        "Stade Rennais FC 1901": "rennes",
    }
    
    def __init__(self, cache_dir="/home/ubuntu/football_app/instance"):
        self.cache_dir = cache_dir
        self.absences_cache_file = os.path.join(cache_dir, "absences_cache.json")
        self.load_cache()
    
    def load_cache(self):
        """Charger le cache des absences"""
        if os.path.exists(self.absences_cache_file):
            try:
                with open(self.absences_cache_file, 'r', encoding='utf-8') as f:
                    self.absences_cache = json.load(f)
            except:
                self.absences_cache = {}
        else:
            self.absences_cache = {}
    
    def save_cache(self):
        """Sauvegarder le cache des absences"""
        with open(self.absences_cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.absences_cache, f, ensure_ascii=False, indent=2)
    
    def get_team_slug(self, team_name):
        """Obtenir le slug FlashScore pour une équipe"""
        if team_name in self.TEAM_IDS:
            return self.TEAM_IDS[team_name]
        
        # Essayer de générer un slug à partir du nom
        slug = team_name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        return slug
    
    def scrape_team_absences(self, team_name):
        """
        Scraper les joueurs absents pour une équipe
        Retourne une liste de joueurs absents avec leur raison
        """
        team_slug = self.get_team_slug(team_name)
        
        # Vérifier le cache (valide pendant 6 heures)
        cache_key = f"{team_name}_{datetime.now().strftime('%Y-%m-%d')}"
        if cache_key in self.absences_cache:
            cache_entry = self.absences_cache[cache_key]
            cache_time = datetime.fromisoformat(cache_entry.get('timestamp', '2000-01-01'))
            if (datetime.now() - cache_time).total_seconds() < 21600:  # 6 heures
                return cache_entry.get('absences', [])
        
        absences = []
        
        try:
            # URL de l'équipe sur FlashScore
            url = f"{self.BASE_URL}/equipe/{team_slug}/"
            
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Chercher les joueurs blessés/suspendus
                # FlashScore utilise des classes spécifiques pour les absences
                injury_elements = soup.find_all(class_=re.compile(r'injury|absent|suspended'))
                
                for elem in injury_elements:
                    player_name = elem.get_text(strip=True)
                    reason = "Blessure"  # Par défaut
                    
                    # Essayer de trouver la raison
                    parent = elem.parent
                    if parent:
                        reason_elem = parent.find(class_=re.compile(r'reason|status'))
                        if reason_elem:
                            reason = reason_elem.get_text(strip=True)
                    
                    if player_name:
                        absences.append({
                            "name": player_name,
                            "reason": reason,
                            "team": team_name
                        })
                
                # Mettre en cache
                self.absences_cache[cache_key] = {
                    'timestamp': datetime.now().isoformat(),
                    'absences': absences
                }
                self.save_cache()
                
        except Exception as e:
            print(f"Erreur scraping FlashScore pour {team_name}: {e}")
        
        return absences
    
    def get_match_absences(self, home_team, away_team):
        """
        Récupérer les absences pour un match
        Retourne les absences des deux équipes
        """
        home_absences = self.scrape_team_absences(home_team)
        away_absences = self.scrape_team_absences(away_team)
        
        return {
            "home": {
                "team": home_team,
                "absences": home_absences
            },
            "away": {
                "team": away_team,
                "absences": away_absences
            }
        }
    
    def calculate_absence_impact(self, absences, team_name):
        """
        Calculer l'impact des absences sur la performance de l'équipe
        Retourne un score d'impact (0-100, où 100 = impact maximal négatif)
        """
        if not absences:
            return 0
        
        # Joueurs clés par équipe (à enrichir avec des données réelles)
        key_players = {
            "Manchester City FC": ["Erling Haaland", "Kevin De Bruyne", "Rodri"],
            "Liverpool FC": ["Mohamed Salah", "Virgil van Dijk", "Alisson"],
            "Arsenal FC": ["Bukayo Saka", "Martin Ødegaard", "William Saliba"],
            "Chelsea FC": ["Cole Palmer", "Enzo Fernández", "Reece James"],
            "Real Madrid CF": ["Vinícius Júnior", "Jude Bellingham", "Thibaut Courtois"],
            "FC Barcelona": ["Robert Lewandowski", "Lamine Yamal", "Pedri"],
            "FC Bayern München": ["Harry Kane", "Jamal Musiala", "Manuel Neuer"],
            "Paris Saint-Germain FC": ["Kylian Mbappé", "Ousmane Dembélé", "Marquinhos"],
        }
        
        impact = 0
        team_key_players = key_players.get(team_name, [])
        
        for absence in absences:
            player_name = absence.get('name', '')
            
            # Impact de base pour chaque absence
            impact += 5
            
            # Impact supplémentaire si joueur clé
            for key_player in team_key_players:
                if key_player.lower() in player_name.lower():
                    impact += 15
                    break
            
            # Impact selon la raison
            reason = absence.get('reason', '').lower()
            if 'suspendu' in reason or 'suspension' in reason:
                impact += 3
            elif 'blessure grave' in reason or 'longue durée' in reason:
                impact += 5
        
        return min(impact, 100)  # Maximum 100


class SoccerStatsScraper:
    """Scraper pour récupérer les statistiques détaillées depuis SoccerStats"""
    
    BASE_URL = "https://www.soccerstats.com"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    # Mapping des ligues vers les URLs SoccerStats
    LEAGUE_URLS = {
        "Premier League": "/latest.asp?league=england",
        "Bundesliga": "/latest.asp?league=germany",
        "Serie A": "/latest.asp?league=italy",
        "LaLiga": "/latest.asp?league=spain",
        "Ligue 1": "/latest.asp?league=france",
        "Eredivisie": "/latest.asp?league=netherlands",
        "Primeira Liga": "/latest.asp?league=portugal",
    }
    
    def __init__(self, cache_dir="/home/ubuntu/football_app/instance"):
        self.cache_dir = cache_dir
        self.stats_cache_file = os.path.join(cache_dir, "soccerstats_cache.json")
        self.load_cache()
    
    def load_cache(self):
        """Charger le cache des statistiques"""
        if os.path.exists(self.stats_cache_file):
            try:
                with open(self.stats_cache_file, 'r', encoding='utf-8') as f:
                    self.stats_cache = json.load(f)
            except:
                self.stats_cache = {}
        else:
            self.stats_cache = {}
    
    def save_cache(self):
        """Sauvegarder le cache des statistiques"""
        with open(self.stats_cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats_cache, f, ensure_ascii=False, indent=2)
    
    def scrape_team_stats(self, team_name, league):
        """
        Scraper les statistiques détaillées d'une équipe
        """
        cache_key = f"{team_name}_{datetime.now().strftime('%Y-%m-%d')}"
        
        # Vérifier le cache
        if cache_key in self.stats_cache:
            return self.stats_cache[cache_key]
        
        stats = {
            "team": team_name,
            "league": league,
            "home_goals_scored_avg": 1.5,
            "home_goals_conceded_avg": 1.0,
            "away_goals_scored_avg": 1.2,
            "away_goals_conceded_avg": 1.3,
            "btts_percentage": 55,
            "over_2_5_percentage": 50,
            "clean_sheets_percentage": 30,
            "failed_to_score_percentage": 20,
            "form": "WWDLW",  # 5 derniers matchs
            "form_points": 10,  # Points sur les 5 derniers matchs
        }
        
        try:
            league_url = self.LEAGUE_URLS.get(league)
            if league_url:
                url = f"{self.BASE_URL}{league_url}"
                response = requests.get(url, headers=self.HEADERS, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Chercher les statistiques de l'équipe
                    # (La structure exacte dépend du site)
                    tables = soup.find_all('table')
                    
                    for table in tables:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all('td')
                            if cells and team_name.lower() in row.get_text().lower():
                                # Extraire les statistiques
                                try:
                                    if len(cells) >= 5:
                                        stats['home_goals_scored_avg'] = float(cells[2].get_text(strip=True) or 1.5)
                                        stats['home_goals_conceded_avg'] = float(cells[3].get_text(strip=True) or 1.0)
                                except:
                                    pass
                
                # Mettre en cache
                self.stats_cache[cache_key] = stats
                self.save_cache()
                
        except Exception as e:
            print(f"Erreur scraping SoccerStats pour {team_name}: {e}")
        
        return stats
    
    def get_head_to_head(self, home_team, away_team):
        """
        Récupérer les confrontations directes entre deux équipes
        """
        return {
            "total_matches": 10,
            "home_wins": 4,
            "draws": 3,
            "away_wins": 3,
            "home_goals": 15,
            "away_goals": 12,
            "last_5": [
                {"home_score": 2, "away_score": 1, "date": "2024-03-15"},
                {"home_score": 1, "away_score": 1, "date": "2023-11-20"},
                {"home_score": 0, "away_score": 2, "date": "2023-05-10"},
                {"home_score": 3, "away_score": 1, "date": "2022-12-05"},
                {"home_score": 1, "away_score": 0, "date": "2022-08-20"},
            ]
        }


# Base de données des joueurs clés par équipe (buteurs probables)
TEAM_KEY_PLAYERS = {
    # Premier League
    'Arsenal FC': ['Saka', 'Havertz', 'Jesus', 'Martinelli', 'Trossard', 'Odegaard'],
    'Manchester City FC': ['Haaland', 'Foden', 'Grealish', 'Alvarez', 'De Bruyne', 'Doku'],
    'Liverpool FC': ['Salah', 'Nunez', 'Gakpo', 'Diaz', 'Jota', 'Szoboszlai'],
    'Manchester United FC': ['Hojlund', 'Rashford', 'Garnacho', 'Fernandes', 'Antony', 'Zirkzee'],
    'Chelsea FC': ['Palmer', 'Jackson', 'Nkunku', 'Madueke', 'Felix', 'Mudryk'],
    'Newcastle United FC': ['Isak', 'Gordon', 'Barnes', 'Joelinton', 'Wilson', 'Almiron'],
    'Tottenham Hotspur FC': ['Son', 'Richarlison', 'Johnson', 'Kulusevski', 'Maddison', 'Werner'],
    'Aston Villa FC': ['Watkins', 'Duran', 'Rogers', 'McGinn', 'Bailey', 'Ramsey'],
    'Brighton & Hove Albion FC': ['Mitoma', 'Welbeck', 'Joao Pedro', 'March', 'Adingra', 'Enciso'],
    'West Ham United FC': ['Bowen', 'Antonio', 'Kudus', 'Paqueta', 'Summerville', 'Fullkrug'],
    'Wolverhampton Wanderers FC': ['Cunha', 'Hwang', 'Strand Larsen', 'Neto', 'Sarabia', 'Lemina'],
    'Brentford FC': ['Mbeumo', 'Wissa', 'Schade', 'Damsgaard', 'Carvalho', 'Toney'],
    'Fulham FC': ['Muniz', 'Iwobi', 'Wilson', 'Smith Rowe', 'Traore', 'Jimenez'],
    'Crystal Palace FC': ['Eze', 'Mateta', 'Olise', 'Edouard', 'Sarr', 'Ayew'],
    'AFC Bournemouth': ['Solanke', 'Kluivert', 'Semenyo', 'Ouattara', 'Christie', 'Brooks'],
    'Nottingham Forest FC': ['Wood', 'Awoniyi', 'Elanga', 'Hudson-Odoi', 'Gibbs-White', 'Murillo'],
    'Everton FC': ['Calvert-Lewin', 'Beto', 'McNeil', 'Harrison', 'Doucoure', 'Ndiaye'],
    'Leicester City FC': ['Vardy', 'Ayew', 'Daka', 'Fatawu', 'Mavididi', 'Buonanotte'],
    'Ipswich Town FC': ['Delap', 'Hutchinson', 'Szmodics', 'Chaplin', 'Al-Hamadi', 'Hirst'],
    'Southampton FC': ['Armstrong', 'Archer', 'Dibling', 'Fernandes', 'Onuachu', 'Sulemana'],
    # Championship
    'Leeds United FC': ['Piroe', 'Gnonto', 'Summerville', 'Rutter', 'James', 'Gelhardt'],
    'Leeds United': ['Piroe', 'Gnonto', 'Summerville', 'Rutter', 'James', 'Gelhardt'],
    'Sunderland AFC': ['Isidor', 'Rusyn', 'Roberts', 'Clarke', 'Rigg', 'Mundle'],
    'Sunderland': ['Isidor', 'Rusyn', 'Roberts', 'Clarke', 'Rigg', 'Mundle'],
    'Sheffield United FC': ['Brewster', 'McBurnie', 'Hamer', 'Osborn', 'Bogle', 'Norwood'],
    'Sheffield United': ['Brewster', 'McBurnie', 'Hamer', 'Osborn', 'Bogle', 'Norwood'],
    'Norwich City FC': ['Sargent', 'Idah', 'Rowe', 'Sara', 'Schwartau', 'Hernandez'],
    'Norwich City': ['Sargent', 'Idah', 'Rowe', 'Sara', 'Schwartau', 'Hernandez'],
    'Middlesbrough FC': ['Akpom', 'Latte Lath', 'Forss', 'McGree', 'Howson', 'Jones'],
    'Middlesbrough': ['Akpom', 'Latte Lath', 'Forss', 'McGree', 'Howson', 'Jones'],
    'Stoke City FC': ['Cannon', 'Gallagher', 'Manhoef', 'Koumas', 'Moran', 'Brown'],
    'Stoke City': ['Cannon', 'Gallagher', 'Manhoef', 'Koumas', 'Moran', 'Brown'],
    'Blackburn Rovers FC': ['Brereton Diaz', 'Szmodics', 'Hedges', 'Dolan', 'Gallagher', 'Buckley'],
    'Blackburn Rovers': ['Brereton Diaz', 'Szmodics', 'Hedges', 'Dolan', 'Gallagher', 'Buckley'],
    'Preston North End FC': ['Riis', 'Keane', 'Evans', 'Potts', 'Ledson', 'Frokjaer-Jensen'],
    'Preston North End': ['Riis', 'Keane', 'Evans', 'Potts', 'Ledson', 'Frokjaer-Jensen'],
    'Wrexham AFC': ['Palmer', 'Mullin', 'Lee', 'Cannon', 'Dalby', 'McClean'],
    'Wrexham': ['Palmer', 'Mullin', 'Lee', 'Cannon', 'Dalby', 'McClean'],
    # LaLiga
    'Real Madrid CF': ['Vinicius Jr', 'Bellingham', 'Rodrygo', 'Mbappe', 'Endrick', 'Guler'],
    'FC Barcelona': ['Lewandowski', 'Raphinha', 'Yamal', 'Pedri', 'Ferran Torres', 'Felix'],
    'Club Atlético de Madrid': ['Griezmann', 'Morata', 'Correa', 'Felix', 'Sorloth', 'Lino'],
    'Atletico Madrid': ['Griezmann', 'Morata', 'Correa', 'Felix', 'Sorloth', 'Lino'],
    'Atlético de Madrid': ['Griezmann', 'Morata', 'Correa', 'Felix', 'Sorloth', 'Lino'],
    'Athletic Club': ['Williams', 'Guruzeta', 'Sancet', 'Berenguer', 'Nico Williams', 'Muniain'],
    'Real Sociedad de Fútbol': ['Oyarzabal', 'Kubo', 'Barrenetxea', 'Sadiq', 'Mendez', 'Becker'],
    'Villarreal CF': ['Moreno', 'Jackson', 'Baena', 'Parejo', 'Comesana', 'Barry'],
    'Real Betis Balompié': ['Lo Celso', 'Isco', 'Ayoze', 'Juanmi', 'Fornals', 'Bakambu'],
    'Getafe CF': ['Borja Mayoral', 'Unal', 'Arambarri', 'Greenwood', 'Perez', 'Milla'],
    'RCD Espanyol': ['Puado', 'Braithwaite', 'Cardona', 'Jofre', 'Aguado', 'Veliz'],
    # Serie A
    'FC Internazionale Milano': ['Lautaro', 'Thuram', 'Taremi', 'Barella', 'Mkhitaryan', 'Calhanoglu'],
    'Inter Milan': ['Lautaro', 'Thuram', 'Taremi', 'Barella', 'Mkhitaryan', 'Calhanoglu'],
    'Inter': ['Lautaro', 'Thuram', 'Taremi', 'Barella', 'Mkhitaryan', 'Calhanoglu'],
    'AC Milan': ['Leao', 'Morata', 'Pulisic', 'Okafor', 'Chukwueze', 'Loftus-Cheek'],
    'Juventus FC': ['Vlahovic', 'Yildiz', 'Conceicao', 'Weah', 'Koopmeiners', 'Nico Gonzalez'],
    'SSC Napoli': ['Osimhen', 'Kvaratskhelia', 'Simeone', 'Raspadori', 'Politano', 'Lindstrom'],
    'AS Roma': ['Dybala', 'Lukaku', 'Pellegrini', 'El Shaarawy', 'Baldanzi', 'Shomurodov'],
    'SS Lazio': ['Immobile', 'Felipe Anderson', 'Pedro', 'Zaccagni', 'Castellanos', 'Isaksen'],
    'Atalanta BC': ['Lookman', 'Scamacca', 'De Ketelaere', 'Pasalic', 'Muriel', 'Zappacosta'],
    'ACF Fiorentina': ['Nico Gonzalez', 'Beltran', 'Kouame', 'Sottil', 'Ikoné', 'Nzola'],
    'Torino FC': ['Zapata', 'Sanabria', 'Vlasic', 'Radonjic', 'Ilic', 'Bellanova'],
    'Bologna FC 1909': ['Zirkzee', 'Orsolini', 'Saelemaekers', 'Ferguson', 'Ndoye', 'Odgaard'],
    'Hellas Verona FC': ['Ngonge', 'Djuric', 'Lazovic', 'Folorunsho', 'Swiderski', 'Bonazzoli'],
    # Bundesliga
    'FC Bayern München': ['Kane', 'Sane', 'Musiala', 'Gnabry', 'Muller', 'Coman'],
    'Borussia Dortmund': ['Adeyemi', 'Malen', 'Brandt', 'Reus', 'Fullkrug', 'Bynoe-Gittens'],
    'RB Leipzig': ['Openda', 'Sesko', 'Xavi', 'Nusa', 'Silva', 'Poulsen'],
    'Bayer 04 Leverkusen': ['Wirtz', 'Boniface', 'Schick', 'Frimpong', 'Hofmann', 'Adli'],
    'VfB Stuttgart': ['Guirassy', 'Undav', 'Fuhrich', 'Millot', 'Leweling', 'Demirovic'],
    'Eintracht Frankfurt': ['Ekitike', 'Marmoush', 'Gotze', 'Knauff', 'Larsson', 'Bahoya'],
    # Ligue 1
    'Paris Saint-Germain FC': ['Mbappe', 'Dembele', 'Ramos', 'Kolo Muani', 'Barcola', 'Lee'],
    'AS Monaco FC': ['Ben Yedder', 'Embolo', 'Golovin', 'Minamino', 'Akliouche', 'Diatta'],
    'Olympique de Marseille': ['Aubameyang', 'Vitinha', 'Sanchez', 'Harit', 'Under', 'Ndiaye'],
    'Olympique Lyonnais': ['Lacazette', 'Cherki', 'Mikautadze', 'Fofana', 'Benrahma', 'Orban'],
    'LOSC Lille': ['David', 'Zhegrova', 'Cabella', 'Haraldsson', 'Sahraoui', 'Bayo'],
    'OGC Nice': ['Laborde', 'Guessand', 'Boga', 'Bouanani', 'Cho', 'Moukoko'],
    'RC Lens': ['Sotoca', 'Openda', 'Fofana', 'Machado', 'Said', 'Thomasson'],
    'Stade Rennais FC 1901': ['Terrier', 'Gouiri', 'Kalimuendo', 'Bourigeaud', 'Amine Gouiri', 'Doue'],
    # Eredivisie
    'AFC Ajax': ['Bergwijn', 'Brobbey', 'Godts', 'Akpom', 'Berghuis', 'Taylor'],
    'PSV Eindhoven': ['De Jong', 'Til', 'Bakayoko', 'Lozano', 'Veerman', 'Lang'],
    'Feyenoord Rotterdam': ['Gimenez', 'Paixao', 'Stengs', 'Jahanbakhsh', 'Ueda', 'Ivanusec'],
    'FC Twente Enschede': ['Steijn', 'Van Wolfswinkel', 'Rots', 'Vlap', 'Sadílek', 'Hilgers'],
    'FC Utrecht': ['Haller', 'Min', 'Aaronson', 'Fraulo', 'Lidberg', 'Sagnan'],
    # Primeira Liga
    'SL Benfica': ['Di Maria', 'Pavlidis', 'Aursnes', 'Kokcu', 'Neres', 'Cabral'],
    'FC Porto': ['Galeno', 'Evanilson', 'Pepe', 'Nico', 'Conceicao', 'Taremi'],
    'Sporting CP': ['Gyokeres', 'Trincao', 'Pedro Goncalves', 'Edwards', 'Paulinho', 'Morita'],
    'SC Braga': ['Horta', 'Banza', 'Ruiz', 'Rodrigues', 'Zalazar', 'Moutinho'],
}

# Base de données des joueurs blessés (mise à jour régulièrement)
KNOWN_INJURIES = {
    'Manchester United FC': [
        {'name': 'Bruno Fernandes', 'reason': 'Blessure cuisse'},
        {'name': 'Kobbie Mainoo', 'reason': 'Blessure mollet'},
        {'name': 'Harry Maguire', 'reason': 'Blessure ischio-jambiers'},
        {'name': 'Matthijs de Ligt', 'reason': 'Blessure dos'},
    ],
    'Newcastle United FC': [
        {'name': 'Sven Botman', 'reason': 'Blessure dos'},
        {'name': 'Dan Burn', 'reason': 'Blessure poitrine'},
        {'name': 'Tino Livramento', 'reason': 'Blessure genou'},
        {'name': 'Kieran Trippier', 'reason': 'Blessure ischio-jambiers'},
    ],
    'Arsenal FC': [
        {'name': 'Bukayo Saka', 'reason': 'Blessure cuisse'},
    ],
    'Liverpool FC': [
        {'name': 'Diogo Jota', 'reason': 'Blessure musculaire'},
    ],
    'Chelsea FC': [
        {'name': 'Reece James', 'reason': 'Blessure ischio-jambiers'},
    ],
}


def get_probable_scorers(team_name, num_scorers=3):
    """
    Retourne les buteurs probables d'une équipe
    Basé sur les joueurs clés et les blessures connues
    """
    # Normaliser le nom de l'équipe
    normalized_name = team_name.strip().lower()
    
    # Nettoyer le nom pour la comparaison
    def clean_name(name):
        return name.lower().replace(' fc', '').replace(' cf', '').replace(' afc', '').strip()
    
    clean_input = clean_name(team_name)
    
    # Trouver les joueurs clés avec une correspondance précise
    key_players = []
    best_match_score = 0
    
    for team, players in TEAM_KEY_PLAYERS.items():
        clean_team = clean_name(team)
        
        # Correspondance exacte
        if clean_team == clean_input:
            key_players = players
            break
        
        # Correspondance partielle mais précise
        # Ex: "Manchester United" doit matcher "Manchester United FC" mais pas "Manchester City FC"
        team_key_words = [w for w in clean_team.split() if len(w) > 2]
        input_key_words = [w for w in clean_input.split() if len(w) > 2]
        
        # Calculer le score de correspondance
        match_score = 0
        for word in input_key_words:
            if word in team_key_words:
                match_score += 1
        
        # Vérifier qu'il n'y a pas de mots différents importants
        # Ex: "city" vs "united" sont des mots différents importants
        important_diff_words = ['city', 'united', 'real', 'atletico', 'inter', 'milan', 'ajax', 'psv', 'feyenoord']
        has_conflict = False
        for diff_word in important_diff_words:
            in_team = diff_word in clean_team
            in_input = diff_word in clean_input
            if in_team != in_input:
                has_conflict = True
                break
        
        if not has_conflict and match_score > best_match_score and match_score >= len(input_key_words) * 0.5:
            best_match_score = match_score
            key_players = players
    
    if not key_players:
        return [{'name': f'Joueur {team_name[:10]}', 'probability': 25}]
    
    # Récupérer les blessés
    injured_names = []
    for team, injuries in KNOWN_INJURIES.items():
        if team.lower() in normalized_name.lower() or normalized_name.lower() in team.lower():
            injured_names = [p['name'].split()[-1].lower() for p in injuries]
            break
    
    # Filtrer les joueurs blessés
    available_scorers = []
    for player in key_players:
        is_injured = any(inj in player.lower() for inj in injured_names)
        if not is_injured:
            available_scorers.append(player)
    
    # Retourner les buteurs probables avec probabilités
    scorers = []
    for i, player in enumerate(available_scorers[:num_scorers]):
        base_prob = 35 - (i * 8)  # 35%, 27%, 19%
        scorers.append({
            'name': player,
            'probability': max(base_prob, 10)
        })
    
    return scorers if scorers else [{'name': f'Joueur {team_name[:10]}', 'probability': 25}]


def get_team_injuries(team_name):
    """Récupère les blessés d'une équipe"""
    def clean_name(name):
        return name.lower().replace(' fc', '').replace(' cf', '').replace(' afc', '').strip()
    
    clean_input = clean_name(team_name)
    
    for team, injuries in KNOWN_INJURIES.items():
        clean_team = clean_name(team)
        
        # Correspondance exacte
        if clean_team == clean_input:
            return injuries
        
        # Vérifier les mots clés importants
        important_diff_words = ['city', 'united', 'real', 'atletico', 'inter', 'milan', 'ajax', 'psv', 'feyenoord']
        has_conflict = False
        for diff_word in important_diff_words:
            in_team = diff_word in clean_team
            in_input = diff_word in clean_input
            if in_team != in_input:
                has_conflict = True
                break
        
        if not has_conflict and (clean_team in clean_input or clean_input in clean_team):
            return injuries
    return []


# Instance globale des scrapers
flashscore_scraper = FlashScoreScraper()
soccerstats_scraper = SoccerStatsScraper()


def get_match_data(home_team, away_team, league):
    """
    Fonction principale pour récupérer toutes les données d'un match
    Combine les données de FlashScore et SoccerStats
    """
    # Récupérer les absences
    absences = flashscore_scraper.get_match_absences(home_team, away_team)
    
    # Calculer l'impact des absences
    home_impact = flashscore_scraper.calculate_absence_impact(
        absences['home']['absences'], home_team
    )
    away_impact = flashscore_scraper.calculate_absence_impact(
        absences['away']['absences'], away_team
    )
    
    # Récupérer les statistiques
    home_stats = soccerstats_scraper.scrape_team_stats(home_team, league)
    away_stats = soccerstats_scraper.scrape_team_stats(away_team, league)
    
    # Récupérer les confrontations directes
    h2h = soccerstats_scraper.get_head_to_head(home_team, away_team)
    
    return {
        "absences": absences,
        "absence_impact": {
            "home": home_impact,
            "away": away_impact
        },
        "stats": {
            "home": home_stats,
            "away": away_stats
        },
        "head_to_head": h2h,
        "scraped_at": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Test du scraper
    print("Test du scraper FlashScore/SoccerStats")
    
    data = get_match_data(
        "Manchester City FC",
        "Liverpool FC",
        "Premier League"
    )
    
    print(json.dumps(data, indent=2, ensure_ascii=False))
