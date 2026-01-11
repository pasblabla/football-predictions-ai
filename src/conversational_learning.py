"""
Système d'apprentissage conversationnel
Analyse les conversations avec les utilisateurs pour enrichir les prédictions
"""
import sqlite3
import re
from datetime import datetime, timedelta
import json

class ConversationalLearning:
    """Apprend des conversations avec les utilisateurs"""
    
    def __init__(self, db_path='/home/ubuntu/football-api-deploy/server/database/app.db'):
        self.db_path = db_path
    
    def save_conversation(self, user_message, ai_response):
        """Enregistre une conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Analyser le sentiment du message
        sentiment = self._analyze_sentiment(user_message)
        
        cursor.execute("""
            INSERT INTO chat_conversations (user_message, ai_response, sentiment)
            VALUES (?, ?, ?)
        """, (user_message, ai_response, sentiment))
        
        conversation_id = cursor.lastrowid
        
        # Extraire les informations pertinentes
        self._extract_feedback(conversation_id, user_message)
        
        conn.commit()
        conn.close()
        
        return conversation_id
    
    def _analyze_sentiment(self, message):
        """Analyse le sentiment du message (positif/négatif/neutre)"""
        message_lower = message.lower()
        
        positive_words = ['merci', 'super', 'excellent', 'génial', 'parfait', 'bravo', 
                         'bon', 'bien', 'correct', 'juste', 'précis', 'top']
        negative_words = ['faux', 'erreur', 'mauvais', 'nul', 'raté', 'perdu', 
                         'incorrect', 'pas bon', 'décevant', 'mauvaise']
        
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_feedback(self, conversation_id, message):
        """Extrait les feedbacks sur les prédictions depuis le message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        message_lower = message.lower()
        
        # Détecter les mentions d'erreurs de prédiction
        if any(word in message_lower for word in ['faux', 'erreur', 'mauvais', 'raté', 'perdu']):
            # Essayer d'extraire le nom de l'équipe
            teams = self._extract_team_names(message)
            
            for team in teams:
                cursor.execute("""
                    INSERT INTO user_feedback 
                    (conversation_id, feedback_type, feedback_text, team_mentioned)
                    VALUES (?, ?, ?, ?)
                """, (conversation_id, 'prediction_error', message, team))
        
        # Détecter les suggestions d'amélioration
        if any(word in message_lower for word in ['devrait', 'faudrait', 'suggère', 'conseil']):
            cursor.execute("""
                INSERT INTO user_feedback 
                (conversation_id, feedback_type, feedback_text)
                VALUES (?, ?, ?)
            """, (conversation_id, 'suggestion', message))
        
        conn.commit()
        conn.close()
    
    def _extract_team_names(self, message):
        """Extrait les noms d'équipes mentionnés dans le message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Récupérer toutes les équipes
        cursor.execute("SELECT name FROM team")
        all_teams = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Chercher les équipes mentionnées
        mentioned_teams = []
        message_lower = message.lower()
        
        for team in all_teams:
            if team.lower() in message_lower:
                mentioned_teams.append(team)
        
        return mentioned_teams
    
    def analyze_feedback_patterns(self):
        """Analyse les patterns dans les feedbacks des utilisateurs"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Analyser les erreurs de prédiction mentionnées
        cursor.execute("""
            SELECT 
                team_mentioned,
                COUNT(*) as error_count,
                GROUP_CONCAT(feedback_text, ' | ') as all_feedback
            FROM user_feedback
            WHERE feedback_type = 'prediction_error'
            AND team_mentioned IS NOT NULL
            GROUP BY team_mentioned
            ORDER BY error_count DESC
            LIMIT 10
        """)
        
        error_patterns = [dict(row) for row in cursor.fetchall()]
        
        # Analyser le sentiment général
        cursor.execute("""
            SELECT 
                sentiment,
                COUNT(*) as count
            FROM chat_conversations
            WHERE created_at > datetime('now', '-7 days')
            GROUP BY sentiment
        """)
        
        sentiment_stats = {row['sentiment']: row['count'] for row in cursor.fetchall()}
        
        # Suggestions des utilisateurs
        cursor.execute("""
            SELECT feedback_text
            FROM user_feedback
            WHERE feedback_type = 'suggestion'
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        suggestions = [row['feedback_text'] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'error_patterns': error_patterns,
            'sentiment_stats': sentiment_stats,
            'suggestions': suggestions,
            'total_conversations': sum(sentiment_stats.values())
        }
    
    def get_insights_for_team(self, team_name):
        """Récupère les insights des utilisateurs pour une équipe spécifique"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                feedback_type,
                feedback_text,
                created_at
            FROM user_feedback
            WHERE team_mentioned = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (team_name,))
        
        insights = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return insights
    
    def generate_learning_report(self):
        """Génère un rapport d'apprentissage basé sur les conversations"""
        patterns = self.analyze_feedback_patterns()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_conversations': patterns['total_conversations'],
            'sentiment_distribution': patterns['sentiment_stats'],
            'teams_with_most_errors': patterns['error_patterns'][:5],
            'recent_suggestions': patterns['suggestions'][:10],
            'recommendations': []
        }
        
        # Générer des recommandations
        if patterns['error_patterns']:
            for error in patterns['error_patterns'][:3]:
                report['recommendations'].append({
                    'type': 'adjust_coefficients',
                    'team': error['team_mentioned'],
                    'reason': f"Erreurs de prédiction mentionnées {error['error_count']} fois",
                    'action': f"Réduire la confiance des prédictions pour {error['team_mentioned']}"
                })
        
        negative_ratio = patterns['sentiment_stats'].get('negative', 0) / max(patterns['total_conversations'], 1)
        if negative_ratio > 0.3:
            report['recommendations'].append({
                'type': 'improve_accuracy',
                'reason': f"Sentiment négatif élevé ({negative_ratio*100:.1f}%)",
                'action': "Réviser l'algorithme de prédiction global"
            })
        
        return report


# Test du système
if __name__ == "__main__":
    learning = ConversationalLearning()
    
    # Test: Enregistrer une conversation
    print("📝 Test d'enregistrement de conversation...")
    conv_id = learning.save_conversation(
        "Votre prédiction sur PSG était fausse, ils ont perdu",
        "Je suis désolé que la prédiction n'ait pas été correcte. Je vais analyser ce match pour améliorer mes futures prédictions."
    )
    print(f"✅ Conversation enregistrée (ID: {conv_id})")
    
    # Analyser les patterns
    print("\n📊 Analyse des patterns...")
    patterns = learning.analyze_feedback_patterns()
    print(f"Total conversations: {patterns['total_conversations']}")
    print(f"Sentiment: {patterns['sentiment_stats']}")
    print(f"Erreurs détectées: {len(patterns['error_patterns'])}")
    
    # Générer un rapport
    print("\n📈 Génération du rapport d'apprentissage...")
    report = learning.generate_learning_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))

