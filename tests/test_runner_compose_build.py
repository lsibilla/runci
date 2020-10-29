import asyncio
import unittest
from io import StringIO
from runci.entities.config import Project, Target, Step
from runci.entities.parameters import Parameters
from runci.engine.runner import RunnerBase,ComposeBuildRunner
from unittest.mock import MagicMock, patch

class test_runner_compose_build(unittest.TestCase):
    @patch('runci.engine.runner.ComposeBuildRunner._run_process')
    def test_command_line_args(self, mock):
        step = Step("test", "compose-build", dict())
        project = Project(
            services = [],
            targets = [Target(
                name="target",
                dependencies=[],
                steps=[step]
            )],
            parameters = Parameters(dataconnection="docker-compose.yml runci.yml", targets="target", verbosity=0)
        )

        async def run():
            runner = ComposeBuildRunner(asyncio.Queue(), step.spec)
            await runner.run(project)
        asyncio.run(run())
        mock.assert_called_once_with('docker-compose -f docker-compose.yml -f runci.yml build'.split(' '))

if __name__ == '__main__':
    unittest.main()
