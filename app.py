#!/usr/bin/env python3
"""Minimal vertical slice for the PC builder."""

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


CPUS = {
    "ryzen-5-7600": {"name": "AMD Ryzen 5 7600", "socket": "AM5", "ram_standards": ["DDR5"], "price": 799},
    "core-i5-14600k": {"name": "Intel Core i5-14600K", "socket": "LGA1700", "ram_standards": ["DDR5"], "price": 1249},
}

MOTHERBOARDS = {
    "b650": {"name": "MSI B650 Gaming Plus WiFi", "socket": "AM5", "ram_standards": ["DDR5"], "price": 699},
    "z790": {"name": "ASUS Prime Z790-P", "socket": "LGA1700", "ram_standards": ["DDR4", "DDR5"], "price": 849},
}

RAM = {
    "ddr5-6000": {"name": "Kingston Fury DDR5 32 GB", "price": 499},
}

GPUS = {
    "rtx-4070": {"name": "GeForce RTX 4070", "price": 2399},
}

DISKS = {
    "nvme-1tb": {"name": "Samsung 990 EVO 1 TB", "price": 399},
}

PSUS = {
    "psu-750": {"name": "be quiet! Pure Power 12 M 750W", "price": 449},
}

COOLING = {
    "fortis-5": {"name": "Endorfy Fortis 5", "price": 199},
}
BUILDER_ONLY_OPTIONS = {
    "cooling": {
        "compatible-cooling": {"name": "Kompatybilne chlodzenie", "price": 199},
    },
}

CASES = {
    "regnum-400": {"name": "Endorfy Regnum 400 ARGB", "price": 299},
}

COMPONENTS = {
    "cpu": CPUS,
    "motherboard": MOTHERBOARDS,
    "ram": RAM,
    "gpu": GPUS,
    "disk": DISKS,
    "psu": PSUS,
    "cooling": COOLING,
    "case": CASES,
}
REQUIRED_TYPES = tuple(COMPONENTS)
POWER_REQUIREMENTS = {
    "ryzen-5-7600": 105,
    "core-i5-14600k": 181,
    "b650": 80,
    "z790": 80,
    "ddr5-6000": 50,
    "ddr4-3200": 50,
    "rtx-4070": 650,
    "nvme-1tb": 10,
    "fortis-5": 5,
    "compatible-cooling": 5,
    "regnum-400": 0,
}
PSU_CAPACITIES = {"psu-750": 750}
PURPOSES = {
    "gaming": "Gaming",
    "programming": "Programowanie",
}
THREE_PART_DEPENDENCIES = {
    ("ryzen-5-7600", "b650", "fortis-5"):
        "wybrane chlodzenie nie jest zgodne z wymaganiami tego polaczenia procesora i plyty glownej",
}


def validate_purpose(purpose: str) -> str:
    if purpose not in PURPOSES:
        raise ValueError("unknown purpose selection")
    return purpose


def component_type_for(model: str) -> str | None:
    if isinstance(model, str) and model.lower().startswith(("ddr4-", "ddr5-")):
        return "ram"
    return next(
        (component_type for component_type, components in COMPONENTS.items() if model in components),
        None,
    )


def ram_standard(ram_id: str | None) -> str | None:
    if not ram_id:
        return None
    standard = ram_id.split("-", 1)[0].upper()
    return standard if standard in {"DDR4", "DDR5"} else None


def selected_component(selected_components: list[dict] | None, component_type: str) -> dict | None:
    return next(
        (component for component in selected_components or [] if component.get("type") == component_type),
        None,
    )


