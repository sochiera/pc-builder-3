import json
import subprocess
import sys
import time
import unittest
from pathlib import Path
from socket import socket
from urllib.request import urlopen


ROOT = Path(__file__).parent


class BuilderSmokeTest(unittest.TestCase):
    def test_running_app_reports_socket_conflict(self):
        with socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        base_url = f"http://127.0.0.1:{port}"
        process = subprocess.Popen([sys.executable, "app.py", "--port", str(port)], cwd=ROOT)
        try:
            for _ in range(20):
                try:
                    with urlopen(f"{base_url}/", timeout=0.2) as response:
                        self.assertIn(b"Buduj PC", response.read())
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                self.fail("Application did not start")

            with urlopen(f"{base_url}/api/analyse?cpu=ryzen-5-7600&motherboard=z790") as response:
                build = json.load(response)
            self.assertEqual(build["status"], "blocked")
            self.assertEqual(build["total"], 1648)
            self.assertEqual(build["issues"][0]["level"], "blocker")
        finally:
            process.terminate()
            process.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
