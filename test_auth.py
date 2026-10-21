"""Authentication checks with a stubbed data layer; no live database required."""
import base64
import importlib.util
import os
from pathlib import Path
import types
import unittest
from unittest.mock import patch
from demo_store import CarDao, CustomerDAO


class AuthenticationTests(unittest.TestCase):
    def test_api_requires_auth_outside_demo_mode(self):
        spec = importlib.util.spec_from_file_location('auth_test_app', Path(__file__).with_name('CarServer.py'))
        module = importlib.util.module_from_spec(spec)
        stubs = {'CarDao': types.SimpleNamespace(CarDao=CarDao),
                 'CustomerDao': types.SimpleNamespace(CustomerDAO=CustomerDAO)}
        with patch.dict(os.environ, DEMO_MODE='0', DEMO_USERNAME='test-user', DEMO_PASSWORD='test-only'):
            with patch.dict('sys.modules', stubs):
                spec.loader.exec_module(module)
        client = module.app.test_client()
        self.assertEqual(client.get('/cars').status_code, 401)
        self.assertEqual(client.get('/customer').status_code, 401)
        self.assertEqual(client.get('/api/reservations').status_code, 401)
        self.assertEqual(client.post('/api/reservations',json={}).status_code, 401)
        credential = base64.b64encode(b'test-user:test-only').decode()
        self.assertEqual(client.get('/cars', headers={'Authorization': 'Basic ' + credential}).status_code, 200)


if __name__ == '__main__':
    unittest.main()
