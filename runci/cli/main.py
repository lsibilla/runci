import asyncio
import click
import logging
import os
import sys

from runci.dal.yaml import load_config
from runci.entities.parameters import Parameters
from runci.engine import core, runner
from runci.engine.job import JobStatus

DEFAULT_CONFIG_FILE = "runci.yml"


@click.command()
@click.option('-f', '--file', 'file', type=click.File('r', lazy=True), default=DEFAULT_CONFIG_FILE)
@click.argument('targets', nargs=-1)
def main(targets, file):
    if hasattr(file, 'name') \
       and isinstance(file.name, str) \
       and os.path.isfile(file.name):
        # If filename available and file exists, load file to allow docker-compose integration
        parameters = Parameters(file.name, targets, 1)
    else:
        parameters = Parameters(file, targets, 1)
    project = load_config(parameters)

    logging.debug("Building the following targets: %s" % str.join(" ", targets))
    unknown_targets = [t for t in targets if t not in [t.name for t in project.targets]]
    if any(unknown_targets):
        print("Unkown targets: %s" % str.join(" ", unknown_targets), file=sys.stderr)
        exit(1)

    runner.import_runners()
    result = asyncio.run(run_project(project))

    if result == JobStatus.SUCCEEDED:
        print("Pipeline has run succesfully.")
        exit(0)
    elif result == JobStatus.FAILED:
        print("Pipeline has failed.", file=sys.stderr)
        exit(1)
    elif result == JobStatus.CANCELED:
        print("Pipeline has been canceled.", file=sys.stderr)
        exit(2)
    else:
        print("Pipeline has been run but outcome is undetermined. Please report this as a bug.", file=sys.stderr)
        exit(3)


async def run_project(project):
    tree = core.DependencyTree(project)
    task = tree.start()

    is_running = True
    while is_running:
        is_running = not task.done()

        working_nodes = [node for node in tree.get_nodes() if node.job.has_new_messages()]
        if any(working_nodes):
            for node in working_nodes:
                while node.job.has_new_messages() or node.job.status == JobStatus.STARTED:
                    node.job.release_new_messages()
                    await asyncio.sleep(0.1)
        else:
            await asyncio.sleep(0.1)

    await task
    return tree.status