def analyse(
    cpu_id: str,
    motherboard_id: str,
    ram_id: str | None = None,
    selected_components: list[dict] | None = None,
    purpose: str = "gaming",
) -> dict:
    """Return the build summary used by both the browser and the HTTP test."""
    validate_purpose(purpose)
    cpu = CPUS[cpu_id]
    motherboard = MOTHERBOARDS[motherboard_id]
    issues = []
    compatibility_reasons = []
    uncertainty_reasons = []
    if cpu["socket"] != motherboard["socket"]:
        compatibility_reasons.append(
            f"procesor wymaga socketu {cpu['socket']}, a motherboard ma {motherboard['socket']}"
        )
    standard = ram_standard(ram_id)
    selected_ram = selected_component(selected_components, "ram")
    selected_cooling = selected_component(selected_components, "cooling")
    if ram_id is None:
        uncertainty_reasons.append("brak standardu RAM potrzebnego do oceny zgodnosci")
    elif selected_ram and selected_ram.get("model") != ram_id:
        uncertainty_reasons.append(
            f"sprzeczne wartosci RAM: parametr {ram_id} oraz wybrany modul {selected_ram.get('model')}"
        )
    elif standard is None:
        uncertainty_reasons.append(f"nierozpoznany standard RAM w parametrze {ram_id}")
    if standard and standard not in motherboard["ram_standards"]:
        compatibility_reasons.append(
            f"RAM w standardzie {standard} nie jest obslugiwany przez motherboard {motherboard_id}"
        )
    if standard and standard not in cpu["ram_standards"]:
        compatibility_reasons.append(
            f"cpu {cpu_id} nie obsluguje RAM w standardzie {standard}"
        )
    dependency_key = (cpu_id, motherboard_id, selected_cooling.get("model")) if selected_cooling else None
    dependency_reason = THREE_PART_DEPENDENCIES.get(dependency_key)
    if dependency_reason:
        compatibility_reasons.append(
            f"zaleznosc CPU-plyta-chlodzenie: {cpu_id}, {motherboard_id} i "
            f"{selected_cooling['model']} - {dependency_reason}"
        )
    total = cpu["price"] + motherboard["price"]
    components = selected_components or [
        {"model": cpu_id},
        {"model": motherboard_id},
        {"model": ram_id},
    ]
    power_required = sum(POWER_REQUIREMENTS.get(component.get("model"), 0) for component in components)
    psu = next((component for component in components if component.get("type") == "psu"), None)
    psu_power = PSU_CAPACITIES.get(psu.get("model")) if psu else None
    if psu_power is not None and power_required > psu_power:
        issues.append({
            "level": "blocker",
            "message": f"Power: zestaw wymaga {power_required} W, a wybrany PSU zapewnia tylko {psu_power} W.",
        })
    if compatibility_reasons:
        issues.append({
            "level": "blocker",
            "message": "Blokada zgodnosci zestawu: " + "; ".join(compatibility_reasons) + ".",
        })
    if uncertainty_reasons:
        issues.append({
            "level": "warning",
            "message": "Nierozstrzygnieta zgodnosc RAM: " + "; ".join(uncertainty_reasons) + ".",
        })
    if selected_components:
        issues.extend([
            {
                "level": "warning",
                "message": "Ostrzezenie: wybrany zestaw wymaga sprawdzenia wszystkich ofert i ich aktualnych cen.",
            },
            {
                "level": "information",
                "message": f"Informacja: analiza dla celu {PURPOSES[purpose]} obejmuje "
                f"{len(selected_components)} wybranych elementow zestawu.",
            },
        ])
    if uncertainty_reasons:
        status = "undetermined"
    elif any(issue["level"] == "blocker" for issue in issues):
        status = "blocked"
    else:
        status = "compatible"
    return {
        "cpu": cpu,
        "motherboard": motherboard,
        "total": total,
        "status": status,
        "issues": issues,
        "power_required": power_required,
        "psu_power": psu_power,
        "purpose": purpose,
    }


def import_products(payload: dict) -> dict:
    """Build the operator report for a prepared x-kom response."""
    products = payload["products"]
    if not isinstance(products, list):
        raise ValueError("products must be a list")
    for index, product in enumerate(products):
        if not isinstance(product, dict) or "id" not in product or "name" not in product:
            raise ValueError(f"product at index {index} must include id and name")

    catalog = []
    products_by_model = {}
    for offer in products:
        model = offer.get("model")
        if (
            not isinstance(model, str)
            or not model
            or component_type_for(model) is None
            or offer.get("price") is None
        ):
            catalog.append(offer)
            continue
        product = products_by_model.get(model)
        if product is None:
            product = {
                "id": model,
                "name": CPUS.get(model, {}).get("name", offer["name"]),
                "offers": [],
            }
            products_by_model[model] = product
            catalog.append(product)
        product["offers"].append(offer)
    return {"products": catalog, "count": len(catalog)}


