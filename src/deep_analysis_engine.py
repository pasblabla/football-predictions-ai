            # Calculer les moyennes
            stats["avg_goals_scored"] = round(stats["goals_scored"] / stats["total_matches"], 2)
            stats["avg_goals_conceded"] = round(stats["goals_conceded"] / stats["total_matches"], 2)
            stats["clean_sheet_rate"] = round((stats["clean_sheets"] / stats["total_matches"]) * 100, 1)
            
            # Formation la plus utilisée
            if stats["formations"]:
                stats["main_formation"] = max(stats["formations"], key=stats["formations"].get)
            else:
                stats["main_formation"] = "Unknown"
            
            return stats
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des stats pour {team_id}: {e}")
            return None
    
    def calculate_realistic_expected_goals(self, home_stats, away_stats):
        """Calcule les buts attendus de manière réaliste"""
        
        # Méthode 1: Moyenne offensive vs défensive
        home_expected = (home_stats["avg_goals_scored"] + away_stats["avg_goals_conceded"]) / 2
        away_expected = (away_stats["avg_goals_scored"] + home_stats["avg_goals_conceded"]) / 2
        
        # Ajustement selon les clean sheets (équipes défensives)
        if home_stats["clean_sheet_rate"] > 40:  # Équipe très défensive
            away_expected *= 0.7
        if away_stats["clean_sheet_rate"] > 40:
            home_expected *= 0.7
        
        # Ajustement selon la forme récente
        home_form = (home_stats["wins"] * 3 + home_stats["draws"]) / (home_stats["total_matches"] * 3)
        away_form = (away_stats["wins"] * 3 + away_stats["draws"]) / (away_stats["total_matches"] * 3)
        
        if home_form > 0.6:  # Bonne forme
            home_expected *= 1.1
        elif home_form < 0.3:  # Mauvaise forme
            home_expected *= 0.9
        
        if away_form > 0.6:
            away_expected *= 1.1
        elif away_form < 0.3:
            away_expected *= 0.9
        
        total_expected = round(home_expected + away_expected, 1)
        
        return {
            "total": total_expected,
            "home": round(home_expected, 1),
            "away": round(away_expected, 1)
        }
    
    def generate_ai_comment(self, home_team_name, away_team_name, home_stats, away_stats, expected_goals):
        """Génère un commentaire IA basé sur les vraies statistiques"""
        
        comments = []
        
        # Analyser la forme
        home_form = (home_stats["wins"] * 3 + home_stats["draws"]) / (home_stats["total_matches"] * 3)
        away_form = (away_stats["wins"] * 3 + away_stats["draws"]) / (away_stats["total_matches"] * 3)
        
        if home_form > 0.6:
            comments.append(f"{home_team_name} est en excellente forme ({home_stats['wins']}V {home_stats['draws']}N {home_stats['losses']}D)")
        elif home_form < 0.3:
            comments.append(f"{home_team_name} traverse une mauvaise passe ({home_stats['wins']}V {home_stats['draws']}N {home_stats['losses']}D)")
        
        if away_form > 0.6:
            comments.append(f"{away_team_name} est également en forme ({away_stats['wins']}V {away_stats['draws']}N {away_stats['losses']}D)")
        elif away_form < 0.3:
            comments.append(f"{away_team_name} est en difficulté ({away_stats['wins']}V {away_stats['draws']}N {away_stats['losses']}D)")
        
        # Analyser la défense
        if home_stats["clean_sheet_rate"] > 40:
            comments.append(f"{home_team_name} a une défense solide ({home_stats['clean_sheet_rate']}% clean sheets)")
        if away_stats["clean_sheet_rate"] > 40:
            comments.append(f"{away_team_name} encaisse peu de buts ({away_stats['clean_sheet_rate']}% clean sheets)")
        
        # Analyser l'attaque
        if home_stats["avg_goals_scored"] > 2:
            comments.append(f"{home_team_name} marque beaucoup ({home_stats['avg_goals_scored']} buts/match)")
        elif home_stats["avg_goals_scored"] < 1:
            comments.append(f"{home_team_name} peine à marquer ({home_stats['avg_goals_scored']} buts/match)")
        
        if away_stats["avg_goals_scored"] > 2:
            comments.append(f"{away_team_name} est prolifique ({away_stats['avg_goals_scored']} buts/match)")
        elif away_stats["avg_goals_scored"] < 1:
            comments.append(f"{away_team_name} manque d'efficacité offensive ({away_stats['avg_goals_scored']} buts/match)")
        
        # Prédiction de buts
        if expected_goals["total"] < 2:
            comments.append(f"Match défensif attendu ({expected_goals['total']} buts prévus)")
        elif expected_goals["total"] > 3:
            comments.append(f"Match offensif en perspective ({expected_goals['total']} buts prévus)")
        else:
            comments.append(f"Match équilibré avec environ {expected_goals['total']} buts prévus")
        
        return ". ".join(comments) + "."
    
    def analyze_match(self, match_id):
        """Analyse approfondie d'un match"""