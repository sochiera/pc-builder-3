#!/usr/bin/env python3
"""Minimal vertical slice for the PC builder."""

import argparse
from datetime import datetime, timedelta, timezone
import itertools
import json
import math
from pathlib import Path
import uuid
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
    "rtx-4070": {"name": "GeForce RTX 4070", "price": 2399, "key_parameter": "12 GB VRAM"},
    "rtx-4080": {"name": "GeForce RTX 4080", "price": 3199, "key_parameter": "16 GB VRAM"},
}
GPU_USEFULNESS = {
    "gaming": {"rtx-4070": 90, "rtx-4080": 95},
    "programming": {"rtx-4070": 45, "rtx-4080": 45},
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

REFRESHED_PRICES = {
    "ryzen-5-7600": 749,
    "core-i5-14600k": 1199,
    "b650": 679,
    "z790": 829,
    "ddr5-6000": 479,
    "rtx-4070": 2299,
    "nvme-1tb": 379,
    "psu-750": 429,
    "psu-900": 429,
    "fortis-5": 189,
    "compatible-cooling": 189,
    "regnum-400": 279,
}
SEARCHED_OFFERS = {
    "ryzen-5-7600": {
        "id": "offer-2",
        "model": "ryzen-5-7600",
        "name": "AMD 7600 3.8 GHz",
        "price": 829,
        "source": "prepared-shop",
        "url": "https://prepared-shop.example/oferta/offer-2",
    },
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
COMPONENTS_BY_TYPE = {
    component_type: {
        **components,
        **BUILDER_ONLY_OPTIONS.get(component_type, {}),
    }
    for component_type, components in COMPONENTS.items()
}
REQUIRED_TYPES = tuple(COMPONENTS)
SAVES_PATH = Path(__file__).with_name(".pc-builder-saves.json")
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
PSU_CAPACITIES = {"psu-750": 750, "psu-900": 900}
PURPOSES = {
    "gaming": "Gaming",
    "programming": "Programowanie",
}
BALANCE_SCORES = {
    "gaming": {
        "cpu": 70,
        "motherboard": 80,
        "ram": 80,
        "gpu": 95,
        "disk": 80,
        "psu": 80,
        "cooling": 80,
        "case": 80,
    },
    "programming": {
        "cpu": 95,
        "motherboard": 80,
        "ram": 85,
        "gpu": 45,
        "disk": 80,
        "psu": 80,
        "cooling": 80,
        "case": 80,
    },
}
THREE_PART_DEPENDENCIES = {
    ("ryzen-5-7600", "b650", "fortis-5"):
        "wybrane chlodzenie nie jest zgodne z wymaganiami tego polaczenia procesora i plyty glownej",
}


def validate_purpose(purpose: str) -> str:
    if purpose not in PURPOSES:
        raise ValueError("unknown purpose selection")
    return purpose


def validate_budget(budget: int | float) -> int | float:
    if (
        isinstance(budget, bool)
        or not isinstance(budget, (int, float))
        or not math.isfinite(budget)
        or budget < 0
    ):
        raise ValueError("budget must be a non-negative number")
    return budget


def validate_catalog_snapshot(snapshot: object) -> None:
    if not isinstance(snapshot, dict):
        raise ValueError("saved catalog snapshot is invalid")
    products = snapshot.get("products")
    options = snapshot.get("options")
    if not isinstance(products, list) or not isinstance(options, list):
        raise ValueError("saved catalog snapshot is invalid")
    for item in products + options:
        if (
            not isinstance(item, dict)
            or not all(isinstance(item.get(field), str) and item[field] for field in ("id", "type", "model", "name"))
            or item.get("type") not in REQUIRED_TYPES
            or isinstance(item.get("price"), bool)
            or not isinstance(item.get("price"), (int, float))
            or not math.isfinite(item["price"])
        ):
            raise ValueError("saved catalog snapshot contains an invalid item")


def load_saves() -> dict:
    if not SAVES_PATH.exists():
        return {}
    with SAVES_PATH.open(encoding="utf-8") as handle:
        saves = json.load(handle)
    if not isinstance(saves, dict):
        raise ValueError("save registry is invalid")
    for saved in saves.values():
        if not isinstance(saved, dict):
            raise ValueError("save registry contains an invalid entry")
        selections = saved.get("selections")
        if not isinstance(selections, dict) or set(selections) != set(REQUIRED_TYPES):
            raise ValueError("save registry contains invalid selections")
        if any(not isinstance(value, str) or not value for value in selections.values()):
            raise ValueError("save registry contains invalid selections")
        validate_purpose(saved.get("purpose"))
        validate_budget(saved.get("budget"))
        try:
            validate_catalog_snapshot(saved.get("catalog"))
        except ValueError as error:
            raise ValueError(f"save registry contains an invalid catalog snapshot: {error}") from error
    return saves


def persist_saves(saves: dict) -> None:
    temporary_path = SAVES_PATH.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as handle:
        json.dump(saves, handle)
    temporary_path.replace(SAVES_PATH)


def save_configuration(payload: dict) -> dict:
    selections = payload.get("selections")
    if not isinstance(selections, dict) or set(selections) != set(REQUIRED_TYPES):
        raise ValueError("one selection is required for each component type")
    if any(not isinstance(value, str) or not value for value in selections.values()):
        raise ValueError("each selection must be a non-empty string")
    options_by_id = {option.get("id"): option for option in BUILD_CATALOG}
    if any(
        selections[component_type] not in options_by_id
        or options_by_id[selections[component_type]].get("type") != component_type
        for component_type in REQUIRED_TYPES
    ):
        raise ValueError("each selection must identify an available component of its type")
    purpose = validate_purpose(payload.get("purpose"))
    budget = validate_budget(payload.get("budget"))

    saves = load_saves()
    save_id = uuid.uuid4().hex
    saves[save_id] = {
        "selections": selections,
        "purpose": purpose,
        "budget": budget,
        "catalog": {"products": IMPORTED_CATALOG, "options": BUILD_CATALOG},
    }
    persist_saves(saves)
    return {"save_id": save_id}


def open_configuration(payload: dict) -> dict:
    save_id = payload.get("save_id")
    if not isinstance(save_id, str) or not save_id:
        raise ValueError("save_id is required")
    saved = saved_configuration(save_id)
    merge_selected_catalog_snapshot(saved.get("catalog"), saved["selections"])
    return {
        "save_id": save_id,
        "selections": saved["selections"],
        "purpose": saved["purpose"],
        "budget": saved["budget"],
    }


def saved_configuration(save_id: str) -> dict:
    if not isinstance(save_id, str) or not save_id:
        raise ValueError("save_id is required")
    saved = load_saves().get(save_id)
    if saved is None:
        raise ValueError("saved build not found")
    return saved


def share_configuration(payload: dict) -> dict:
    save_id = payload.get("save_id")
    saved_configuration(save_id)
    return {"url": f"/share/{save_id}"}


def public_configuration(save_id: str) -> dict:
    saved = saved_configuration(save_id)
    build = build_from_selections(
        saved["selections"],
        saved["catalog"]["options"],
        saved["purpose"],
        saved["budget"],
    )
    return {
        "save_id": save_id,
        "selections": saved["selections"],
        "purpose": saved["purpose"],
        "budget": budget_relation(build["total"], saved["budget"]),
        "total": build["total"],
        "analysis": build["analysis"],
        "build": build,
        "catalog": saved["catalog"],
    }


def component_type_for(model: str) -> str | None:
    if isinstance(model, str) and model.lower().startswith(("ddr4-", "ddr5-")):
        return "ram"
    if model in PSU_CAPACITIES:
        return "psu"
    return next(
        (
            component_type
            for component_type, components in COMPONENTS_BY_TYPE.items()
            if model in components
        ),
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


def balance_assessment(selected_components: list[dict], purpose: str) -> dict:
    scores = BALANCE_SCORES[purpose]
    weakest = min(
        selected_components,
        key=lambda component: scores.get(component.get("type"), 0),
    )
    weakest_type = weakest.get("type", "element")
    weakest_model = weakest.get("model")
    return {
        "rating": scores.get(weakest_type, 0),
        "weakest": weakest_model,
        "explanation": (
            f"{PURPOSES[purpose]}: najslabszym elementem jest {weakest_model}; "
            f"ogranicza bilans zestawu dla celu {PURPOSES[purpose]}"
        ),
    }


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
        if not compatibility_reasons and standard:
            issues.append({
                "level": "information",
                "message": f"Zgodnosc: socket CPU {cpu['socket']} pasuje do plyty {motherboard['socket']}, "
                f"a plyta i procesor obsluguja RAM {standard}.",
            })
    if uncertainty_reasons:
        status = "undetermined"
    elif any(issue["level"] == "blocker" for issue in issues):
        status = "blocked"
    else:
        status = "compatible"
    result = {
        "cpu": cpu,
        "motherboard": motherboard,
        "total": total,
        "status": status,
        "issues": issues,
        "power_required": power_required,
        "psu_power": psu_power,
        "purpose": purpose,
    }
    if selected_components:
        result["balance"] = balance_assessment(selected_components, purpose)
    return result


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
            if "key_parameter" in offer:
                product["key_parameter"] = offer["key_parameter"]
            products_by_model[model] = product
            catalog.append(product)
        product["offers"].append(offer)
    return {"products": catalog, "count": len(catalog)}


def catalog_products(products: list[dict]) -> list[dict]:
    """Expose one buyer-facing item per imported, recognized product."""
    catalog = []
    type_indexes = {}
    imported_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for product in products:
        offers = product.get("offers")
        component_type = component_type_for(product.get("id"))
        priced_offers = [offer for offer in offers or [] if offer.get("price") is not None]
        if not priced_offers or component_type is None:
            continue
        type_indexes[component_type] = type_indexes.get(component_type, 0) + 1
        latest_offer = priced_offers[-1]
        for offer in priced_offers:
            offer.setdefault("price_history", [price_measurement(offer["price"], imported_at)])
        catalog_product = {
            "id": f"{component_type}-{type_indexes[component_type]}",
            "type": component_type,
            "model": product["id"],
            "name": product["name"],
            "price": latest_offer["price"],
            "offers": priced_offers,
            "last_price": latest_offer["price"],
            "last_checked": imported_at,
            "price_direction": "unchanged",
        }
        if "key_parameter" in product:
            catalog_product["key_parameter"] = product["key_parameter"]
        catalog.append(catalog_product)
    return catalog


def price_direction(current: int | float, previous: int | float) -> str:
    if current > previous:
        return "up"
    if current < previous:
        return "down"
    return "unchanged"


def price_measurement(price: int | float, checked_at: str) -> dict:
    return {"price": price, "checked_at": checked_at}


def refresh_product(product_id: str, offer_id: str | None = None) -> dict:
    """Refresh one imported product while preserving its recognized identity."""
    product = next((item for item in IMPORTED_CATALOG if item["model"] == product_id), None)
    if product is None:
        raise ValueError("unknown product")
    if product_id not in REFRESHED_PRICES:
        raise ValueError("unsupported product")
    target_offer = next(
        (offer for offer in product["offers"]
         if offer_id and offer.get("id") == offer_id),
        None,
    ) if offer_id else next(
        (offer for offer in product["offers"] if offer.get("source") == "x-kom"),
        product["offers"][0],
    )
    if target_offer is None:
        raise ValueError("unknown offer")
    checked_at_value = datetime.now(timezone.utc).replace(microsecond=0)
    refreshed_price = REFRESHED_PRICES[product_id]
    history = target_offer.setdefault("price_history", [])
    if not history:
        history.append(price_measurement(target_offer["price"], checked_at_value.isoformat()))
    last_checked = datetime.fromisoformat(history[0]["checked_at"])
    if checked_at_value <= last_checked:
        checked_at_value = last_checked + timedelta(seconds=1)
    checked_at = checked_at_value.isoformat()
    history.append(price_measurement(refreshed_price, checked_at))
    history.sort(key=lambda measurement: measurement["checked_at"], reverse=True)
    latest_measurement = history[0]
    previous_measurement = history[1] if len(history) > 1 else None
    target_offer["price"] = refreshed_price
    target_offer["checked_at"] = checked_at
    product["previous_price"] = previous_measurement["price"]
    product["previous_checked"] = previous_measurement["checked_at"]
    product["price_direction"] = price_direction(latest_measurement["price"], previous_measurement["price"])
    product["price"] = latest_measurement["price"]
    product["last_price"] = latest_measurement["price"]
    product["last_checked"] = latest_measurement["checked_at"]
    return product


def search_product_offer(product_id: str) -> dict:
    """Add the known second-store offer to an imported product once."""
    product = next((item for item in IMPORTED_CATALOG if item["model"] == product_id), None)
    if product is None:
        raise ValueError("unknown product")
    offer = SEARCHED_OFFERS.get(product_id)
    if offer is None:
        raise ValueError("no matching offer")
    existing = next(
        (item for item in product["offers"] if item.get("source") == offer["source"]),
        None,
    )
    if existing is None:
        offer = dict(offer)
        offer["price_history"] = [price_measurement(
            offer["price"], datetime.now(timezone.utc).isoformat(timespec="seconds")
        )]
        product["offers"].append(offer)
    else:
        offer = existing
    product["price"] = product["offers"][-1]["price"]
    sync_build_catalog_product(product)
    return product


def sync_build_catalog_product(product: dict) -> None:
    """Keep build calculations aligned with a refreshed imported product."""
    for option in BUILD_CATALOG:
        if option.get("model") == product["id"]:
            option["price"] = product["price"]
            option["offers"] = product["offers"]


def catalog_options(catalog: list[dict], imported_products: list[dict] | None = None) -> list[dict]:
    """Add known models to buyer options without changing the imported catalog."""
    options = list(catalog)
    used_ids = {product["id"] for product in options}
    imported_models = {product.get("model") for product in imported_products or []}
    for component_type, components in COMPONENTS_BY_TYPE.items():
        existing = [product for product in catalog if product["type"] == component_type]
        if not existing:
            continue
        id_prefix = existing[0]["id"].rsplit("-", 1)[0]
        known_models = {product["model"] for product in existing}
        next_index = len(existing) + 1
        for model, details in components.items():
            if model in known_models or model in imported_models:
                continue
            while f"{id_prefix}-{next_index}" in used_ids:
                next_index += 1
            options.append({
                "id": f"{id_prefix}-{next_index}",
                "type": component_type,
                "model": model,
                "name": details["name"],
                "price": details["price"],
            })
            used_ids.add(f"{id_prefix}-{next_index}")
            next_index += 1
    return options


def compare_gpus(first_id: str, second_id: str, purpose: str, catalog: list[dict]) -> dict:
    """Return public comparison data for exactly two catalog GPUs."""
    validate_purpose(purpose)
    by_id = {product.get("id"): product for product in catalog}
    first = by_id.get(first_id)
    second = by_id.get(second_id)
    if first is None or first.get("type") != "gpu":
        raise ValueError("unknown first GPU selection")
    if second is None or second.get("type") != "gpu":
        raise ValueError("unknown second GPU selection")
    if first_id == second_id:
        raise ValueError("two different GPU selections are required")
    products = [first, second]
    if any(not isinstance(product.get("price"), (int, float)) for product in products):
        raise ValueError("GPU price is unavailable")
    components = [
        {
            "id": product["id"],
            "model": product["model"],
            "name": product["name"],
            "price": product["price"],
            "key_parameter": product.get("key_parameter"),
            "usefulness": GPU_USEFULNESS[purpose].get(product["model"], 0),
        }
        for product in products
    ]
    for component, other in zip(components, reversed(components)):
        component["explanation"] = (
            f"Dla celu {PURPOSES[purpose]} karta {component['name']} ma ocene "
            f"przydatnosci {component['usefulness']}/100, czyli "
            f"{component['usefulness'] - other['usefulness']:+d} pkt "
            f"wzgledem {other['name']}."
        )
    more_expensive, cheaper = sorted(components, key=lambda component: component["price"], reverse=True)
    price_difference = more_expensive["price"] - cheaper["price"]
    return {
        "purpose": purpose,
        "purpose_label": PURPOSES[purpose],
        "components": components,
        "parameter_difference": (
            f"Brak roznic parametru: {first.get('key_parameter') or 'nieznany'}"
            if first.get("key_parameter") == second.get("key_parameter")
            else f"Roznica parametru: {first.get('key_parameter') or 'nieznany'} vs {second.get('key_parameter') or 'nieznany'}"
        ),
        "price_difference": price_difference,
        "price_explanation": (
            f"Roznica ceny: {price_difference} PLN. Drozsza opcja ({more_expensive['name']}) "
            f"ma dla celu {PURPOSES[purpose]} ocene {more_expensive['usefulness']}/100, "
            f"a tansza ({cheaper['name']}) {cheaper['usefulness']}/100."
        ),
    }


def compare_motherboards(
    first_id: str, second_id: str, selections: dict, catalog: list[dict]
) -> dict:
    """Analyse two motherboard replacements without changing the current build."""
    if not isinstance(selections, dict):
        raise ValueError("current build selections are required")
    by_id = {product.get("id"): product for product in catalog}
    first = by_id.get(first_id)
    second = by_id.get(second_id)
    if first is None or first.get("type") != "motherboard":
        raise ValueError("unknown first motherboard selection")
    if second is None or second.get("type") != "motherboard":
        raise ValueError("unknown second motherboard selection")
    if first_id == second_id:
        raise ValueError("two different motherboard selections are required")

    selected = []
    for component_type in REQUIRED_TYPES:
        if component_type == "motherboard":
            continue
        product = by_id.get(selections.get(component_type))
        if product is None or product.get("type") != component_type:
            raise ValueError(f"unknown current {component_type} selection")
        selected.append(product)

    options = []
    for motherboard in (first, second):
        components = selected + [motherboard]
        cpu = next(product for product in components if product["type"] == "cpu")
        ram = next(product for product in components if product["type"] == "ram")
        result = analyse(
            cpu["model"], motherboard["model"], ram["model"], components
        )
        result["total"] = sum(product["price"] for product in components)
        options.append({
            "id": motherboard["id"],
            "model": motherboard["model"],
            "name": motherboard["name"],
            "price": motherboard["price"],
            "total": result["total"],
            "status": result["status"],
            "issues": result["issues"],
        })
    return {"options": options}


def budget_relation(total: int | float, budget: int | float) -> dict:
    difference = budget - total
    return {"limit": budget, "remaining" if difference >= 0 else "overage": abs(difference)}


def build_from_selections(
    selections: dict,
    catalog: list[dict],
    purpose: str = "gaming",
    budget: int | float | None = None,
) -> dict:
    if not isinstance(selections, dict):
        raise ValueError("selections must be an object")
    validate_purpose(purpose)
    if budget is not None:
        validate_budget(budget)
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
    result = {
        "products": [product["id"] for product in selected],
        "total": total,
        "purpose": purpose,
        "analysis": analysis,
    }
    if budget is not None:
        result["budget"] = budget_relation(total, budget)
    return result


def recommend_set(catalog: list[dict], purpose: str, budget: int | float) -> dict:
    """Choose the least expensive complete catalog combination within budget."""
    validate_purpose(purpose)
    validate_budget(budget)
    options = [
        [product for product in catalog if product["type"] == component_type]
        for component_type in REQUIRED_TYPES
    ]
    if any(not products for products in options):
        raise ValueError("complete catalog is required for recommendation")
    candidates = []
    for products in itertools.product(*options):
        total = sum(product["price"] for product in products)
        if total <= budget:
            selections = {product["type"]: product["id"] for product in products}
            candidate = build_from_selections(selections, catalog, purpose, budget)
            if candidate["analysis"]["status"] == "compatible":
                candidates.append(candidate)
    if not candidates:
        raise ValueError("no complete set fits the budget")
    return min(candidates, key=lambda result: result["total"])


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
     #comparison { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
     #comparison > section { background: #1a2228; border: 1px solid #2d3a42; border-radius: .5rem; padding: 1rem; }
     #comparison > p { grid-column: 1 / -1; margin: 0; }
     @media (max-width: 600px) { #comparison { grid-template-columns: 1fr; } #comparison > p { grid-column: auto; } }
   </style>
</head>
<body>
  <header><h1>Buduj PC</h1><p class='lead'>Sprawdz kompatybilnosc zestawu na biezaco.</p></header>
  <main>
    <section id='selectors'></section>
      <section id='base-build' class='summary' aria-live='polite'><label for='purpose'>Przeznaczenie zestawu</label><select id='purpose'><option value='gaming'>Gaming</option><option value='programming'>Programowanie</option></select><label for='budget'>Maksymalny budzet (PLN)</label><input id='budget' type='number' min='0' step='1' placeholder='Podaj budzet'><button id='recommend' type='button'>Dobierz najtanszy zestaw</button><p><button id='save' type='button'>Zapisz zestaw</button><input id='save-id' type='text' placeholder='Identyfikator zapisu'><button id='open' type='button'>Otworz zapis</button><button id='share' type='button'>Udostepnij zestaw</button></p><p id='save-status' aria-live='polite'></p><p id='share-result'></p><p id='budget-summary'></p><strong id='status'>Wybierz czesci...</strong><p id='total'></p><p id='power'></p><p id='balance'></p><div id='issue'></div><ul id='build-products'></ul></section>
     <section id='variants'></section>
    <section class='summary'>
      <button id='import' type='button'>Importuj odpowiedz x-kom</button>
      <p id='import-status' aria-live='polite'></p>
      <ul id='import-products'></ul>
    </section>
     <section class='summary'>
       <h2>Katalog czesci</h2>
       <label for='catalog-search'>Szukaj produktu</label>
       <input id='catalog-search' type='text' placeholder='Wpisz fragment nazwy'>
       <label for='catalog-type'>Typ czesci</label>
       <select id='catalog-type'><option value=''>Wszystkie typy</option></select>
       <ul id='catalog-products'></ul>
     </section>
       <section class='summary'>
         <h2 id='comparison-heading'>Porownaj komponenty</h2>
        <div id='comparison-controls'></div>
        <div id='comparison' aria-live='polite'></div>
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
      const comparisonTypeNames = {
        motherboard: { plural: 'plyty glowne', first: 'Pierwsza plyta glowna', second: 'Druga plyta glowna' },
        gpu: { plural: 'karty graficzne', first: 'Pierwsza karta graficzna', second: 'Druga karta graficzna' },
      };
     const issueLabels = { blocker: 'Blokada', warning: 'Ostrzezenie', information: 'Informacja' };
     let catalog = [];
      let buildCatalog = [];
      let variantState = null;
      let variantRefreshGeneration = 0;
      let shareSaveId = '';
     const purposeOptions = [...document.querySelectorAll('#purpose option')];
     const preparedResponse = { products: [
        { id: 'offer-1', model: 'ryzen-5-7600', name: 'AMD Ryzen 5 7600 BOX', price: 799, source: 'x-kom', url: 'https://x-kom.pl/p/offer-1' },
        { id: 'offer-2', model: 'ryzen-5-7600', name: 'AMD 7600 3.8 GHz', price: 829, source: 'prepared-shop', url: 'https://prepared-shop.example/oferta/offer-2' },
       { id: 'offer-3', model: 'b650', name: 'MSI B650 Gaming Plus WiFi', price: 699, source: 'prepared-shop' },
       { id: 'offer-4', model: 'ddr5-6000', name: 'Kingston Fury DDR5 32 GB', price: 499, source: 'prepared-shop' },
        { id: 'offer-5', model: 'rtx-4070', name: 'GeForce RTX 4070', price: 2399, source: 'prepared-shop', key_parameter: '12 GB VRAM' },
        { id: 'offer-6', model: 'rtx-4080', name: 'GeForce RTX 4080', price: 3199, source: 'prepared-shop', key_parameter: '16 GB VRAM' },
        { id: 'offer-7', model: 'nvme-1tb', name: 'Samsung 990 EVO 1 TB', price: 399, source: 'prepared-shop' },
        { id: 'offer-8', model: 'psu-900', name: 'be quiet! Pure Power 12 M 900W', price: 449, source: 'prepared-shop' },
        { id: 'offer-9', model: 'compatible-cooling', name: 'Kompatybilne chlodzenie', price: 199, source: 'prepared-shop' },
        { id: 'offer-10', model: 'regnum-400', name: 'Endorfy Regnum 400 ARGB', price: 299, source: 'prepared-shop' }
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
         select.addEventListener('change', () => refreshBuild());
        label.append(select);
         container.append(label);
       });
     }
      function clearBuildSummary() {
       const status = document.querySelector('#status');
       status.textContent = 'Wybierz czesci...';
       status.className = '';
       document.querySelector('#budget-summary').textContent = '';
       document.querySelector('#total').textContent = '';
       document.querySelector('#power').textContent = '';
       document.querySelector('#balance').textContent = '';
       document.querySelector('#issue').replaceChildren();
       document.querySelector('#build-products').replaceChildren();
       }
       function showBuildError(message) {
         clearBuildSummary();
         const status = document.querySelector('#status');
         status.textContent = `Blad doboru: ${message}`;
         status.className = 'blocked';
       }
       let buildRefreshGeneration = 0;
       let catalogRefreshGeneration = 0;
      function readBudget() {
          const value = document.querySelector('#budget').value;
          return value === '' ? null : Number(value);
        }
        function currentSelections() {
          return Object.fromEntries(requiredTypes.map(type => [type, document.querySelector(`#${type}`).value]));
        }
        async function refreshBuild(savedBuild = null) {
        const refreshGeneration = ++buildRefreshGeneration;
        const selections = currentSelections();
       if (Object.values(selections).some(value => !value)) {
         clearBuildSummary();
         return;
       }
      const purpose = document.querySelector('#purpose').value;
      if (!purposeOptions.some(option => option.value === purpose)) return;
       const budget = readBudget();
      if (budget !== null && (!Number.isFinite(budget) || budget < 0)) return;
       let build = savedBuild;
        if (!build) {
         const response = await fetch('/api/build', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ selections, purpose, budget })
          });
          build = await response.json();
        }
        if (refreshGeneration !== buildRefreshGeneration) return;
        const currentState = {
          selections: currentSelections(),
          purpose: document.querySelector('#purpose').value,
          budget: readBudget(),
        };
        if (!savedBuild && JSON.stringify(currentState) !== JSON.stringify({ selections, purpose, budget })) {
          refreshBuild();
          return;
        }
        const status = document.querySelector('#status');
       const statusPresentation = {
         compatible: { label: 'Kompatybilny zestaw', className: 'ok' },
         blocked: { label: 'Konfiguracja zablokowana', className: 'blocked' },
         undetermined: { label: 'Nierozstrzygnieta zgodnosc', className: 'undetermined' },
       }[build.analysis.status] || { label: 'Konfiguracja zablokowana', className: 'blocked' };
       status.textContent = statusPresentation.label;
       status.className = statusPresentation.className;
      document.querySelector('#total').textContent = `Suma: ${build.total} PLN`;
      const budgetSummary = document.querySelector('#budget-summary');
      if (build.budget) {
        const relation = build.budget.remaining !== undefined
          ? `Pozostaly budzet: ${build.budget.remaining} PLN`
          : `Przekroczono budzet o: ${build.budget.overage} PLN`;
        budgetSummary.textContent = `Budzet: ${build.budget.limit} PLN | ${relation}`;
      } else {
        budgetSummary.textContent = '';
      }
      document.querySelector('#power').textContent = `Przeznaczenie: ${build.purpose} | Zapotrzebowanie: ${build.analysis.power_required} W | PSU: ${build.analysis.psu_power} W`;
      const balance = document.querySelector('#balance');
      balance.textContent = build.analysis.balance
        ? `Bilans: ocena ${build.analysis.balance.rating}; najslabszy element ${build.analysis.balance.weakest}. ${build.analysis.balance.explanation}`
        : '';
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
       if (build.products.length === requiredTypes.length) renderVariantAction();
       await renderComparison();
      }
      function renderVariantAction() {
        if (document.querySelector('#create-variant')) return;
        const button = document.createElement('button');
        button.id = 'create-variant';
        button.type = 'button';
        button.textContent = 'Utworz wariant';
        button.addEventListener('click', createVariant);
        document.querySelector('#base-build').append(button);
      }
      function renderVariant() {
        const container = document.querySelector('#variants');
        container.replaceChildren();
        if (!variantState) return;
        const section = document.createElement('section');
        section.id = 'variant-1';
        section.className = 'summary';
        const heading = document.createElement('h2');
        heading.textContent = 'Wariant 1';
        section.append(heading);
        requiredTypes.forEach(type => {
          const label = document.createElement('label');
          label.textContent = typeNames[type];
          const select = document.createElement('select');
           select.id = `variant-${type}`;
          buildCatalog.filter(item => item.type === type).forEach(product => {
            select.append(new Option(`${product.name} - ${product.price} PLN`, product.id));
          });
          select.value = variantState.selections[type];
          select.addEventListener('change', () => {
            variantState.selections[type] = select.value;
            refreshVariant();
          });
          label.append(select);
          section.append(label);
        });
        const total = document.createElement('p');
        total.id = 'variant-total';
        total.textContent = variantState.build ? `Suma: ${variantState.build.total} PLN` : '';
        section.append(total);
        const products = document.createElement('ul');
        variantState.build?.products.forEach(id => {
          const product = buildCatalog.find(item => item.id === id);
          const item = document.createElement('li');
          item.textContent = product ? product.name : id;
          products.append(item);
        });
        section.append(products);
        container.append(section);
      }
      function createVariant() {
        if (variantState) return;
        variantState = {
          selections: Object.fromEntries(requiredTypes.map(type => [type, document.querySelector(`#${type}`).value])),
          build: null,
        };
        renderVariant();
        refreshVariant();
      }
      async function refreshVariant() {
        const refreshGeneration = ++variantRefreshGeneration;
        if (!variantState) return;
        const response = await fetch('/api/build', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            selections: variantState.selections,
            purpose: document.querySelector('#purpose').value,
            budget: readBudget(),
          }),
        });
        if (!response.ok) return;
        const build = await response.json();
        if (refreshGeneration !== variantRefreshGeneration) return;
        variantState.build = build;
        renderVariant();
      }
     async function recommendSet() {
       const recommendationGeneration = buildRefreshGeneration;
       const budget = readBudget();
        const purpose = document.querySelector('#purpose').value;
        if (budget === null || !Number.isFinite(budget) || budget < 0) return;
        try {
          const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ purpose, budget })
          });
           const recommendation = await response.json();
           if (!response.ok) throw new Error(recommendation.error || 'Dobor zestawu nie powiodl sie');
           if (recommendationGeneration !== buildRefreshGeneration) return;
           const productsById = Object.fromEntries(buildCatalog.map(product => [product.id, product]));
          const selections = Object.fromEntries(
            recommendation.products.map(id => [productsById[id]?.type, id])
          );
          if (requiredTypes.some(type => !selections[type])) {
            throw new Error('Odpowiedz doboru nie zawiera kompletnego zestawu');
          }
          requiredTypes.forEach(type => {
            const select = document.querySelector(`#${type}`);
            if (select) select.value = selections[type];
          });
          await refreshBuild();
        } catch (error) {
           showBuildError(error.message);
        }
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
         renderImportedProducts(report.products);
          await refreshCatalog();
         status.textContent = `Zaimportowano: ${report.count}`;
       } catch (error) {
         status.textContent = `Blad importu: ${error.message}`;
       }
     }
       async function saveBuild() {
        const budget = readBudget();
        const saveStatus = document.querySelector('#save-status');
        try {
          const response = await fetch('/api/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ selections: currentSelections(), purpose: document.querySelector('#purpose').value, budget })
          });
          const result = await response.json();
          if (!response.ok) throw new Error(result.error || 'Zapis nie powiodl sie');
            shareSaveId = result.save_id;
            document.querySelector('#save-id').value = result.save_id;
           saveStatus.textContent = `Zapisano zestaw: ${result.save_id}`;
        } catch (error) {
          saveStatus.textContent = `Blad zapisu: ${error.message}`;
        }
      }
       async function shareBuild() {
         const saveStatus = document.querySelector('#save-status');
         const shareResult = document.querySelector('#share-result');
          const saveId = document.querySelector('#save-id').value.trim();
         try {
           const response = await fetch('/api/share', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ save_id: saveId }) });
           const result = await response.json();
           if (!response.ok) throw new Error(result.error || 'Udostepnianie nie powiodlo sie');
           const link = document.createElement('a');
           link.id = 'share-link';
           link.href = new URL(result.url, window.location.origin).href;
           link.textContent = link.href;
           shareResult.replaceChildren(link);
           saveStatus.textContent = `Udostepniono zestaw: ${saveId}`;
         } catch (error) {
           shareResult.textContent = '';
           saveStatus.textContent = `Blad udostepniania: ${error.message}`;
         }
       }
       async function loadSharedBuild() {
         const response = await fetch(window.location.pathname, { headers: { Accept: 'application/json' } });
         const result = await response.json();
         if (!response.ok) throw new Error(result.error || 'Nie mozna otworzyc udostepnionego zestawu');
         shareSaveId = result.save_id;
         document.querySelector('#save-id').value = result.save_id;
         document.querySelector('#purpose').value = result.purpose;
         document.querySelector('#budget').value = result.budget.limit;
         catalog = result.catalog.products;
         buildCatalog = result.catalog.options;
         renderCatalogTypeOptions();
         filterCatalog();
         renderSelectors(buildCatalog);
         requiredTypes.forEach(type => {
           const select = document.querySelector(`#${type}`);
           if (select) select.value = result.selections[type];
         });
          await refreshBuild(result.build);
         document.querySelector('#save-status').textContent = `Otworzono udostepniony zestaw: ${result.save_id}`;
       }
       async function openBuild() {
        const saveStatus = document.querySelector('#save-status');
        const saveId = document.querySelector('#save-id').value.trim();
        try {
          const response = await fetch('/api/open', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ save_id: saveId })
          });
          const result = await response.json();
          if (!response.ok) throw new Error(result.error || 'Odczyt nie powiodl sie');
           shareSaveId = result.save_id;
           document.querySelector('#purpose').value = result.purpose;
          document.querySelector('#budget').value = result.budget;
           await refreshCatalog();
          requiredTypes.forEach(type => {
            const select = document.querySelector(`#${type}`);
            if (select) select.value = result.selections[type];
          });
           await refreshBuild();
          saveStatus.textContent = `Otworzono zestaw: ${result.save_id}`;
        } catch (error) {
          saveStatus.textContent = `Blad odczytu: ${error.message}`;
        }
      }
      function appendOffer(item, offer) {
        const details = document.createTextNode(` ${offer.name} - ${offer.price} PLN `);
        if (offer.url) {
          const link = document.createElement('a');
          link.href = offer.url;
          link.textContent = offer.source;
          link.title = `${offer.name} - ${offer.price} PLN`;
          item.append(details, link);
        } else {
          item.append(details, document.createTextNode(offer.source));
        }
        if (offer.price_history?.length) {
          const history = document.createElement('span');
          history.textContent = ` Historia ceny (${offer.source}): ` +
            offer.price_history.map(measurement =>
              `${measurement.price} PLN (${measurement.checked_at})`
            ).join(' | ');
          item.append(history);
        }
      }
      function renderCatalog(products) {
        const list = document.querySelector('#catalog-products');
        list.replaceChildren();
        products.forEach(product => {
          const item = document.createElement('li');
          item.textContent = `${product.type} - ${product.model} - ${product.price} PLN`;
          const refresh = document.createElement('button');
          refresh.type = 'button';
           refresh.textContent = 'Odswiez ceny';
            const selectedOffer = (product.offers || []).find(offer => offer.source === 'x-kom') || product.offers?.[0];
            refresh.addEventListener('click', () => refreshProduct(product.model, selectedOffer?.id));
           item.append(document.createTextNode(' '), refresh);
           if (!(product.offers || []).some(offer => offer.source === 'prepared-shop')) {
             const search = document.createElement('button');
             search.type = 'button';
             search.textContent = 'Szukaj oferty';
             search.addEventListener('click', () => searchProductOffer(product.model));
             item.append(document.createTextNode(' '), search);
           }
            (product.offers || []).forEach(offer => appendOffer(item, offer));
          if (product.last_checked) {
            item.append(document.createTextNode(` Sprawdzono: ${product.last_checked}`));
          }
          if (product.previous_checked) {
            const directionLabels = { up: 'Cena wzrosla', down: 'Cena spadla', unchanged: 'Cena bez zmian' };
            item.append(document.createTextNode(
              ` Ostatnia cena: ${product.last_price} PLN (${product.last_checked})` +
              ` | Poprzednia cena: ${product.previous_price} PLN (${product.previous_checked})` +
              ` | ${directionLabels[product.price_direction] || 'Kierunek ceny nieznany'}`,
            ));
          }
         list.append(item);
       });
      }
       let comparisonRequestGeneration = 0;
       async function renderComparison() {
         const requestGeneration = ++comparisonRequestGeneration;
         const comparison = document.querySelector('#comparison');
        const controls = document.querySelector('#comparison-controls');
           const candidateTypes = ['motherboard', 'gpu'];
           const candidates = candidateTypes.flatMap(type =>
             buildCatalog.filter(product => product.type === type)
           );
         if (!candidates.length) {
           controls.replaceChildren();
           comparison.textContent = 'Brak elementow do porownania.';
          return;
        }
        let firstSelect = document.querySelector('#compare-first');
        let secondSelect = document.querySelector('#compare-second');
        const previousFirst = firstSelect?.value;
        const previousSecond = secondSelect?.value;
        if (!firstSelect || !secondSelect) {
          const firstLabel = document.createElement('label');
           firstLabel.id = 'compare-first-label';
           firstLabel.textContent = 'Pierwszy komponent';
          firstSelect = document.createElement('select');
          firstSelect.id = 'compare-first';
          firstLabel.append(firstSelect);
          const secondLabel = document.createElement('label');
           secondLabel.id = 'compare-second-label';
           secondLabel.textContent = 'Drugi komponent';
          secondSelect = document.createElement('select');
          secondSelect.id = 'compare-second';
          secondLabel.append(secondSelect);
          controls.replaceChildren(firstLabel, secondLabel);
          firstSelect.addEventListener('change', renderComparison);
          secondSelect.addEventListener('change', renderComparison);
        }
        firstSelect.replaceChildren();
        secondSelect.replaceChildren();
          const fillOptions = (select, valueFor) => candidates.forEach(product => {
          const label = `${product.name} - ${product.price} PLN`;
          select.append(new Option(label, valueFor(product)));
        });
         fillOptions(firstSelect, product => product.id);
         fillOptions(secondSelect, product => product.id);
         firstSelect.value = candidates.some(product => product.id === previousFirst)
           ? previousFirst : candidates[0].id;
         secondSelect.value = candidates.some(product => product.id === previousSecond)
           ? previousSecond : (candidates[1] || candidates[0]).id;
           const first = candidates.find(product => product.id === firstSelect.value);
           const second = candidates.find(product => product.id === secondSelect.value);
           const comparisonType = first?.type === second?.type ? first.type : null;
           if (!comparisonType) {
             document.querySelector('#comparison-heading').textContent = 'Porownaj komponenty';
             comparison.textContent = 'Wybierz dwa elementy tego samego typu.';
             return;
           }
           const comparisonNames = comparisonTypeNames[comparisonType];
           document.querySelector('#comparison-heading').textContent = `Porownaj ${comparisonNames.plural}`;
           document.querySelector('#compare-first-label').firstChild.textContent = comparisonNames.first;
           document.querySelector('#compare-second-label').firstChild.textContent = comparisonNames.second;
          const purpose = document.querySelector('#purpose').value;
          const selections = Object.fromEntries(
            requiredTypes.filter(type => type !== comparisonType).map(type => [
              type, document.querySelector(`#${type}`)?.value
            ])
          );
          const response = await fetch('/api/compare', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify(comparisonType === 'motherboard'
              ? { first_motherboard: first.id, second_motherboard: second.id, selections }
              : { first_gpu: first.id, second_gpu: second.id, purpose })
         });
         const result = await response.json();
         if (requestGeneration !== comparisonRequestGeneration) return;
         if (!response.ok) {
           comparison.textContent = `Blad porownania: ${result.error}`;
           return;
         }
         comparison.replaceChildren();
          (result.components || result.options).forEach(product => {
            const card = document.createElement('section');
            card.textContent = result.components
              ? `${product.name} - ${product.price} PLN | ${product.key_parameter || 'Parametr kluczowy niedostepny'} | Przydatnosc dla ${result.purpose_label}: ${product.usefulness}/100`
              : `${product.name} - ${product.price} PLN | Suma zestawu: ${product.total} PLN | ${product.status}`;
            if (result.options) {
              product.issues.forEach(issue => {
                const reason = document.createElement('p');
                reason.textContent = issue.message;
                card.append(reason);
              });
            }
            comparison.append(card);
          });
          if (result.options) return;
         const difference = document.createElement('p');
         difference.textContent = result.parameter_difference;
         comparison.append(difference);
         result.components.forEach(product => {
           const explanation = document.createElement('p');
           explanation.textContent = product.explanation;
           comparison.append(explanation);
         });
         const priceExplanation = document.createElement('p');
         priceExplanation.textContent = result.price_explanation;
        comparison.append(priceExplanation);
      }
        async function refreshProduct(productId, offerId = null) {
        const response = await fetch('/api/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ product_id: productId, ...(offerId ? { offer_id: offerId } : {}) })
        });
         const report = await response.json();
         if (!response.ok) return;
         const selectedValues = Object.fromEntries(
           requiredTypes
             .map(type => [type, document.querySelector(`#${type}`)?.value])
             .filter(([, value]) => value)
         );
          replaceCatalogProduct(report.product);
         renderSelectors(buildCatalog);
         requiredTypes.forEach(type => {
           const select = document.querySelector(`#${type}`);
           const selectedValue = selectedValues[type];
           if (select && selectedValue && [...select.options].some(option => option.value === selectedValue)) {
             select.value = selectedValue;
           }
         });
           await refreshBuild();
           if (variantState) await refreshVariant();
            filterCatalog();
            renderComparison();
       }
       function replaceCatalogProduct(updatedProduct) {
         catalog = catalog.map(product => product.model === updatedProduct.model ? updatedProduct : product);
         buildCatalog = buildCatalog.map(product => product.model === updatedProduct.model
           ? { ...product, price: updatedProduct.price, offers: updatedProduct.offers }
           : product);
       }
       async function searchProductOffer(productId) {
         const response = await fetch('/api/search-offer', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId })
         });
         const report = await response.json();
         if (!response.ok) return;
         replaceCatalogProduct(report.product);
         renderSelectors(buildCatalog);
         filterCatalog();
         renderComparison();
       }
       function filterCatalog() {
       const fragment = document.querySelector('#catalog-search').value.trim().toLowerCase();
       const selectedType = document.querySelector('#catalog-type').value;
       const matches = product => {
         const searchableText = `${product.model} ${product.name}`.toLowerCase();
         return (!fragment || searchableText.includes(fragment))
           && (!selectedType || product.type === selectedType);
       };
       renderCatalog(catalog.filter(matches));
     }
     function renderCatalogTypeOptions() {
       const select = document.querySelector('#catalog-type');
       const selectedType = select.value;
       select.replaceChildren(new Option('Wszystkie typy', ''));
       [...new Set(catalog.map(product => product.type))].forEach(type => {
         select.append(new Option(type, type));
       });
       select.value = [...select.options].some(option => option.value === selectedType) ? selectedType : '';
     }
      async function refreshCatalog() {
        const refreshGeneration = ++catalogRefreshGeneration;
        buildRefreshGeneration += 1;
        const selectedValues = Object.fromEntries(
         requiredTypes
           .map(type => [type, document.querySelector(`#${type}`)?.value])
           .filter(([, value]) => value)
       );
        const response = await fetch('/api/catalog');
        const report = await response.json();
        if (!response.ok) throw new Error(report.error || 'Nie mozna otworzyc katalogu');
        if (refreshGeneration !== catalogRefreshGeneration) return;
        catalog = report.products;
        buildCatalog = report.options;
        renderCatalogTypeOptions();
        filterCatalog();
        renderComparison();
       renderSelectors(buildCatalog);
       requiredTypes.forEach(type => {
         const select = document.querySelector(`#${type}`);
         const selectedValue = selectedValues[type];
         if (select && selectedValue && [...select.options].some(option => option.value === selectedValue)) {
           select.value = selectedValue;
         } else if (select && selectedValue) {
           select.value = '';
         }
       });
       await refreshBuild();
     }
     document.querySelector('#import').addEventListener('click', importCatalog);
     document.querySelector('#catalog-search').addEventListener('input', filterCatalog);
      document.querySelector('#catalog-type').addEventListener('change', filterCatalog);
     document.querySelector('#purpose').addEventListener('change', () => {
       refreshBuild();
       renderComparison();
     });
      document.querySelector('#budget').addEventListener('change', () => refreshBuild());
     document.querySelector('#recommend').addEventListener('click', recommendSet);
      document.querySelector('#save').addEventListener('click', saveBuild);
      document.querySelector('#open').addEventListener('click', openBuild);
      document.querySelector('#share').addEventListener('click', shareBuild);
      if (window.location.pathname.startsWith('/share/')) {
        loadSharedBuild().catch(error => showBuildError(error.message));
      } else {
        refreshCatalog();
      }
  </script>
