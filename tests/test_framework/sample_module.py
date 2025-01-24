from collections.abc import Callable


def some_function(callback: Callable[..., object]) -> None:
    callback()
