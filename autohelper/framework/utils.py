# ruff: noqa: BLE001

from __future__ import annotations

import sys
from collections.abc import Generator, MutableSequence
from contextlib import ContextDecorator, contextmanager, suppress

__all__ = ("errors", "guess_module_name")


type Maybe = ContextDecorator[None]


@contextmanager
def maybe_context(caught: MutableSequence[Exception]) -> Generator[None]:
    try:
        yield
    except Exception as exception:
        caught.append(exception)


@contextmanager
def errors(message: str = "Caught some exceptions") -> Generator[Maybe]:
    caught: MutableSequence[Exception] = []
    try:
        yield maybe_context(caught)
    except Exception as exception:
        caught.append(exception)

    if caught:
        try:
            raise ExceptionGroup(message, caught)
        finally:
            caught.clear()


def guess_module_name(stack_offset: int = 2, default: str = "__main__") -> str:
    with suppress(AttributeError):
        return sys._getframemodulename(stack_offset) or default
    return sys._getframe(stack_offset).f_globals.get("__name__", default)
