import asyncio
from enum import Enum
import sys
import traceback

from runci.entities import config
from runci.entities.parameters import Parameters
from runci.engine import runner


class JobStepStatus(Enum):
    "runci step status enum type"
    CREATED = 'created'
    STARTED = 'started'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELED = 'canceled'
    
class JobStatus(Enum):
    "runci job status enum type"
    CREATED = 'created'
    STARTED = 'started'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELED = 'canceled'
    
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
            self._messages.put_nowait(runner.RunnerOutput(output_stream, message))

    async def _start(self):
        if self._status == JobStatus.CREATED:
            self._messages = asyncio.Queue()
            try:
                self._status = JobStatus.STARTED

                for step in self._target.steps:
                    if step.type=='compose-build':
                        step_runner = runner.ComposeBuildRunner(self._messages, step.spec)
                        await step_runner.run(self._project)
                        if step_runner.status != JobStepStatus.SUCCEEDED:
                            self._log_message(sys.stderr, 'Step %s failed.' % step.name)
                            self._status = JobStatus.FAILED
                            break
                    else:
                        self._log_message(sys.stderr, 'Unknown step type: %s' % step.type)
                        self._status = JobStatus.FAILED
                        break
            except:
                self._log_message(sys.stderr, traceback.format_exc())
                self._status = JobStatus.FAILED
            else:
                self._status = JobStatus.SUCCEEDED

    def wait(self):
        return asyncio.ensure_future(self._task)
    
    def start(self):
        self._task = asyncio.create_task(self._start())
        return self._task

    def run(self):
        return asyncio.run(self._start())

    def cancel(self):
        if self._status == JobStatus.CREATED or self._status == JobStatus.STARTED:
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

