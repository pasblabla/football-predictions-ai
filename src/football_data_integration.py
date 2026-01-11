from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from src.models.football import db, League, Team, Match, Prediction
from src.data_sources.football_data_org import FootballDataOrgClient
from src.ai_prediction_engine import AIPredictionEngine
import os

football_data_bp = Blueprint("football_data", __name__)

# Initialiser le client API et le moteur d'IA
api_client = FootballDataOrgClient()
ai_engine = AIPredictionEngine()

# Mapping des compétitions football-data.org vers nos codes
COMPETITION_MAPPING = {
    2021: {"code": "PL", "name": "Premier League", "country": "England"},
    2015: {"code": "FL1", "name": "Ligue 1", "country": "France"},
    2002: {"code": "BL1", "name": "Bundesliga", "country": "Germany"},
    2019: {"code": "SA", "name": "Serie A", "country": "Italy"},
    2014: {"code": "PD", "name": "LaLiga", "country": "Spain"},
    2017: {"code": "PPL", "name": "Primeira Liga", "country": "Portugal"},
    2003: {"code": "DED", "name": "Eredivisie", "country": "Netherlands"},
    2001: {"code": "CL", "name": "UEFA Champions League", "country": "Europe"},
    2146: {"code": "EL", "name": "UEFA Europa League", "country": "Europe"},
    2018: {"code": "EC", "name": "European Championship", "country": "Europe"},
}

