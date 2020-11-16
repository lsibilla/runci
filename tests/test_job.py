import asyncio
import unittest
from unittest.mock import patch

from runci.engine import core
from runci.engine.runner.base import RunnerBase
from runci.engine.job import Job, JobStatus
from runci.entities.context import Context
from runci.entities.config import Project, Target, Step
from runci.entities.event import JobStartEvent, JobStepUnknownTypeEvent, JobFailureEvent


class test_job(unittest.TestCase):
    test_command = "sleep 1; " + \
                  "echo stdout1 && echo stderr1 1>&2; " + \
                  "echo stdout2 && echo stderr2 1>&2; " + \
                  "echo stderr3 1>&2 && echo stdout3;"

    @patch("runci.engine.job.Job._log_event")
    def test_invalid_step_type(self, mock):
        target = Target("test", "", [Step("test", "invalid", {})])
        project = Project([], [target])
        context = core.create_context(project, None)
        job = Job(context, target)
        job.run()
        self.assertEqual(job.status, JobStatus.FAILED)
        self.assertTrue(any([mock_call for mock_call in mock.mock_calls
                             if isinstance(mock_call.args[0], JobStepUnknownTypeEvent)]))

    @patch("runci.engine.job.Job._log_event")
    def test_exception(self, mock):
        class TestRunner(RunnerBase):
            async def run_internal(self, project: Project):
                raise Exception("Simulating an exception")

        target = Target("test", "", [Step("test", "mock", {})])
        project = Project([], [target])
        context = core.create_context(project, None)
        job = Job(context, target)
        job.run()
        self.assertEqual(job.status, JobStatus.FAILED)

        self.assertEqual(mock.call_count, 3)
        self.assertIsInstance(mock.mock_calls[0].args[0], JobStartEvent)
        self.assertIsInstance(mock.mock_calls[1].args[0], JobStepUnknownTypeEvent)
        self.assertIsInstance(mock.mock_calls[2].args[0], JobFailureEvent)

    def test_release_messages(self):
        command = self.test_command

        class TestRunner(RunnerBase):
            async def run_internal(self, context: Context):
                await self._run_process(["sh", "-c", command])

        target = Target("test", "", [Step("test", "mock", {})])
        project = Project([], [target])
        context = core.create_context(project, None)
        context.runners["mock"] = TestRunner
        job = Job(context, target)
        job.run()
        self.assertEqual(job.status, JobStatus.SUCCEEDED)

        self.assertTrue(job.has_new_events())
        asyncio.run(job.process_events())
        self.assertFalse(job.has_new_events())


if __name__ == '__main__':
    unittest.main()
