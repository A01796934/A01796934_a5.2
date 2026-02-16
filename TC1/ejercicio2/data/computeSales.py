#!/usr/bin/env python3
"""
Actividad 5.2 – Ejercicio 2: Compute Sales

Uso:
    python computeSales.py <product_list.json> <sales.json>

- Calcula total de ventas usando catálogo de precios.
- Genera "recibo" (detalle por producto, cantidad, precio, subtotal).
- Maneja datos inválidos: reporta errores y continúa.
- Imprime y guarda resultados en SalesResults.txt
- Incluye tiempo transcurrido.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

RESULTS_FILENAME = "SalesResults.txt"

# Posibles nombres de campos en el JSON (común en tareas)
PRODUCT_KEYS = (
    "product",
    "Product",
    "title",
    "Title",
    "name",
    "Name",
    "item",
    "Item",
)
PRICE_KEYS = (
    "price",
    "Price",
    "cost",
    "Cost",
    "unit_price",
    "unitPrice",
    "UnitPrice",
)
QTY_KEYS = (
    "quantity",
    "Quantity",
    "qty",
    "Qty",
    "amount",
    "Amount",
    "units",
    "Units",
)

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
    """Devuelve el primer valor encontrado en `data` cuyo key esté en `keys`."""
    for key in keys:
        if key in data:
            return data[key]
    return None


def to_float(value: Any) -> Optional[float]:
    """Convierte `value` a float si es posible; si no, devuelve None."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def iter_records(obj: Any) -> Iterable[Any]:
    """
    Devuelve elementos tipo 'record' de distintas estructuras.

    Soporta:
    - lista => itera elementos
    - dict con 'items'/'records'/'sales'/'data' => itera esa lista
    - dict único => lo considera un record
    """
    if isinstance(obj, list):
        yield from obj
        return

    if isinstance(obj, dict):
        candidate_keys = (
            "items",
            "Items",
            "records",
            "Records",
            "sales",
            "Sales",
            "data",
            "Data",
        )
        for key in candidate_keys:
            if key in obj and isinstance(obj[key], list):
                yield from obj[key]
                return
        yield obj
        return

    return


def build_catalogue(raw: Any) -> Tuple[Dict[str, float], List[str]]:
    """
    Construye un catálogo {product_name: price} desde `raw`.

    Retorna:
        (catalogue, errors)
    """
    errors: List[str] = []
    catalogue: Dict[str, float] = {}

    for idx, record in enumerate(iter_records(raw), start=1):
        if not isinstance(record, dict):
            errors.append(
                f"[Catalogue {idx}] Record inválido (no es objeto JSON)."
            )
            continue

        product = first_present(record, PRODUCT_KEYS)
        price = first_present(record, PRICE_KEYS)

        if not isinstance(product, str) or not product.strip():
            errors.append(
                f"[Catalogue {idx}] Producto inválido o vacío: {product!r}"
            )
            continue

        price_val = to_float(price)
        if price_val is None or price_val < 0:
            errors.append(
                f"[Catalogue {idx}] Precio inválido para '{product}': {price!r}"
            )
            continue

        catalogue[product.strip()] = price_val

    # Caso alterno: dict directo {"A":10,"B":5}
    if not catalogue and isinstance(raw, dict):
        for key, value in raw.items():
            if not isinstance(key, str):
                continue
            price_val = to_float(value)
            if price_val is None or price_val < 0:
                continue
            catalogue[key.strip()] = price_val

    if not catalogue:
        errors.append(
            "No se pudo construir el catálogo: formato inesperado o vacío."
        )

    return catalogue, errors


def build_sales(raw: Any) -> Tuple[List[SaleLine], List[str]]:
    """
    Extrae líneas de venta desde `raw`.

    Retorna:
        (sales_lines, errors)
    """
    errors: List[str] = []
    lines: List[SaleLine] = []

    for idx, record in enumerate(iter_records(raw), start=1):
        if not isinstance(record, dict):
            errors.append(f"[Sales {idx}] Record inválido (no es objeto JSON).")
            continue

        product = first_present(record, PRODUCT_KEYS)
        qty = first_present(record, QTY_KEYS)

        if not isinstance(product, str) or not product.strip():
            errors.append(
                f"[Sales {idx}] Producto inválido o vacío: {product!r}"
            )
            continue

        qty_val = to_float(qty)
        if qty_val is None:
            errors.append(
                f"[Sales {idx}] Cantidad inválida para '{product}': {qty!r}"
            )
            continue

        lines.append(SaleLine(product=product.strip(), quantity=qty_val))

    if not lines:
        errors.append("No se pudieron extraer ventas: formato inesperado o vacío.")

    return lines, errors


