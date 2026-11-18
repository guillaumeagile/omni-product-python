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
- `docs/ubiquitous-language.json` : le vocabulaire du domaine. Tu le lis, tu ne le modifies pas.
- Le code et les tests métier : `src/` et `tests/`, exclure `tests/harness/`.

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

## Le nom de la branche : il désigne l'équipe

Le jeu se joue par équipe. Le classement lit l'équipe et la règle dans le nom de la branche :

```text
<equipe>/regle-<N>-<slug>
```

- `<equipe>` : le nom de ton équipe, le même sur toutes ses branches (lettres, chiffres, `-`, `_`). Exemple : `rouges`.
- `<N>` : le numéro de la règle travaillée, celui de `docs/python-regles-de-harnais.md`.
- `<slug>` : quelques mots en kebab-case. Exemple : `rouges/regle-3-modele-riche`.

Une branche hors convention ne rapporte aucun point à l'équipe. Si l'humain ne t'a pas donné le nom de l'équipe, tu
le lui demandes avant de créer la première branche.

Le score d'une PR est le total de sa scorecard. Le score de l'équipe est la somme de ses PR ouvertes. Le classement
de toutes les équipes est dans l'issue épinglée « Classement de l'atelier CUPID ».

## La chaîne de branches : chaque branche part de la précédente

- La première branche de l'équipe part de `main`.
- Chaque branche suivante part de la branche précédente de l'équipe. Les branches s'enchaînent : chacune contient
  le travail de la précédente.
- La base de la PR d'une branche est la branche précédente de l'équipe.
- Les constats et la scorecard se calculent contre la branche précédente : `--base-ref origin/<branche-précédente>`.
  À partir de la deuxième branche, la référence de comparaison est toujours la branche précédente.
- Le diff d'une PR ne montre donc que la règle qu'elle traite.

## La boucle : une PR par règle

1. Une PR par règle, sur une branche qui suit la convention ci-dessus. Son titre nomme la règle : « Team T >> Règle N :  … ». T est le nom de ton équipe car le jeu se joue en groupe. Le score est celui de l'équipe (et l'agent en fait partie)
2. La base de la PR : `main` pour la première PR de l'équipe, la branche précédente de l'équipe pour toutes les suivantes (voir la section ci-dessus).
3. Une itération :
   a. Lance `uv run python -m harness.rules` et `uv run python -m harness.scorecard --base-ref origin/<branche-précédente>`
   (`origin/main` pour la première PR), puis lis les constats.
   b. Lis la fiche de la règle dans `docs/python-regles-de-harnais.md`.
   c. Propose à l'humain deux ou trois options. Pour chacune : la lettre CUPID visée, les fichiers touchés, les tests à adapter.
   d. Attends sa réponse. Tu ne codes rien avant.
   e. Code le choix retenu et lance les tests locaux utiles.
   f. Committe. Le message donne le nombre de constats avant et après, et le choix retenu en une ligne.
   g. Pousse sans force-push. Suis la CI avec `gh pr checks`, puis le commentaire Scorecard et le classement. Le score de mutation testing est à surveiller aussi. et bien évidemment que les tests doivent rester au vert.
4. Recommence l'itération tant que la règle a des constats ou que la CI est rouge.
5. Fin : la règle n'a plus de constats, la CI est verte et l'humain valide. Personne ne fusionne. Tu ne fusionnes pas. les PR restent volontairement ouvertes: c'est pour garder les scores de chaque équipe à chaque étape.

## Comment poser la question

- En session directe : utilise `AskUserQuestion`, une question par décision, deux à quatre options.
- En session de fond : termine ton message par une ligne `needs input:` qui énonce la décision attendue.

## Ce que tu ne fais jamais

- Fusionner une PR, pousser en force, pousser sur `main`.
- Regrouper deux règles dans une même PR.
- Optimiser un chiffre de métrique au détriment de la lecture du code.

## Ce que tu peux faire
- Evaluer la perplexité du LLM face au nouveau code écrit (suite au refactoring). C'est la libre appréciation du LLM. 
