#!/usr/bin/env python3
"""
Actividad 5.2 – Ejercicio 2: Compute Sales

Uso:
    python compute_sales.py <product_list.json> <sales.json>
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

RESULTS_FILENAME = "SalesResults.txt"

# Constantes de búsqueda para robustez en JSON
PRODUCT_KEYS = ("product", "Product", "title", "name", "item")
PRICE_KEYS = ("price", "Price", "cost", "unit_price", "unitPrice")
QTY_KEYS = ("quantity", "Quantity", "qty", "amount", "units")

ReceiptLine = Tuple[str, float, float, float]


@dataclass(frozen=True)
class SaleLine:
    """Representa una línea de venta validada (producto y cantidad)."""
    product: str
    quantity: float


def load_json(path_str: str) -> Any:
    """Carga y retorna el contenido JSON desde un archivo."""
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def first_present(data: Dict[str, Any], keys: Iterable[str]) -> Any:
    """Devuelve el primer valor encontrado en data cuyo key esté en keys."""
    for key in keys:
        if key in data:
            return data[key]
    return None


def to_float(value: Any) -> Optional[float]:
    """Convierte value a float si es posible; si no, devuelve None."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def iter_records(obj: Any) -> Iterable[Any]:
    """Devuelve elementos tipo 'record' de distintas estructuras."""
    if isinstance(obj, list):
        yield from obj
        return

    if isinstance(obj, dict):
        candidate_keys = ("items", "records", "sales", "data")
        for key in candidate_keys:
            # Versión multilínea para evitar E501
            val = obj.get(key)
            if isinstance(val, list):
                yield from val
                return
        yield obj
    return


def build_catalogue(raw: Any) -> Tuple[Dict[str, float], List[str]]:
    """Construye un catálogo {product_name: price} desde raw."""
    errors: List[str] = []
    catalogue: Dict[str, float] = {}

    for idx, record in enumerate(iter_records(raw), start=1):
        if not isinstance(record, dict):
            errors.append(f"[Catalogue {idx}] Record inválido.")
            continue

        product = first_present(record, PRODUCT_KEYS)
        price = first_present(record, PRICE_KEYS)

        if not isinstance(product, str) or not product.strip():
            errors.append(f"[Catalogue {idx}] Producto vacío: {product!r}")
            continue

        p_val = to_float(price)
        if p_val is None or p_val < 0:
            errors.append(f"[Catalogue {idx}] Precio inválido: {price!r}")
            continue

        catalogue[product.strip()] = p_val

    if not catalogue:
        errors.append("Catálogo vacío o formato inesperado.")

    return catalogue, errors


def build_sales(raw: Any) -> Tuple[List[SaleLine], List[str]]:
    """Extrae líneas de venta desde raw."""
    errors: List[str] = []
    lines: List[SaleLine] = []

    for idx, record in enumerate(iter_records(raw), start=1):
        if not isinstance(record, dict):
            errors.append(f"[Sales {idx}] Record inválido.")
            continue

        product = first_present(record, PRODUCT_KEYS)
        qty = first_present(record, QTY_KEYS)

        if not isinstance(product, str) or not product.strip():
            errors.append(f"[Sales {idx}] Producto inválido: {product!r}")
            continue

        qty_val = to_float(qty)
        if qty_val is None:
            errors.append(f"[Sales {idx}] Cantidad inválida: {qty!r}")
            continue

        lines.append(SaleLine(product=product.strip(), quantity=qty_val))

    if not lines:
        errors.append("No se pudieron extraer ventas.")

    return lines, errors


def compute_receipt(
    catalogue: Dict[str, float],
    sales: List[SaleLine],
) -> Tuple[List[ReceiptLine], float, List[str]]:
    """Genera el recibo a partir del catálogo y las ventas."""
    errors: List[str] = []
    receipt: List[ReceiptLine] = []
    total = 0.0

    for idx, sale in enumerate(sales, start=1):
        if sale.quantity <= 0:
            errors.append(f"[Sales {idx}] Qty <= 0: {sale.quantity}")
            continue

        if sale.product not in catalogue:
            errors.append(f"[Sales {idx}] No en catálogo: {sale.product}")
            continue

        unit_price = catalogue[sale.product]
        subtotal = unit_price * sale.quantity
        receipt.append((sale.product, sale.quantity, unit_price, subtotal))
        total += subtotal

    return receipt, total, errors


def format_report(
    receipt: List[ReceiptLine],
    total: float,
    errors: List[str],
    elapsed: float,
) -> str:
    """Formatea el reporte final como texto."""
    lines: List[str] = ["=== SALES RECEIPT ==="]

    if receipt:
        header = f"{'Product':30} {'Qty':>10} {'Unit':>12} {'Subtotal':>14}"
        lines.append(header)
        lines.append("-" * 70)
        for prod, qty, unit, sub in receipt:
            lines.append(f"{prod[:30]:30} {qty:10.2f} {unit:12.2f} {sub:14.2f}")
        lines.append("-" * 70)
        lines.append(f"{'TOTAL':>54} {total:14.2f}")
    else:
        lines.append("No valid sales lines.")

    lines.append(f"\nElapsed time (s): {elapsed:.6f}\n")
    if errors:
        lines.append("=== ERRORS ===")
        lines.extend(errors)
    else:
        lines.append("No errors detected.")

    return "\n".join(lines) + "\n"


def safe_load_json(path_str: str, label: str) -> Any:
    """Carga JSON y levanta un error con mensaje claro si falla."""
    try:
        return load_json(path_str)
    except (FileNotFoundError, PermissionError, OSError, json.JSONDecodeError) \
            as exc:
        raise RuntimeError(f"Error loading {label} '{path_str}': {exc}") from exc


def main(argv: List[str]) -> int:
    """Punto de entrada. Reducido para evitar 'too-many-locals'."""
    start = time.perf_counter()

    if len(argv) != 3:
        print(f"Usage: python {argv[0]} <products.json> <sales.json>")
        return 2

    try:
        # Cargamos directamente en una estructura procesable
        cat, cat_err = build_catalogue(safe_load_json(argv[1], "product"))
        sales, sales_err = build_sales(safe_load_json(argv[2], "sales"))
    except RuntimeError as exc:
        print(str(exc))
        return 1

    receipt, total, calc_err = compute_receipt(cat, sales)
    report = format_report(receipt, total, cat_err + sales_err + calc_err,
                           time.perf_counter() - start)

    print(report)
    Path(RESULTS_FILENAME).write_text(report, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))