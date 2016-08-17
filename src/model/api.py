
from tornado.gen import coroutine, Return
from common.options import options

from distutils.version import LooseVersion


class APIModel(object):
    def __init__(self):
        self.versions = options.api_versions

    @coroutine
    def get_versions(self, min_api=None):

        versions = self.versions

        versions = sorted(versions, cmp=lambda a, b: 1 if LooseVersion(a) > LooseVersion(b) else -1)

        if min_api:
            def check_version(version, min_api):
                return LooseVersion(version) >= LooseVersion(min_api)

            raise Return([v for v in versions if check_version(v, min_api)])

        raise Return(versions)
