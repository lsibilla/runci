import asyncio
import unittest

from runci.entities.config import Project, Target, Step
from runci.entities.parameters import Parameters
from runci.engine.core import create_context, DependencyTree
from runci.engine.runner.docker_pull import DockerPullRunner
from unittest.mock import patch, call


class test_runner_docker_build(unittest.TestCase):
    step = Step("test", "docker-pull", {
        "image": "busybox alpine"
    })

    project = Project(
        services=[],
        targets=[Target(
            name="target",
            dependencies=[],
            steps=[step]
        )])
    parameters = Parameters(dataconnection="runci.yml", targets=["target"], verbosity=0)

    @patch('runci.engine.runner.docker_pull.DockerPullRunner._run_process')
    def test_command_line_args(self, mock):
        async def run():
            runner = DockerPullRunner(self.project.targets[0], self.step, lambda e: None)
            context = create_context(self.project, self.parameters)
            await runner.run(context)

        asyncio.run(run())
        mock.assert_has_calls([
            call('docker pull busybox'.split(' ')),
            call('docker pull alpine'.split(' '))])

    @patch('runci.engine.runner.docker_pull.DockerPullRunner.run')
    def test_integration(self, mock):
        context = create_context(self.project, self.parameters)
        DependencyTree(context).run()
        mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
