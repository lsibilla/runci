import random
import string
import sys

from .base import RunnerBase
from runci.entities.context import Context


class ComposeRunRunner(RunnerBase):
    _selector = 'compose-run'

    async def run_internal(self, context: Context):
        files = self._step.spec.get('file', 'docker-compose.yml ' + context.parameters.dataconnection).split(' ')
        service_list = self._step.spec.get('services', None)
        project_name = self._step.spec.get('projectName', None)
        build = self._step.spec.get('build', True)

        if (project_name is None):
            # Generate a random string
            project_name = ''.join(random.choice(string.ascii_lowercase) for i in range(8))

        dc_args = ['docker-compose']
        for file in files:
            dc_args.extend(['-f', file])

        dc_args.extend(['-p', project_name])

        if build:
            self._log_runner_message(sys.stdout, "Ensuring images are built")

            build_args = list(dc_args)
            build_args.extend(['build', '-q'])

            await self._run_process(build_args)

        run_args = list(dc_args)
        run_args.extend(['run', '--rm'])

        if service_list is not None:
            run_args.extend(service_list.split(' '))

        await self._run_process(run_args)

        down_args = list(dc_args)
        down_args.extend(['down'])

        await self._run_process(down_args)
