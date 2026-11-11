# Règles de harnais pour CUPID : document de travail

> **Statut : brouillon de travail.** Ce document sert à décider quelles règles le harnais appliquera.
> Il est modifié au fil des décisions. Les décisions prises sont marquées ✅, les points
> ouverts ❓.
>
> Documents voisins : [`HARNAIS.md`](HARNAIS.md) (le harnais global), [`METRIQUES.md`](METRIQUES.md) (les chiffres de
> la scorecard).

## Pourquoi on repart de zéro

Le harnais Java avait environ 25 règles (`HA1` à `HA12.1`, `HA4.1` à `HA4.9`). Deux problèmes :

1. **Trop de règles, et le lien avec CUPID se perd.** Beaucoup décrivent une forme de code (HA9 `Identifiable`, HA10
   « pas de service au constructeur », HA4.2 à HA4.9).
   Un participant voit la règle, sans voir pourquoi elle va dans le sens de CUPID.
2. **Les règles se recouvrent**, entre elles (HA5, HA6, HA7 disent toutes « cette classe fait trop de choses ») et
   avec les métriques (le fan-out mesure déjà ce que HA7 interdit, `boucles` ce que HA4.8 interdit).

## Les principes ✅

On connait **CUPID** (Composable, Unix, Predictable,
  Idiomatic, Domain-based) : *comment le code est construit*. 

On a ajouté une colonne **CUTE**
  ([`cute-ddd.md`](../../Cute-KanDDDinsky-2026/slides/markdown/cute-ddd.md)) qui les complète, en emojis pour ne pas
  confondre ses C et U avec ceux de CUPID : 
  - 🗺️ Contextual, 
  - 🗣️ Ubiquitous, 
  - 🧪 Testable, 
  - 📖 Expressive. 
 
CUTE dit *ce que   le code apporte à l'équipe*. 
- **Les métriques sont le thermomètre, les règles sont les portes.** La scorecard montre le mouvement, la règle dit
  quand une étape est franchie.
- **Chaque règle dit le refactoring attendu** et comment vérifier qu'il a eu lieu.
- **Du stratégique avant le tactique.** L'atelier porte d'abord sur des choix de découpage (DDD stratégique), puis sur
  des focus tactiques courts (ADT, immutabilité).

## Les 10 règles

