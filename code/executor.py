"""executor.py - Exécution des commandes et pipelines.

Jalons 1, 2, 3 : fork/exec/wait, builtins, redirections,
pipes '->', arrière-plan '&', signaux.
"""
import os
import signal
import sys

from redirect import apply_redirections, parse_redirections, redirected
from shell_builtins import is_builtin, resolve_alias, run_builtin
from state import state


def prepare(commands):
    """Analyse toutes les commandes AVANT de lancer un fork.

    Retourne une liste de (argv, redir). Lève ValueError en cas d'erreur
    de syntaxe (ex: 'say hi >'), pour ne rien lancer.
    """
    prepared = []
    for cmd in commands:
        argv, redir = parse_redirections(cmd)
        argv = resolve_alias(argv)
        if not argv:
            raise ValueError("commande vide")
        prepared.append((argv, redir))
    return prepared


def child_process(argv, redir, fd_in, fd_out, all_fds, background, old_mask):
    """Code exécuté dans le FILS (ne retourne jamais)."""
    # Le père bloquait SIGCHLD pendant le fork : le fils doit le débloquer,
    # sinon le programme lancé hériterait du masque.
    signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
    # Ctrl+C : tue un fils au premier plan, mais un fils en arrière-plan l'ignore.
    # (un signal IGNORÉ reste ignoré après exec)
    signal.signal(signal.SIGINT, signal.SIG_IGN if background else signal.SIG_DFL)

    # Câblage du pipe : entrée 0 <- pipe précédent, sortie 1 -> pipe suivant
    if fd_in is not None:
        os.dup2(fd_in, 0)
    if fd_out is not None:
        os.dup2(fd_out, 1)
    # TRÈS IMPORTANT : fermer TOUS les bouts de pipes ouverts, sinon le
    # lecteur ne verra jamais la fin du flux (EOF) et restera bloqué.
    for fd in all_fds:
        os.close(fd)

    # En arrière-plan, on ne doit pas voler le clavier : stdin = /dev/null
    if background and fd_in is None and "<" not in redir:
        devnull = os.open(os.devnull, os.O_RDONLY)
        os.dup2(devnull, 0)
        os.close(devnull)

    try:
        apply_redirections(redir)   # appliquées APRÈS les pipes : elles gagnent
    except OSError as e:
        print(f"opsh: {e.filename}: {e.strerror}", file=sys.stderr)
        os._exit(1)

    if is_builtin(argv[0]):
        # Builtin dans un pipeline : exécuté dans le fils
        try:
            status = run_builtin(argv)
        except SystemExit as e:
            status = e.code or 0
        sys.stdout.flush()
        os._exit(status)

    try:
        os.execvp(argv[0], argv)    # remplace l'image du processus
    except FileNotFoundError:
        print(f"opsh: commande introuvable: {argv[0]}", file=sys.stderr)
    except PermissionError:
        print(f"opsh: permission refusée: {argv[0]}", file=sys.stderr)
    os._exit(127)


def wait_foreground(pids):
    """Attend les fils du premier plan. Retourne le statut du DERNIER."""
    status = 0
    for pid in pids:
        while True:
            try:
                _, st = os.waitpid(pid, 0)
                break
            except KeyboardInterrupt:
                continue            # Ctrl+C : le fils l'a reçu aussi, on attend
            except ChildProcessError:
                st = 0
                break
        if os.WIFEXITED(st):
            status = os.WEXITSTATUS(st)
        else:
            sig = os.WTERMSIG(st)
            if sig == signal.SIGINT:
                print()
            status = 128 + sig
    return status


def run_pipeline(commands, background=False):
    """Exécute 'cmd1 -> cmd2 -> cmd3' (avec & éventuel). Retourne le statut."""
    try:
        prepared = prepare(commands)
    except ValueError as e:
        print(f"opsh: {e}", file=sys.stderr)
        return 2

    # Cas simple : un builtin seul, au premier plan -> dans le shell, sans fork
    if len(prepared) == 1 and not background and is_builtin(prepared[0][0][0]):
        argv, redir = prepared[0]
        try:
            with redirected(redir):
                return run_builtin(argv)
        except OSError as e:
            print(f"opsh: {e.filename}: {e.strerror}", file=sys.stderr)
            return 1

    n = len(prepared)
    # n commandes -> n-1 pipes. os.pipe() donne (bout_lecture, bout_écriture)
    pipes = [os.pipe() for _ in range(n - 1)]
    all_fds = [fd for p in pipes for fd in p]

    # Au premier plan, on bloque SIGCHLD : sinon le gestionnaire pourrait
    # récolter nos fils avant waitpid et on perdrait leur code de retour.
    old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGCHLD})
    pids = []
    try:
        for i, (argv, redir) in enumerate(prepared):
            fd_in = pipes[i - 1][0] if i > 0 else None
            fd_out = pipes[i][1] if i < n - 1 else None
            pid = os.fork()
            if pid == 0:
                child_process(argv, redir, fd_in, fd_out, all_fds,
                              background, old_mask)
            pids.append(pid)

        # Le père ferme tous ses bouts de pipes (il ne s'en sert pas)
        for fd in all_fds:
            os.close(fd)
        all_fds = []

        if background:
            state["last_bg_pid"] = pids[-1]
            print(f"[{pids[-1]}]")
            return 0
        return wait_foreground(pids)
    finally:
        for fd in all_fds:          # sécurité en cas d'erreur
            os.close(fd)
        signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
