# Règles de harnais pour atelier Python

## Les principes ✅

On se base sur **CUPID** (Composable, Unix, Predictable, Idiomatic, Domain-based) : *comment le code est construit*.
Voir [`POURQUOI-CUPID.md`](POURQUOI-CUPID.md).

On a ajouté une colonne **CUTE** ([`cute-ddd.md`](../slides/markdown/cute-ddd.md)) qui les complète. Elle s'écrit
en emojis pour ne pas confondre ses C et U avec ceux de CUPID :

- 🗺️ Contextual,
- 🗣️ Ubiquitous,
- 🧪 Testable,
- 📖 Expressive.

CUTE dit *ce que le code apporte à l'équipe*. Les jauges CUTE, calculées à partir des règles et des métriques, sont
décrites dans [`CUTE.md`](CUTE.md).

- **Les métriques sont le thermomètre, les règles sont les portes.** La scorecard montre le mouvement, la règle dit
  quand une étape est franchie.
- **Chaque règle dit le refactoring attendu** et comment vérifier qu'il a eu lieu.
- **Du stratégique avant le tactique.** L'atelier porte d'abord sur des choix de découpage (DDD stratégique), puis sur
  des focus tactiques courts (ADT, immutabilité).

## Les 10 règles

| # | Règle (la question) | CUPID | Aussi | CUTE | Refactoring attendu | Comment on vérifie |
|---|---|:-:|:-:|:-:|---|---|
| 1 | Chaque classe parle-t-elle d'**un seul contexte borné** ? | **U** | D, C | 🗺️ | Éclater `Product` en classes par contexte (Catalog, Pricing, Storage, Supplier, Transport). Les liens passent par des identifiants. | `ast` + [`ubiquitous-language.json`](ubiquitous-language.json). En appui : LCOM*, WMC et CBO. |
| 2 | Tout type du domaine est-il **une entité (identifiant obligatoire) ou un Value Object** ? | **D** | P, U | 🗣️ | Classer chaque classe du modèle dans l'une des deux familles.<br>**Entité :** un champ `id` d'un type dédié (`ProductId`, pas `str`).<br>**Value Object :** `dataclass(frozen=True)`, sans identité.<br>Les primitives du domaine (`price`, `slug`, `quantity`) deviennent des Value Objects. Une entité en référence une autre par son identifiant. | `ast` : chaque classe du modèle est un Value Object (frozen, sans `id`) ou une entité (`id` typé dédié), et rien d'autre. Un membre dont le nom relève de l'ubiquitous language, typé par une primitive brute, est signalé. |
| 3 | Le modèle **ignore-t-il le stockage** ? | **D** | P, C | 🧪 | Sortir SQLAlchemy du modèle. Le mapping vit dans `dal/` et se branche de l'extérieur. Le choix de base devient un détail remplaçable. | `ast` : aucun import `sqlalchemy` ni `omni_product.database` sous `anemic_model/`. Test : instancier une entité sans session. |
| 4 | Les variantes sont-elles **composées** et non héritées ? | **C** | P, D | 📖 | `PerishableProduct(Product)` et `NonExpiringProduct(Product)` deviennent `ShelfLife = Perishable \| NonExpiring`. `Product` porte un `shelf_life`. | `ast` : aucune classe du modèle n'hérite d'une autre (Enum, Protocol, Exception et TypedDict exceptés), pas d'`isinstance` sur les variantes. |
| 5 | Un échec métier est-il **une valeur** ? | **P** | C, D | 📖 | Un `raise` métier devient un résultat. Exemple : `withdraw` rend `Withdrawn \| InsufficientStock`. | `ast` : aucun `raise` dans `domain/model/` et `anemic_model/` (`service/` est hors périmètre). Pyright : `match` exhaustif sur le résultat. |
| 6 | Les **effets impurs** sont-ils expulsés du cœur ? | **P** | C, D | 🧪 | Heure, aléatoire, UUID, fichiers, réseau et base sortent du cœur du domaine. Le cœur les reçoit en paramètre, ou par un port nommé dans le métier (`Clock`, `IdGenerator`) qu'on injecte. Le cœur devient pur et ses tests se font avec de simples faux, sans `patch`. | `ast` : `anemic_model/` n'appelle pas `date.today`, `datetime.now`, `time.time`, `uuid4`, `random.*`, `open`, `print`, ni `requests` ou `httpx`. Les tests n'utilisent ni `patch` ni `freezegun`. |
| 7 | **Un état illégal est-il impossible à construire ?** | **P** | D, C | 📖 | Remplacer les combinaisons incohérentes (drapeaux, `None` qui vont par paires) par un ADT : une union fermée de dataclasses frozen. Exemple : `Perishable(sell_by, use_by)` ou `NonExpiring(best_before)`. L'invariant (`sell_by <= use_by`) est validé par une fabrique qui rend un résultat. | `ast` : pas de champ booléen `is_*` ou `has_*` stocké, pas de plusieurs champs `X \| None` qui vont ensemble. Pyright : `match` exhaustif sur l'ADT. |
| 8 | Le code s'écrit-il avec **les idiomes courants de Python** ? | **I** | P, U | 📖 | Remplacer les formes héritées d'autres langages par les formes que Python recommande : les boucles qui remplissent une liste deviennent des compréhensions, les chaînes de `if` un `match` ou une table, les retours anticipés remplacent l'imbrication. Chaque branche en moins fait baisser la complexité cyclomatique. | ruff durci (`PERF`, `C4`, `SIM`, `UP`, `C90`), sans code maison : `PERF401` repère la boucle qui remplit une liste. En appui, sur la scorecard : `boucles`, complexités cyclomatique et cognitive. |
| 9 | Le code va-t-il **plus loin vers le fonctionnel, jusqu'au ROP** (II) ? | **II** | P, U | 📖 | Écrire en Railway Oriented Programming, du service au controller : chaque étape rend un `Result`, les étapes s'enchaînent avec `.map`, `.and_then` et `.map_err`, sans `if` ni `try` entre elles, et un `match` exhaustif termine le chemin à la frontière. Une petite `lambda` sert d'étape sur les rails. Les accumulateurs deviennent `sum`, `any`, `all` ou `reduce`. Le style rejoint celui de Rust, Java, C# et Kotlin. | `ast` maison sur tout `omni_product/`, controllers et services compris : bascule à la main sur un `Result` (`SF001`), `unwrap` (`SF002`), `try` (`SF003`), accumulateur dans une boucle (`SF004`), `raise` hors du modèle (`SF005`). En appui, sur la scorecard : `lambdas sur les rails`. |
| 10 | Les dépendances **pointent-elles vers le cœur** (architecture en oignon, ports et adaptateurs) ? | **C** | P | 🧪 | Sortir de l'architecture en couches `controller → service → dal → base`. Le cœur (modèle et cas d'usage) ne connaît que des **ports**, des `Protocol` écrits dans le langage du métier (`ProductRepository`, `Clock`). Les **adaptateurs** (FastAPI, SQLAlchemy) sont à l'extérieur, implémentent les ports, et sont branchés à un seul endroit (la composition root). Le `dal/` disparaît au profit d'adaptateurs. | `import-linter` : contrats de couches (le cœur n'importe ni `controller`, ni `dal`, ni `infrastructure`, ni `fastapi`, ni `sqlalchemy`). Test : les cas d'usage se testent avec des faux en mémoire, sans base ni HTTP. |

## Règles Python

Les participants voient la règle par son numéro et par son code de diagnostic (`CB001`, `EV002`…). Ce tableau relie
les deux. Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.

| # | Nom court | Code | CUPID | Phase | État dans le harnais |
|---|---|---|:-:|---|---|
| 1 | Contexte borné | `CB001` (`CB002` : mots hors ubiquitous language, hors points) | **U** | 1, stratégique | ✅ en place (`harness/rules/contexte_borne.py`) |
| 2 | Entité ou Value Object | `EV001`, `EV002` | **D** | 1, stratégique | ✅ en place (`entite_valeur.py`) |
| 3 | Pas de modèle anémique | `MA001` | **D** | 1, stratégique | ✅ en place (`modele_anemique.py`) |
| 4 | Composition plutôt qu'héritage | `HE001` | **C** | 2, tactique | ✅ en place (`heritage.py`) |
| 5 | Un échec métier est une valeur | `FV001` | **P** | 2, tactique | ✅ en place (`echec_valeur.py`) |
| 6 | Effets impurs hors du cœur | `EI001` (modèle), `EI002` (tests) | **P** | 2, tactique | ✅ en place (`effet_impur.py`) |
| 7 | État illégal impossible à construire | `EL001`, `EL002` | **P** | 2, tactique | ✅ en place (`etat_illegal.py`) |
| 8 | Idiomes courants de Python | ruff (`PERF`, `C4`, `SIM`, `UP`, `C90`) | **I** | 2, tactique | ✅ en place (`idiomes.py`, ruff, sans code maison) |
| 9 | Style fonctionnel et ROP (II) | `SF001` à `SF005` | **II** | 2, tactique | ✅ en place (`style_fonctionnel.py`), rouge sur le legacy |
| 10 | Architecture en oignon | `AO001`, `AO002` | **C** | 3, aboutissement | ✅ en place (`architecture_oignon.py`), rouge sur le legacy |

Le numéro de la règle est celui du tableau « Les 10 règles » plus haut, qui donne la question, le refactoring attendu et
la vérification. Les préfixes des codes viennent du nom de la règle : **C**ontexte **B**orné, **E**ntité **V**aleur,
**M**odèle **A**némique, **H**éritag**E**, **F**ailure **V**alue (l'échec valeur), **E**ffet **I**mpur, **E**tat **L**égal (`EI` étant pris), **S**tyle **F**onctionnel.

## Stratégique, puis tactique (DDD, all the way)

- **Phase 1, stratégique : règles 1, 2, 3.** Les participants choisissent une stratégie, et chacune déclenche les
  mêmes règles dans un ordre différent :
  - **par contexte :** couper `Product` par contexte borné (règle 1).
  - **par langage :** commencer par les types du domaine (règle 2).
  - **par stockage :** commencer par isoler SQLAlchemy (règle 3).

  La scorecard montre ce que chaque chemin a coûté. Le débrief compare les trois : c'est là que se trouve la leçon.
- **Phase 2, tactique : règles 4 à 9.** Des focus courts (ADT, échecs en valeurs, effets, idiomes) sur du code déjà
  bien découpé.
- **Règle 10, l'aboutissement** : elle réorganise tout le projet, donc elle vient en dernier (phase 3), une fois le
  cœur bien découpé et pur. ❓ à confirmer.

## Les ADT en Python : la bibliothèque retenue

**Décision : [`result`](https://github.com/rustedpy/result) 0.17.0** (dépendance du projet). Un résultat est `Ok` ou
`Err`, pyright signale l'oubli d'un cas dans un `match`, et les étapes s'enchaînent avec `.map`, `.and_then` et
`.map_err` (Railway Oriented Programming). Le comparatif et ses limites sont dans l'[annexe](#annexe--comparatif-des-bibliothèques-adt).

## Annexe : comparatif des bibliothèques ADT

Test dans un projet jetable, avec pyright, en supprimant un cas du `match` pour voir si l'oubli est signalé.
Mesures de performance dans [POURQUOI-CUPID.md](POURQUOI-CUPID.md).

| Critère | `result` (retenue) | `returns` | `expression` | Maison (union de dataclasses) |
|---|---|---|---|---|
| Oubli signalé par pyright | oui | non (`Result` n'est pas une union fermée pour lui) | ❓ | oui |
| Chaînage ROP | `.map`, `.and_then`, `.map_err` | `bind`, `flow` (le plus proche de Wlaschin) | pipe | à écrire, une vingtaine de lignes |
| Performance | parmi les plus rapides | un peu plus lente | la plus lente (1,3 µs pour construire une erreur) | celle d'un `NamedTuple` |
| Motifs `match` | `Ok(valeur)`, `Err(erreur)` | riches, mais prévus pour mypy | peu naturels (`Some` est une fonction) | naturels |
| Maintenance | à surveiller à chaque montée de version | à vérifier | à vérifier | notre code |

**Pourquoi `result`.** C'est la seule qui cumule le `match` exhaustif et la vitesse, et qui permet le ROP. `returns`
donne le ROP le plus riche, mais sans l'oubli signalé, ce qui retire l'intérêt principal du style. La solution maison
reste le repli si `result` cesse d'être maintenue : elle ne demande aucune dépendance.
