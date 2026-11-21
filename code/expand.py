"""expand.py - Expansion des variables et substitutions (Personne C).

Jalons 4 et 5 : $VAR, ${VAR}, $?, $!, $(...) et `...`.
"""
from state import state


def expand(line: str) -> str:
    """Remplace $VAR, ${VAR}, $?, $!, $(cmd) dans la ligne.

    TODO (C) : implémenter. Pour l'instant, retourne la ligne telle quelle.
    """
    return line


def handle_export(argv):
    """Gère 'export VAR=valeur' (os.environ).

    TODO (C). Retourne True si argv était une commande export/affectation.
    """
    return False
