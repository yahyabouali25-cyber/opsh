"""signals_handler.py - Signaux (Personne A).

Jalon 3 : SIGINT (Ctrl+C) ne doit pas tuer le shell ;
SIGCHLD sert à récupérer les fils en arrière-plan (éviter les zombies).
"""
import signal


def setup_signals():
    """Installe les gestionnaires de signaux.

    TODO (A) : SIGINT, SIGCHLD (avec os.waitpid(-1, os.WNOHANG)).
    """
    pass
