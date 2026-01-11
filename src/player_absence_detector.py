        """Récupère l'historique des confrontations directes"""
        try:
            # L'API ne fournit pas directement les H2H
            # On va récupérer les matchs des deux équipes et chercher les confrontations
            url = f"{API_BASE_URL}/teams/{home_team_id}/matches"
            params = {
                'status': 'FINISHED',
                'limit': 50
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                
                # Filtrer les matchs contre l'équipe adverse
                h2h_matches = []
                for match in matches:
                    home_id = match.get('homeTeam', {}).get('id')
                    away_id = match.get('awayTeam', {}).get('id')
                    
                    if (home_id == home_team_id and away_id == away_team_id) or \
                       (home_id == away_team_id and away_id == home_team_id):
                        h2h_matches.append(match)
                    
                    if len(h2h_matches) >= limit:
                        break
                
                return h2h_matches[:limit]
            else:
                print(f"❌ Erreur API H2H: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Erreur get_h2h_history: {e}")
            return []
    
    def analyze_h2h(self, h2h_matches, home_team_id):
        """Analyse l'historique H2H"""
        analysis = {
            'total_matches': len(h2h_matches),
            'home_wins': 0,
            'away_wins': 0,
            'draws': 0,
            'avg_goals_home': 0.0,
            'avg_goals_away': 0.0,
            'trend': 'neutral'
        }
        
        if not h2h_matches:
            return analysis
        
        try:
            total_goals_home = 0
            total_goals_away = 0
            
            for match in h2h_matches:
                home_id = match.get('homeTeam', {}).get('id')
                score = match.get('score', {}).get('fullTime', {})
                home_score = score.get('home', 0)
                away_score = score.get('away', 0)
                
                # Déterminer qui est qui
                if home_id == home_team_id:
                    total_goals_home += home_score
                    total_goals_away += away_score
                    
                    if home_score > away_score:
                        analysis['home_wins'] += 1
                    elif away_score > home_score:
                        analysis['away_wins'] += 1
                    else:
                        analysis['draws'] += 1
                else:
                    total_goals_home += away_score
                    total_goals_away += home_score
                    
                    if away_score > home_score:
                        analysis['home_wins'] += 1