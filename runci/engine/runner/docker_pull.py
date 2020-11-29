import asyncio

from .base import RunnerBase
from runci.entities.context import Context


class DockerPullRunner(RunnerBase):
    _selector = 'docker-pull'

    async def run_internal(self, context: Context):
        images = self.spec.get("image",
                               self.spec.get("_", None))

        if images is None:
            raise Exception("Image name should be specified for docker-pull step")

        base_args = ['docker', 'pull']

        tasks = []
        for image in images.split(' '):
            args = list(base_args)
            args.append(image)
            tasks.append(asyncio.create_task(self._run_process(args)))

        await asyncio.wait(tasks)
