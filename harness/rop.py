"""Le vocabulaire de la Railway Oriented Programming (ROP) sur le `Result` de la bibliothèque `result`.

Un `Result` est `Ok` ou `Err`. Les étapes s'enchaînent par des méthodes qui gardent le train sur les rails : à la
première erreur, il bascule sur le rail d'échec et saute les étapes suivantes, sans `if` ni `try`.

La règle 9 (`harness.rules.style_fonctionnel`) et la métrique « Lambdas sur les rails » (`harness.metrics.style`)
lisent ce module : elles parlent des mêmes rails.
"""

# Le module de la bibliothèque retenue (voir docs/python-regles-de-harnais.md, « Les ADT en Python »).
RESULT_MODULE = "result"

# Les méthodes qui gardent le train sur les rails. Une `lambda` passée à l'une d'elles est une étape du chemin.
RAIL_METHODS = frozenset(
    {
        "map",
        "map_async",
        "map_err",
        "map_or",
        "map_or_else",
        "and_then",
        "and_then_async",
        "or_else",
        "inspect",
        "inspect_err",
        "unwrap_or_else",
    }
)

# Les méthodes qui sortent des rails en levant une exception quand le cas attendu n'est pas là.
RAISING_EXITS = frozenset({"unwrap", "unwrap_err", "expect", "expect_err", "unwrap_or_raise"})

# Les méthodes et fonctions qui demandent « succès ou échec ? » pour brancher à la main.
MANUAL_SWITCHES = frozenset({"is_ok", "is_err"})

# Les deux cas d'un `Result`, par nom qualifié.
OK = f"{RESULT_MODULE}.Ok"
ERR = f"{RESULT_MODULE}.Err"
