import importlib.util
import json
import pathlib
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('teardown', pathlib.Path(__file__).parents[1] / 'lab-teardown.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TeardownScopeTest(unittest.TestCase):
    def test_quiet_success_response_is_an_empty_object(self):
        with patch.object(module, 'run', return_value=''):
            self.assertEqual({}, module.aws('s3api', 'delete-objects'))

    def test_backend_finalization_refuses_remaining_project_cluster(self):
        with patch.object(module, 'aws', return_value={'clusters': ['oficina']}):
            with self.assertRaises(AssertionError):
                module.verify_absent_without_state()

    def test_inventory_rejects_unknown_resources(self):
        state = {'resources': [{'mode': 'managed', 'type': 'aws_vpc', 'name': 'unrelated'}]}
        with patch.object(module, 'run', return_value=json.dumps(state)):
            with self.assertRaisesRegex(AssertionError, 'Unexpected state address'):
                module.inventory()

    def test_inventory_rejects_child_modules(self):
        state = {'resources': [{'mode': 'managed', 'module': 'module.unrelated'}]}
        with patch.object(module, 'run', return_value=json.dumps(state)):
            with self.assertRaisesRegex(AssertionError, 'Unexpected module scope'):
                module.inventory()

    def test_inventory_does_not_treat_access_denied_as_missing_production(self):
        denied = subprocess.CompletedProcess([], 1, '', 'AccessDenied (403)')
        with patch.object(module, 'run', return_value='{}'), patch.object(module.subprocess, 'run', return_value=denied):
            with self.assertRaisesRegex(AssertionError, 'Cannot establish absence'):
                module.inventory()

    def test_inventory_accepts_explicit_missing_production(self):
        missing = subprocess.CompletedProcess([], 1, '', 'Not Found (404)')
        with patch.object(module, 'run', return_value='{}'), patch.object(module.subprocess, 'run', return_value=missing):
            self.assertEqual(3, len(module.inventory()))

    def test_plan_rejects_creation_or_update(self):
        folder = pathlib.Path('/tmp/scoped-test')
        for actions in [['create'], ['update'], ['delete', 'create']]:
            data = {'resource_changes': [{'change': {'actions': actions}}]}
            with patch.object(module, 'run', side_effect=['', json.dumps(data)]):
                with self.assertRaises(AssertionError):
                    module.plan(folder)


if __name__ == '__main__':
    unittest.main()
