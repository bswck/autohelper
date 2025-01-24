from __future__ import annotations

from collections.abc import Generator, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, TypedDict

import arc
import hikari
import logfire
from hikari.impl.config import CacheSettings, HTTPSettings, ProxySettings
from hikari.internal.data_binding import JSONDecoder, JSONEncoder

from autohelper.framework.app_settings import AppSettings, get_app_settings
from autohelper.framework.utils import errors

if TYPE_CHECKING:
    from _typeshed import StrPath

__all__ = (
    "App",
    "BotArgs",
    "RunArgs",
    "configure",
    "get_app",
    "run",
)


_app_state_var: ContextVar[App] = ContextVar("app_state")
get_app, _set_app = _app_state_var.get, _app_state_var.set


class BotArgs(TypedDict, total=False):
    allow_color: bool
    banner: str | None
    force_color: bool
    cache_settings: CacheSettings | None
    http_settings: HTTPSettings | None
    dumps: JSONEncoder
    loads: JSONDecoder
    intents: hikari.Intents
    auto_chunk_members: bool
    logs: StrPath | int | dict[str, Any]
    max_rate_limit: float
    max_retries: int
    proxy_settings: ProxySettings | None
    rest_url: str | None


class RunArgs(TypedDict, total=False):
    activity: hikari.Activity | None
    afk: bool
    check_for_updates: bool
    coroutine_tracking_depth: int | None
    enable_signal_handlers: bool | None
    idle_since: datetime | None
    ignore_session_start_limit: bool
    large_threshold: int
    propagate_interrupts: bool
    status: hikari.Status
    shard_ids: Sequence[int] | None
    shard_count: int | None


@dataclass
class App:
    settings: AppSettings
    _modules: tuple[ModuleType, ...] = field(init=False, default=())

    @cached_property
    def bot_args(self) -> BotArgs:
        return BotArgs()

    @cached_property
    def run_args(self) -> RunArgs:
        return RunArgs()

    @cached_property
    def bot(self) -> hikari.GatewayBot:
        return hikari.GatewayBot(
            self.settings.bot_token.get_secret_value(),
            suppress_optimization_warning=True,
            executor=ThreadPoolExecutor(thread_name_prefix="autohelper_"),
            **self.bot_args,
        )

    @cached_property
    def client(self) -> arc.GatewayClient:
        return arc.GatewayClient(
            self.bot,
            default_enabled_guilds=self.settings.default_enabled_guilds,
            is_dm_enabled=self.settings.dm_enabled,
        )

    def _module_importer(self) -> Generator[ModuleType]:
        with errors("Can't import all modules") as maybe:
            for package_name in (
                *self.settings.install_modules,
                *self.settings.extra_modules,
            ):
                with logfire.span(
                    "Importing {package_name}", package_name=package_name
                ):
                    module = maybe(import_module)(package_name)
                    if module:
                        logfire.info(
                            "Imported {package_name}", package_name=package_name
                        )
                        yield module

    def import_modules(self) -> None:
        self._modules = tuple(self._module_importer())

    @property
    def modules(self) -> tuple[ModuleType, ...]:
        return self._modules

    def run(self) -> None:
        import __main__

        logfire.debug("Modules: {modules}", modules=self.modules)

        with logfire.span(
            "Starting the bot initiated by {module}...",
            module=Path(__main__.__file__).relative_to(Path.cwd()),
        ):
            self.bot.run(
                **self.run_args,
                asyncio_debug=__debug__,
                close_passed_executor=True,
            )


def configure() -> None:
    app = App(get_app_settings())
    _set_app(app)
    app.import_modules()


def run() -> None:
    get_app().run()
