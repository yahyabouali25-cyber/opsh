"""history.py - Historique et complétion (Personne B).

Jalon 5. Commande 'past' = history. Utiliser le module readline.
"""
history_list = []


def add(line):
    """Ajoute une ligne à l'historique."""
    history_list.append(line)


def show():
    """Affiche l'historique numéroté (commande 'past')."""
    for i, line in enumerate(history_list, 1):
        print(f"{i:4}  {line}")
