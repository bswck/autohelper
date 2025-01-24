import inspect
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any, NamedTuple

__all__ = (
    "get_frame_location",
    "get_location",
    "get_location_info",
    "save_location",
)

LOCATION_ATTR = "__object_location__"


class LocationInfo(NamedTuple):
    filename: str
    lineno: int


def get_frame_location(*, offset: int = 1) -> LocationInfo | None:
    if not __debug__:
        return None
    frame_info = inspect.getframeinfo(sys._getframe(offset))  # noqa: SLF001
    return LocationInfo(
        filename=frame_info.filename,
        lineno=frame_info.lineno,
    )


def save_location(obj: Any, *, stack_offset: int = 1) -> None:
    if not __debug__:
        return
    location = get_frame_location(offset=stack_offset + 1)
    try:
        obj.__dict__[LOCATION_ATTR] = location
    except Exception:  # noqa: BLE001
        with suppress(Exception):
            object.__setattr__(obj, LOCATION_ATTR, location)


def get_location_info(obj: object) -> LocationInfo | None:
    return getattr(obj, LOCATION_ATTR, None)


def get_location(obj: Any) -> str:
    if not __debug__:
        return ""
    frame_info: LocationInfo | None = get_location_info(obj)
    if not frame_info:
        try:
            source_filename = frame_info or inspect.getsourcefile(obj)
        except (OSError, TypeError):
            return ""
        else:
            _, source_lineno = inspect.findsource(obj)
            source_lineno += 1
    else:
        source_filename = frame_info.filename
        source_lineno = frame_info.lineno
    if not source_filename:
        return ""
    return f"{Path(source_filename).relative_to(Path.cwd())}:{source_lineno}"
