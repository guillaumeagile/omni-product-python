# omni-product (port Python)

Port de `omni-product-spring-boot-java-bdxio-phase1` : FastAPI + SQLAlchemy 2 + SQLite en mémoire.

| Java | Python |
|---|---|
| Spring Boot / MVC | FastAPI |
| JPA / Hibernate | SQLAlchemy 2.0 (`@Embeddable` → `composite`, `@ElementCollection` → tables enfants + `association_proxy`) |
| Spring Data `JpaRepository` | couche DAL à l'ancienne : fonctions `*_dal.py` prenant la Session SQLAlchemy |
| H2 | SQLite en mémoire |
| RestTemplate | httpx |
| Jackson | Pydantic (JSON en camelCase) |
| JUnit / AssertJ / MockMvc | pytest / `TestClient` |

## Le jeu : l'atelier CUPID

Les équipes refactorent ce code règle après règle, guidées par le harnais. Chaque PR gagne ou perd des points.
Le classement des équipes se met à jour à chaque push.

### Règles du jeu

1. **Une équipe, un nom.** Choisissez un nom court (`rouges`, `team-gip`…) et gardez-le sur toutes vos branches.
2. **Une PR par règle.** La branche s'appelle `<equipe>/regle-<N>-<slug>`, par exemple
   `rouges/regle-3-modele-riche`. `<N>` est le numéro de la règle dans `docs/python-regles-de-harnais.md`.
   Une branche hors convention ne compte pas au classement.
3. **Les PR s'enchaînent.** La première PR de l'équipe part de `main` et vise `main`. Les suivantes partent de la
   branche de l'étape précédente et la visent. Chaque PR est notée par rapport à sa base.
4. **Le titre** nomme l'équipe et la règle : « Team rouges >> Règle 3 : … ».
5. **Personne ne fusionne.** Les PR restent ouvertes jusqu'à la fin de l'atelier : elles portent le score de l'équipe.
6. **Le harnais est hors jeu.** Une PR qui touche `harness/`, `tests/harness/` ou `docs/ubiquitous-language.json`
   est bloquée par la garde.

### Où lire son score

- **Le commentaire Scorecard** de la PR : règles du harnais, métriques, et le **Total** des points de la PR.
- **L'issue épinglée « Classement de l'atelier CUPID »** : le score de chaque équipe, somme des totaux de ses PR
  ouvertes, et le détail par PR.

Avant de pousser, lancez le harnais en local :

```bash
uv run python -m harness.rules                                  # constats règle par règle
uv run python -m harness.scorecard --base-ref origin/<base>     # la scorecard de la PR
```

Les consignes pour un agent qui joue avec l'équipe sont dans `AGENTS.md`.

## Première installation (macOS ou Windows)

Le projet demande Python 3.13 ou plus récent. `uv` installe Python à votre place : c'est le chemin recommandé.

### 1. Installer uv

- **macOS avec Homebrew** : `brew install uv`
- **macOS ou Linux sans Homebrew** : `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows (PowerShell)** : `winget install astral-sh.uv`

Ouvrez ensuite un nouveau terminal et vérifiez : `uv --version`.

### 2. Installer Python 3.13

```bash
uv python install 3.13
```

uv télécharge Python 3.13 dans son propre dossier. Votre Python système n'est pas modifié.

Vous préférez installer Python vous-même ? Installez Python 3.13 ou plus avant l'étape 3 :

- **macOS** : `brew install python@3.13`, ou l'installeur sur python.org.
- **Windows** : `winget install Python.Python.3.13`, ou l'installeur sur python.org. Cochez « Add python.exe to PATH ».

uv utilise alors ce Python installé.

### 3. Cloner le projet et installer les dépendances

```bash
git clone <url-du-depot>
cd python-omni-product
uv sync
```

`uv sync` crée le dossier `.venv` et y installe les dépendances. Vous n'avez pas besoin d'activer `.venv` : `uv run` s'en charge.

### 4. Vérifier l'installation

```bash
uv run pytest                                    # les tests doivent passer
uv run uvicorn omni_product.main:app --reload    # lance l'API
```

Ouvrez ensuite http://localhost:8000/docs dans le navigateur.

### En cas de problème

- **`uv: command not found`** : fermez le terminal, ouvrez-en un nouveau, puis relancez la commande. Sous Windows, relancez PowerShell.
- **PowerShell refuse d'exécuter le script d'installation de uv** : lancez d'abord
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, puis recommencez l'étape 1.
- **Python 3.13 introuvable** : relancez `uv python install 3.13`, ou vérifiez l'installation manuelle de l'étape 2.

## Commandes

```bash
uv sync                                          # installe les dépendances (.venv)
uv run ruff check . && uv run ruff format --check .   # lint + format
uv run pyright                                   # types (mode strict)
uv run pytest                                    # tests
uv build                                         # wheel + sdist dans dist/
uv run uvicorn omni_product.main:app --reload    # lance l'API (http://localhost:8000/docs)
```
