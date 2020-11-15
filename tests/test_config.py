import unittest
import os

from runci.dal.yaml import load_project


script_path = os.path.dirname(__file__)
sample_config_path = "%s%s%s" % (script_path, os.sep, "runci.yml")


class test_config(unittest.TestCase):
    def test_target_list(self):
        config = load_project(sample_config_path)
        self.assertListEqual([t.name for t in config.targets], ['default', 'build', 'utests', 'utest-a', 'utest-b'])

    def test_dependencies(self):
        config = load_project(sample_config_path)
        dependencies_list = [t.dependencies for t in config.targets if t.name == 'default'][0]
        dependencies_string = [t.dependencies for t in config.targets if t.name == 'utests'][0]

        self.assertListEqual(dependencies_list, ['build', 'utests', 'itests', 'etests', 'stests'])
        self.assertListEqual(dependencies_string, ['utest-a', 'utest-b'])

    def test_steps(self):
        config = load_project(sample_config_path)
        steps = [t.steps for t in config.targets if t.name == 'utest-a'][0]
        steps_name = [s.name for s in steps]
        steps_type = [s.type for s in steps]

        self.assertListEqual(steps_name, ['Gate step', 'Step 1', 'Step 2', 'Gate step'])
        self.assertListEqual(steps_type, ['compose-build', 'compose-run', 'compose-start', 'compose-build'])

    def test_step_spec_is_not_none(self):
        config = load_project(sample_config_path)
        steps = [t.steps for t in config.targets if t.name == 'utest-a'][0]
        steps_spec = [s.spec for s in steps]

        self.assertNotIn(None, steps_spec)


if __name__ == '__main__':
    unittest.main()
