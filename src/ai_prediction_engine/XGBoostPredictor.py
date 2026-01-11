"""
Module de Prédiction XGBoost v1.0
- Utilise XGBoost pour améliorer les prédictions
- Entraîné sur les données historiques
- Optimisé pour la détection des matchs nuls
"""

import numpy as np
import json
import os
import hashlib
import random
from datetime import datetime

try:
    import xgboost as xgb
    from sklearn.preprocessing import StandardScaler
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

class XGBoostPredictor:
    """Prédicteur XGBoost pour le football"""
    
    def __init__(self):
        self.model_dir = "/home/ubuntu/football_app/instance/models"
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.model = None
        self.scaler = None
        self.is_trained = False
        
        # Charger le modèle s'il existe
        self._load_model()
        
        # Si pas de modèle, créer un modèle de base
        if not self.is_trained and XGBOOST_AVAILABLE:
            self._create_base_model()
    
    def _load_model(self):
        """Charger le modèle XGBoost sauvegardé"""
        model_path = os.path.join(self.model_dir, "xgboost_model.ubj")
        if os.path.exists(model_path) and XGBOOST_AVAILABLE:
            try:
                booster = xgb.Booster()
                booster.load_model(model_path)
                self.model = xgb.XGBClassifier()
                self.model._Booster = booster
                self.is_trained = True
            except:
                pass
    
    def _save_model(self):
        """Sauvegarder le modèle XGBoost"""
        if self.model and XGBOOST_AVAILABLE:
            model_path = os.path.join(self.model_dir, "xgboost_model.ubj")
            try:
                # Utiliser le booster interne pour sauvegarder
                self.model.get_booster().save_model(model_path)
            except:
                pass
    
    def _create_base_model(self):
        """Créer un modèle de base avec des données synthétiques"""
        if not XGBOOST_AVAILABLE:
            return
        
        # Générer des données d'entraînement synthétiques basées sur des patterns réalistes
        np.random.seed(42)
        n_samples = 1000
        
        # Features: [home_strength, away_strength, home_form, away_form, xg_home, xg_away, 
        #            strength_diff, form_diff, xg_diff, is_derby, league_draw_rate]
        X = []
        y = []
        
        for _ in range(n_samples):
            home_strength = np.random.uniform(0.4, 0.95)
            away_strength = np.random.uniform(0.4, 0.95)
            home_form = np.random.uniform(0.2, 0.9)
            away_form = np.random.uniform(0.2, 0.9)
            xg_home = np.random.uniform(0.8, 2.5)
            xg_away = np.random.uniform(0.6, 2.2)
            strength_diff = home_strength - away_strength
            form_diff = home_form - away_form
            xg_diff = xg_home - xg_away
            is_derby = np.random.choice([0, 1], p=[0.9, 0.1])
            league_draw_rate = np.random.uniform(0.22, 0.30)
            
            features = [home_strength, away_strength, home_form, away_form, 
                       xg_home, xg_away, strength_diff, form_diff, xg_diff,
                       is_derby, league_draw_rate]
            X.append(features)
            
            # Déterminer le résultat basé sur les features
            # 0 = HOME, 1 = DRAW, 2 = AWAY
            
            # Probabilité de base
            home_prob = 0.45 + strength_diff * 0.3 + form_diff * 0.1 + xg_diff * 0.15
            away_prob = 0.30 - strength_diff * 0.3 - form_diff * 0.1 - xg_diff * 0.15
            draw_prob = 0.25
            
            # Ajuster pour les matchs équilibrés
            if abs(strength_diff) < 0.1:
                draw_prob += 0.10
                home_prob -= 0.05
                away_prob -= 0.05
            
            # Ajuster pour les derbys
            if is_derby:
                draw_prob += 0.08
                home_prob -= 0.04
                away_prob -= 0.04
            
            # Ajuster selon le taux de nuls de la ligue
            draw_prob += (league_draw_rate - 0.25) * 0.5
            
            # S'assurer que les probabilités sont positives
            home_prob = max(0.05, home_prob)
            draw_prob = max(0.05, draw_prob)
            away_prob = max(0.05, away_prob)
            
            # Normaliser
            total = home_prob + draw_prob + away_prob
            home_prob /= total
            draw_prob /= total
            away_prob /= total
            
            # Choisir le résultat
            result = np.random.choice([0, 1, 2], p=[home_prob, draw_prob, away_prob])
            y.append(result)
        
        X = np.array(X)
        y = np.array(y)
        
        # Créer et entraîner le modèle
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            objective='multi:softprob',
            num_class=3,
            use_label_encoder=False,
            eval_metric='mlogloss',
            random_state=42
        )
        
        self.model.fit(X, y)
        self.is_trained = True
        self._save_model()
    
    def extract_features(self, home_team, away_team, home_strength, away_strength,
                        home_form_score, away_form_score, xg_home, xg_away, 
                        league_draw_rate=0.25):
        """Extraire les features pour la prédiction"""
        strength_diff = home_strength - away_strength
        form_diff = home_form_score - away_form_score
        xg_diff = xg_home - xg_away
        
        # Détecter si c'est un derby (équipes de la même ville)
        is_derby = 0
        derby_cities = ['Manchester', 'London', 'Milan', 'Madrid', 'Rome', 'Liverpool', 'Glasgow']
        for city in derby_cities:
            if city.lower() in home_team.lower() and city.lower() in away_team.lower():
                is_derby = 1
                break
        
        features = [
            home_strength, away_strength, home_form_score, away_form_score,
            xg_home, xg_away, strength_diff, form_diff, xg_diff,
            is_derby, league_draw_rate
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict(self, home_team, away_team, home_strength, away_strength,
               home_form_score, away_form_score, xg_home, xg_away,
               league_draw_rate=0.25):
        """
        Prédire le résultat d'un match
        
        Retourne:
        - prediction: '1' (home), 'X' (draw), '2' (away)
        - probabilities: dict avec les probabilités pour chaque résultat
        """
        if not self.is_trained or not XGBOOST_AVAILABLE:
            # Fallback si XGBoost n'est pas disponible
            return self._fallback_predict(home_strength, away_strength, 
                                         home_form_score, away_form_score,
                                         xg_home, xg_away)
        
        features = self.extract_features(
            home_team, away_team, home_strength, away_strength,
            home_form_score, away_form_score, xg_home, xg_away,
            league_draw_rate
        )
        
        try:
            # Utiliser le booster directement pour la prédiction
            dmatrix = xgb.DMatrix(features)
            proba = self.model.get_booster().predict(dmatrix)[0]
            
            # Si c'est un tableau 1D (une seule prédiction), le convertir
            if len(proba.shape) == 0 or (len(proba.shape) == 1 and proba.shape[0] == 3):
                if len(proba.shape) == 0:
                    # Prédiction unique, utiliser fallback
                    return self._fallback_predict(home_strength, away_strength, 
                                                 home_form_score, away_form_score,
                                                 xg_home, xg_away)
            
            # proba[0] = HOME, proba[1] = DRAW, proba[2] = AWAY
            home_prob = round(float(proba[0]) * 100, 1)
            draw_prob = round(float(proba[1]) * 100, 1)
            away_prob = round(float(proba[2]) * 100, 1)
            
            # Déterminer la prédiction
            max_idx = np.argmax(proba)
            if max_idx == 0:
                prediction = '1'
            elif max_idx == 1:
                prediction = 'X'
            else:
                prediction = '2'
            
            return {
                'prediction': prediction,
                'home_prob': home_prob,
                'draw_prob': draw_prob,
                'away_prob': away_prob,
                'confidence': round(max(proba) * 100, 1),
                'model': 'XGBoost'
            }
        except Exception as e:
            # En cas d'erreur, utiliser le fallback
            return self._fallback_predict(home_strength, away_strength, 
                                         home_form_score, away_form_score,
                                         xg_home, xg_away)
    
    def _fallback_predict(self, home_strength, away_strength, 
                         home_form_score, away_form_score,
                         xg_home, xg_away):
        """Prédiction de secours si XGBoost n'est pas disponible"""
        strength_diff = home_strength - away_strength
        form_diff = home_form_score - away_form_score
        xg_diff = xg_home - xg_away
        
        # Calcul simple des probabilités
        home_prob = 45 + strength_diff * 30 + form_diff * 10 + xg_diff * 15
        away_prob = 30 - strength_diff * 30 - form_diff * 10 - xg_diff * 15
        draw_prob = 25
        
        # Ajuster pour les matchs équilibrés
        if abs(strength_diff) < 0.1:
            draw_prob += 10
            home_prob -= 5
            away_prob -= 5
        
        # Normaliser
        total = home_prob + draw_prob + away_prob
        home_prob = round(home_prob / total * 100, 1)
        draw_prob = round(draw_prob / total * 100, 1)
        away_prob = round(100 - home_prob - draw_prob, 1)
        
        # Déterminer la prédiction
        if home_prob > away_prob and home_prob > draw_prob:
            prediction = '1'
        elif away_prob > home_prob and away_prob > draw_prob:
            prediction = '2'
        else:
            prediction = 'X'
        
        return {
            'prediction': prediction,
            'home_prob': home_prob,
            'draw_prob': draw_prob,
            'away_prob': away_prob,
            'confidence': max(home_prob, draw_prob, away_prob),
            'model': 'Fallback'
        }
    
    def train_on_historical_data(self, matches_data):
        """
        Entraîner le modèle sur des données historiques
        
        matches_data: liste de dicts avec:
        - home_team, away_team
        - home_strength, away_strength
        - home_form_score, away_form_score
        - xg_home, xg_away
        - result: 'HOME', 'DRAW', 'AWAY'
        """
        if not XGBOOST_AVAILABLE:
            return False
        
        X = []
        y = []
        
        for match in matches_data:
            features = self.extract_features(
                match['home_team'], match['away_team'],
                match['home_strength'], match['away_strength'],
                match['home_form_score'], match['away_form_score'],
                match['xg_home'], match['xg_away'],
                match.get('league_draw_rate', 0.25)
            )
            X.append(features[0])
            
            result_map = {'HOME': 0, 'DRAW': 1, 'AWAY': 2}
            y.append(result_map[match['result']])
        
        X = np.array(X)
        y = np.array(y)
        
        # Ré-entraîner le modèle
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            objective='multi:softprob',
            num_class=3,
            use_label_encoder=False,
            eval_metric='mlogloss',
            random_state=42
        )
        
        self.model.fit(X, y)
        self.is_trained = True
        self._save_model()
        
        return True


# Instance globale
xgboost_predictor = XGBoostPredictor()
