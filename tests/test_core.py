import asyncio
from parameterized import parameterized
import unittest
from unittest.mock import patch, MagicMock, call
from io import StringIO
import sys

from runci.entities.config import Project, Target, Step
from runci.entities.parameters import Parameters
from runci.engine.runner import RunnerBase, RunnerOutput
from runci.engine import core
from runci.engine.job import JobStatus

project_inexistent_target = [
        Project(services = [],
                targets = [Target(name="target",
                                    dependencies=[],
                                    steps=[])],
                parameters = Parameters(dataconnection="runci.yml",
                                        targets=["inexistant_target"],
                                        verbosity=0))]
param_simple_target_single_step = [
        Project(services = [],
                targets = [Target(name="target",
                                  dependencies=[],
                                  steps=[Step("test", "compose-build", dict())])],
                parameters = Parameters(dataconnection="runci.yml",
                                        targets=["target"],
                                        verbosity=0)),
        [call("docker-compose -f runci.yml build".split(" "))]]

param_dependent_targets_single_step = [
        Project(services = [],
                targets = [Target(name="target1",
                                  dependencies=["target2"],
                                  steps=[Step("test", "compose-build", {"services":"s1"})]),
                           Target(name="target2",
                                  dependencies=[],
                                  steps=[Step("test", "compose-build", {"services":"s2"})]
                        )],
                parameters = Parameters(dataconnection="runci.yml",
                                        targets=["target1"],
                                        verbosity=0)
            ),
        [call("docker-compose -f runci.yml build s2".split(" ")),
         call("docker-compose -f runci.yml build s1".split(" "))]]

param_parallel_targets_single_step = [
        Project(services = [],
                targets = [Target(name="target1",
                                  dependencies=[],
                                  steps=[Step("test", "compose-build", {"services":"s1"})]),
                           Target(name="target2",
                                  dependencies=[],
                                  steps=[Step("test", "compose-build", {"services":"s2"})]
                        )],
                parameters = Parameters(dataconnection="runci.yml",
                                        targets=["target1", "target2"],
                                        verbosity=0)
            ),
        [call("docker-compose -f runci.yml build s1".split(" ")),
         call("docker-compose -f runci.yml build s2".split(" "))]]

param_parallel_dependent_targets_single_step = [
        Project(services = [],
                targets = [Target(name="target1",
                                  dependencies=["target2", "target3"],
                                  steps=[Step("test", "compose-build", {"services":"s1"})]),
                           Target(name="target2",
                                  dependencies=[],
                                  steps=[Step("test", "compose-build", {"services":"s2"})]),
                           Target(name="target3",
                                  dependencies=[],
                                  steps=[Step("test", "compose-build", {"services":"s3"})]
                        )],
                parameters = Parameters(dataconnection="runci.yml",
                                        targets=["target1", "target2"],
                                        verbosity=0)
            ),
        [call("docker-compose -f runci.yml build s2".split(" ")),
         call("docker-compose -f runci.yml build s3".split(" ")),
         call("docker-compose -f runci.yml build s1".split(" "))]]

class test_core_target(unittest.TestCase):
    @parameterized.expand([project_inexistent_target])
    def test_inexistent_target(self, project):
        with self.assertRaises(core.UnknownTargetException):
            core.DependencyTree(project).run()

@patch("runci.engine.runner.RunnerBase.run")
class test_core_run(unittest.TestCase):
    @parameterized.expand([param_simple_target_single_step,
                           param_dependent_targets_single_step])
    def test_runner_run(self, mock, project, calls):
            core.DependencyTree(project).run()
            mock.assert_has_calls([call(project)])

@patch("runci.engine.runner.RunnerBase._run_process")
class test_core_run_process(unittest.TestCase):
    @parameterized.expand([param_simple_target_single_step,
                           param_dependent_targets_single_step,
                           param_parallel_targets_single_step,
                           param_parallel_dependent_targets_single_step])
    def test_command_line_args(self, mock, project, calls):
        core.DependencyTree(project).run(noparallel=False)
        mock.assert_has_calls(calls)

    @parameterized.expand([param_simple_target_single_step,
                           param_dependent_targets_single_step,
                           param_parallel_targets_single_step,
                           param_parallel_dependent_targets_single_step])
    def test_command_line_args_noparallel(self, mock, project, calls):
        core.DependencyTree(project).run(noparallel=True)
        mock.assert_has_calls(calls)

if __name__ == '__main__':
    unittest.main()
