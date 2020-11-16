import asyncio
from collections import namedtuple
import importlib
import inspect
import sys

from runci.entities.config import Target
from runci.entities.context import Context
from runci.engine.job import Job, JobStatus
from runci.engine.runner.base import RunnerBase
from runci.engine.listener.base import ListenerBase


class RunCIEngineException(Exception):
    pass


class UnknownTargetException(RunCIEngineException):
    pass


class AmbiguousTargetException(RunCIEngineException):
    pass


class DependencyNode(namedtuple("dependency_node", "job dependencies")):
    "runci depencency tree node"
    async def _run_dependencies(self, noparallel):
        if noparallel:
            jobs = [job
                    for node in self.dependencies
                    for job in await node.start(noparallel)]
        else:
            tasks = [node.start(noparallel) for node in self.dependencies]
            jobs = [job
                    for task in tasks
                    for job in await task]

        return jobs

    async def _run(self, noparallel=False):
        jobs = list(await self._run_dependencies(noparallel))
        if any([job for job in jobs if job.status in [JobStatus.FAILED, JobStatus.CANCELED]]):
            self.job.fail()
        else:
            jobs.append(self.job)
            await self.job.start()

        return jobs

    def start(self, noparallel=False):
        return asyncio.create_task(self._run(noparallel))

    def run(self, noparallel=False):
        return asyncio.run(self._run(noparallel))

    @property
    def status(self):
        return self.job.status


class DependencyTree():
    _context: Context
    _root_node: DependencyNode

    @property
    def context(self):
        return self._context

    @property
    def root_node(self):
        return self._root_node

    def __init__(self, context):
        self._context = context

        if len(self._context.parameters.targets) == 1:
            self._root_node = self._get_dependency_subtree(self._context.parameters.targets[0])
        else:
            dependent_subtree = list([self._get_dependency_subtree(target)
                                      for target in self._context.parameters.targets])
            root_job = Job(self._context, Target("root", [], []))
            self._root_node = DependencyNode(root_job, dependent_subtree)

    def _get_dependency_subtree(self, target_name: str) -> DependencyNode:
        target = get_target(self._context, target_name)
        job = get_job(self._context, target)
        dependent_subtree = list([self._get_dependency_subtree(dependency)
                                  for dependency in target.dependencies])
        return DependencyNode(job, dependent_subtree)

    def get_nodes(self, root=None):
        if root is None:
            root = self.root_node
        nodes = [root]
        nodes.extend([dependency
                      for node in root.dependencies
                      for dependency in self.get_nodes(node)])
        return nodes

    def start(self, noparallel=False):
        return self._root_node.start(noparallel)

    def run(self, noparallel=False):
        return self._root_node.run(noparallel)

    @property
    def status(self):
        return self.root_node.status


default_modules = [
    "runci.engine.runner.compose_build",
    "runci.engine.runner.compose_run",
    "runci.engine.runner.docker_build",
    "runci.engine.runner.target_run",
    "runci.engine.listener.terminal",
]


def create_context(project, parameters, modules=default_modules):
    runners = {}
    listeners = {}
    processors = {}

    for module_name in modules:
        importlib.import_module(module_name)
        for name, obj in inspect.getmembers(sys.modules[module_name], inspect.isclass):
            if issubclass(obj, RunnerBase):
                runners[obj.get_selector()] = obj

            if issubclass(obj, ListenerBase):
                for event_type, listener in obj.event_listeners.items():
                    listeners[event_type] = listeners.get(event_type, []) + [listener]

                for event_type, processor in obj.event_processors.items():
                    processors[event_type] = processors.get(event_type, []) + [processor]

    context = Context(project, parameters, runners, listeners, processors)
    return context


def get_target(context, target_name: str) -> Target:
    matching_targets = [t for t in context.project.targets if t.name == target_name]
    if len(matching_targets) == 0:
        raise UnknownTargetException("Can't find target " + target_name)
    elif len(matching_targets) == 0:
        raise AmbiguousTargetException("Ambiguous target: " + target_name)

    return matching_targets[0]


def get_job(context, target: Target) -> Job:
    job = context.jobs.get(target.name, None)
    if job is None:
        job = Job(context, target)
        context.jobs[target.name] = job

    return job


def get_jobs(context: Context) -> list:
    return list(context.jobs.values())
