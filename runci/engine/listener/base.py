from abc import ABC


class ListenerBase(ABC):
    event_listeners = {}
    event_processors = {}

    def __init__(self):
        pass