def catalog_products(products: list[dict]) -> list[dict]:
    """Expose one buyer-facing item per imported, recognized product."""
    catalog = []
    for product in products:
        offers = product.get("offers")
        component_type = component_type_for(product.get("id"))
        priced_offers = [offer for offer in offers or [] if offer.get("price") is not None]
        if not priced_offers or component_type is None:
            continue
        catalog.append({
            "id": priced_offers[-1]["id"],
            "type": component_type,
            "model": product["id"],
            "name": product["name"],
            "price": priced_offers[-1]["price"],
        })
    return catalog


def catalog_options(catalog: list[dict], imported_products: list[dict] | None = None) -> list[dict]:
    """Add known models to buyer options without changing the imported catalog."""
    options = list(catalog)
    imported_models = {product.get("model") for product in imported_products or []}
    for component_type, components in {**COMPONENTS, **BUILDER_ONLY_OPTIONS}.items():
        existing = [product for product in catalog if product["type"] == component_type]
        if not existing:
            continue
        id_prefix = existing[0]["id"].rsplit("-", 1)[0]
        known_models = {product["model"] for product in existing}
        next_index = len(existing) + 1
        for model, details in components.items():
            if model in known_models or model in imported_models:
                continue
            options.append({
                "id": f"{id_prefix}-{next_index}",
                "type": component_type,
                "model": model,
                "name": details["name"],
                "price": details["price"],
            })
            next_index += 1
    return options


def build_from_selections(selections: dict, catalog: list[dict], purpose: str = "gaming") -> dict:
    if not isinstance(selections, dict):
        raise ValueError("selections must be an object")
    validate_purpose(purpose)
    by_id = {product["id"]: product for product in catalog}
    if set(selections) != set(REQUIRED_TYPES):
        raise ValueError("one selection is required for each component type")
    selected = []
    for component_type in REQUIRED_TYPES:
        product = by_id.get(selections[component_type])
        if product is None or product["type"] != component_type:
            raise ValueError(f"unknown {component_type} selection")
        selected.append(product)
    cpu = next(product for product in selected if product["type"] == "cpu")
    motherboard = next(product for product in selected if product["type"] == "motherboard")
    ram = next(product for product in selected if product["type"] == "ram")
    analysis = analyse(cpu["model"], motherboard["model"], ram["model"], selected, purpose)
    total = sum(product["price"] for product in selected)
    analysis["total"] = total
    return {
        "products": [product["id"] for product in selected],
        "total": total,
        "purpose": purpose,
        "analysis": analysis,
    }


