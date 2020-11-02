import asyncio
import sys
import unittest
from unittest.mock import patch, call

from runci.engine import runner
from runci.engine.job import Job, JobStatus
from runci.entities.config import Project, Target, Step


class test_job(unittest.TestCase):
    test_command = "sleep 1; " + \
                  "echo stdout1 && echo stderr1 1>&2; " + \
                  "echo stdout2 && echo stderr2 1>&2; " + \
                  "echo stderr3 1>&2 && echo stdout3;"

    @patch("runci.engine.job.Job._log_message")
    def test_invalid_step_type(self, mock):
        target = Target("test", "", [Step("test", "invalid", {})])
        job = Job(None, target)
        job.run()
        self.assertEqual(job.status, JobStatus.FAILED)
        mock.assert_called_once_with(sys.stderr, 'Unknown step type: invalid')

    @patch("runci.engine.job.Job._log_message")
    def test_exception(self, mock):
        class TestRunner(runner.RunnerBase):
            async def run_internal(self, project: Project):
                raise Exception("Simulating an exception")

        runner.selector["mock"] = TestRunner
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

        class TestRunner(runner.RunnerBase):
            async def run_internal(self, project: Project):
                await self._run_process(["sh", "-c", command])

        async def job_start(self):
            self._messages = asyncio.Queue()
            self._status = JobStatus.STARTED
            self.runner = TestRunner(self._log_message, dict())
            await self.runner.run(self._project)

        mock.side_effect = job_start
        job = Job(None, None)
        job.run()
        self.assertTrue(job.runner.is_succeeded)

        self.assertTrue(job.has_new_messages())
        job.release_new_messages()
        self.assertFalse(job.has_new_messages())


if __name__ == '__main__':
    unittest.main()
