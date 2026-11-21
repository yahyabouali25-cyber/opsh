# opsh — Mini-shell en Python

Projet semestriel du module **Systèmes d'Exploitation** — UIR / ESIN
Encadrant : Pr. Ilias Tougui

**Équipe :** [yahya bouali] · [youssef el moubarik] · [yasser ait el fakir]

`opsh` est un interpréteur de commandes (un *shell*) écrit en Python, qui reconstruit les mécanismes réels de Bash : création de processus (`fork` / `exec` / `wait`), redirections, pipes, signaux, variables, substitution de commandes et mode script. Il utilise directement les appels système Unix via le module `os`.

---

## Prérequis

- **Linux** (Ubuntu recommandé). Sous Windows, utiliser **WSL2** (`wsl --install`) ou GitHub Codespaces : `os.fork()` n'existe pas sous Windows natif.
- **Python 3.8+** (`python3 --version`)
- Aucune bibliothèque externe : uniquement la bibliothèque standard.

## Installation et lancement

```bash
git clone https://github.com/yahyabouali25-cyber/opsh.git
cd opsh/code
python3 opsh.py
```

Le prompt `opsh> ` apparaît. Pour quitter : `quit` (ou `Ctrl+D`).

**Mode script :**

```bash
python3 opsh.py exemples/demo.opsh
```

---

## Fonctionnalités (par jalon)

| Jalon | Fonctionnalité | Exemple |
|---|---|---|
| 1 | Boucle REPL, `fork` / `execvp` / `waitpid` | `ls` |
| 2 | Builtins, alias, redirections | `say hello > f.txt` |
| 3 | Pipes, arrière-plan, signaux | `show f.txt -> wc -l`, `sleep 10 &` |
| 4 | Variables et expansion | `NAME=Yahya`, `say $NAME`, `$?`, `$!` |
| 5 | Substitution de commande, `.opshrc`, historique, complétion | `say $(date)` |
| 6 | Mode script (`if` / `for` / `while`) | `python3 opsh.py script.opsh` |

### Commandes renommées

| Bash | opsh | Type | | Bash | opsh | Type |
|---|---|---|---|---|---|---|
| `cd` | `go` | builtin | | `ls` | `list` | alias |
| `exit` | `quit` | builtin | | `cat` | `show` | alias |
| `pwd` | `path` | builtin | | `cp` | `copy` | alias |
| `echo` | `say` | builtin | | `mv` | `move` | alias |
| `help` | `info` | builtin | | `rm` | `del` | alias |
| `history` | `past` | builtin | | `mkdir` | `newdir` | alias |
| `\|` | `->` | opérateur | | `touch` | `newfile` | alias |

Le builtin `osinfo` affiche `Systèmes d'Exploitation -- UIR/ESIN`.

---

## Exemples d'utilisation

```text
opsh> list
opsh> go ..
opsh> path
opsh> say hello > f.txt            # redirection (écrase)
opsh> say encore >> f.txt          # redirection (ajoute)
opsh> show f.txt
opsh> wc -l < f.txt                # entrée depuis un fichier
opsh> show f.txt -> wc -l          # pipe
opsh> show f.txt -> sort -r -> head -1
opsh> sleep 10 &                   # arrière-plan, affiche le PID
opsh> ps
opsh> NAME=Yahya                   # variable du shell
opsh> say bonjour $NAME
opsh> export PROJET=opsh           # variable d'environnement (héritée par les fils)
opsh> false
opsh> say $?                       # code de sortie : 1
opsh> say il est $(date)           # substitution de commande
opsh> past                         # historique
opsh> osinfo
```

La touche **Tab** complète les commandes et les noms de fichiers. Les flèches haut/bas parcourent l'historique, conservé entre les sessions dans `~/.opsh_history`.

### Fichier de démarrage `~/.opshrc`

Lu au lancement du mode interactif, une commande par ligne (`#` = commentaire) :

```text
# ~/.opshrc
PROJET=opsh
say Bienvenue dans $PROJET
```