PAGE = """<!doctype html>
<html lang='pl'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Buduj PC</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; background: #101418; color: #edf2f5; }
    body { max-width: 760px; margin: 4rem auto; padding: 0 1.25rem; }
    header { border-left: 4px solid #62e3a0; padding-left: 1rem; margin-bottom: 2rem; }
    h1 { margin: 0; } .lead { color: #a9b6be; }
    main { display: grid; gap: 1rem; } label, .summary { background: #1a2228; border-radius: .5rem; padding: 1rem; }
    select { display: block; width: 100%; margin-top: .5rem; padding: .65rem; border-radius: .3rem; }
     .summary { border: 1px solid #2d3a42; } .ok { color: #62e3a0; } .blocked { color: #ff8d7a; } .undetermined { color: #ffd166; }
    button { padding: .65rem 1rem; border: 0; border-radius: .3rem; cursor: pointer; }
    #import-products { margin: .5rem 0 0; padding-left: 1.25rem; }
  </style>
</head>
<body>
  <header><h1>Buduj PC</h1><p class='lead'>Sprawdz kompatybilnosc zestawu na biezaco.</p></header>
  <main>
    <section id='selectors'></section>
    <section class='summary' aria-live='polite'><label for='purpose'>Przeznaczenie zestawu</label><select id='purpose'><option value='gaming'>Gaming</option><option value='programming'>Programowanie</option></select><strong id='status'>Wybierz czesci...</strong><p id='total'></p><p id='power'></p><div id='issue'></div><ul id='build-products'></ul></section>
    <section class='summary'>
      <button id='import' type='button'>Importuj odpowiedz x-kom</button>
      <p id='import-status' aria-live='polite'></p>
      <ul id='import-products'></ul>
    </section>
    <section class='summary'>
      <h2>Katalog czesci</h2>
      <ul id='catalog-products'></ul>
    </section>
  </main>
  <script>
     const componentDefinitions = [
       ['cpu', 'Procesor'], ['motherboard', 'Plyta glowna'], ['ram', 'Pamiec RAM'],
       ['gpu', 'Karta graficzna'], ['disk', 'Dysk'], ['psu', 'Zasilacz'],
       ['cooling', 'Chlodzenie'], ['case', 'Obudowa'],
     ];
     const requiredTypes = componentDefinitions.map(([type]) => type);
     const typeNames = Object.fromEntries(componentDefinitions);
     const issueLabels = { blocker: 'Blokada', warning: 'Ostrzezenie', information: 'Informacja' };
    let catalog = [];
    let buildCatalog = [];
     const purposeOptions = [...document.querySelectorAll('#purpose option')];
    const preparedResponse = { products: [
      { id: 'offer-1', model: 'ryzen-5-7600', name: 'AMD Ryzen 5 7600 BOX', price: 799, source: 'x-kom' },
      { id: 'offer-2', model: 'ryzen-5-7600', name: 'AMD 7600 3.8 GHz', price: 829, source: 'prepared-shop' }
    ] };
    function renderImportedProducts(products) {
      const list = document.querySelector('#import-products');
      list.replaceChildren();
      products.forEach(product => {
        const item = document.createElement('li');
        item.textContent = `${product.name} (${product.id})`;
        if (product.offers) {
          const offers = document.createElement('div');
          product.offers.forEach(offer => {
            const offerItem = document.createElement('div');
            offerItem.textContent = `${offer.name} - ${offer.price} PLN - ${offer.source}`;
            offers.append(offerItem);
          });
          item.append(offers);
        }
        list.append(item);
      });
    }
    function renderSelectors(products) {
      const container = document.querySelector('#selectors');
      container.replaceChildren();
      requiredTypes.forEach(type => {
        const options = buildCatalog.filter(item => item.type === type);
        const label = document.createElement('label');
        label.textContent = typeNames[type];
        const select = document.createElement('select');
        select.id = type;
        options.forEach(product => {
          const option = document.createElement('option');
          option.value = product.id;
          option.textContent = `${product.name} - ${product.price} PLN`;
          select.append(option);
        });
        select.addEventListener('change', refreshBuild);
        label.append(select);
        container.append(label);
      });
    }
    async function refreshBuild() {
      const selections = Object.fromEntries(requiredTypes.map(type => [type, document.querySelector(`#${type}`).value]));
      if (Object.values(selections).some(value => !value)) return;
      const purpose = document.querySelector('#purpose').value;
      if (!purposeOptions.some(option => option.value === purpose)) return;
      const response = await fetch('/api/build', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selections, purpose })
      });
      const build = await response.json();
       const status = document.querySelector('#status');
       const statusPresentation = {
         compatible: { label: 'Kompatybilny zestaw', className: 'ok' },
         blocked: { label: 'Konfiguracja zablokowana', className: 'blocked' },
         undetermined: { label: 'Nierozstrzygnieta zgodnosc', className: 'undetermined' },
       }[build.analysis.status] || { label: 'Konfiguracja zablokowana', className: 'blocked' };
       status.textContent = statusPresentation.label;
       status.className = statusPresentation.className;
      document.querySelector('#total').textContent = `Suma: ${build.total} PLN`;
      document.querySelector('#power').textContent = `Przeznaczenie: ${build.purpose} | Zapotrzebowanie: ${build.analysis.power_required} W | PSU: ${build.analysis.psu_power} W`;
      const issueList = document.querySelector('#issue');
      issueList.replaceChildren();
       build.analysis.issues.forEach(issue => {
         const item = document.createElement('p');
         item.dataset.level = issue.level;
         item.textContent = `${issueLabels[issue.level]}: ${issue.message}`;
         issueList.append(item);
       });
      const products = document.querySelector('#build-products');
      products.replaceChildren();
      build.products.forEach(id => {
        const product = buildCatalog.find(item => item.id === id);
        const item = document.createElement('li');
        item.textContent = product ? product.name : id;
        products.append(item);
      });
    }
    async function importCatalog() {
      const status = document.querySelector('#import-status');
      status.textContent = 'Importowanie...';
      renderImportedProducts([]);
      try {
        const response = await fetch('/api/import', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(preparedResponse)
        });
        const report = await response.json();
        if (!response.ok) throw new Error(report.error || 'Import nie powiodl sie');
        status.textContent = `Zaimportowano: ${report.count}`;
        renderImportedProducts(report.products);
        await refreshCatalog();
      } catch (error) {
        status.textContent = `Blad importu: ${error.message}`;
      }
    }
    function renderCatalog(products) {
      const list = document.querySelector('#catalog-products');
      list.replaceChildren();
      products.forEach(product => {
        const item = document.createElement('li');
        item.textContent = `${product.type} - ${product.model} - ${product.price} PLN`;
        list.append(item);
      });
    }
    async function refreshCatalog() {
      const response = await fetch('/api/catalog');
      const report = await response.json();
      if (!response.ok) throw new Error(report.error || 'Nie mozna otworzyc katalogu');
        catalog = report.products;
        buildCatalog = report.options;
        renderCatalog(catalog);
        renderSelectors(buildCatalog);
      await refreshBuild();
    }
    document.querySelector('#import').addEventListener('click', importCatalog);
    document.querySelector('#purpose').addEventListener('change', refreshBuild);
    refreshCatalog();
  </script>
</body>
</html>"""


