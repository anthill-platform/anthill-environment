
from common.options import options

import handler
import common.server
import common.handler
import common.sign
import common.access
import common.database
import common.keyvalue

from model.environment import EnvironmentModel
from model.application import ApplicationsModel

import admin
import options as _opts


class EnvironmentServer(common.server.Server):
    def __init__(self):
        super(EnvironmentServer, self).__init__()

        self.db = common.database.Database(
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
        return handler.InternalHandler(self)

    def get_handlers(self):
        return [
            (r"/(.*)/(.*)", handler.DiscoverHandler),
        ]


if __name__ == "__main__":
    stt = common.server.init()
    common.access.AccessToken.init([common.access.public()])
    common.server.start(EnvironmentServer)
