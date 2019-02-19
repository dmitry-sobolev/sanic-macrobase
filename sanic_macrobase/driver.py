from typing import List, ClassVar
import logging.config

from macrobase_driver.driver import MacrobaseDriver
from macrobase_driver.logging import get_logging_config

from sanic_macrobase.config import SanicDriverConfig
from sanic_macrobase.route import Route

from structlog import get_logger
from sanic import Sanic, Blueprint
from sanic.config import Config


log = get_logger('SanicDriver')


class SanicDriver(MacrobaseDriver):

    def __init__(self, name: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = name
        self.config = SanicDriverConfig()
        self._routes = []
        self._preload_server()

    def _preload_server(self):
        self._sanic = Sanic(name=self.name, log_config=get_logging_config(self.config))
        self._sanic.config = Config()

    def update_config(self, config_obj: ClassVar[SanicDriverConfig]):
        """
        Add sanic driver config
        """
        self.config.from_object(config_obj)

    def add_routes(self, routes: List[Route]):
        """
        Add HTTP routes
        """
        self._routes.extend(routes)

    def _apply_routes(self):
        prefix = self.config.APP_BLUEPRINT

        if prefix is None or len(prefix) == 0:
            server = self._sanic
        else:
            server = Blueprint(prefix, url_prefix=prefix)

        [server.add_route(
            r.handler,
            r.uri,
            methods=r.methods,
            host=r.host,
            strict_slashes=r.strict_slashes,
            version=r.version,
            name=r.name) for r in self._routes]

        if isinstance(server, Blueprint):
            self._sanic.blueprint(server)

    def _apply_logging(self):
        self._logging_config = get_logging_config(self.config)
        logging.config.dictConfig(self._logging_config)

    def _prepare_server(self):
        self._sanic.config.from_object(self.config)
        # self._apply_logging()
        self._apply_routes()

    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)

        self._prepare_server()

        self._sanic.run(
            host=self.config.APP_HOST,
            port=self.config.APP_PORT,
            debug=self.config.DEBUG,
            workers=self.config.WORKERS)