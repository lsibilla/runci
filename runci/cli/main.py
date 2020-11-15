import asyncio
import click
import os
import sys

from runci.dal.yaml import load_project
from runci.entities.parameters import Parameters
from runci.engine import core, runner
from runci.engine.job import JobStatus

DEFAULT_CONFIG_FILE = "runci.yml"


@click.command()
@click.option('-f', '--file', 'file', type=click.File('r', lazy=True), default=DEFAULT_CONFIG_FILE)
@click.argument('targets', nargs=-1)
def main(targets, file):
    if len(targets) == 0:
        targets = ["default"]

    if hasattr(file, 'name') \
       and isinstance(file.name, str) \
       and os.path.isfile(file.name):
        # If filename available and file exists, load file to allow docker-compose integration
        parameters = Parameters(file.name, targets, 1)
    else:
        parameters = Parameters(file, targets, 1)
    project = load_project(parameters)
    context = core.create_context(project, parameters)

    print("Running RunCI pipeline for the following target(s): %s" % str.join(" ", targets))
    unknown_targets = [t for t in targets if t not in [t.name for t in project.targets]]
    if any(unknown_targets):
        print("Unkown targets: %s" % str.join(" ", unknown_targets), file=sys.stderr)
        exit(1)

    runner.import_runners()
    result = asyncio.run(run_project(context))

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


async def run_project(context):
    tree = context.dependencyTree
    task = tree.start()

    is_running = True
    while is_running:
        is_running = not task.done()

        working_nodes = [node for node in tree.get_nodes() if node.job.has_new_events()]
        if any(working_nodes):
            for node in working_nodes:
                while node.job.has_new_events() or node.job.status == JobStatus.STARTED:
                    await node.job.release_all_events()
        else:
            # Looks like no job has been started yet. Wait a moment.
            await asyncio.sleep(0.1)

    await task
    return tree.status
