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

## Commandes

```bash
uv sync                                          # installe les dépendances (.venv)
uv run ruff check . && uv run ruff format --check .   # lint + format
uv run pyright                                   # types (mode strict)
uv run pytest                                    # tests
uv build                                         # wheel + sdist dans dist/
uv run uvicorn omni_product.main:app --reload    # lance l'API (http://localhost:8000/docs)
```
