from .base import RunnerBase
from runci.entities.context import Context


class ComposeRunRunner(RunnerBase):
    _selector = 'compose-run'

    async def run_internal(self, context: Context):
        files = self.spec.get('file', context.parameters.dataconnection).split(' ')
        service_list = self.spec.get('services', None)
        project_name = self.spec.get('projectName', None)

        dc_args = ['docker-compose']
        for file in files:
            dc_args.extend(['-f', file])

        if project_name is not None:
            dc_args.extend(['-p', project_name])

        run_args = list(dc_args)
        run_args.extend(['run', '--rm'])

        if service_list is not None:
            run_args.extend(service_list.split(' '))

        await self._run_process(run_args)

        down_args = list(dc_args)
        down_args.extend(['down'])

        await self._run_process(down_args)
