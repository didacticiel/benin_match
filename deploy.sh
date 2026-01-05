#!/bin/bash
# Nom du script : deploy.sh

echo "=========================================="
echo "🚀 DÉPLOIEMENT AUTOMATIQUE BENIN MATCH"
echo "=========================================="

# 1. Activer l'environnement virtuel Python
source ~/benin_match/venv/bin/activate

# 2. Se placer dans le dossier du projet
cd ~/benin_match

# 3. Récupérer le dernier code depuis GitHub
echo "📥 Mise à jour du code (git pull)..."
git pull origin main

# 4. Mettre à jour les dépendances Python
echo "🐍 Mise à jour des paquets Python..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Appliquer les migrations de la base de données (Postgres)
echo "💾 Migration de la base de données..."
python manage.py migrate --noinput

# 6. Compiler les fichiers statiques (CSS/JS/Images)
echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# 7. Compiler Tailwind CSS v4 avec Node.js (Nouvelle méthode)
echo "🎨 Compilation de Tailwind CSS (npm)..."
npm run build

# 8. Nettoyer le cache Django si nécessaire (optionnel)
# python manage.py clearsessions

echo "=========================================="
echo "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS"
echo "⚠️ ACTION MANUELLE REQUISE :"
echo "⚠️ Va sur l'onglet 'Web' de PythonAnywhere et clique sur le bouton vert 'Reload'"
echo "=========================================="