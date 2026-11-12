# Pourquoi CUPID

Cette page explique le choix de CUPID comme fil conducteur de l'atelier. Elle sert de point de départ : les règles
du harnais en découlent, et chacune se rattache à une lettre.

## D'où l'on part

Le code de départ respecte mal les principes SOLID : une classe `Product` mélange le catalogue, le prix, le stockage
et le transport, elle hérite de l'ORM, elle lève des exceptions pour des cas normaux, et elle lit l'horloge dans ses
méthodes. On appelle ça du « terrible OO design » : il fonctionne, et chaque évolution coûte cher.

## Pourquoi pas SOLID

SOLID est une liste de cinq principes d'orientation objet. Elle est précieuse, et elle a deux limites pour un atelier :

- **Elle se décrit en termes d'interfaces et d'héritage.** Pour un participant Python, « Liskov » et « Interface
  Segregation » demandent une traduction avant d'être utiles.
- **On peut la satisfaire sans rendre le code plus simple.** On trouve des codes SOLID avec dix classes et trois
  interfaces là où une fonction suffisait.

## CUPID : des propriétés qu'on constate

CUPID (Dan North) décrit des **propriétés du code**, qu'on peut vérifier en le lisant. Cinq lettres :

| Lettre | Propriété | La question qu'on se pose |
|---|---|---|
| **C** | Composable | Puis-je brancher ce morceau ailleurs, ou le remplacer, sans rien casser ? |
| **U** | Unix | Fait-il une seule chose, bien ? |
| **P** | Predictable | Fait-il ce qu'on attend, tout le temps ? |
| **I** | Idiomatic | S'écrit-il comme on écrit dans ce langage ? |
| **D** | Domain-based | Parle-t-il le langage du métier ? |

Le **D** est la lettre que le parcours d'apprentissage d'origine (en C#) laisse de côté. L'atelier la travaille
à fond : un code qui parle le langage du métier est plus facile à découper et à faire évoluer.

Chaque lettre en une image, avec du code :

**C, Composable.** Une règle de remise paramétrée se compose, alors qu'une règle codée en dur se copie.

```python
# avant : le seuil est dans le code
def remise_fidelite(total): return total * 0.9 if total > 100 else total

# après : on compose
def remise(seuil: float, taux: float) -> Callable[[float], float]:
    return lambda total: total * taux if total > seuil else total
```

**U, Unix.** `Product` qui gère le prix, le stock et le transport fait trois choses. Trois classes qui en font
chacune une peuvent se lire, se tester et se changer séparément.

**P, Predictable.** Une fonction qui lit l'horloge ou lève une exception pour un cas normal est difficile à prévoir.

```python
# avant : l'appelant doit deviner qu'elle peut lever
def retirer(self, quantite):
    if quantite > self.stock:
        raise ValueError("stock insuffisant")

# après : le résultat dit tout
def retirer(self, quantite) -> Retire | StockInsuffisant: ...
```

**II, Idiomatic FP.** Le code s'ouvre vers des expressions plus fonctionnelles et plus fluides : compréhensions,
lambdas, enchaînements de transformations, et jusqu'aux monades (`Result`, `Option`). On décrit ce qu'on veut, et
non les étapes pour y arriver.

```python
# avant : étape par étape, avec une variable qui change à chaque tour
perimes = []
for produit in produits:
    if produit.est_perime():
        perimes.append(produit.nom)

# après : une expression
perimes = [produit.nom for produit in produits if produit.est_perime()]

# plus loin : un enchaînement fluide sur un résultat (monade), sans `if` ni `try`
prix_ttc = (
    trouver(produit_id)                   # Ok(produit) ou Err(Introuvable)
    .map(lambda produit: produit.prix)
    .map(lambda prix: prix * 1.2)
)
```

Si `trouver` échoue, l'enchaînement s'arrête et `prix_ttc` porte l'erreur. Le code se lit comme une suite de
transformations. Les deux premiers exemples sont du Python courant. Le troisième est un parti pris de l'atelier, que la
section « FP: a New Hope in Idioms » assume et discute.

**D, Domain-based.** `price: float` devient `Prix`, `str` devient `ProductId`. Le code utilise les mots du métier, et
les types interdisent de mélanger un prix avec une quantité.

## Deux virages

Le parcours d'apprentissage se fait en deux temps.

**Virage 1, de SOLID à CUPID, en restant en objet.** On corrige les défauts du code de départ un par un : découper
les classes (U), paramétrer au lieu de coder en dur (C), retirer les comportements cachés (P), écrire en Python
moderne (I). Chaque étape corrige un défaut et enseigne une lettre.

**Virage 2, de l'objet au fonctionnel avec II** On change de paradigme : un résultat est une valeur (une union de cas
possibles, comme `Retire | StockInsuffisant`), les données sont immuables, les fonctions sont pures, le `match`
remplace les enchaînements de `if`. Le style fonctionnel répond naturellement à CUPID : une fonction pure se compose,
se prévoit et se lit.

