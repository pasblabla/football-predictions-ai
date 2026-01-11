"""
Module d'Auto-Évolution de l'IA
Gère le versioning dynamique et le ré-entraînement automatique du modèle
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class AutoEvolution:
    """Système d'auto-évolution de l'IA avec versioning dynamique"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.base_path = base_path
        self.instance_path = os.path.join(base_path, 'instance')
        self.version_file = os.path.join(self.instance_path, 'ai_version.json')
        self.evolution_log = os.path.join(self.instance_path, 'evolution_log.json')
        self.model_path = os.path.join(self.instance_path, 'xgboost_model.pkl')
        
        # Créer le dossier instance si nécessaire
        os.makedirs(self.instance_path, exist_ok=True)
        
        # Charger ou initialiser la version
        self.version_info = self._load_version_info()
    
    def _load_version_info(self) -> Dict:
        """Charger les informations de version"""
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Version initiale
        return {
            'major': 7,
            'minor': 4,
            'patch': 0,
            'build': 0,
            'last_update': datetime.now().isoformat(),
            'last_training': None,
            'total_training_sessions': 0,
            'total_predictions_analyzed': 0,
            'current_accuracy': 0.44,
            'best_accuracy': 0.44,
            'improvements': []
        }
    
    def _save_version_info(self):
        """Sauvegarder les informations de version"""
        with open(self.version_file, 'w') as f:
            json.dump(self.version_info, f, indent=2, default=str)
    
    def get_version_string(self) -> str:
        """Obtenir la chaîne de version complète"""
        v = self.version_info
        base_version = f"v{v['major']}.{v['minor']}.{v['patch']}"
        
        if v['build'] > 0:
            return f"{base_version}.{v['build']}"
        return base_version
    
    def get_version_info(self) -> Dict:
        """Obtenir toutes les informations de version"""
        return {
            'version': self.get_version_string(),
            'last_update': self.version_info['last_update'],
            'last_training': self.version_info['last_training'],
            'total_training_sessions': self.version_info['total_training_sessions'],
            'current_accuracy': self.version_info['current_accuracy'],
            'best_accuracy': self.version_info['best_accuracy'],
            'is_evolving': True
        }
    
    def increment_version(self, reason: str, accuracy_change: float = 0):
        """Incrémenter la version après une amélioration"""
        self.version_info['build'] += 1
        self.version_info['last_update'] = datetime.now().isoformat()
        
        # Enregistrer l'amélioration
        improvement = {
            'version': self.get_version_string(),
            'date': datetime.now().isoformat(),
            'reason': reason,
            'accuracy_change': accuracy_change
        }
        self.version_info['improvements'].append(improvement)
        
        # Garder seulement les 50 dernières améliorations
        if len(self.version_info['improvements']) > 50:
            self.version_info['improvements'] = self.version_info['improvements'][-50:]
        
        self._save_version_info()
        self._log_evolution(improvement)
        
        return self.get_version_string()
    
    def _log_evolution(self, improvement: Dict):
        """Logger l'évolution dans un fichier séparé"""
        log = []
        if os.path.exists(self.evolution_log):
            try:
                with open(self.evolution_log, 'r') as f:
                    log = json.load(f)
            except:
                pass
        
        log.append(improvement)
        
        # Garder les 100 dernières entrées
        if len(log) > 100:
            log = log[-100:]
        
        with open(self.evolution_log, 'w') as f:
            json.dump(log, f, indent=2)
    
    def update_accuracy(self, new_accuracy: float):
        """Mettre à jour la précision actuelle"""
        old_accuracy = self.version_info['current_accuracy']
        self.version_info['current_accuracy'] = new_accuracy
        
        if new_accuracy > self.version_info['best_accuracy']:
            self.version_info['best_accuracy'] = new_accuracy
        
        accuracy_change = new_accuracy - old_accuracy
        
        # Si amélioration significative (> 1%), incrémenter la version
        if accuracy_change > 0.01:
            self.increment_version(
                f"Amélioration de la précision: {old_accuracy*100:.1f}% → {new_accuracy*100:.1f}%",
                accuracy_change
            )
        else:
            self._save_version_info()
        
        return accuracy_change
    
    def record_training_session(self, predictions_analyzed: int, accuracy: float):
        """Enregistrer une session d'entraînement"""
        self.version_info['total_training_sessions'] += 1
        self.version_info['total_predictions_analyzed'] += predictions_analyzed
        self.version_info['last_training'] = datetime.now().isoformat()
        
        accuracy_change = self.update_accuracy(accuracy)
        
        return {
            'session_number': self.version_info['total_training_sessions'],
            'predictions_analyzed': predictions_analyzed,
            'accuracy': accuracy,
            'accuracy_change': accuracy_change,
            'new_version': self.get_version_string()
        }
    
    def should_retrain(self) -> Tuple[bool, str]:
        """Déterminer si le modèle doit être ré-entraîné"""
        last_training = self.version_info.get('last_training')
        
        if last_training is None:
            return True, "Aucun entraînement précédent"
        
        try:
            last_dt = datetime.fromisoformat(last_training)
            days_since = (datetime.now() - last_dt).days
            
            # Ré-entraîner si plus de 7 jours
            if days_since >= 7:
                return True, f"Dernier entraînement il y a {days_since} jours"
            
            # Ré-entraîner si la précision est faible
            if self.version_info['current_accuracy'] < 0.5:
                return True, f"Précision faible ({self.version_info['current_accuracy']*100:.1f}%)"
            
            return False, f"Prochain entraînement dans {7 - days_since} jours"
        except:
            return True, "Erreur de parsing de la date"


