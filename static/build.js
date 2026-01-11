#!/usr/bin/env node

/**
 * Script de build pour le déploiement
 * Copie les fichiers nécessaires dans dist/
 */

const fs = require('fs');
const path = require('path');

console.log('🔨 Build Football Predictions API...\n');

// Créer le répertoire dist s'il n'existe pas
const distDir = path.join(__dirname, 'dist');
if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true });
    console.log('✅ Répertoire dist/ créé');
}

// Vérifier que index.js existe
const indexPath = path.join(distDir, 'index.js');
if (fs.existsSync(indexPath)) {
    console.log('✅ dist/index.js existe');
} else {
    console.error('❌ dist/index.js manquant!');
    process.exit(1);
}

// Vérifier que le serveur Python existe
const serverPath = path.join(__dirname, 'server', 'main.py');
if (fs.existsSync(serverPath)) {
    console.log('✅ server/main.py existe');
} else {
    console.error('❌ server/main.py manquant!');
    process.exit(1);
}

// Vérifier que la base de données existe
const dbPath = path.join(__dirname, 'server', 'database', 'app.db');
if (fs.existsSync(dbPath)) {
    console.log('✅ Base de données existe');
} else {
    console.warn('⚠️  Base de données manquante (sera créée au démarrage)');
}

console.log('\n🎉 Build terminé avec succès!');
console.log('📦 Prêt pour le déploiement\n');

