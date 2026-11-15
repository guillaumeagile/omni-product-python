"""L'ubiquitous language du domaine : à quel contexte borné appartient un nom.

Le fichier `docs/ubiquitous-language.json` liste, par contexte, les mots du métier. Un nom (méthode, attribut,
type) est rattaché à un contexte si un de ses mots-clés apparaît dedans, mot entier par mot entier, sans tenir
compte de la casse ni du pluriel.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

LANGUAGE_PATH = Path(__file__).resolve().parents[2] / "docs" / "ubiquitous-language.json"

_WORD = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


def words(name: str) -> tuple[str, ...]:
    """`getProductSlug`, `product_slug` et `ProductSlugs` donnent tous un mot-clé sous forme de mots en minuscules.

    Le pluriel est replié (`products` → `product`) pour que `Products` et `Product` se rencontrent.
    """
    folded: list[str] = []
    for word in _WORD.findall(name):
        lower = word.lower()
        if len(lower) > 3 and lower.endswith("s") and not lower.endswith("ss"):
            lower = lower[:-1]
        folded.append(lower)
    return tuple(folded)


@dataclass(frozen=True)
class Keyword:
    concern: str
    words: tuple[str, ...]
    weak: bool


@dataclass(frozen=True)
class UbiquitousLanguage:
    keywords: tuple[Keyword, ...]
    # Mots des identifiants naturels (SIREN, TVA…) : une donnée du métier, jamais un lien vers une autre entité.
    natural_words: frozenset[str] = frozenset()
    # Mots sans sens métier (id, get, name…) : un nom qui n'en contient pas d'autres n'est pas un trou de l'ubiquitous language.
    generic_words: frozenset[str] = frozenset()

    @classmethod
    def load(cls, path: Path = LANGUAGE_PATH) -> "UbiquitousLanguage":
        data = json.loads(path.read_text(encoding="utf-8"))
        weak = set(data.get("weakConcerns", []))
        natural = frozenset(
            word for identifier in data.get("naturalIdentifiers", []) for word in words(identifier)
        )
        generic = frozenset(word for term in data.get("genericWords", []) for word in words(term))
        return cls(
            tuple(
                Keyword(concern, words(keyword), concern in weak)
                for concern, keywords in data["concerns"].items()
                for keyword in keywords
            ),
            natural,
            generic,
        )

    def is_generic(self, word: str) -> bool:
        return word in self.generic_words

    def is_link(self, name: str) -> bool:
        """Un identifiant qui renvoie vers une autre entité : `product_id`, `supplierIds`.

        Il se termine par `id` ou `ids`, et ne contient aucun mot d'identifiant naturel (`tvaId` reste une donnée).
        Un lien ne porte pas de contexte : il dit seulement quelle entité est visée.
        """
        parts = words(name)
        return (
            len(parts) > 1
            and parts[-1] in ("id", "ids")
            and not self.natural_words.intersection(parts)
        )

    def concern_of(self, name: str) -> str | None:
        """Le contexte d'un nom, ou `None` s'il ne contient aucun mot-clé.

        Le mot-clé le plus précis gagne (le plus de mots, puis le plus long). Un contexte faible ne compte que si
        aucun contexte fort ne correspond.
        """
        name_words = words(name)
        matches = [kw for kw in self.keywords if _contains(name_words, kw.words)]
        strong = [kw for kw in matches if not kw.weak]
        candidates = strong or matches
        if not candidates:
            return None
        best = max(candidates, key=lambda kw: (len(kw.words), sum(map(len, kw.words))))
        return best.concern


def _contains(name_words: tuple[str, ...], keyword_words: tuple[str, ...]) -> bool:
    size = len(keyword_words)
    return any(name_words[i : i + size] == keyword_words for i in range(len(name_words) - size + 1))
