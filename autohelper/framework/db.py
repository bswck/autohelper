from sqlalchemy.orm import registry

__all__ = ("db_cache_metadata",)

db_cache_registry = registry()
db_cache_metadata = db_cache_registry.metadata
