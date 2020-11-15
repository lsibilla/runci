from runci.engine import runner
from .base import RunnerBase
from runci.entities.context import Context


class ComposeBuildRunner(RunnerBase):
    async def run_internal(self, context: Context):
        files = self.spec.get('file', context.parameters.dataconnection).split(' ')
        service_list = self.spec.get('services', None)

        args = ['docker-compose']
        for file in files:
            args.extend(['-f', file])
        args.append('build')

        if service_list is not None:
            args.extend(service_list.split(' '))

        await self._run_process(args)


runner.register_runner('compose-build', ComposeBuildRunner)
