from click.testing import CliRunner
import unittest

from runci.cli.main import main
from runci.entities.config import Project, Target, Step
from runci.entities.parameters import Parameters

test_project = Project(services=[],
                       targets=[Target(name="build_succeed",
                                       dependencies=[],
                                       steps=[]),
                                Target(name="build_fail",
                                       dependencies=[],
                                       steps=[Step("fail", "compose-build", {"services": "non-exist"})]),
                                Target(name="wrong_step_type",
                                       dependencies=[],
                                       steps=[Step("wrong_step", "wrong_type", {})])
                                ])

test_parameters = Parameters(dataconnection="runci.yml",
                             targets=["target"],
                             verbosity=0)
test_project_yaml = """
version: "2.4"
targets:
    build_succeed:
    build_fail:
        steps:
            - name: fail
              compose-build:
                services: non-exist
    wrong_step_type:
        steps:
            - name: wrong step stype
              wrong_type:
"""


class test_cli(unittest.TestCase):
    def test_wrong_target(self):
        runner = CliRunner(mix_stderr=False)
        with runner.isolated_filesystem():
            with open("runci.yml", 'w') as f:
                f.write(test_project_yaml)

            result = runner.invoke(main, ['wrong_target'])

            self.assertEqual(result.exit_code, 1)

    def test_succeed(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("runci.yml", 'w') as f:
                f.write(test_project_yaml)

            result = runner.invoke(main, ['build_succeed'])

            self.assertEqual(result.exit_code, 0)

    def test_failed_step(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("runci.yml", 'w') as f:
                f.write(test_project_yaml)

            result = runner.invoke(main, ['build_fail'])

            self.assertEqual(result.exit_code, 1)

    def test_wrong_step_type(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("runci.yml", 'w') as f:
                f.write(test_project_yaml)

            result = runner.invoke(main, ['wrong_step_type'])

            self.assertEqual(result.exit_code, 1)


if __name__ == '__main__':
    unittest.main()
