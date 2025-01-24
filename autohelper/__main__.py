import logfire

from autohelper.framework import Feature


def main(entrypoint: str = __package__ or __name__.rsplit(".")[0]) -> None:
    logfire.configure()
    this = Feature(package_name=entrypoint)
    this.call("configure")
    this.call("run")


if __name__ == "__main__":
    main()
