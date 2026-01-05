# benin_match/Makefile

# ===========================================================
# VARIABLES GLOBALES
# ===========================================================
APP_NAME = benin_match
PYTHON = python3
MANAGE = $(PYTHON) manage.py

# Configuration des fichiers de settings
SETTINGS_DEV = config.settings.local
SETTINGS_TEST = config.settings.testing
SETTINGS_PROD = config.settings.production

.PHONY: help install migrate test run ci static build-tailwind clean

help:
    @echo ""
    @echo "📘 Benin Match Makefile — Mode Production Ready"
    @echo ""
    @echo "COMMANDES LOCALES :"
    @echo "  make install      → Installe les dépendances Python"
    @echo "  make install-node → Installe les dépendances Node (Tailwind)"
    @echo "  make migrate      → Applique les migrations (Dev)"
    @echo "  make run          → Lance le serveur de développement"
    @echo ""
    @echo "FRONTEND (TAILWIND) :"
    @echo "  make build-tailwind → Compile le CSS (Tailwind v4 + DaisyUI)"
    @echo "  make static       → Compile CSS + Collecte les fichiers statiques"
    @echo ""
    @echo "COMMANDES CI/CD & QUALITÉ :"
    @echo "  make test         → Lance les tests unitaires (Settings Testing)"
    @echo "  make ci           → Pipeline complet (Install Node -> Build -> Install Py -> Test)"
    @echo "  make lint         → Vérifie la qualité du code (Flake8)"
    @echo ""

# ===========================================================
# INSTALLATION & SETUP
# ===========================================================
install:
    @echo "🐍 Installation des dépendances Python..."
    pip install -r requirements.txt

install-node:
    @echo "📦 Installation des dépendances Node (Tailwind)..."
    npm install

migrate:
    @echo "🗄️ Application des migrations..."
    $(MANAGE) migrate --settings=$(SETTINGS_DEV)

# ===========================================================
# FRONTEND & STATICS
# ===========================================================
build-tailwind:
    @echo "🎨 Compilation de Tailwind CSS (npm)..."
    npm run build

static: build-tailwind
    @echo "📦 Collecte des fichiers statiques..."
    $(MANAGE) collectstatic --no-input --settings=$(SETTINGS_PROD)

run:
    @echo "🚀 Démarrage du serveur local..."
    $(MANAGE) runserver --settings=$(SETTINGS_DEV)

# ===========================================================
# TESTS & CI (Utilisé par GitHub Actions)
# ===========================================================
test:
    @echo "🧪 Exécution des tests (Environnement de Test)..."
    # Utilise settings.testing (à créer si besoin, sinon settings.local)
    $(MANAGE) test --settings=$(SETTINGS_TEST)

ci: install-node build-tailwind install test
    @echo "✅ Pipeline CI terminé avec succès !"

lint:
    @echo "🔍 Analyse statique du code..."
    # Nécessite 'pip install flake8'
    flake8 apps config

# ===========================================================
# NETTOYAGE
# ===========================================================
clean:
    @echo "🧹 Nettoyage des fichiers temporaires..."
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -delete
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    rm -rf staticfiles/
    rm -rf .pytest_cache/
    rm -rf node_modules/.cache/