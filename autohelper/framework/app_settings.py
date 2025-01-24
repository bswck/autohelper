from __future__ import annotations

import asyncio
import sys
from contextvars import ContextVar
from itertools import filterfalse
from os import getenv
from pathlib import Path
from typing import Any, Self, cast

from pydantic import DirectoryPath, Field, SecretStr, computed_field, model_validator
from pydantic_core import MultiHostUrl
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)

from autohelper import default_modules

__all__ = (
    "AppSettings",
    "get_app_settings",
    "get_app_settings_async",
)

app_settings_var: ContextVar[AppSettings] = ContextVar("app_settings")


class AppSettings(
    BaseSettings,
    env_prefix="AUTOHELPER_",
    env_file=getenv("AUTOHELPER_ENV_FILE") or ".env",
    toml_file=getenv("AUTOHELPER_CONFIG_FILE") or "autohelper.toml",
):
    cache_db_filename: Path
    bot_token: SecretStr
    dm_enabled: bool = True
    quiet: bool = False
    autohelper_development: bool = Field(default=False)
    default_enabled_guilds: list[int] = Field(default_factory=list)
    install_modules: list[str] = Field(default=default_modules)
    extra_modules: list[str] = Field(default_factory=list)
    python_path: list[DirectoryPath] = Field(default_factory=list)

    modules: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def side_effects(self) -> Self:
        sys.path.extend(filterfalse(sys.path.__contains__, map(str, self.python_path)))
        return self

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


async def get_app_settings_async() -> AppSettings:
    """Get the application settings without blocking the event loop."""
    settings = app_settings_var.get(None)
    if settings is None:
        settings = cast(AppSettings, await asyncio.to_thread(AppSettings))  # type: ignore[call-arg]
        app_settings_var.set(settings)
    return settings


def get_app_settings() -> AppSettings:
    """Get the application settings."""
    settings = app_settings_var.get(None)
    if settings is None:
        settings = AppSettings()  # type: ignore[call-arg]
        app_settings_var.set(settings)
    return settings
