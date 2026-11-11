"""Le coût de lecture : les tokens, comptés comme le ferait un modèle de langage (`o200k_base`)."""

from collections.abc import Callable
from functools import cache

import tiktoken


@cache
def _encoder() -> Callable[[str], list[int]]:
    encoding = tiktoken.get_encoding("o200k_base")

    def encode(text: str) -> list[int]:
        return encoding.encode(text, disallowed_special=())

    return encode


def count(text: str) -> int:
    return len(_encoder()(text))
