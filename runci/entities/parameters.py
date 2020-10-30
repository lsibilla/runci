from collections import namedtuple


class Parameters(namedtuple("parameters", "dataconnection targets verbosity")):
    """runci invocation parameters"""
