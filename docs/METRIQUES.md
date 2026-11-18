# Les métriques de l'arbitre, pour les curieux

Pendant l'atelier, l'arbitre commente chaque PR avec un tableau de chiffres. Ce document explique **ce que mesure
chaque chiffre, et pourquoi on le regarde**. Tu n'as pas besoin de le lire pour jouer : il est là si tu veux comprendre
ce que le tableau dit de ton code.

> **Une règle d'or avant de commencer.** Une métrique est un thermomètre. Si tu écris du code pour
> faire baisser un chiffre, tu fabriques du code étrange qui plaît au thermomètre. Écris le code le plus clair
> possible, puis regarde ce que les chiffres en disent. C'est l'inverse qui ne marche pas.

## Ce qui est mesuré

Seul le code que tu fais évoluer est mesuré : le **modèle**, l'**infrastructure** et la **persistance** (`dal/`). Les
tests, le controller, les services et le harnais ne comptent pas. `dal/` est mesuré pour que la persistance qui
passe dans `infrastructure/` (règle 10) ne compte pas comme du code ajouté. L'arbitre compare ton code à celui de ton baby step précédent : c'est la **variation** qui
compte, pas la valeur absolue.

Les mesures sont déterministes : le même code donne toujours les mêmes chiffres.

## 1. Le coût de lecture : les tokens

**Ce que c'est.** Un token est un morceau de texte, à peu près un mot ou un bout de mot, tel qu'un modèle de langage le
découpe. `ProductNameException` fait plusieurs tokens, `if` en fait un.

**Pourquoi on le regarde.** Un agent (ou un humain pressé) paie à la lecture : plus il y a de tokens, plus il y a à
lire, à comprendre et à garder en tête. Moins de tokens, c'est souvent moins de répétition, moins de code mort,
moins de cérémonie.

**Ce qui est compté.** Le **code efficace** seulement : ni les commentaires, ni les docstrings, ni la mise en forme
(espaces, retours à la ligne), ni les tests. Commenter ne coûte donc rien, et réécrire sans commentaires ne fait rien
gagner : seul le code qui s'exécute pèse.

**Comment c'est compté.** Avec `tiktoken`, l'encodage `o200k_base`. Ce n'est pas le découpage exact de tous les modèles,
mais l'ordre de grandeur est juste, et surtout les **variations** d'une PR à l'autre sont fidèles.

**Le piège.** Raccourcir les noms (`price` devient `p`) fait baisser les tokens et dégrade le code. Lisible avant court.

**Le petit diff.** L'arbitre compte aussi les tokens de **ta modification** (les lignes de code ajoutées et retirées, commentaires exclus). Une PR
qui change peu est facile à relire et facile à annuler : c'est l'esprit du *baby step*. Une PR qui ne modifie aucun
token de code du périmètre est une **PR vide** : elle coûte 5 points. Un changement de commentaires seuls, de tests
seuls ou de documentation seule en fait partie.

## 2. Le nombre de chemins : la complexité cyclomatique

**Ce que c'est.** Le nombre de chemins indépendants dans une fonction. Une fonction sans `if` a un chemin (valeur 1).
Chaque `if`, `for`, `while`, `and`, `or` ou `except` en ajoute un.

```python
def frais(poids, express):  # 1 chemin de base
    if poids > 20:  # +1
        return 30
    if express and poids > 5:  # +1 pour le if, +1 pour le and
        return 15
    return 5  # complexité = 4
```

**Pourquoi on le regarde.** C'est le nombre de tests minimum pour couvrir la fonction. À 4, il faut 4 cas de test. À
15, plus personne n'ose y toucher.

**Ce que l'arbitre additionne.** La somme sur toutes les fonctions et méthodes du périmètre. Une méthode au corps vide
(`...`, `pass`, une docstring seule) compte 0 : c'est une signature, comme celles d'un port (`Protocol`). Retirer des branches
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

**Ce que l'arbitre en fait.** Il affiche le total, sans points. La cognitive suit de près la cyclomatique : noter
les deux compterait deux fois les mêmes branches. Seule la cyclomatique rapporte des points.

## 5. Le couplage : fan-out (et CBO)

**Ce que c'est.** Le nombre d'autres types dont une classe dépend. Le **fan-out** est PMD, le **CBO** (*Coupling
Between Objects*) est CK : deux outils, la même idée.

**Pourquoi on le regarde.** Plus une classe connaît de monde, plus elle casse quand l'un d'eux change. C'est le
« C » de Composable dans CUPID : un bon module se branche sur peu de choses.

**Ce qui ne compte pas.** La bibliothèque standard et `result` : c'est le socle que la règle 10 permet au cœur.

## 6. La cohésion : TCC (et LCOM)

**Ce que c'est.** Parmi les paires de méthodes d'une classe, quelle part utilise au moins un attribut en commun. Valeur
de 0 à 1 : à 1, toutes les méthodes travaillent sur les mêmes données.

**Pourquoi on le regarde.** Une classe cohésive fait une seule chose. Une classe à faible cohésion est deux classes
collées ensemble : un groupe de méthodes sur un groupe d'attributs, un autre groupe sur un autre. C'est le signal
« tu peux la couper en deux ». **LCOM** est la mesure inverse (le manque de cohésion) : plus haut, c'est pire.

L'arbitre regarde la **pire** classe (TCC minimum). Une classe dont aucune méthode ne touche d'attribut, comme un port
(`Protocol`), n'a pas de cohésion mesurable : elle n'entre pas dans ce minimum.

## 7. Les signaux de style : états, boucles, lambdas

Ces compteurs ne jugent pas le code bon ou mauvais. Ils indiquent **vers quel style il penche**.

