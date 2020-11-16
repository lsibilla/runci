from collections import namedtuple


class Context(namedtuple('context', 'project parameters runners listeners processors jobs')):
    """Represent the runci context entity."""

    def __new__(cls, project, parameters, runners, listeners, processors):
        jobs = dict()
        return super(Context, cls).__new__(cls, project, parameters, runners, listeners, processors, jobs)
