/**
 * Crée une carte de match avec prédiction hybride (Agent IA Avancé v6.0)
 * Affiche le meilleur pari recommandé (1X2, BTTS, Over/Under)
 * Inclut bouton H2H et statistiques des arbitres
 */
function createHybridMatchCard(item, number) {
    const div = document.createElement('div');
    div.className = 'match-card p-4';

    const match = item.match;
    const pred = item.prediction;
    
    const date = new Date(match.date);
    const dateStr = date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
    const timeStr = date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

    const prob1 = pred.win_probability_home;
    const probX = pred.draw_probability;
    const prob2 = pred.win_probability_away;
    
    let pronoChoice = 'X';
    let maxProb = probX;
    
    if (prob1 > maxProb) {
        pronoChoice = '1';
        maxProb = prob1;
    }
    if (prob2 > maxProb) {
        pronoChoice = '2';
        maxProb = prob2;
    }

    // Récupérer le meilleur pari recommandé
    const bestBet = pred.best_bet || { type: pronoChoice, confidence: maxProb, description: 'Prédiction standard' };
    
    // Couleur du badge selon le meilleur pari
    let bestBetColor = 'gray';
    let bestBetBg = 'bg-gray-100';
    let bestBetText = 'text-gray-800';
    if (bestBet.type === '1' || bestBet.type === '2') {
        bestBetColor = 'green';
        bestBetBg = 'bg-green-100';
        bestBetText = 'text-green-800';
    } else if (bestBet.type === 'X') {
        bestBetColor = 'yellow';
        bestBetBg = 'bg-yellow-100';
        bestBetText = 'text-yellow-800';
    } else if (bestBet.type === 'BTTS') {
        bestBetColor = 'purple';
        bestBetBg = 'bg-purple-100';
        bestBetText = 'text-purple-800';
    } else if (bestBet.type && bestBet.type.includes('Over')) {
        bestBetColor = 'blue';
        bestBetBg = 'bg-blue-100';
        bestBetText = 'text-blue-800';
    } else if (bestBet.type === '1X' || bestBet.type === 'X2') {
        bestBetColor = 'teal';
        bestBetBg = 'bg-teal-100';
        bestBetText = 'text-teal-800';
    }

    // Badge de confiance avec couleur
    let confidenceBadge = '';
    if (pred.confidence === 'Très Élevée') {
        confidenceBadge = '<span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">🎯 Très Élevée</span>';
    } else if (pred.confidence === 'Élevée') {
        confidenceBadge = '<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">✅ Élevée</span>';
    } else if (pred.confidence === 'Moyenne') {
        confidenceBadge = '<span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-semibold">⚖️ Moyenne</span>';
    } else {
        confidenceBadge = '<span class="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-semibold">⚠️ Faible</span>';
    }
    
    // Récupérer les absences
    const absenceImpact = pred.absence_impact || { home_absences: [], away_absences: [] };
    const homeAbsences = absenceImpact.home_absences || [];
    const awayAbsences = absenceImpact.away_absences || [];
    const hasAbsences = homeAbsences.length > 0 || awayAbsences.length > 0;

    // ID unique pour le modal H2H
    const h2hModalId = `h2h-modal-${match.id || Math.random().toString(36).substr(2, 9)}`;

    div.innerHTML = `
        <div class="match-number">${number}</div>
        <div class="mb-3 flex items-center justify-between">
            <span class="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-semibold">
                ${match.league}
            </span>
            <span class="text-sm text-gray-600">${dateStr} - ${timeStr}</span>
        </div>
        <div class="flex items-center justify-between mb-4">
            <div class="flex-1 text-center">
                <div class="text-xl font-bold text-gray-800">${match.home_team}</div>
            </div>
            <div class="px-4">
                <div class="prono-badge">
                    <div class="prono-choice">${pronoChoice}</div>
                    <div class="prono-prob">${maxProb}%</div>
                </div>
            </div>
            <div class="flex-1 text-center">
                <div class="text-xl font-bold text-gray-800">${match.away_team}</div>
            </div>
        </div>
        
        <!-- MEILLEUR PARI RECOMMANDÉ - TRÈS VISIBLE -->
        <div class="mb-4 p-4 ${bestBetBg} border-2 border-${bestBetColor}-400 rounded-xl shadow-lg">
            <div class="text-xs ${bestBetText} font-bold mb-2">🎯 MEILLEUR PARI RECOMMANDÉ:</div>
            <div class="flex items-center justify-between">
                <div>
                    <span class="text-2xl font-black ${bestBetText}">${bestBet.type}</span>
                    <span class="text-sm text-gray-600 ml-2">${bestBet.description}</span>
                </div>
                <div class="px-4 py-2 bg-${bestBetColor}-500 text-white rounded-full font-bold text-lg">
                    ${bestBet.confidence}%
                </div>
            </div>
        </div>
        
        <!-- Score prédit et buts attendus -->
        <div class="mb-4 text-center">
            <div class="inline-block px-6 py-3 bg-gradient-to-r from-purple-100 to-pink-100 border-3 border-purple-400 rounded-xl shadow-lg">
                <div class="text-xs text-purple-600 font-semibold mb-1">SCORE PRÉDIT</div>
                <div class="text-3xl font-black text-purple-900 mb-1">${pred.predicted_score}</div>
                <div class="text-sm font-bold text-pink-700">⚽ ${pred.expected_goals} buts attendus</div>
            </div>
        </div>
        
        <div class="grid grid-cols-3 gap-3 mb-3">
            <div class="proba-box ${prob1 === maxProb ? 'winner' : ''}">
                <div class="proba-label">Victoire 1</div>
                <div class="proba-value">${prob1}%</div>
            </div>
            <div class="proba-box ${probX === maxProb ? 'winner' : ''}">
                <div class="proba-label">Match Nul</div>
                <div class="proba-value">${probX}%</div>
            </div>
            <div class="proba-box ${prob2 === maxProb ? 'winner' : ''}">
                <div class="proba-label">Victoire 2</div>
                <div class="proba-value">${prob2}%</div>
            </div>
        </div>
        
        <!-- Statistiques supplémentaires -->
        <div class="grid grid-cols-2 gap-3 mb-3 text-sm">
            <div class="bg-gray-50 p-2 rounded">
                <div class="text-gray-600">BTTS</div>
                <div class="font-bold text-gray-800">${pred.btts_probability}%</div>
            </div>
            <div class="bg-gray-50 p-2 rounded">
                <div class="text-gray-600">Fiabilité</div>
                <div class="font-bold text-gray-800">${pred.reliability_score || (pred.convergence / 10).toFixed(1)}/10</div>
            </div>
        </div>
        
        <!-- Confiance -->
        <div class="mb-3 flex items-center justify-between">
            <span class="text-sm text-gray-600">Confiance:</span>
            ${confidenceBadge}
        </div>
        
        <!-- Probabilités de buts (Over/Under) -->
        <div class="mb-3 p-3 bg-green-50 rounded border border-green-200">
            <div class="font-semibold text-gray-700 mb-2">⚽ Probabilités de buts:</div>
            <div class="grid grid-cols-5 gap-1 text-xs text-center">
                <div class="bg-white p-2 rounded shadow-sm">
                    <div class="text-gray-500 font-medium">+0.5</div>
                    <div class="font-bold text-green-600">${pred.prob_over_05 || 90}%</div>
                </div>
                <div class="bg-white p-2 rounded shadow-sm">
                    <div class="text-gray-500 font-medium">+1.5</div>
                    <div class="font-bold text-green-600">${pred.prob_over_15 || 70}%</div>
                </div>
                <div class="bg-white p-2 rounded shadow-sm">
                    <div class="text-gray-500 font-medium">+2.5</div>
                    <div class="font-bold text-green-600">${pred.prob_over_2_5 || 50}%</div>
                </div>
                <div class="bg-white p-2 rounded shadow-sm">
                    <div class="text-gray-500 font-medium">+3.5</div>
                    <div class="font-bold text-orange-600">${pred.prob_over_35 || 30}%</div>
                </div>
                <div class="bg-white p-2 rounded shadow-sm">
                    <div class="text-gray-500 font-medium">+4.5</div>
                    <div class="font-bold text-red-600">${pred.prob_over_45 || 15}%</div>
                </div>
            </div>
        </div>
        
        <!-- STATISTIQUES DE L'ARBITRE -->
        ${pred.referee && pred.referee.name ? `
        <div class="mb-3 p-3 bg-orange-50 rounded border border-orange-200">
            <div class="font-semibold text-orange-700 mb-2">⚽ Arbitre: ${pred.referee.name}</div>
            <div class="grid grid-cols-4 gap-2 text-xs text-center">
                <div class="bg-white p-2 rounded shadow-sm">
                    <div class="text-yellow-500 font-bold">🟨 ${pred.referee.avg_yellow_cards}</div>
                    <div class="text-gray-500">Jaunes/match</div>
                </div>
                <div class="bg-white p-2 rounded shadow-sm">
                    <div class="text-red-500 font-bold">🟥 ${pred.referee.avg_red_cards}</div>
                    <div class="text-gray-500">Rouges/match</div>
                </div>
                <div class="bg-white p-2 rounded shadow-sm">
                    <div class="text-blue-500 font-bold">⚽ ${pred.referee.avg_penalties}</div>
                    <div class="text-gray-500">Pénaltys/match</div>
                </div>
                <div class="bg-white p-2 rounded shadow-sm">
                    <div class="font-bold">${pred.referee.tendency_icon} ${pred.referee.tendency}</div>
                    <div class="text-gray-500">Tendance</div>
                </div>
            </div>
            <div class="mt-2 text-xs text-orange-800 italic">${pred.referee.analysis || ''}</div>
        </div>
        ` : ''}
        
        <!-- BOUTON CONFRONTATIONS DIRECTES (H2H) -->
        <div class="mb-3">
            <button onclick="showH2HModal('${match.home_team}', '${match.away_team}', '${h2hModalId}')" 
                    class="w-full py-3 px-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-bold rounded-lg shadow-lg hover:from-indigo-600 hover:to-purple-700 transition-all duration-200 flex items-center justify-center gap-2">
                <span>⚔️</span>
                <span>Voir les confrontations directes</span>
                <span>📊</span>
            </button>
        </div>
        
        <!-- Modal H2H (caché par défaut) -->
        <div id="${h2hModalId}" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto">
                <div class="p-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-t-xl flex justify-between items-center">
                    <h3 class="font-bold text-lg">⚔️ Confrontations directes</h3>
                    <button onclick="closeH2HModal('${h2hModalId}')" class="text-white hover:text-gray-200 text-2xl">&times;</button>
                </div>
                <div id="${h2hModalId}-content" class="p-4">
                    <div class="text-center py-8">
                        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto"></div>
                        <p class="mt-4 text-gray-600">Chargement des données...</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Buteurs probables -->
        ${pred.probable_scorers ? `
        <div class="mb-3 p-3 bg-yellow-50 rounded border border-yellow-200">
            <div class="font-semibold text-gray-700 mb-2">⚽ Buteurs probables:</div>
            <div class="grid grid-cols-2 gap-3 text-xs">
                <div>
                    <div class="font-semibold text-gray-600 mb-2">${match.home_team}:</div>
                    ${(() => {
                        try {
                            const scorers = typeof pred.probable_scorers === 'string' ? JSON.parse(pred.probable_scorers) : pred.probable_scorers;
                            if (scorers && scorers.home) {
                                return scorers.home.slice(0, 3).map(s => `
                                    <div class="mb-1 px-2 py-1 bg-white rounded flex justify-between items-center">
                                        <span class="text-gray-800">${s.name}</span>
                                        <span class="text-green-600 font-bold">${s.probability}%</span>
                                    </div>
                                `).join('');
                            }
                            return '<div class="text-gray-500 text-xs">Aucune donnée</div>';
                        } catch(e) { 
                            console.error('Erreur parsing buteurs:', e);
                            return '<div class="text-gray-500 text-xs">Aucune donnée</div>'; 
                        }
                    })()}
                </div>
                <div>
                    <div class="font-semibold text-gray-600 mb-2">${match.away_team}:</div>
                    ${(() => {
                        try {
                            const scorers = typeof pred.probable_scorers === 'string' ? JSON.parse(pred.probable_scorers) : pred.probable_scorers;
                            if (scorers && scorers.away) {
                                return scorers.away.slice(0, 3).map(s => `
                                    <div class="mb-1 px-2 py-1 bg-white rounded flex justify-between items-center">
                                        <span class="text-gray-800">${s.name}</span>
                                        <span class="text-green-600 font-bold">${s.probability}%</span>
                                    </div>
                                `).join('');
                            }
                            return '<div class="text-gray-500 text-xs">Aucune donnée</div>';
                        } catch(e) { 
                            console.error('Erreur parsing buteurs:', e);
                            return '<div class="text-gray-500 text-xs">Aucune donnée</div>'; 
                        }
                    })()}
                </div>
            </div>
        </div>
        ` : ''}
        
        <!-- Joueurs absents (si disponibles) -->
        ${hasAbsences ? `
        <div class="mb-3 p-3 bg-red-50 rounded border border-red-200">
            <div class="font-semibold text-red-700 mb-2">🚑 Joueurs absents:</div>
            <div class="grid grid-cols-2 gap-3 text-xs">
                <div>
                    <div class="font-semibold text-gray-600 mb-2">${match.home_team}:</div>
                    ${homeAbsences.length > 0 ? 
                        homeAbsences.map(a => `
                            <div class="mb-1 px-2 py-1 bg-white rounded flex justify-between items-center">
                                <span class="text-red-700">❌ ${a.name || a}</span>
                                <span class="text-gray-500 text-xs">${a.reason || ''}</span>
                            </div>
                        `).join('') :
                        '<div class="text-green-600 text-xs">✅ Aucune absence</div>'
                    }
                </div>
                <div>
                    <div class="font-semibold text-gray-600 mb-2">${match.away_team}:</div>
                    ${awayAbsences.length > 0 ? 
                        awayAbsences.map(a => `
                            <div class="mb-1 px-2 py-1 bg-white rounded flex justify-between items-center">
                                <span class="text-red-700">❌ ${a.name || a}</span>
                                <span class="text-gray-500 text-xs">${a.reason || ''}</span>
                            </div>
                        `).join('') :
                        '<div class="text-green-600 text-xs">✅ Aucune absence</div>'
                    }
                </div>
            </div>
        </div>
        ` : ''}
        
        <!-- Raisonnement de l'IA -->
        <div class="mt-3 p-3 bg-blue-50 border-l-4 border-blue-500 rounded">
            <div class="text-xs font-semibold text-blue-800 mb-1">💡 Analyse IA Avancée:</div>
            <div class="text-xs text-blue-900 leading-relaxed">${pred.reasoning || pred.ai_analysis}</div>
        </div>
        
        <!-- Badge système hybride -->
        <div class="mt-3 text-center">
            <span class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                🤖 ${pred.model_version || 'Advanced Hybrid AI v6.0'} (Arbitres + Tactiques + Absences)
            </span>
        </div>
    `;
    
    // Ajouter le bouton de partage
    if (typeof createShareButton === 'function') {
        const shareButton = createShareButton(match.id, {
            home_team: match.home_team,
            away_team: match.away_team,
            predicted_score: pred.predicted_score,
            confidence: pred.confidence,
            best_bet: bestBet.type,
            home_prob: Math.round(pred.home_win_prob * 10) / 10,
            draw_prob: Math.round(pred.draw_prob * 10) / 10,
            away_prob: Math.round(pred.away_win_prob * 10) / 10,
            btts: pred.btts_prob ? Math.round(pred.btts_prob) : 0,
            over25: pred.over_25_prob ? Math.round(pred.over_25_prob) : 0
        });
        div.appendChild(shareButton);
    }

    return div;
}

