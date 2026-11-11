# Les métriques de l'arbitre, pour les curieux

Pendant l'atelier, l'arbitre commente chaque PR avec un tableau de chiffres. Ce document explique **ce que mesure
chaque chiffre, et pourquoi on le regarde**. Tu n'as pas besoin de le lire pour jouer : il est là si tu veux comprendre
ce que le tableau dit de ton code.

> **Une règle d'or avant de commencer.** Une métrique est un thermomètre, pas un objectif. Si tu écris du code pour
> faire baisser un chiffre, tu fabriques du code étrange qui plaît au thermomètre. Écris le code le plus clair
> possible, puis regarde ce que les chiffres en disent. C'est l'inverse qui ne marche pas.

## Ce qui est mesuré

Seul le code que tu fais évoluer est mesuré : le **modèle** et les **services**. Les tests, le controller et le
harnais ne comptent pas. L'arbitre compare ton code à celui de ton baby step précédent : c'est la **variation** qui
compte, pas la valeur absolue.

Les mesures sont déterministes : le même code donne toujours les mêmes chiffres.

## 1. Le coût de lecture : les tokens

**Ce que c'est.** Un token est un morceau de texte, à peu près un mot ou un bout de mot, tel qu'un modèle de langage le
découpe. `ProductNameException` fait plusieurs tokens, `if` en fait un.

**Pourquoi on le regarde.** Un agent (ou un humain pressé) paie à la lecture : plus il y a de tokens, plus il y a à
lire, à comprendre et à garder en tête. Moins de tokens, c'est souvent moins de répétition, moins de code mort,
moins de cérémonie.

**Comment c'est compté.** Avec `tiktoken`, l'encodage `o200k_base`. Ce n'est pas le découpage exact de tous les modèles,
mais l'ordre de grandeur est juste, et surtout les **variations** d'une PR à l'autre sont fidèles.

**Le piège.** Raccourcir les noms (`price` devient `p`) fait baisser les tokens et dégrade le code. Lisible avant court.

**Le petit diff.** L'arbitre compte aussi les tokens de **ta modification** (les lignes ajoutées et retirées). Une PR
qui change peu est facile à relire et facile à annuler : c'est l'esprit du *baby step*.

## 2. Le nombre de chemins : la complexité cyclomatique

**Ce que c'est.** Le nombre de chemins indépendants dans une fonction. Une fonction sans `if` a un chemin (valeur 1).
Chaque `if`, `for`, `while`, `and`, `or` ou `except` en ajoute un.

```python
def frais(poids, express):          # 1 chemin de base
    if poids > 20:                  # +1
        return 30
    if express and poids > 5:       # +1 pour le if, +1 pour le and
        return 15
    return 5                        # complexité = 4
```

**Pourquoi on le regarde.** C'est le nombre de tests minimum pour couvrir la fonction. À 4, il faut 4 cas de test. À
15, plus personne n'ose y toucher.

**Ce que l'arbitre additionne.** La somme sur toutes les méthodes du modèle et des services. Retirer des branches
(remplacer un `if/elif` par du polymorphisme, supprimer un cas mort) la fait baisser.

## 3. La complexité d'une classe : WMC

**Ce que c'est.** *Weighted Methods per Class* : la somme des complexités de toutes les méthodes d'une classe.

**Pourquoi on le regarde.** Une classe à WMC élevé fait trop de choses. C'est la signature d'une *god class*. L'arbitre
regarde le **maximum** : la pire classe du lot.

## 4. La complexité cognitive

**Ce que c'est.** Une cousine de la complexité cyclomatique, qui mesure la **difficulté de compréhension** plutôt que
le nombre de chemins. Elle punit l'imbrication : un `if` dans un `for` dans un `if` coûte beaucoup plus que trois `if`
à plat.

**Pourquoi on le regarde.** Deux fonctions peuvent avoir la même complexité cyclomatique et être très inégales à lire.
La cognitive attrape les pyramides d'indentation que la cyclomatique laisse passer. Une garde et un retour anticipé
(*early return*) la font baisser.

