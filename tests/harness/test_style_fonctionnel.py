"""La règle 9 : le code s'enchaîne sur les rails d'un `Result` (ROP), sans `if` ni `try`."""

import textwrap
from pathlib import Path

from harness.rules import RULES, evaluate, style_fonctionnel
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage


def source(text: str) -> Source:
    return Source.from_text("omni_product.service.product_service", textwrap.dedent(text))


def codes_of(text: str) -> list[tuple[int, str]]:
    return [
        (f.line, f.code) for f in style_fonctionnel.check(source(text), UbiquitousLanguage.load())
    ]


def test_a_chain_on_the_rails_is_green():
    text = """
        from result import Err, Ok, Result

        def prix_ttc(produit_id: str) -> Result[float, str]:
            return (
                trouver(produit_id)
                .map(lambda produit: produit.prix)
                .and_then(appliquer_remise)
                .map(lambda prix: prix * 1.2)
            )

        def total(prix: list[float]) -> float:
            return sum(prix)
        """

    assert codes_of(text) == []


def test_an_exhaustive_match_at_the_border_is_green():
    text = """
        from result import Err, Ok

        def reponse(resultat):
            match resultat:
                case Ok(produit):
                    return {"produit": produit}
                case Err(erreur):
                    return {"erreur": str(erreur)}
        """

    assert codes_of(text) == []


def test_asking_ok_or_err_is_a_manual_switch():
    text = """
        from result import Err, is_err

        def prix(resultat):
            if resultat.is_ok():
                return resultat.ok_value
            if is_err(resultat):
                return None
            if isinstance(resultat, Err):
                return None
        """

    assert codes_of(text) == [
        (5, style_fonctionnel.MANUAL_SWITCH),
        (7, style_fonctionnel.MANUAL_SWITCH),
        (9, style_fonctionnel.MANUAL_SWITCH),
    ]


def test_isinstance_is_resolved_through_the_imports():
    text = """
        import result as r

        def f(x):
            return isinstance(x, (int, r.Ok))

        def g(x):
            return isinstance(x, Ok)
        """

    # `Ok` non importé de `result` dans `g` : ce n'est pas le `Ok` d'un `Result`.
    assert codes_of(text) == [(5, style_fonctionnel.MANUAL_SWITCH)]


def test_a_match_that_passes_the_error_through_is_a_manual_switch():
    text = """
        from result import Err, Ok

        def a(resultat):
            match resultat:
                case Ok(produit):
                    return Ok(produit.prix)
                case Err():
                    return resultat

        def b(resultat):
            match resultat:
                case Ok(produit):
                    return Ok(produit.prix)
                case Err(erreur):
                    return Err(erreur)

        def c(resultat):
            match resultat:
                case Ok(produit):
                    return Ok(produit.prix)
                case Err() as erreur:
                    return erreur
        """

    assert codes_of(text) == [
        (8, style_fonctionnel.MANUAL_SWITCH),
        (15, style_fonctionnel.MANUAL_SWITCH),
        (22, style_fonctionnel.MANUAL_SWITCH),
    ]


def test_unwrap_and_expect_leave_the_rails():
    text = """
        def f(resultat):
            produit = resultat.unwrap()
            return resultat.expect("introuvable"), resultat.unwrap_or(0)
        """

    assert codes_of(text) == [
        (3, style_fonctionnel.RAISING_EXIT),
        (4, style_fonctionnel.RAISING_EXIT),
    ]


def test_a_try_with_handlers_is_a_finding_a_try_finally_is_not():
    text = """
        def f(client):
            try:
                return client.appeler()
            except ValueError:
                return None

        def g(fichier):
            try:
                return fichier.lire()
            finally:
                fichier.fermer()
        """

    assert codes_of(text) == [(3, style_fonctionnel.TRY)]


def test_a_raise_outside_the_model_is_a_finding():
    text = """
        from fastapi import HTTPException

        def lire(produit_id):
            if produit_id is None:
                raise HTTPException(404)
            return produit_id
        """

    assert codes_of(text) == [(6, style_fonctionnel.RAISE)]


def test_a_raise_in_the_model_is_left_to_rule_5():
    for module in ("omni_product.domain.model.product", "omni_product.anemic_model.product"):
        model = Source.from_text(module, "def f() -> None:\n    raise ValueError('x')\n")

        assert style_fonctionnel.check(model, UbiquitousLanguage.load()) == []


def test_an_accumulator_in_a_loop_is_a_finding():
    text = """
        def total(lignes):
            somme = 0
            for ligne in lignes:
                somme += ligne.prix
            compte = 0
            while compte < 3:
                compte += 1
            return somme
        """

    assert codes_of(text) == [
        (5, style_fonctionnel.ACCUMULATOR),
        (8, style_fonctionnel.ACCUMULATOR),
    ]


def test_an_augmented_assignment_outside_a_loop_or_in_a_nested_function_is_not_a_finding():
    text = """
        def f(prix, lignes):
            prix += 1
            for ligne in lignes:
                def g(x):
                    x += 1
                    return x
                ligne.attribut += 1
            return prix
        """

    assert codes_of(text) == []


def test_lambdas_are_never_findings():
    text = """
        def f(produits, resultat):
            tries = sorted(produits, key=lambda p: p.prix)
            return resultat.map(lambda p: p.prix), tries
        """

    assert codes_of(text) == []


def test_a_local_variable_named_result_is_not_the_module():
    text = """
        def f(result, x):
            return isinstance(x, result.Ok)
        """

    assert codes_of(text) == []


def test_the_finding_names_the_rails():
    [finding] = style_fonctionnel.check(
        source("def f(r):\n    return r.is_ok()\n"), UbiquitousLanguage.load()
    )

    assert str(finding).startswith("omni_product/service/product_service.py:2:12: SF001 ")
    assert "`.and_then`" in finding.message


def test_rule_9_reads_controllers_and_services(tmp_path: Path):
    src = tmp_path / "src"
    for name in ("controller/api.py", "service/svc.py", "domain/model/m.py"):
        path = src / "omni_product" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def f(r):\n    return r.unwrap()\n", encoding="utf-8")

    findings = evaluate(src)

    assert [str(f).split(":")[0] for f in findings[9]] == [
        (src / "omni_product" / name).as_posix()
        for name in ("controller/api.py", "domain/model/m.py", "service/svc.py")
    ]
    # Les autres règles gardent le périmètre du cœur, sauf la 10 : elle suit tout le paquet.
    assert all(rule.hors != () for rule in RULES if rule.number not in (9, 10))
