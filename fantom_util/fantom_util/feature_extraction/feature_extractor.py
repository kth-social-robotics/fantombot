import hashlib
import inspect
from functools import lru_cache
from collections import Hashable, defaultdict

import redis
import msgpack
import msgpack_numpy as m
from fantom_util.feature_extraction.fasttext_extractor import (
    word_embeddings,
    start_calculate_fasttext_process,
)

m.patch()
from fantom_util.constants import REDIS_HOST, REDIS_PORT
from fantom_util.feature_extraction.nlp import activate_model
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor(object):
    """Load a list of extractors and use it to provide features for a sentence
    """

    def __init__(self, features, start_extractor_servers=True):
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
        self.row = {}
        self.features = features
        self.extractors = {}
        self.steps = {}
        self.step_hash = {}
        self.required_inputs = defaultdict(set)
        self.extractors = set()

        for feature, steps in features.items():
            self.get_required_inputs(feature, steps)

        if start_extractor_servers:
            for extractor in self.extractors:
                if extractor == word_embeddings:
                    start_calculate_fasttext_process()

        for feature, steps in features.items():
            self.steps[feature] = self.step_runner(steps)
            self.step_hash[feature] = str(FeatureExtractor.stringify_steps(steps))

    def __call__(self, row, return_redis_key=False):
        self.row = row
        """Take a dictionary row and adds/updates key and value
        for each feature specified
        """
        result = {}
        for feature in ("text", "parent_id", "id"):
            if feature in self.row.keys():
                result[feature] = self.row[feature]

        redis_keys = {}

        if self.redis_pool:
            r = redis.StrictRedis(connection_pool=self.redis_pool, socket_timeout=1)

            # sort the dict based on the key and extract the values

            for feature_name, steps in self.steps.items():
                dict_values = [
                    self.row[key] for key in sorted(self.required_inputs[feature_name])
                ]
                redis_keys[feature_name] = hashlib.md5(
                    f"{self.step_hash[feature_name]}--+--{dict_values}".encode("utf-8")
                ).hexdigest()

                old_value = r.get(redis_keys[feature_name])
                logger.debug(redis_keys[feature_name])
                if old_value:
                    result[feature_name] = msgpack.unpackb(old_value, raw=False)
                    logger.debug(f"old redis value")
                else:
                    result[feature_name] = self.runner(steps)
                    r.set(
                        redis_keys[feature_name],
                        msgpack.packb(result[feature_name], use_bin_type=True),
                    )
                    logger.debug(f"extracted new value and saved to redis")
        else:
            for feature_name, steps in self.steps.items():
                result[feature_name] = self.runner(steps)
                logger.debug(f"not using redis, extracted value")

        if return_redis_key:
            if not redis_keys:
                raise Exception("unable to connect to redis")
            return result, redis_keys
        else:
            return result

    def step_runner(self, steps):
        if type(steps) not in [list, tuple]:
            if callable(steps):
                activate_model(steps)
                return steps
            elif isinstance(steps, str):
                return lambda *x: self.row[steps]
        else:
            if isinstance(steps, tuple):
                return tuple(self.step_runner(step) for step in steps)
            elif isinstance(steps, list):
                return list(self.step_runner(step) for step in steps)

    def runner(self, steps, x=None):
        if not steps:
            return FeatureExtractor.get_val(x)
        if isinstance(steps, tuple):
            return MultiValue(
                [FeatureExtractor.get_val(self.runner(step, x)) for step in steps]
            )
        elif isinstance(steps, list):
            return FeatureExtractor.get_val(
                self.runner(steps[1:], self.runner(steps[0], x))
            )
        else:
            return FeatureExtractor.call_extractor(steps, x)

    @staticmethod
    def get_val(x):
        return x.val if isinstance(x, MultiValue) else x

    @staticmethod
    def call_extractor(func, val):
        @lru_cache()
        def cached_run(step, x):
            return run(step, x)

        def run(step, x):
            if isinstance(x, MultiValue):
                return step(*x.val)
            else:
                return step(x)

        return cached_run(func, val) if isinstance(val, Hashable) else run(func, val)

    @staticmethod
    def stringify_steps(l):
        if isinstance(l, list):
            return [FeatureExtractor.stringify_steps(x) for x in l]
        elif isinstance(l, tuple):
            return tuple([FeatureExtractor.stringify_steps(x) for x in l])
        elif callable(l):
            try:
                return inspect.getsource(l)
            except TypeError:
                return l.__name__
        else:
            return str(l)

    def get_required_inputs(self, feature, l):
        if isinstance(l, list):
            return [self.get_required_inputs(feature, x) for x in l]
        elif isinstance(l, tuple):
            return tuple([self.get_required_inputs(feature, x) for x in l])
        elif isinstance(l, str):
            self.required_inputs[feature].add(l)
        elif callable(l):
            self.extractors.add(l)


class MultiValue(object):
    def __init__(self, val):
        self.val = val

