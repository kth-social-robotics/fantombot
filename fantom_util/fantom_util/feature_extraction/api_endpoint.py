import json
import logging
import time
from os import environ

import falcon
import numpy as np
import redis
import msgpack
import msgpack_numpy as m

m.patch()

from fantom_util import constants
from fantom_util.constants import REDIS_HOST, REDIS_PORT
from fantom_util.feature_extraction.feature_extractor import FeatureExtractor
from fantom_util.misc import gen_feature_dict
from fantom_util.fantom_logging import create_sns_logger


log_fantom_version = environ.get("FANTOM_VERSION", "UNKNOWN_FANTOM_VERSION")
log_stage = environ.get("STAGE", "UNKNOWN_STAGE")
log_docker = environ.get("DOCKER_NAME", "UNKNOWN_DOCKER_NAME")

LOGGING_FORMAT = f"[%(asctime)s] [STAGE: {log_stage}, FANTOM_UTIL: {log_fantom_version}, PID: %(process)d, NAME: %(name)s, DOCKER: {log_docker} LINE:%(lineno)s] [%(levelname)s] %(message)s"

logging.basicConfig(level=logging.DEBUG)
formatter = logging.Formatter(LOGGING_FORMAT)

logger = logging.getLogger(__name__)
gunicorn_error_logger = logging.getLogger("gunicorn.error")
logger.handlers.extend(gunicorn_error_logger.handlers)
logger.setLevel(logging.DEBUG)

logger.addHandler(create_sns_logger())

for handler in logger.handlers:
    handler.setFormatter(formatter)
np.set_printoptions(threshold=5)


class Endpoint(object):
    redis_host = environ.get("REDIS_HOST", "localhost")
    redis_port = environ.get("REDIS_PORT", 6379)

    def __init__(self, feature):
        self.feature = feature
        self.extractor = FeatureExtractor(
            gen_feature_dict(feature, cobot=True), start_extractor_servers=True
        )
        self.required_context = self.feature["cobot-input"]
        try:
            self.redis_pool = redis.ConnectionPool(
                host=REDIS_HOST, port=REDIS_PORT, db=0
            )
            r = redis.StrictRedis(connection_pool=self.redis_pool)
            r.ping()
            logger.info("using redis")
        except redis.exceptions.ConnectionError:
            logger.info("not using redis")
            self.redis_pool = None

    def on_post(self, req, resp):
        """Handles GET requests"""
        t0 = time.time()

        data = json.loads(req.stream.read())

        validation = self.__validate_input(data)
        if validation:
            resp.body = json.dumps(validation)
            raise falcon.HTTPBadRequest()

        data = self.process_input(data)

        logger.info(f"data sent to feature extractor: {data}")

        values, redis_keys = self.extractor(data, return_redis_key=True)

        ret = {"response": {"cache_key": redis_keys[self.feature["name"]]}}

        if self.feature["name"] not in constants.REDIS_ONLY:
            ret["response"]["result"] = values[self.feature["name"]]
        logger.info(ret)

        ret["performance"] = (time.time() - t0,)
        ret["error"] = False

        logger.info("result: %s", ret)

        resp.body = json.dumps(ret)

    def __validate_input(self, args):
        message = ""
        for ctx in self.required_context:
            if not args.get(ctx["cobot-name"]):
                message = "Context missing: name: {}, cobot: {}, history_turns: {}".format(
                    ctx["name"], ctx["cobot-name"], ctx.get("history_turns")
                )
        if message:
            return {"message": message, "error": True}
        return None

    def process_input(self, data):
        """Grab latest value of each required_context"""
        logger.info("input received: %s", data)
        out = {}
        for ctx in self.required_context:
            logger.info(ctx)
            value = data[ctx["cobot-name"]][ctx.get("history_turns", 0)]

            if value and isinstance(value, dict):
                new_value = value.get("result")
                if new_value:
                    out[ctx["name"]] = new_value
                elif self.redis_pool and value.get("cache_key"):
                    r = redis.StrictRedis(
                        connection_pool=self.redis_pool, socket_timeout=1
                    )
                    out[ctx["name"]] = msgpack.unpackb(
                        r.get(value.get("cache_key")), raw=False
                    )
                else:
                    raise Exception(
                        f"No redis connection or no cache_key available available and need to get from redis. {value}"
                    )

            else:
                out[ctx["name"]] = value

        return out


class HealthCheck(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp):
        resp.status = falcon.HTTP_200
