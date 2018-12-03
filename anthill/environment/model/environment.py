
from anthill.common.database import DuplicateError, DatabaseError
from anthill.common.model import Model
from anthill.common.validate import validate

import ujson


class EnvironmentDataError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class EnvironmentAdapter(object):
    def __init__(self, data):
        self.environment_id = data.get("environment_id")
        self.name = data.get("environment_name")
        self.discovery = data.get("environment_discovery")
        self.data = data.get("environment_data")


class EnvironmentPlusVersionAdapter(object):
    def __init__(self, data):
        self.discovery = data.get("environment_discovery")
        self.data = data.get("environment_data")


class EnvironmentModel(Model):
    def __init__(self, db):
        self.db = db

    def get_setup_db(self):
        return self.db

    async def setup_table_environments(self):
        await self.create_environment("dev", "http://localhost:9502")

    async def setup_table_scheme(self):
        await self.set_scheme({"type": "object", "properties": {"test-option": {"type": "string"}}})

    def get_setup_tables(self):
        return ["environments", "scheme"]

    async def create_environment(self, environment_name, environment_discovery):

        try:
            record_id = await self.db.insert(
                """
                    INSERT INTO `environments`
                    (`environment_name`, `environment_discovery`, `environment_data`)
                    VALUES (%s, %s, %s);
                """,
                environment_name, environment_discovery, "{}"
            )
        except DuplicateError:
            raise EnvironmentExists()
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to create environment: " + e.args[1])

        return record_id

    async def delete_environment(self, environment_id):

        try:
            deleted = await self.db.execute(
                """
                    DELETE FROM `environments`
                    WHERE `environment_id`=%s;
                """, environment_id)
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to delete environment: " + e.args[1])
        else:
            return bool(deleted)

    async def find_environment(self, environment_name):
        try:
            env = await self.db.get(
                """
                    SELECT `environment_id`
                    FROM `environments`
                    WHERE environment_name=%s;
                """, environment_name, cache_time=60)
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to find environment: " + e.args[1])

        if env is None:
            raise EnvironmentNotFound()

        return EnvironmentAdapter(env)

    async def get_environment(self, environment_id):
        try:
            env = await self.db.get(
                """
                    SELECT *
                    FROM `environments`
                    WHERE `environment_id`=%s;
                """, environment_id, cache_time=60)
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to get environment: " + e.args[1])

        if env is None:
            raise EnvironmentNotFound()

        return EnvironmentAdapter(env)

    async def list_environments(self):
        try:
            environments = await self.db.query(
                """
                    SELECT *
                    FROM `environments`;
                """, cache_time=60
            )
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to list environments: " + e.args[1])

        return list(map(EnvironmentAdapter, environments))

    async def get_scheme(self, exception=False):
        try:
            env = await self.db.get(
                """
                    SELECT `data` FROM `scheme`;
                """)
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to get scheme: " + e.args[1])

        if env is None:
            if exception:
                raise SchemeNotExists()

            return {}

        return env["data"]

    async def get_version_environment(self, app_name, app_version):

        try:
            version = await self.db.get(
                """
                    SELECT `environment_discovery`, `environment_data`
                    FROM `applications`, `application_versions`, `environments`
                    WHERE `application_versions`.`application_id`=`applications`.`application_id`
                        AND `applications`.`application_name`=%s AND `application_versions`.`version_name`=%s
                        AND `environment_id`=`application_versions`.`version_environment`;
                """, app_name, app_version)
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to get version environment: " + e.args[1])

        if version is None:
            raise EnvironmentNotFound()

        return EnvironmentPlusVersionAdapter(version)

    @validate(data="json_dict")
    async def set_scheme(self, data):

        if not isinstance(data, dict):
            raise AttributeError("data is not a dict")

        try:
            updated = await self.db.execute(
                """
                    INSERT INTO `scheme`
                    (`data`)
                    VALUES (%s)
                    ON DUPLICATE KEY 
                    UPDATE `data`=VALUES(`data`);
                """, ujson.dumps(data)
            )
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to insert scheme: " + e.args[1])
        else:
            return bool(updated)

    async def update_environment(self, record_id, env_name, env_discovery, env_data):
        if not isinstance(env_data, dict):
            raise AttributeError("env_data is not a dict")

        try:
            updated = await self.db.execute("""
                UPDATE `environments`
                SET `environment_name`=%s, `environment_discovery`=%s, `environment_data`=%s
                WHERE `environment_id`=%s;
            """, env_name, env_discovery, ujson.dumps(env_data), record_id)
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to update environment: " + e.args[1])

        return bool(updated)


class EnvironmentNotFound(Exception):
    pass


class EnvironmentExists(Exception):
    pass


class SchemeNotExists(Exception):
    pass
