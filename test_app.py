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
            self.webdriver(
                "POST",
                f"{base}/execute/sync",
                {
                    "script": """
                        window.__importBodies = [];
                        window.__fetchPaths = [];
                        const originalFetch = window.fetch;
                        window.fetch = async (...args) => {
                            window.__fetchPaths.push(args[0]);
                            if (args[0] === '/api/import') {
                                window.__importBodies.push(JSON.parse(args[1].body));
                            }
                            return originalFetch(...args);
                        };
                    """,
                    "args": [],
                },
            )
            button = self.webdriver("POST", f"{base}/element", {"using": "css selector", "value": "#import"})
            self.webdriver("POST", f"{base}/element/{button['value']['element-6066-11e4-a52e-4f735466cecf']}/click", {})
            for _ in range(20):
                status = self.webdriver("POST", f"{base}/execute/sync", {"script": "return document.querySelector('#import-status').textContent", "args": []})
                if status["value"].startswith("Zaimportowano:"):
                    break
                time.sleep(0.1)
            else:
                self.fail("import result did not render")
            self.assertEqual(status["value"], "Zaimportowano: 1", "same-model offers produce one imported product")
            imported_payload = self.webdriver(
                "POST",
                f"{base}/execute/sync",
                {"script": "return window.__importBodies[0]", "args": []},
            )["value"]
            self.assertEqual(len(imported_payload["products"]), 2)
            self.assertEqual(
                [offer["model"] for offer in imported_payload["products"]],
                ["ryzen-5-7600", "ryzen-5-7600"],
                "prepared UI response contains two offers of the same model",
            )
            rendered = self.webdriver("POST", f"{base}/execute/sync", {"script": "return document.querySelector('#import-products').textContent", "args": []})
            product_count = self.webdriver("POST", f"{base}/execute/sync", {"script": "return document.querySelectorAll('#import-products li').length", "args": []})
            self.assertEqual(product_count["value"], 1, "same-model offers render as one catalog product")
            self.assertIn("AMD Ryzen 5 7600", rendered["value"])
            self.assertIn("AMD Ryzen 5 7600 BOX", rendered["value"], "rendered product includes first offer")
            self.assertIn("799 PLN", rendered["value"], "rendered product includes first offer price")
            self.assertIn("x-kom", rendered["value"], "rendered product includes first offer source")
            self.assertIn("AMD 7600 3.8 GHz", rendered["value"], "rendered product includes second offer")
            self.assertIn("829 PLN", rendered["value"], "rendered product includes second offer price")
            self.assertIn("prepared-shop", rendered["value"], "rendered product includes second offer source")
            for _ in range(20):
                catalog_rendered = self.webdriver(
                    "POST",
                    f"{base}/execute/sync",
                    {"script": "return document.querySelector('#catalog-products')?.textContent || ''", "args": []},
                )
                if "ryzen-5-7600" in catalog_rendered["value"]:
                    break
                time.sleep(0.1)
            else:
                self.fail("catalog did not render after import")
            fetch_paths = self.webdriver(
                "POST",
                f"{base}/execute/sync",
                {"script": "return window.__fetchPaths", "args": []},
            )["value"]
            self.assertIn("/api/catalog", fetch_paths, "buyer view reads the catalog endpoint")
            self.assertEqual(
                self.webdriver(
                    "POST",
                    f"{base}/execute/sync",
                    {"script": "return document.querySelectorAll('#catalog-products li').length", "args": []},
                )["value"],
                1,
                "buyer view renders one item for the two offers",
            )
            self.assertIn("cpu", catalog_rendered["value"])
            self.assertIn("ryzen-5-7600", catalog_rendered["value"])
            self.assertIn("829 PLN", catalog_rendered["value"])
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
        self.assertIn("model: 'ryzen-5-7600", page, "prepared response identifies the imported model")
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
                {"id": "cpu-1", "model": "ryzen-5-7600", "name": "AMD Ryzen 5 7600"},
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

            with urlopen(f"{base_url}/api/catalog") as response:
                catalog_status = response.status
                catalog = json.load(response)
            self.assertEqual(catalog_status, 200, "catalog projection does not invalidate a successful import")
            self.assertEqual(catalog["products"], [], "catalog omits a recognized offer without a price")

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

    def test_import_groups_same_model_offers_and_preserves_price_and_source(self):
        payload = {
            "products": [
                {
                    "id": "offer-1",
                    "model": "ryzen-5-7600",
                    "name": "AMD Ryzen 5 7600 BOX",
                    "price": 799,
                    "source": "x-kom",
                },
                {
                    "id": "offer-2",
                    "model": "ryzen-5-7600",
                    "name": "AMD 7600 3.8 GHz",
                    "price": 829,
                    "source": "prepared-shop",
                },
                {
                    "id": "offer-3",
                    "name": "Unmatched graphics card",
                    "price": 1499,
                    "source": "unknown-shop",
                },
                {
                    "id": "offer-4",
                    "model": "unrecognized-model",
                    "name": "Uncertain match A",
                    "price": 100,
                    "source": "shop-a",
                },
                {
                    "id": "offer-5",
                    "model": "unrecognized-model",
                    "name": "Uncertain match B",
                    "price": 110,
                    "source": "shop-b",
                },
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
            with urlopen(request) as response:
                report = json.load(response)

            self.assertEqual(
                len(report["products"]),
                4,
                "recognized model groups, while unmatched offers stay separate",
            )
            expected_product = {
                "id": "ryzen-5-7600",
                "name": "AMD Ryzen 5 7600",
                "offers": payload["products"][:2],
            }
            self.assertEqual(
                report["products"][0],
                expected_product,
                "one product preserves both complete offers with price and source",
            )
            self.assertEqual(
                report["products"][1],
                payload["products"][2],
                "offer without a recognized model remains a separate product",
            )
            self.assertEqual(report["products"][2], payload["products"][3])
            self.assertEqual(report["products"][3], payload["products"][4])
        finally:
            process.terminate()
            process.wait(timeout=3)

    def test_catalog_exposes_one_product_with_current_offer_price_after_import(self):
        payload = {
            "products": [
                {
                    "id": "offer-1",
                    "model": "ryzen-5-7600",
                    "name": "AMD Ryzen 5 7600 BOX",
                    "price": 799,
                    "source": "x-kom",
                },
                {
                    "id": "offer-2",
                    "model": "ryzen-5-7600",
                    "name": "AMD 7600 3.8 GHz",
                    "price": 829,
                    "source": "prepared-shop",
                },
                {
                    "id": "offer-board",
                    "model": "b650",
                    "name": "MSI B650 Gaming Plus WiFi",
                    "price": 699,
                    "source": "prepared-shop",
                },
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
            with urlopen(request) as response:
                self.assertEqual(response.status, 200, "catalog can be opened after import")

            try:
                with urlopen(f"{base_url}/api/catalog") as response:
                    catalog_status = response.status
                    catalog = json.load(response)
            except HTTPError as error:
                catalog_status = error.code
                catalog = {}

            self.assertEqual(catalog_status, 200, "catalog is available after import")
            self.assertEqual(len(catalog["products"]), 2, "each supported prepared part appears once")
            cpu, motherboard = catalog["products"]
            self.assertEqual(cpu["type"], "cpu", "catalog identifies the CPU type")
            self.assertEqual(cpu["model"], "ryzen-5-7600", "catalog identifies the CPU model")
            self.assertEqual(cpu["price"], 829, "catalog shows the current CPU offer price")
            self.assertEqual(motherboard["type"], "motherboard", "catalog identifies the motherboard type")
            self.assertEqual(motherboard["model"], "b650", "catalog identifies the motherboard model")
            self.assertEqual(motherboard["price"], 699, "catalog shows the motherboard offer price")
        finally:
            process.terminate()
            process.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
