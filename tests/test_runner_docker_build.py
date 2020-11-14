import asyncio
import unittest
from runci.entities.config import Project, Target, Step
from runci.entities.parameters import Parameters
from runci.engine import core
from runci.engine.runner.docker_build import DockerBuildRunner
from unittest.mock import patch


class test_runner_docker_build(unittest.TestCase):
    step = Step("test", "docker-build", {
        "dockerfile": "Dockerfile",
        "tags": "runci/tag:latest runci/tag:v1.0"
    })

    project = Project(
        services=[],
        targets=[Target(
            name="target",
            dependencies=[],
            steps=[step]
        )],
        parameters=Parameters(dataconnection="runci.yml", targets=["target"], verbosity=0)
    )

    @patch('runci.engine.runner.docker_build.DockerBuildRunner._run_process')
    def test_command_line_args(self, mock):
        async def run():
            runner = DockerBuildRunner(lambda a, b: None, self.step.spec)
            await runner.run(self.project)

        asyncio.run(run())
        mock.assert_called_once_with('docker build -f Dockerfile -t runci/tag:latest -t runci/tag:v1.0 .'.split(' '))

    @patch('runci.engine.runner.docker_build.DockerBuildRunner.run')
    def test_integration(self, mock):
        core.DependencyTree(self.project).run()
        mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
