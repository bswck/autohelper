from __future__ import annotations

from collections.abc import Callable
from threading import local
from typing import Any

from pydantic import BaseModel

from autohelper.framework import debugging
from autohelper.framework.app import get_app
from autohelper.framework.app_settings import get_app_settings
from autohelper.framework.utils import guess_module_name

__all__ = ("get_settings", "read_settings", "setup")


settings_registry = local()


def get_settings(name: str | None = None, *, _stack_offset: int = 1) -> Any:
    if name is None:
        name = guess_module_name(stack_offset=_stack_offset + 1)
    settings = getattr(settings_registry, name, None)
    if settings is None:
        msg = f"{name!r} settings not found"
        raise LookupError(msg)
    return settings


def read_settings[SettingsModel: BaseModel](
    settings_class: type[SettingsModel],
    name: str | None = None,
    *,
    section: str,
) -> SettingsModel:
    name = name or guess_module_name(stack_offset=2)
    app_settings = get_app_settings()
    settings = settings_class(**app_settings.modules.get(section) or {})
    setattr(settings_registry, name, settings)
    debugging.save_location(settings, stack_offset=2)
    return settings


def setup[Func: Callable[[], object]](func: Func) -> Func:
    if get_app(None):
        func()
    return func
