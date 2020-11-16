import enum


class RunnerStatus(enum.Enum):
    "runci step status enum type"
    CREATED = 'created'
    STARTED = 'started'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELED = 'canceled'
    PAUSED = 'paused'