| # | Règle (la question) | CUPID | Aussi | CUTE | Refactoring attendu | Comment on vérifie |
|---|---|:-:|:-:|:-:|---|---|
| 1 | Chaque classe parle-t-elle d'**un seul contexte borné** ? | **U** | D, C | 🗺️ | Éclater `Product` en classes par contexte (Catalog, Pricing, Storage, Supplier, Transport). Les liens passent par des identifiants. | `ast` + [`ubiquitous-language-map.json`](ubiquitous-language-map.json). En appui : LCOM*, WMC et CBO. |
| 2 | Tout type du domaine est-il **une entité (identifiant obligatoire) ou un Value Object** ? | **D** | P, U | 🗣️ | Classer chaque classe du modèle dans l'une des deux familles.<br>**Entité :** un champ `id` d'un type dédié (`ProductId`, pas `str`).<br>**Value Object :** `dataclass(frozen=True)`, sans identité.<br>Les primitives du domaine (`price`, `slug`, `quantity`) deviennent des Value Objects. Une entité en référence une autre par son identifiant. | `ast` : chaque classe du modèle est un Value Object (frozen, sans `id`) ou une entité (`id` typé dédié), et rien d'autre. Un membre du vocabulaire en primitive brute est signalé. |
| 3 | Le modèle **ignore-t-il le stockage** ? | **D** | P, C | 🧪 | Sortir SQLAlchemy du modèle. Le mapping vit dans `dal/` et se branche de l'extérieur. Le choix de base devient un détail remplaçable. | `ast` : aucun import `sqlalchemy` ni `omni_product.database` sous `model/`. Test : instancier une entité sans session. |
| 4 | Les variantes sont-elles **composées** et non héritées ? | **C** | P, D | · | `PerishableProduct(Product)` et `NonExpiringProduct(Product)` deviennent `ShelfLife = Perishable \| NonExpiring`. `Product` porte un `shelf_life`. | `ast` : aucune classe du modèle n'hérite d'une autre (Enum, Protocol, Exception et TypedDict exceptés), pas d'`isinstance` sur les variantes. |
| 5 | Un échec métier est-il **une valeur** ? | **P** | C, D | 📖 | Un `raise` métier devient un résultat. Exemple : `withdraw` rend `Withdrawn \| InsufficientStock`. | `ast` : pas de `raise` métier dans `model/` et `service/`. Pyright : `match` exhaustif sur le résultat. |
| 6 | Les **effets impurs** sont-ils expulsés du cœur ? | **P** | C, D | 🧪 | Heure, aléatoire, UUID, fichiers, réseau et base sortent du cœur du domaine. Le cœur les reçoit en paramètre, ou par un port nommé dans le métier (`Clock`, `IdGenerator`) qu'on injecte. Le cœur devient pur et ses tests se font avec de simples faux, sans `patch`. | `ast` : `model/` n'appelle pas `date.today`, `datetime.now`, `time.time`, `uuid4`, `random.*`, `open`, `print`, ni `requests` ou `httpx`. Les tests n'utilisent ni `patch` ni `freezegun`. |
| 7 | **Un état illégal est-il impossible à construire ?** | **P** | D, C | 📖 | Remplacer les combinaisons incohérentes (drapeaux, `None` qui vont par paires) par un ADT : une union fermée de dataclasses frozen. Exemple : `Perishable(sell_by, use_by)` ou `NonExpiring(best_before)`. L'invariant (`sell_by <= use_by`) est validé par une fabrique qui rend un résultat. | `ast` : pas de champ booléen `is_*` ou `has_*` stocké, pas de plusieurs champs `X \| None` qui vont ensemble, pas de `raise` dans `__init__` ou `__post_init__`. Pyright : `match` exhaustif sur l'ADT. |
| 8 | Le code s'écrit-il avec **les idiomes courants de Python** ? | **I** | P, U | · | Remplacer les formes héritées d'autres langages par les formes que Python recommande : les boucles qui remplissent une liste deviennent des compréhensions, les chaînes de `if` un `match` ou une table, les retours anticipés remplacent l'imbrication. Chaque branche en moins fait baisser la complexité cyclomatique. | ruff durci (`PERF`, `C4`, `SIM`, `UP`, `C90`), sans code maison : `PERF401` repère la boucle qui remplit une liste. En appui, sur la scorecard : `boucles`, complexités cyclomatique et cognitive. |
| 9 | Le code va-t-il **plus loin vers le fonctionnel** (I++) ? | **I** | P, U | · | Pousser le style au-delà de ce que Python impose : `sum`, `any`, `all`, `map`, `filter` et `reduce` à la place des boucles d'accumulation, petits `lambda`, enchaînements fluides sur un `Result` ou un `Option` (`.map`, `.and_then`) à la place des `if` et des `try`. Le style rejoint celui de Rust, Java, C# et Kotlin. | `ast` maison ❓ : pas de boucle `for` qui accumule (`append`, `+=`) dans `model/` et `service/`. En appui, sur la scorecard : `boucles`, `affectations`, `lambdas`. |
| 10 | Les dépendances **pointent-elles vers le cœur** (architecture en oignon, ports et adaptateurs) ? | **C** | P | 🧪 | Sortir de l'architecture en couches `controller → service → dal → base`. Le cœur (modèle et cas d'usage) ne connaît que des **ports**, des `Protocol` écrits dans le langage du métier (`ProductRepository`, `Clock`). Les **adaptateurs** (FastAPI, SQLAlchemy) sont à l'extérieur, implémentent les ports, et sont branchés à un seul endroit (la composition root). Le `dal/` disparaît au profit d'adaptateurs. | `import-linter` : contrats de couches (le cœur n'importe ni `controller`, ni `dal`, ni `infrastructure`, ni `fastapi`, ni `sqlalchemy`). Test : les cas d'usage se testent avec des faux en mémoire, sans base ni HTTP. |

### Notes sur les règles

- **Règle 2 ✅** : elle absorbe l'ancienne règle d'immuabilité. Un Value Object est frozen par définition. La métrique
  `attributs mutables` reste un thermomètre.
- **Règle 3 ✅** : c'est une vraie décision d'architecture. Dans ce port, le modèle **est**
  l'ORM (`Product(Base)`), donc la sortir du modèle coûte cher.
- **Règle 6 ✅** : elle est séparée de la règle 5. Les effets impurs (horloge comprise) sont une préoccupation à part :
  on les expulse du cœur par injection de dépendance pour que le cœur se teste facilement.
- **Règles 4 et 7** : la même union (`ShelfLife`) peut satisfaire les deux, mais ce sont deux questions distinctes.
  La 4 demande de composer au lieu d'hériter. La 7 demande que l'incohérent ne puisse pas se construire.
- **Règle 8 ✅ (I)** : les idiomes que la communauté Python recommande déjà. Ils se vérifient avec ruff, sans code
  maison. Les compréhensions y gagnent sur `map` et `filter` avec un `lambda`.
- **Règle 9 ✅ (I++)** : elle assume un parti pris. Elle va plus loin que la 8, vers le style fonctionnel que l'on
  retrouve en Rust, Java, C# et Kotlin, et que la communauté Python n'adopte pas tout entière. La page
  [`POURQUOI-CUPID.md`](POURQUOI-CUPID.md) (« FP: a New Hope in Idioms ») expose cette divergence. Précision pour
  Python : `reduce` reste rare, car `sum`, `any` et `all` couvrent l'essentiel, et la compréhension reste préférée à
  `map` ou `filter` avec un `lambda` sur une liste. Les `lambda` servent surtout aux enchaînements sur un `Result`.
- **Règle 10 ✅** : elle généralise la règle 3. La règle 3 sort le stockage du modèle, la règle 10 organise tout le
  projet autour du cœur. Le port `domain/port` et l'adaptateur `infrastructure/adapter`, déjà présents pour le
  transport carbone, sont le modèle à reproduire pour le reste. La règle 3 devient donc la première marche de la 10.
- **La testabilité n'est pas une lettre de CUPID ✅** : c'est pourquoi la colonne CUTE a le 🧪. Les règles 3, 6 et 10
  rendent le cœur testable sans base, sans horloge et sans réseau. La règle 10 est **C** côté CUPID (on branche et on
  débranche les adaptateurs) et 🧪 côté CUTE.
- **📖 (Expressive) ❓** : proposé pour les règles 5 et 7 (résultats et ADT qui disent l'intention métier). À
  confirmer.
- **Règle 4 dépend de la règle 3** : tant que le modèle est mappé par SQLAlchemy, supprimer l'héritage oblige à
  toucher au mapping.

## Ce que deviennent les règles Java

| Règle Java | Devenir |
|---|---|
| HA5 (4 propriétés max), HA6 (single concern), HA7 (fan-out) | **Règle 1.** Le fan-out et le CBO restent en métrique. |
| HA11 (concept non primitif), HA12 (identifiants riches), HA12.1, HA9 (`Identifiable`), HA3 (records) | **Règle 2.** « Entité ou Value Object » remplace `Identifiable`, artefact Java. |
| HA8 (pas de persistance) | **Règle 3.** |
| HA4.1 (pas d'héritage), HA4.3 (`Product` porte un ADT) | **Règles 4 et 7.** |
| HA2 (données immuables) | **Règle 2** (Value Objects frozen). |
| HA4.2, HA4.4, HA4.5 (échecs en valeurs, ADT, `switch` exhaustif) | **Règles 5 et 7.** L'exhaustivité est vérifiée par pyright. |
| HA4.6 (horloge), HA10 (pas de service au constructeur) | **Règle 6.** |
| HA1 (idiomes) | **Règle 8.** |
| HA4.8 (pipeline, pas de boucle) | **Règle 9** : idiomes fonctionnels (I++). |
| (aucune : nouveauté de la version Python) | **Règle 10** : architecture en oignon. |
| HA4.7 (retrait après `canSell`), HA4.9 (validation en chaîne) | **Supprimées.** HA4.7 et HA4.9 imposent un style trop précis pour être expliquées en une phrase. |

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

## Les ADT en Python : quelle bibliothèque ❓

Test dans un projet jetable, avec pyright, en supprimant un cas du `match` pour voir si l'oubli est signalé :

| Bibliothèque | Version testée | Résultat |
|---|---|---|
| [`result`](https://github.com/rustedpy/result) | 0.17.0 | `Ok` ou `Err`. Pyright **signale l'oubli** d'un cas. Pas d'`Option`. |
| `returns` | 0.26.0 | Pyright **ne signale pas** l'oubli (`Result` n'est pas une union fermée pour lui). Riche, mais prévue pour mypy. |
| `expression` | 5.8.0 | Complète (`Option`, `Result`), mais ses motifs `match` sont peu naturels (`Some` est une fonction, pas une classe). |

**Piste :** `result` pour les résultats (règles 5 et 7), et de simples **unions de dataclasses frozen** pour tout le
reste, avec la bibliothèque standard. L'absence d'une valeur reste `X | None`.

À vérifier avant de l'imposer : la maintenance de `result` (non vérifiée).

## Points ouverts ❓

1. **Règle 3 (modèle sans stockage)** : en phase 1, ou en bonus réservé à la stratégie « par stockage » ?
2. **Blocage** : ne bloquer que la règle de l'étape en cours, et laisser les autres en avertissement sur la scorecard ?
3. **Règle 2** : garder l'immuabilité fondue dedans, ou la séparer en règle P ?
4. **Bibliothèque d'ADT** : `result` + unions de dataclasses, ou autre chose ?
5. **Règle 7** : les heuristiques `ast` (booléens stockés, `None` par paires) sont-elles assez fiables, ou faut-il
   les accompagner d'un test par propriétés (`hypothesis`) ?
6. **Règle 10** : en phase 3, ou dès la phase 1 comme quatrième stratégie (« par architecture ») ? Et `import-linter`
   comme outil de vérification, ou une règle `ast` maison ?
7. **Moteur de règles maison** : `ast` de la bibliothèque standard, ou tree-sitter ? Plus on s'éloigne du Python seul
   (autres langages, requêtes déclaratives), plus tree-sitter se justifie.

## Prochaines étapes

- [ ] Valider les points ouverts ci-dessus.
- [ ] Écrire la page « pourquoi CUPID » (reprise du `CUPID-Learning-Path`, avec le D de Domain-based).
- [ ] Une fiche par règle : question, pourquoi c'est CUPID, avant/après de 5 lignes, vérification.
- [ ] Écrire les règles `ast` dans `harness/rules/`, une par règle, avec des tests à réponse connue.
- [ ] Brancher les règles sur la scorecard (progression par lettre).
