"""
Routes pour l'apprentissage automatique et l'analyse pré-match
"""

from flask import Blueprint, jsonify
import sys
import os

# Ajouter le chemin parent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les scripts d'apprentissage
from scripts.continuous_learning import ContinuousLearning
from scripts.pre_match_analysis import PreMatchAnalyzer

learning_bp = Blueprint('learning', __name__)

@learning_bp.route('/run-learning', methods=['POST'])
def run_learning():
    """Exécute un cycle d'apprentissage automatique"""
    try:
        learner = ContinuousLearning()
        learner.run_learning_cycle(days_back=1)
        learner.close()
        
        return jsonify({
            'success': True,
            'message': 'Apprentissage automatique exécuté avec succès'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@learning_bp.route('/run-prematch', methods=['POST'])
def run_prematch():
    """Exécute l'analyse pré-match"""
    try:
        analyzer = PreMatchAnalyzer()
        analyzer.run_analysis()
        analyzer.close()
        
        return jsonify({
            'success': True,
            'message': 'Analyse pré-match exécutée avec succès'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@learning_bp.route('/coefficients', methods=['GET'])
def get_coefficients():
    """Récupère les coefficients d'apprentissage actuels"""
    try:
        learner = ContinuousLearning()
        coefficients = learner.coefficients
        learner.close()
        
        return jsonify({
            'success': True,
            'coefficients': coefficients
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

