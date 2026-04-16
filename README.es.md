# Anritsu MS2711D — captura de traza

**Idiomas:** [English](README.md) · [Español](README.es.md)

Utilidades en **Python** para leer la traza espectral actual de un **Anritsu MS2711D** Spectrum Master por **puerto serie** (modo remoto), interpretar el bloque binario y **graficar** o **exportar CSV**.

Manual de programación: [10580-00098 (Anritsu)](https://dl.cdn-anritsu.com/en-us/test-measurement/files/Manuals/Programming-Manual/10580-00098.pdf).

## Contenido del repositorio

| Archivo | Descripción |
|---------|-------------|
| `MS2111D_capture_data.py` | Script original en un solo archivo (flujo simple). |
| `MS2111D_capture_data_optimized.py` | Versión refactorizada: API orientada a objetos, CLI, serie configurable, exportación CSV/imagen. |

## Requisitos

- **Python** 3.9 o superior (el script optimizado evita anotaciones solo válidas en 3.10+, p. ej. `str \| None`).
- Paquetes:
  - `pyserial`
  - `numpy`
  - `matplotlib`

Instalación (ejemplo con entorno virtual):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install pyserial numpy matplotlib
```

## Hardware / sistema operativo

- Conecta el analizador por USB–serie (o adaptador RS-232). En macOS/Linux suele aparecer como `/dev/tty.usbserial-*` o `/dev/ttyUSB0`. Indica la ruta correcta con `--port`.
- El puerto por defecto en el código es `/dev/tty.usbserial-1420` — **cámbialo** según tu equipo.

## Uso (script optimizado)

Ayuda:

```bash
python3 MS2111D_capture_data_optimized.py --help
```

Capturar y mostrar el gráfico (por defecto):

```bash
python3 MS2111D_capture_data_optimized.py
```

Ajustes de serie:

```bash
python3 MS2111D_capture_data_optimized.py --port /dev/tty.usbserial-1410 --baudrate 9600 --timeout 10.0
```

Guardar la traza en CSV (frecuencia en Hz, amplitud en dBm):

```bash
python3 MS2111D_capture_data_optimized.py --save traza.csv
```

Guardar la figura sin abrir ventana:

```bash
python3 MS2111D_capture_data_optimized.py --save traza.png --no-plot
```

### Opciones de línea de comandos

| Opción | Descripción |
|--------|-------------|
| `--port` | Ruta del dispositivo serie (por defecto: `/dev/tty.usbserial-1420`). |
| `--baudrate` | Velocidad en baudios (por defecto: `9600`). |
| `--timeout` | Tiempo máximo de lectura en segundos (por defecto: `10.0`). Súbelo si el buffer de traza llega incompleto. |
| `--save` | Si la ruta termina en `.csv`, guarda datos numéricos; si no, guarda el gráfico con la extensión indicada. |
| `--no-plot` | No abre la ventana interactiva de matplotlib. |

## Solución de problemas

- **`ModuleNotFoundError: No module named 'serial'`** — Instala **pyserial** (`pip install pyserial`).
- **Buffer de traza incompleto** (menos de 2035 bytes) — Aumenta `--timeout` o revisa cable, puerto y baudrate.
- **No se puede abrir el puerto serie** — Comprueba la ruta, permisos y que ningún otro programa use el puerto.
- **Avisos de caché de matplotlib** — Define un directorio escribible, p. ej. `export MPLCONFIGDIR=/ruta/escribible`.

## Licencia / atribución

Ver encabezados en los archivos fuente. Copyright 2026 — Vicente Montecinos Gaete.
