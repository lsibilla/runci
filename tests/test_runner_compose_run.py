import asyncio
import unittest
from runci.entities.config import Project, Target, Step
from runci.entities.parameters import Parameters
from runci.engine import core
from runci.engine.runner.compose_run import ComposeRunRunner
from unittest.mock import patch


class test_runner_compose_build(unittest.TestCase):
    step = Step("test", "compose-run", {"services": "app"})
    project = Project(
        services=[],
        targets=[Target(
            name="target",
            dependencies=[],
            steps=[step]
        )],
        parameters=Parameters(dataconnection="docker-compose.yml runci.yml", targets=["target"], verbosity=0)
    )

    @patch('runci.engine.runner.compose_run.ComposeRunRunner._run_process')
    def test_command_line_args(self, mock):

        async def run():
            runner = ComposeRunRunner(lambda a, b: None, self.step.spec)
            await runner.run(self.project)

        asyncio.run(run())
        mock.assert_called_once_with('docker-compose -f docker-compose.yml -f runci.yml run --rm app'.split(' '))

    @patch('runci.engine.runner.compose_run.ComposeRunRunner.run')
    def test_integration(self, mock):
        core.DependencyTree(self.project).run()
        mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
