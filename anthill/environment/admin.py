import ujson

import anthill.common.admin as a

from . model.environment import EnvironmentNotFound, EnvironmentExists
from . model.application import VersionNotFound, VersionExists, ApplicationNotFound, ApplicationExists, ReservedName
from . model.application import ApplicationError


class ApplicationController(a.AdminController):
    async def delete(self, **ignored):
        record_id = self.context.get("record_id")

        applications = self.application.applications

        try:
            app = await applications.get_application(record_id)
        except ApplicationNotFound:
            raise a.ActionError("Application was not found.")

        deleted = await applications.delete_application(record_id)

        if deleted:
            self.audit("times", "Deleted an application",
                       application_title=app.title)

        raise a.Redirect("apps", message="Application has been deleted")

    async def get(self, record_id):

        applications = self.application.applications

        try:
            app = await applications.get_application(record_id)
        except ApplicationNotFound:
            raise a.ActionError("Application was not found.")

        versions = await applications.list_application_versions(record_id)

        result = {
            "application_name": app.name,
            "application_title": app.title,
            "versions": versions,
        }

        return result

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

    async def update(self, application_name, application_title):
        record_id = self.context.get("record_id")

        applications = self.application.applications

        try:
            app = await applications.get_application(record_id)
        except ApplicationNotFound:
            raise a.ActionError("Application was not found.")

        try:
            await applications.update_application(
                record_id,
                application_name,
                application_title)

        except ApplicationExists:
            raise a.ActionError("Such application already exists")

        self.audit("mobile", "Updated an application",
                   only_if=True,
                   application_name=(app.name, application_name),
                   application_title=(app.title, application_title))

        raise a.Redirect(
            "app",
            message="Application has been updated",
            record_id=record_id)


class ApplicationVersionController(a.AdminController):
    async def delete(self, **ignored):

        applications = self.application.applications

        version_id = self.context.get("version_id")
        app_name = self.context.get("app_id")

        try:
            app = await applications.find_application(app_name)
        except ApplicationNotFound:
            raise a.ActionError("App was not found.")

        app_id = app.application_id

        try:
            version = await applications.get_application_version(app_id, version_id)
        except VersionNotFound:
            raise a.ActionError("No such version")
        except ApplicationError as e:
            raise a.ActionError(e.message)

        deleted = await applications.delete_application_version(version_id)

        if deleted:
            self.audit("times", "Deleted application version",
                       version=version.name,
                       application_name=app.name,
                       application_title=app.title)

        raise a.Redirect(
            "app",
            message="Application version has been deleted",
            record_id=app_id)

    async def get(self, app_id, version_id):

        environment = self.application.environment
        applications = self.application.applications

        try:
            app = await applications.find_application(app_id)
        except ApplicationNotFound:
            raise a.ActionError("App was not found.")

        application_id = app.application_id

        try:
            version = await applications.get_application_version(application_id, version_id)
        except ApplicationNotFound:
            raise a.ActionError("Application was not found.")
        except VersionNotFound:
            raise a.ActionError("Version was not found.")

        result = {
            "app_title": app.title,
            "application_id": application_id,
            "envs": (await environment.list_environments()),
            "version_name": version.name,
            "version_env": version.environment
        }

        return result

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

    async def update(self, version_name, version_env):
        record_id = self.context.get("version_id")
        app_id = self.context.get("app_id")

        applications = self.application.applications

        try:
            app = await applications.find_application(app_id)
        except ApplicationNotFound:
            raise a.ActionError("App was not found.")

        application_id = app.application_id

        try:
            version = await applications.get_application_version(application_id, record_id)
        except ApplicationNotFound:
            raise a.ActionError("Application was not found.")
        except VersionNotFound:
            raise a.ActionError("Version was not found.")

        environment = self.application.environment

        try:
            new_env = await environment.get_environment(version_env)
            if str(version.environment) == str(new_env.environment_id):
                old_env = new_env
            else:
                old_env = await environment.get_environment(version.environment)
        except EnvironmentNotFound:
            raise a.ActionError("No such environment")

        updated = await applications.update_application_version(
            application_id,
            record_id,
            version_name,
            version_env)

        if updated:
            self.audit("tags", "Updated application version", only_if=True,
                       application_name=app.name,
                       version_name=(version.name, version_name),
                       version_environment=(old_env.name, new_env.name))

        raise a.Redirect(
            "app_version",
            message="Application version has been updated",
            app_id=self.context.get("app_id"), version_id=record_id)