/**
 * Afficher le modal H2H avec les données
 */
async function showH2HModal(homeTeam, awayTeam, modalId) {
    const modal = document.getElementById(modalId);
    const contentDiv = document.getElementById(`${modalId}-content`);
    
    if (!modal || !contentDiv) return;
    
    // Afficher le modal
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    
    try {
        // Appeler l'API pour récupérer les données H2H
        const response = await fetch(`/api/football/head-to-head/${encodeURIComponent(homeTeam)}/${encodeURIComponent(awayTeam)}`);
        const result = await response.json();
        
        if (result.success && result.data) {
            const h2h = result.data;
            contentDiv.innerHTML = renderH2HContent(h2h, homeTeam, awayTeam);
        } else {
            contentDiv.innerHTML = `
                <div class="text-center py-8 text-red-500">
                    <p>Erreur lors du chargement des données.</p>
                    <p class="text-sm text-gray-500 mt-2">${result.error || 'Veuillez réessayer.'}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Erreur H2H:', error);
        contentDiv.innerHTML = `
            <div class="text-center py-8 text-red-500">
                <p>Erreur de connexion.</p>
                <p class="text-sm text-gray-500 mt-2">Veuillez réessayer plus tard.</p>
            </div>
        `;
    }
}

/**
 * Fermer le modal H2H
 */
function closeH2HModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

/**
 * Rendre le contenu H2H
 */
function renderH2HContent(h2h, homeTeam, awayTeam) {
    const matches = h2h.last_5_matches || [];
    
    return `
        <div class="space-y-4">
            <!-- Titre -->
            <div class="text-center pb-3 border-b">
                <h4 class="font-bold text-lg text-gray-800">${homeTeam} vs ${awayTeam}</h4>
                <p class="text-sm text-gray-500">${h2h.total_matches} confrontations</p>
            </div>
            
            <!-- Statistiques globales -->
            <div class="grid grid-cols-3 gap-2 text-center">
                <div class="bg-green-100 p-3 rounded-lg">
                    <div class="text-2xl font-black text-green-700">${h2h.home_wins}</div>
                    <div class="text-xs text-green-600">Victoires ${homeTeam.split(' ')[0]}</div>
                </div>
                <div class="bg-gray-100 p-3 rounded-lg">
                    <div class="text-2xl font-black text-gray-700">${h2h.draws}</div>
                    <div class="text-xs text-gray-600">Nuls</div>
                </div>
                <div class="bg-blue-100 p-3 rounded-lg">
                    <div class="text-2xl font-black text-blue-700">${h2h.away_wins}</div>
                    <div class="text-xs text-blue-600">Victoires ${awayTeam.split(' ')[0]}</div>
                </div>
            </div>
            
            <!-- Stats de buts -->
            <div class="grid grid-cols-2 gap-2 text-center text-sm">
                <div class="bg-yellow-50 p-2 rounded">
                    <div class="font-bold text-yellow-700">${h2h.avg_goals_per_match}</div>
                    <div class="text-xs text-yellow-600">Buts/match</div>
                </div>
                <div class="bg-purple-50 p-2 rounded">
                    <div class="font-bold text-purple-700">${h2h.btts_percentage}%</div>
                    <div class="text-xs text-purple-600">BTTS</div>
                </div>
            </div>
            
            <!-- Dernières confrontations -->
            <div class="mt-4">
                <h5 class="font-semibold text-gray-700 mb-2">📅 Dernières confrontations:</h5>
                <div class="space-y-2">
                    ${matches.map(m => `
                        <div class="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                            <span class="text-gray-500 text-xs w-20">${m.date}</span>
                            <span class="flex-1 text-center font-medium ${m.result === 'home' ? 'text-green-600' : (m.result === 'away' ? 'text-blue-600' : 'text-gray-600')}">
                                ${m.home_team} ${m.home_score} - ${m.away_score} ${m.away_team}
                            </span>
                            <span class="text-xs text-gray-400 w-24 text-right">${m.competition}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <!-- Résumé -->
            <div class="mt-4 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                <p class="text-sm text-indigo-800">${h2h.summary}</p>
            </div>
        </div>
    `;
}

// Fermer le modal si on clique en dehors
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('fixed') && e.target.classList.contains('bg-black')) {
        e.target.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
});
