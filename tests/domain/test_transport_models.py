from omni_product.domain.model.transport import Kilos


def test_negative_weight_is_refused_by_the_value_object() -> None:
    result = Kilos.of(-2.0)

    assert result.is_err()
    assert str(result.unwrap_err()) == "Kilos ne peut pas être négatif"
