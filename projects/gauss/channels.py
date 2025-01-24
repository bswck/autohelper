import arc
from pydantic import BaseModel

from autohelper.abstract.channels import Category, GuildTextChannel
from autohelper.framework import read_settings
from autohelper.framework.app import get_app

app = get_app()
plugin = arc.GatewayPlugin(__name__)
app.client.add_plugin(plugin)


class CommunityCategory(Category):
    main: GuildTextChannel
    forum: GuildTextChannel


class InternalCategory(Category):
    admins: GuildTextChannel


class ChannelsConfig(BaseModel):
    community: CommunityCategory
    internal: InternalCategory


settings = read_settings(ChannelsConfig, section="channels")
