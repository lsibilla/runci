from .base import RunnerBase
from runci.entities.context import Context


class DockerBuildRunner(RunnerBase):
    _selector = 'docker-build'

    async def run_internal(self, context: Context):
        dockerfile = self._step.spec.get('dockerfile', None)
        context = self._step.spec.get('context', '.')
        tags = self._step.spec.get('tags', None)

        args = ['docker', 'build']
        if dockerfile is not None:
            args.extend(['-f', dockerfile])

        if tags is not None:
            for tag in tags.split(' '):
                args.extend(['-t', tag])

        args.append(context)

        await self._run_process(args)