## I ❤️ FP: a New Hope in Idioms

L'atelier prend position : le style d'un grand nombre de langages de programmation évolue vers plus de fonctionnel, de types précis et d'immuabilité .
Nous pensons que Python gagnerait à suivre ce mouvement.
Il faut dire que sur certains points, une partie de la communauté Python pense
autrement.

**Là où tout le monde est d'accord.** Compréhensions et générateurs, `@dataclass(frozen=True)`, annotations de type
vérifiées par `pyright` ou `mypy`, `match`, unions `A | B`. Ces idiomes sont mainstream, et ce sont eux qui portent la
lettre **I** (règle 8). La règle 9, que l'on appelle **II** (un second I), pousse plus loin vers le fonctionnel :
c'est elle qui prend position. Une fois appliquée, CUPID s'écrit **CUPIID**.

**Là où la communauté se divise.**

| Pratique | Position de l'atelier | Une partie de la communauté Python |
|---|---|---|
| `lambda`, `map`, `filter`, `reduce` | Utiles, en petites doses. Sur une liste, la compréhension reste préférée (règles 8 et 9). | Guido van Rossum a voulu les retirer de Python 3 ; `reduce` est allé dans `functools`. |
| Enchaînement fluide (`.map(...).map(...)`) | Un style qui se lit comme une suite de transformations. | Les listes n'ont pas de `.map()` natif : ce style n'est pas naturel. |
| `Result` et `Option` (monades) | Un échec métier est une valeur (règles 5, 7 et 9). | Le style attendu est de lever une exception et de la rattraper (EAFP). |

**La question que pose l'atelier : pourquoi Python ferait-il de la résistance ?**

Le mouvement existe déjà ailleurs :

- **Rust :** `Result`, `Option` et `match` sont le cœur du langage.
- **Java :** `Optional`, `Stream`, les `record`, les classes `sealed` et le `switch` par motifs.
- **C# :** les `record`, les expressions `switch` et LINQ.
- **Kotlin :** les classes `sealed`, `Result`, `map` et `filter` sur les collections.

Python a lui-même fait la moitié du chemin : les compréhensions viennent de Haskell, et `match`, les dataclasses
`frozen` et les annotations de type sont arrivés ces dernières années. Les résistances ont des raisons historiques
plutôt que techniques :

- **Un langage né pour le script**, où lever une exception est le geste le plus court.
- **Une culture de la lisibilité immédiate** (« il devrait y avoir une façon évidente de le faire »), qui préfère
  la boucle ou la compréhension à un enchaînement de lambdas.
- **Un typage longtemps facultatif**, qui rendait les unions fermées et le `match` exhaustif peu utiles.

Ce dernier frein a disparu : avec `pyright` en mode strict, un `match` qui oublie un cas est signalé. C'est ce qui
rend les `Result` et les ADT intéressants en Python aujourd'hui.

### Et la performance des exceptions ?

En Java et en C#, lever une exception coûte cher : le runtime capture la pile d'appels, et chaque `throw` se paie en
microsecondes. C'est un argument classique contre les exceptions pour le flux normal.

En Python, l'argument est faible. Mesure sur ce dépôt (Python 3.14.7, une fonction appelée 500 fois, minimum de
5 séries) :

