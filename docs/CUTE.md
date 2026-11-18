# Les jauges CUTE

> **État :** conception validée, à coder dans le harnais (`harness/cute.py`). Ce document décrit le calcul. Le code
> suivra sur une branche, avec ses tests.

## Pourquoi des jauges

La scorecard affiche 16 lignes de métriques, 10 règles, des badges et un tableau de couches. Chaque chiffre est juste.
Pour qui découvre le harnais, la question reste : lequel regarder ?

CUTE (voir [`POURQUOI-CUPID.md`](POURQUOI-CUPID.md#cute--la-lettre-qui-manque) et la slide
[`cute-ddd.md`](../slides/markdown/cute-ddd.md)) pose quatre questions simples. Le harnais y répond par quatre jauges
de 0 à 100, calculées à partir des règles et des métriques qu'il a déjà. Les jauges s'affichent en tête du commentaire
de la PR. Le détail reste disponible, replié en dessous.

| Jauge | La question |
|:-:|---|
| 🗺️ Contextual | Chaque classe sait-elle dans quel contexte elle vit ? |
| 🗣️ Ubiquitous | Le code parle-t-il la langue du métier ? |
| 🧪 Testable | Peut-on tester le cœur sans base, sans patch, avec peu de cas ? |
| 📖 Expressive | Le code dit-il l'intention métier ? |

## Le principe : le chemin parcouru

Une jauge dit **quelle part du chemin est faite** depuis le code legacy. Le legacy vaut 0. Une règle verte vaut 100.

Pour une règle *n*, la part faite vaut :

```
R(n) = 1 − constats_aujourd'hui / constats_du_legacy      bornée entre 0 et 1
```

Les constats du legacy sont figés une fois, dans un fichier de référence du harnais. La jauge ne bouge donc pas quand
la base de la PR change : elle raconte toute la progression de l'atelier. Une règle sans constat au départ vaut 1.

Les métriques déjà comprises entre 0 et 1 (la métrique Uncle Bob D, le score de mutation) entrent telles quelles. Les
autres passent par un seuil fixe, écrit dans la formule.

Les poids sont ronds pour rester faciles à expliquer à voix haute.

## 🗺️ Contextual

```
C = 0.6 × R1  +  0.4 × (1 − D)
```

| Ingrédient | Source | Ce qu'il dit |
|---|---|---|
| R1 | règle 1, `CB001` | Une classe touche plusieurs contextes bornés. |
| D | métrique Uncle Bob (D moyen des couches) | Les couches sont-elles à leur place sur la séquence principale ? |

**Plafond.** Tant que la ligne « Violations du sens des dépendances » est au-dessus de 0, C est plafonnée à 50. Une
flèche à l'envers casse les frontières, quel que soit le reste.

**Écartées.** TCC et LCOM valent déjà 1,0 et 0,0 sur le legacy : les classes anémiques n'ont pas de méthodes. Elles ne
départagent rien et restent dans le détail.

## 🗣️ Ubiquitous

```
U = 0.5 × R2  +  0.5 × Couverture_UL
```

| Ingrédient | Source | Ce qu'il dit |
|---|---|---|
| R2 | règle 2, `EV001` et `EV002` | Une classe n'est ni entité ni Value Object, ou un mot du métier est typé par une primitive brute (`price: float`). |
| Couverture_UL | règle 1, classement des membres | La part des membres publics que le glossaire rattache à un contexte. |

**Couverture_UL** est le seul calcul nouveau. Il utilise ce que `contexte_borne.py` sait déjà :

```
Couverture_UL = membres publics rattachés à un contexte / membres publics non génériques
```

Un membre non générique contient au moins un mot absent des `genericWords` de
[`ubiquitous-language.json`](ubiquitous-language.json). Les membres non rattachés sont les constats `CB002`, les mots
hors du langage.

## 🧪 Testable

```
T = 0.4 × Mutation  +  0.3 × moyenne(R3, R6, R10)  +  0.3 × Simplicité

Simplicité = (10 − CC_max) / 6,  bornée entre 0 et 1
```

| Ingrédient | Source | Ce qu'il dit |
|---|---|---|
| Mutation | score mutmut de la CI | Les tests crient-ils quand on casse le code ? |
| R3 | règle 3, `MA001` | Le modèle a quitté `anemic_model/` et SQLAlchemy. |
| R6 | règle 6, `EI001` et `EI002` | Le cœur est pur, et ses tests se passent de `patch`. |
| R10 | règle 10, `AO001` et `AO002` | Le cœur ne dépend que de lui-même : on le teste avec des faux en mémoire. |
| CC_max | complexité cyclomatique max par fonction | Le nombre minimal de tests de la pire fonction. |

Simplicité vaut 1 quand la pire fonction a au plus 4 chemins, et 0 à partir de 10.

**Sans score de mutation** (calcul en local, ou job de mutation absent), son poids se reporte sur les deux autres
termes : `T = 0.5 × moyenne(R3, R6, R10) + 0.5 × Simplicité`. La scorecard l'indique.

## 📖 Expressive

```
E = 0.4 × moyenne(R5, R7)  +  0.3 × moyenne(R4, R8, R9)  +  0.3 × Immuabilité

Immuabilité = 1 − attributs_mutables / attributs_mutables_du_legacy,  bornée entre 0 et 1
```

| Ingrédient | Source | Ce qu'il dit |
|---|---|---|
| R5 | règle 5, `FV001` | Un échec métier est une valeur (`Withdrawn \| InsufficientStock`). |
| R7 | règle 7, `EL001` et `EL002` | Un état illégal est impossible à construire. |
| R4 | règle 4, `HE001` | Les variantes sont des types composés. |
| R8 | règle 8, ruff | Le code suit les idiomes de Python. |
| R9 | règle 9, `SF001` à `SF005` | Les étapes s'enchaînent sur les rails d'un `Result`. |
| Immuabilité | ligne « Attributs mutables » | Un état qui ne change pas se lit d'un coup d'œil. |

R5 et R7 pèsent le plus : ce sont les deux règles où le type raconte le métier. R4, R8 et R9 portent la forme du code.

## Les valeurs de départ

Mesurées sur le legacy (`main`, novembre 2026) :

| Jauge | Calcul | Valeur |
|:-:|---|--:|
| 🗺️ | R1 = 0 (4 constats), D = 0,44 → 0,6 × 0 + 0,4 × 0,56 | **22** |
| 🗣️ | R2 = 0 (8 constats), couverture à mesurer | **0 à 50** |
| 🧪 | R3 = R6 = R10 = 0, CC_max = 7 → Simplicité = 0,5 | **15 + 0,4 × mutation** |
| 📖 | R8 = 1 (déjà verte), le reste à 0 | **10** |

## Ce que verra un participant

```
### 🌈 CUTE
🗺️ Contextual   22 → 41  (+19)   ████░░░░░░
🗣️ Ubiquitous    8 →  8          █░░░░░░░░░
🧪 Testable     31 → 38  (+7)    ████░░░░░░
📖 Expressive   10 → 10          █░░░░░░░░░

▶ Le détail : règles, métriques, couches
```

La première colonne est la base de la PR, la deuxième la PR. Le détail actuel de la scorecard est replié dans un
`<details>`.

## Ce qui reste hors des jauges

- **Tokens, affectations, boucles, lambdas, complexité cognitive.** Ils restent dans le détail. Les ajouter compterait
  deux fois ce que les règles 8 et 9 mesurent déjà.
- **Un score CUTE unique.** Les points de la scorecard jouent déjà ce rôle. Les jauges guident sans noter : elles ne
  rapportent aucun point.

## Le rattachement des règles

| Jauge | Règles | Métriques |
|:-:|---|---|
| 🗺️ | 1 | métrique Uncle Bob, violations du sens des dépendances |
| 🗣️ | 2 (et 1 pour la couverture du langage) | — |
| 🧪 | 3, 6, 10 | score de mutation, complexité cyclomatique max |
| 📖 | 4, 5, 7, 8, 9 | attributs mutables |

Ce tableau suit la colonne CUTE de [`python-regles-de-harnais.md`](python-regles-de-harnais.md).

## L'intégration au harnais (à venir)

1. `harness/cute.py` : les quatre formules, pures, à partir des constats des règles et de `Metrics`.
2. `harness/cute_reference.json` : les constats et les attributs mutables du legacy, figés.
3. La scorecard affiche les jauges en tête et replie le reste.
4. Des tests à réponse connue dans `tests/harness/test_cute.py`.
