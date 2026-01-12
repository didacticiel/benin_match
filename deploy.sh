#!/bin/bash
echo "=========================================="
echo "🚀 DÉPLOIEMENT BENIN MATCH (MODE LIGHT)"
echo "=========================================="

# 1. Aller dans le dossier et activer l'environnement
cd ~/benin_match
source venv/bin/activate

# 2. Récupérer le code (le CSS doit être compilé en LOCAL avant le push)
echo "📥 Mise à jour du code..."
git pull origin main

# 3. Mettre à jour Python
echo "🐍 Mise à jour des paquets Python..."
pip install -r requirements.txt

# 4. Base de données
echo "💾 Migration de la base de données..."
python manage.py migrate --noinput

# 5. Fichiers statiques
echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear

# 6. Rechargement automatique du serveur
echo "🔄 Rechargement du serveur..."
touch /var/www/beninmatch_pythonanywhere_com_wsgi.py

echo "=========================================="
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "=========================================="
