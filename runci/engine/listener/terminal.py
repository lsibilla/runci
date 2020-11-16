import sys

from runci.entities import event
from .base import ListenerBase


class TerminalListener(ListenerBase):
    @staticmethod
    def message_event_logger(job_event: event.JobMessageEvent):
        valid_streams = [sys.stdout, sys.stderr]
        job_message = job_event.message
        message = job_message.message
        stream = job_message.stream

        if isinstance(message, bytes):
            message = message.decode(stream.encoding)

        if stream in valid_streams:
            stream.write(message)
        else:
            print("Unknown stream: " + stream, file=sys.stderr)
            print("Message: " + message, file=sys.stderr)

    event_processors = {
        event.JobMessageEvent: message_event_logger.__func__
    }
