# Actividad 5.2 – Ejercicio 2: Compute Sales
**Matrícula:** A01796934

Este proyecto consiste en un motor de procesamiento de ventas desarrollado en Python que calcula el costo total de transacciones basadas en catálogos de productos dinámicos y registros de ventas en formato JSON.

---

## 🛠️ Características Principales
* **Arquitectura Modular**: Separación clara entre el código fuente (`src/`), datos de entrada (`TCx/`) y reportes (`results/`).
* **Salida Dinámica**: Generación automática de reportes con nombres descriptivos basados en el archivo de entrada.
* **Calidad de Código**: Cumplimiento del 100% con los estándares **PEP 8**, verificado mediante **Pylint** y **Flake8**.
* **Robustez**: Manejo de errores para archivos JSON mal formados, datos faltantes o discrepancias en el catálogo.

---

## 📂 Estructura del Repositorio
```text
A01796934_A5.2/
├── data_input/        # Catálogos de productos base
├── results/           # Todos los reportes generados automáticamente
├── src/               # Código fuente (compute_sales.py)
├── TC1/               # Escenario de prueba 1 (Ventas)
├── TC2/               # Escenario de prueba 2 (Ventas)
├── TC3/               # Escenario de prueba 3 (Ventas)
└── README.md          # Documentación del proyecto
