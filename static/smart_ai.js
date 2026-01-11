// IA Intelligente avec avis variés et réfléchis
function getSmartAIRecommendation(pred, match) {
    const prob1 = Math.round((pred.prob_home_win || 0.33) * 100);
    const probX = Math.round((pred.prob_draw || 0.33) * 100);
    const prob2 = Math.round((pred.prob_away_win || 0.33) * 100);
    const probOver25 = Math.round((pred.prob_over_2_5 || 0) * 100);
    const probBTTS = Math.round((pred.prob_both_teams_score || 0) * 100);
    const reliability = pred.reliability_score || 5;
    const confidence = pred.confidence || 'Moyenne';
    
    const homeName = match.home_team.name;
    const awayName = match.away_team.name;
    
    // Calculer des indicateurs d'analyse
    const maxWinProb = Math.max(prob1, probX, prob2);
    const spread = maxWinProb - Math.min(prob1, probX, prob2);
    const isBalanced = spread < 25;
    const isHighScoring = probOver25 > 75 && probBTTS > 65;
    const isDefensive = probOver25 < 55 && probBTTS < 55;
    
    // Générer un nombre pseudo-aléatoire basé sur l'ID du match pour avoir de la variété
    const matchSeed = match.id % 100;
    
    // === ANALYSE INTELLIGENTE AVEC VARIÉTÉ ===
    
    // Cas 1: Match très équilibré (20%)
    if (isBalanced) {
        if (matchSeed < 30) {
            return `⚖️ Match équilibré (${prob1}%/${probX}%/${prob2}%). À mon avis, <strong>BTTS</strong> (${probBTTS}%) est plus sûr que de parier sur un vainqueur.`;
        } else if (matchSeed < 60) {
            return `🤔 Difficile de départager ces deux équipes. Je pencherais pour <strong>Match Nul</strong> (${probX}%) ou <strong>+2.5 buts</strong> (${probOver25}%) si vous voulez du spectacle.`;
        } else {
            return `⚠️ Match incertain ! Les stats disent ${prob1}% pour ${homeName}, mais je vois un <strong>Match Nul</strong> (${probX}%). Méfiez-vous.`;
        }
    }
    
    // Cas 2: Match offensif attendu (15%)
    if (isHighScoring) {
        if (matchSeed < 25) {
            return `🔥 Festival de buts en vue ! Oubliez le vainqueur, misez sur <strong>+2.5 buts</strong> (${probOver25}%) et <strong>BTTS</strong> (${probBTTS}%). Les deux attaques sont en forme !`;
        } else if (matchSeed < 50) {
            return `⚽ Match spectaculaire attendu ! Même si ${homeName} est favori (${prob1}%), je préfère <strong>BTTS</strong> (${probBTTS}%). Les deux vont marquer !`;
        } else if (matchSeed < 75) {
            return `💥 Les défenses vont souffrir ! Mon conseil : <strong>+2.5 buts</strong> (${probOver25}%) plutôt que de parier sur le résultat final.`;
        } else {
            return `🎯 Attention, match piège ! Les stats disent ${prob1}% pour ${homeName}, mais avec ${probBTTS}% de BTTS, je mise sur <strong>les deux équipes marquent</strong>.`;
        }
    }
    
    // Cas 3: Match défensif (10%)
    if (isDefensive) {
        if (matchSeed < 33) {
            return `🛡️ Match fermé attendu. ${homeName} devrait gagner (${prob1}%), mais sur un <strong>score serré 1-0 ou 2-0</strong>. Évitez BTTS et +2.5 buts.`;
        } else if (matchSeed < 66) {
            return `🔒 Bataille tactique en perspective. Je vois un <strong>Match Nul 0-0 ou 1-1</strong> (${probX}%) malgré les ${prob1}% pour ${homeName}.`;
        } else {
            return `⚔️ Match défensif. Si vous devez parier, <strong>Victoire ${homeName}</strong> (${prob1}%) mais sur score serré. Peu de buts attendus.`;
        }
    }
    
    // Cas 4: Favori clair à domicile (prob1 > 65) (20%)
    if (prob1 > 65) {
        if (matchSeed < 20) {
            return `💪 ${homeName} est largement favori (${prob1}%), mais attention ! Je préfère <strong>+2.5 buts</strong> (${probOver25}%) pour plus de sécurité.`;
        } else if (matchSeed < 40) {
            return `✅ ${homeName} devrait dominer (${prob1}%). Mon conseil : <strong>Victoire 1</strong> avec confiance. L'avantage du terrain sera décisif.`;
        } else if (matchSeed < 60) {
            return `🎯 Malgré les ${prob1}% pour ${homeName}, je trouve que <strong>BTTS</strong> (${probBTTS}%) offre un meilleur rapport risque/récompense.`;
        } else if (matchSeed < 80) {
            return `⚽ ${homeName} favori (${prob1}%), mais ${awayName} peut surprendre. Je recommande <strong>+2.5 buts</strong> (${probOver25}%) plutôt que la victoire sèche.`;
        } else {
            return `🤷 Les stats disent ${prob1}% pour ${homeName}, mais je ne suis pas convaincu. <strong>BTTS</strong> (${probBTTS}%) me semble plus intéressant.`;
        }
    }
    
    // Cas 5: Favori à l'extérieur (prob2 > 60) (15%)
    if (prob2 > 60) {
        if (matchSeed < 30) {
            return `🚀 ${awayName} favori à l'extérieur (${prob2}%), mais c'est risqué. Je préfère <strong>BTTS</strong> (${probBTTS}%) pour plus de sécurité.`;
        } else if (matchSeed < 60) {
            return `✅ ${awayName} en grande forme ! <strong>Victoire 2</strong> (${prob2}%) malgré le déplacement. Belle opportunité !`;
        } else {
            return `🤔 ${awayName} favori (${prob2}%), mais jouer à l'extérieur change tout. Je mise sur <strong>+2.5 buts</strong> (${probOver25}%) ou <strong>Match Nul</strong> (${probX}%).`;
        }
    }
    
    // Cas 6: Match nul probable (probX > 30) (10%)
    if (probX > 30) {
        if (matchSeed < 50) {
            return `⚖️ Match très équilibré ! <strong>Match Nul</strong> (${probX}%) est mon pronostic. Les deux équipes vont se neutraliser.`;
        } else {
            return `🤝 Je vois un <strong>Match Nul</strong> (${probX}%) ou <strong>BTTS</strong> (${probBTTS}%). Difficile de départager ${homeName} et ${awayName}.`;
        }
    }
    
    // Cas 7: Analyse contextuelle variée (10%)
    if (reliability >= 7) {
        if (matchSeed < 25) {
            return `📊 Haute fiabilité (${reliability}/10) ! Mon analyse : <strong>${prob1 > prob2 ? 'Victoire ' + homeName : 'Victoire ' + awayName}</strong>. Les stats ne mentent pas.`;
        } else if (matchSeed < 50) {
            return `🎯 Fiabilité élevée, mais je préfère jouer la sécurité : <strong>+2.5 buts</strong> (${probOver25}%) ou <strong>BTTS</strong> (${probBTTS}%).`;
        } else if (matchSeed < 75) {
            return `💡 Malgré la haute fiabilité, je trouve que <strong>BTTS</strong> (${probBTTS}%) offre un meilleur rapport. Les deux attaques sont solides.`;
        } else {
            return `🔍 Analyse approfondie : ${homeName} (${prob1}%) vs ${awayName} (${prob2}%). Mon conseil : <strong>+2.5 buts</strong> (${probOver25}%). Match ouvert !`;
        }
    }
    
    // Cas 8: Avis contrarian (défier les probabilités) (reste)
    if (matchSeed < 15) {
        return `🎲 Les stats disent ${prob1}% pour ${homeName}, mais je sens un <strong>Match Nul</strong> (${probX}%) ou même une surprise de ${awayName}. Match piège !`;
    } else if (matchSeed < 30) {
        return `💭 Tout le monde mise sur ${prob1 > prob2 ? homeName : awayName}, mais moi je vois <strong>BTTS</strong> (${probBTTS}%). Les deux vont marquer, croyez-moi.`;
    } else if (matchSeed < 45) {
        return `🤨 ${prob1}% pour ${homeName} ? Trop prévisible. Je préfère <strong>+2.5 buts</strong> (${probOver25}%) pour un meilleur ratio risque/gain.`;
    } else if (matchSeed < 60) {
        return `⚡ Match intéressant ! Plutôt que ${homeName} (${prob1}%), je recommande <strong>BTTS</strong> (${probBTTS}%). ${awayName} ne va pas se laisser faire.`;
    } else if (matchSeed < 75) {
        return `🧠 Mon analyse : oubliez le vainqueur. <strong>+2.5 buts</strong> (${probOver25}%) est le pari intelligent ici. Match ouvert et offensif !`;
    } else {
        return `🎯 Conseil d'expert : <strong>${probBTTS > probOver25 ? 'BTTS' : '+2.5 buts'}</strong> (${Math.max(probBTTS, probOver25)}%) plutôt que de parier sur le résultat. Plus sûr !`;
    }
}

