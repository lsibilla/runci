from .base import RunnerBase
from runci.entities.context import Context


class ComposeRunRunner(RunnerBase):
    _selector = 'compose-run'

    async def run_internal(self, context: Context):
        files = self.spec.get('file', context.parameters.dataconnection).split(' ')
        service_list = self.spec.get('services', None)
        project_name = self.spec.get('projectName', None)

        args = ['docker-compose']
        for file in files:
            args.extend(['-f', file])

        if project_name is not None:
            args.extend(['-p', project_name])

        args.extend(['run', '--rm'])

        if service_list is not None:
            args.extend(service_list.split(' '))

        await self._run_process(args)
