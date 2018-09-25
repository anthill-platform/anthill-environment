
from anthill.common.options import options

from . import handler as h
from . import admin
from . import options as _opts

from anthill.common import server, access, database

from . model.environment import EnvironmentModel
from . model.application import ApplicationsModel


class EnvironmentServer(server.Server):
    def __init__(self):
        super(EnvironmentServer, self).__init__()

        self.db = database.Database(
            host=options.db_host,
            database=options.db_name,
            user=options.db_username,
            password=options.db_password)

        self.environment = EnvironmentModel(self.db)
        self.applications = ApplicationsModel(self.db, self.environment)

    def get_models(self):
        return [self.environment, self.applications]

    def get_admin(self):
        return {
            "index": admin.RootAdminController,
            "apps": admin.ApplicationsController,
            "app": admin.ApplicationController,
            "new_app": admin.NewApplicationController,
            "app_version": admin.ApplicationVersionController,
            "new_app_version": admin.NewApplicationVersionController,
            "envs": admin.EnvironmentsController,
            "environment": admin.EnvironmentController,
            "new_env": admin.NewEnvironmentController,
            "vars": admin.EnvironmentVariablesController,
        }

    def get_metadata(self):
        return {
            "title": "Environment",
            "description": "Sandbox Test environment from Live",
            "icon": "cube"
        }

    def get_internal_handler(self):
        return h.InternalHandler(self)

    def get_handlers(self):
        return [
            (r"/(.*)/(.*)", h.DiscoverHandler),
        ]


if __name__ == "__main__":
    stt = server.init()
    access.AccessToken.init([access.public()])
    server.start(EnvironmentServer)
