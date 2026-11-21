"""signals_handler.py - Signaux (jalon 3).

SIGINT  (Ctrl+C) : le shell ne doit PAS mourir quand on interrompt une commande.
                   (géré dans opsh.py et executor.py, voir wait_foreground)
SIGCHLD : envoyé au père quand un fils se termine. On l'utilise pour
          "récolter" (waitpid) les fils en arrière-plan : sans cela,
          ils restent ZOMBIES (terminés mais jamais attendus).
"""
import os
import signal
import sys


def sigchld_handler(signum, frame):
    """Récolte tous les fils terminés, sans bloquer (WNOHANG)."""
    while True:
        try:
            pid, _status = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:   # plus aucun fils
            break
        if pid == 0:                # des fils existent mais aucun n'est fini
            break
        print(f"\n[processus {pid} terminé]", file=sys.stderr)


def setup_signals():
    """Installe le gestionnaire SIGCHLD (appelé une fois au démarrage)."""
    signal.signal(signal.SIGCHLD, sigchld_handler)