class XGBoostAutoTrainer:
    """Système de ré-entraînement automatique du modèle XGBoost"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.base_path = base_path
        self.instance_path = os.path.join(base_path, 'instance')
        self.model_path = os.path.join(self.instance_path, 'xgboost_evolved_model.pkl')
        self.training_data_path = os.path.join(self.instance_path, 'training_data.json')
        
        os.makedirs(self.instance_path, exist_ok=True)
    
    def collect_training_data(self, db_session) -> List[Dict]:
        """Collecter les données d'entraînement depuis la base de données"""
        from src.models.football import Match, Prediction, Team
        
        training_data = []
        
        # Récupérer les matchs terminés avec prédictions
        matches = Match.query.filter(
            Match.home_score.isnot(None)
        ).order_by(Match.date.desc()).limit(500).all()
        
        for match in matches:
            prediction = Prediction.query.filter_by(match_id=match.id).first()
            
            if not prediction:
                continue
            
            # Déterminer le résultat réel
            if match.home_score > match.away_score:
                actual_result = 0  # Victoire domicile
            elif match.away_score > match.home_score:
                actual_result = 2  # Victoire extérieur
            else:
                actual_result = 1  # Nul
            
            # Créer les features
            features = {
                'prob_home': prediction.prob_home_win or 0.33,
                'prob_draw': prediction.prob_draw or 0.33,
                'prob_away': prediction.prob_away_win or 0.33,
                'confidence': prediction.confidence_level or 0.5,
                'predicted_home_goals': prediction.predicted_score_home or 1,
                'predicted_away_goals': prediction.predicted_score_away or 1,
                'actual_result': actual_result,
                'is_correct': (prediction.predicted_winner == '1' and actual_result == 0) or
                             (prediction.predicted_winner == 'X' and actual_result == 1) or
                             (prediction.predicted_winner == '2' and actual_result == 2)
            }
            
            training_data.append(features)
        
        return training_data
    
    def train_model(self, training_data: List[Dict]) -> Dict:
        """Entraîner le modèle XGBoost avec les nouvelles données"""
        try:
            import xgboost as xgb
            import numpy as np
        except ImportError:
            return {'success': False, 'error': 'XGBoost non installé'}
        
        if len(training_data) < 50:
            return {'success': False, 'error': f'Pas assez de données ({len(training_data)} < 50)'}
        
        # Préparer les features et labels
        X = []
        y = []
        
        for data in training_data:
            features = [
                data['prob_home'],
                data['prob_draw'],
                data['prob_away'],
                data['confidence'],
                data['predicted_home_goals'],
                data['predicted_away_goals'],
                data['prob_home'] - data['prob_away'],  # Différence de probabilité
                abs(data['prob_home'] - data['prob_away']),  # Écart absolu
                data['prob_draw'] / max(data['prob_home'], data['prob_away'], 0.01),  # Ratio nul
            ]
            X.append(features)
            y.append(data['actual_result'])
        
        X = np.array(X)
        y = np.array(y)
        
        # Diviser en train/test
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Entraîner le modèle
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            objective='multi:softprob',
            num_class=3,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
        
        model.fit(X_train, y_train)
        
        # Évaluer
        train_accuracy = model.score(X_train, y_train)
        test_accuracy = model.score(X_test, y_test)
        
        # Sauvegarder le modèle
        with open(self.model_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Sauvegarder les données d'entraînement pour référence
        with open(self.training_data_path, 'w') as f:
            json.dump({
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'train_accuracy': float(train_accuracy),
                'test_accuracy': float(test_accuracy),
                'last_training': datetime.now().isoformat()
            }, f, indent=2)
        
        return {
            'success': True,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'train_accuracy': float(train_accuracy),
            'test_accuracy': float(test_accuracy),
            'model_path': self.model_path
        }
    
    def load_model(self):
        """Charger le modèle entraîné"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        return None
    
    def predict(self, features: List[float]) -> Dict:
        """Faire une prédiction avec le modèle entraîné"""
        model = self.load_model()
        
        if model is None:
            return None
        
        try:
            import numpy as np
            X = np.array([features])
            probs = model.predict_proba(X)[0]
            
            return {
                'home_prob': float(probs[0]),
                'draw_prob': float(probs[1]),
                'away_prob': float(probs[2]),
                'prediction': int(np.argmax(probs))
            }
        except Exception as e:
            return None


def run_auto_evolution(app_context=None):
    """Exécuter l'auto-évolution complète"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'version_update': None,
        'training_result': None,
        'errors': []
    }
    
    try:
        # Initialiser les modules
        evolution = AutoEvolution()
        trainer = XGBoostAutoTrainer()
        
        # Vérifier si on doit ré-entraîner
        should_train, reason = evolution.should_retrain()
        results['should_train'] = should_train
        results['train_reason'] = reason
        
        if should_train and app_context:
            # Collecter les données
            training_data = trainer.collect_training_data(app_context)
            results['training_data_count'] = len(training_data)
            
            if len(training_data) >= 50:
                # Entraîner le modèle
                train_result = trainer.train_model(training_data)
                results['training_result'] = train_result
                
                if train_result['success']:
                    # Enregistrer la session d'entraînement
                    session_result = evolution.record_training_session(
                        len(training_data),
                        train_result['test_accuracy']
                    )
                    results['version_update'] = session_result
        
        results['current_version'] = evolution.get_version_string()
        results['version_info'] = evolution.get_version_info()
        
    except Exception as e:
        results['errors'].append(str(e))
    
    return results


# Fonction pour obtenir la version actuelle (utilisée par l'IA)
def get_current_version() -> str:
    """Obtenir la version actuelle de l'IA"""
    try:
        evolution = AutoEvolution()
        return evolution.get_version_string()
    except:
        return "v7.4.0"
