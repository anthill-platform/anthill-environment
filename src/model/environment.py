from tornado.gen import coroutine, Return

import ujson

from common.database import DuplicateError, DatabaseError
from common.model import Model


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
        self.api = data.get("api_version")
        self.data = data.get("environment_data")


class EnvironmentModel(Model):
    def __init__(self, db):
        self.db = db

    def get_setup_db(self):
        return self.db

    @coroutine
    def setup_table_environments(self):
        yield self.create_environment("dev", "http://discovery-dev.anthill.local")

    @coroutine
    def setup_table_scheme(self):
        yield self.set_scheme({"type": "object", "properties": {"test-option": {"type": "string"}}})

    def get_setup_tables(self):
        return ["environments", "scheme"]

    @coroutine
    def create_environment(self, environment_name, environment_discovery):

        try:
            record_id = yield self.db.insert(
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

        raise Return(record_id)

    @coroutine
    def delete_environment(self, environment_id):

        try:
            with (yield self.db.acquire()) as db:
                yield db.execute(
                    """
                        DELETE FROM `application_versions`
                        WHERE `version_environment`=%s;
                    """, environment_id)

                yield db.execute(
                    """
                        DELETE FROM `environments`
                        WHERE `environment_id`=%s;
                    """, environment_id)

        except DatabaseError as e:
            raise EnvironmentDataError("Failed to delete environment: " + e.args[1])

    @coroutine
    def find_environment(self, environment_name):
        try:
            env = yield self.db.get(
                """
                    SELECT `environment_id`
                    FROM `environments`
                    WHERE environment_name=%s;
                """, environment_name, cache_time=60)
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to find environment: " + e.args[1])

        if env is None:
            raise EnvironmentNotFound()

        raise Return(EnvironmentAdapter(env))

    @coroutine
    def get_environment(self, environment_id):
        try:
            env = yield self.db.get(
                """
                    SELECT *
                    FROM `environments`
                    WHERE `environment_id`=%s;
                """, environment_id, cache_time=60)
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to get environment: " + e.args[1])

        if env is None:
            raise EnvironmentNotFound()

        raise Return(EnvironmentAdapter(env))

    @coroutine
    def list_environments(self):
        try:
            environments = yield self.db.query(
                """
                    SELECT *
                    FROM `environments`;
                """, cache_time=60
            )
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to list environments: " + e.args[1])

        raise Return(map(EnvironmentAdapter, environments))

    @coroutine
    def get_scheme(self, exception=False):
        try:
            env = yield self.db.get(
                """
                    SELECT `data` FROM `scheme`;
                """)
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to get scheme: " + e.args[1])

        if env is None:
            if exception:
                raise SchemeNotExists()

            raise Return({})

        raise Return(env["data"])

    @coroutine
    def get_version_environment(self, app_name, app_version):

        try:
            version = yield self.db.get(
                """
                    SELECT `environment_discovery`, `environment_data`, `api_version`
                    FROM `applications`, `application_versions`, `environments`
                    WHERE `application_versions`.`application_id`=`applications`.`application_id`
                        AND `applications`.`application_id`=%s AND `version_name`=%s
                        AND `environment_id`=`version_environment`;
                """, app_name, app_version)
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to get version environment: " + e.args[1])

        if version is None:
            raise EnvironmentNotFound()

        raise Return(EnvironmentPlusVersionAdapter(version))

    @coroutine
    def set_scheme(self, data):

        if not isinstance(data, dict):
            raise AttributeError("data is not a dict")

        try:
            yield self.get_scheme(exception=True)
        except SchemeNotExists:
            try:
                yield self.db.insert(
                    """
                        INSERT INTO `scheme`
                        (`data`)
                        VALUES (%s);
                    """, ujson.dumps(data)
                )
            except DatabaseError as e:
                raise EnvironmentDataError("Failed to insert scheme: " + e.args[1])
        else:
            try:
                yield self.db.execute(
                    """
                        UPDATE `scheme`
                        SET `data`=%s;
                    """,
                    ujson.dumps(data)
                )
            except DatabaseError as e:
                raise EnvironmentDataError("Failed to update scheme: " + e.args[1])

    @coroutine
    def update_environment(self, record_id, env_name, env_discovery, env_data):

        if not isinstance(env_data, dict):
            raise AttributeError("env_data is not a dict")

        try:
            yield self.db.execute("""
                UPDATE `environments`
                SET `environment_name`=%s, `environment_discovery`=%s, `environment_data`=%s
                WHERE `environment_id`=%s;
            """, env_name, env_discovery, ujson.dumps(env_data), record_id)
        except DatabaseError as e:
            raise EnvironmentDataError("Failed to update environment: " + e.args[1])


class EnvironmentNotFound(Exception):
    pass


class EnvironmentExists(Exception):
    pass


class SchemeNotExists(Exception):
    pass

