# Analyse de SoccerStats.com

## Données Disponibles

### Statistiques par Ligue (Premier League exemple)
- **170 matchs joués / 380** total
- **2.83 buts par match** en moyenne

### Statistiques par Équipe
| Équipe | GP | W | D | L | GF | GA | GD | Pts | PPG | CS | SR |
|--------|----|----|----|----|----|----|-----|-----|-----|----|----|
| Arsenal | 17 | 12 | 3 | 2 | 31 | 10 | +21 | 39 | 2.29 | 53% | 94% |
| Manchester City | 17 | 12 | 1 | 4 | 41 | 16 | +25 | 37 | 2.18 | 47% | 88% |
| Aston Villa | 17 | 11 | 3 | 3 | 27 | 18 | +9 | 36 | 2.12 | 29% | 71% |

### Statistiques Pré-Match (Home/Away)
Exemple pour Manchester Utd vs Newcastle Utd (26 Dec):
- **Man Utd (Home)**: 58% PPG, 2.00 GF, 1.50 GA, 3.50 TG, 50% Over 2.5
- **Newcastle (Away)**: 25% PPG, 0.88 GF, 1.25 GA, 2.13 TG, 50% Over 2.5

### Données Utiles pour les Prédictions
1. **PPG (Points Per Game)** - Performance globale
2. **CS (Clean Sheets)** - Solidité défensive
3. **SR (Scoring Rate)** - Capacité offensive
4. **Over 2.5%** - Tendance aux matchs à buts
5. **Forme récente (Last 4/8 matchs)**
6. **Stats Home vs Away** - Différence de performance

### Onglets Disponibles
- LATEST - Dernières stats
- MATCHES - Calendrier
- FORM - Forme récente
- H2H - Confrontations directes
- GOALS - Statistiques de buts
- HALF-TIME - Stats mi-temps
- TIMING - Timing des buts
- FIRST GOAL - Premier but

## Structure URL
- Ligue: `https://www.soccerstats.com/latest.asp?league=england`
- Équipe: `https://www.soccerstats.com/team.asp?league=england&team=Arsenal`
- H2H: `https://www.soccerstats.com/head2head.asp?league=england`

## Scraping Possible
Le site est accessible sans authentification et contient des données très riches.
