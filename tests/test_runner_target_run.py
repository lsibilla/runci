import unittest
from runci.entities.config import Project, Target, Step
from runci.entities.parameters import Parameters
from runci.engine.core import create_context, DependencyTree
from unittest.mock import patch


class test_runner_docker_build(unittest.TestCase):
    step = Step("test", "target-run", {
        "target": "test"
    })

    project = Project(
        services=[],
        targets=[Target(
            name="target",
            dependencies=[],
            steps=[step]
        )])
    parameters = Parameters(dataconnection="runci.yml", targets=["target"], verbosity=0)

    @patch('runci.engine.runner.target_run.TargetRunRunner.run')
    def test_integration(self, mock):
        context = create_context(self.project, self.parameters)
        DependencyTree(context).run()
        mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