@football_data_bp.route("/sync-competitions", methods=["POST"])
def sync_competitions():
    """Synchroniser les compétitions depuis football-data.org"""
    try:
        competitions_data = api_client.get_competitions()
        synced_count = 0
        
        for comp in competitions_data.get('competitions', []):
            comp_id = comp['id']
            if comp_id in COMPETITION_MAPPING:
                mapping = COMPETITION_MAPPING[comp_id]
                
                # Vérifier si la ligue existe déjà
                league = League.query.filter_by(code=mapping['code']).first()
                if not league:
                    league = League(
                        name=mapping['name'],
                        country=mapping['country'],
                        code=mapping['code'],
                        season=comp.get('currentSeason', {}).get('startDate', '')[:4] + "-" + 
                               comp.get('currentSeason', {}).get('endDate', '')[:4] if comp.get('currentSeason') else "2024-25",
                        external_id=comp_id
                    )
                    db.session.add(league)
                    synced_count += 1
                else:
                    # Mettre à jour l'external_id si nécessaire
                    if not hasattr(league, 'external_id') or league.external_id is None:
                        league.external_id = comp_id
                        synced_count += 1
        
        db.session.commit()
        return jsonify({
            "message": f"{synced_count} compétitions synchronisées",
            "total_available": len(competitions_data.get('competitions', []))
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@football_data_bp.route("/sync-matches/<int:competition_id>", methods=["POST"])
def sync_matches_for_competition(competition_id):
    """Synchroniser les matchs d'une compétition depuis football-data.org"""
    try:
        # Trouver la ligue correspondante
        league = League.query.filter_by(external_id=competition_id).first()
        if not league:
            return jsonify({"error": "Compétition non trouvée dans la base de données"}), 404
        
        # Récupérer les matchs depuis l'API
        matches_data = api_client.get_matches_for_competition(competition_id)
        synced_count = 0
        
        for match_data in matches_data.get('matches', []):
            # Vérifier si le match existe déjà
            external_match_id = match_data['id']
            existing_match = Match.query.filter_by(external_id=external_match_id).first()
            
            if existing_match:
                # Mettre à jour le statut et les scores si le match existe
                existing_match.status = match_data['status']
                if match_data.get('score', {}).get('fullTime'):
                    existing_match.home_score = match_data['score']['fullTime'].get('home')
                    existing_match.away_score = match_data['score']['fullTime'].get('away')
                synced_count += 1
                continue
            
            # Créer ou récupérer les équipes
            home_team_data = match_data['homeTeam']
            away_team_data = match_data['awayTeam']
            
            home_team = Team.query.filter_by(external_id=home_team_data['id']).first()
            if not home_team:
                home_team = Team(
                    name=home_team_data['name'],
                    country=league.country,
                    external_id=home_team_data['id']
                )
                db.session.add(home_team)
                db.session.flush()
            
            away_team = Team.query.filter_by(external_id=away_team_data['id']).first()
            if not away_team:
                away_team = Team(
                    name=away_team_data['name'],
                    country=league.country,
                    external_id=away_team_data['id']
                )
                db.session.add(away_team)
                db.session.flush()
            
            # Créer le match
            match_date = datetime.fromisoformat(match_data['utcDate'].replace('Z', '+00:00'))
            match = Match(
                date=match_date,
                status=match_data['status'],
                venue=match_data.get('venue', f"{home_team.name} Stadium"),
                league_id=league.id,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                external_id=external_match_id
            )
            
            # Ajouter les scores si disponibles
            if match_data.get('score', {}).get('fullTime'):
                match.home_score = match_data['score']['fullTime'].get('home')
                match.away_score = match_data['score']['fullTime'].get('away')
            
            db.session.add(match)
            db.session.flush()
            
            # Générer une prédiction si le match est à venir
            if match.status in ['SCHEDULED', 'TIMED']:
                prediction = generate_prediction_for_match(match)
                db.session.add(prediction)
            
            synced_count += 1
        
        db.session.commit()
        return jsonify({
            "message": f"{synced_count} matchs synchronisés pour {league.name}",
            "league": league.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@football_data_bp.route("/sync-all-matches", methods=["POST"])
def sync_all_matches():
    """Synchroniser les matchs de toutes les compétitions"""
    try:
        leagues = League.query.filter(League.external_id.isnot(None)).all()
        results = []
        
        for league in leagues:
            try:
                matches_data = api_client.get_matches_for_competition(league.external_id)
                synced_count = 0
                
                for match_data in matches_data.get('matches', []):
                    external_match_id = match_data['id']
                    existing_match = Match.query.filter_by(external_id=external_match_id).first()
                    
                    if existing_match:
                        existing_match.status = match_data['status']
                        if match_data.get('score', {}).get('fullTime'):
                            existing_match.home_score = match_data['score']['fullTime'].get('home')
                            existing_match.away_score = match_data['score']['fullTime'].get('away')
                        synced_count += 1
                        continue
                    
                    # Créer ou récupérer les équipes
                    home_team_data = match_data['homeTeam']
                    away_team_data = match_data['awayTeam']
                    
                    home_team = Team.query.filter_by(external_id=home_team_data['id']).first()
                    if not home_team:
                        home_team = Team(
                            name=home_team_data['name'],
                            country=league.country,
                            external_id=home_team_data['id']
                        )
                        db.session.add(home_team)
                        db.session.flush()
                    
                    away_team = Team.query.filter_by(external_id=away_team_data['id']).first()
                    if not away_team:
                        away_team = Team(
                            name=away_team_data['name'],
                            country=league.country,
                            external_id=away_team_data['id']
                        )
                        db.session.add(away_team)
                        db.session.flush()
                    
                    # Créer le match
                    match_date = datetime.fromisoformat(match_data['utcDate'].replace('Z', '+00:00'))
                    match = Match(
                        date=match_date,
                        status=match_data['status'],
                        venue=match_data.get('venue', f"{home_team.name} Stadium"),
                        league_id=league.id,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        external_id=external_match_id
                    )
                    
                    if match_data.get('score', {}).get('fullTime'):
                        match.home_score = match_data['score']['fullTime'].get('home')
                        match.away_score = match_data['score']['fullTime'].get('away')
                    
                    db.session.add(match)
                    db.session.flush()
                    
                    if match.status in ['SCHEDULED', 'TIMED']:
                        prediction = generate_prediction_for_match(match)
                        db.session.add(prediction)
                    
                    synced_count += 1
                
                results.append({
                    "league": league.name,
                    "synced": synced_count
                })
                
            except Exception as e:
                results.append({
                    "league": league.name,
                    "error": str(e)
                })
        
        db.session.commit()
        return jsonify({
            "message": "Synchronisation terminée",
            "results": results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def generate_prediction_for_match(match):
    """Générer une prédiction pour un match en utilisant le moteur d'IA"""
    home_team_name = match.home_team.name
    away_team_name = match.away_team.name
    league_name = match.league.name
    
    # Utiliser le moteur d'IA pour générer la prédiction
    prediction_data = ai_engine.predict_match(home_team_name, away_team_name, league_name)
    
    prediction = Prediction(
        match_id=match.id,
        predicted_winner=prediction_data['predicted_winner'],
        confidence=prediction_data['confidence'],
        prob_home_win=prediction_data['prob_home_win'],
        prob_draw=prediction_data['prob_draw'],
        prob_away_win=prediction_data['prob_away_win'],
        predicted_score_home=prediction_data['predicted_score_home'],
        predicted_score_away=prediction_data['predicted_score_away'],
        reliability_score=prediction_data['reliability_score']
    )
    
    return prediction

@football_data_bp.route("/status", methods=["GET"])
def get_sync_status():
    """Obtenir le statut de synchronisation"""
    try:
        total_leagues = League.query.count()
        synced_leagues = League.query.filter(League.external_id.isnot(None)).count()
        total_matches = Match.query.count()
        total_teams = Team.query.count()
        
        upcoming_matches = Match.query.filter(
            Match.date >= datetime.now(),
            Match.status.in_(['SCHEDULED', 'TIMED'])
        ).count()
        
        return jsonify({
            "leagues": {
                "total": total_leagues,
                "synced": synced_leagues
            },
            "matches": {
                "total": total_matches,
                "upcoming": upcoming_matches
            },
            "teams": total_teams
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

