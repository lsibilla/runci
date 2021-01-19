import asyncio
from enum import Enum

from runci.entities import event
from runci.entities.context import Context
from runci.entities.config import Target


class JobStatus(Enum):
    "runci job status enum type"
    CREATED = 'created'
    STARTED = 'started'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELED = 'canceled'
    PAUSED = 'paused'


class Job(object):
    """description of class"""

    _context: Context
    _target: Target
    _status: JobStatus
    _events: asyncio.Queue
    _job_event_listeners: dict
    _job_event_processors: dict

    def __init__(self, context: Context, target: Target):
        self._context = context
        self._target = target
        self._status = JobStatus.CREATED
        self._events = None
        self._job_event_listeners = {
            event.JobStepPauseEvent: [self.pause],
            event.JobStepResumeEvent: [self.resume],
        }
        self._job_event_processors = {}

    def _ensure_event_queue_is_created(self):
        if self._events is None:
            self._events = asyncio.Queue()

    def _log_event(self, job_event):
        if not isinstance(job_event, event.JobEvent):
            raise Exception("Event logged is not of type JobEvent or subclass")
        else:
            self._ensure_event_queue_is_created()
            self._events.put_nowait(job_event)

            listeners = self._context.listeners.get(type(job_event), []) + \
                self._job_event_listeners.get(type(job_event), [])

            for listener in listeners:
                listener(job_event)

    async def _start(self):
        if self._status == JobStatus.CREATED:
            self._status = JobStatus.STARTED
            self._log_event(event.JobStartEvent(self._target))

            for step in self._target.steps:
                step_runner_cls = self._context.runners.get(step.type, None)
                if step_runner_cls is not None:
                    step_runner = step_runner_cls(self._target, self._log_event, step.spec)
                    await step_runner.run(self._context)
                    if step_runner.is_succeeded:
                        self._log_event(event.JobStepSuccessEvent(self._target))
                    else:
                        self._log_event(event.JobStepFailureEvent(self._target))
                        self.fail()
                        break
                else:
                    self._log_event(event.JobStepUnknownTypeEvent(self._target))
                    self.fail()
                    break

            if self._status == JobStatus.STARTED:
                self.success()

    def start(self):
        self._task = asyncio.create_task(self._start())
        return self._task

    def run(self):
        return asyncio.run(self._start())

    def pause(self, job_event=None):
        if self._status in [JobStatus.STARTED]:
            self._status = JobStatus.PAUSED
            self._log_event(event.JobPauseEvent(self._target))

    def resume(self, job_event=None):
        if self._status in [JobStatus.PAUSED]:
            self._status = JobStatus.STARTED
            self._log_event(event.JobResumeEvent(self._target))

    def success(self, job_event=None):
        if self._status in [JobStatus.CREATED, JobStatus.STARTED]:
            self._status = JobStatus.SUCCEEDED
            self._log_event(event.JobSuccessEvent(self._target))

    def fail(self, job_event=None):
        self._log_event(event.JobFailureEvent(self._target))
        self._status = JobStatus.FAILED

    def cancel(self, job_event=None):
        if self._status == JobStatus.CREATED:
            self._log_event(event.JobCanceledEvent(self._target))
            self._status = JobStatus.CANCELED
        elif self._status == JobStatus.STARTED:
            self._task.cancel()
            self._log_event(event.JobCanceledEvent(self._target))
            self._status = JobStatus.CANCELED

    @property
    def status(self) -> JobStatus:
        return self._status

    def has_new_events(self):
        return not (self._events is None
                    or self._events.empty())

    async def process_events(self, no_wait=True):
        self._ensure_event_queue_is_created()

        while ((not no_wait and self._status == JobStatus.STARTED) or
               not self._events.empty()):
            job_event = await self._events.get()
            processors = self._context.processors.get(type(job_event), [])
            for processor in processors:
                processor(job_event)
