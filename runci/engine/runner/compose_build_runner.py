from .base import RunnerBase
from io import TextIOBase
from runci.entities.config import Project
from runci.entities.parameters import Parameters
import threading

class ComposeBuildRunner(RunnerBase):
    async def run_internal(self, project:Project):
        files = self.spec.get('file', project.parameters.dataconnection).split(' ')
        service_list = self.spec.get('services', None)

        args = ['docker-compose']
        for file in files:
            args.extend(['-f', file])
        args.append('build')

        if service_list != None:
            args.extend(service_list.split(' '))
            
        await self._run_process(args)
