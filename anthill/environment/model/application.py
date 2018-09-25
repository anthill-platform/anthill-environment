
from anthill.common.database import DuplicateError, DatabaseError
from anthill.common.model import Model


DEFAULT = "def"


class ApplicationError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ApplicationExists(Exception):
    pass


class ApplicationNotFound(Exception):
    pass


class ApplicationAdapter(object):
    def __init__(self, data):
        self.application_id = data.get("application_id")
        self.name = data.get("application_name")
        self.title = data.get("application_title")


class ApplicationVersionAdapter(object):
    def __init__(self, data):
        self.version_id = data.get("version_id")
        self.application_id = data.get("application_id")
        self.name = data.get("version_name")
        self.environment = data.get("version_environment")


class ApplicationsModel(Model):
    def __init__(self, db, environment):
        self.db = db
        self.environment = environment

    def get_setup_db(self):
        return self.db

    async def setup_table_applications(self):
        await self.create_application("test", "Test application")

    async def setup_table_application_versions(self):

        dev_env = await self.environment.find_environment("dev")
        test_app = await self.find_application("test")

        await self.create_application_version(test_app.application_id, "1.0", dev_env.environment_id)

    def get_setup_tables(self):
        return ["applications", "application_versions"]

    async def create_application(self, application_name, application_title):

        try:
            await self.find_application(application_name)
        except ApplicationNotFound:
            pass
        else:
            raise ApplicationExists()

        try:
            record_id = await self.db.insert(
                """
                    INSERT INTO `applications`
                    (`application_name`, `application_title`)
                    VALUES (%s, %s);
                """, application_name, application_title)
        except DuplicateError:
            raise ApplicationExists()
        except DatabaseError as e:
            raise ApplicationError("Failed to create application: " + e.args[1])

        return record_id

    async def create_application_version(self, application_id, version_name, version_environment):

        if version_name == DEFAULT:
            raise ApplicationError("Version '{0}' is reserved".format(DEFAULT))

        try:
            await self.find_application_version(application_id, version_name)
        except VersionNotFound:
            pass
        else:
            raise ReservedName()

        try:
            version_id = await self.db.insert(
                """
                    INSERT INTO `application_versions`
                    (`application_id`, `version_name`, version_environment)
                    VALUES (%s, %s, %s);
                """,
                application_id, version_name, version_environment)

        except DatabaseError as e:
            raise ApplicationError("Failed to create application version: " + e.args[1])

        return version_id

    async def delete_application(self, application_id):

        try:
            deleted = await self.db.execute(
                """
                    DELETE FROM `applications`
                    WHERE `application_id`=%s;
                """, application_id)

        except DatabaseError as e:
            raise ApplicationError("Failed to delete application: " + e.args[1])
        else:
            return bool(deleted)

    async def delete_application_version(self, version_id):
        try:
            deleted = await self.db.execute(
                """
                    DELETE FROM `application_versions`
                    WHERE `version_id`=%s;
                """, version_id)
        except DatabaseError as e:
            raise ApplicationError("Failed to delete application version: " + e.args[1])
        else:
            return bool(deleted)

    async def find_application(self, application_name):

        try:
            app = await self.db.get(
                """
                    SELECT *
                    FROM `applications`
                    WHERE `application_name`=%s;
                """, application_name)
        except DatabaseError as e:
            raise ApplicationError("Failed to find application: " + e.args[1])

        if app is None:
            raise ApplicationNotFound(application_name)

        return ApplicationAdapter(app)

    async def find_application_version(self, application_id, version_name):

        try:
            version = await self.db.get(
                """
                    SELECT *
                    FROM `application_versions`
                    WHERE `application_id`=%s AND `version_name`=%s;
                """, application_id, version_name
            )
        except DatabaseError as e:
            raise ApplicationError("Failed to find application version: " + e.args[1])

        if version is None:
            raise VersionNotFound()

        return ApplicationVersionAdapter(version)

    async def get_application(self, application_id):
        try:
            application = await self.db.get(
                """
                    SELECT *
                    FROM `applications`
                    WHERE `application_id`=%s;
                """, application_id)

        except DatabaseError as e:
            raise ApplicationError("Failed to get application: " + e.args[1])

        if application is None:
            raise ApplicationNotFound()

        return ApplicationAdapter(application)

    async def get_application_version(self, application_id, version_id):

        try:
            version = await self.db.get(
                """
                    SELECT *
                    FROM `application_versions`
                    WHERE `application_id`=%s AND `version_id`=%s;
                """, application_id, version_id)

        except DatabaseError as e:
            raise ApplicationError("Failed to get application version: " + e.args[1])

        if version is None:
            raise VersionNotFound()

        return ApplicationVersionAdapter(version)

    async def list_application_versions(self, application_id):

        try:
            versions = await self.db.query(
                """
                    SELECT *
                    FROM `application_versions`
                    WHERE `application_id`=%s
                    ORDER BY `version_name` ASC;
                """, application_id)
        except DatabaseError as e:
            raise ApplicationError("Failed to list application versions: " + e.args[1])

        return map(ApplicationVersionAdapter, versions)

    async def list_applications(self):

        try:
            apps = await self.db.query(
                """
                    SELECT `application_id`, `application_name`, `application_title`
                    FROM `applications`
                    ORDER BY `application_name` ASC;
                """)

        except DatabaseError as e:
            raise ApplicationError("Failed to list applications: " + e.args[1])

        return map(ApplicationAdapter, apps)

    async def update_application(self, application_id, application_name, application_title):
        try:
            updated = await self.db.execute(
                """
                    UPDATE `applications`
                    SET `application_name`=%s, `application_title`=%s
                    WHERE `application_id`=%s;
                """, application_name, application_title, application_id)
        except DuplicateError:
            raise ApplicationExists()
        except DatabaseError as e:
            raise ApplicationError("Failed to update application: " + e.args[1])

        return bool(updated)

    async def update_application_version(self, application_id, version_id, version_name, version_env):
        try:
            updated = await self.db.execute(
                """
                    UPDATE `application_versions`
                    SET `version_name`=%s, version_environment=%s
                    WHERE `version_id`=%s AND `application_id`=%s;
                """,
                version_name, version_env, version_id, application_id
            )
        except DatabaseError as e:
            raise ApplicationError("Failed to update application version: " + e.args[1])

        return bool(updated)


class VersionExists(Exception):
    pass


class ReservedName(Exception):
    pass


class VersionNotFound(Exception):
    pass
