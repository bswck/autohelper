import arc

from autohelper.framework.app import get_app
from autohelper.framework.settings import setup
from autohelper.framework.utils import guess_module_name

__all__ = ("setup_plugin",)


def setup_plugin(name: str | None = None) -> arc.GatewayPlugin:
    name = name or guess_module_name()
    plugin = arc.GatewayPlugin(name)
    setup(lambda: get_app().client.add_plugin(plugin))
    return plugin
