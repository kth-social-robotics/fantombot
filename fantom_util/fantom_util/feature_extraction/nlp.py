import logging
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)
models = {}
registered_models = defaultdict(set)


def get_func_name(func):
    return func.__module__ + "." + func.__name__


def activate_model(func):
    global models, registered_models
    for model in registered_models[get_func_name(func)]:
        if not models.get(model):
            logger.info("LOADING MODEL %s", model)
            models[model] = model()


def preload_model(load_model_func):
    global models, registered_models
    models[load_model_func] = None

    def outer_wrapper(func):
        registered_models[get_func_name(func)].add(load_model_func)

        @wraps(func)
        def inner_wrapper(*arg, **kargs):
            if not models.get(load_model_func):
                models[load_model_func] = load_model_func()
            return func(models[load_model_func], *arg, **kargs)

        return inner_wrapper

    return outer_wrapper
