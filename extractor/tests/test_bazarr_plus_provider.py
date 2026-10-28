"""Offline Bazarr+ adapter and private SRT cache regression tests."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import tempfile
import sys
from unittest.mock import MagicMock
import unittest
from unittest.mock import patch

from extractor import provider_bridge, server

MODULE = Path(__file__).resolve().parents[2] / "provider" / "provider.py"
spec = importlib.util.spec_from_file_location("moonfin_bazarrplus_provider", MODULE)
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)

SERIES_URL = "https://www.disneyplus.com/es-419/browse/entity-571475d5-8b1a-453f-a57f-26bb4dd13304"
TVDB = 123456
RULES = "17x1-13=1x1\n17x14-26=2x1\n17x27-40=3x1\n17x41-50=4x1"
VIDEO = {"kind": "episode", "series": "Bleach",
         "series_tvdb_id": TVDB, "season": 17, "episode": 3}
LANGUAGE = {"alpha3": "spa", "alpha2": "es", "hi": False, "forced": False}
TOKEN = "x" * 64
CONFIG = {
    "agent_url": "http://moonfin-streaming-agent:8787",
    "bridge_token": TOKEN,
    "series_json": json.dumps([{"tvdb_id": TVDB, "series_url": SERIES_URL, "mapping": RULES}]),
    "enable_requests": False,
}
SRT = b"1\n00:00:01,000 --> 00:00:02,000\nHola!\n"


class ProviderTests(unittest.TestCase):
    def test_provider_hub_manifest_hashes(self):
        manifest = json.loads((MODULE.parent / "provider.json").read_text(encoding="utf-8"))
        contents = MODULE.read_bytes()
        self.assertEqual(manifest["api_version"], "bazarr.provider-hub.v1")
        self.assertEqual(manifest["files"]["provider.py"], hashlib.sha256(contents).hexdigest())
        canonical = b"provider.py\0" + str(len(contents)).encode("ascii") + b"\0" + contents + b"\0"
        self.assertEqual(manifest["bundle_sha256"], hashlib.sha256(canonical).hexdigest())
        self.assertIn("bridge_token", manifest["secret_fields"])
        self.assertFalse(manifest["config_schema"]["properties"]["enable_requests"]["default"])

    def test_mapper_strict_and_cours(self):
        self.assertEqual(provider.map_episode(RULES, 17, 3), (1, 3))
        self.assertEqual(provider.map_episode(RULES, 17, 14), (2, 1))
        self.assertEqual(provider.map_episode(RULES, 17, 41), (4, 1))
        self.assertIsNone(provider.map_episode(RULES, 16, 1))
        self.assertEqual(provider.map_episode("", 17, 3), (17, 3))
        with self.assertRaises(ValueError):
            provider.parse_mapping("17x1-3=1x1\n17x3-5=2x1")
        with self.assertRaises(ValueError):
            provider.parse_mapping("17x1=1x1\n17x2=1x1")

    def test_rejects_other_series_and_languages_without_network(self):
        candidate = provider.MoonfinBridgeProvider()
        with patch.object(candidate, "_post", side_effect=AssertionError("unexpected call")):
            self.assertEqual(candidate.search({**VIDEO, "series_tvdb_id": 88}, [LANGUAGE], CONFIG), [])
            self.assertEqual(candidate.search(VIDEO, [{**LANGUAGE, "forced": True}], CONFIG), [])
            self.assertEqual(candidate.search(VIDEO, [{**LANGUAGE, "hi": True}], CONFIG), [])
            self.assertEqual(candidate.search(VIDEO, [{"alpha3": "eng"}], CONFIG), [])

    def test_opt_in_off_and_no_false_positive_while_queued(self):
        candidate = provider.MoonfinBridgeProvider()
        calls = []
        def mock_post(path, data, config):
            calls.append((path, data))
            return b'{"state":"queued"}'
        with patch.object(candidate, "_post", side_effect=mock_post):
            self.assertEqual(candidate.search(VIDEO, [LANGUAGE], CONFIG), [])
        self.assertEqual(calls[0][0], "/v1/provider/lookup")
        self.assertFalse(calls[0][1]["enqueue"])
        self.assertEqual((calls[0][1]["streaming_season"], calls[0][1]["streaming_episode"]), (1, 3))
        self.assertNotIn("bridge_token", calls[0][1])

    def test_ready_then_download_integrity(self):
        candidate = provider.MoonfinBridgeProvider()
        ident = "a" * 64
        sha = hashlib.sha256(SRT).hexdigest()
        with patch.object(candidate, "_post", return_value=json.dumps(
            {"state": "ready", "id": ident, "sha256": sha}).encode("utf-8")):
            found = candidate.search(VIDEO, [LANGUAGE], CONFIG)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["provider"], "moonfinbridge")
        self.assertEqual(found[0]["matches"], ["series", "season", "episode", "tvdb_id"])
        self.assertNotIn(TOKEN, json.dumps(found))
        payload = found[0]["provider_payload"]
        with patch.object(candidate, "_post", return_value=SRT):
            downloaded = candidate.download(payload, LANGUAGE, CONFIG)
        self.assertEqual(base64.b64decode(downloaded["content_b64"]), SRT)
        self.assertEqual(downloaded["content_sha256"], sha)
        with patch.object(candidate, "_post", return_value=SRT+b"!"):
            with self.assertRaises(ValueError):
                candidate.download(payload, LANGUAGE, CONFIG)
        with self.assertRaises(ValueError):
            candidate.download({**payload, "id": "../secret"}, LANGUAGE, CONFIG)

    def test_bad_url_or_duplicate_mapping_rejected(self):
        cfg = dict(CONFIG)
        cfg["series_json"] = json.dumps([{"tvdb_id": TVDB,
                                         "series_url": "http://127.0.0.1/internal",
                                         "mapping": RULES}])
        with self.assertRaises(ValueError):
            provider._series_config(VIDEO, cfg)

    def test_search_waits_once_and_polls_without_enqueue(self):
        candidate = provider.MoonfinBridgeProvider()
        ready = {"state": "ready", "id": "a" * 64, "sha256": hashlib.sha256(SRT).hexdigest()}
        replies = iter([{"state": "queued"}, {"state": "absent"}, ready])
        calls = []
        now = [0.0]
        def post(path, body, config):
            calls.append(dict(body))
            now[0] += 1
            return json.dumps(next(replies)).encode()
        with patch.object(candidate, "_post", side_effect=post), \
                patch.object(provider.time, "monotonic", side_effect=lambda: now[0]), \
                patch.object(provider.time, "sleep", side_effect=lambda s: now.__setitem__(0, now[0]+s)):
            results = candidate.search(VIDEO, [LANGUAGE], dict(CONFIG, enable_requests=True))
        self.assertEqual(len(results), 1)
        self.assertEqual([x["enqueue"] for x in calls], [True, False, False])
        self.assertTrue(all(x["streaming_episode"] == 3 for x in calls))

    def test_wait_deadline_preserves_pending_job_and_reserves_http_timeout(self):
        candidate = provider.MoonfinBridgeProvider()
        now = [0.0]
        calls = []
        def post(path, body, config):
            calls.append(dict(body))
            now[0] += provider._HTTP_TIMEOUT
            return json.dumps({"state": "pending" if body["enqueue"] else "absent"}).encode()
        with patch.object(candidate, "_post", side_effect=post), \
                patch.object(provider.time, "monotonic", side_effect=lambda: now[0]), \
                patch.object(provider.time, "sleep", side_effect=lambda s: now.__setitem__(0, now[0]+s)):
            self.assertEqual(candidate.search(VIDEO, [LANGUAGE], dict(CONFIG, enable_requests=True, wait_seconds=30)), [])
        self.assertEqual([x["enqueue"] for x in calls], [True, False])
        self.assertLessEqual(now[0], 30)

    def test_cache_only_busy_and_zero_wait_never_poll(self):
        for enabled, state, wait in [(False, "pending", 75), (True, "busy", 75),
                                     (True, "queued", 0), (True, "absent", 75),
                                     (True, "failed", 75), (True, "cooldown", 75),
                                     (True, "interrupted", 75)]:
            with self.subTest(enabled=enabled, state=state, wait=wait):
                candidate = provider.MoonfinBridgeProvider()
                with patch.object(candidate, "_post", return_value=json.dumps({"state": state}).encode()) as post, \
                        patch.object(provider.time, "sleep", side_effect=AssertionError("must not wait")):
                    self.assertEqual(candidate.search(VIDEO, [LANGUAGE], dict(CONFIG, enable_requests=enabled, wait_seconds=wait)), [])
                self.assertEqual(post.call_count, 1)

    def test_poll_stops_on_failure_without_reenqueue(self):
        for state in ('failed', 'interrupted', 'cooldown'):
            candidate = provider.MoonfinBridgeProvider()
            with patch.object(candidate, '_post', side_effect=[
                    b'{"state":"processing"}', json.dumps({'state': state}).encode()]) as post, \
                    patch.object(provider.time, 'sleep'):
                self.assertEqual(candidate.search(VIDEO, [LANGUAGE], dict(CONFIG, enable_requests=True)), [])
                self.assertEqual(post.call_count, 2)
                self.assertFalse(post.call_args.args[1]['enqueue'])

    def test_wait_validation_before_network_and_unknown_state_rejected(self):
        candidate = provider.MoonfinBridgeProvider()
        for value in (-1, 91, True, "75", 1.5):
            with self.subTest(value=value), patch.object(candidate, "_post") as post:
                with self.assertRaises(ValueError):
                    candidate.search(VIDEO, [LANGUAGE], dict(CONFIG, wait_seconds=value))
                post.assert_not_called()
        with patch.object(candidate, "_post", return_value=b'{"state":"unexpected"}'):
            with self.assertRaises(ValueError):
                candidate.search(VIDEO, [LANGUAGE], CONFIG)

    def test_duplicate_series_mapping_rejected(self):
        cfg = dict(CONFIG)
        cfg["series_json"] = json.dumps([
            {"tvdb_id": TVDB, "series_url": SERIES_URL, "mapping": RULES},
            {"tvdb_id": TVDB, "series_url": SERIES_URL, "mapping": RULES}])
        with self.assertRaises(ValueError):
            provider._series_config(VIDEO, cfg)


class AgentCacheTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.state = patch.dict(os.environ, {
            "STATE_FILE": str(Path(self.dir.name) / "state" / "attempts.json")})
        self.state.start()
        # server.PERSIST is resolved at import time; isolate it from /data.
        self.persist_patch = patch.object(server, "PERSIST",
            Path(self.dir.name) / "state" / "attempts.json")
        self.persist_patch.start()
        self.queue = queue.Queue(maxsize=30)
        self.saved_queue = server.QUEUE
        self.saved_last = dict(server.LAST_RUN)
        server.QUEUE = self.queue
        server.LAST_RUN.clear()

    def tearDown(self):
        server.QUEUE = self.saved_queue
        server.LAST_RUN.clear()
        server.LAST_RUN.update(self.saved_last)
        self.persist_patch.stop()
        self.state.stop()
        self.dir.cleanup()

    def request(self, enqueue=False):
        return {
            "tvdb_id": TVDB, "season": 17, "episode": 3,
            "streaming_season": 1, "streaming_episode": 3,
            "language": "es", "series_url": SERIES_URL, "enqueue": enqueue
        }

    def test_no_enqueue_by_default_and_exact_ready_cache(self):
        self.assertEqual(server.provider_lookup(self.request())["state"], "absent")
        self.assertTrue(self.queue.empty())
        response = server.provider_lookup(self.request(enqueue=True))
        self.assertEqual(response["state"], "queued")
        self.assertEqual(self.queue.qsize(), 1)
        job = self.queue.get_nowait()
        self.assertEqual(job["delivery"], "bazarr_plus")
        self.assertEqual(job["tvdb_id"], TVDB)
        provider_bridge.save_cached(job, SRT)
        ready = server.provider_lookup(self.request())
        self.assertEqual(ready["state"], "ready")
        self.assertEqual(ready["sha256"], hashlib.sha256(SRT).hexdigest())
        self.assertEqual(provider_bridge.get_cached(ready["id"]), SRT)
        self.assertEqual(server.provider_lookup({**self.request(), "episode": 4})["state"], "absent")
        # Different Disney+ mapping or title must not reuse the old SRT.
        self.assertEqual(server.provider_lookup({
            **self.request(), "streaming_episode": 4
        })["state"], "absent")

    def test_cooldown_cannot_create_duplicate_jobs(self):
        self.assertEqual(server.provider_lookup(self.request(enqueue=True))["state"], "queued")
        self.assertEqual(server.provider_lookup(self.request(enqueue=True))["state"], "queued")
        self.assertEqual(self.queue.qsize(), 1)

    def test_failed_job_persists_and_retry_requires_opt_in_after_cooldown(self):
        with patch.object(server.time, "time", return_value=100000):
            server.provider_lookup(self.request(enqueue=True))
            job = self.queue.get_nowait()
            with patch.object(server, "BROWSER_LOCK") as browser:
                browser.acquire.return_value = False
                server.process_job(job)
            failed = server.provider_lookup(self.request())
            self.assertEqual(failed, {"state": "failed", "retry_after_seconds": 86400})
            self.assertEqual(server.provider_lookup(self.request(enqueue=True)), failed)
            self.assertTrue(self.queue.empty())
            server.LAST_RUN.clear()
            server.load_previous()
            self.assertEqual(server.provider_lookup(self.request()), failed)
        with patch.object(server.time, "time", return_value=186401):
            self.assertEqual(server.provider_lookup(self.request())["retry_after_seconds"], 0)
            self.assertTrue(self.queue.empty())
            self.assertEqual(server.provider_lookup(self.request(enqueue=True))["state"], "queued")
            self.assertEqual(self.queue.qsize(), 1)

    def test_restart_marks_active_work_interrupted_and_loads_legacy_timestamps(self):
        with patch.object(server.time, "time", return_value=100000):
            server.provider_lookup(self.request(enqueue=True))
            job = self.queue.get_nowait()
            server.job_state(job, "processing")
            self.assertEqual(server.provider_lookup(self.request())["state"], "processing")
            server.LAST_RUN.clear()
            server.load_previous()
            self.assertEqual(server.provider_lookup(self.request())["state"], "interrupted")
            server.PERSIST.write_text(json.dumps({job["attempt_key"]: 100000}))
            server.LAST_RUN.clear()
            server.load_previous()
            self.assertEqual(server.provider_lookup(self.request()),
                             {"state": "cooldown", "retry_after_seconds": 86400})

    def test_active_job_never_duplicates_even_after_retry_interval(self):
        with patch.object(server.time, "time", return_value=100000):
            server.provider_lookup(self.request(enqueue=True))
        with patch.object(server.time, "time", return_value=200000):
            self.assertEqual(server.provider_lookup(self.request(enqueue=True))["state"], "queued")
            self.assertEqual(self.queue.qsize(), 1)

    def test_worker_success_and_extractor_failure_without_browser(self):
        for failure in (False, True):
            with self.subTest(failure=failure):
                server.LAST_RUN.clear()
                server.provider_lookup(self.request(enqueue=True))
                job = self.queue.get_nowait()
                api = MagicMock()
                context = api.sync_playwright.return_value.__enter__.return_value.chromium.launch_persistent_context.return_value
                with patch.dict(sys.modules, {'playwright.sync_api': api}), \
                        patch.object(server, 'match_episode', return_value='unused'), \
                        patch.object(server, 'DisneyBrowserExtractor') as extractor, \
                        patch.object(server, 'save_cached') as save:
                    def extract(*args):
                        self.assertEqual(server.provider_lookup(self.request())["state"], "processing")
                        if failure:
                            raise server.SubtitleError('pista cifrada')
                        return SRT
                    extractor.return_value.extract.side_effect = extract
                    server.process_job(job)
                    context.close.assert_called_once()
                    self.assertEqual(server.LAST_RUN[job['attempt_key']]['state'],
                                     'failed' if failure else 'complete')
                    self.assertEqual(save.call_count, 0 if failure else 1)
                self.assertFalse(server.BROWSER_LOCK.locked())

    def test_invalid_job_and_unsafe_cache_id(self):
        with self.assertRaises(ValueError):
            provider_bridge.validated_request({**self.request(), "series_url": "https://example.com/"})
        with self.assertRaises(ValueError):
            provider_bridge.validated_request({**self.request(), "tvdb_id": True})
        with self.assertRaises(ValueError):
            provider_bridge.get_cached("../../secret")


if __name__ == "__main__":
    unittest.main()
