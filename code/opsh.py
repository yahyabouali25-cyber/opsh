#!/usr/bin/env python3
"""opsh - Mini-shell en Python (Systèmes d'Exploitation, UIR/ESIN).

Programme principal (Personne A) : assemble les modules.
Chaîne de traitement :
  expand -> découpage par '->' -> resolve_alias -> redirections -> run_pipeline
"""
import readline  # noqa: F401 - active les flèches / l'édition de ligne
import shlex

import history
from executor import run_pipeline
from expand import expand
from signals_handler import setup_signals
from state import state

PROMPT = "opsh> "


def parse_line(line):
    """'show f.txt -> wc -l' => [['show','f.txt'], ['wc','-l']]"""
    segments = [seg.strip() for seg in line.split("->")]
    return [tokenize(seg) for seg in segments if seg]


def tokenize(segment):
    """Découpe en mots en isolant les opérateurs < > >> (même sans espaces)."""
    lexer = shlex.shlex(segment, posix=True, punctuation_chars="<>")
    lexer.whitespace_split = True
    return list(lexer)


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
    if commands:
        state["last_status"] = run_pipeline(commands, background)


def main():
    setup_signals()
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
