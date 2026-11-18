# omni-product (port Python)

Port de `omni-product-spring-boot-java-bdxio-phase1` : le cœur métier et ses services, données en mémoire. L'API HTTP est retirée pour l'instant ; elle sera réécrite.

| Java | Python |
|---|---|
| Spring Data `JpaRepository` | ports `ContextRepository[T]` / `SupplierRepository`, adaptateurs en mémoire (`infrastructure/persistence/in_memory.py`) |
| RestTemplate | httpx |
| JUnit / AssertJ | pytest |

## Commandes

```bash
uv sync                                          # installe les dépendances (.venv)
uv run ruff check . && uv run ruff format --check .   # lint + format
uv run pyright                                   # types (mode strict)
uv run pytest                                    # tests
uv build                                         # wheel + sdist dans dist/
```
