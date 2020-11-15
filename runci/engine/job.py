from abc import ABC, abstractmethod
import asyncio
from enum import Enum
from collections import namedtuple
from datetime import datetime
import sys

from runci.entities.context import Context
from runci.entities.config import Target


class JobStatus(Enum):
    "runci job status enum type"
    CREATED = 'created'
    STARTED = 'started'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELED = 'canceled'


class JobEvent(ABC):
    @abstractmethod
    def release(self):
        pass


class JobMessage(namedtuple("JobMessage", "stream timestamp message")):
    """Represent a RunCI runner output line to stdout or stderr"""
    _valid_streams = [sys.stdout, sys.stderr]

    def __new__(cls, stream, message):
        timestamp = datetime.now()
        return super(JobMessage, cls).__new__(cls, stream, timestamp, message)

    def release(self):
        message = self.message
        if isinstance(message, bytes):
            message = message.decode(self.stream.encoding)

        if self.stream in self._valid_streams:
            self.stream.write(message)
        else:
            print("Unknown stream: " + self.stream, file=sys.stderr)
            print("Message: " + message, file=sys.stderr)


class JobMessageEvent(JobEvent):
    """Represent a RunCI runner output line to stdout or stderr event"""
    data: JobMessage

    def __init__(self, stream, message):
        self.data = JobMessage(stream, message)

    def release(self):
        self.data.release()


class JobStartEvent(JobEvent):
    def release(self):
        pass


class JobStepStartEvent(JobEvent):
    def release(self):
        pass


class JobStepEndEvent(JobEvent):
    def release(self):
        pass


class JobStepSuccessEvent(JobStepEndEvent):
    def release(self):
        pass


class JobStepFailureEvent(JobStepEndEvent):
    def release(self):
        pass


class JobStepUnknownTypeEvent(JobStepFailureEvent):
    def release(self):
        pass


class JobEndEvent(JobEvent):
    def release(self):
        pass


class JobSuccessEvent(JobEndEvent):
    def release(self):
        pass


class JobFailureEvent(JobEndEvent):
    def release(self):
        pass


class JobCanceledEvent(JobFailureEvent):
    def release(self):
        pass


class Job(object):
    """description of class"""

    _context: Context
    _target: Target
    _status: JobStatus
    _events: asyncio.Queue

    def __init__(self, context: Context, target: Target):
        self._context = context
        self._target = target
        self._status = JobStatus.CREATED
        self._events = None

    def _ensure_event_queue_is_created(self):
        if self._events is None:
            self._events = asyncio.Queue()

    def _log_message_event(self, output_stream, message):
        if message != []:
            self._log_event(JobMessageEvent(output_stream, message))

    def _log_event(self, event):
        if not isinstance(event, JobEvent):
            raise Exception("Event logged is not of type JobEvent or subclass")
        else:
            self._ensure_event_queue_is_created()
            self._events.put_nowait(event)

    async def _start(self):
        if self._status == JobStatus.CREATED:
            self._status = JobStatus.STARTED
            self._log_event(JobStartEvent())

            for step in self._target.steps:
                step_runner_cls = self._context.runners.get(step.type, None)
                if step_runner_cls is not None:
                    step_runner = step_runner_cls(self._log_message_event, step.spec)
                    await step_runner.run(self._context)
                    if step_runner.is_succeeded:
                        self._log_event(JobStepSuccessEvent())
                    else:
                        self._log_event(JobStepFailureEvent())
                        self.fail()
                        break
                else:
                    self._log_event(JobStepUnknownTypeEvent())
                    self.fail()
                    break

            if self._status == JobStatus.STARTED:
                self.success()

    def start(self):
        self._task = asyncio.create_task(self._start())
        return self._task

    def run(self):
        return asyncio.run(self._start())

    def success(self):
        if self._status in [JobStatus.CREATED, JobStatus.STARTED]:
            self._status = JobStatus.SUCCEEDED
            self._log_event(JobSuccessEvent())

    def fail(self):
        self._log_event(JobFailureEvent())
        self._status = JobStatus.FAILED

    def cancel(self):
        if self._status == JobStatus.CREATED:
            self._log_event(JobCanceledEvent())
            self._status = JobStatus.CANCELED
        elif self._status == JobStatus.STARTED:
            self._task.cancel()
            self._log_event(JobCanceledEvent())
            self._status = JobStatus.CANCELED

    @property
    def status(self) -> JobStatus:
        return self._status

    def has_new_events(self):
        return not (self._events is None
                    or self._events.empty())

    def release_new_events(self):
        if self._events is not None:
            while not self._events.empty():
                self._events.get_nowait().release()

    async def release_all_events(self):
        self._ensure_event_queue_is_created()
        job_running = self._status == JobStatus.STARTED

        if job_running:
            while job_running:
                message = await self._events.get()
                message.release()
                job_running = not isinstance(message, JobEndEvent)
        else:
            self.release_new_events()
