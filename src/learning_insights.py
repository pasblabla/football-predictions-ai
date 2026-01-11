"""
Routes API pour les insights d'apprentissage conversationnel
"""
from flask import Blueprint, jsonify
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from conversational_learning import ConversationalLearning

learning_insights_bp = Blueprint('learning_insights', __name__)

@learning_insights_bp.route('/api/learning/insights', methods=['GET'])
def get_learning_insights():
    """Récupère les insights d'apprentissage"""
    try:
        learning = ConversationalLearning()
        report = learning.generate_learning_report()
        
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@learning_insights_bp.route('/api/learning/feedback-patterns', methods=['GET'])
def get_feedback_patterns():
    """Récupère les patterns de feedback"""
    try:
        learning = ConversationalLearning()
        patterns = learning.analyze_feedback_patterns()
        
        return jsonify(patterns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@learning_insights_bp.route('/api/learning/team-insights/<team_name>', methods=['GET'])
def get_team_insights(team_name):
    """Récupère les insights pour une équipe spécifique"""
    try:
        learning = ConversationalLearning()
        insights = learning.get_insights_for_team(team_name)
        
        return jsonify({
            'team': team_name,
            'insights': insights
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

