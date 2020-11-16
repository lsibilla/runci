from parameterized import parameterized
import unittest
from unittest.mock import patch, call

from runci.entities.config import Project, Target, Step
from runci.entities.parameters import Parameters
from runci.engine.core import UnknownTargetException
from runci.engine import core, job, runner

param_inexistent_target = [
    Project(services=[],
            targets=[Target(name="target",
                            dependencies=[],
                            steps=[])]),
    Parameters(dataconnection="runci.yml",
               targets=["inexistant_target"],
               verbosity=0)
    ]

param_simple_target_single_step = [
    Project(services=[],
            targets=[Target(name="target",
                            dependencies=[],
                            steps=[Step("test", "compose-build", {"services": "s1"})])]),
    Parameters(dataconnection="runci.yml",
               targets=["target"],
               verbosity=0),
    [call("docker-compose -f runci.yml build s1".split(" "))]]

param_dependent_targets_single_step = [
    Project(services=[],
            targets=[Target(name="target1",
                            dependencies=["target2"],
                            steps=[Step("test", "compose-build", {"services": "s1"})]),
                     Target(name="target2",
                            dependencies=[],
                            steps=[Step("test", "compose-build", {"services": "s2"})])]),
    Parameters(dataconnection="runci.yml",
               targets=["target1"],
               verbosity=0),
    [call("docker-compose -f runci.yml build s2".split(" ")),
     call("docker-compose -f runci.yml build s1".split(" "))]]

param_parallel_targets_single_step = [
    Project(services=[],
            targets=[Target(name="target1",
                            dependencies=[],
                            steps=[Step("test", "compose-build", {"services": "s1"})]),
                     Target(name="target2",
                            dependencies=[],
                            steps=[Step("test", "compose-build", {"services": "s2"})])]),
    Parameters(dataconnection="runci.yml",
               targets=["target1", "target2"],
               verbosity=0),
    [call("docker-compose -f runci.yml build s1".split(" ")),
     call("docker-compose -f runci.yml build s2".split(" "))]]

param_parallel_dependent_targets_single_step = [
    Project(services=[],
            targets=[Target(name="target1",
                            dependencies=["target2", "target3"],
                            steps=[Step("test", "compose-build", {"services": "s1"})]),
                     Target(name="target2",
                            dependencies=[],
                            steps=[Step("test", "compose-build", {"services": "s2"})]),
                     Target(name="target3",
                            dependencies=[],
                            steps=[Step("test", "compose-build", {"services": "s3"})])]),
    Parameters(dataconnection="runci.yml",
               targets=["target1", "target2"],
               verbosity=0),
    [call("docker-compose -f runci.yml build s2".split(" ")),
     call("docker-compose -f runci.yml build s3".split(" ")),
     call("docker-compose -f runci.yml build s1".split(" "))]]

allparams = [param_simple_target_single_step,
             param_dependent_targets_single_step,
             param_parallel_targets_single_step,
             param_parallel_dependent_targets_single_step]

allparams_paralellization = ([param + [True] for param in allparams] +
                             [param + [False] for param in allparams])


class test_target(unittest.TestCase):
    @parameterized.expand([param_inexistent_target])
    def test_inexistent(self, project, parameters):
        with self.assertRaises(UnknownTargetException):
            context = core.create_context(project, parameters)
            core.DependencyTree(context).run()


@patch("runci.engine.runner.base.RunnerBase.run")
class test_run(unittest.TestCase):
    @parameterized.expand(allparams)
    def test_runner_run(self, mock, project, parameters, calls):
        context = core.create_context(project, parameters)
        core.DependencyTree(context).run()
        mock.assert_has_calls([call(context)])


@patch("runci.engine.runner.base.RunnerBase._run_process")
class test_run_process(unittest.TestCase):
    @parameterized.expand(allparams_paralellization)
    def test_command_line_args(self, mock, project, parameters, calls, noparallel):
        context = core.create_context(project, parameters)
        core.DependencyTree(context).run(noparallel)
        mock.assert_has_calls(calls)


@patch("runci.engine.runner.base.RunnerBase.run", autospec=True)
class test_build_result(unittest.TestCase):
    @parameterized.expand(allparams_paralellization)
    def test_sucessful_build(self, mock, project, parameters, calls, noparallel):
        def side_effect(self, project):
            self._status = runner.RunnerStatus.SUCCEEDED
        mock.side_effect = side_effect

        context = core.create_context(project, parameters)
        tree = core.DependencyTree(context)
        tree.run(noparallel)
        self.assertEqual(tree.status, job.JobStatus.SUCCEEDED)

    @parameterized.expand(allparams_paralellization)
    def test_failing_build(self, mock, project, parameters, calls, noparallel):
        def side_effect(self, project):
            self._status = runner.RunnerStatus.FAILED
        mock.side_effect = side_effect

        context = core.create_context(project, parameters)
        tree = core.DependencyTree(context)
        tree.run(noparallel)
        self.assertEqual(tree.status, job.JobStatus.FAILED)


if __name__ == '__main__':
    unittest.main()
