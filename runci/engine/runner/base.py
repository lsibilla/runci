from abc import abstractmethod
import asyncio
import os
import sys
import traceback
from typing import Callable

from runci.entities.context import Context
from runci.entities import event
from . import RunnerStatus


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


class RunnerSubprocessProtocol(asyncio.SubprocessProtocol):
    _streams = [sys.stdout, sys.stderr]

    def __init__(self, message_logger, exit_future):
        self._message_logger = message_logger
        self._exit_future = exit_future

    def pipe_data_received(self, fd, data):
        self._message_logger(self._streams[fd-1], data)

    def process_exited(self):
        self._exit_future.set_result(True)


class RunnerBase():
    spec: dict
    _status: RunnerStatus
    _event_logger: Callable
    _selector = None

    def __init__(self, event_logger: Callable, spec: dict):
        self.spec = spec
        self._status = RunnerStatus.CREATED
        self._event_logger = event_logger

    @classmethod
    def get_selector(cls):
        return cls._selector

    def _log_event(self, job_event):
        self._event_logger(job_event)

    def _log_message(self, output_stream, message):
        if message != []:
            self._log_event(event.JobMessageEvent(output_stream, message))

    def _log_runner_message(self, output_stream, message):
        self._log_message(output_stream, message + os.linesep)

    async def _log_stream(self, output_stream, input_stream: asyncio.StreamReader):
        if output_stream not in [sys.stdout, sys.stderr]:
            raise Exception("output_stream should be stdout or stderr")
        while not input_stream.at_eof():
            message = await input_stream.readline()
            self._log_message(output_stream, message)

    @abstractmethod
    async def run_internal(self, context: Context):
        pass

    async def run(self, context: Context):
        self._status = RunnerStatus.STARTED
        self._log_runner_message(sys.stdout, "Starting %s runner" % type(self).__name__)
        try:
            await self.run_internal(context)
        except Exception:
            self._log_runner_message(sys.stderr, "Runner %s failed:" % type(self).__name__)
            self._log_runner_message(sys.stderr, traceback.format_exc())
            self._status = RunnerStatus.FAILED

        if self._status == RunnerStatus.STARTED:
            self._status = RunnerStatus.SUCCEEDED

    async def _run_process(self, args):
        self._log_runner_message(sys.stdout, "Running command: %s" % str.join(" ", args))
        loop = asyncio.get_event_loop()
        exit_future = asyncio.Future(loop=loop)

        transport, protocol = await loop.subprocess_exec(
            lambda: RunnerSubprocessProtocol(self._log_message, exit_future),
            args[0], *args[1:],
            stdin=None)

        await exit_future
        return_code = transport.get_returncode()
        transport.close()

        if return_code != 0:
            self._status = RunnerStatus.FAILED

        return return_code

    @property
    def is_succeeded(self):
        return self._status == RunnerStatus.SUCCEEDED
