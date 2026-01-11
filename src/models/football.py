from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class League(db.Model):
    __tablename__ = 'league'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    country = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    season = db.Column(db.String(10), nullable=False)
    
    teams = db.relationship('Team', backref='league', lazy=True)
    matches = db.relationship('Match', backref='league', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "code": self.code,
            "season": self.season
        }

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    country = db.Column(db.String(100), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'), nullable=True)
    logo = db.Column(db.String(500), nullable=True)
    
    home_matches = db.relationship('Match', foreign_keys='Match.home_team_id', backref='home_team', lazy=True)
    away_matches = db.relationship('Match', foreign_keys='Match.away_team_id', backref='away_team', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "logo": self.logo
        }

class Match(db.Model):
    __tablename__ = 'match'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False) # SCHEDULED, FINISHED, TIMED, etc.
    venue = db.Column(db.String(200), nullable=True)
    
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'), nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    
    home_score = db.Column(db.Integer, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    
    # Champs supplémentaires pour le format attendu
    ai_comment = db.Column(db.Text, nullable=True)
    expected_goals = db.Column(db.Float, nullable=True)
    probable_scorers = db.Column(db.Text, nullable=True)  # JSON string
    
    # Probabilités supplémentaires
    prob_over_05 = db.Column(db.Float, nullable=True)
    prob_over_15 = db.Column(db.Float, nullable=True)
    prob_over_35 = db.Column(db.Float, nullable=True)
    prob_over_45 = db.Column(db.Float, nullable=True)
    
    prediction = db.relationship('Prediction', backref='match', uselist=False, lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "status": self.status,
            "venue": self.venue,
            "ai_comment": self.ai_comment,
            "expected_goals": self.expected_goals,
            "probable_scorers": self.probable_scorers,
            "prob_over_05": self.prob_over_05,
            "prob_over_15": self.prob_over_15,
            "prob_over_35": self.prob_over_35,
            "prob_over_45": self.prob_over_45,
            "league": self.league.to_dict() if self.league else None,
            "home_team": self.home_team.to_dict() if self.home_team else None,
            "away_team": self.away_team.to_dict() if self.away_team else None,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "predictions": self.prediction.to_dict() if self.prediction else None
        }

class Prediction(db.Model):
    __tablename__ = 'prediction'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), unique=True, nullable=False)
    
    # Prédictions de base
    predicted_winner = db.Column(db.String(10), nullable=False) # 'home', 'away', 'draw'
    confidence = db.Column(db.String(20), nullable=True) # 'Élevée', 'Moyenne', 'Faible'
    confidence_level = db.Column(db.Float, nullable=True)
    
    # Probabilités détaillées
    prob_home_win = db.Column(db.Float, nullable=True)
    prob_draw = db.Column(db.Float, nullable=True)
    prob_away_win = db.Column(db.Float, nullable=True)
    prob_over_2_5 = db.Column(db.Float, nullable=True)
    prob_both_teams_score = db.Column(db.Float, nullable=True)
    
    # Scores prédits
    predicted_score_home = db.Column(db.Integer, nullable=True)
    predicted_score_away = db.Column(db.Integer, nullable=True)
    
    # Autres métriques
    reliability_score = db.Column(db.Float, nullable=True)
    accuracy_score = db.Column(db.Float, nullable=True)
    analysis_date = db.Column(db.DateTime, nullable=True)
    tactical_analysis = db.Column(db.Text, nullable=True)
    home_tactical_score = db.Column(db.Float, nullable=True)
    away_tactical_score = db.Column(db.Float, nullable=True)
    is_correct_winner = db.Column(db.Boolean, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "match_id": self.match_id,
            "predicted_winner": self.predicted_winner,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "prob_home_win": self.prob_home_win,
            "prob_draw": self.prob_draw,
            "prob_away_win": self.prob_away_win,
            "prob_over_2_5": self.prob_over_2_5,
            "prob_both_teams_score": self.prob_both_teams_score,
            "predicted_score_home": self.predicted_score_home,
            "predicted_score_away": self.predicted_score_away,
            "reliability_score": self.reliability_score,
            "accuracy_score": self.accuracy_score,
            "analysis_date": self.analysis_date.isoformat() if self.analysis_date else None,
            "tactical_analysis": self.tactical_analysis,
            "home_tactical_score": self.home_tactical_score,
            "away_tactical_score": self.away_tactical_score,
            "is_correct_winner": self.is_correct_winner,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
