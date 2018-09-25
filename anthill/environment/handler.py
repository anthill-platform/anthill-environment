

from tornado.web import HTTPError

from anthill.common.handler import JsonHandler

from . model.environment import EnvironmentNotFound
from . model.application import ApplicationNotFound


class InternalHandler(object):
    def __init__(self, application):
        self.application = application

    async def get_app_info(self, app_name):
        applications = self.application.applications

        try:
            app = await applications.find_application(app_name)
        except ApplicationNotFound:
            raise HTTPError(404, "Application {0} was not found".format(app_name))

        application_id = app.application_id

        versions = await applications.list_application_versions(application_id)

        return {
            "id": app.application_id,
            "name": app.name,
            "title": app.title,
            "versions": {
                version.name: version.version_id
                for version in versions
            }
        }

    async def get_apps(self):

        applications = self.application.applications
        apps = await applications.list_applications()

        return [
            {
                "app_id": app.application_id,
                "app_name": app.name,
                "app_title": app.title
            }
            for app in apps
        ]


class DiscoverHandler(JsonHandler):
    async def get(self, app_name, app_version):
        environment = self.application.environment

        try:
            version = await environment.get_version_environment(app_name, app_version)
        except EnvironmentNotFound:
            raise HTTPError(
                404, "Version {0} of the app {1} was not found.".format(
                    app_version, app_name))

        res = {
            "discovery": version.discovery
        }

        res.update(version.data)

        self.dumps(res)
