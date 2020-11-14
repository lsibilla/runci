import enum


class RunnerStatus(enum.Enum):
    "runci step status enum type"
    CREATED = 'created'
    STARTED = 'started'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELED = 'canceled'


def register_runner(name, cls):
    selector[name] = cls


def import_runners():
    import pkgutil
    import importlib
    for finder, name, ispkg in pkgutil.iter_modules(__path__, "runci.engine.runner."):
        importlib.import_module(name)


selector = {}
