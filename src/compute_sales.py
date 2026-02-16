#!/usr/bin/env python3
"""
Actividad 5.2 – Ejercicio 2: Compute Sales con salida dinámica
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Carpeta global para todos los resultados
RESULTS_DIR = "results"

PRODUCT_KEYS = ("product", "Product", "title", "name", "item")
PRICE_KEYS = ("price", "Price", "cost", "unit_price", "unitPrice")
QTY_KEYS = ("quantity", "Quantity", "qty", "amount", "units")

ReceiptLine = Tuple[str, float, float, float]


@dataclass(frozen=True)
class SaleLine:
    """Línea de venta."""
    product: str
    quantity: float


def load_json(path_str: str) -> Any:
    """Carga JSON."""
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def first_present(data: Dict[str, Any], keys: Iterable[str]) -> Any:
    """Busca key."""
    for key in keys:
        if key in data:
            return data[key]
    return None


def to_float(value: Any) -> Optional[float]:
    """A float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def iter_records(obj: Any) -> Iterable[Any]:
    """Itera registros."""
    if isinstance(obj, list):
        yield from obj
        return
    if isinstance(obj, dict):
        for key in ("items", "records", "sales", "data"):
            val = obj.get(key)
            if isinstance(val, list):
                yield from val
                return
        yield obj
    return


def build_catalogue(raw: Any) -> Tuple[Dict[str, float], List[str]]:
    """Catálogo {prod: precio}."""
    errs, cat = [], {}
    for idx, rec in enumerate(iter_records(raw), start=1):
        if not isinstance(rec, dict):
            errs.append(f"[Cat {idx}] Invalido")
            continue
        prod = first_present(rec, PRODUCT_KEYS)
        price = first_present(rec, PRICE_KEYS)
        if not isinstance(prod, str) or not prod.strip():
            errs.append(f"[Cat {idx}] Vacio: {prod!r}")
            continue
        p_val = to_float(price)
        if p_val is None or p_val < 0:
            errs.append(f"[Cat {idx}] Precio: {price!r}")
            continue
        cat[prod.strip()] = p_val
    if not cat:
        errs.append("Sin catalogo.")
    return cat, errs


def build_sales(raw: Any) -> Tuple[List[SaleLine], List[str]]:
    """Extrae ventas."""
    errs, lines = [], []
    for idx, rec in enumerate(iter_records(raw), start=1):
        if not isinstance(rec, dict):
            errs.append(f"[Sales {idx}] Invalido")
            continue
        prod = first_present(rec, PRODUCT_KEYS)
        qty = first_present(rec, QTY_KEYS)
        if not isinstance(prod, str) or not prod.strip():
            errs.append(f"[Sales {idx}] Invalido: {prod!r}")
            continue
        q_val = to_float(qty)
        if q_val is None:
            errs.append(f"[Sales {idx}] Cant: {qty!r}")
            continue
        lines.append(SaleLine(product=prod.strip(), quantity=q_val))
    if not lines:
        errs.append("Sin ventas.")
    return lines, errs


def compute_receipt(
    catalogue: Dict[str, float],
    sales: List[SaleLine],
) -> Tuple[List[ReceiptLine], float, List[str]]:
    """Recibo."""
    errs, receipt, total = [], [], 0.0
    for idx, sale in enumerate(sales, start=1):
        if sale.quantity <= 0:
            errs.append(f"[Sales {idx}] Qty<=0: {sale.quantity}")
            continue
        if sale.product not in catalogue:
            errs.append(f"[Sales {idx}] No cat: {sale.product}")
            continue
        u_p = catalogue[sale.product]
        sub = u_p * sale.quantity
        receipt.append((sale.product, sale.quantity, u_p, sub))
        total += sub
    return receipt, total, errs


def format_report(
    receipt: List[ReceiptLine],
    total: float,
    errors: List[str],
    elapsed: float,
) -> str:
    """Reporte."""
    lines = ["=== SALES RECEIPT ==="]
    if receipt:
        header = f"{'Product':30} {'Qty':>10} {'Unit':>12} {'Subtotal':>14}"
        lines.append(header)
        lines.append("-" * 70)
        for p, q, u, s in receipt:
            lines.append(f"{p[:30]:30} {q:10.2f} {u:12.2f} {s:14.2f}")
        lines.append("-" * 70)
        lines.append(f"{'TOTAL':>54} {total:14.2f}")
    else:
        lines.append("No sales.")
    lines.append(f"\nElapsed (s): {elapsed:.6f}\n")
    if errors:
        lines.append("=== ERRORS ===")
        lines.extend(errors)
    return "\n".join(lines) + "\n"


def safe_load_json(path: str, label: str) -> Any:
    """Carga JSON."""
    try:
        return load_json(path)
    except (FileNotFoundError, PermissionError, OSError,
            json.JSONDecodeError) as exc:
        msg = f"Err {label}: {exc}"
        raise RuntimeError(msg) from exc


def main(argv: List[str]) -> int:
    """Main."""
    start = time.perf_counter()
    if len(argv) != 3:
        print("Usage: python src/compute_sales.py <p.json> <s.json>")
        return 2
    try:
        cat_raw = safe_load_json(argv[1], "product")
        sal_raw = safe_load_json(argv[2], "sales")
        cat, c_err = build_catalogue(cat_raw)
        sal, s_err = build_sales(sal_raw)
    except RuntimeError as exc:
        print(str(exc))
        return 1
    receipt, total, calc_err = compute_receipt(cat, sal)
    dur = time.perf_counter() - start
    rep = format_report(receipt, total, c_err + s_err + calc_err, dur)
    print(rep)

    # Lógica de guardado dinámico
    output_dir = Path(RESULTS_DIR)
    output_dir.mkdir(exist_ok=True)
    # Toma el nombre del archivo de ventas y le pone prefijo
    sales_file_name = Path(argv[2]).stem
    result_path = output_dir / f"Results_{sales_file_name}.txt"
    result_path.write_text(rep, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
