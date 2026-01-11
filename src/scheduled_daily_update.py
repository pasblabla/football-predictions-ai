Text file: scheduled_daily_update.py
Latest content with line numbers:
151	        for code, comp_id in COMPETITIONS.items():
152	            try:
153	                league = League.query.filter_by(code=code).first()
154	                if not league:
155	                    continue
156	                
157	                # Récupérer les matchs à venir
158	                from datetime import timedelta
159	                date_from = datetime.now().strftime('%Y-%m-%d')
160	                date_to = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
161	                
162	                matches_url = f"{BASE_URL}/competitions/{comp_id}/matches?dateFrom={date_from}&dateTo={date_to}"
163	                response = requests.get(matches_url, headers=headers)
164	                
165	                if response.status_code == 429:
166	                    time.sleep(70)
167	                    response = requests.get(matches_url, headers=headers)
168	                
169	                if response.status_code != 200:
170	                    continue
171	                
172	                matches_data = response.json()
173	                matches_list = matches_data.get('matches', [])
174	                
175	                for match_data in matches_list:
176	                    external_id = match_data.get('id')
177	                    
178	                    # Vérifier si le match existe déjà
179	                    existing = Match.query.filter_by(external_id=external_id).first()
180	                    if existing:
181	                        continue
182	                    
183	                    # Créer le nouveau match
184	                    home_team_data = match_data.get('homeTeam', {})
185	                    away_team_data = match_data.get('awayTeam', {})
186	                    
187	                    home_team = Team.query.filter_by(external_id=home_team_data.get('id')).first()
188	                    away_team = Team.query.filter_by(external_id=away_team_data.get('id')).first()
189	                    
190	                    if not home_team or not away_team:
191	                        continue
192	                    
193	                    match_date_str = match_data.get('utcDate')
194	                    if match_date_str:
195	                        match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
196	                    else:
197	                        continue
198	                    
199	                    new_match = Match(
200	                        date=match_date,
201	                        status=match_data.get('status', 'SCHEDULED'),
202	                        league_id=league.id,
203	                        home_team_id=home_team.id,
204	                        away_team_id=away_team.id,
205	                        external_id=external_id
206	                    )
207	                    
208	                    db.session.add(new_match)
209	                    db.session.commit()
210	                    
211	                    # Générer une prédiction
212	                    if new_match.status in ['SCHEDULED', 'TIMED']:
213	                        prediction_data = engine.predict_match(
214	                            home_team_id=home_team.external_id,
215	                            away_team_id=away_team.external_id,
216	                            league_id=league.external_id,
217	                            home_team_name=home_team.name,
218	                            away_team_name=away_team.name,
219	                            league_name=league.name
220	                        )
221	                        
222	                        prediction = Prediction(
223	                            match_id=new_match.id,
224	                            predicted_winner=prediction_data['predicted_winner'],
225	                            confidence=prediction_data['confidence'],
226	                            prob_home_win=prediction_data['prob_home_win'],
227	                            prob_draw=prediction_data['prob_draw'],
228	                            prob_away_win=prediction_data['prob_away_win'],
229	                            predicted_score_home=prediction_data['predicted_score_home'],
230	                            predicted_score_away=prediction_data['predicted_score_away'],
231	                            reliability_score=prediction_data['reliability_score'],
232	                            prob_over_2_5=prediction_data['prob_over_2_5'],
233	                            prob_both_teams_score=prediction_data['prob_both_teams_score']
234	                        )
235	                        db.session.add(prediction)
236	                        db.session.commit()
237	                    
238	                    new_matches_count += 1
239	                
240	                time.sleep(7)
241	                
242	            except Exception as e:
243	                print(f"❌ Erreur pour {code}: {str(e)}")
244	                db.session.rollback()
245	                continue
246	    
247	    print(f"✅ {new_matches_count} nouveaux matchs ajoutés")
248	    return new_matches_count
249	
250	def main():