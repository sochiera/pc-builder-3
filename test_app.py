import json
import subprocess
import sys
import time
import unittest
from pathlib import Path
from socket import socket
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).parent


class BuilderSmokeTest(unittest.TestCase):
    def webdriver(self, method, path, payload=None):
        request = Request(
            f"http://127.0.0.1:{self.webdriver_port}{path}",
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urlopen(request) as response:
            return json.load(response)

    def test_operator_view_imports_and_renders_success_and_error(self):
        with socket() as listener:
            listener.bind(("127.0.0.1", 0))
            app_port = listener.getsockname()[1]
        with socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.webdriver_port = listener.getsockname()[1]
        app_process = subprocess.Popen([sys.executable, "app.py", "--port", str(app_port)], cwd=ROOT)
        driver_process = subprocess.Popen(
            ["geckodriver", "--port", str(self.webdriver_port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(20):
                try:
                    with urlopen(f"http://127.0.0.1:{self.webdriver_port}/status", timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                self.skipTest("geckodriver is unavailable")
            session = self.webdriver("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "firefox"}}})
            session_id = session["value"]["sessionId"]
            base = f"/session/{session_id}"
            self.webdriver("POST", f"{base}/url", {"url": f"http://127.0.0.1:{app_port}/"})
            button = self.webdriver("POST", f"{base}/element", {"using": "css selector", "value": "#import"})
            self.webdriver("POST", f"{base}/element/{button['value']['element-6066-11e4-a52e-4f735466cecf']}/click", {})
            for _ in range(20):
                status = self.webdriver("POST", f"{base}/execute/sync", {"script": "return document.querySelector('#import-status').textContent", "args": []})
                if "Zaimportowano: 2" in status["value"]:
                    break
                time.sleep(0.1)
            else:
                self.fail("import result did not render")
            rendered = self.webdriver("POST", f"{base}/execute/sync", {"script": "return document.querySelector('#import-products').textContent", "args": []})
            self.assertIn("AMD Ryzen 5 7600", rendered["value"])
            self.assertIn("MSI B650 Gaming Plus WiFi", rendered["value"])
            self.webdriver("POST", f"{base}/execute/sync", {"script": "window.fetch = async () => new Response(JSON.stringify({error: 'bad response'}), {status: 400}); document.querySelector('#import').click()", "args": []})
            for _ in range(20):
                error = self.webdriver("POST", f"{base}/execute/sync", {"script": "return document.querySelector('#import-status').textContent", "args": []})
                if "Blad importu: bad response" in error["value"]:
                    break
                time.sleep(0.1)
            else:
                self.fail("import error did not render")
        finally:
            if 'session_id' in locals():
                try:
                    self.webdriver("DELETE", f"/session/{session_id}")
                except OSError:
                    pass
            driver_process.terminate()
            driver_process.wait(timeout=3)
            app_process.terminate()
            app_process.wait(timeout=3)

    def test_operator_view_can_run_import_and_show_report(self):
        from app import PAGE

        page = PAGE.lower()
        self.assertIn("import", page, "operator view offers an import action")
        self.assertRegex(page, r"fetch\([^)]*api/import", "operator view calls the import endpoint")
        self.assertIn("method: 'post'", page, "operator view submits the prepared response")
        self.assertIn("cpu-1', name: 'amd ryzen 5 7600", page, "prepared response includes the first product")
        self.assertIn("board-1', name: 'msi b650 gaming plus wifi", page, "prepared response includes the second product")
        self.assertIn("renderimportedproducts(report.products)", page, "operator view renders every imported product")
        self.assertIn("zaimportowano: ${report.count}", page, "operator view presents the import count")
        self.assertIn("product.name", page, "operator view presents each product name")
        self.assertIn("product.id", page, "operator view presents each product id")

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

    def test_import_reports_every_product_and_import_count(self):
        payload = {
            "products": [
                {"id": "cpu-1", "name": "AMD Ryzen 5 7600"},
                {"id": "board-1", "name": "MSI B650 Gaming Plus WiFi"},
            ]
        }
        with socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        base_url = f"http://127.0.0.1:{port}"
        process = subprocess.Popen([sys.executable, "app.py", "--port", str(port)], cwd=ROOT)
        try:
            for _ in range(20):
                try:
                    with urlopen(f"{base_url}/", timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                self.fail("Application did not start")

            request = Request(
                f"{base_url}/api/import",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urlopen(request) as response:
                    status = response.status
                    report = json.load(response)
            except HTTPError as error:
                status = error.code
                report = {}

            self.assertEqual(status, 200, "operator can run the prepared x-kom import")
            self.assertEqual(report["products"], payload["products"], "report contains every imported product")
            self.assertEqual(report["count"], len(payload["products"]), "report contains the imported item count")

            invalid_request = Request(
                f"{base_url}/api/import",
                data=json.dumps({}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as error_context:
                urlopen(invalid_request)
            self.assertEqual(error_context.exception.code, 400, "failed import is reported as an error")
            with error_context.exception as error_response:
                error_report = json.load(error_response)
            self.assertTrue(error_report["error"], "failed import includes the reason")
        finally:
            process.terminate()
            process.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
