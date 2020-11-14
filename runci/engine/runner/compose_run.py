from runci.engine import runner
from .base import RunnerBase
from runci.entities.config import Project


class ComposeRunRunner(RunnerBase):
    async def run_internal(self, project: Project):
        files = self.spec.get('file', project.parameters.dataconnection).split(' ')
        service_list = self.spec.get('services', None)
        project_name = self.spec.get('projectName', None)

        args = ['docker-compose']
        for file in files:
            args.extend(['-f', file])
        args.extend(['run', '--rm'])

        if project_name is not None:
            args.extend(['-p', project_name])

        if service_list is not None:
            args.extend(service_list.split(' '))

        await self._run_process(args)


runner.register_runner('compose-run', ComposeRunRunner)
