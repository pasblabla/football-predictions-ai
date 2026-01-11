
import os
import requests

class FootballDataOrgClient:
    def __init__(self):
        self.api_key = os.getenv("FOOTBALL_DATA_API_KEY")
        self.base_url = "https://api.football-data.org/v4/"
        self.headers = {"X-Auth-Token": self.api_key}

    def _make_request(self, endpoint):
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_competitions(self):
        return self._make_request("competitions")

    def get_matches_for_competition(self, competition_id):
        return self._make_request(f"competitions/{competition_id}/matches")

    def get_teams_for_competition(self, competition_id):
        return self._make_request(f"competitions/{competition_id}/teams")

    def get_match_details(self, match_id):
        return self._make_request(f"matches/{match_id}")

    def get_players_for_team(self, team_id):
        # football-data.org doesn't directly provide player probabilities for scoring
        # This would require custom logic or another API
        return []



