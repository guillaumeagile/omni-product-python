# Guide du maître du jeu : les smells de design du code legacy

Ce document est pour l'animateur de l'atelier de refactoring. Il liste les défauts de design **volontairement laissés**
dans ce port Python, ce que le harnais devra détecter, et surtout **pourquoi le linter et le type checker ne les
empêchent pas**. Il ne doit pas être donné aux participants.

Le code est un port de `omni-product-spring-boot-java-bdxio-phase1`. Les smells sont organisés par propriété CUPID
(Composable, Unix, Predictable, Idiomatic, Domain-based). La correspondance avec les règles `HA*` du harnais est à
compléter par l'animateur : je n'ai pas lu le harnais, donc je ne la devine pas.

## 1. Pourquoi le linter et le type checker sont permissifs

Principe : on veut des **smells de design** (couplage, responsabilités, nommage, duplication), pas des défauts que
l'outillage attraperait seul. Si ruff ou pyright criaient sur chaque smell, les participants corrigeraient les
warnings au lieu de réfléchir au design.

### Ruff (`pyproject.toml`, section `[tool.ruff.lint]`)

| Réglage actuel | Ce que ça laisse passer | Pourquoi |
|---|---|---|
| Règles `E F I UP B SIM N RUF C4 PT` seulement | Voir les familles non activées ci-dessous | Base « hygiène » : le code compile proprement mais n'est pas jugé sur son design |
| `ignore = ["N818"]` | Exceptions sans suffixe `Error` (`ProductNameException`, `TransportCarbonException`) | On garde les noms Java pour tracer le portage |
| `per-file-ignores` : `SIM102` sur `controller/product_controller.py` | `if` imbriqués qu'on pourrait fusionner (le null-check en cascade de `create_product`) | C'est un smell voulu (voir S-C3) |

Familles ruff **volontairement non activées**, qui détecteraient des smells présents :

