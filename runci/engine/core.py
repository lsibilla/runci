import asyncio
from collections import namedtuple
import importlib
import inspect
import sys

from runci.entities.config import Target
from runci.entities.context import Context
from runci.engine.job import Job, JobStatus
from runci.engine.runner.base import RunnerBase


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
    def project(self):
        return self._project

    @property
    def root_node(self):
        return self._root_node

    def __init__(self):
        self._context = None
        pass

    def set_context(self, context):
        if self._context is not None and self._context != context:
            raise "DependencyTree context already set"

        self._context = context

        if len(self._context.parameters.targets) == 1:
            self._root_node = self._get_dependency_subtree(self._context.parameters.targets[0])
        else:
            dependent_subtree = list([self._get_dependency_subtree(target)
                                      for target in self._context.parameters.targets])
            root_job = Job(self._context.project, Target("root", [], []))
            self._root_node = DependencyNode(root_job, dependent_subtree)

    def _get_dependency_subtree(self, target_name: str) -> DependencyNode:
        target = self._get_target(target_name)
        job = self._get_job(target)
        dependent_subtree = list([self._get_dependency_subtree(dependency)
                                  for dependency in target.dependencies])
        return DependencyNode(job, dependent_subtree)

    def _get_target(self, target_name: str) -> Target:
        matching_targets = [t for t in self._context.project.targets if t.name == target_name]
        if len(matching_targets) == 0:
            raise UnknownTargetException("Can't find target " + target_name)
        elif len(matching_targets) == 0:
            raise AmbiguousTargetException("Ambiguous target: " + target_name)

        return matching_targets[0]

    def _get_job(self, target: Target) -> Job:
        job = self._context.jobs.get(target.name, None)
        if job is None:
            job = Job(self._context, target)
            self._context.jobs[target.name] = job

        return job

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


def create_context(project, parameters, modules=["compose_build", "compose_run", "docker_build"]):
    runners = {}
    for module in modules:
        module_fullname = "runci.engine.runner." + module
        importlib.import_module(module_fullname)
        for name, obj in inspect.getmembers(sys.modules[module_fullname], inspect.isclass):
            if issubclass(obj, RunnerBase):
                runners[obj.get_selector()] = obj

    tree = DependencyTree()
    context = Context(project, parameters, runners, tree)
    tree.set_context(context)
    return context
