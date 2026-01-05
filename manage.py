#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def get_settings_module():
    """
    Détermine le module de paramètres (settings) à charger intelligemment.
    """
    # 1. PRIORITÉ ABSOLUE : Détection des tests
    # Si tu lances "python manage.py test", on force le fichier de test.
    if 'test' in sys.argv or 'pytest' in sys.modules:
        return 'config.settings.testing'

    # 2. PRIORITÉ : Variable d'environnement définie par Makefile/Deploy/PythonAnywhere
    # Si quelqu'un force un fichier (ex: DJANGO_SETTINGS_MODULE=config.settings.production),
    # on le respecte.
    if 'DJANGO_SETTINGS_MODULE' in os.environ:
        return os.environ.get('DJANGO_SETTINGS_MODULE')

    # 3. DÉFAUT : Environnement Local
    # Si rien n'est précisé, on suppose qu'on est en train de coder en local.
    return 'config.settings.local'


if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    # On définit la variable si elle n'existe pas
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', get_settings_module())


def main():
    """Run administrative tasks."""
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()