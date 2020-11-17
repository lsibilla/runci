import asyncio
import unittest
from runci.entities.config import Project, Target, Step
from runci.entities.parameters import Parameters
from runci.engine.core import create_context, DependencyTree
from runci.engine.runner.compose_run import ComposeRunRunner
from unittest.mock import patch, call


class test_runner_compose_build(unittest.TestCase):
    step = Step("test", "compose-run", {"services": "app"})
    project = Project(
        services=[],
        targets=[Target(
            name="target",
            dependencies=[],
            steps=[step]
        )])
    parameters = Parameters(dataconnection="docker-compose.yml runci.yml", targets=["target"], verbosity=0)

    @patch('runci.engine.runner.compose_run.ComposeRunRunner._run_process')
    def test_command_line_args(self, mock):
        async def run():
            runner = ComposeRunRunner(lambda e: None, self.step.spec)
            context = create_context(self.project, self.parameters)
            await runner.run(context)

        asyncio.run(run())
        mock.assert_has_calls([call('docker-compose -f docker-compose.yml -f runci.yml run --rm app'.split(' ')),
                               call('docker-compose -f docker-compose.yml -f runci.yml down'.split(' '))])

    @patch('runci.engine.runner.compose_run.ComposeRunRunner.run')
    def test_integration(self, mock):
        context = create_context(self.project, self.parameters)
        DependencyTree(context).run()
        mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
