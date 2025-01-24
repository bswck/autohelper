__all__ = (
    "configure",
    "get_config",
    "setup",
)

import arc
import hikari
from pydantic_settings import BaseSettings

from autohelper.framework import use_config
from autohelper.main import get_app_state

plugin = arc.GatewayPlugin("activities")


class ActivityConfig(BaseSettings):
    initial_activity_name: str | None = None
    initial_activity_state: str | None = None


def update_run_args() -> None:
    app, config = get_app_state(), get_config()

    if config.initial_activity_name:
        app.run_args["activity"] = hikari.Activity(
            name=config.initial_activity_name,
            state=config.initial_activity_state,
        )


configure, get_config = use_config(
    ActivityConfig,
    name=plugin.name,
    hooks=[update_run_args],
)


def setup() -> None:
    app = get_app_state()
    app.client.add_plugin(plugin)