| Cas | Coût par appel |
|---|---:|
| `try/except`, sans exception levée | 18 ns |
| `raise` puis `except` | 149 ns |
| `match` sur un `Result` (dataclass frozen) qui réussit | 209 ns |
| `match` sur un `Result` qui échoue | 227 ns |

Lever et rattraper une exception coûte environ 130 ns de plus qu'un appel normal, et un `try` qui ne lève rien est
quasi gratuit (depuis Python 3.11). Un `Result` construit avec une dataclass frozen coûte **plus** cher qu'une
exception, car la construction d'une instance frozen est lente. Ces chiffres varient avec la machine et avec la
profondeur de la pile, mais l'ordre de grandeur reste : **en Python, on ne passe pas aux `Result` pour la vitesse.**

Les raisons de les adopter sont ailleurs :

- **L'échec apparaît dans la signature.** `retirer(...) -> Retire | StockInsuffisant` dit ce qui peut arriver, là où
  `raise ValueError` se découvre à l'exécution.
- **`pyright` vérifie qu'on traite tous les cas** avec un `match` exhaustif.
- **Les étapes se composent** : c'est l'idée de la *Railway Oriented Programming* (ROP) de Scott Wlaschin.

### Railway Oriented Programming

Scott Wlaschin représente un enchaînement d'étapes comme deux rails : le rail du succès et le rail de l'échec. Chaque
étape reçoit un succès et rend un succès ou un échec. À la première erreur, le train bascule sur le rail d'échec et
saute les étapes suivantes. Il n'y a ni `if` ni `try` entre les étapes.

```python
def passer_commande(demande):
    return (
        valider(demande)              # Ok(demande) ou Err(Invalide)
        .and_then(trouver_produit)    # Ok(produit)  ou Err(Introuvable)
        .and_then(retirer_du_stock)   # Ok(retrait)  ou Err(StockInsuffisant)
        .map(facturer)
    )
```

En Python, ça se fait avec `.and_then` (appelé `bind` ou `flatmap` ailleurs) sur le `Result` de la bibliothèque
`result`, ou avec `bind` et `flow` dans `returns`. Le chaînage de méthodes se lit mieux que des `if` imbriqués. Les
exemples de Scott Wlaschin sont en F#, sur [fsharpforfunandprofit.com](https://fsharpforfunandprofit.com/rop/).

L'atelier ne cherche pas à convertir tout le monde. Il propose d'essayer ce style sur un code réel, de mesurer ce
qu'il apporte avec la scorecard, et de juger sur pièces.

## CUTE : la lettre qui manque

CUPID ne nomme pas la testabilité, alors que presque toutes les améliorations de l'atelier la rendent meilleure. Un
cœur sans base de données, sans horloge et sans réseau se teste avec de simples faux.

CUTE (*Contextual, Ubiquitous, Testable, Expressive*) complète CUPID. Ses lettres C et U ressemblent à celles de CUPID
et ne veulent pas dire la même chose, donc le harnais les écrit en emojis :

| Emoji | CUTE | Sens |
|:-:|---|---|
| 🗺️ | Contextual | Les décisions suivent le contexte métier |
| 🗣️ | Ubiquitous | Un langage partagé par tous |
| 🧪 | Testable | Facile à tester à tous les niveaux |
| 📖 | Expressive | Le code raconte l'intention métier |

CUPID dit **comment le code est construit**, CUTE dit **ce qu'il apporte à l'équipe**.

## Ce que ça change dans l'atelier

Les règles du harnais sont les gestes concrets qui mènent à ces propriétés : chacune a une lettre CUPID principale,
éventuellement des annexes, et un emoji CUTE quand elle en a un. Les chiffres de la scorecard (voir
[`METRIQUES.md`](METRIQUES.md)) montrent si le code avance dans cette direction. Le détail des règles est dans
[`python-regles-de-harnais.md`](python-regles-de-harnais.md).

## Pour aller plus loin

- Dan North, [*CUPID, for joyful coding*](https://dannorth.net/cupid-for-joyful-coding/)
- Le parcours d'apprentissage CUPID de l'atelier (`CUPID-Learning-Path.md`), en C#.
