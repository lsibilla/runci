import asyncio
import sys

from .base import RunnerBase
from . import RunnerStatus
from runci.engine import core
from runci.engine.job import JobStatus
from runci.entities import event
from runci.entities.context import Context


class TargetRunRunner(RunnerBase):
    _selector = 'target-run'

    async def run_internal(self, context: Context):
        target_names = self.spec.get("target",
                                     self.spec.get("_", None))
        if target_names is None:
            raise Exception("Target should be specified for target-run step")

        self._log_runner_message(sys.stdout, "Running the following targets: " + target_names)

        targets = [core.get_target(context, target_name) for target_name in target_names.split(' ')]
        jobs = [core.get_job(context, target) for target in targets]

        self._status = RunnerStatus.PAUSED
        self._log_event(event.JobStepPauseEvent(self._target))
        await asyncio.gather(*[job.start() for job in jobs])
        self._status = RunnerStatus.STARTED
        self._log_event(event.JobStepResumeEvent(self._target))

        if any([job.status == JobStatus.FAILED for job in jobs]):
            self._status = RunnerStatus.FAILED
        elif any([job.status == JobStatus.CANCELED for job in jobs]):
            self._status = RunnerStatus.CANCELED
        elif all([job.status == JobStatus.SUCCEEDED for job in jobs]):
            self._status = RunnerStatus.SUCCEEDED
        else:
            raise Exception("Unexpected error: target-run has encountered inconsistent target results.")
