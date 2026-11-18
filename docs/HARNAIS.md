# Le harnais de l'atelier

Le harnais regarde ton code à ta place pendant l'atelier : il compile, vérifie, mesure et juge. Il est le même pour
tout le monde et tu n'y touches pas.

## L'idée

Tu fais un **baby step** : un petit changement, une PR. Le harnais répond à trois questions, dans cet ordre :

1. **Est-ce que ça tient debout ?** Le code est propre, typé, et les tests passent. Sinon, rien d'autre ne compte.
2. **Est-ce que c'est mieux ?** Les mesures du code ont bougé dans le bon sens depuis le baby step précédent.
3. **Est-ce que tu as respecté la règle du tour ?** Une règle de design précise passe au vert, sans en casser d'autres.
   La règle du tour est annoncée dans l'énoncé de l'étape.

## Les étages

### 1. La CI : le sol

Un workflow GitHub Actions tourne sur chaque PR : `ruff` (hygiène), `pyright` en mode strict (types) et `pytest`
(comportement). Un check rouge veut dire « ne pas fusionner ». Il ne juge pas ton design : le linter reste volontairement
permissif là-dessus.

Un second job, le **mutation testing** (`mutmut`, sur le modèle), casse le code à petites doses et regarde si un test
crie. Il est informatif.

### 2. Les mesures : le thermomètre

Le paquet `harness/metrics` lit le modèle et les services et sort des chiffres : complexités, cohésion, couplage,
tokens, style (champs mutables, affectations, boucles, lambdas). Ce sont des faits reproductibles. Le détail de chaque
chiffre est dans [METRIQUES.md](METRIQUES.md).

```bash
uv run python -m harness.metrics                      # tableau résumé
uv run python -m harness.metrics --json rapport.json  # détail par classe
```

À chaque PR, le job **Scorecard** mesure ton code et celui de sa base, puis commente la PR : un tableau avant / après
(✅ mieux, ⚠️ moins bien), les tokens modifiés et les classes à regarder en premier. Le commentaire est
mis à jour à chaque push. Le job est informatif. Les chiffres sont mauvais au départ, et l'atelier sert à les faire
bouger.

```bash
uv run python -m harness.scorecard --base-ref main    # la même scorecard en local
```

### 3. Les règles : le détecteur de design

Les mesures disent *combien*. Les **règles** disent *quoi* : « cette classe fait telle chose qu'elle ne devrait pas ».
Chacune cible un défaut de design précis que ni `ruff` ni `pyright` ne signalent. Elles lisent l'arbre syntaxique du code
(module `ast`), pas le texte.

Une règle est **rouge** tant qu'il reste des constats, **verte** quand il n'y en a plus. Chaque constat s'affiche au
format de ruff : `chemin:ligne:colonne: CODE message`. La liste des règles, leurs codes et leur état se trouvent dans
le tableau « Règles Python » de [python-regles-de-harnais.md](python-regles-de-harnais.md).

```bash
uv run python -m harness.rules                        # les constats de chaque règle
```

La scorecard affiche les règles en tête, avec leurs points : +10 par règle passée au vert, +5 pour un vrai baby step.
Elle ajoute aussi, pour chaque métrique marquée dans la scorecard, son chiffre de variation, compté dans le sens « mieux »
de la métrique : une hausse de complexité retranche ses points, une baisse les ajoute. Chaque métrique est plafonnée à ±15.
Une PR vide perd 5 points.

### 4. L'arbitre : le score (à venir)

Un workflow GitHub comparera trois états du code : la base, ton baby step précédent et la tête de ta PR. Il commentera
la PR avec un verdict, le score du round et le niveau. Le barème sera dans son commentaire, ligne par ligne.

## Ce que tu peux et ne peux pas faire

- **Tu peux** lancer les mesures et les règles en local à tout moment, pour voir où tu en es.
- **Tu ne touches pas** à `harness/`, ni aux workflows : le code d'une PR ne juge pas la PR.
- **Tu n'optimises pas** pour les chiffres. Un chiffre qui baisse grâce à du code bizarre trompe le thermomètre sans
  améliorer le code.
