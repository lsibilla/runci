import asyncio
from collections import namedtuple

from runci.entities import config
from runci.engine.job import Job, JobStatus


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
    _project: config.Project
    _root_node: DependencyNode
    _job_dict: dict

    @property
    def project(self):
        return self._project

    @property
    def root_node(self):
        return self._root_node

    def __init__(self, project: config.Project):
        self._project = project
        self._job_dict = dict()

        if len(project.parameters.targets) == 1:
            self._root_node = self._get_dependency_subtree(project.parameters.targets[0])
        else:
            dependent_subtree = list([self._get_dependency_subtree(target)
                                      for target in project.parameters.targets])
            root_job = Job(project, config.Target("root", [], []))
            self._root_node = DependencyNode(root_job, dependent_subtree)

    def _get_dependency_subtree(self, target_name: str) -> DependencyNode:
        target = self._get_target(self.project, target_name)
        job = self._get_job(self.project, target)
        dependent_subtree = list([self._get_dependency_subtree(dependency)
                                  for dependency in target.dependencies])
        return DependencyNode(job, dependent_subtree)

    def _get_target(self, project: config.Project, target_name: str) -> config.Target:
        matching_targets = [t for t in self.project.targets if t.name == target_name]
        if len(matching_targets) == 0:
            raise UnknownTargetException("Can't find target " + target_name)
        elif len(matching_targets) == 0:
            raise AmbiguousTargetException("Ambiguous target: " + target_name)

        return matching_targets[0]

    def _get_job(self, project: config.Project, target: config.Target) -> Job:
        job = self._job_dict.get(target.name, None)
        if job is None:
            job = Job(project, target)
            self._job_dict[target.name] = job

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
