# Pruebas · Tests

Pruebas automáticas de Non-Synapse-Mouse. Se ejecutan en Linux con una pantalla virtual
(Xvfb); no necesitan ratón.

## Requisitos
```
sudo apt install python3-tk xvfb
pip install hidapi pillow pystray pyflakes
```
(`harness.py` y `simharness.py` cargan las clases de menú de `pystray` desde
`/usr/local/lib/python3.12/dist-packages/pystray`; cambia esa ruta si la tuya es otra.)

## Dos tipos de prueba
- **`t_*.py`** — interfaz y lógica con un ratón falso de alto nivel (`harness.py`).
- **`s_*.py`** — uso real con un **ratón simulado a nivel de protocolo** (`sim.py` +
  `simharness.py`): el programa usa su `RazerMouse` y su `ButtonListener` de verdad, y el
  simulador contesta a los informes HID de 90 bytes, con fallos de receptor a la carta.

## Ejecutar
```
xvfb-run -a python3 t_func.py              # 57 comprobaciones de la interfaz
xvfb-run -a python3 s_full.py              # 11 escenarios de uso real (unos 3 min)
xvfb-run -a python3 s_full.py control sleep # solo algunos escenarios
SOAK=300 xvfb-run -a python3 s_more.py     # asistente, luces, bandeja... y 5 min de uso intensivo
SC=zero xvfb-run -a python3 s_batt0.py     # bateria al arrancar (zero|stale|timeout|busy|all)
SC=busy LAT=0.03 xvfb-run -a python3 s_lag.py   # mide los tirones de la ventana
python3 t_core.py ; python3 t_update.py   # sin pantalla
xvfb-run -a python3 t_mv.py                # modo Mediavida (55 comprobaciones; falla si toca la red)
```
`NSM_SRC=/ruta/a/otra/version.py` prueba otra versión del programa (útil para comparar).

Archivos de apoyo: `t_v14shots.py`, `t_final_shots.py`, `t_shots.py` (capturas),
`make_icon.py` (icono), `t_dbg.py`, `pt.py`, `t_open.py`, `t_sb.py` (diagnóstico).
