import ujson

from tornado.gen import coroutine, Return
import common.admin as a

from model.environment import EnvironmentNotFound, EnvironmentExists
from model.application import VersionNotFound, VersionExists, ApplicationNotFound, ApplicationExists, ReservedName


class ApplicationController(a.AdminController):
    @coroutine
    def delete(self, **ignored):
        record_id = self.context.get("record_id")

        applications = self.application.applications

        yield applications.delete_application(record_id)

        raise a.Redirect("apps", message="Application has been deleted")

    @coroutine
    def get(self, record_id):

        applications = self.application.applications

        try:
            app = yield applications.get_application(record_id)
        except ApplicationNotFound:
            raise a.ActionError("Application was not found.")

        versions = yield applications.list_application_versions(record_id)

        result = {
            "application_name": app.name,
            "application_title": app.title,
            "versions": versions,
        }

        raise a.Return(result)

    def render(self, data):
        return [
            a.breadcrumbs([
                a.link("apps", "Applications"),
            ], data.get("app_name", "Application")),
            a.form("Application information", fields={
                "application_name": a.field("Application ID", "text", "primary", "non-empty"),
                "application_title": a.field("Application Title", "text", "primary", "non-empty")
            }, methods={
                "update": a.method("Update", "primary", order=1),
                "delete": a.method("Delete", "danger", order=2)
            }, data=data),
            a.links("Application versions", links=[
                a.link("app_version", v.name, icon="tags", app_id=data.get("application_name"),
                       version_id=v.version_id) for v in data["versions"]
                ]),
            a.links("Navigate", [
                a.link("apps", "Go back", icon="chevron-left"),
                a.link("new_app_version", "New application version", "plus", app_id=data.get("application_name"))
            ])
        ]

    def access_scopes(self):
        return ["env_admin"]

    @coroutine
    def update(self, application_name, application_title):
        record_id = self.context.get("record_id")

        applications = self.application.applications

        try:
            yield applications.update_application(
                record_id,
                application_name,
                application_title)

        except ApplicationExists:
            raise a.ActionError("Such application already exists")

        raise a.Redirect(
            "app",
            message="Application has been updated",
            record_id=record_id)


class ApplicationVersionController(a.AdminController):
    @coroutine
    def delete(self, **ignored):

        applications = self.application.applications

        record_id = self.context.get("version_id")
        app_id = self.context.get("app_id")

        yield applications.delete_application_version(record_id)

        try:
            app = yield applications.find_application(app_id)
        except ApplicationNotFound:
            raise a.ActionError("App was not found.")

        record_id = app.application_id

        raise a.Redirect(
            "app",
            message="Application version has been deleted",
            record_id=record_id)

    @coroutine
    def get(self, app_id, version_id):

        environment = self.application.environment
        applications = self.application.applications

        try:
            app = yield applications.find_application(app_id)
        except ApplicationNotFound:
            raise a.ActionError("App was not found.")

        application_id = app.application_id

        try:
            version = yield applications.get_application_version(application_id, version_id)
        except ApplicationNotFound:
            raise a.ActionError("Application was not found.")
        except VersionNotFound:
            raise a.ActionError("Version was not found.")

        result = {
            "app_title": app.title,
            "application_id": application_id,
            "envs": (yield environment.list_environments()),
            "version_name": version.name,
            "version_env": version.environment
        }

        raise a.Return(result)

    def render(self, data):
        return [
            a.breadcrumbs([
                a.link("apps", "Applications"),
                a.link("app", data.get("app_title", "Application"), record_id=data.get("application_id")),
            ], data.get("version_name")),
            a.form("Application version", fields={
                "version_name": a.field("Version name", "text", "primary", "non-empty"),
                "version_env": a.field("Environment", "select", "primary", "non-empty", values={
                    env.environment_id: env.name for env in data["envs"]
                })
            }, methods={
                "update": a.method("Update", "primary", order=1),
                "delete": a.method("Delete", "danger", order=2)
            }, data=data),
            a.links("Navigate", [
                a.link("app", "Go back", icon="chevron-left", record_id=data.get("record_id")),
                a.link("new_app_version", "New application version", "plus", app_id=self.context.get("app_id"))
            ])
        ]

    def access_scopes(self):
        return ["env_admin"]

    @coroutine
    def update(self, version_name, version_env):
        record_id = self.context.get("version_id")

        applications = self.application.applications

        yield applications.update_application_version(
            record_id,
            version_name,
            version_env)

        raise a.Redirect(
            "app_version",
            message="Application version has been updated",
            app_id=self.context.get("app_id"), version_id=record_id)


