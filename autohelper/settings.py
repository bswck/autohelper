from __future__ import annotations

__all__ = ("AutoHelperSettings",)

import asyncio
import importlib
from contextvars import ContextVar
from os import getenv
from pathlib import Path
from typing import Any, cast

from pydantic import Field, SecretStr, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)

from autohelper import features as features_pkg

app_settings_var: ContextVar[AutoHelperSettings] = ContextVar("app_settings")


def get_default_feature_names() -> list[str]:
    return [
        importlib.import_module(f"{features_pkg.__name__}.{module}").__name__
        for module in getattr(features_pkg, "default_features", ())
    ]


class AutoHelperSettings(
    BaseSettings,
    env_prefix="AUTOHELPER_",
    env_file=getenv("AUTOHELPER_ENV_FILE") or ".env",
    toml_file=getenv("AUTOHELPER_CONFIG_FILE") or "autohelper.toml",
):
    cache_db_filename: Path
    bot_token: SecretStr
    dm_enabled: bool = True
    default_enabled_guilds: list[int] = Field(default_factory=list)
    install_features: list[str] | None = Field(
        default_factory=get_default_feature_names
    )

    features: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]  # python/mypy#1362
    @property
    def cache_db_url(self) -> str:
        path = str(self.cache_db_filename)
        return str(MultiHostUrl.build(scheme="sqlite+aiosqlite", hosts=[], path=path))

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Define the sources and their order for loading the settings values.

        Args:
            settings_cls: The Settings class.
            init_settings: The `InitSettingsSource` instance.
            env_settings: The `EnvSettingsSource` instance.
            dotenv_settings: The `DotEnvSettingsSource` instance.
            file_secret_settings: The `SecretsSettingsSource` instance.

        Returns:
            A tuple containing the sources and their order for loading.

        """
        toml_settings = TomlConfigSettingsSource(
            settings_cls=settings_cls,
            toml_file=cls.model_config.get("toml_file"),
        )
        return (
            init_settings,
            toml_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


async def get_app_settings_async() -> AutoHelperSettings:
    """Get the application settings without blocking the event loop."""
    settings = app_settings_var.get(None)
    if settings is None:
        settings = cast(AutoHelperSettings, await asyncio.to_thread(AutoHelperSettings))  # type: ignore[call-arg]
        app_settings_var.set(settings)
    return settings


def get_app_settings() -> AutoHelperSettings:
    """Get the application settings."""
    settings = app_settings_var.get(None)
    if settings is None:
        settings = AutoHelperSettings()  # type: ignore[call-arg]
        app_settings_var.set(settings)
    return settings