class ApplicationsController(a.AdminController):
    async def get(self):
        applications = self.application.applications
        apps = await applications.list_applications()

        result = {
            "apps": apps
        }

        return result

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
    async def delete(self, **ignored):
        record_id = self.context.get("record_id")

        environment = self.application.environment

        try:
            env = await environment.get_environment(record_id)
        except EnvironmentNotFound:
            raise a.ActionError("No such environment")

        deleted = await environment.delete_environment(record_id)

        if deleted:
            self.audit("times", "Deleted an environment",
                       environment_name=env.name)

        raise a.Redirect("envs", message="Environment has been deleted")

    async def get(self, record_id):

        environment = self.application.environment

        try:
            env = await environment.get_environment(record_id)
        except EnvironmentNotFound:
            raise a.ActionError("Environment was not found.")

        scheme = await environment.get_scheme()

        return {
            "env_name": env.name,
            "env_discovery": env.discovery,
            "env_data": env.data,
            "scheme": scheme
        }

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

    async def update(self, env_name, env_discovery, env_data, **ignored):
        record_id = self.context.get("record_id")

        try:
            env_data = ujson.loads(env_data)
        except (KeyError, ValueError):
            raise a.ActionError("Corrupted JSON")

        environment = self.application.environment

        try:
            env = await environment.get_environment(record_id)
        except EnvironmentNotFound:
            raise a.ActionError("No such environment")

        updated = await environment.update_environment(record_id, env_name, env_discovery, env_data)

        if updated:
            self.audit("random", "Updated an environment",
                       environment_name=(env.name, env_name),
                       environment_discovery_location=(env.discovery, env_discovery),
                       environment_variables=(env.data, env_data))

        raise a.Redirect(
            "environment",
            message="Environment has been updated",
            record_id=record_id)


class EnvironmentVariablesController(a.AdminController):
    async def get(self):

        environment = self.application.environment

        scheme = await environment.get_scheme()

        result = {
            "scheme": scheme
        }

        return result

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

    async def update(self, scheme):
        try:
            scheme = ujson.loads(scheme)
        except (KeyError, ValueError):
            raise a.ActionError("Corrupted JSON")

        environment = self.application.environment

        old_scheme = await environment.get_scheme()

        updated = await environment.set_scheme(scheme)

        if updated:
            self.audit("cogs", "Updated environment variables",
                       scheme=(old_scheme, scheme))

        raise a.Redirect("vars", message="Variables scheme has been updated")


class EnvironmentsController(a.AdminController):
    async def get(self):
        environment = self.application.environment

        return {
            "envs": await environment.list_environments()
        }

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
    async def create(self, app_name, app_title):

        applications = self.application.applications

        try:
            record_id = await applications.create_application(app_name, app_title)
        except ApplicationExists:
            raise a.ActionError("Application with id " + app_name + " already exists.")

        self.audit("plus", "Created an application",
                   application_name=app_name,
                   application_title=app_title)

        raise a.Redirect(
            "app",
            message="New application has been created",
            record_id=record_id)

    async def get(self):
        return {}

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
    async def create(self, version_name, version_env):

        applications = self.application.applications

        app_id = self.context.get("app_id")

        try:
            app = await applications.find_application(app_id)
        except ApplicationNotFound:
            raise a.ActionError("App " + str(app_id) + " was not found.")

        environment = self.application.environment

        try:
            env = await environment.get_environment(version_env)
        except EnvironmentNotFound:
            raise a.ActionError("No such environment")

        application_id = app.application_id

        try:
            record_id = await applications.create_application_version(
                application_id,
                version_name,
                version_env)
        except VersionExists:
            raise a.ActionError("Version already exists")
        except ReservedName:
            raise a.ActionError("This version name is reserved")
        else:
            self.audit("plus", "Created new application version",
                       version=version_name,
                       environment=env.name,
                       application_name=app.name,
                       application_title=app.title)

        raise a.Redirect(
            "app_version",
            message="New application version has been created",
            app_id=app_id,
            version_id=record_id)

    async def get(self, app_id):

        environment = self.application.environment
        applications = self.application.applications

        try:
            app = await applications.find_application(app_id)
        except ApplicationNotFound:
            raise a.ActionError("App " + str(app_id) + " was not found.")

        application_id = app.application_id

        result = {
            "app_name": app.title,
            "application_id": application_id,
            "envs": (await environment.list_environments())
        }

        return result

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
    async def create(self, env_name, env_discovery):

        environment = self.application.environment

        try:
            record_id = await environment.create_environment(env_name, env_discovery)
        except VersionExists:
            raise a.ActionError("Such environment already exists.")

        self.audit("plus", "Created new environment",
                   environment_name=env_name,
                   discovery_service_location=env_discovery)

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
