from abc import ABC
from collections import namedtuple
from datetime import datetime


class JobEvent(ABC):
    pass


class JobMessage(namedtuple("JobMessage", "stream timestamp message")):
    """Represent a RunCI runner output line to stdout or stderr"""
    def __new__(cls, stream, message):
        timestamp = datetime.now()
        return super(JobMessage, cls).__new__(cls, stream, timestamp, message)


class JobMessageEvent(JobEvent):
    """Represent a RunCI runner output line to stdout or stderr event"""
    _message: JobMessage

    def __init__(self, stream, message):
        self._message = JobMessage(stream, message)

    @property
    def message(self):
        return self._message


class JobStartEvent(JobEvent):
    pass


class JobStepStartEvent(JobEvent):
    pass


class JobStepPauseEvent(JobEvent):
    pass


class JobStepResumeEvent(JobEvent):
    pass


class JobStepEndEvent(JobEvent):
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
