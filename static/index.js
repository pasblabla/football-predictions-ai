/**
 * Point d'entrée pour le déploiement Manus
 * Lance le serveur Flask Python
 */

const { spawn } = require('child_process');
const path = require('path');

console.log('🚀 Démarrage du serveur Football Predictions API...');

// Lancer le serveur Flask
const pythonProcess = spawn('python3', [
    path.join(__dirname, 'server', 'main.py')
], {
    cwd: __dirname,
    env: {
        ...process.env,
        PYTHONUNBUFFERED: '1'
    }
});

// Afficher les logs Python
pythonProcess.stdout.on('data', (data) => {
    console.log(data.toString());
});

pythonProcess.stderr.on('data', (data) => {
    console.error(data.toString());
});

pythonProcess.on('close', (code) => {
    console.log(`Serveur Flask arrêté avec le code ${code}`);
    process.exit(code);
});

// Gérer l'arrêt propre
process.on('SIGTERM', () => {
    console.log('SIGTERM reçu, arrêt du serveur...');
    pythonProcess.kill('SIGTERM');
});

process.on('SIGINT', () => {
    console.log('SIGINT reçu, arrêt du serveur...');
    pythonProcess.kill('SIGINT');
});

