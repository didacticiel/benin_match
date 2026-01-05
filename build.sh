#!/usr/bin/env bash
# benin_match/start.sh
# Ce script est conçu pour l'initialisation automatique (ex: Docker, Render)

# Exit si une erreur survient
set -o errexit

echo "======================================================="
echo "🚀 INITIALISATION DE BENIN MATCH"
echo "======================================================="

# 1. Installation des dépendances Python
echo "[1/6] Installation Python..."
pip install -r requirements.txt

# 2. Installation des dépendances Node (Tailwind)
echo "[2/6] Installation Node (Tailwind v4)..."
npm install

# 3. Compilation de Tailwind CSS
echo "[3/6] Compilation du CSS..."
npm run build

# 4. Lancer les tests (Pour s'assurer que rien n'est cassé)
echo "[4/6] Lancement des tests..."
python manage.py test --settings=config.settings.testing

# 5. Collecte des fichiers statiques
echo "[5/6] Collecte des fichiers statiques..."
python manage.py collectstatic --no-input --settings=config.settings.production

# 6. Mise à jour de la base de données
echo "[6/6] Migration de la base de données..."
python manage.py migrate --settings=config.settings.production

# 7. Création automatique du Superuser (Si les env vars sont définies)
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Création automatique du superutilisateur..."
    python manage.py createsuperuser \
        --no-input \
        --settings=config.settings.production || echo "Le superutilisateur existe déjà."
fi

echo "======================================================="
echo "✅ CONFIGURATION TERMINÉE. DÉMARRAGE DE GUNICORN..."
echo "======================================================="

# 8. Démarrage de l'application
# Note le changement : src.wsgi -> config.wsgi
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000