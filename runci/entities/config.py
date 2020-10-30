from collections import namedtuple


class Project(namedtuple('config', 'services targets parameters')):
    """Represent the runci configuration entity."""


class Service(namedtuple('service', 'name spec')):
    """Represent the docker-compose service entity."""


class Target(namedtuple('target', 'name dependencies steps')):
    """Represent the runci target entity."""


class Step(namedtuple('config', 'name type spec')):
    """Represent the runci step entity."""


def create_entities(factory, iterator):
    return list(map(factory, iterator))