| Signal | Ce que c'est | Ce qu'il raconte |
|---|---|---|
| **Attributs mutables** | Attributs qu'on peut réassigner après la construction | Plus il y en a, plus l'état peut changer sous tes pieds (en Python : classe non `frozen`, attribut réassigné hors `__init__`) |
| **Affectations** | Les `=`, `+=`, `-=`… | Chaque affectation est un état qui évolue ; un code qui en a peu se lit comme une suite de valeurs |
| **Boucles** | `for`, `while` | Souvent remplaçables par une compréhension ou un `map`/`filter` qui dit *quoi* au lieu de *comment* |
| **Lambdas** | Petites fonctions anonymes | Un style plus déclaratif. Un thermomètre, sans points : sur une liste, la compréhension reste préférée à `map(lambda ...)` (règle 8) |
| **Lambdas sur les rails (ROP)** | Les lambdas passées à `.map`, `.and_then`, `.map_err`… d'un `Result` | Le style que vise la règle 9 : l'arbitre en récompense un peu |

C'est un parti pris de l'atelier (le style fonctionnel facilite la lecture et le test), pas une vérité universelle.

## 8. Les couches : les métriques de Robert Martin

**Ce que c'est.** Les mesures précédentes regardent une classe. Celles-ci regardent une **couche** (`domain`,
`infrastructure`, `dal`…) et le **sens** de ses liens avec les autres.

| Mesure | Ce que c'est |
|---|---|
| **Ca** (couplage afférent) | Les modules d'autres couches qui importent celle-ci. Ils cassent quand elle change. |
| **Ce** (couplage efférent) | Les modules de la couche qui importent une autre couche. Elle casse quand l'autre change. |
| **I** (instabilité) | Ce / (Ca + Ce). À 0, tout le monde dépend d'elle et elle ne dépend de rien : elle est stable. À 1, l'inverse. |
| **A** (abstraction) | La part de ses classes qui sont abstraites : `Protocol`, `ABC`, une `@abstractmethod`. |
| **D** (distance) | \|A + I − 1\|. À 0, la couche est sur la *séquence principale*. |

**Pourquoi on le regarde.** Une couche stable doit être abstraite, une couche instable peut être concrète. Le cœur
d'une architecture en oignon est stable (on dépend de lui) et porte les ports (abstraits) : D proche de 0. Une couche
stable et concrète est dure à changer, car tout le monde en dépend. Une couche instable et abstraite déclare des
abstractions que personne n'utilise. Les deux s'éloignent de la séquence principale : D monte vers 1.

La colonne **Dépend de** montre le sens des liens. Dans une architecture en oignon, aucune flèche ne part du cœur vers
l'extérieur.

**Comment c'est compté.** L'unité est le module, là où Martin compte les classes : `dal/` n'a que des fonctions. Ca ne
voit que les modules mesurés. Le détail par couche est affiché, base → PR, et ne rapporte pas de points.

**Le chiffre du tableau.** Les couches se résument en une ligne : la **métrique Uncle Bob**, le D moyen pondéré par
le nombre de modules de chaque couche. Elle va de 0 à 1, et 0 est le mieux. D résume déjà Ca, Ce et A, qui entrent
dans I et A. La pondération donne plus de poids à une grosse couche mal placée qu'à un module isolé. Une couche sans
lien n'entre pas dans la moyenne. Cette ligne remplace les totaux de fan-out et de CBO : ils additionnaient les liens
de chaque classe sans en voir le sens. Les pires classes (fan-out et CBO max) restent dans le tableau.

**Les points.** La métrique Uncle Bob est notée avec un poids de 10 : D varie par dixièmes, et une baisse de 0,1 vaut
1 point, une hausse de 0,1 en coûte 1. Le plafond commun à toutes les métriques s'applique.

**Ce que la métrique Uncle Bob agrège.** Toutes les mesures du tableau des couches, sauf le sens des liens. D se
calcule avec I et A : D = |A + I − 1|. I se calcule lui-même avec Ca et Ce. Quand une de ces valeurs bouge, D bouge
aussi. I et A ne sont pas notés seuls, car aucun des deux n'a de bon sens : `main` doit être instable et le cœur
stable, et une abstraction de plus ne vaut que dans une couche stable. Le rapport entre les deux a un bon sens, et
c'est D.

**Le sens des liens.** D juge chaque couche seule. Il ne voit pas où pointe chaque flèche. Le *principe des
dépendances stables* le fait : une couche dépend de plus stable qu'elle. Si X dépend de Y alors que Y est plus
instable que X (I(Y) > I(X)), le lien est une **violation**. Une couche dont beaucoup dépendent casse alors à
chaque changement d'une couche qui bouge souvent. La ligne « Violations du sens des dépendances » les compte, une
fois par paire de couches. Un lien vers une couche hors du périmètre n'est pas jugé, car son I est inconnu. Chaque
violation ajoutée coûte 1 point, chaque violation retirée en rapporte 1.

## Comment l'arbitre note

En résumé, il récompense la **baisse** de ces chiffres d'un baby step à l'autre, avec des **plafonds** pour qu'une seule
métrique ne fasse pas tout le score. La complexité cyclomatique pèse plus que les tokens. Une dégradation du couplage
(CK) fait perdre quelques points. Le barème exact apparaît dans le commentaire de l'arbitre sur ta PR, ligne par
ligne : c'est lui la référence, pas ce document.

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
- Ca, Ce, I, A, D : Robert C. Martin, *OO Design Quality Metrics: An Analysis of Dependencies* (1994)
- Outils du harnais Java : [PMD](https://pmd.github.io/), [CK](https://github.com/mauricioaniche/ck),
  [JTokkit](https://github.com/knuddelsgmbh/jtokkit)