| Famille | Aurait signalé | Smell concerné |
|---|---|---|
| `C90` (complexité McCabe) | Fonctions trop ramifiées | S-C3 |
| `PLR0913` (trop d'arguments) | `create_supplier` / `update_supplier` à 6 paramètres | S-S2 |
| `PLR2004` (valeurs magiques) | Code HTTP `424`, `422` | S-C4 |
| `BLE` (`except Exception`) | Catch-all de l'adaptateur | S-I1 |
| `ARG` (arguments inutilisés) | Paramètres non utilisés | divers |
| `A` (masque un builtin) | Paramètre `id` dans `SupplierService` et `Supplier.from_services` | S-S2 |
| `ERA` (code commenté) | Pas de cas aujourd'hui | à surveiller |
| `D` (docstrings), `ANN` | Absence de documentation | hors sujet |

Les `# noqa: A002` de `supplier_service.py` et `model/supplier.py` sont **inertes** (la famille `A` n'est pas activée) :
ils ne servent à rien aujourd'hui. À supprimer ou à garder comme bruit, au choix de l'animateur.

### Pyright (`pyproject.toml`, section `[tool.pyright]`)

| Réglage actuel | Effet | Pourquoi |
|---|---|---|
| `typeCheckingMode = "strict"` | Aucun `Any` implicite, tout est annoté | On veut des smells de **design**, pas des trous de typage. Gardé strict à dessein |
| `reportUnnecessaryComparison = false` | Autorise `if service is None` sur un paramètre non optionnel, et `if body is not None` sur un modèle Pydantic | Nécessaire pour garder les null-checks inutiles (S-C1, S-C3) |

Pragmas `# pyright: ignore` restants dans le code : `main.py` (2), `supplier_repository.py` (1) et
`domain/model/transport_request.py` (2). Les deux de `transport_request.py` sont **devenus redondants** depuis que
`reportUnnecessaryComparison` est désactivé globalement ; ils peuvent être retirés. Les autres sont de la plomberie
(import pour enregistrer les tables, handler enregistré par décorateur, critère SQLAlchemy), pas des smells.

### Candidats pour assouplir davantage (non appliqués)

À décider par l'animateur selon les smells qu'il veut garder :

- Désactiver `reportUnknownMemberType` / `reportUnknownVariableType` dans `tests/` si on veut des tests moins typés.
- Activer `PLR0913` / `BLE` / `C90` **plus tard**, comme règles du harnais ou comme étape de la phase 2 : le linter
  devient alors un allié pour vérifier qu'un smell est bien corrigé.

## 2. Catalogue des smells

Les chemins sont relatifs à `src/omni_product/`. Pas de numéros de ligne : ils bougent.

### Predictable / Idiomatic : contrôleurs

| ID | Smell | Où | Détail |
|---|---|---|---|
| S-C1 | Null-check inutile | `controller/product_controller.py`, `get_all_products` | `if product_service is None` : l'injection ne peut pas le fournir nul. Lève `ProductNameException` avec un message absurde |
| S-C2 | Exception métier levée dans le contrôleur | `create_product` | Le handler existe dans `main.py`, mais la validation est dans le contrôleur au lieu de la couche domaine ou d'une validation Pydantic |
| S-C3 | `if` imbriqués redondants + code mort | `create_product` | `if body is not None: if body.name is not None:` après une validation qui garantit déjà les deux. Le `raise ... "Something went wrong in the void"` final est inatteignable en pratique |
| S-C4 | Statut HTTP sémantiquement faux | `main.py` | `ProductNameException` → 424 (Failed Dependency) pour une donnée invalide : un 400 ou 422 serait attendu |
| S-C5 | Duplication contrôleur / service | `product_controller.py` | `update_product` et `delete_product` font `find_by_id` pour tester l'existence, puis le service refait la lecture |

### Domain-based / Unix : modèle

| ID | Smell | Où | Détail |
|---|---|---|---|
| S-M1 | Inversion de dépendance : le modèle connaît les services | `model/supplier.py`, `Supplier.from_services` | Une entité qui prend `ProductService` et `SupplierService`, fait de l'I/O (`find_all`, `get_supplier`) pendant sa construction. Les imports sont sous `TYPE_CHECKING`, donc le cycle est caché à l'exécution mais présent dans le design |
| S-M2 | Association bidirectionnelle avec cascade | `Supplier.products` ↔ `Product.supplier` | `cascade="all, delete-orphan"` : supprimer un fournisseur supprime ses produits |
| S-M3 | Obsession des primitives | `model/product.py` | `Price` en `float` (argent), `volume: str` qui contient `"10x10x10"`, `discounts: list[str]`, `images: dict[str, str]` |
| S-M4 | Donnée dérivée stockée | `Price` | `tax` et `tax_rate` coexistent avec `base` : redondants, peuvent diverger |
| S-M5 | Nommage incohérent | `Product` | `kilos` (poids), `volume` (dimensions), `image_detail` (une URL) ; le constructeur Java appelait ces champs `weight` et `dimensions` |
| S-M6 | Deux « Supplier » | `Supplier` (entité) et `RegionSupplier` (valeur embarquée) | Même mot pour deux concepts. En Java c'était `Product.Supplier` contre `Supplier` ; en Python j'ai déjà renommé la classe embarquée, donc le smell est atténué |
| S-M7 | Partout nullable | `Supplier`, `ProductSchema` | Quasiment tous les champs sont `X \| None` : aucune invariante n'est exprimée |

### Composable : services et dépôts

| ID | Smell | Où | Détail |
|---|---|---|---|
| S-S1 | Intermédiaire sans valeur (middle man) | `service/product_service.py` | Quatre méthodes qui délèguent telles quelles au dépôt |
| S-S2 | Longue liste de paramètres, paramètres de même type | `SupplierService.create_supplier` / `update_supplier` | Six `str \| None` consécutifs : on peut permuter `country` et `region` sans erreur de type. Le même groupe de six champs est répété dans `SupplierRequest`, `SupplierUpdateRequest`, le contrôleur, le service et l'entité (data clump) |
| S-S3 | Exceptions génériques pour des cas métier | `SupplierService` | `ValueError("Supplier not found: ...")` : aucun handler, donc l'API répond 500 au lieu de 404 |
| S-S4 | Dépendance entre agrégats | `SupplierService` | Dépend de `ProductRepository` pour un seul contrôle d'existence |
| S-S5 | Code mort | `repository/*`, `service/product_transport_service.py`, `dependencies.py` | `find_by_name`, `find_by_slug`, `exists_by_slug`, `delete_by_slug` jamais appelés. `ProductTransportService` et `get_product_transport_service` sont câblés mais aucune route ne les utilise |
| S-S6 | Frontière transactionnelle dans le dépôt | `repository/*` | Chaque `save` / `delete` fait son propre `commit`. `update_supplier` (lire puis modifier puis sauver) n'est pas atomique, et rien ne permet une transaction englobant plusieurs opérations |
| S-S7 | Primitives à la frontière du service | `ProductTransportService.calculate_shipment_carbon` | Prend `str, float, float` puis construit `TransportRequest` lui-même |

### Predictable / Composable : infrastructure et câblage

| ID | Smell | Où | Détail |
|---|---|---|---|
| S-I1 | Catch-all | `infrastructure/adapter/impact_co2_transport_adapter.py` | `except Exception` qui réemballe tout, y compris les erreurs de programmation |
| S-I2 | Validations sans cohérence avec les types | `domain/model/transport_request.py` | Teste `is None` sur des champs typés `float` ; `TransportCarbonMetrics` ne valide pas `co2_direct_kg` |
| S-I3 | Localisateur de services | `dependencies.py` | `request.app.state.*` est non typé ; l'adaptateur et le client HTTP sont reconstruits à chaque requête |
| S-I4 | Effet de bord à l'import | `main.py` | `app = create_app()` au niveau du module crée le moteur de base dès l'import |
| S-I5 | Configuration bruyante par défaut | `config.py` | `show_sql = True` par défaut, comme `show-sql: true` dans `application.yml` |

### Héritage : hiérarchies superficielles (ajoutées pour l'atelier)

Aucun de ces smells n'est visible pour ruff ni pyright : l'héritage est valide, il est juste mal motivé.

| ID | Smell | Où | Détail |
|---|---|---|---|
| S-H1 | Sous-classe vide | `model/product.py`, `NonExpiringProduct` | Aucun champ ni comportement propre : la classe ne sert qu'à porter un `isinstance`. Le type `non_expiring` pourrait être une valeur de colonne |
| S-H2 | Colonnes de sous-classe dans la table parente | `model/product.py`, `PerishableProduct` | Héritage mono-table : `expiration_date` et `shelf_life_days` sont nullables pour tous les produits, aucune invariante « périssable ⇒ date » |
| S-H3 | La base connaît ses enfants | `Product.is_perishable`, `controller/schemas/mapping.py` (`_kind_of`, `schema_to_product`) | La classe de base fait `isinstance(self, PerishableProduct)` ; la conversion refait un switch sur le type à deux endroits. Chaque nouveau type oblige à toucher la base et les schémas |
| S-H4 | Hériter pour réutiliser des champs, pas pour un « est-un » | `controller/schemas/supplier.py` (`SupplierUpdateRequest` → `SupplierRequest` → `SupplierSchema`), `infrastructure/adapter/impact_co2_dtos.py` (`ImpactCo2Request` → `ImpactCo2Response`) | Une réponse de création hérite d'une requête, qui hérite d'une mise à jour. Changer `SupplierUpdateRequest` change silencieusement la réponse |
| S-H5 | Racine d'exceptions vide et mal rangée | `exception/business_exception.py` | `BusinessException` n'a ni message ni comportement. `TransportCarbonException` (domaine) en dépend, donc le domaine importe depuis `exception/` ; `ProductNameException` reste dans un autre paquet que l'exception du domaine |
| S-H6 | Socle de dépôt pour trois lignes | `repository/session_repository.py` | `SessionRepository` ne porte que la session et deux helpers. `find_all`, `find_by_id` et `delete_all` restent dupliqués dans chaque dépôt, donc le socle ne mutualise pas grand-chose |
| S-H7 | Violation de Liskov au niveau du comportement | `model/product.py` (`is_perishable`), `controller/schemas/mapping.py` (`_kind_of`, `schema_to_product`) | Le sous-type ne se comporte pas comme la base : le comportement dépend de la classe Python réelle, pas de la donnée. Voir le détail ci-dessous |

#### S-H7 : pourquoi c'est un smell de comportement, pas seulement de structure

Côté base de données, le modèle est juste : `PerishableProduct` est une ligne de `products` avec `kind = 'perishable'`,
et l'héritage SQLAlchemy la recharge dans la bonne classe. Mais côté code actif, le principe de substitution de
Liskov n'est pas respecté : un `Product` doit pouvoir être remplacé par un `PerishableProduct` sans que le programme
change de comportement, et ce n'est pas le cas.

- **Deux sources de vérité.** La colonne `kind` et la classe Python peuvent diverger. Vérifié à l'exécution (SQLite en
  mémoire) : on crée un `Product`, on met `kind = "perishable"`, on commit. Au commit, `is_perishable()` répond
  `False`. Rechargé depuis la base, le même objet devient un `PerishableProduct` et répond `True`. Le même objet donne
  donc deux réponses selon qu'il a été rechargé ou non, et l'erreur n'apparaît qu'à l'exécution.
- **Le comportement dépend du type.** Pour que le code marche, il faut tester la classe : `isinstance` dans
  `is_perishable` et `_kind_of`, `match` sur `kind` dans `schema_to_product`. C'est exactement ce que le polymorphisme
  devait éviter : on ne dit plus à l'objet ce qu'il sait faire, on demande à quelle sous-classe il appartient.
- **Un nouveau type casse les appelants silencieusement.** Il faut penser à ajouter la branche dans chaque `isinstance`
  et chaque `match`. Le `case _:` de `schema_to_product` renvoie alors un `Product` sans erreur, et l'oubli ne se voit
  qu'au test métier, pas au linter ni au type checker.
- **Le sous-type n'ajoute aucune garantie.** `PerishableProduct` sans date est accepté : il n'est donc pas plus
  contraint que la base, et un appelant ne peut pas raisonner sur « un périssable a une date limite ».

Piste pour l'animateur (ne pas donner aux participants) : soit un polymorphisme réel, où chaque sous-classe implémente
le comportement et la base ne teste jamais le type ; soit une composition, où `Product` porte une valeur optionnelle
`shelf_life: ShelfLife | None` (un objet dont la présence a un sens) au lieu d'une sous-classe. Dans les deux cas,
l'invariant « périssable ⇒ date » devient vérifiable par le type ou par le constructeur, ce que le smell S-H2 n'offre pas.

Point d'attention : `# noqa: RUF012` sur les trois `__mapper_args__`. C'est l'idiome SQLAlchemy (dict de classe) ;
le `ClassVar` provoquerait une erreur pyright, car SQLAlchemy déclare cet attribut en variable d'instance.

### Tests

| ID | Smell | Où | Détail |
|---|---|---|---|
| S-T1 | Test fourre-tout | `tests/controller/test_product_controller.py::test_crud_operations` | Un seul test enchaîne create / validation / get / update / delete |
| S-T2 | Zones non couvertes | | Aucun test pour `ProductService`, `Supplier.from_services`, la branche « universe has collapsed », les dépôts isolés |
| S-T3 | Tout passe par la vraie base | `tests/` | Pas de test unitaire de service avec doublure ; seule la couche transport utilise un faux |

### Bugs latents : comportements faux que les tests ne voient pas

Ajoutés pour l'atelier (branche `worktree-latent-bugs-legacy`). Ils ne font échouer aucun test courant.

| ID | Bug | Où | Détail |
|---|---|---|---|
| S-B1 | Stock absent devient 0 | `controller/schemas/mapping.py` (`schema_to_product`) | `stock or 0` : « inconnu » et « zéro » deviennent indiscernables |
| S-B2 | Quantité absente reprend le stock | `controller/schemas/mapping.py` | `quantity` retombe sur `stock` quand il n'est pas fourni |
| S-B3 | Nom impossible à effacer | `service/supplier_service.py` (`update_supplier`) | `name or supplier.name` : les autres champs sont écrasés, celui-ci non |
| S-B4 | Distance arrondie à 0 | `service/product_transport_service.py` | `round(distance_km)` : une livraison de 0,3 km devient invalide |

À trancher :
- S-B1 : un stock absent doit-il être `None` (inconnu) ou `0` ? Le choix actuel masque l'information.
- S-B2 : le repli quantité → stock est-il voulu comme raccourci, ou un bug pur ?
- S-B3 : le PUT doit-il être uniforme (tout écrasé, y compris par `None`) ? Dans ce cas le `or` est le seul écart.
- S-B4 : l'arrondi est-il un défaut de précision (arrondir au dixième de km suffirait), ou un bug à garder tel quel ?

Autres comportements douteux déjà présents, non modifiés. Les classer en bugs ou en smells est à trancher :
- `SupplierService.create_supplier` agit en upsert : un POST sur un id existant écrase le fournisseur.
- `update_product` (PUT) ne valide pas le nom, contrairement à `create_product`.
- Supprimer un fournisseur supprime ses produits (cascade `all, delete-orphan`).

## 3. Écarts avec le code Java d'origine

À connaître avant l'atelier, car ils changent ce que le harnais verra :

1. **DTO au lieu d'entités exposées.** Java sérialisait les entités JPA directement. Ici `controller/schemas/`
   (Pydantic) s'interpose. Le smell « l'entité fuit dans l'API » n'existe donc plus. Si on le veut, il faut le
   réintroduire (par exemple en renvoyant les entités depuis les routes).
2. **Le lazy loading n'est pas reproduit.** `LAZY_LOADING_ISSUE.md` n'a pas d'équivalent : `get_suppliers_by_product`
   passe par une requête SQL (`find_by_product_id`) et le test, `@Disabled` en Java, est actif et passe.
3. **Champ `supplierId` ajouté** à `ProductSchema` (absent en Java) pour pouvoir rattacher un fournisseur par l'API.
4. **`Supplier.products` non sérialisé**, pour éviter la référence circulaire.
5. **422 sur création sans `id`** : comportement ajouté, Java échouait plus tard à l'enregistrement.
6. **Message d'erreur nettoyé** : « Product name is missing » remplace l'ancien message injurieux. À remettre tel quel
   si l'animateur veut le conserver.
7. **`Supplier.from_services` est un classmethod** : Python n'a pas de surcharge de constructeur.
8. Le `TODO: never throw exceptions in controllers` du Java n'a **pas** été reporté : les consignes étaient de ne pas
   commenter les smells.
9. **Les participants ne doivent pas toucher** `domain/` et `infrastructure/` (consigne de `AGENTS.md` côté Java) :
   S-I1 et S-I2 vivent dans ces dossiers. À trancher : ces smells servent-ils de leçon de l'animateur, ou faut-il
   les sortir de cette zone ?

## 4. Vérifier que les smells sont toujours là

```bash
uv run ruff check .      # doit rester vert : c'est voulu
uv run pyright           # idem
uv run pytest            # 40 tests verts : le comportement est figé
```

Un linter vert ne veut pas dire code sain ici. Il garantit seulement que le comportement testé reste identique
pendant le refactoring.
