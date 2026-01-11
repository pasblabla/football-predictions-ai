# Observations sur l'historique des matchs

## Date: 24/12/2025

### Constat principal
Les matchs récents (20 décembre) affichent "Non prédit" avec un point d'interrogation orange, ce qui indique que les prédictions n'ont pas été générées avant ces matchs.

### Code couleur observé
- **Orange** (?) : Matchs sans prédiction préalable
- Les matchs avec prédictions correctes (vert) et incorrectes (rouge) devraient apparaître pour les matchs plus anciens

### Statistiques affichées
- Précision actuelle: 44%
- Objectif: 70%
- Matchs analysés: 1056 (30 derniers jours)
- 66/150 prédictions correctes

### Patterns identifiés par l'IA
- 22% victoires à domicile
- 14% victoires à l'extérieur  
- 19% matchs nuls (8 manqués par l'IA)

### Recommandations de l'IA
1. Améliorer la détection des matchs nuls (+4% précision estimée)
2. Intégrer les statistiques de buts marqués/encaissés (+3% précision estimée)

### APScheduler Status
- Running: true
- Jobs configurés:
  - task_6h: cron[hour='6', minute='0'] - Prochaine: 25/12/2025 06:00
  - task_18h: cron[hour='18', minute='0'] - Prochaine: 25/12/2025 18:00
  - task_midnight: cron[hour='0', minute='0'] - Prochaine: 25/12/2025 00:00

### Test d'exécution manuelle
- Tâches exécutées avec succès via /api/scheduler/run-now
- 57 matchs analysés, 57 prédictions mises à jour
- Modèle XGBoost ré-entraîné (précision test: 43.3%)
- Version mise à jour: v7.4.0.1
