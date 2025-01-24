import logfire

default_modules: tuple[str, ...] = (
    "activities",
    "decorations",
    "journal",
    "logs",
)


def go() -> None:
    from autohelper.framework import configure, run

    logfire.configure()
    configure()
    run()
