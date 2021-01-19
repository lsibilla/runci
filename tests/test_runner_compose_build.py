import asyncio
import unittest
from runci.entities.config import Project, Target, Step
from runci.entities.parameters import Parameters
from runci.engine.core import create_context, DependencyTree
from runci.engine.runner.compose_build import ComposeBuildRunner
from unittest.mock import patch


class test_runner_compose_build(unittest.TestCase):
    step = Step("test", "compose-build", {})
    project = Project(
        services=[],
        targets=[Target(
            name="target",
            dependencies=[],
            steps=[step]
        )])
    parameters = Parameters(dataconnection="runci.yml", targets=["target"], verbosity=0)

    @patch('runci.engine.runner.compose_build.ComposeBuildRunner._run_process')
    def test_command_line_args(self, mock):

        async def run():
            runner = ComposeBuildRunner(None, lambda e: None, self.step.spec)
            context = create_context(self.project, self.parameters)
            await runner.run(context)

        asyncio.run(run())
        mock.assert_called_once_with('docker-compose -f runci.yml build'.split(' '))

    @patch('runci.engine.runner.compose_build.ComposeBuildRunner.run')
    def test_integration(self, mock):
        context = create_context(self.project, self.parameters)
        DependencyTree(context).run()
        mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
