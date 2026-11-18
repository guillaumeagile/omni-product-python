# omni-product (port Python)

Port de `omni-product-spring-boot-java-bdxio-phase1` : FastAPI, données en mémoire.

| Java | Python |
|---|---|
| Spring Boot / MVC | FastAPI |
| Spring Data `JpaRepository` | ports `ProductRepository` / `SupplierRepository`, adaptateurs en mémoire (`infrastructure/persistence/in_memory.py`) |
| RestTemplate | httpx |
| Jackson | Pydantic (JSON en camelCase) |
| JUnit / AssertJ / MockMvc | pytest / `TestClient` |

## Commandes

```bash
uv sync                                          # installe les dépendances (.venv)
uv run ruff check . && uv run ruff format --check .   # lint + format
uv run pyright                                   # types (mode strict)
uv run pytest                                    # tests
uv build                                         # wheel + sdist dans dist/
uv run uvicorn omni_product.main:app --reload    # lance l'API (http://localhost:8000/docs)
```