def compute_receipt(
    catalogue: Dict[str, float],
    sales: List[SaleLine],
) -> Tuple[List[ReceiptLine], float, List[str]]:
    """
    Genera el recibo a partir del catálogo y las ventas.

    Retorna:
        (receipt_lines, total, errors)
    """
    errors: List[str] = []
    receipt: List[ReceiptLine] = []
    total = 0.0

    for idx, sale in enumerate(sales, start=1):
        if sale.quantity <= 0:
            errors.append(
                f"[Sales {idx}] Cantidad no positiva para '{sale.product}': "
                f"{sale.quantity}"
            )
            continue

        if sale.product not in catalogue:
            errors.append(
                f"[Sales {idx}] Producto no existe en catálogo: '{sale.product}'"
            )
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
    """Formatea el reporte final (recibo + tiempo + errores) como texto."""
    lines: List[str] = ["=== SALES RECEIPT ==="]

    if receipt:
        header = f"{'Product':30} {'Qty':>10} {'Unit':>12} {'Subtotal':>14}"
        lines.append(header)
        lines.append("-" * 70)

        for product, qty, unit, subtotal in receipt:
            lines.append(
                f"{product[:30]:30} {qty:10.2f} {unit:12.2f} {subtotal:14.2f}"
            )

        lines.append("-" * 70)
        lines.append(f"{'TOTAL':>54} {total:14.2f}")
    else:
        lines.append("No valid sales lines to compute a receipt.")
        lines.append(f"TOTAL: {total:.2f}")

    lines.append("")
    lines.append(f"Elapsed time (s): {elapsed:.6f}")
    lines.append("")

    if errors:
        lines.append("=== ERRORS (execution continued) ===")
        lines.extend(errors)
    else:
        lines.append("No errors detected.")

    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str]) -> Tuple[str, str]:
    """Valida argumentos y retorna (product_path, sales_path)."""
    if len(argv) != 3:
        raise ValueError(
            "Usage: python computeSales.py <product_list.json> <sales.json>"
        )
    return argv[1], argv[2]


def safe_load_json(path_str: str, label: str) -> Any:
    """Carga JSON y levanta un error con mensaje claro si falla."""
    try:
        return load_json(path_str)
    except FileNotFoundError as exc:
        raise RuntimeError(f"{label} file not found: '{path_str}'") from exc
    except PermissionError as exc:
        raise RuntimeError(f"No permission to read {label} file: '{path_str}'") from exc
    except OSError as exc:
        raise RuntimeError(f"OS error reading {label} file '{path_str}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in {label} file '{path_str}': {exc}"
        ) from exc


def write_results(report: str, filename: str = RESULTS_FILENAME) -> None:
    """Escribe el reporte a disco."""
    Path(filename).write_text(report, encoding="utf-8")


def main(argv: List[str]) -> int:
    """Punto de entrada del programa."""
    start = time.perf_counter()

    try:
        product_path, sales_path = parse_args(argv)
    except ValueError as exc:
        print(str(exc))
        return 2

    try:
        raw_products = safe_load_json(product_path, label="product")
        raw_sales = safe_load_json(sales_path, label="sales")
    except RuntimeError as exc:
        print(str(exc))
        return 1

    catalogue, cat_errors = build_catalogue(raw_products)
    sales_lines, sales_errors = build_sales(raw_sales)
    receipt, total, calc_errors = compute_receipt(catalogue, sales_lines)

    elapsed = time.perf_counter() - start
    all_errors = cat_errors + sales_errors + calc_errors
    report = format_report(receipt, total, all_errors, elapsed)

    print(report)
    write_results(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
