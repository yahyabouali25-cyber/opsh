"""script.py - Fichier de démarrage .opshrc et mode script (jalons 5 et 6).

Mode script :  python3 opsh.py script.opsh
Syntaxe (inspirée de Bash, un mot-clé par ligne) :

    for i in 1 2 3            while test $n -lt 3        if test -f f.txt
    do                        do                         then
      say $i                    n=$(expr $n + 1)           say existe
    done                      done                       else
                                                           say absent
                                                         fi

Une CONDITION est une commande : elle est "vraie" si son code de sortie
est 0 (convention Unix). On utilise 'test' (ou '[') et 'true'/'false'.
Aussi gérés : break, continue, "; do" et "; then" en fin de ligne.

Principe : on lit le fichier, on construit un ARBRE (parse_block), puis on
parcourt l'arbre (run_nodes) en exécutant chaque commande avec execute_line.
"""
import glob
import os
import re
import shlex
import sys

from expand import expand, set_var
from redirect import tokenize
from state import state

KEYWORDS = {"then", "else", "fi", "do", "done"}


class ScriptError(Exception):
    """Erreur de syntaxe dans le script."""


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


# ---------------------------------------------------------------- .opshrc
def load_rc(execute_line):
    """Exécute chaque ligne de ~/.opshrc avec execute_line(line).

    Les lignes vides et celles qui commencent par # sont ignorées.
    """
    path = os.path.expanduser("~/.opshrc")
    if not os.path.isfile(path):
        return
    with open(path) as f:
        for num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                execute_line(line)
            except SystemExit:
                break
            except Exception as e:
                print(f"opsh: .opshrc ligne {num}: {e}")


# ---------------------------------------------------------------- analyse
def first_word(text):
    return text.split()[0]


def expect(lines, i, word, what):
    """Vérifie que la ligne i est exactement 'word' ; sinon erreur."""
    if i >= len(lines) or lines[i][1] != word:
        num = lines[i][0] if i < len(lines) else "fin de fichier"
        raise ScriptError(f"ligne {num}: '{word}' attendu ({what})")


def header(lines, i, keyword_len, closer):
    """Lit l'en-tête d'un if/for/while.

    'while test $n -lt 3; do' ou 'while test $n -lt 3' + ligne 'do'.
    Retourne (texte_en_tête, index_du_corps).
    """
    num, text = lines[i]
    text = text[keyword_len:].strip()
    if text.endswith("; " + closer) or text.endswith(";" + closer):
        return text.rsplit(";", 1)[0].strip(), i + 1
    expect(lines, i + 1, closer, f"après la ligne {num}")
    return text, i + 2


def parse_block(lines, i, stops):
    """Construit la liste de noeuds jusqu'à rencontrer un mot de 'stops'.

    Noeuds : ("cmd", ligne) ("if", cond, alors, sinon) ("for", var, mots, corps)
             ("while", cond, corps) ("break",) ("continue",)
    Retourne (noeuds, index du mot d'arrêt).
    """
    nodes = []
    while i < len(lines):
        num, text = lines[i]
        word = first_word(text)

        if word in stops:
            return nodes, i
        if word in KEYWORDS:
            raise ScriptError(f"ligne {num}: '{word}' inattendu")

        if word == "if":
            cond, i = header(lines, i, 2, "then")
            then_nodes, i = parse_block(lines, i, {"else", "fi"})
            else_nodes = []
            if i < len(lines) and lines[i][1] == "else":
                else_nodes, i = parse_block(lines, i + 1, {"fi"})
            expect(lines, i, "fi", f"fin du 'if' de la ligne {num}")
            nodes.append(("if", cond, then_nodes, else_nodes))
            i += 1

        elif word == "for":
            head, i = header(lines, i, 3, "do")
            m = re.match(r"^([A-Za-z_]\w*)\s+in(?:\s+(.*))?$", head)
            if not m:
                raise ScriptError(f"ligne {num}: syntaxe 'for VAR in mots'")
            body, i = parse_block(lines, i, {"done"})
            expect(lines, i, "done", f"fin du 'for' de la ligne {num}")
            nodes.append(("for", m.group(1), m.group(2) or "", body))
            i += 1

        elif word == "while":
            cond, i = header(lines, i, 5, "do")
            body, i = parse_block(lines, i, {"done"})
            expect(lines, i, "done", f"fin du 'while' de la ligne {num}")
            nodes.append(("while", cond, body))
            i += 1

        elif text in ("break", "continue"):
            nodes.append((text,))
            i += 1

        else:
            nodes.append(("cmd", text))
            i += 1

    return nodes, i


# ---------------------------------------------------------------- exécution
def loop_words(words_line, execute_line):
    """Mots d'un 'for' : expansion des variables, puis des jokers (*.txt)."""
    result = []
    for w in tokenize(expand(words_line)):
        if any(ch in w for ch in "*?["):
            result.extend(sorted(glob.glob(w)) or [w])
        else:
            result.append(w)
    return result


def run_nodes(nodes, execute_line):
    for node in nodes:
        kind = node[0]

        if kind == "cmd":
            execute_line(node[1])

        elif kind == "if":
            _, cond, then_nodes, else_nodes = node
            execute_line(cond)
            # code de sortie 0 = vrai
            run_nodes(then_nodes if state["last_status"] == 0 else else_nodes,
                      execute_line)

        elif kind == "for":
            _, var, words_line, body = node
            for word in loop_words(words_line, execute_line):
                set_var(var, word)
                try:
                    run_nodes(body, execute_line)
                except _Continue:
                    continue
                except _Break:
                    break

        elif kind == "while":
            _, cond, body = node
            while True:
                execute_line(cond)
                if state["last_status"] != 0:
                    break
                try:
                    run_nodes(body, execute_line)
                except _Continue:
                    continue
                except _Break:
                    break

        elif kind == "break":
            raise _Break()
        elif kind == "continue":
            raise _Continue()


def run_script(path, execute_line):
    """Exécute un fichier script. Retourne le code de sortie du script."""
    try:
        with open(path) as f:
            raw = f.read().splitlines()
    except OSError as e:
        print(f"opsh: {path}: {e.strerror}", file=sys.stderr)
        return 127

    # (numéro de ligne, texte) sans lignes vides ni commentaires (# et #!)
    lines = [(n, l.strip()) for n, l in enumerate(raw, 1)
             if l.strip() and not l.strip().startswith("#")]
    try:
        nodes, _ = parse_block(lines, 0, set())
        run_nodes(nodes, execute_line)
    except ScriptError as e:
        print(f"opsh: {path}: {e}", file=sys.stderr)
        return 2
    except (_Break, _Continue):
        print(f"opsh: {path}: 'break'/'continue' hors d'une boucle",
              file=sys.stderr)
        return 2
    except SystemExit as e:
        return e.code or 0
    return state["last_status"]