class ApplicationsController(a.AdminController):
    @coroutine
    def get(self):
        applications = self.application.applications
        apps = yield applications.list_applications()

        result = {
            "apps": apps
        }

        raise a.Return(result)

    def render(self, data):
        return [
            a.breadcrumbs([], "Applications"),
            a.links("Applications", links=[
                a.link("app", app.title, icon="mobile", record_id=app.application_id) for app in data["apps"]
            ]),
            a.links("Navigate", [
                a.link("index", "Go back", icon="chevron-left"),
                a.link("new_app", "New application", "plus")
            ])
        ]

    def access_scopes(self):
        return ["env_admin"]


class EnvironmentController(a.AdminController):
    @coroutine
    def delete(self, **ignored):
        record_id = self.context.get("record_id")

        environment = self.application.environment

        yield environment.delete_environment(record_id)

        raise a.Redirect("envs", message="Environment has been deleted")

    @coroutine
    def get(self, record_id):

        environment = self.application.environment

        try:
            env = yield environment.get_environment(record_id)
        except EnvironmentNotFound:
            raise a.ActionError("Environment was not found.")

        scheme = yield environment.get_scheme()

        result = {
            "env_name": env.name,
            "env_discovery": env.discovery,
            "env_data": env.data,
            "scheme": scheme
        }

        raise a.Return(result)

    def render(self, data):
        return [
            a.breadcrumbs([
                a.link("envs", "Environments")
            ], data.get("env_name")),
            a.form("Environment information", fields={
                "env_name": a.field("Environment name", "text", "primary", "non-empty"),
                "env_discovery": a.field("Discovery service location", "text", "primary", "non-empty"),
                "env_data": a.field("Environment variables", "dorn", "primary", "non-empty",
                                    schema=data["scheme"]),
            }, methods={
                "update": a.method("Update", "primary"),
                "delete": a.method("Delete", "danger")
            }, data=data),
            a.links("Navigate", [
                a.link("envs", "Go back", icon="chevron-left"),
                a.link("new_env", "New environment", "plus")
            ])
        ]

    def access_scopes(self):
        return ["env_envs_admin"]

    @coroutine
    def update(self, env_name, env_discovery, env_data, **ignored):
        record_id = self.context.get("record_id")

        try:
            env_data = ujson.loads(env_data)
        except (KeyError, ValueError):
            raise a.ActionError("Corrupted JSON")

        environment = self.application.environment

        yield environment.update_environment(record_id, env_name, env_discovery, env_data)

        raise a.Redirect(
            "environment",
            message="Environment has been updated",
            record_id=record_id)


class EnvironmentVariablesController(a.AdminController):
    @coroutine
    def get(self):

        environment = self.application.environment

        scheme = yield environment.get_scheme()

        result = {
            "scheme": scheme
        }

        raise a.Return(result)

    def render(self, data):
        return [
            a.breadcrumbs([
                a.link("envs", "Environments")
            ], "Variables scheme"),
            a.form("Scheme", fields={
                "scheme": a.field("Scheme", "json", "primary", "non-empty")
            }, methods={
                "update": a.method("Update", "primary")
            }, data=data),
            a.links("Navigate", [
                a.link("envs", "Go back", icon="chevron-left"),
                a.link("https://spacetelescope.github.io/understanding-json-schema/index.html", "See docs", icon="book")
            ])
        ]

    def access_scopes(self):
        return ["env_envs_admin"]

    @coroutine
    def update(self, scheme):
        try:
            scheme = ujson.loads(scheme)
        except (KeyError, ValueError):
            raise a.ActionError("Corrupted JSON")

        environment = self.application.environment

        yield environment.set_scheme(scheme)

        result = {
            "scheme": scheme
        }

        raise a.Return(result)


class EnvironmentsController(a.AdminController):
    @coroutine
    def get(self):
        environment = self.application.environment
        envs = yield environment.list_environments()

        result = {
            "envs": envs
        }

        raise a.Return(result)

    def render(self, data):
        return [
            a.breadcrumbs([], "Environments"),
            a.links("Environments", links=[
                a.link("environment", env.name, icon="random", record_id=env.environment_id) for env in data["envs"]
                ]),
            a.links("Navigate", [
                a.link("index", "Go back", icon="chevron-left"),
                a.link("vars", "Environment variables", "cog"),
                a.link("new_env", "New environment", "plus")
            ])
        ]

    def access_scopes(self):
        return ["env_envs_admin"]