IMPORTED_CATALOG = []
BUILD_CATALOG = []


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        request = urlparse(self.path)
        if request.path == "/":
            self.respond(HTTPStatus.OK, "text/html; charset=utf-8", PAGE.encode())
            return
        if request.path == "/api/analyse":
            query = parse_qs(request.query)
            try:
                result = analyse(query["cpu"][0], query["motherboard"][0], query.get("ram", [None])[0])
            except (KeyError, IndexError):
                self.respond(HTTPStatus.BAD_REQUEST, "application/json", b'{"error":"unknown component"}')
                return
            self.respond(HTTPStatus.OK, "application/json", json.dumps(result).encode())
            return
        if request.path == "/api/catalog":
            self.respond(
                HTTPStatus.OK,
                "application/json",
                json.dumps({"products": IMPORTED_CATALOG, "options": BUILD_CATALOG}).encode(),
            )
            return
        self.respond(HTTPStatus.NOT_FOUND, "text/plain", b"Not found")

    def do_POST(self):
        request = urlparse(self.path)
        if request.path not in ("/api/import", "/api/build"):
            self.respond(HTTPStatus.NOT_FOUND, "text/plain", b"Not found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            if request.path == "/api/build":
                result = build_from_selections(payload.get("selections"), BUILD_CATALOG, payload.get("purpose", "gaming"))
                self.respond(HTTPStatus.OK, "application/json", json.dumps(result).encode())
                return
            report = import_products(payload)
            IMPORTED_CATALOG[:] = catalog_products(report["products"])
            BUILD_CATALOG[:] = catalog_options(IMPORTED_CATALOG, report["products"])
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            body = json.dumps({"error": str(error)}).encode()
            self.respond(HTTPStatus.BAD_REQUEST, "application/json", body)
            return
        self.respond(HTTPStatus.OK, "application/json", json.dumps(report).encode())

    def respond(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Buduj PC: http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
