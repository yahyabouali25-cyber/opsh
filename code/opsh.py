#!/usr/bin/env python3
"""opsh - Mini-shell en Python (Systèmes d'Exploitation, UIR/ESIN).

Programme principal (Personne A) : assemble les modules.
Chaîne de traitement :
  expand -> découpage par '->' -> resolve_alias -> redirections -> run_pipeline
"""
import atexit
import sys
import readline  # noqa: F401 - active les flèches / l'édition de ligne
import shlex

import completion
import history
from executor import run_pipeline
from expand import expand, handle_export, set_executor
from redirect import tokenize
from script import load_rc, run_script
from signals_handler import setup_signals
from state import state

PROMPT = "opsh> "


def parse_line(line):
    """'show f.txt -> wc -l' => [['show','f.txt'], ['wc','-l']]"""
    segments = [seg.strip() for seg in line.split("->")]
    return [tokenize(seg) for seg in segments if seg]


def execute_line(line):
    """Exécute une ligne complète. Réutilisée par le mode script (C)."""
    line = line.strip()
    if not line:
        return
    line = expand(line)
    background = line.endswith("&")
    if background:
        line = line[:-1].strip()
    commands = parse_line(line)
    if not commands:
        return
    # VAR=valeur et export : doivent agir dans le shell lui-même (comme 'go')
    if len(commands) == 1 and not background:
        status = handle_export(commands[0])
        if status is not None:
            state["last_status"] = status
            return
    state["last_status"] = run_pipeline(commands, background)


def main():
    setup_signals()
    set_executor(execute_line)      # pour $(...) : expand doit pouvoir exécuter

    # Mode script :  python3 opsh.py script.opsh
    if len(sys.argv) > 1:
        sys.exit(run_script(sys.argv[1], execute_line))

    # Mode interactif
    history.load()                  # historique de la session précédente
    completion.setup()              # touche Tab
    atexit.register(history.save)   # sauvegarde à la sortie
    load_rc(execute_line)           # ~/.opshrc
    while True:
        try:
            line = input(PROMPT)
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue
        if line.strip():
            history.add(line.strip())
        try:
            execute_line(line)
        except SystemExit:
            break


if __name__ == "__main__":
    main()
