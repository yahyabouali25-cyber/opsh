"""redirect.py - Redirections > >> < (jalon 2).

Rappel : chaque processus a 3 descripteurs de fichiers ouverts par défaut
    0 = stdin (entrée), 1 = stdout (sortie), 2 = stderr (erreurs).
Rediriger, c'est remplacer le fichier derrière le descripteur 0 ou 1
avec os.dup2(fd_fichier, 0 ou 1). Le programme lancé (ex: wc) ne se
rend compte de rien : il lit/écrit toujours sur 0 et 1.
"""
import contextlib
import os
import shlex
import sys

REDIR_OPS = ("<", ">", ">>")


def tokenize(segment):
    """Découpe en mots en isolant les opérateurs < > >> (même sans espaces)."""
    lexer = shlex.shlex(segment, posix=True, punctuation_chars="<>")
    lexer.whitespace_split = True
    return list(lexer)


def parse_redirections(argv):
    """Sépare les arguments des redirections.

    ['say', 'hi', '>', 'f.txt'] -> (['say', 'hi'], {'>': 'f.txt'})
    Lève ValueError si le nom de fichier manque (ex: 'say hi >').
    """
    args = []
    redir = {}
    i = 0
    while i < len(argv):
        token = argv[i]
        if token in REDIR_OPS:
            if i + 1 >= len(argv):
                raise ValueError(f"fichier manquant après '{token}'")
            redir[token] = argv[i + 1]
            i += 2  # on saute l'opérateur ET le nom de fichier
        else:
            args.append(token)
            i += 1
    return args, redir


def apply_redirections(redir):
    """Applique les redirections avec os.open + os.dup2.

    Peut lever OSError (fichier introuvable, permission refusée...).
    Dans un fils : on s'en fiche de restaurer, il va faire exec.
    """
    if "<" in redir:
        fd = os.open(redir["<"], os.O_RDONLY)
        os.dup2(fd, 0)          # le fichier devient l'entrée standard
        os.close(fd)            # le doublon suffit, on ferme l'original
    if ">" in redir:
        fd = os.open(redir[">"], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        os.dup2(fd, 1)          # le fichier devient la sortie standard
        os.close(fd)
    if ">>" in redir:
        fd = os.open(redir[">>"], os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        os.dup2(fd, 1)
        os.close(fd)


@contextlib.contextmanager
def redirected(redir):
    """Applique les redirections dans le shell lui-même (pour les builtins),
    puis restaure stdin/stdout à la sortie du bloc 'with'.

    Nécessaire car un builtin (say, path...) s'exécute dans le processus
    du shell : sans restauration, le shell resterait redirigé pour toujours.
    """
    saved_in = os.dup(0)    # sauvegarde des vrais stdin/stdout
    saved_out = os.dup(1)
    try:
        apply_redirections(redir)
        yield
    finally:
        sys.stdout.flush()  # vider le tampon Python AVANT de restaurer
        os.dup2(saved_in, 0)
        os.dup2(saved_out, 1)
        os.close(saved_in)
        os.close(saved_out)
