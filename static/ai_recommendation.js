// Fonction intelligente pour obtenir la recommandation personnalisée de l'IA
function getAIRecommendation(pred, match) {
    const prob1 = Math.round((pred.prob_home_win || 0.33) * 100);
    const probX = Math.round((pred.prob_draw || 0.33) * 100);
    const prob2 = Math.round((pred.prob_away_win || 0.33) * 100);
    const probOver25 = Math.round((pred.prob_over_2_5 || 0) * 100);
    const probBTTS = Math.round((pred.prob_both_teams_score || 0) * 100);
    const reliability = pred.reliability_score || 5;
    
    // Analyser l'équilibre du match
    const maxWinProb = Math.max(prob1, probX, prob2);
    const minWinProb = Math.min(prob1, probX, prob2);
    const spread = maxWinProb - minWinProb;
    
    // Match très équilibré (écart < 20%)
    if (spread < 20) {
        if (probBTTS > 70) {
            return `🤔 Match équilibré ! Je préfère miser sur <strong>BTTS (les deux équipes marquent)</strong> à ${probBTTS}% plutôt que de choisir un vainqueur. Plus sûr !`;
        } else if (probOver25 > 75) {
            return `🤔 Match serré ! Plutôt que de parier sur le résultat, je recommande <strong>+2.5 buts</strong> (${probOver25}%). Les deux équipes vont se donner à fond.`;
        } else {
            return `⚠️ Match très incertain. Les probabilités sont trop équilibrées (${prob1}% / ${probX}% / ${prob2}%). Je conseille d'éviter ce match ou de miser sur <strong>Match Nul</strong> si vous devez parier.`;
        }
    }
    
    // Favori clair (écart > 40%)
    if (spread > 40) {
        if (prob1 > 65) {
            if (probBTTS < 60 && reliability >= 6) {
                return `💪 ${match.home_team.name} est largement favori (${prob1}%). Je recommande <strong>Victoire 1</strong> avec confiance. Domination attendue !`;
            } else if (probOver25 > 80) {
                return `⚽ ${match.home_team.name} devrait gagner, mais je préfère <strong>+2.5 buts</strong> (${probOver25}%). Match offensif en perspective !`;
            } else {
                return `✅ <strong>Victoire ${match.home_team.name}</strong> (${prob1}%) semble solide, mais surveillez la défense adverse.`;
            }
        } else if (prob2 > 65) {
            if (probBTTS < 60 && reliability >= 6) {
                return `💪 ${match.away_team.name} est largement favori à l'extérieur (${prob2}%). Je recommande <strong>Victoire 2</strong>. Performance attendue !`;
            } else {
                return `✅ <strong>Victoire ${match.away_team.name}</strong> (${prob2}%) est mon choix, malgré le déplacement.`;
            }
        }
    }
    
    // Favori modéré (écart entre 20% et 40%)
    if (spread >= 20 && spread <= 40) {
        if (prob1 > probX && prob1 > prob2) {
            // Favori à domicile
            if (probBTTS > 75) {
                return `🎯 ${match.home_team.name} est favori (${prob1}%), mais je préfère <strong>BTTS</strong> (${probBTTS}%). Les deux équipes ont de bonnes attaques !`;
            } else if (probOver25 > 80 && probBTTS > 65) {
                return `⚽ Plutôt que la victoire de ${match.home_team.name}, je recommande <strong>+2.5 buts</strong> (${probOver25}%). Match ouvert et offensif !`;
            } else if (reliability >= 7) {
                return `✅ <strong>Victoire ${match.home_team.name}</strong> (${prob1}%) est mon conseil. Avantage du terrain décisif.`;
            } else {
                return `🤷 ${match.home_team.name} favori à ${prob1}%, mais fiabilité moyenne. Je suggère <strong>BTTS</strong> (${probBTTS}%) pour plus de sécurité.`;
            }
        } else if (prob2 > probX && prob2 > prob1) {
            // Favori à l'extérieur
            if (probBTTS > 75) {
                return `🎯 ${match.away_team.name} favori à l'extérieur (${prob2}%), mais je préfère <strong>BTTS</strong> (${probBTTS}%). Match équilibré offensivement !`;
            } else if (reliability >= 7) {
                return `✅ <strong>Victoire ${match.away_team.name}</strong> (${prob2}%) malgré le déplacement. Bonne forme attendue.`;
            } else {
                return `🤔 ${match.away_team.name} légèrement favori (${prob2}%), mais à l'extérieur c'est risqué. Je préfère <strong>+2.5 buts</strong> (${probOver25}%).`;
            }
        } else {
            // Match nul probable
            if (probBTTS > 70) {
                return `⚖️ Match très équilibré ! Plutôt que le nul, je recommande <strong>BTTS</strong> (${probBTTS}%). Les deux vont marquer.`;
            } else {
                return `⚖️ <strong>Match Nul</strong> (${probX}%) est ma prédiction. Équilibre parfait entre les deux équipes.`;
            }
        }
    }
    
    // Analyse spéciale pour les matchs à haut score
    if (probOver25 > 85 && probBTTS > 80) {
        return `🔥 Match spectaculaire en vue ! Je recommande <strong>BTTS + +2.5 buts</strong> (${probBTTS}% et ${probOver25}%). Festival de buts attendu !`;
    }
    
    // Analyse spéciale pour les matchs défensifs
    if (probOver25 < 50 && probBTTS < 50) {
        if (prob1 > 60) {
            return `🛡️ Match défensif. <strong>Victoire ${match.home_team.name}</strong> (${prob1}%) sur un score serré. Peu de buts attendus.`;
        } else if (prob2 > 60) {
            return `🛡️ Match défensif. <strong>Victoire ${match.away_team.name}</strong> (${prob2}%) sur un score serré.`;
        } else {
            return `🛡️ Match fermé. <strong>Match Nul 0-0 ou 1-1</strong> probable. Évitez BTTS et +2.5 buts.`;
        }
    }
    
    // Par défaut : recommandation basée sur la plus haute probabilité avec nuance
    const allProbs = [
        { type: `Victoire ${match.home_team.name}`, prob: prob1, code: '1' },
        { type: 'Match Nul', prob: probX, code: 'X' },
        { type: `Victoire ${match.away_team.name}`, prob: prob2, code: '2' },
        { type: '+2.5 buts', prob: probOver25, code: 'O2.5' },
        { type: 'BTTS', prob: probBTTS, code: 'BTTS' }
    ];
    
    allProbs.sort((a, b) => b.prob - a.prob);
    const best = allProbs[0];
    const second = allProbs[1];
    
    if (best.prob - second.prob < 10) {
        return `🤔 Choix difficile entre <strong>${best.type}</strong> (${best.prob}%) et <strong>${second.type}</strong> (${second.prob}%). Je penche légèrement pour ${best.type}.`;
    } else {
        return `✅ Mon conseil : <strong>${best.type}</strong> (${best.prob}%). C'est le pronostic le plus solide pour ce match.`;
    }
}