class NewApplicationController(a.AdminController):
    @coroutine
    def create(self, app_name, app_title):

        applications = self.application.applications

        try:
            record_id = yield applications.create_application(app_name, app_title)
        except ApplicationExists:
            raise a.ActionError("Application with id " + app_name + " already exists.")

        raise a.Redirect(
            "app",
            message="New application has been created",
            record_id=record_id)

    @coroutine
    def get(self):
        raise Return({})

    def render(self, data):
        return [
            a.breadcrumbs([
                a.link("apps", "Applications"),
            ], "New application"),
            a.form("New application", fields={
                "app_name": a.field("Application ID", "text", "primary", "non-empty"),
                "app_title": a.field("Application Title", "text", "primary", "non-empty")
            }, methods={
                "create": a.method("Create", "primary")
            }, data=data),
            a.links("Navigate", [
                a.link("apps", "Go back", icon="chevron-left")
            ])
        ]

    def access_scopes(self):
        return ["env_admin"]


class NewApplicationVersionController(a.AdminController):
    @coroutine
    def create(self, version_name, version_env):

        applications = self.application.applications

        app_id = self.context.get("app_id")

        try:
            app = yield applications.find_application(app_id)
        except ApplicationNotFound:
            raise a.ActionError("App " + str(app_id) + " was not found.")

        application_id = app.application_id

        try:
            record_id = yield applications.create_application_version(
                application_id,
                version_name,
                version_env)

        except VersionExists:
            raise a.ActionError("Version already exists")

        except ReservedName:
            raise a.ActionError("This version name is reserved")

        raise a.Redirect(
            "app_version",
            message="New application version has been created",
            app_id=app_id,
            version_id=record_id)

    @coroutine
    def get(self, app_id):

        environment = self.application.environment
        applications = self.application.applications

        try:
            app = yield applications.find_application(app_id)
        except ApplicationNotFound:
            raise a.ActionError("App " + str(app_id) + " was not found.")

        application_id = app.application_id

        result = {
            "app_name": app.title,
            "application_id": application_id,
            "envs": (yield environment.list_environments())
        }

        raise a.Return(result)

    def render(self, data):
        return [
            a.breadcrumbs([
                a.link("apps", "Applications"),
                a.link("app", data.get("app_name", "Application"), record_id=data.get("application_id")),
            ], "New version"),
            a.form("New application version", fields={
                "version_name": a.field("Version name", "text", "primary", "non-empty"),
                "version_env": a.field("Environment", "select", "primary", "non-empty", values={
                    env.environment_id: env.name for env in data["envs"]
                })
            }, methods={
                "create": a.method("Create", "primary")
            }, data=data),
            a.links("Navigate", [
                a.link("app", "Go back", icon="chevron-left", record_id=data.get("record_id"))
            ])
        ]

    def access_scopes(self):
        return ["env_admin"]


class NewEnvironmentController(a.AdminController):
    @coroutine
    def create(self, env_name, env_discovery):

        environment = self.application.environment

        try:
            record_id = yield environment.create_environment(env_name, env_discovery)
        except VersionExists:
            raise a.ActionError("Such environment already exists.")

        raise a.Redirect(
            "environment",
            message="New environment has been created",
            record_id=record_id)

    def render(self, data):
        return [
            a.breadcrumbs([
                a.link("envs", "Environments")
            ], "New environment"),
            a.form("New environment", fields={
                "env_name": a.field("Environment name", "text", "primary", "non-empty"),
                "env_discovery": a.field("Discovery service location", "text", "primary", "non-empty"),
            }, methods={
                "create": a.method("Create", "primary")
            }, data=data),
            a.links("Navigate", [
                a.link("apps", "Go back", icon="chevron-left")
            ])
        ]

    def access_scopes(self):
        return ["env_envs_admin"]


class RootAdminController(a.AdminController):
    def render(self, data):
        return [
            a.links("Environment service", [
                a.link("apps", "Edit applications", icon="mobile"),
                a.link("envs", "Edit environments", icon="random")
            ])
        ]

    def access_scopes(self):
        return ["env_admin"]
