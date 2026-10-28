"""Check standalone HTTP boundaries without a browser or library access."""
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from http.server import ThreadingHTTPServer

from extractor import server


class StandaloneApiTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'BRIDGE_API_TOKEN': 't' * 64})
        self.env.start()
        self.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()
        self.env.stop()

    def request(self, path, token='t' * 64, body=None):
        request = urllib.request.Request(
            f'http://127.0.0.1:{self.http.server_port}{path}',
            data=json.dumps(body).encode() if body is not None else None,
            headers={'X-Bridge-Key': token, 'Content-Type': 'application/json'})
        return urllib.request.urlopen(request, timeout=2)

    def test_legacy_scan_is_absent(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/v1/scan', body={'jobs': []})
        self.assertEqual(error.exception.code, 404)
        self.assertFalse(hasattr(server, 'BazarrClient'))
        self.assertFalse(hasattr(server, 'enqueue'))

    def test_status_requires_auth_and_only_reports_disney(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/v1/status', token='wrong')
        self.assertEqual(error.exception.code, 401)
        with self.request('/v1/status') as response:
            self.assertEqual(set(json.load(response)['providers']), {'disney'})

    def test_login_dispatches_to_browser_without_external_credentials(self):
        with patch.object(server, 'start_session', return_value={'started': True}) as start:
            with self.request('/v1/login', body={'provider': 'disney'}) as response:
                self.assertEqual(response.status, 202)
            start.assert_called_once_with('disney')