### Mode script

```text
for i in 1 2 3
do
  say compteur: $i
done

n=0
while test $n -lt 3
do
  n=$(expr $n + 1)
done

if test -f f.txt
then
  say existe
else
  say absent
fi
```

Une **condition est une commande** : vraie si son code de sortie vaut 0 (`test`, `true`, `false`...). Sont gérés : `if/else/fi`, `for … in … do/done`, `while … do/done`, `break`, `continue`, `; do` / `; then` en fin de ligne, et les jokers (`*.txt`) dans un `for`.

---

## Architecture

```
opsh/
├── README.md
├── report.pdf
├── demo.mp4
└── code/
    ├── opsh.py              programme principal (boucle REPL, execute_line)
    ├── executor.py          fork / exec / wait, pipes, arrière-plan
    ├── shell_builtins.py    builtins et alias
    ├── redirect.py          tokenisation, redirections (dup2)
    ├── expand.py            variables, $(...), export
    ├── script.py            .opshrc et mode script (analyse + arbre)
    ├── signals_handler.py   SIGCHLD (récolte des fils)
    ├── history.py           historique persistant
    ├── completion.py        complétion par Tab (readline)
    ├── state.py             état partagé ($?, $!, variables)
    └── exemples/demo.opsh   script de démonstration
```

**Chaîne de traitement d'une ligne** (`execute_line`) :

```
ligne → expand ($VAR, $?, $(...)) → détection de & → découpage par ->
      → tokenisation (< > >>) → alias → redirections → run_pipeline
```

---

## Concepts du cours mis en œuvre

- **Programme vs processus ; `fork` / `exec` / `wait`** : chaque commande externe est lancée dans un fils (`os.fork`), qui remplace son image par le programme (`os.execvp`) pendant que le père attend (`os.waitpid`).
- **Zombies / orphelins** : un fils terminé non attendu reste zombie. Le gestionnaire `SIGCHLD` récolte les fils en arrière-plan avec `waitpid(-1, WNOHANG)`.
- **Descripteurs 0 / 1 / 2 et redirections** : `os.open` + `os.dup2` branchent un fichier sur stdin/stdout.
- **Pipes comme IPC** : `os.pipe()` relie la sortie d'un fils à l'entrée du suivant. Tous les bouts inutiles sont fermés pour que le lecteur voie la fin du flux (EOF).
- **Signaux** : `Ctrl+C` (SIGINT) interrompt la commande au premier plan sans tuer le shell ; les fils en arrière-plan l'ignorent ; SIGCHLD est bloqué pendant l'attente au premier plan pour ne pas perdre le code de retour.
- **Pourquoi `go` (`cd`) est un builtin** : le dossier courant est propre à chaque processus. Un fils qui ferait `chdir` ne modifierait pas le dossier du shell. Même raison pour `export` et `VAR=valeur`.
- **Environnement** : une variable du shell n'est visible que dans `opsh` ; `export` la copie dans `os.environ`, que les fils héritent à travers `fork` et `exec`.
- **Mode utilisateur vs noyau** : `fork`, `execve`, `waitpid`, `pipe`, `dup2`, `open`, `chdir` sont des appels système ; le shell ne fait que les enchaîner.

---

## Limites connues

- Pas de contrôle de tâches (`jobs`, `fg`, `bg`) — fonctionnalité optionnelle non implémentée.
- Le pipe `->` est détecté dans toute la ligne, même entre guillemets.
- `&` n'est reconnu qu'en fin de ligne ; pas de `;` pour chaîner plusieurs commandes.
- Pas de redirection de l'erreur standard (`2>`).
- Pas de `elif` ; `if`/`for`/`while` sont réservés au mode script (pas en saisie interactive multi-lignes).
- Le texte produit par `$(...)` est ré-analysé : une sortie contenant des guillemets ou des `<`/`>` peut être interprétée.

---

## Livrables

`code/` · `README.md` · `report.pdf` · `demo.mp4`
