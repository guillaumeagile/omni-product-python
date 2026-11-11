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

**I, Idiomatic.** Une boucle qui remplit une liste s'écrit mieux en compréhension, et une chaîne de `if` en `match`.

**D, Domain-based.** `price: float` devient `Prix`, `str` devient `ProductId`. Le code utilise les mots du métier, et
les types interdisent de mélanger un prix avec une quantité.

## Deux virages

Le parcours d'apprentissage se fait en deux temps.

**Virage 1, de SOLID à CUPID, en restant en objet.** On corrige les défauts du code de départ un par un : découper
les classes (U), paramétrer au lieu de coder en dur (C), retirer les comportements cachés (P), écrire en Python
moderne (I). Chaque étape corrige un défaut et enseigne une lettre.

**Virage 2, de l'objet au fonctionnel.** On change de paradigme : un résultat est une valeur (une union de cas
possibles, comme `Retire | StockInsuffisant`), les données sont immuables, les fonctions sont pures, le `match`
remplace les enchaînements de `if`. Le style fonctionnel répond naturellement à CUPID : une fonction pure se compose,
se prévoit et se lit.

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
[`CUPID-regles-de-harnais.md`](CUPID-regles-de-harnais.md).

## Pour aller plus loin

- Dan North, [*CUPID, for joyful coding*](https://dannorth.net/cupid-for-joyful-coding/)
- Le parcours d'apprentissage CUPID de l'atelier (`CUPID-Learning-Path.md`), en C#.
