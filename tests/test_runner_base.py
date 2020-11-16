import asyncio
import sys
import unittest

from runci.entities.context import Context
from runci.engine.runner.base import RunnerBase


class test_runner_base(unittest.TestCase):
    test_command = "sleep 1; " + \
                  "echo stdout1 && echo stderr1 1>&2; " + \
                  "echo stdout2 && echo stderr2 1>&2; " + \
                  "echo stderr3 1>&2 && echo stdout3;"

    def test_catch_exception(self):
        class TestRunner(RunnerBase):
            async def run_internal(self, context: Context):
                raise Exception("Simulating failed runner")

        context = Context(None, None, None, None, None)
        test_runner = TestRunner(lambda e: None, dict())
        asyncio.run(test_runner.run(context))
        self.assertFalse(test_runner.is_succeeded)

    def test_failed_process(self):
        command = "exit 1"

        class TestRunner(RunnerBase):
            async def run_internal(self, context: Context):
                await self._run_process(["sh", "-c", command])

        context = Context(None, None, None, None, None)
        test_runner = TestRunner(lambda e: None, dict())
        asyncio.run(test_runner.run(context))
        self.assertFalse(test_runner.is_succeeded)

    def test_successful_process(self):
        command = "exit 0"

        class TestRunner(RunnerBase):
            async def run_internal(self, context: Context):
                await self._run_process(["sh", "-c", command])

        context = Context(None, None, None, None, None)
        test_runner = TestRunner(lambda e: None, dict())
        asyncio.run(test_runner.run(context))
        self.maxDiff = None
        self.assertTrue(test_runner.is_succeeded)

    @unittest.skip("Not properly implemented")
    def test_process_output(self):
        messages = list()
        command = self.test_command

        def _log_message(output_stream, message):
            if message != []:
                messages.append([output_stream, message])

        class TestRunner(RunnerBase):
            async def run_internal(self, context: Context):
                await self._run_process(["sh", "-c", command])

        context = Context(None, None, None, None, None, None)
        test_runner = TestRunner(_log_message, dict())
        asyncio.run(test_runner.run(context))
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
