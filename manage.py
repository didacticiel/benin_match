#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


#  (Détecte si on est en local ou en prod)
# Si la variable d'environnement DJANGO_SETTINGS_MODULE n'est pas définie, on force local
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local') 
# Note: En production (PA), cette variable sera déjà définie dans la config Web de PythonAnywhere.

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
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
