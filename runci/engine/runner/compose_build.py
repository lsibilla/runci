from .base import RunnerBase
from runci.entities.context import Context


class ComposeBuildRunner(RunnerBase):
    _selector = 'compose-build'

    async def run_internal(self, context: Context):
        files = self._step.spec.get('file', context.parameters.dataconnection).split(' ')
        service_list = self._step.spec.get('services', None)
        project_name = self._step.spec.get('projectName', None)

        args = ['docker-compose']
        for file in files:
            args.extend(['-f', file])

        if project_name is not None:
            args.extend(['-p', project_name])

        args.append('build')

        if service_list is not None:
            args.extend(service_list.split(' '))

        await self._run_process(args)
