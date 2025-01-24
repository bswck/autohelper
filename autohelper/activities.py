from typing import Self

import hikari
from pydantic import model_validator
from pydantic_settings import BaseSettings

from autohelper.framework import get_app, read_settings, setup_plugin

plugin = setup_plugin()


class ActivitySettings(BaseSettings):
    initial_activity_name: str | None = None
    initial_activity_state: str | None = None

    @model_validator(mode="after")
    def side_effects(self) -> Self:
        app = get_app()
        if self.initial_activity_name:
            app.run_args["activity"] = hikari.Activity(
                name=self.initial_activity_name,
                state=self.initial_activity_state,
            )
        return self


settings = read_settings(ActivitySettings, section="activities")
