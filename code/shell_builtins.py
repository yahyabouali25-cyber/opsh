"""shell_builtins.py - Builtins et alias (jalon 2).

Builtins : go, quit, path, say, info, past, osinfo.
Alias    : list->ls, show->cat, copy->cp, move->mv, del->rm,
           newdir->mkdir, newfile->touch.

Pourquoi 'go' (cd) DOIT être un builtin : chaque processus a son propre
dossier courant. Un fils qui ferait chdir ne changerait que SON dossier,
pas celui du shell père. Il faut donc exécuter chdir dans le shell.
"""
import os

import history

ALIASES = {
    "list": "ls", "show": "cat", "copy": "cp", "move": "mv",
    "del": "rm", "newdir": "mkdir", "newfile": "touch",
}

BUILTINS = {"go", "quit", "path", "say", "info", "past", "osinfo"}

HELP = """Commandes opsh :
  go [dossier]   changer de dossier        (cd)
  path           afficher le dossier        (pwd)
  say texte      afficher du texte          (echo)
  past           historique                 (history)
  info           cette aide                 (help)
  quit           quitter                    (exit)
  osinfo         informations sur le cours
Alias : list=ls  show=cat  copy=cp  move=mv  del=rm  newdir=mkdir  newfile=touch
Pipe : cmd1 -> cmd2     Redirections : >  >>  <"""


def resolve_alias(argv):
    """Remplace le nom de la commande par son équivalent bash."""
    if argv and argv[0] in ALIASES:
        return [ALIASES[argv[0]]] + argv[1:]
    return argv


def is_builtin(name):
    return name in BUILTINS


def run_builtin(argv):
    """Exécute un builtin dans le processus du shell. Retourne le code de sortie."""
    cmd, args = argv[0], argv[1:]

    if cmd == "quit":
        raise SystemExit(0)

    if cmd == "go":
        target = os.path.expanduser(args[0]) if args else os.path.expanduser("~")
        try:
            os.chdir(target)
        except OSError as e:
            print(f"go: {target}: {e.strerror}")
            return 1
        return 0

    if cmd == "path":
        print(os.getcwd())
        return 0

    if cmd == "say":
        print(" ".join(args))
        return 0

    if cmd == "info":
        print(HELP)
        return 0

    if cmd == "past":
        history.show()
        return 0

    if cmd == "osinfo":
        print("Systèmes d'Exploitation -- UIR/ESIN")
        return 0

    return 1
