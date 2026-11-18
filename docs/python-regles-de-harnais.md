# Règles de harnais pour atelier Python : document de travail

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

On se base sur **CUPID** (Composable, Unix, Predictable, Idiomatic, Domain-based) : *comment le code est construit*.
Voir [`POURQUOI-CUPID.md`](POURQUOI-CUPID.md).

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
| 1 | Chaque classe parle-t-elle d'**un seul contexte borné** ? | **U** | D, C | 🗺️ | Éclater `Product` en classes par contexte (Catalog, Pricing, Storage, Supplier, Transport). Les liens passent par des identifiants. | `ast` + [`ubiquitous-language.json`](ubiquitous-language.json). En appui : LCOM*, WMC et CBO. |
| 2 | Tout type du domaine est-il **une entité (identifiant obligatoire) ou un Value Object** ? | **D** | P, U | 🗣️ | Classer chaque classe du modèle dans l'une des deux familles.<br>**Entité :** un champ `id` d'un type dédié (`ProductId`, pas `str`).<br>**Value Object :** `dataclass(frozen=True)`, sans identité.<br>Les primitives du domaine (`price`, `slug`, `quantity`) deviennent des Value Objects. Une entité en référence une autre par son identifiant. | `ast` : chaque classe du modèle est un Value Object (frozen, sans `id`) ou une entité (`id` typé dédié), et rien d'autre. Un membre dont le nom relève de l'ubiquitous language, typé par une primitive brute, est signalé. |
| 3 | Le modèle **ignore-t-il le stockage** ? | **D** | P, C | 🧪 | Sortir SQLAlchemy du modèle. Le mapping vit dans `dal/` et se branche de l'extérieur. Le choix de base devient un détail remplaçable. | `ast` : aucun import `sqlalchemy` ni `omni_product.database` sous `anemic_model/`. Test : instancier une entité sans session. |
| 4 | Les variantes sont-elles **composées** et non héritées ? | **C** | P, D | · | `PerishableProduct(Product)` et `NonExpiringProduct(Product)` deviennent `ShelfLife = Perishable \| NonExpiring`. `Product` porte un `shelf_life`. | `ast` : aucune classe du modèle n'hérite d'une autre (Enum, Protocol, Exception et TypedDict exceptés), pas d'`isinstance` sur les variantes. |
| 5 | Un échec métier est-il **une valeur** ? | **P** | C, D | 📖 | Un `raise` métier devient un résultat. Exemple : `withdraw` rend `Withdrawn \| InsufficientStock`. | `ast` : pas de `raise` métier dans `anemic_model/` et `service/`. Pyright : `match` exhaustif sur le résultat. |
| 6 | Les **effets impurs** sont-ils expulsés du cœur ? | **P** | C, D | 🧪 | Heure, aléatoire, UUID, fichiers, réseau et base sortent du cœur du domaine. Le cœur les reçoit en paramètre, ou par un port nommé dans le métier (`Clock`, `IdGenerator`) qu'on injecte. Le cœur devient pur et ses tests se font avec de simples faux, sans `patch`. | `ast` : `anemic_model/` n'appelle pas `date.today`, `datetime.now`, `time.time`, `uuid4`, `random.*`, `open`, `print`, ni `requests` ou `httpx`. Les tests n'utilisent ni `patch` ni `freezegun`. |
| 7 | **Un état illégal est-il impossible à construire ?** | **P** | D, C | 📖 | Remplacer les combinaisons incohérentes (drapeaux, `None` qui vont par paires) par un ADT : une union fermée de dataclasses frozen. Exemple : `Perishable(sell_by, use_by)` ou `NonExpiring(best_before)`. L'invariant (`sell_by <= use_by`) est validé par une fabrique qui rend un résultat. | `ast` : pas de champ booléen `is_*` ou `has_*` stocké, pas de plusieurs champs `X \| None` qui vont ensemble. Pyright : `match` exhaustif sur l'ADT. |
| 8 | Le code s'écrit-il avec **les idiomes courants de Python** ? | **I** | P, U | · | Remplacer les formes héritées d'autres langages par les formes que Python recommande : les boucles qui remplissent une liste deviennent des compréhensions, les chaînes de `if` un `match` ou une table, les retours anticipés remplacent l'imbrication. Chaque branche en moins fait baisser la complexité cyclomatique. | ruff durci (`PERF`, `C4`, `SIM`, `UP`, `C90`), sans code maison : `PERF401` repère la boucle qui remplit une liste. En appui, sur la scorecard : `boucles`, complexités cyclomatique et cognitive. |
| 9 | Le code va-t-il **plus loin vers le fonctionnel** (II) ? | **II** | P, U | · | Pousser le style au-delà de ce que Python impose : `sum`, `any`, `all`, `map`, `filter` et `reduce` à la place des boucles d'accumulation, petits `lambda`, enchaînements fluides sur un `Result` ou un `Option` (`.map`, `.and_then`) à la place des `if` et des `try`. Le style rejoint celui de Rust, Java, C# et Kotlin. | `ast` maison ❓ : pas de boucle `for` qui accumule (`append`, `+=`) dans `anemic_model/` et `service/`. En appui, sur la scorecard : `boucles`, `affectations`, `lambdas`. |
| 10 | Les dépendances **pointent-elles vers le cœur** (architecture en oignon, ports et adaptateurs) ? | **C** | P | 🧪 | Sortir de l'architecture en couches `controller → service → dal → base`. Le cœur (modèle et cas d'usage) ne connaît que des **ports**, des `Protocol` écrits dans le langage du métier (`ProductRepository`, `Clock`). Les **adaptateurs** (FastAPI, SQLAlchemy) sont à l'extérieur, implémentent les ports, et sont branchés à un seul endroit (la composition root). Le `dal/` disparaît au profit d'adaptateurs. | `import-linter` : contrats de couches (le cœur n'importe ni `controller`, ni `dal`, ni `infrastructure`, ni `fastapi`, ni `sqlalchemy`). Test : les cas d'usage se testent avec des faux en mémoire, sans base ni HTTP. |

### Notes sur les règles

- **Périmètre** : le harnais analyse `omni_product/`, hors `controller/`, `service/`, `dal/`, `config.py` et
  `database.py` (`harness/perimetre.py`). Ces fichiers sont de la plomberie : l'architecture en oignon
  (règle 10 du tableau) les sortira du cœur. Un mot technique ne s'ajoute jamais à l'ubiquitous language pour faire
  taire le harnais : on exclut le fichier.

- **Règle 2 ✅** : elle absorbe l'ancienne règle d'immuabilité. Un Value Object est frozen par définition. La métrique
  `attributs mutables` reste un thermomètre.
- **Règle 3 ✅** : c'est une vraie décision d'architecture. Dans ce port, le modèle **est**
  l'ORM (`Product(Base)`), donc la sortir du modèle coûte cher.
- **Règle 6 ✅** : elle est séparée de la règle 5. Les effets impurs (horloge comprise) sont une préoccupation à part :
  on les expulse du cœur par injection de dépendance pour que le cœur se teste facilement.
  - **Ce que le harnais lit** (`EI001`, `harness/rules/effet_impur.py`) : toute référence à un effet impur dans
    `domain/model` et `anemic_model`. Un effet est l'horloge (`date.today`, `datetime.now`, `time.time`), un
    identifiant tiré au hasard (`uuid4`, `random.*`, `secrets.*`), un fichier ou la sortie (`open`, `print`, `input`),
    le réseau (`httpx`, `requests`, `socket`), l'environnement (`os.environ`, `os.getenv`), le journal (`logging`),
    un processus (`subprocess`).
  - **Références, appelées ou non** : `field(default_factory=uuid4)` et `default_factory=date.today` sont des
    constats, car l'effet entre dans le modèle sans appel visible.
  - **Noms résolus par les imports** : `import datetime as dt` puis `dt.datetime.now()` est vu comme
    `datetime.datetime.now`. Importer `date` pour typer `sell_by` reste permis : l'effet est `date.today`.
  - **Le refactoring attendu** : la méthode reçoit la date (`is_expired(self, today: date)`), ou le cœur reçoit un
    port `Clock` écrit dans le métier. Le service, hors périmètre, fournit l'horloge réelle.
  - **Limites** : la règle travaille fichier par fichier. Un effet atteint par un autre module pur n'est pas vu. Elle
    constate l'absence d'effet. Elle ne peut pas exiger qu'un port soit injecté : les tests avec faux le démontrent.
  - **Les tests, `EI002`** : un `patch`, `patch.object`, `patch.dict` (`unittest.mock`), un `monkeypatch.*`, un
    `mocker.patch`, un `freezegun` ou un `time_machine` dans `tests/` remplace l'effet au lieu de le recevoir. Chaque
    référence est un constat, et il compte avec ceux de `EI001` : la règle 6 est verte quand les deux sont à 0. Un
    `MagicMock` passé en paramètre reste permis, c'est le faux que la règle demande. Les tests du harnais
    (`tests/harness/`) restent hors lecture : ils testent le harnais. La scorecard extrait `tests/` de la base
    comme elle extrait `src/`, pour comparer ce qui est comparable.
  - **Sur le legacy de l'atelier** : la règle est rouge. `domain/model/freshness.py` lit `date.today()` (`EI001`) et
    ses tests figent l'horloge avec `patch` (`EI002`). Elle passe au vert quand l'heure entre en paramètre et que
    les tests passent une date. Sur un modèle sans effet ni `patch`, elle compte 0 constat.
- **Règle 7 ✅** : un état illégal ne se construit pas. Le harnais lit deux indices dans `domain/model` et
  `anemic_model` (`harness/rules/etat_illegal.py`), avec des heuristiques `ast`.
  - **`EL001`, drapeau stocké** : un champ `is_*` ou `has_*` annoté `bool`. Le drapeau et les champs qu'il commande
    peuvent se contredire. Chaque valeur devient une variante d'union fermée. Une méthode `is_perishable()` n'est pas
    un champ stocké : elle n'est pas lue.
  - **`EL002`, `None` par paires** : une classe avec au moins deux champs `X | None` (`Optional[X]`, `Union[X, None]`
    et `Mapped[X | None]` de SQLAlchemy compris) donne un constat, posé sur la classe. Une variante par combinaison
    légale, et plus de `None`. Un seul champ optionnel est permis.
  - **Exceptions** : énumérations, `Protocol`, `TypedDict` et exceptions, comme pour les règles 2 et 4.
  - **Le refactoring attendu** : une union fermée de dataclasses frozen (`Perishable(sell_by, use_by)` ou
    `NonExpiring(best_before)`), et un `match` exhaustif vérifié par pyright.
  - **Limites** : le harnais lit la forme des champs, pas l'intention. Deux champs optionnels indépendants donnent un
    faux positif, et deux champs liés par un type différent de `None` lui échappent. Le point ouvert 5 reste ouvert :
    un test par propriétés (`hypothesis`) compléterait les heuristiques.
  - **Sur le legacy de l'atelier** : la règle est rouge. `PerishableProduct` porte `expiration_date` et
    `shelf_life_days`, `Price` et `RegionSupplier` trois champs optionnels chacun.
- **Règles 4 et 7** : la même union (`ShelfLife`) peut satisfaire les deux, mais ce sont deux questions distinctes.
  La 4 demande de composer au lieu d'hériter. La 7 demande que l'incohérent ne puisse pas se construire.
- **Règle 8 ✅ (I)** : les idiomes que la communauté Python recommande déjà. Ils se vérifient avec ruff, sans code
  maison. Les compréhensions y gagnent sur `map` et `filter` avec un `lambda`.
- **Règle 9 ✅ (II)** : un second **I**. Quand elle est appliquée, CUPID s'écrit **CUPIID**. Elle assume un parti pris. Elle va plus loin que la 8, vers le style fonctionnel que l'on
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
| 8 | Idiomes courants de Python | ruff (`PERF`, `C4`, `SIM`, `UP`, `C90`) | **I** | 2, tactique | ⏳ à faire |
| 9 | Style fonctionnel (II) | à venir | **II** | 2, tactique | ⏳ à faire |
| 10 | Architecture en oignon | à venir | **C** | 3, aboutissement | ⏳ à faire |

Le numéro de la règle est celui du tableau « Les 10 règles » plus haut, qui donne la question, le refactoring attendu et
la vérification. Les préfixes des codes viennent du nom de la règle : **C**ontexte **B**orné, **E**ntité **V**aleur,
**M**odèle **A**némique, **H**éritag**E**, **F**ailure **V**alue (l'échec valeur), **E**ffet **I**mpur, **E**tat **L**égal (`EI` étant pris).

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

## Points ouverts ❓

1. **Règle 3 (modèle sans stockage)** : en phase 1, ou en bonus réservé à la stratégie « par stockage » ?
2. **Blocage** : ne bloquer que la règle de l'étape en cours, et laisser les autres en avertissement sur la scorecard ?
3. **Règle 2** : garder l'immuabilité fondue dedans, ou la séparer en règle P ?
4. ~~**Bibliothèque d'ADT**~~ : tranché, `result` (voir la section sur les ADT et l'annexe).
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
