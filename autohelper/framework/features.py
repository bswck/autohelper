from __future__ import annotations

__all__ = ("Feature", "use_config")

import importlib
from collections.abc import Callable, Sequence
from contextvars import Context, ContextVar, copy_context
from dataclasses import KW_ONLY, dataclass, field
from functools import cached_property, partial
from typing import Any

import logfire
from pydantic import BaseModel


class FeatureConfigurationError(ValueError):
    """Raised when a feature module is missing required components."""


config_var: ContextVar[BaseModel] = ContextVar("feature_config")


def get_config() -> Any:
    return config_var.get()


@dataclass(unsafe_hash=True)
class Feature:
    package_name: str
    _: KW_ONLY
    context: Context = field(default_factory=copy_context)

    @cached_property
    def package(self) -> Any:
        try:
            return importlib.import_module(self.package_name)
        except ImportError as exc:
            msg = f"Could not import {self.package_name!r}"
            raise FeatureConfigurationError(msg) from exc

    def call(
        self,
        routine_name: str,
        *,
        required: bool = False,
        warn_on_missing: bool = True,
    ) -> None:
        if (routine := getattr(self.package, routine_name, None)) is not None:
            with logfire.span(
                "Calling `{package_name}.{routine_name}`",
                routine_name=routine_name,
                package_name=self.package_name,
            ):
                self.context.run(routine)
            return
        if required:
            msg = f"Module {self.package_name!r} does not export {routine_name!r}"
            raise FeatureConfigurationError(msg)
        if warn_on_missing:
            logfire.warn(
                "Attempted to call an undefined function "
                "`{package_name}.{routine_name}`",
                package_name=self.package_name,
                routine_name=routine_name,
            )


@dataclass
class FeatureSet:
    features: Sequence[Feature]

    def call(
        self,
        routine_name: str,
        *,
        required: bool = False,
        warn_on_missing: bool = True,
    ) -> None:
        errors = {}
        for feature in self.features:
            try:
                feature.call(
                    routine_name,
                    required=required,
                    warn_on_missing=warn_on_missing,
                )
            except Exception as exc:  # noqa: BLE001
                errors[feature.package_name] = exc
        if errors:
            msg = f"Error calling {routine_name!r} on features: {', '.join(errors)}"
            raise ExceptionGroup(msg, tuple(errors.values()))


def configure[**P, M: BaseModel](
    model: Callable[P, M],
    name: str,
    hooks: Sequence[Callable[[], object]],
    /,
    *args: P.args,
    **kwargs: P.kwargs,
) -> None:
    from autohelper.settings import get_app_settings

    settings = get_app_settings()
    try:
        feature_config: M = get_config()
    except LookupError:
        feature_config = model(
            *args,
            **settings.features.get(name) or {} | kwargs,
        )
    else:
        if args or kwargs:
            feature_config = model(
                *args,
                **feature_config.model_dump(round_trip=True) | kwargs,
            )

    config_var.set(feature_config)

    exceptions = []
    for hook in hooks:
        try:
            hook()
        except Exception as exc:  # noqa: BLE001
            exceptions.append(exc)
    if exceptions:
        msg = "Error calling configuration hooks"
        raise ExceptionGroup(msg, exceptions)


def use_config[**P, M: BaseModel](
    model: Callable[P, M],
    *,
    name: str,
    hooks: Sequence[Callable[[], object]] = (),
) -> tuple[Callable[P, None], Callable[[], M]]:
    return (
        partial(configure, model, name, hooks),  # type: ignore[call-arg]  # prob. a bug in mypy
        get_config,
    )
