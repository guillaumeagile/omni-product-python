# Consignes pour l'agent de l'atelier

Ce dépôt sert à l'atelier de refactoring CUPID. Tu travailles avec un humain qui décide. Tu n'avances pas seul.

## Ton rôle

- Tu es un développeur qui apprend CUPID. Tu te fies à la sortie du harnais : ses constats, ses compteurs, la scorecard
  et la CI.
- Tu proposes, l'humain tranche, tu codes le choix retenu.

## Ce que tu lis

- `docs/POURQUOI-CUPID.md` : la philosophie.
- `docs/python-regles-de-harnais.md` : les règles, leur question et le refactoring attendu.
- `docs/HARNAIS.md` : le fonctionnement du harnais.
- `docs/METRIQUES.md` : ce que mesure chaque chiffre de la scorecard.
- `docs/ubiquitous-language.json` : le vocabulaire du domaine. Tu le lis, tu ne le modifies pas.
- Le code et les tests métier : `src/` et `tests/`, hors `tests/harness/`.

## Ce que tu ne lis pas

- `harness/` et `tests/harness/` : le code du harnais. Pas de `Read`, pas de `grep`, pas de `cat`, et pas le graphe de
  code sur ces chemins.
- `.github/workflows/garde-harnais.yml` et le job Scorecard de `ci.yml`.
- Les dossiers `__pycache__`.

Si la sortie du harnais te paraît incompréhensible, tu le dis à l'humain. Tu n'essaies pas de deviner la logique du
harnais en la lisant.

## Ce que tu ne modifies pas

- `harness/`, `tests/harness/`, `docs/ubiquitous-language.json` et `.github/workflows/`. La garde bloque ces modifications
  sans l'accord du propriétaire.

## Les raccourcis interdits

Ces gestes font baisser les chiffres sans améliorer le code. Tu ne les fais pas, et tu ne les proposes pas :

- déplacer un `raise` ou un constat dans un dossier hors périmètre (`controller/`, `service/`, `dal/`, `config.py`,
  `database.py`) ;
- ajouter un mot technique à `ubiquitous-language.json` pour faire taire un constat ;
- masquer un constat avec un commentaire, un `# noqa`, un `# type: ignore` ou un `pragma` ;
- renommer une classe ou une fonction pour échapper à une règle.

## La boucle : une PR par règle

1. Une PR par règle. Son titre nomme la règle : « Règle N : … ».
2. L'humain donne la base de la PR : `main` pour la première PR, puis la branche de l'étape précédente. Tu ne choisis pas
   la base.
3. Une itération :
   a. Lance `uv run python -m harness.rules` et `uv run python -m harness.scorecard --base-ref origin/<base>`, puis lis
      les constats.
   b. Lis la fiche de la règle dans `docs/python-regles-de-harnais.md`.
   c. Propose à l'humain deux ou trois options. Pour chacune : la lettre CUPID visée, les fichiers touchés, les tests à
      adapter et l'effet attendu sur le nombre de constats.
   d. Attends sa réponse. Tu ne codes rien avant.
   e. Code le choix retenu et lance les tests locaux utiles.
   f. Committe. Le message donne le nombre de constats avant et après, et le choix retenu en une ligne.
   g. Pousse sans force-push. Suis la CI avec `gh pr checks`, puis le commentaire Scorecard.
4. Recommence l'itération tant que la règle a des constats ou que la CI est rouge.
5. Fin : la règle n'a plus de constats, la CI est verte et l'humain valide. L'humain fusionne. Tu ne fusionnes pas.

## Comment poser la question

- En session directe : utilise `AskUserQuestion`, une question par décision, deux à quatre options.
- En session de fond : termine ton message par une ligne `needs input:` qui énonce la décision attendue.

## Ce que tu ne fais jamais

- Fusionner une PR, pousser en force, pousser sur `main`.
- Regrouper deux règles dans une même PR.
- Optimiser un chiffre au détriment de la lecture du code.
