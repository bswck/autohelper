__all__ = (
    "event",
    "register_event",
)

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, dataclass_transform, overload

import logfire


def register_event(event_class: type[object]) -> None:
    logfire.debug("Registered event model {event_class}", event_class=event_class)


type ModelDecorator[M] = Callable[[M], M]


if TYPE_CHECKING:

    @overload
    @dataclass_transform()
    def event[M](event_class: None = None) -> ModelDecorator[M]: ...

    @overload
    @dataclass_transform()
    def event[M](event_class: type[M]) -> type[M]: ...


def event[M](event_class: type[M] | None = None) -> type[M] | ModelDecorator[M]:
    if event_class is None:
        return partial(event)  # type: ignore[return-value]
    register_event(event_class)
    return event_class
