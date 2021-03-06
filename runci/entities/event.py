from abc import ABC
from collections import namedtuple
from datetime import datetime

from runci.entities.config import Target, Step


class JobEvent(ABC):
    _timestamp: datetime
    _target: Target

    def __init__(self, target: Target):
        self._timestamp = datetime.now()
        self._target = target

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def target(self):
        return self._target

    pass


class JobStepEvent(JobEvent):
    _step: Step

    def __init__(self, target: Target, step: Step):
        self._step = step
        super().__init__(target)


class JobMessage(namedtuple("JobMessage", "stream message")):
    """Represent a RunCI runner output line to stdout or stderr"""
    def __new__(cls, stream, message):
        return super(JobMessage, cls).__new__(cls, stream, message)


class JobMessageEvent(JobEvent):
    """Represent a RunCI runner output line to stdout or stderr event"""
    _message: JobMessage

    def __init__(self, target: Target, stream, message):
        self._message = JobMessage(stream, message)
        super().__init__(target)

    @property
    def message(self):
        return self._message


class JobStartEvent(JobEvent):
    pass


class JobStepStartEvent(JobStepEvent):
    pass


class JobStepPauseEvent(JobStepEvent):
    pass


class JobStepResumeEvent(JobStepEvent):
    pass


class JobStepEndEvent(JobStepEvent):
    pass


class JobStepSuccessEvent(JobStepEndEvent):
    pass


class JobStepFailureEvent(JobStepEndEvent):
    pass


class JobStepUnknownTypeEvent(JobStepFailureEvent):
    pass


class JobPauseEvent(JobEvent):
    pass


class JobResumeEvent(JobEvent):
    pass


class JobEndEvent(JobEvent):
    pass


class JobSuccessEvent(JobEndEvent):
    pass


class JobFailureEvent(JobEndEvent):
    pass


class JobCanceledEvent(JobFailureEvent):
    pass
