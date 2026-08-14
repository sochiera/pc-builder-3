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
                        window.__realFetch = originalFetch;
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

            with urlopen(f"{base_url}/api/analyse?cpu=ryzen-5-7600&motherboard=z790&ram=ddr5-6000") as response:
                build = json.load(response)
            self.assertEqual(build["status"], "blocked")
            self.assertEqual(build["total"], 1648)
            self.assertEqual(build["issues"][0]["level"], "blocker")
        finally:
            process.terminate()
            process.wait(timeout=3)

    def test_analysis_reports_ram_conflicts_with_motherboard_and_cpu(self):
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

            cases = {
                "motherboard": "cpu=ryzen-5-7600&motherboard=b650&ram=ddr4-3200",
                "cpu": "cpu=core-i5-14600k&motherboard=z790&ram=ddr4-3200",
            }
            for conflict, query in cases.items():
                with self.subTest(conflict=conflict):
                    with urlopen(f"{base_url}/api/analyse?{query}") as response:
                        result = json.load(response)
                    self.assertEqual(result["status"], "blocked", f"DDR4 conflict blocks on {conflict}")
                    self.assertTrue(result["issues"], f"DDR4 conflict with {conflict} has an issue")
                    issue = result["issues"][0]
                    self.assertEqual(issue["level"], "blocker", f"RAM conflict with {conflict} is a blocker")
                    self.assertIn("RAM", issue["message"], "RAM conflict explains the involved memory")
                    self.assertIn(conflict, issue["message"], f"RAM conflict identifies the {conflict}")
                    self.assertIn("DDR4", issue["message"], "RAM conflict explains the unsupported standard")
        finally:
            process.terminate()
            process.wait(timeout=3)

    def test_analysis_marks_missing_and_conflicting_data_as_undetermined(self):
        from app import analyse

        cases = {
            "missing RAM standard": {
                "ram_id": None,
                "selected_components": None,
                "reason": "RAM",
            },
            "conflicting RAM values": {
                "ram_id": "ddr5-6000",
                "selected_components": [{"type": "ram", "model": "ddr4-3200"}],
                "reason": "RAM",
            },
            "conflicting RAM values with socket conflict": {
                "ram_id": "ddr5-6000",
                "selected_components": [{"type": "ram", "model": "ddr4-3200"}],
                "cpu": "core-i5-14600k",
                "motherboard": "b650",
                "reason": "RAM",
            },
        }

        for case, data in cases.items():
            with self.subTest(case=case):
                result = analyse(
                    data.get("cpu", "core-i5-14600k"),
                    data.get("motherboard", "z790"),
                    data["ram_id"],
                    data["selected_components"],
                )
                self.assertEqual(result["status"], "undetermined", f"{case} does not confirm compatibility")
                self.assertTrue(result["issues"], f"{case} provides a reason")
                self.assertTrue(
                    any(data["reason"] in issue["message"] for issue in result["issues"]),
                    f"{case} identifies the uncertain data",
                )

    def test_analysis_exposes_blocker_warning_and_information_with_reasons(self):
        from app import analyse

        selected_components = [
            {"type": "cpu", "model": "core-i5-14600k"},
            {"type": "motherboard", "model": "b650"},
            {"type": "ram", "model": "ddr4-3200"},
            {"type": "gpu", "model": "rtx-4070"},
            {"type": "disk", "model": "nvme-1tb"},
            {"type": "psu", "model": "psu-750"},
            {"type": "cooling", "model": "fortis-5"},
            {"type": "case", "model": "regnum-400"},
        ]

        result = analyse(
            "core-i5-14600k",
            "b650",
            "ddr4-3200",
            selected_components,
        )
        issues_by_level = {issue["level"]: issue for issue in result["issues"]}

        self.assertEqual(
            set(issues_by_level),
            {"blocker", "warning", "information"},
            "analysis distinguishes every public message level",
        )
        for level, issue in issues_by_level.items():
            with self.subTest(level=level):
                self.assertIsInstance(issue.get("message"), str)
                self.assertTrue(issue["message"].strip(), f"{level} includes an explanation")
        self.assertIn("socketu", issues_by_level["blocker"]["message"])
        self.assertIn("RAM", issues_by_level["blocker"]["message"])

        compatible_components = [
            {"type": "cpu", "model": "core-i5-14600k"},
            {"type": "motherboard", "model": "z790"},
            {"type": "ram", "model": "ddr5-6000"},
            {"type": "gpu", "model": "low-power-gpu"},
            {"type": "disk", "model": "quiet-disk"},
            {"type": "psu", "model": "psu-750"},
            {"type": "cooling", "model": "quiet-cooling"},
            {"type": "case", "model": "quiet-case"},
        ]
        compatible = analyse(
            "core-i5-14600k",
            "z790",
            "ddr5-6000",
            compatible_components,
        )
        self.assertEqual(compatible["status"], "compatible", "warnings and information do not block a build")
        self.assertEqual(
            {issue["level"] for issue in compatible["issues"]},
            {"warning", "information"},
            "a compatible build still exposes non-blocking message levels",
        )

    def test_analysis_reports_cpu_motherboard_cooling_dependency_and_refreshes(self):
        from app import analyse

        conflicting_components = [
            {"type": "cpu", "model": "ryzen-5-7600"},
            {"type": "motherboard", "model": "b650"},
            {"type": "ram", "model": "ddr5-6000"},
            {"type": "cooling", "model": "fortis-5"},
        ]
        compatible_components = [
            *conflicting_components[:3],
            {"type": "cooling", "model": "compatible-cooling"},
        ]

        blocked = analyse("ryzen-5-7600", "b650", "ddr5-6000", conflicting_components)
        self.assertEqual(blocked["status"], "blocked", "the prepared three-part dependency blocks the build")
        blocker_messages = [
            issue["message"] for issue in blocked["issues"] if issue["level"] == "blocker"
        ]
        self.assertTrue(blocker_messages, "the dependency exposes a blocker explanation")
        dependency_message = " ".join(blocker_messages)
        for component in ("ryzen-5-7600", "b650", "fortis-5"):
            with self.subTest(component=component):
                self.assertIn(component, dependency_message, "the explanation names every involved part")
        self.assertRegex(
            dependency_message.lower(),
            r"socket|chlod|cool|wysok|wysoko|zgod",
            "the blocker explains why the three selected parts conflict",
        )

        refreshed = analyse("ryzen-5-7600", "b650", "ddr5-6000", compatible_components)
        self.assertNotEqual(refreshed["status"], "blocked", "a compatible cooling choice clears the dependency blocker")
        self.assertFalse(
            any(issue["level"] == "blocker" for issue in refreshed["issues"]),
            "the refreshed analysis no longer reports the dependency as a blocker",
        )

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

    def test_catalog_preserves_multiple_imported_variants_of_each_type(self):
        payload = {
            "products": [
                {"id": "cpu-1", "model": "ryzen-5-7600", "name": "AMD Ryzen 5 7600", "price": 799},
                {"id": "cpu-2", "model": "core-i5-14600k", "name": "Intel Core i5-14600K", "price": 1249},
                {"id": "board-1", "model": "b650", "name": "MSI B650 Gaming Plus WiFi", "price": 699},
                {"id": "board-2", "model": "z790", "name": "ASUS Prime Z790-P", "price": 849},
                {"id": "ram-1", "model": "ddr5-6000", "name": "Kingston Fury DDR5 32 GB", "price": 499},
                {"id": "gpu-1", "model": "rtx-4070", "name": "GeForce RTX 4070", "price": 2399},
                {"id": "disk-1", "model": "nvme-1tb", "name": "Samsung 990 EVO 1 TB", "price": 399},
                {"id": "psu-1", "model": "psu-750", "name": "be quiet! Pure Power 12 M 750W", "price": 449},
                {"id": "cooler-1", "model": "fortis-5", "name": "Endorfy Fortis 5", "price": 199},
                {"id": "cooler-2", "model": "compatible-cooling", "name": "Kompatybilne chlodzenie", "price": 249},
                {"id": "case-1", "model": "regnum-400", "name": "Endorfy Regnum 400 ARGB", "price": 299},
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
                    with urlopen(base_url):
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
                self.assertEqual(response.status, 200)
            with urlopen(f"{base_url}/api/catalog") as response:
                catalog = json.load(response)
            self.assertEqual(len(catalog["products"]), 10, "catalog keeps every recognized imported variant")
            self.assertEqual(
                {product["model"] for product in catalog["products"] if product["type"] == "cpu"},
                {"ryzen-5-7600", "core-i5-14600k"},
            )
            self.assertEqual(
                {product["model"] for product in catalog["products"] if product["type"] == "motherboard"},
                {"b650", "z790"},
            )
            self.assertEqual(len(catalog["options"]), 10, "builder options reflect imported variants")
        finally:
            process.terminate()
            process.wait(timeout=3)

    def test_builder_accepts_one_catalog_part_of_each_required_type_as_one_set(self):
        payload = {
            "products": [
                {"id": "cpu-1", "model": "ryzen-5-7600", "name": "AMD Ryzen 5 7600", "price": 799},
                {"id": "board-1", "model": "b650", "name": "MSI B650 Gaming Plus WiFi", "price": 699},
                {"id": "ram-1", "model": "ddr5-6000", "name": "Kingston Fury DDR5 32 GB", "price": 499},
                {"id": "gpu-1", "model": "rtx-4070", "name": "GeForce RTX 4070", "price": 2399},
                {"id": "disk-1", "model": "nvme-1tb", "name": "Samsung 990 EVO 1 TB", "price": 399},
                {"id": "psu-1", "model": "psu-750", "name": "be quiet! Pure Power 12 M 750W", "price": 449},
                {"id": "cooler-1", "model": "fortis-5", "name": "Endorfy Fortis 5", "price": 199},
                {"id": "case-1", "model": "regnum-400", "name": "Endorfy Regnum 400 ARGB", "price": 299},
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

            import_request = Request(
                f"{base_url}/api/import",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(import_request) as response:
                self.assertEqual(response.status, 200)

            with urlopen(f"{base_url}/api/catalog") as response:
                catalog = json.load(response)
            with self.subTest("catalog contains all required types"):
                self.assertEqual(len(catalog["products"]), 8, "catalog contains one imported part of each required type")
                self.assertEqual(
                    len({product["id"] for product in catalog["products"]}),
                    8,
                    "catalog does not duplicate an imported part",
                )
                self.assertEqual(
                    {product["type"] for product in catalog["products"]},
                    {"cpu", "motherboard", "ram", "gpu", "disk", "psu", "cooling", "case"},
                    "catalog provides each required component type",
                )

            selections = {product["type"]: product["id"] for product in catalog["products"]}
            build_request = Request(
                f"{base_url}/api/build",
                data=json.dumps({"selections": selections}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urlopen(build_request) as response:
                    build_status = response.status
                    build = json.load(response)
            except HTTPError as error:
                build_status = error.code
                build = {}
            with self.subTest("builder returns one complete set"):
                self.assertEqual(build_status, 200, "builder accepts one selection for every required type")
                if build_status == 200:
                    self.assertEqual(set(build["products"]), set(selections.values()), "one set contains all selected parts")
                    selected_total = sum(product["price"] for product in catalog["products"])
                    self.assertEqual(build["total"], selected_total, "set reports total price")
                    self.assertEqual(build["analysis"]["total"], selected_total, "analysis reports the complete set total")
                    self.assertEqual(build["analysis"]["status"], "blocked", "insufficient PSU power blocks the complete set")
                    self.assertGreater(build["analysis"]["power_required"], build["analysis"]["psu_power"])
                    self.assertEqual(build["analysis"]["psu_power"], 750)
                    self.assertTrue(build["analysis"]["issues"], "blocked selections report an analysis issue")
        finally:
            process.terminate()
            process.wait(timeout=3)

    def test_builder_blocks_a_set_that_exceeds_selected_psu_power(self):
        payload = {
            "products": [
                {"id": "cpu-1", "model": "ryzen-5-7600", "name": "AMD Ryzen 5 7600", "price": 799},
                {"id": "board-1", "model": "b650", "name": "MSI B650 Gaming Plus WiFi", "price": 699},
                {"id": "ram-1", "model": "ddr5-6000", "name": "Kingston Fury DDR5 32 GB", "price": 499},
                {"id": "gpu-1", "model": "rtx-4070", "name": "GeForce RTX 4070", "price": 2399},
                {"id": "disk-1", "model": "nvme-1tb", "name": "Samsung 990 EVO 1 TB", "price": 399},
                {"id": "psu-1", "model": "psu-750", "name": "be quiet! Pure Power 12 M 750W", "price": 449},
                {"id": "cooler-1", "model": "fortis-5", "name": "Endorfy Fortis 5", "price": 199},
                {"id": "case-1", "model": "regnum-400", "name": "Endorfy Regnum 400 ARGB", "price": 299},
            ]
        }
        with socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        base_url = f"http://127.0.0.1:{port}"
        process = subprocess.Popen([sys.executable, "app.py", "--port", str(port)], cwd=ROOT)
        try:
            import_request = Request(
                f"{base_url}/api/import",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            for _ in range(20):
                try:
                    with urlopen(import_request) as response:
                        self.assertEqual(response.status, 200)
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                self.fail("Application did not start")

            with urlopen(f"{base_url}/api/catalog") as response:
                catalog = json.load(response)
            selections = {product["type"]: product["id"] for product in catalog["products"]}
            build_request = Request(
                f"{base_url}/api/build",
                data=json.dumps({"selections": selections}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(build_request) as response:
                build = json.load(response)

            analysis = build["analysis"]
            self.assertEqual(analysis["status"], "blocked", "insufficient PSU power blocks the set")
            self.assertGreater(analysis["power_required"], analysis["psu_power"], "reported requirement exceeds available PSU power")
            self.assertEqual(analysis["psu_power"], 750, "analysis reports the selected PSU capacity")
            power_issues = [
                issue for issue in analysis["issues"]
                if "power" in issue["message"].lower() or "moc" in issue["message"].lower()
            ]
            self.assertTrue(power_issues, "power blocker explains the requirement and available PSU power")
            self.assertIn("900 W", power_issues[0]["message"])
            self.assertIn("750 W", power_issues[0]["message"])
        finally:
            process.terminate()
            process.wait(timeout=3)

    def test_builder_view_selects_all_parts_and_refreshes_complete_set(self):
        payload = {
            "products": [
                {"id": "cpu-1", "model": "ryzen-5-7600", "name": "AMD Ryzen 5 7600", "price": 799},
                {"id": "board-1", "model": "b650", "name": "MSI B650 Gaming Plus WiFi", "price": 699},
                {"id": "ram-1", "model": "ddr5-6000", "name": "Kingston Fury DDR5 32 GB", "price": 499},
                {"id": "ram-2", "model": "ddr4-3200", "name": "Kingston Fury DDR4 32 GB", "price": 299},
                {"id": "gpu-1", "model": "rtx-4070", "name": "GeForce RTX 4070", "price": 2399},
                {"id": "disk-1", "model": "nvme-1tb", "name": "Samsung 990 EVO 1 TB", "price": 399},
                {"id": "psu-1", "model": "psu-750", "name": "be quiet! Pure Power 12 M 750W", "price": 449},
                {"id": "cooler-1", "model": "fortis-5", "name": "Endorfy Fortis 5", "price": 199},
                {"id": "case-1", "model": "regnum-400", "name": "Endorfy Regnum 400 ARGB", "price": 299},
            ]
        }
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
            import_request = Request(
                f"http://127.0.0.1:{app_port}/api/import",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            for _ in range(20):
                try:
                    with urlopen(import_request) as response:
                        self.assertEqual(response.status, 200)
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                self.fail("Application did not start")
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
                        window.__buildBodies = [];
                        window.__buildResponses = [];
                        const originalFetch = window.fetch;
                        window.__realFetch = originalFetch;
                        window.fetch = async (...args) => {
                            if (args[0] === '/api/build') window.__buildBodies.push(JSON.parse(args[1].body));
                            const response = await originalFetch(...args);
                            if (args[0] === '/api/build') window.__buildResponses.push(await response.clone().json());
                            return response;
                        };
                    """,
                    "args": [],
                },
            )
            required_types = ["cpu", "motherboard", "ram", "gpu", "disk", "psu", "cooling", "case"]
            expected_ids = {
                "cpu": "cpu-1",
                "motherboard": "board-1",
                "ram": "ram-1",
                "gpu": "gpu-1",
                "disk": "disk-1",
                "psu": "psu-1",
                "cooling": "cooler-1",
                "case": "case-1",
            }
            expected_option_counts = {
                "cpu": 2,
                "motherboard": 2,
                "ram": 2,
                "gpu": 1,
                "disk": 1,
                "psu": 1,
                "cooling": 2,
                "case": 1,
            }
            for _ in range(20):
                select_count = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return document.querySelectorAll('#selectors select').length", "args": []}
                )["value"]
                if select_count == len(required_types):
                    break
                time.sleep(0.1)
            else:
                self.fail("builder does not render all required component selectors")
            self.assertEqual(
                self.webdriver(
                    "POST", f"{base}/execute/sync",
                    {"script": "return [...document.querySelectorAll('#selectors select')].map(select => select.id)", "args": []},
                )["value"],
                required_types,
                "builder renders a selector for every required component type",
            )
            for component_type in required_types:
                self.assertEqual(
                    self.webdriver(
                        "POST", f"{base}/execute/sync",
                        {"script": f"return document.querySelector('#{component_type}').options.length", "args": []},
                    )["value"],
                    expected_option_counts[component_type],
                    f"{component_type} selector exposes every catalog model",
                )
                self.assertEqual(
                    self.webdriver(
                        "POST", f"{base}/execute/sync",
                        {"script": f"return document.querySelector('#{component_type}').value", "args": []},
                    )["value"],
                    expected_ids[component_type],
                    f"{component_type} selector exposes its catalog selection",
                )
            for _ in range(20):
                summary = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return document.querySelector('#build-products').textContent", "args": []}
                )["value"]
                if all(product["name"] in summary for product in payload["products"] if product["id"] in expected_ids.values()):
                    break
                time.sleep(0.1)
            else:
                self.fail("complete build summary did not render")
            self.assertEqual(
                self.webdriver(
                    "POST", f"{base}/execute/sync",
                    {"script": "return document.querySelectorAll('#build-products li').length", "args": []},
                )["value"],
                8,
                "build summary renders every selected product together",
            )
            page = self.webdriver(
                "POST", f"{base}/execute/sync", {"script": "return document.querySelector('.summary').textContent", "args": []}
            )["value"]
            self.assertIn("5742 PLN", page)
            self.assertIn("Konfiguracja zablokowana", page)
            self.assertIn("900 W | PSU: 750 W", page, "initial analysis renders the current power reserve")
            self.assertIn("Przeznaczenie: gaming", page, "initial analysis renders the default purpose")
            self.webdriver(
                "POST", f"{base}/execute/sync",
                {
                    "script": "document.querySelector('#purpose').dispatchEvent(new Event('change', {bubbles: true}));",
                    "args": [],
                },
            )
            for _ in range(20):
                gaming_responses = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return window.__buildResponses", "args": []}
                )["value"]
                if any(response.get("purpose") == "gaming" for response in gaming_responses):
                    break
                time.sleep(0.1)
            else:
                self.fail("gaming purpose change does not render a build response")
            gaming_analysis = next(
                response["analysis"] for response in gaming_responses if response.get("purpose") == "gaming"
            )
            gaming_information = next(
                issue["message"] for issue in gaming_analysis["issues"] if issue["level"] == "information"
            )
            self.assertIn("Gaming", gaming_information, "gaming analysis explains its selected purpose")
            purpose_selector = self.webdriver(
                "POST", f"{base}/execute/sync",
                {"script": "return document.querySelector('#purpose').tagName", "args": []},
            )
            self.assertEqual(purpose_selector["value"], "SELECT", "builder restricts purpose to prepared choices")
            purpose_options = self.webdriver(
                "POST", f"{base}/execute/sync",
                {"script": "return [...document.querySelectorAll('#purpose option')].map(option => option.value)", "args": []},
            )["value"]
            self.assertIn("gaming", purpose_options, "purpose selector exposes the prepared gaming option")
            self.assertIn("programming", purpose_options, "purpose selector exposes another prepared option")
            self.webdriver(
                "POST", f"{base}/execute/sync",
                {
                    "script": "const purpose = document.querySelector('#purpose'); purpose.value = 'programming'; purpose.dispatchEvent(new Event('change', {bubbles: true}));",
                    "args": [],
                },
            )
            for _ in range(20):
                bodies = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return window.__buildBodies", "args": []}
                )["value"]
                if bodies and bodies[-1].get("purpose") == "programming":
                    break
                time.sleep(0.1)
            else:
                self.fail("purpose change does not submit the selected purpose with the build")
            self.assertEqual(bodies[-1]["purpose"], "programming", "build request carries the changed purpose")
            for _ in range(20):
                purpose_summary = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return document.querySelector('.summary').textContent", "args": []}
                )["value"]
                if "programming" in purpose_summary:
                    break
                time.sleep(0.1)
            else:
                self.fail("selected purpose does not render beside the build")
            self.assertIn("Przeznaczenie: programming", purpose_summary, "changed purpose remains visible with the build")
            programming_responses = self.webdriver(
                "POST", f"{base}/execute/sync", {"script": "return window.__buildResponses", "args": []}
            )["value"]
            programming_analysis = next(
                response["analysis"] for response in programming_responses if response.get("purpose") == "programming"
            )
            programming_information = next(
                issue["message"] for issue in programming_analysis["issues"] if issue["level"] == "information"
            )
            self.assertIn("Programowanie", programming_information, "programming analysis explains its selected purpose")
            self.assertNotEqual(
                programming_analysis,
                gaming_analysis,
                "changing purpose refreshes an analysis that reflects the new goal",
            )
            dependency_message = self.webdriver(
                "POST", f"{base}/execute/sync",
                {"script": "return [...document.querySelectorAll('#issue [data-level=blocker]')].map(item => item.textContent).join(' ')", "args": []},
            )["value"]
            for component in ("ryzen-5-7600", "b650", "fortis-5"):
                with self.subTest(component=component):
                    self.assertIn(component, dependency_message, "the visible dependency explanation names every involved part")
            self.assertRegex(
                dependency_message.lower(),
                r"socket|chlod|cool|wysok|wysoko|zgod",
                "the visible dependency explanation includes the conflict reason",
            )
            rendered_levels = self.webdriver(
                "POST", f"{base}/execute/sync",
                {
                    "script": "return [...document.querySelectorAll('#issue [data-level]')].map(item => ({level: item.dataset.level, text: item.textContent}))",
                    "args": [],
                },
            )["value"]
            self.assertEqual(
                {item["level"] for item in rendered_levels},
                {"blocker", "warning", "information"},
                "analysis renders each message level in a separate element",
            )
            for item in rendered_levels:
                with self.subTest(level=item["level"]):
                    self.assertTrue(item["text"].strip(), "each rendered level keeps its explanation")
            visible_labels = {
                "blocker": "Blokada",
                "warning": "Ostrzezenie",
                "information": "Informacja",
            }
            for item in rendered_levels:
                with self.subTest(label=item["level"]):
                    self.assertIn(
                        visible_labels[item["level"]],
                        item["text"],
                        "each analysis level has a visible label for the buyer",
                    )
            self.webdriver(
                "POST", f"{base}/execute/sync",
                {
                    "script": """
                        window.fetch = async (url) => {
                            if (url === '/api/build') {
                                return new Response(JSON.stringify({
                                    products: ['cpu-1', 'board-1', 'ram-1', 'gpu-1', 'disk-1', 'psu-1', 'cooler-1', 'case-1'],
                                    total: 5742,
                                    analysis: {
                                        status: 'undetermined',
                                        power_required: 900,
                                        psu_power: 750,
                                        issues: [{level: 'warning', message: 'Nierozstrzygnieta zgodnosc RAM: brak standardu RAM potrzebnego do oceny zgodnosci.'}]
                                    }
                                }), {headers: {'Content-Type': 'application/json'}});
                            }
                            return window.__realFetch(url);
                        };
                        document.querySelector('#ram').dispatchEvent(new Event('change', {bubbles: true}));
                    """,
                    "args": [],
                },
            )
            for _ in range(20):
                undetermined_summary = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return document.querySelector('.summary').textContent", "args": []}
                )["value"]
                if "Nierozstrzygnieta" in undetermined_summary:
                    break
                time.sleep(0.1)
            else:
                self.fail("undetermined analysis does not render a distinct buyer-facing state")
            self.assertIn("Nierozstrzygnieta", undetermined_summary, "undetermined analysis has a distinct status")
            self.assertNotIn("Konfiguracja zablokowana", undetermined_summary, "undetermined analysis is not presented as blocked")
            self.assertIn("brak standardu RAM", undetermined_summary, "undetermined analysis keeps its explanation")
            self.assertEqual(
                self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return document.querySelector('#status').className", "args": []}
                )["value"],
                "undetermined",
                "undetermined analysis uses a distinct status class",
            )
            self.webdriver(
                "POST", f"{base}/execute/sync",
                {
                    "script": """
                        window.fetch = async (...args) => {
                            if (args[0] === '/api/build') window.__buildBodies.push(JSON.parse(args[1].body));
                            return window.__realFetch(...args);
                        };
                    """,
                    "args": [],
                },
            )
            self.webdriver(
                "POST", f"{base}/execute/sync",
                {"script": "const ram = document.querySelector('#ram'); ram.value = 'ram-2'; ram.dispatchEvent(new Event('change', {bubbles: true}));", "args": []},
            )
            for _ in range(20):
                ram_summary = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return document.querySelector('.summary').textContent", "args": []}
                )["value"]
                if "Konfiguracja zablokowana" in ram_summary and "DDR4" in ram_summary:
                    break
                time.sleep(0.1)
            else:
                self.fail("RAM change does not refresh the compatibility analysis")
            self.assertIn("RAM", ram_summary, "RAM change renders the involved component")
            self.assertIn("b650", ram_summary, "RAM change identifies the affected motherboard")
            self.webdriver(
                "POST", f"{base}/execute/sync",
                {"script": "const ram = document.querySelector('#ram'); ram.value = 'ram-1'; ram.dispatchEvent(new Event('change', {bubbles: true}));", "args": []},
            )
            for _ in range(20):
                compatible_summary = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return document.querySelector('.summary').textContent", "args": []}
                )["value"]
                if "Konfiguracja zablokowana" in compatible_summary and "DDR4" not in compatible_summary:
                    break
                time.sleep(0.1)
            else:
                self.fail("compatible RAM change does not clear the RAM compatibility issue")
            self.assertNotIn("DDR4", compatible_summary, "compatible RAM does not leave a RAM conflict")
            self.assertIn("900 W | PSU: 750 W", compatible_summary, "RAM refresh preserves the current power assessment")
            self.webdriver(
                "POST", f"{base}/execute/sync",
                {"script": "const cooling = document.querySelector('#cooling'); cooling.value = 'cooler-2'; cooling.dispatchEvent(new Event('change', {bubbles: true}));", "args": []},
            )
            for _ in range(20):
                bodies = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return window.__buildBodies", "args": []}
                )["value"]
                if bodies and bodies[-1]["selections"]["cooling"] == "cooler-2":
                    break
                time.sleep(0.1)
            else:
                self.fail("compatible cooling change does not refresh the build")
            self.assertEqual(bodies[-1]["selections"]["cooling"], "cooler-2")
            for _ in range(20):
                cooling_summary = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return document.querySelector('.summary').textContent", "args": []}
                )["value"]
                if "zaleznosc CPU-plyta-chlodzenie" not in cooling_summary:
                    break
                time.sleep(0.1)
            else:
                self.fail("compatible cooling change does not clear the three-part dependency blocker")
            self.assertNotIn("fortis-5", cooling_summary, "compatible cooling clears the three-part dependency blocker")
            self.assertNotIn("zaleznosc CPU-plyta-chlodzenie", cooling_summary)
            self.webdriver(
                "POST", f"{base}/execute/sync",
                {"script": "const cpu = document.querySelector('#cpu'); cpu.value = 'cpu-2'; cpu.dispatchEvent(new Event('change', {bubbles: true}));", "args": []},
            )
            for _ in range(20):
                bodies = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return window.__buildBodies", "args": []}
                )["value"]
                if bodies and bodies[-1]["selections"]["cpu"] == "cpu-2":
                    break
                time.sleep(0.1)
            else:
                self.fail("changing a component does not refresh the build")
            self.assertEqual(set(bodies[-1]["selections"]), set(required_types), "refresh submits every component selection")
            self.assertEqual(bodies[-1]["selections"]["cpu"], "cpu-2", "refresh submits the newly selected model")
            for _ in range(20):
                refreshed_products = self.webdriver(
                    "POST", f"{base}/execute/sync",
                    {"script": "return document.querySelector('#build-products').textContent", "args": []},
                )["value"]
                if "Intel Core i5-14600K" in refreshed_products:
                    break
                time.sleep(0.1)
            else:
                self.fail("CPU change does not render the newly selected product")
            blocked_summary = self.webdriver(
                "POST", f"{base}/execute/sync", {"script": "return document.querySelector('.summary').textContent", "args": []}
            )["value"]
            self.assertIn("Konfiguracja zablokowana", blocked_summary, "incompatible CPU change blocks the build")
            self.assertIn("socketu", blocked_summary, "blocked build renders the compatibility issue")
            self.assertIn("976 W | PSU: 750 W", blocked_summary, "changing the CPU refreshes the power assessment")
            self.webdriver(
                "POST", f"{base}/execute/sync",
                {"script": "const board = document.querySelector('#motherboard'); board.value = 'board-2'; board.dispatchEvent(new Event('change', {bubbles: true}));", "args": []},
            )
            for _ in range(20):
                bodies = self.webdriver(
                    "POST", f"{base}/execute/sync", {"script": "return window.__buildBodies", "args": []}
                )["value"]
                if bodies[-1]["selections"]["motherboard"] == "board-2":
                    break
                time.sleep(0.1)
            else:
                self.fail("changing the motherboard does not refresh the build")
            self.assertEqual(
                self.webdriver(
                    "POST", f"{base}/execute/sync",
                    {"script": "return document.querySelectorAll('#build-products li').length", "args": []},
                )["value"],
                8,
                "refresh keeps all selected products in the summary",
            )
            refreshed_products = self.webdriver(
                "POST", f"{base}/execute/sync",
                {"script": "return document.querySelector('#build-products').textContent", "args": []},
            )["value"]
            self.assertIn("Intel Core i5-14600K", refreshed_products)
            self.assertIn("ASUS Prime Z790-P", refreshed_products)
            refreshed_summary = self.webdriver(
                "POST", f"{base}/execute/sync", {"script": "return document.querySelector('.summary').textContent", "args": []}
            )["value"]
            self.assertIn("6342 PLN", refreshed_summary, "refresh shows the total for the newly selected models")
            self.assertIn("Konfiguracja zablokowana", refreshed_summary, "refresh keeps the current analysis visible")
            self.assertNotIn("socketu", refreshed_summary, "compatible motherboard change clears the prior issue")
            self.assertIn("976 W | PSU: 750 W", refreshed_summary, "motherboard refresh keeps the current power assessment")
        finally:
            if "session_id" in locals():
                try:
                    self.webdriver("DELETE", f"/session/{session_id}")
                except OSError:
                    pass
            driver_process.terminate()
            driver_process.wait(timeout=3)
            app_process.terminate()
            app_process.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
