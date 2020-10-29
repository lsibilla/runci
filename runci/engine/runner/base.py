import asyncio
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime
from io import TextIOBase
import re
import subprocess
import time
import traceback
import sys

from runci.engine.job import JobStepStatus
from runci.entities.config import Project
from runci.entities.parameters import Parameters

class RunnerOutput(namedtuple("RunnerOutput", "stream timestamp message")):
    """Represent a RunCI runner output line to stdout or stderr"""
    _valid_streams = [sys.stdout, sys.stderr]
    
    def __new__(cls, stream, message):
        timestamp = datetime.now()
        return super(RunnerOutput, cls).__new__(cls, stream, timestamp, message)
    
    def release(self):
        message = self.message
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        message = re.sub("\r+\n+$", "", message)

        if self.stream in self._valid_streams:
            print(message, file=self.stream)
        else:
            print("Unknown stream: " + self.stream, sys.stderr)
            print("Message: " + message, file=sys.stderr)


class RunnerBase():
    spec: dict
    status: JobStepStatus
    _message_queue: asyncio.Queue

    def __init__(self, message_queue: asyncio.Queue, spec: dict):
        self.spec = spec
        self.status = JobStepStatus.CREATED
        self._message_queue = message_queue

    def _log_message(self, output_stream, message):
        if message != []:
            self._message_queue.put_nowait(RunnerOutput(output_stream, message))

    async def _log_stream(self, output_stream, input_stream:asyncio.StreamReader):
        if not output_stream in [sys.stdout, sys.stderr]:
            raise Exception("output_stream should be stdout or stderr")
        while not input_stream.at_eof():
            self._log_message(output_stream, await input_stream.readline())

    @abstractmethod
    async def run_internal(self, project:Project):
        pass

    async def run(self, project:Project):
        self.status = JobStepStatus.STARTED
        self._log_message(sys.stdout, "Starting %s runner\n" % type(self).__name__)
        try:
            await self.run_internal(project)
        except Exception as ex:
            self._log_message(sys.stderr, "Runner %s failed:" % type(self))
            self._log_message(sys.stderr, traceback.format_exc())
            self.status = JobStepStatus.FAILED

        if self.status == JobStepStatus.STARTED:
            self.status = JobStepStatus.SUCCEEDED

    async def _run_process(self, args):
        self._log_message(sys.stdout, "Running command: %s\n" % str.join(" ", args))
        process = await asyncio.create_subprocess_exec(args[0], *args[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        await asyncio.wait([self._log_stream(sys.stdout, process.stdout),
                            self._log_stream(sys.stderr, process.stderr),
                            process.wait()])

        if process.returncode == 0:
            self.status = JobStepStatus.SUCCEEDED
        else:
            self.status = JobStepStatus.FAILED