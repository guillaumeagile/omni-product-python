# Le harnais de l'atelier

Le harnais est tout ce qui regarde ton code à ta place pendant l'atelier : il compile, vérifie, mesure, et (bientôt)
juge. Ce document dit **ce qui existe aujourd'hui, ce qui viendra, et comment ça s'enchaîne**. Il évolue avec l'atelier :
la section « État » en bas dit toujours où on en est.

Pour le détail de chaque chiffre mesuré, voir [METRIQUES.md](METRIQUES.md). Ici, on parle du dispositif, pas des
chiffres.

## L'idée

Tu fais un **baby step** : un petit changement, une PR. Le harnais répond à trois questions, dans cet ordre :

1. **Est-ce que ça tient debout ?** Le code est propre, typé, et les tests passent. Sinon, rien d'autre ne compte.
2. **Est-ce que c'est mieux ?** Les mesures du code ont-elles bougé dans le bon sens depuis le baby step précédent ?
3. **Est-ce que tu as respecté la règle du tour ?** (à venir) Une règle de design précise doit passer au vert, sans
   en casser d'autres.

Le harnais ne se discute pas dans la PR : ce n'est pas du code que tu modifies. Il est le même pour tout le monde.

## Les quatre étages

### 1. La CI : le sol

Un workflow GitHub Actions (`.github/workflows/ci.yml`) tourne sur chaque PR :

| Étape | Outil | Ce qu'il vérifie |
|---|---|---|
| Installation | `uv sync --locked` | Les dépendances exactes du `uv.lock` |
| Lint | `ruff check` | Hygiène : erreurs, imports, simplifications, nommage |
| Types | `pyright` (mode strict) | Les types sont cohérents |
| Tests | `pytest` | Le comportement n'a pas régressé |

C'est le seul étage **bloquant** aujourd'hui. Un check rouge veut dire « ne pas fusionner », pas « tu as mal joué ».
Le linter est volontairement **permissif** sur le design : il ne doit pas te corriger à ta place (voir le guide de
l'animateur).

Un second job, le **mutation testing** (`mutmut`, périmètre : le modèle), mesure si les tests détectent vraiment les
bugs : on casse le code à petites doses, et on regarde si un test crie. Il est **informatif** : il ne bloque pas.

### 2. Les mesures : le thermomètre

Le paquet `harness/metrics` lit le code du **modèle** et des **services** et sort des chiffres : complexités,
cohésion, couplage. Pas de jugement : des faits, reproductibles (même code, mêmes chiffres).

```bash
uv run python -m harness.metrics                    # tableau résumé
uv run python -m harness.metrics --json rapport.json  # détail par classe
```

Chaque mesure a son outil, ou, quand il n'existe pas de bibliothèque Python reconnue, un calcul maison petit et
testé :

| Mesure | D'où elle vient |
|---|---|
| Complexité cyclomatique, WMC | [radon](https://radon.readthedocs.io/) |
| Complexité cognitive | [cognitive-complexity](https://pypi.org/project/cognitive-complexity/) |
| TCC, LCOM* | calcul maison (module `ast` de Python) |
| Fan-out, CBO | calcul maison (module `ast` de Python) |
| Tokens | [tiktoken](https://github.com/openai/tiktoken), encodage `o200k_base`, sur le code efficace (hors commentaires, docstrings et tests) |
| Style (attributs mutables, affectations, boucles, lambdas) | calcul maison (module `ast` de Python) |

#### La scorecard de chaque PR

À chaque PR, la CI (job **Scorecard**) mesure le code de la PR **et** celui de sa base, puis publie un commentaire :
un tableau avant / après avec le sens de la variation (✅ mieux, ⚠️ moins bien), les tokens modifiés (🤏 Small diff) et
les classes à regarder en premier. Le commentaire est mis à jour à chaque push, pas dupliqué. Le job est
**informatif** : la scorecard guide les tours de refactoring, elle ne bloque rien. Que les chiffres soient mauvais sur
le code de départ est normal : c'est le but de l'atelier de les faire bouger.

```bash
uv run python -m harness.scorecard --base-ref main    # la même scorecard en local
```

Le rapport JSON est fait pour être **comparé** : le harnais ne regarde pas la valeur d'un chiffre, il regarde de combien
il a bougé entre deux baby steps.

### 3. Les règles maison : le détecteur de design (à venir)

Les mesures disent *combien*, pas *quoi*. Les **règles** disent : « ici, cette classe fait telle chose qu'elle ne
devrait pas ». Elles sont propres à l'atelier CUPID : chacune cible un défaut de design précis, laissé exprès dans le
code, que ni `ruff` ni `pyright` ne signalent.

Elles liront le code par son **arbre syntaxique** (module `ast`, éventuellement `tree-sitter`), pas par du texte : on
cherche des structures, pas des mots. Une règle est **rouge** tant qu'il reste des violations, **verte** quand il n'y en
a plus.

La règle du tour est annoncée dans l'énoncé de l'étape ; tu n'as pas à deviner laquelle est visée.

### 4. L'arbitre : le score (à venir)

L'arbitre est un workflow GitHub qui, à chaque PR, fait tourner le harnais sur trois états du code :

- la **base** (la branche de la phase),
- ton **baby step précédent**,
- la **tête** de ta PR.

Il compare les rapports et commente la PR : verdict (accepté ou non), score du round, niveau, badges. Il fait échouer le
check quand la PR n'est pas un vrai baby step : la règle visée n'est pas verte, quelque chose a régressé, ou le harnais
lui-même a été touché.

C'est lui qui transformera les mesures de l'étage 2 en points. Le barème sera dans son commentaire, ligne par ligne.

## Ce que tu peux et ne peux pas faire

- **Tu peux** lancer les mesures en local à tout moment, pour voir où tu en es.
- **Tu ne touches pas** à `harness/`, ni aux workflows : le code d'une PR ne juge pas la PR.
- **Tu n'optimises pas** pour les chiffres. Si un chiffre baisse parce que tu as fabriqué du code bizarre, tu as
  trompé le thermomètre, pas amélioré le code.

## État

> À mettre à jour à chaque évolution du harnais (nouvelle règle, nouvelle mesure, nouveau seuil).

| Étage | État |
|---|---|
| CI (ruff, pyright, pytest) | ✅ en place, bloquant |
| Mutation testing (modèle) | ✅ en place, informatif |
| Mesures : complexités cyclomatique et cognitive, WMC | ✅ en place (`harness/metrics`) |
| Mesures : TCC, LCOM*, fan-out, CBO | ✅ en place (`harness/metrics`) |
| Mesures : tokens, métriques « style » (champs mutables, affectations, boucles, lambdas) | ✅ en place (`harness/metrics`) |
| Scorecard par PR (commentaire publié par la CI) | ✅ en place, informatif |
| Règles de design maison | ⏳ à faire |
| Arbitre (verdict, score, badges, classement) | ⏳ à faire |
| Règles plus dures (seuils bloquants) | ⏳ à faire |

## Historique des durcissements

Les règles deviendront plus dures au fil des phases. On note ici chaque durcissement, pour que personne ne le découvre
par surprise.

| Date | Changement |
|---|---|
| 2026-11-11 | Les tokens ne comptent que le code efficace (ni commentaires, ni docstrings, ni tests) |
| 2026-11-11 | Tokens, métriques de style et scorecard par PR (informative) |
| 2026-11-11 | Première version : CI, mutation testing, mesures de complexité, cohésion et couplage |
