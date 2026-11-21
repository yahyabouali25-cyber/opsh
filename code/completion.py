"""completion.py - Complétion avec la touche Tab (jalon 5).

- 1er mot de la commande (ou mot après '->') : noms de commandes
  (builtins, alias, programmes du PATH).
- Autres mots : noms de fichiers / dossiers.
readline appelle completer(text, state) : state = 0, 1, 2... jusqu'à ce
qu'on retourne None ; chaque appel donne la proposition suivante.
"""
import glob
import os

try:
    import readline
except ImportError:
    readline = None

from shell_builtins import ALIASES, BUILTINS

_matches = []


def command_names():
    """Tous les noms de commandes possibles."""
    names = set(BUILTINS) | set(ALIASES)
    for folder in os.environ.get("PATH", "").split(os.pathsep):
        try:
            for f in os.listdir(folder):
                if os.access(os.path.join(folder, f), os.X_OK):
                    names.add(f)
        except OSError:
            pass
    return sorted(names)


def completer(text, state):
    global _matches
    if state == 0:                       # nouvelle recherche
        line = readline.get_line_buffer()
        before = line[:readline.get_begidx()].strip()
        if before == "" or before.endswith("->"):
            _matches = [c + " " for c in command_names() if c.startswith(text)]
        else:
            _matches = []
            for p in sorted(glob.glob(os.path.expanduser(text) + "*")):
                _matches.append(p + "/" if os.path.isdir(p) else p + " ")
    return _matches[state] if state < len(_matches) else None


def setup():
    if readline is None:
        return
    readline.set_completer_delims(" \t\n")   # le mot = tout jusqu'à l'espace
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
