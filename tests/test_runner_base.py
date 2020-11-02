import asyncio
import sys
import unittest

from runci.entities.config import Project
from runci.engine import runner


class test_runner_base(unittest.TestCase):
    test_command = "sleep 1; " + \
                  "echo stdout1 && echo stderr1 1>&2; " + \
                  "echo stdout2 && echo stderr2 1>&2; " + \
                  "echo stderr3 1>&2 && echo stdout3;"

    def test_catch_exception(self):
        class TestRunner(runner.RunnerBase):
            async def run_internal(self, project: Project):
                raise Exception("Simulating failed runner")

        project = Project([], [], [])
        test_runner = TestRunner(lambda s, m: m, dict())
        asyncio.run(test_runner.run(project))
        self.assertFalse(test_runner.is_succeeded)

    def test_failed_process(self):
        messages = list()
        command = "exit 1"

        def _log_message(output_stream, message):
            if message != []:
                messages.append([output_stream, message])

        class TestRunner(runner.RunnerBase):
            async def run_internal(self, project: Project):
                await self._run_process(["sh", "-c", command])

        project = Project([], [], [])
        test_runner = TestRunner(_log_message, dict())
        asyncio.run(test_runner.run(project))
        self.assertFalse(test_runner.is_succeeded)

    def test_successful_process(self):
        messages = list()
        command = "exit 0"

        def _log_message(output_stream, message):
            if message != []:
                messages.append([output_stream, message])

        class TestRunner(runner.RunnerBase):
            async def run_internal(self, project: Project):
                await self._run_process(["sh", "-c", command])

        project = Project([], [], [])
        test_runner = TestRunner(_log_message, dict())
        asyncio.run(test_runner.run(project))
        self.maxDiff = None
        self.assertTrue(test_runner.is_succeeded)

    @unittest.skip("Not properly implemented")
    def test_process_output(self):
        messages = list()
        command = self.test_command

        def _log_message(output_stream, message):
            if message != []:
                messages.append([output_stream, message])

        class TestRunner(runner.RunnerBase):
            async def run_internal(self, project: Project):
                await self._run_process(["sh", "-c", command])

        project = Project([], [], [])
        test_runner = TestRunner(_log_message, dict())
        asyncio.run(test_runner.run(project))
        self.maxDiff = None
        self.assertListEqual(messages,
                             [[sys.stdout, 'Starting TestRunner runner\n'],
                              [sys.stdout, 'Running command: sh -c ' + command + '\n'],
                              [sys.stdout, b'stdout1\n'],
                              [sys.stderr, b'stderr1\n'],
                              [sys.stdout, b'stdout2\n'],
                              [sys.stderr, b'stderr2\n'],
                              [sys.stderr, b'stderr3\n'],
                              [sys.stdout, b'stdout3\n'],
                              [sys.stdout, b''],
                              [sys.stderr, b'']])


if __name__ == '__main__':
    unittest.main()
