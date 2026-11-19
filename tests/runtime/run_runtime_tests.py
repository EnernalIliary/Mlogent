"""Application ownership and concurrent runtime contracts."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from logic_runtime import Application, current_application
import chats


class RuntimeTests(unittest.TestCase):
    def test_concurrent_queue_access_creates_one_queue(self):
        with tempfile.TemporaryDirectory() as root:
            app = Application(root)
            with patch('logic_runtime.jobqueue.Queue') as factory:
                queue = factory.return_value
                queue.start.return_value = queue
                factory.side_effect = lambda *args, **kwargs: (time.sleep(0.01) or queue)
                with ThreadPoolExecutor(max_workers=8) as pool:
                    queues = list(pool.map(lambda _: app.jobs_queue(), range(32)))
                self.assertTrue(all(q is queue for q in queues))
                factory.assert_called_once()
                app.close()
                app.close()
                queue.stop.assert_called_once()
                with self.assertRaises(RuntimeError):
                    app.jobs_queue()
                self.assertTrue(app.STOP.is_set())

    def test_chat_workers_keep_their_application(self):
        with tempfile.TemporaryDirectory() as root:
            apps = [Application(Path(root) / str(i)) for i in range(2)]
            barrier = threading.Barrier(2)
            seen = []
            def run(chat):
                barrier.wait(timeout=5)
                app = current_application()
                seen.append((app, chats.store().path, app.LLM_STATE['model']))
            try:
                with patch('chats._run_loop', side_effect=run):
                    for i, app in enumerate(apps):
                        app.LLM_STATE.update(kind='llm', url='http://unused', model=str(i))
                        app.chats.start({'text': 'runtime isolation'})
                    deadline = time.monotonic() + 5
                    while any(app.chats.running() for app in apps) and time.monotonic() < deadline:
                        time.sleep(0.01)
                self.assertEqual(len(seen), 2)
                for app, path, model in seen:
                    self.assertEqual(model, str(apps.index(app)))
                    self.assertEqual(path, str(Path(app.WROOT) / 'out/jobs/chats'))
                self.assertIsNot(apps[0].chat_store, apps[1].chat_store)
                self.assertTrue(all(app.chats.running() == 0 for app in apps))
                apps[0].chat_gone.add('first-only')
                self.assertNotIn('first-only', apps[1].chat_gone)
                apps[0].STOP.set()
                self.assertFalse(apps[1].STOP.is_set())
            finally:
                for app in apps:
                    app.close()

    def test_construction_keeps_stores_lazy(self):
        with tempfile.TemporaryDirectory() as root:
            app = Application(root)
            self.assertIsNone(app.JOBS)
            self.assertIsNone(app.chat_store)
            self.assertFalse((Path(root) / 'out').exists())
            app.close()
        self.assertNotIn('logicd', sys.modules)


if __name__ == '__main__':
    unittest.main()
