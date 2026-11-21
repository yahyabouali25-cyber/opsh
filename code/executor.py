"""executor.py - Exécution des commandes et pipelines.

Jalons 1 et 2 : fork / exec / wait, builtins, redirections.
TODO jalon 3 : pipes '->', arrière-plan '&'.
"""
import os
import sys

from shell_builtins import is_builtin, resolve_alias, run_builtin
from redirect import apply_redirections, parse_redirections, redirected
from state import state


def run_pipeline(commands, background=False):
    """Exécute une liste de commandes reliées par des pipes.

    commands = [['show', 'f.txt'], ['wc', '-l']]
    Version actuelle : une seule commande (les pipes viennent au jalon 3).
    Retourne le code de sortie.
    """
    if len(commands) > 1:
        print("opsh: pipes '->' pas encore implémentés (jalon 3)")
        return 1

    try:
        argv, redir = parse_redirections(commands[0])
    except ValueError as e:
        print(f"opsh: {e}", file=sys.stderr)
        return 2
    argv = resolve_alias(argv)
    if not argv:
        return 0

    # Builtin : exécuté DANS le shell (pas de fork), redirections temporaires
    if is_builtin(argv[0]):
        try:
            with redirected(redir):
                return run_builtin(argv)
        except OSError as e:
            print(f"opsh: {e.filename}: {e.strerror}", file=sys.stderr)
            return 1

    # Commande externe : fork + redirections dans le fils + exec
    pid = os.fork()
    if pid == 0:
        # --- fils ---
        try:
            apply_redirections(redir)
        except OSError as e:
            print(f"opsh: {e.filename}: {e.strerror}", file=sys.stderr)
            os._exit(1)
        try:
            os.execvp(argv[0], argv)
        except FileNotFoundError:
            print(f"opsh: commande introuvable: {argv[0]}", file=sys.stderr)
        except PermissionError:
            print(f"opsh: permission refusée: {argv[0]}", file=sys.stderr)
        os._exit(127)
    # --- père ---
    _, status = os.waitpid(pid, 0)
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    return 128 + os.WTERMSIG(status)
