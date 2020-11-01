import click
import logging
from runci.dal.yaml import load_config
from runci.entities.parameters import Parameters
from runci.engine import core
from runci.engine.job import JobStatus
import asyncio

DEFAULT_CONFIG_FILE = "runci.yml"


@click.command()
@click.option('-f', '--file', 'file', type=click.File('r', lazy=True), default=DEFAULT_CONFIG_FILE)
@click.argument('targets', nargs=-1)
def main(targets, file):
    parameters = Parameters(file.name, targets, 1)
    project = load_config(parameters)

    logging.debug("Building the following targets: %s" % str.join(" ", targets))
    unknown_targets = [t for t in targets if t not in [t.name for t in project.targets]]
    if any(unknown_targets):
        logging.error("Unkown targets: %s" % str.join(" ", unknown_targets))
        return 1

    asyncio.run(run_project(project))


async def run_project(project):
    tree = core.DependencyTree(project)
    task = tree.start()

    is_running = True
    while is_running:
        is_running = not task.done()

        working_nodes = [node for node in tree.get_nodes() if node.job.has_new_messages()]
        if any(working_nodes):
            for node in working_nodes:
                while node.job.status == JobStatus.STARTED:
                    node.job.release_new_messages()
                    await asyncio.sleep(0.1)
        else:
            await asyncio.sleep(0.1)

    return await task
