from omni_product.exception.business_exception import BusinessException


class ProductNameException(BusinessException):
    """Traduite en HTTP 424 (Failed Dependency) comme le `@ResponseStatus` Java."""
