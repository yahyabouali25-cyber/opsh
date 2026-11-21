"""state.py - État partagé du shell (Personne C).

Tous les modules importent ce dictionnaire pour lire/écrire
le code de retour ($?), le dernier PID en arrière-plan ($!),
et les variables du shell.
"""
state = {
    "last_status": 0,     # $?  : code de sortie de la dernière commande
    "last_bg_pid": None,  # $!  : PID du dernier processus lancé avec &
    "vars": {},           # variables locales (VAR=valeur)
}