</body>
</html>"""


IMPORTED_CATALOG = []
BUILD_CATALOG = []


def restore_catalog_snapshot(snapshot: dict | None) -> None:
    validate_catalog_snapshot(snapshot)
    products = snapshot["products"]
    options = snapshot["options"]
    IMPORTED_CATALOG[:] = products
    BUILD_CATALOG[:] = options


def merge_selected_catalog_snapshot(snapshot: dict | None, selections: dict) -> None:
    validate_catalog_snapshot(snapshot)
    products = snapshot["products"]
    options = snapshot["options"]

    saved_options = {option.get("id"): option for option in options}
    selected_options = {}
    for component_type in REQUIRED_TYPES:
        option = saved_options.get(selections.get(component_type))
        if not isinstance(option, dict) or option.get("type") != component_type:
            raise ValueError("saved catalog snapshot does not contain the selected components")
        selected_options[option["id"]] = option

    merged_options = []
    replaced_option_ids = set()
    for option in BUILD_CATALOG:
        replacement = selected_options.get(option.get("id"))
        merged_options.append(replacement if replacement is not None else option)
        if replacement is not None:
            replaced_option_ids.add(option["id"])
    merged_options.extend(
        option for option_id, option in selected_options.items()
        if option_id not in replaced_option_ids
    )

    selected_models = {option["model"] for option in selected_options.values()}
    saved_products = {
        product.get("model"): product
        for product in products
        if product.get("model") in selected_models
    }
    merged_products = []
    replaced_models = set()
    for product in IMPORTED_CATALOG:
        replacement = saved_products.get(product.get("model"))
        merged_products.append(replacement if replacement is not None else product)
        if replacement is not None:
            replaced_models.add(product["model"])
    merged_products.extend(
        product for model, product in saved_products.items()
        if model not in replaced_models
    )

    IMPORTED_CATALOG[:] = merged_products
    BUILD_CATALOG[:] = merged_options


def load_current_catalog() -> None:
    if not SAVES_PATH.exists():
        return
    try:
        saves = load_saves()
        latest_save = next(reversed(saves.values()), None)
        snapshot = latest_save.get("catalog") if isinstance(latest_save, dict) else None
        if not isinstance(snapshot, dict):
            return
        restore_catalog_snapshot(snapshot)
    except (OSError, ValueError, json.JSONDecodeError):
        return


load_current_catalog()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        request = urlparse(self.path)
        if request.path == "/":
            self.respond(HTTPStatus.OK, "text/html; charset=utf-8", PAGE.encode())
            return
        if request.path.startswith("/share/"):
            save_id = request.path.removeprefix("/share/")
            try:
                result = public_configuration(save_id)
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
                self.respond(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", str(error).encode())
                return
            if "text/html" in self.headers.get("Accept", ""):
                self.respond(HTTPStatus.OK, "text/html; charset=utf-8", PAGE.encode())
            else:
                self.respond(HTTPStatus.OK, "application/json", json.dumps(result).encode())
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
        if request.path not in (
            "/api/import", "/api/build", "/api/recommend", "/api/refresh",
            "/api/search-offer", "/api/save", "/api/open", "/api/share", "/api/compare",
        ):
            self.respond(HTTPStatus.NOT_FOUND, "text/plain", b"Not found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            if request.path == "/api/save":
                result = save_configuration(payload)
                self.respond(HTTPStatus.OK, "application/json", json.dumps(result).encode())
                return
            if request.path == "/api/open":
                result = open_configuration(payload)
                self.respond(HTTPStatus.OK, "application/json", json.dumps(result).encode())
                return
            if request.path == "/api/share":
                result = share_configuration(payload)
                self.respond(HTTPStatus.OK, "application/json", json.dumps(result).encode())
                return
            if request.path == "/api/build":
                result = build_from_selections(
                    payload.get("selections"),
                    BUILD_CATALOG,
                    payload.get("purpose", "gaming"),
                    payload.get("budget"),
                )
                self.respond(HTTPStatus.OK, "application/json", json.dumps(result).encode())
                return
            if request.path == "/api/recommend":
                result = recommend_set(
                    BUILD_CATALOG,
                    payload.get("purpose", "gaming"),
                    payload.get("budget"),
                )
                self.respond(HTTPStatus.OK, "application/json", json.dumps(result).encode())
                return
            if request.path == "/api/refresh":
                result = refresh_product(payload.get("product_id"), payload.get("offer_id"))
                sync_build_catalog_product(result)
                self.respond(HTTPStatus.OK, "application/json", json.dumps({"product": result}).encode())
                return
            if request.path == "/api/search-offer":
                result = search_product_offer(payload.get("product_id"))
                self.respond(HTTPStatus.OK, "application/json", json.dumps({"product": result}).encode())
                return
            if request.path == "/api/compare":
                if payload.get("first_motherboard") or payload.get("second_motherboard"):
                    result = compare_motherboards(
                        payload.get("first_motherboard"),
                        payload.get("second_motherboard"),
                        payload.get("selections"),
                        BUILD_CATALOG,
                    )
                else:
                    result = compare_gpus(
                        payload.get("first_gpu"),
                        payload.get("second_gpu"),
                        payload.get("purpose", "gaming"),
                        BUILD_CATALOG,
                    )
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
