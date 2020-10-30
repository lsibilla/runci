from yaml import safe_load
from runci.entities import config
from runci.entities.parameters import Parameters

"""YAML data layer for runci"""


def __create_service(item):
    return config.Service(item[0], item[1])


def __create_target(item):
    name = item[0]
    spec = item[1]

    if spec is None:
        return config.Target(name, [], [])

    if not isinstance(spec, dict):
        raise Exception("spec argument should be a dictionnary")

    dependencies = spec.get('dependencies', [])
    if isinstance(dependencies, str):
        dependencies = dependencies.split(' ')
    steps = config.create_entities(__create_step, spec.get('steps', []))
    return config.Target(name, dependencies, steps)


def __create_step(item):
    name = item.get('name', 'Unamed step')
    other_keys = [k for k in item.keys() if k != 'name']
    if len(other_keys) != 1:
        raise Exception("Can't find key for step '%s'." % name)
    type = other_keys[0]
    spec = item[type]
    if spec is None:
        spec = dict()
    return config.Step(name, type, spec)


def load_config(parameters):
    if isinstance(parameters, Parameters):
        file = parameters.dataconnection
    else:
        file = parameters

    if isinstance(file, str):
        datastream = open(file, 'r')
    else:
        datastream = file

    data = safe_load(datastream)
    datastream.close()

    services = config.create_entities(__create_service, data['services'].items())

    if "targets" in data:
        targets = data['targets']
    elif "x-targets" in data:     # Allow for docker-compose friendly x-targets rather than targets collection.
        targets = data['x-targets']

    targets = config.create_entities(__create_target, targets.items())

    return config.Project(services, targets, parameters)
