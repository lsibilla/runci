from runci.engine import runner
from .base import RunnerBase
from runci.entities.config import Project


class DockerBuildRunner(RunnerBase):
    async def run_internal(self, project: Project):
        dockerfile = self.spec.get('dockerfile', None)
        context = self.spec.get('context', '.')
        tags = self.spec.get('tags', None).split(' ')

        args = ['docker', 'build']
        if dockerfile is not None:
            args.extend(['-f', dockerfile])

        for tag in tags:
            args.extend(['-t', tag])

        args.append(context)

        await self._run_process(args)


runner.register_runner('docker-build', DockerBuildRunner)
