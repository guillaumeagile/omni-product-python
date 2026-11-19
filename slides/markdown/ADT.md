# ADT

En programmation fonctionnelle (FP), ADT signifie *Algebraic Data Type* (type de données algébrique). Le terme ne désigne pas un *Abstract Data Type*, qui est un autre concept. [1] (https://en.wikipedia.org/wiki/Algebraic_data_type)

Un type algébrique se construit en combinant des types plus simples avec deux opérations : le produit et la somme. Elles se comportent comme la multiplication et l'addition. [1] (https://en.wikipedia.org/wiki/Algebraic_data_type), [2] (https://dev.to/gcanti/functional-design-algebraic-data-types-36kf)

## Les deux familles

### 1. Type produit (le « ET »)

- **Ce que c'est :** une donnée qui porte plusieurs valeurs en même temps.
- **Comment ça marche :** si A a x valeurs possibles et B en a y, un produit de A et B en a x × y.
- **En Python :** un `dataclass(frozen=True)` avec plusieurs champs.

```python
@dataclass(frozen=True)
class Point:
    x: float
    y: float
```

### 2. Type somme / union étiquetée (le « OU »)

- **Ce que c'est :** une donnée qui porte une seule variante parmi plusieurs, identifiable à l'exécution.
- **Comment ça marche :** si A a x valeurs et B en a y, une somme de A ou B en a x + y.
- **En Python :** une union `A | B` de dataclasses, lue par `match`.

```python
@dataclass(frozen=True)
class CarteBancaire:
    numero: str


@dataclass(frozen=True)
class Paypal:
    email: str


@dataclass(frozen=True)
class Especes:
    pass


Paiement = CarteBancaire | Paypal | Especes


def libelle(paiement: Paiement) -> str:
    match paiement:
        case CarteBancaire(numero=n):
            return f"carte {n[-4:]}"
        case Paypal(email=e):
            return f"paypal {e}"
        case Especes():
            return "espèces"
```

Les types de résultat de l'atelier suivent le même modèle : `Retire | StockInsuffisant`. Une fonction qui retire du stock renvoie l'une des deux variantes, et l'appelant doit les traiter.

## Pourquoi les ADT comptent

- **Les états invalides ne se construisent pas.** Avec des produits et des sommes, le modèle ne laisse exister que les combinaisons valides. Une carte bancaire sans numéro ne peut pas être créée.
- **Le contrôle d'exhaustivité.** Un `match` sur une union doit couvrir chaque variante. Avec `pyright` en mode strict, un cas oublié est signalé avant l'exécution. Pour le vérifier à la main, on termine le `match` par `assert_never(paiement)`.
- **Remplacer `None` et les exceptions.** Un résultat qui peut échouer se déclare dans la signature : `Result` (`Ok | Err`) ou `Option` (`X | None`). L'appelant voit le cas d'échec sans avoir à le deviner. [1] (https://dev.to/gcanti/functional-design-algebraic-data-types-36kf)

En Python, ces trois propriétés sont aujourd'hui accessibles avec la bibliothèque standard et `pyright`. Voir la section « I ❤️ FP » du harnais pour la position de l'atelier sur ces pratiques.
