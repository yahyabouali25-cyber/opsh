r"""expand.py - Variables et expansion (jalon 4).

Syntaxes gérées : $VAR  ${VAR}  $?  $!  $$
Règles (comme Bash) :
  - dans 'apostrophes simples' : AUCUNE expansion
  - dans "guillemets doubles" ou sans guillemets : expansion
  - \$ : le dollar est protégé (littéral)
  - $(...) est laissé tel quel (jalon 5)

Deux sortes de variables :
  - variable du SHELL  : VAR=valeur         -> visible seulement dans opsh
  - variable d'ENVIRONNEMENT : export VAR   -> copiée dans os.environ, donc
    HÉRITÉE par tous les processus fils (fork + exec conservent l'environnement)
"""
import os
import re

from state import state

NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
ASSIGN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", re.DOTALL)


def get_var(name):
    """Cherche d'abord les variables du shell, puis l'environnement."""
    if name in state["vars"]:
        return state["vars"][name]
    return os.environ.get(name, "")


def set_var(name, value):
    """VAR=valeur. Si la variable est déjà exportée, elle le reste."""
    if name in os.environ:
        os.environ[name] = value
    else:
        state["vars"][name] = value


def expand(line: str) -> str:
    """Remplace $VAR, ${VAR}, $?, $!, $$ dans la ligne."""
    out = []
    i = 0
    in_single = False
    in_double = False
    n = len(line)
    while i < n:
        c = line[i]
        # suivi des guillemets
        if c == "'" and not in_double:
            in_single = not in_single
            out.append(c)
            i += 1
        elif c == '"' and not in_single:
            in_double = not in_double
            out.append(c)
            i += 1
        elif c == "\\" and not in_single and i + 1 < n and line[i + 1] == "$":
            out.append("\\$")            # $ protégé : shlex enlèvera le \
            i += 2
        elif c == "$" and not in_single and i + 1 < n:
            nxt = line[i + 1]
            if nxt == "?":
                out.append(str(state["last_status"]))
                i += 2
            elif nxt == "!":
                pid = state["last_bg_pid"]
                out.append("" if pid is None else str(pid))
                i += 2
            elif nxt == "$":
                out.append(str(os.getpid()))
                i += 2
            elif nxt == "{":
                end = line.find("}", i + 2)
                if end == -1:            # accolade jamais fermée : on laisse tel quel
                    out.append(c)
                    i += 1
                else:
                    out.append(get_var(line[i + 2:end]))
                    i = end + 1
            else:
                m = NAME_RE.match(line, i + 1)
                if m:                    # $NOM
                    out.append(get_var(m.group(0)))
                    i = m.end()
                else:                    # $( ... ) ou $ seul : inchangé
                    out.append(c)
                    i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def handle_export(argv):
    """Gère 'VAR=valeur', 'export VAR=valeur' et 'export VAR'.

    Retourne le code de sortie si argv était une affectation/export,
    sinon None (ce n'est alors pas pour nous : la commande est exécutée
    normalement).
    """
    if not argv:
        return None

    # export VAR=valeur [VAR2=valeur2 ...] / export VAR
    if argv[0] == "export":
        for arg in argv[1:]:
            m = ASSIGN_RE.match(arg)
            if m:
                name, value = m.group(1), m.group(2)
                state["vars"].pop(name, None)
                os.environ[name] = value
            elif NAME_RE.fullmatch(arg):
                # export d'une variable shell existante : on la "promeut"
                value = state["vars"].pop(arg, os.environ.get(arg, ""))
                os.environ[arg] = value
            else:
                print(f"export: '{arg}': identifiant invalide")
                return 1
        return 0

    # VAR=valeur seul (sans commande après)
    if all(ASSIGN_RE.match(a) for a in argv):
        for a in argv:
            m = ASSIGN_RE.match(a)
            set_var(m.group(1), m.group(2))
        return 0

    return None
