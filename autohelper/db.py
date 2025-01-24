__all__ = ("cache_metadata",)

from sqlalchemy.orm import registry

cache_registry = registry()
cache_metadata = cache_registry.metadata
