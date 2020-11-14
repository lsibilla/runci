import asyncio
import sys
import unittest
from unittest.mock import patch, call

from runci.engine.runner.base import RunnerBase
from runci.engine import runner
from runci.engine.job import Job, JobStatus, JobStepUnknownTypeEvent
from runci.entities.config import Project, Target, Step


class test_job(unittest.TestCase):
    test_command = "sleep 1; " + \
                  "echo stdout1 && echo stderr1 1>&2; " + \
                  "echo stdout2 && echo stderr2 1>&2; " + \
                  "echo stderr3 1>&2 && echo stdout3;"

    @patch("runci.engine.job.Job._log_event")
    def test_invalid_step_type(self, mock):
        target = Target("test", "", [Step("test", "invalid", {})])
        job = Job(None, target)
        job.run()
        self.assertEqual(job.status, JobStatus.FAILED)
        self.assertTrue(any([call for call in mock.mock_calls
                             if isinstance(call.args[0], JobStepUnknownTypeEvent)]))

    @patch("runci.engine.job.Job._log_message_event")
    def test_exception(self, mock):
        class TestRunner(RunnerBase):
            async def run_internal(self, project: Project):
                raise Exception("Simulating an exception")

        runner.register_runner("mock", TestRunner)
        target = Target("test", "", [Step("test", "mock", {})])
        job = Job(None, target)
        job.run()
        self.assertEqual(job.status, JobStatus.FAILED)

        mock.assert_has_calls([call(sys.stdout, 'Starting TestRunner runner\n'),
                               call(sys.stderr, 'Runner TestRunner failed:')])
        stacktrace_call = mock.mock_calls[2]
        stream, message = stacktrace_call.args
        self.assertEqual(stream, sys.stderr)
        self.assertRegex(message, "^Traceback ")
        self.assertRegex(message, "Exception: Simulating an exception$")

    @patch("sys.stderr")
    @patch("sys.stdout")
    @patch("runci.engine.job.Job._start", autospec=True)
    def test_release_messages(self, mock, mock_stdout, mock_stderr):
        command = self.test_command

        class TestRunner(RunnerBase):
            async def run_internal(self, project: Project):
                await self._run_process(["sh", "-c", command])

        async def job_start(self):
            self._messages = asyncio.Queue()
            self._status = JobStatus.STARTED
            self.runner = TestRunner(self._log_message_event, dict())
            await self.runner.run(self._project)

        mock.side_effect = job_start
        mock_stdout.encoding = 'utf-8'
        mock_stderr.encoding = 'utf-8'
        job = Job(None, None)
        job.run()
        self.assertTrue(job.runner.is_succeeded)

        self.assertTrue(job.has_new_events())
        job.release_new_events()
        self.assertFalse(job.has_new_events())


if __name__ == '__main__':
    unittest.main()
