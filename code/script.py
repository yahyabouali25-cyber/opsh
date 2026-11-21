"""script.py - Fichier de démarrage .opshrc et mode script.

Jalon 5 : ~/.opshrc est lu au démarrage (une commande par ligne).
Jalon 6 : 'opsh script.opsh' avec if / for / while (TODO).
"""
import os


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


def run_script(path, execute_line):
    """Exécute un fichier script ligne par ligne (if/for/while).

    TODO (jalon 6).
    """
    pass
