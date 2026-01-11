        print(f"📊 {self.learning_data['total_analyzed']} matchs analysés")
        print(f"✅ {self.learning_data['correct_predictions']} prédictions correctes")
        print(f"🎯 Précision actuelle: {self.learning_data['accuracy']}%")
        print()
        
        # 2. Identifier les patterns
        print("🔍 Patterns identifiés:")
        print(f"   - Victoires domicile: {self.learning_data['patterns']['home_wins_rate']}%")
        print(f"   - Victoires extérieur: {self.learning_data['patterns']['away_wins_rate']}%")
        print(f"   - Matchs nuls: {self.learning_data['patterns']['draws_rate']}%")
        print(f"   - Erreurs avantage domicile: {self.learning_data['patterns']['home_advantage_errors']}")
        print(f"   - Matchs nuls manqués: {self.learning_data['patterns']['draws_missed']}")
        print()
        
        # 3. Générer les ajustements
        adjustments = self.generate_adjustments()
        if adjustments:
            print(f"⚙️  {len(adjustments)} ajustements suggérés:")
            for adj in adjustments:
                print(f"   - {adj['type']}: {adj['current_value']} → {adj['suggested_value']}")
                print(f"     Raison: {adj['reason']}")
                print(f"     Impact: {adj['impact']}")
            print()
        
        # 4. Générer les recommandations
        recommendations = self.generate_recommendations()
        if recommendations:
            print(f"💡 {len(recommendations)} recommandations:")
            for rec in recommendations:
                print(f"   [{rec['priority']}] {rec['title']}")
                print(f"     {rec['description']}")
                print(f"     Amélioration estimée: {rec['expected_improvement']}")
            print()
        
        # 5. Sauvegarder
        output_file = self.save_learning_data()
        
        print("=" * 80)
        print(f"✅ Analyse terminée ! Objectif: passer de {self.learning_data['accuracy']}% à 70%+")
        print("=" * 80)
        
        return self.learning_data


if __name__ == '__main__':
    with app.app_context():
        engine = AILearningEngine()
        result = engine.run_full_analysis()

