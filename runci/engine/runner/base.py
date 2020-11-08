import asyncio
from abc import abstractmethod
import subprocess
import sys
import traceback
from typing import Callable

from runci.entities.config import Project
from . import RunnerStatus


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


class RunnerBase():
    spec: dict
    _status: RunnerStatus
    _message_logger: asyncio.Queue

    def __init__(self, message_logger: Callable, spec: dict):
        self.spec = spec
        self._status = RunnerStatus.CREATED
        self._message_logger = message_logger

    def _log_message(self, output_stream, message):
        if message != []:
            self._message_logger(output_stream, message)

    async def _log_stream(self, output_stream, input_stream: asyncio.StreamReader):
        if output_stream not in [sys.stdout, sys.stderr]:
            raise Exception("output_stream should be stdout or stderr")
        while not input_stream.at_eof():
            self._log_message(output_stream, await input_stream.readline())

    @abstractmethod
    async def run_internal(self, project: Project):
        pass

    async def run(self, project: Project):
        self._status = RunnerStatus.STARTED
        self._log_message(sys.stdout, "Starting %s runner\n" % type(self).__name__)
        try:
            await self.run_internal(project)
        except Exception:
            self._log_message(sys.stderr, "Runner %s failed:" % type(self).__name__)
            self._log_message(sys.stderr, traceback.format_exc())
            self._status = RunnerStatus.FAILED

        if self._status == RunnerStatus.STARTED:
            self._status = RunnerStatus.SUCCEEDED

    async def _run_process(self, args):
        self._log_message(sys.stdout, "Running command: %s\n" % str.join(" ", args))
        process = await asyncio.create_subprocess_exec(args[0], *args[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        await asyncio.wait([asyncio.create_task(coro)
                            for coro in [self._log_stream(sys.stdout, process.stdout),
                                         self._log_stream(sys.stderr, process.stderr),
                                         process.wait()]])

        if process.returncode == 0:
            self._status = RunnerStatus.SUCCEEDED
        else:
            self._status = RunnerStatus.FAILED

    @property
    def is_succeeded(self):
        return self._status == RunnerStatus.SUCCEEDED
