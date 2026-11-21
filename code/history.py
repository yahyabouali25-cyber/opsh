"""history.py - Historique persistant (jalon 5).

- 'past' affiche l'historique numéroté.
- L'historique est sauvegardé dans ~/.opsh_history à la sortie et rechargé
  au démarrage : on le retrouve d'une session à l'autre.
- Les flèches haut/bas sont fournies par le module readline.
"""
import os

try:
    import readline
except ImportError:          # pas de readline : pas de flèches, c'est tout
    readline = None

MAX_LINES = 500
history_list = []


def _path():
    return os.path.expanduser("~/.opsh_history")


def load():
    """Charge l'historique du fichier (au démarrage)."""
    try:
        with open(_path()) as f:
            for line in f:
                line = line.rstrip("\n")
                if line:
                    history_list.append(line)
                    if readline:
                        readline.add_history(line)   # pour les flèches
    except OSError:
        pass


def save():
    """Sauvegarde les dernières lignes (à la sortie, via atexit)."""
    try:
        with open(_path(), "w") as f:
            for line in history_list[-MAX_LINES:]:
                f.write(line + "\n")
    except OSError:
        pass


def add(line):
    """Ajoute une ligne à l'historique."""
    history_list.append(line)


def show():
    """Affiche l'historique numéroté (commande 'past')."""
    for i, line in enumerate(history_list, 1):
        print(f"{i:4}  {line}")
