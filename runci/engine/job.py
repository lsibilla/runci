import asyncio
from enum import Enum
from collections import namedtuple
from datetime import datetime
import sys

from runci.entities import config
from runci.engine import runner


class JobStatus(Enum):
    "runci job status enum type"
    CREATED = 'created'
    STARTED = 'started'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELED = 'canceled'


class JobOutput(namedtuple("JobOutput", "stream timestamp message")):
    """Represent a RunCI runner output line to stdout or stderr"""
    _valid_streams = [sys.stdout, sys.stderr]

    def __new__(cls, stream, message):
        timestamp = datetime.now()
        return super(JobOutput, cls).__new__(cls, stream, timestamp, message)

    def release(self):
        message = self.message
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        message = message.rstrip()

        if self.stream in self._valid_streams:
            print(message, file=self.stream)
        else:
            print("Unknown stream: " + self.stream, file=sys.stderr)
            print("Message: " + message, file=sys.stderr)


class Job(object):
    """description of class"""

    _project: config.Project
    _target: config.Target
    _status: JobStatus
    _messages: asyncio.Queue

    def __init__(self, project: config.Project, target: config.Target):
        self._project = project
        self._target = target
        self._status = JobStatus.CREATED
        self._messages = None

    def _log_message(self, output_stream, message):
        if message != []:
            self._messages.put_nowait(JobOutput(output_stream, message))

    async def _start(self):
        if self._status == JobStatus.CREATED:
            self._status = JobStatus.STARTED
            self._messages = asyncio.Queue()

            for step in self._target.steps:
                step_runner_cls = runner.selector.get(step.type, None)
                if step_runner_cls is not None:
                    step_runner = step_runner_cls(self._log_message, step.spec)
                    await step_runner.run(self._project)
                    if not step_runner.is_succeeded:
                        self._log_message(sys.stderr, 'Step %s failed.' % step.name)
                        self._status = JobStatus.FAILED
                        break
                else:
                    self._log_message(sys.stderr, 'Unknown step type: %s' % step.type)
                    self._status = JobStatus.FAILED
                    break

            if self._status == JobStatus.STARTED:
                self._status = JobStatus.SUCCEEDED

    def start(self):
        self._task = asyncio.create_task(self._start())
        return self._task

    def run(self):
        return asyncio.run(self._start())

    def cancel(self):
        if self._status == JobStatus.CREATED:
            self._status = JobStatus.CANCELED
        elif self._status == JobStatus.STARTED:
            self._task.cancel()
            self._status = JobStatus.CANCELED

    @property
    def status(self) -> JobStatus:
        return self._status

    def has_new_messages(self):
        if self._messages:
            return not self._messages.empty()

    def release_new_messages(self):
        if self._messages:
            while not self._messages.empty():
                self._messages.get_nowait().release()