## 5. Le couplage : fan-out (et CBO)

**Ce que c'est.** Le nombre d'autres types dont une classe dépend. Le **fan-out** est PMD, le **CBO** (*Coupling
Between Objects*) est CK : deux outils, la même idée.

**Pourquoi on le regarde.** Plus une classe connaît de monde, plus elle casse quand l'un d'eux change. C'est le
« C » de Composable dans CUPID : un bon module se branche sur peu de choses.

## 6. La cohésion : TCC (et LCOM)

**Ce que c'est.** Parmi les paires de méthodes d'une classe, quelle part utilise au moins un attribut en commun. Valeur
de 0 à 1 : à 1, toutes les méthodes travaillent sur les mêmes données.

**Pourquoi on le regarde.** Une classe cohésive fait une seule chose. Une classe à faible cohésion est deux classes
collées ensemble : un groupe de méthodes sur un groupe d'attributs, un autre groupe sur un autre. C'est le signal
« tu peux la couper en deux ». **LCOM** est la mesure inverse (le manque de cohésion) : plus haut, c'est pire.

L'arbitre regarde la **pire** classe (TCC minimum).

## 7. Les signaux de style : états, boucles, lambdas

Ces compteurs ne jugent pas le code bon ou mauvais. Ils indiquent **vers quel style il penche**.

| Signal | Ce que c'est | Ce qu'il raconte |
|---|---|---|
| **Attributs mutables** | Attributs qu'on peut réassigner après la construction | Plus il y en a, plus l'état peut changer sous tes pieds (en Python : classe non `frozen`, attribut réassigné hors `__init__`) |
| **Affectations** | Les `=`, `+=`, `-=`… | Chaque affectation est un état qui évolue ; un code qui en a peu se lit comme une suite de valeurs |
| **Boucles** | `for`, `while` | Souvent remplaçables par une compréhension ou un `map`/`filter` qui dit *quoi* au lieu de *comment* |
| **Lambdas** | Petites fonctions anonymes | Un style plus déclaratif ; l'arbitre en récompense un peu |

C'est un parti pris de l'atelier (le style fonctionnel facilite la lecture et le test), pas une vérité universelle.

## Comment l'arbitre note

En résumé, il récompense la **baisse** de ces chiffres d'un baby step à l'autre, avec des **plafonds** pour qu'une seule
métrique ne fasse pas tout le score. La complexité cyclomatique pèse plus que les tokens. Une dégradation du couplage
(CK) fait perdre quelques points. Le barème exact apparaît dans le commentaire de l'arbitre sur ta PR, ligne par
ligne : c'est lui la référence, pas ce document.

Quelques badges viennent de ces mesures : **🤏 Small diff** (peu de tokens modifiés) et **🧹 Clean Coder** (les
métriques de qualité s'améliorent d'un seuil minimum).

## Ce que les métriques ne voient pas

- **Le nommage.** Un nom trompeur ne coûte rien en tokens ni en complexité.
- **Le domaine.** Aucun chiffre ne dit si la classe porte la bonne idée métier.
- **Le bon découpage.** Découper en dix classes fait baisser le WMC de chacune, et peut rendre l'ensemble illisible.
  C'est pourquoi le nombre de classes est affiché mais **jamais noté**.
- **Les tests.** Ils ne sont pas dans le périmètre.

Les chiffres t'aident à trouver où regarder. Ils ne disent pas quoi faire.

## Pour aller plus loin

- Complexité cyclomatique : Thomas McCabe, *A Complexity Measure* (1976)
- Complexité cognitive : G. Ann Campbell, *Cognitive Complexity* (SonarSource)
- WMC, CBO, LCOM : Chidamber & Kemerer, *A Metrics Suite for Object Oriented Design* (1994)
- Outils du harnais Java : [PMD](https://pmd.github.io/), [CK](https://github.com/mauricioaniche/ck),
  [JTokkit](https://github.com/knuddelsgmbh/jtokkit)
