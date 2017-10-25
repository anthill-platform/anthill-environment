

import ujson

from tornado.gen import coroutine, Return
from tornado.web import RequestHandler, HTTPError

from common.handler import JsonHandler

from model.environment import EnvironmentNotFound
from model.application import ApplicationNotFound


class InternalHandler(object):
    def __init__(self, application):
        self.application = application

    @coroutine
    def get_app_info(self, app_name):
        applications = self.application.applications

        try:
            app = yield applications.find_application(app_name)
        except ApplicationNotFound:
            raise HTTPError(404, "Application {0} was not found".format(app_name))

        application_id = app.application_id

        versions = yield applications.list_application_versions(application_id)

        raise Return({
            "id": app.application_id,
            "name": app.name,
            "title": app.title,
            "versions": {
                version.name: version.version_id
                for version in versions
            }
        })

    @coroutine
    def get_apps(self):

        applications = self.application.applications
        apps = yield applications.list_applications()

        raise Return([
            {
                "app_id": app.application_id,
                "app_name": app.name,
                "app_title": app.title
            }
            for app in apps
        ])


class DiscoverHandler(JsonHandler):
    @coroutine
    def get(self, app_name, app_version):
        environment = self.application.environment

        try:
            version = yield environment.get_version_environment(app_name, app_version)
        except EnvironmentNotFound as e:
            raise HTTPError(
                404, "Version {0} of the app {1} was not found.".format(
                    app_version, app_name))

        discovery = version.discovery + "/v" + version.api

        res = {
            "discovery": discovery
        }

        res.update(version.data)

        self.dumps(res)
