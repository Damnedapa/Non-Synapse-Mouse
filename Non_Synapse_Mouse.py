#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Non-Synapse-Mouse - configurador ligero para ratones Razer sin Synapse.
# Copyright (C) 2026 damneddamm
#
# Este programa es software libre: puedes redistribuirlo y/o modificarlo
# bajo los terminos de la Licencia Publica General de GNU (GPL) publicada
# por la Free Software Foundation, version 3 o (a tu eleccion) posterior.
#
# Se distribuye con la esperanza de que sea util, pero SIN NINGUNA GARANTIA;
# ni siquiera la garantia implicita de COMERCIABILIDAD o IDONEIDAD PARA UN
# PROPOSITO PARTICULAR. Consulta la GPL para mas detalles.
#
# Deberias haber recibido una copia de la GPL junto a este programa
# (archivo LICENSE). Si no, visita <https://www.gnu.org/licenses/>.
#
# El protocolo de comunicacion con el raton se basa en la ingenieria inversa
# del proyecto OpenRazer (GPL-2.0): https://github.com/openrazer/openrazer
# Este proyecto NO esta afiliado a Razer Inc. "Razer", "Synapse" y "Chroma"
# son marcas de Razer Inc.
"""
Non-Synapse-Mouse  ·  configurador ligero para ratones Razer (sin Synapse)
==========================================================================
Sustituto minimalista de Razer Synapse. Habla directamente con el ratón por
HID (los mismos "feature reports" que manda Synapse) sin servicios de fondo,
sin nube y sin instalar drivers.

FUNCIONES
  - Selector de modelo (o autodetección de cualquier Razer).
  - Interfaz bilingüe español / inglés con selector arriba a la izquierda.
  - Leer / aplicar DPI (se graba en la memoria interna del ratón → persiste).
  - Cambiar la tasa de sondeo (125 / 500 / 1000 Hz).
  - Leer batería y estado de carga (en modelos inalámbricos).
  - Iluminación del LED (logo): color, intensidad y encendido/apagado.
  - 5 presets de DPI, uno por perfil onboard, con detección y SEGUIMIENTO
    automático del perfil activo y aviso emergente (toast) al cambiar.

SOBRE LOS PERFILES ONBOARD
  El ratón guarda hasta 5 perfiles y se cambia entre ellos con el botón físico.
  El comando para CAMBIAR o LEER el perfil por software no está documentado
  (Razer lo mantiene cerrado), así que el perfil activo se DEDUCE por el DPI:
  se compara el DPI actual con los 5 presets. Con "Empezar seguimiento" se ancla
  el Perfil 1 y, a partir de ahí, cada cambio de DPI se registra en el preset que
  toca. Ver comentarios en run_gui (secciones 7 y 9).

ESTRUCTURA DEL CÓDIGO (para revisar)
  1. Constantes de dispositivo/protocolo:  DEVICES, TX_*, POLL_ARG, LOGO_LED...
  2. build_report() / _normalize():         construir y parsear informes Razer.
  3. class RazerMouse:                       toda la comunicación con el ratón
     (conexión, autodetección del transaction_id, DPI, polling, batería, LED).
  4. load_presets() / save_presets():        persistencia en razer_presets.json.
  5. run_gui():                              interfaz gráfica (Tkinter). Incluye
     el sistema de idiomas (diccionario LANG + tr() + retranslate()); ver la
     docstring de run_gui para el detalle de la internacionalización.
  6. run_cli():                              modo consola de respaldo.

REQUISITOS:  Python 3.8+  y  el paquete "hidapi"
    py -m pip install hidapi
    (instala "hidapi", NO "hid" a secas: son paquetes distintos)

USO:  py Non_Synapse_Mouse.py         → interfaz gráfica
      py Non_Synapse_Mouse.py --cli   → modo consola

Protocolo verificado contra OpenRazer (razermouse_driver.c / razerchromacommon.c).
Escrito sin poder probarlo contra cada modelo: empieza SIEMPRE por
"Detectar / Probar conexión". Si lee bien firmware/DPI/batería, funciona.
"""

import sys
import os
import json
import time
import webbrowser

try:
    import hid  # paquete pip "hidapi"
except ImportError:
    hid = None

# ---------------------------------------------------------------------------
# Base de datos de modelos
#   pids: {product_id: etiqueta_de_conexion}
#   tx  : transaction_id "sugerido" (la autodeteccion lo confirma/corrige)
#   dpi_max, wireless
# ---------------------------------------------------------------------------
RAZER_VID = 0x1532

DEVICES = [
    {"name": "Razer Viper Ultimate",      "pids": {0x007A: "cable", 0x007B: "dongle"}, "dpi_max": 20000, "wireless": True,  "tx": 0xFF},
    {"name": "Razer Viper",               "pids": {0x0078: "cable"},                    "dpi_max": 16000, "wireless": False, "tx": 0xFF},
    {"name": "Razer Viper Mini",          "pids": {0x008A: "cable"},                    "dpi_max": 8500,  "wireless": False, "tx": 0xFF},
    {"name": "Razer Viper 8KHz",          "pids": {0x0091: "cable"},                    "dpi_max": 20000, "wireless": False, "tx": 0xFF},
    {"name": "Razer Viper V2 Pro",        "pids": {0x00A5: "cable", 0x00A6: "dongle"}, "dpi_max": 30000, "wireless": True,  "tx": 0x1F},
    {"name": "Razer Viper Mini SE",       "pids": {0x009E: "cable", 0x009F: "dongle"}, "dpi_max": 30000, "wireless": True,  "tx": 0xFF},
    {"name": "Razer DeathAdder V2",       "pids": {0x0084: "cable"},                    "dpi_max": 20000, "wireless": False, "tx": 0x3F},
    {"name": "Razer DeathAdder V2 Pro",   "pids": {0x007C: "cable", 0x007D: "dongle"}, "dpi_max": 20000, "wireless": True,  "tx": 0x3F},
    {"name": "Razer DeathAdder V2 Mini",  "pids": {0x008C: "cable"},                    "dpi_max": 8500,  "wireless": False, "tx": 0x3F},
    {"name": "Razer DeathAdder Elite",    "pids": {0x005C: "cable"},                    "dpi_max": 16000, "wireless": False, "tx": 0x3F},
    {"name": "Razer DeathAdder V3 Pro",   "pids": {0x00B6: "cable", 0x00B7: "dongle"}, "dpi_max": 30000, "wireless": True,  "tx": 0x1F},
    {"name": "Razer Basilisk V2",         "pids": {0x0085: "cable"},                    "dpi_max": 20000, "wireless": False, "tx": 0x1F},
    {"name": "Razer Basilisk V3",         "pids": {0x0099: "cable"},                    "dpi_max": 26000, "wireless": False, "tx": 0x1F, "led": 0x00},
    {"name": "Razer Basilisk Ultimate",   "pids": {0x0086: "cable", 0x0088: "dongle"}, "dpi_max": 20000, "wireless": True,  "tx": 0x1F},
    {"name": "Razer Basilisk X HyperSpeed","pids": {0x0083: "dongle"},                  "dpi_max": 16000, "wireless": True,  "tx": 0x1F},
    {"name": "Razer Naga Pro",            "pids": {0x008F: "cable", 0x0090: "dongle"}, "dpi_max": 20000, "wireless": True,  "tx": 0x1F},
    {"name": "Razer Naga X",              "pids": {0x0096: "cable"},                    "dpi_max": 18000, "wireless": False, "tx": 0x1F},
    {"name": "Razer Cobra",               "pids": {0x00A3: "cable"},                    "dpi_max": 8500,  "wireless": False, "tx": 0xFF},
    {"name": "Razer Mamba Elite",         "pids": {0x006C: "cable"},                    "dpi_max": 16000, "wireless": False, "tx": 0xFF},
    {"name": "Razer Orochi V2",           "pids": {0x0094: "dongle", 0x0095: "bt"},    "dpi_max": 18000, "wireless": True,  "tx": 0x1F},
    {"name": "Razer Mouse Dock (Viper Ultimate)", "pids": {0x007E: "USB"}, "dpi_max": 0, "wireless": False, "tx": 0x3F, "led": 0x00, "lighting_only": True},
    {"name": "Auto-detectar (cualquier Razer)", "pids": None,                          "dpi_max": 30000, "wireless": True,  "tx": 0xFF},
]

# ---------------------------------------------------------------------------
# Constantes del protocolo
# ---------------------------------------------------------------------------
NOSTORE  = 0x00
VARSTORE = 0x01
LOGO_LED = 0x04          # zona logo (la de la Viper Ultimate)
ZERO_LED = 0x00
POLL_ARG = {1000: 0x01, 500: 0x02, 125: 0x08}
DPI_MIN  = 100
TX_CANDIDATES = [0xFF, 0x1F, 0x3F, 0x08, 0x00]
TX_LIGHT_CANDIDATES = [0x3F, 0x1F, 0xFF, 0x08]   # la iluminacion suele ir en 0x3F/0x1F

STATUS = {0x00: "nuevo", 0x01: "ocupado", 0x02: "OK",
          0x03: "fallo", 0x04: "timeout", 0x05: "no soportado"}

# Carpeta base donde se guarda la configuracion:
#  - ejecutable (.exe de PyInstaller): junto al propio .exe (portable)
#  - script .py normal: junto al script
# (con PyInstaller, __file__ apunta a una carpeta temporal que se borra, por eso
#  se usa sys.executable cuando la app va "congelada")
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(_BASE_DIR, "razer_presets.json")
KOFI_URL = "https://ko-fi.com/damneddamm"


# ---------------------------------------------------------------------------
# Construccion / parseo de informes
# ---------------------------------------------------------------------------
def build_report(command_class, command_id, data_size, args=b"", transaction_id=0xFF):
    r = bytearray(90)
    r[1] = transaction_id
    r[5] = data_size & 0xFF
    r[6] = command_class & 0xFF
    r[7] = command_id & 0xFF
    for i, b in enumerate(args):
        r[8 + i] = b & 0xFF
    crc = 0
    for i in range(2, 88):
        crc ^= r[i]
    r[88] = crc
    return r


def _normalize(raw, command_class):
    raw = bytes(raw)
    for off in (1, 0):
        r = raw[off:off + 90]
        if len(r) >= 8 and r[6] == command_class:
            return r
    return raw[1:91] if len(raw) >= 91 else raw


# Constructores de comandos de LECTURA (seguros para sondear el transaction_id)
READ_BUILDERS = {
    0x00: lambda: build_report(0x00, 0x81, 0x02),                       # firmware
    0x04: lambda: build_report(0x04, 0x85, 0x07, bytes([VARSTORE])),    # dpi
    0x07: lambda: build_report(0x07, 0x80, 0x02),                       # bateria
}


class RazerMouse:
    def __init__(self):
        self.dev = None
        self.model = None
        self.pid = None
        self.tx_cache = {}   # command_class -> transaction_id que funciona

    @property
    def lighting_only(self):
        return bool(self.model and self.model.get("lighting_only", False))

    def _require_mouse(self):
        if self.lighting_only:
            raise RuntimeError("La base de carga solo admite controles de iluminacion.")

    # --- transporte ------------------------------------------------------
    def _raw(self, dev, report, command_class, retries=5):
        last = None
        for _ in range(retries):
            if dev.send_feature_report(bytes([0x00]) + bytes(report)) < 0:
                return None
            time.sleep(0.06)
            raw = dev.get_feature_report(0x00, 91)
            if not raw:
                time.sleep(0.05); continue
            resp = _normalize(raw, command_class)
            if len(resp) < 8:
                time.sleep(0.05); continue
            last = resp
            if resp[0] == 0x01:      # ocupado
                time.sleep(0.08); continue
            return resp
        return last

    def _probe_tx(self, dev, command_class):
        """Prueba transaction_ids con un comando de LECTURA de esa clase.
        Devuelve el tx cuya respuesta hace eco de la clase, o None."""
        builder = READ_BUILDERS.get(command_class)
        if builder is None:
            return None
        base = builder()
        order = TX_CANDIDATES[:]
        if self.model and self.model.get("tx") in order:
            order.remove(self.model["tx"]); order.insert(0, self.model["tx"])
        for tx in order:
            rep = bytearray(base); rep[1] = tx
            crc = 0
            for i in range(2, 88): crc ^= rep[i]
            rep[88] = crc
            resp = self._raw(dev, rep, command_class, retries=2)
            if resp and resp[6] == command_class:
                return tx
        return None

    def _get_tx(self, command_class):
        if command_class in self.tx_cache:
            return self.tx_cache[command_class]
        tx = self._probe_tx(self.dev, command_class)
        if tx is None:
            tx = self.tx_cache.get(0x00, 0xFF)   # fallback
        self.tx_cache[command_class] = tx
        return tx

    def _cmd(self, command_class, command_id, data_size, args=b""):
        if self.dev is None:
            raise RuntimeError("No conectado. Pulsa 'Detectar / Probar conexion'.")
        tx = self._get_tx(command_class)
        resp = self._raw(self.dev, build_report(command_class, command_id, data_size, args, tx), command_class)
        if resp is None:
            raise RuntimeError("El raton no respondio.")
        return resp

    # --- conexion --------------------------------------------------------
    def connect(self, model, log=lambda s: None):
        if hid is None:
            raise RuntimeError("Falta 'hidapi'. Instalalo con:  py -m pip install hidapi")
        self.close()
        self.model = model
        self.tx_cache = {}

        # reunir candidatos (interfaces HID a probar)
        candidates = []
        if model["pids"] is None:               # auto-detectar cualquier Razer
            log("Auto-deteccion: buscando cualquier raton Razer...")
            try:
                for info in hid.enumerate(RAZER_VID, 0):
                    candidates.append((info.get("product_id"), info))
            except Exception as e:
                raise RuntimeError(f"No se pudo enumerar dispositivos Razer: {e}")
        else:
            for pid in model["pids"]:
                try:
                    for info in hid.enumerate(RAZER_VID, pid):
                        candidates.append((pid, info))
                except Exception as e:
                    log(f"  (PID {pid:04X} no enumerable: {e})")

        if not candidates:
            raise RuntimeError("No se encontro el raton. Comprueba que este encendido y conectado.")

        log(f"{len(candidates)} interfaz(es) a probar; buscando la que responde...")
        for pid, info in candidates:
            try:
                d = hid.device(); d.open_path(info["path"])
            except Exception as e:
                log(f"  if {info.get('interface_number')}: no se pudo abrir ({e})"); continue
            tx = self._probe_tx(d, 0x00)         # sondea firmware
            if tx is not None:
                self.dev = d; self.pid = pid; self.tx_cache[0x00] = tx
                if model["pids"] is None:
                    self.model = next((item for item in DEVICES
                                       if item["pids"] and pid in item["pids"]), model)
                conn = ""
                if model["pids"]:
                    conn = model["pids"].get(pid, "")
                log(f"Conectado (PID {pid:04X} {conn}) · transaction_id 0x{tx:02X}")
                return True
            try: d.close()
            except Exception: pass
            log(f"  if {info.get('interface_number')}: sin respuesta valida")

        raise RuntimeError("Interfaces abiertas pero ninguna respondio. Cierra Synapse por completo (servicios incluidos) y reintenta.")

    def close(self):
        if self.dev is not None:
            try: self.dev.close()
            except Exception: pass
        self.dev = None

    # --- comandos --------------------------------------------------------
    def get_firmware(self):
        r = self._cmd(0x00, 0x81, 0x02)
        return r[8], r[9]     # major, minor

    def get_battery(self):
        self._require_mouse()
        r = self._cmd(0x07, 0x80, 0x02)
        pct = round(r[9] / 255 * 100)
        c = self._cmd(0x07, 0x84, 0x02)
        return pct, bool(c[9])

    def get_dpi(self):
        self._require_mouse()
        r = self._cmd(0x04, 0x85, 0x07, bytes([VARSTORE]))
        return (r[9] << 8) | r[10], (r[11] << 8) | r[12]

    def set_dpi(self, dpi_x, dpi_y=None, persist=True):
        self._require_mouse()
        dpi_max = self.model["dpi_max"] if self.model else 30000
        dpi_y = dpi_x if dpi_y is None else dpi_y
        dpi_x = max(DPI_MIN, min(dpi_max, int(dpi_x)))
        dpi_y = max(DPI_MIN, min(dpi_max, int(dpi_y)))
        store = VARSTORE if persist else NOSTORE
        args = bytes([store, (dpi_x >> 8) & 0xFF, dpi_x & 0xFF,
                      (dpi_y >> 8) & 0xFF, dpi_y & 0xFF, 0, 0])
        r = self._cmd(0x04, 0x05, 0x07, args)
        return r[0], (dpi_x, dpi_y)

    def set_poll_rate(self, hz):
        self._require_mouse()
        if hz not in POLL_ARG:
            raise ValueError("La tasa debe ser 125, 500 o 1000 Hz.")
        r = self._cmd(0x00, 0x05, 0x01, bytes([POLL_ARG[hz]]))
        return r[0]

    # --- iluminacion (clase 0x0F; en la Viper Ultimate usa tid 0x3F) -----
    def _cmd_light(self, command_id, data_size, args):
        """Comandos de LED. La clase 0x0F no tiene lectura para sondear el
        transaction_id, asi que se prueba al enviar (el propio 'aplicar' hace
        de sonda): el primer tid cuya respuesta hace eco de la clase 0x0F vale."""
        if self.dev is None:
            raise RuntimeError("No conectado. Pulsa 'Detectar / Probar conexion'.")
        order = list(TX_LIGHT_CANDIDATES)
        if self.model and self.model.get("lighting_only"):
            order.insert(0, self.model["tx"])
        if 0x0F in self.tx_cache:
            order.insert(0, self.tx_cache[0x0F])
        for tx in dict.fromkeys(order):
            resp = self._raw(self.dev, build_report(0x0F, command_id, data_size, args, tx), 0x0F)
            if (resp and len(resp) >= 8 and resp[6] == 0x0F
                    and resp[7] == command_id and resp[0] == 0x02):
                self.tx_cache[0x0F] = tx
                return resp
        raise RuntimeError("El raton no acepto el comando de iluminacion.")

    def set_color(self, r, g, b):
        led = self.model.get("led", LOGO_LED) if self.model else LOGO_LED
        # static: args = [varstore, led, effect=0x01, 0,0, 0x01, R, G, B]
        args = bytes([VARSTORE, led, 0x01, 0x00, 0x00, 0x01, r & 0xFF, g & 0xFF, b & 0xFF])
        return self._cmd_light(0x02, 0x09, args)

    def set_light_off(self):
        led = self.model.get("led", LOGO_LED) if self.model else LOGO_LED
        # none: args = [varstore, led, effect=0x00]
        return self._cmd_light(0x02, 0x06, bytes([VARSTORE, led, 0x00]))

    def set_brightness(self, pct):
        led = self.model.get("led", LOGO_LED) if self.model else LOGO_LED
        val = max(0, min(255, round(int(pct) / 100 * 255)))
        return self._cmd_light(0x04, 0x03, bytes([VARSTORE, led, val]))


# ---------------------------------------------------------------------------
# Persistencia de presets
# ---------------------------------------------------------------------------
def load_presets():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_presets(data):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Interfaz grafica
# ---------------------------------------------------------------------------
def run_gui():
    """Interfaz grafica del programa.

    ARQUITECTURA DE LA INTERFAZ
    ===========================
    - Toda la logica de hardware vive en la clase `RazerMouse` (mas arriba).
      Aqui solo construimos widgets y llamamos a esos metodos.
    - INTERNACIONALIZACION (ES/EN): no se reconstruye la ventana al cambiar de
      idioma. En su lugar:
        * `LANG` es un diccionario con TODOS los textos, en las dos lenguas.
        * `tr(clave, **kw)` devuelve el texto en el idioma activo (con formato).
        * Cada widget con texto se REGISTRA con un pequeno callback en la lista
          `i18n`. Al cambiar de idioma, `retranslate()` ejecuta todos los
          callbacks y reajusta el tamano de la ventana.
        * Las etiquetas dinamicas (estado, bateria, DPI actual, perfil activo)
          guardan su ESTADO en variables `state_*` y tienen una funcion
          `render_*` que pinta ese estado en el idioma actual. Asi, al cambiar
          de idioma, se vuelven a pintar correctamente.
        * El historico del log NO se retraduce (las lineas ya escritas se quedan
          en el idioma en que se generaron); las nuevas salen en el idioma
          activo. Esto es el comportamiento normal de cualquier consola.
    - PESTANAS: dos (ttk.Notebook): "Rendimiento y perfiles" e "Iluminacion".
    - TAMANO FIJO: al final se mide el contenido y se fija la ventana a ese
      tamano exacto (nada se recorta, no se puede redimensionar).
    """
    import tkinter as tk
    from tkinter import ttk, messagebox

    # =====================================================================
    # 1) TEXTOS EN LOS DOS IDIOMAS
    #    Claves compartidas; {..} son huecos que rellena tr(clave, hueco=...).
    # =====================================================================
    LANG = {
        "es": {
            "status_disc": "Sin conectar",
            "status_conn": "Conectado · {name}",
            "model_lbl": "Modelo:",
            "btn_connect": "Detectar / Probar conexión",
            "tab_main": "Rendimiento y perfiles",
            "tab_led": "Iluminación",
            "batt0": "Batería: --",
            "batt": "Batería: {pct}%{chg}",
            "batt_charging": "  (cargando)",
            "batt_na": "Batería: no disponible",
            "kofi_link": "☕ Spot me a protein scoop",
            "btn_read": "Leer",
            "dpi_hdr": "DPI",
            "persist_chk": "Guardar en memoria del ratón (persiste)",
            "dpi_cur0": "Actual: --",
            "dpi_cur": "Actual: {x} × {y} DPI",
            "btn_read_dpi": "Leer DPI",
            "btn_apply_dpi": "Aplicar DPI",
            "poll_lbl": "Tasa de sondeo:",
            "btn_apply": "Aplicar",
            "presets_hdr": "Presets de DPI (uno por perfil)",
            "presets_hint": "Cambia de perfil con el botón del ratón y pulsa el preset del mismo número.",
            "profile": "Perfil",
            "active_idle": "Perfil activo: pulsa «Empezar seguimiento»",
            "active_track": "Perfil activo: Perfil {n}  ({dpi} DPI) · seguimiento activo",
            "active_est": "Perfil activo (estimado): Perfil {n}  ({dpi} DPI)",
            "active_unk": "Perfil activo: desconocido  (DPI {dpi} no coincide con presets)",
            "active_amb": "Perfil activo: ambiguo  (perfiles {nums} comparten {dpi} DPI)",
            "btn_start": "Empezar seguimiento",
            "btn_reanchor": "Reanclar (estoy en Perfil 1)",
            "btn_detect_val": "Detectar (por valor)",
            "btn_apply_active": "Aplicar a perfil activo",
            "chk_auto": "Seguimiento automático en primer plano",
            "chk_notify": "Aviso emergente al cambiar (sondea en 2º plano)",
            "led_color_hdr": "Color fijo del LED",
            "col_red": "Rojo", "col_green": "Verde", "col_blue": "Azul",
            "col_cyan": "Cian", "col_magenta": "Magenta", "col_yellow": "Amarillo",
            "col_white": "Blanco",
            "btn_apply_color": "Aplicar color (del cuadro #RRGGBB)",
            "led_bright_hdr": "Intensidad",
            "btn_apply_bright": "Aplicar intensidad",
            "btn_led_off": "Apagar LED",
            "btn_led_on": "Encender LED",
            "log_lbl": "Registro",
            "about_title": "Acerca de · Non-Synapse-Mouse",
            "about_text": (
                "El Synapse/Chroma de Razer ocupa espacio, es invasivo, consume "
                "RAM y es una mierda. Este no. Y funciona en Windows.\n\n"
                "Cambia los DPI de tu ratón Razer, la iluminación y otras "
                "opciones, así como la visibilidad de la batería y el aviso "
                "emergente de cambio de perfil, sin usar Synapse.\n\nDe nada."
            ),
            "dlg_noconn_title": "Sin conexión",
            "dlg_noconn_msg": "Primero pulsa «Detectar / Probar conexión».",
            "dlg_track_title": "Empezar seguimiento automático",
            "dlg_track_msg": (
                "1) Con el botón de perfil de tu ratón, ve al PERFIL 1 (el "
                "primero del ciclo).\n"
                "2) Cuando estés en el Perfil 1, pulsa Aceptar.\n\n"
                "A partir de ahí, cada vez que cambies de perfil con el botón, "
                "el programa lo registrará y te dirá en cuál estás sin que "
                "toques nada."
            ),
            # --- lineas de log ---
            "log_connecting": "Conectando a: {name}",
            "log_fw": "Firmware: v{a}.{b}",
            "log_fw_err": "(firmware no leído: {e})",
            "log_batt": "Batería {pct}%{chg}",
            "log_dpi_cur": "DPI actual: {x} × {y}",
            "log_dpi_set": "DPI → {x} ({st}){tag}",
            "tag_saved": "  [guardado]",
            "tag_temp": "  [temporal]",
            "log_poll": "Polling → {hz} Hz ({st})",
            "log_preset": "Perfil {n} → {x} DPI ({st}) [guardado]",
            "log_est": "Perfil activo estimado: Perfil {n} (DPI {x})",
            "log_unk": "El DPI actual {x} no coincide con ningún preset.",
            "log_amb": "Ambiguo: perfiles {nums} comparten {x} DPI.",
            "log_track_start": "Seguimiento iniciado. Perfil 1 = {x} DPI. Cambia con el botón y se registrará solo.",
            "log_dups": "Aviso: hay perfiles con el mismo DPI; en esos saltos no podré detectar el cambio.",
            "log_change": "Cambio detectado → Perfil {n} ({x} DPI) [registrado]",
            "log_notify_hint": "Aviso emergente activado: conecta y pulsa «Empezar seguimiento» para que funcione.",
            "log_color": "Color → {hex}",
            "log_bright": "Intensidad → {v}%",
            "log_led_off": "LED apagado",
            "log_led_on": "LED encendido",
            "log_browser_err": "No se pudo abrir el navegador: {e}",
            "log_steps1": "Pasos: 1) elige tu modelo  2) «Detectar / Probar conexión»  3) «Empezar seguimiento» (te dirá qué hacer).",
            "log_steps2": "Después, cambia de perfil con el botón del ratón y se registrará solo.",
            "err_hex": "Color hex inválido (usa #RRGGBB).",
            "toast": "Perfil {n}    ·    {x} DPI",
        },
        "en": {
            "status_disc": "Not connected",
            "status_conn": "Connected · {name}",
            "model_lbl": "Model:",
            "btn_connect": "Detect / Test connection",
            "tab_main": "Performance & profiles",
            "tab_led": "Lighting",
            "batt0": "Battery: --",
            "batt": "Battery: {pct}%{chg}",
            "batt_charging": "  (charging)",
            "batt_na": "Battery: n/a",
            "kofi_link": "☕ Spot me a protein scoop",
            "btn_read": "Read",
            "dpi_hdr": "DPI",
            "persist_chk": "Save to mouse memory (persists)",
            "dpi_cur0": "Current: --",
            "dpi_cur": "Current: {x} × {y} DPI",
            "btn_read_dpi": "Read DPI",
            "btn_apply_dpi": "Apply DPI",
            "poll_lbl": "Polling rate:",
            "btn_apply": "Apply",
            "presets_hdr": "DPI presets (one per profile)",
            "presets_hint": "Switch profile with the mouse button and press the preset with the same number.",
            "profile": "Profile",
            "active_idle": "Active profile: press \u201cStart tracking\u201d",
            "active_track": "Active profile: Profile {n}  ({dpi} DPI) · tracking on",
            "active_est": "Active profile (estimated): Profile {n}  ({dpi} DPI)",
            "active_unk": "Active profile: unknown  (DPI {dpi} doesn't match presets)",
            "active_amb": "Active profile: ambiguous  (profiles {nums} share {dpi} DPI)",
            "btn_start": "Start tracking",
            "btn_reanchor": "Re-anchor (I'm on Profile 1)",
            "btn_detect_val": "Detect (by value)",
            "btn_apply_active": "Apply to active profile",
            "chk_auto": "Auto-tracking while in foreground",
            "chk_notify": "Pop-up on change (polls in background)",
            "led_color_hdr": "Static LED color",
            "col_red": "Red", "col_green": "Green", "col_blue": "Blue",
            "col_cyan": "Cyan", "col_magenta": "Magenta", "col_yellow": "Yellow",
            "col_white": "White",
            "btn_apply_color": "Apply color (from #RRGGBB box)",
            "led_bright_hdr": "Brightness",
            "btn_apply_bright": "Apply brightness",
            "btn_led_off": "Turn LED off",
            "btn_led_on": "Turn LED on",
            "log_lbl": "Log",
            "about_title": "About · Non-Synapse-Mouse",
            "about_text": (
                "Razer's Synapse/Chroma takes up space, is invasive, eats your "
                "RAM and is a piece of crap. This one isn't. And it works on "
                "Windows.\n\n"
                "Change your Razer mouse DPI, lighting and other options, plus "
                "battery readout and a profile-change pop-up, without using "
                "Synapse.\n\nYou're welcome."
            ),
            "dlg_noconn_title": "Not connected",
            "dlg_noconn_msg": "First press \u201cDetect / Test connection\u201d.",
            "dlg_track_title": "Start automatic tracking",
            "dlg_track_msg": (
                "1) Using your mouse's profile button, go to PROFILE 1 (the "
                "first one in the cycle).\n"
                "2) When you're on Profile 1, press OK.\n\n"
                "From then on, every time you switch profile with the button, "
                "the program will record it and tell you which one you're on "
                "without you touching anything."
            ),
            "log_connecting": "Connecting to: {name}",
            "log_fw": "Firmware: v{a}.{b}",
            "log_fw_err": "(firmware not read: {e})",
            "log_batt": "Battery {pct}%{chg}",
            "log_dpi_cur": "Current DPI: {x} × {y}",
            "log_dpi_set": "DPI → {x} ({st}){tag}",
            "tag_saved": "  [saved]",
            "tag_temp": "  [temporary]",
            "log_poll": "Polling → {hz} Hz ({st})",
            "log_preset": "Profile {n} → {x} DPI ({st}) [saved]",
            "log_est": "Estimated active profile: Profile {n} (DPI {x})",
            "log_unk": "Current DPI {x} matches no preset.",
            "log_amb": "Ambiguous: profiles {nums} share {x} DPI.",
            "log_track_start": "Tracking started. Profile 1 = {x} DPI. Switch with the button and it records itself.",
            "log_dups": "Warning: some profiles share the same DPI; those switches can't be detected.",
            "log_change": "Change detected → Profile {n} ({x} DPI) [recorded]",
            "log_notify_hint": "Pop-up enabled: connect and press \u201cStart tracking\u201d to make it work.",
            "log_color": "Color → {hex}",
            "log_bright": "Brightness → {v}%",
            "log_led_off": "LED off",
            "log_led_on": "LED on",
            "log_browser_err": "Couldn't open the browser: {e}",
            "log_steps1": "Steps: 1) pick your model  2) \u201cDetect / Test connection\u201d  3) \u201cStart tracking\u201d (it'll tell you what to do).",
            "log_steps2": "Then switch profile with the mouse button and it records itself.",
            "err_hex": "Invalid hex color (use #RRGGBB).",
            "toast": "Profile {n}    ·    {x} DPI",
        },
    }
    # Nombres de los codigos de estado del raton, por idioma
    STATUS_L = {
        "es": {0: "nuevo", 1: "ocupado", 2: "OK", 3: "fallo", 4: "timeout", 5: "no soportado"},
        "en": {0: "new", 1: "busy", 2: "OK", 3: "fail", 4: "timeout", 5: "unsupported"},
    }

    mouse = RazerMouse()
    presets = load_presets()
    lang = [presets.get("lang", "es")]          # idioma activo (holder mutable)

    def tr(key, **kw):
        """Texto en el idioma activo. Si falta la clave, cae al espanol y luego
        a la propia clave. Aplica .format(**kw) si se pasan huecos."""
        s = LANG.get(lang[0], {}).get(key) or LANG["es"].get(key, key)
        return s.format(**kw) if kw else s

    def st_name(code):
        return STATUS_L.get(lang[0], STATUS_L["es"]).get(code, hex(code))

    # =====================================================================
    # 2) PALETA PLANA PROFESIONAL (colores solidos, sin degradados)
    # =====================================================================
    BG      = "#1e2128"   # fondo de la ventana
    PANEL   = "#252932"   # paneles / pestanas sin seleccionar
    ENTRY   = "#2b303a"   # campos de texto y desplegables
    FG      = "#e4e6eb"   # texto principal
    MUTED   = "#8b919c"   # texto secundario
    ACCENT  = "#3d7dff"   # color de acento (botones)
    ACCENT2 = "#5590ff"   # acento al pasar/pulsar
    BORDER  = "#333844"   # bordes y separadores
    GREEN   = "#3fb950"   # perfil activo / LED encendido / batería alta
    YELL    = "#d9a441"   # batería media
    RED     = "#e5534b"   # batería baja
    LOGBG   = "#161920"   # fondo del log
    LOGFG   = "#9fe3c8"   # texto del log

    root = tk.Tk()
    root.title("Non-Synapse-Mouse")
    root.configure(bg=BG)

    # --- estilos ttk (tema "clam" es el mas personalizable) --------------
    st = ttk.Style()
    try: st.theme_use("clam")
    except Exception: pass
    st.configure(".", background=BG, foreground=FG, fieldbackground=ENTRY,
                 bordercolor=BORDER, font=("Segoe UI", 10))
    st.configure("TFrame", background=BG)
    st.configure("TLabel", background=BG, foreground=FG)
    st.configure("Muted.TLabel", background=BG, foreground=MUTED)
    st.configure("Title.TLabel", background=BG, foreground=FG, font=("Segoe UI", 15, "bold"))
    st.configure("H.TLabel", background=BG, foreground=FG, font=("Segoe UI", 11, "bold"))
    st.configure("Active.TLabel", background=BG, foreground=GREEN, font=("Segoe UI", 10, "bold"))
    st.configure("TButton", background=ACCENT, foreground="#ffffff", relief="flat",
                 borderwidth=0, focuscolor=BG, padding=(8, 4), font=("Segoe UI", 10))
    st.map("TButton", background=[("pressed", ACCENT2), ("active", ACCENT2), ("disabled", PANEL)],
           foreground=[("disabled", MUTED)])
    st.configure("TCheckbutton", background=BG, foreground=FG, focuscolor=BG)
    st.map("TCheckbutton", background=[("active", BG)],
           indicatorcolor=[("selected", ACCENT), ("!selected", ENTRY)])
    st.configure("TEntry", fieldbackground=ENTRY, foreground=FG, bordercolor=BORDER,
                 insertcolor=FG, relief="flat", padding=4)
    st.configure("TCombobox", fieldbackground=ENTRY, background=PANEL, foreground=FG,
                 arrowcolor=FG, bordercolor=BORDER, relief="flat", padding=3)
    st.map("TCombobox", fieldbackground=[("readonly", ENTRY)], foreground=[("readonly", FG)])
    st.configure("Horizontal.TScale", background=ACCENT, troughcolor=ENTRY, borderwidth=0)
    st.configure("TSeparator", background=BORDER)
    st.configure("TNotebook", background=BG, bordercolor=BORDER, borderwidth=0, tabmargins=(6, 6, 6, 0))
    st.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(14, 6),
                 borderwidth=0, focuscolor=BG, font=("Segoe UI", 10, "bold"))
    st.map("TNotebook.Tab", background=[("selected", BG)], foreground=[("selected", FG)])
    st.configure("About.TButton", background=PANEL, foreground=FG, relief="flat",
                 borderwidth=0, focuscolor=BG, padding=(2, 0), font=("Segoe UI", 11, "bold"))
    st.map("About.TButton", background=[("active", ACCENT), ("pressed", ACCENT)],
           foreground=[("active", "#ffffff")])
    st.configure("Kofi.TButton", background="#29abe0", foreground="#ffffff", relief="flat",
                 borderwidth=0, focuscolor=BG, padding=(10, 7), font=("Segoe UI", 10, "bold"))
    st.map("Kofi.TButton", background=[("active", "#3cc0f5"), ("pressed", "#3cc0f5")])

    # el desplegable (popup) del combobox es un Listbox tk: forzarlo al tema
    root.option_add("*TCombobox*Listbox.background", ENTRY)
    root.option_add("*TCombobox*Listbox.foreground", FG)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
    root.option_add("*TCombobox*Listbox.borderWidth", 0)

    # =====================================================================
    # 3) INFRAESTRUCTURA DE IDIOMA (registro + retraduccion)
    # =====================================================================
    i18n = []   # lista de callbacks que reaplican textos al cambiar idioma

    def reg_text(widget, key, **kw):
        """Registra un widget para que su texto siga el idioma. Lo aplica ya
        y devuelve el widget (para poder encadenar .pack())."""
        def apply(): widget.configure(text=tr(key, **kw))
        i18n.append(apply); apply()
        return widget

    def reg(cb):
        """Registra un callback de re-render (para etiquetas dinamicas y
        pestanas) y lo ejecuta una vez."""
        i18n.append(cb); cb()

    def retranslate():
        for cb in i18n:
            try: cb()
            except Exception: pass
        # tras cambiar textos, reajusta el tamano fijo al nuevo contenido
        root.update_idletasks()
        root.geometry(f"{max(480, root.winfo_reqwidth())}x{root.winfo_reqheight()}")

    # =====================================================================
    # 4) CABECERA: titulo, estado, selector de idioma y boton "?"
    # =====================================================================
    ttk.Label(root, text="Non-Synapse-Mouse", style="Title.TLabel").pack(pady=(14, 0))
    status_var = tk.StringVar()
    ttk.Label(root, textvariable=status_var, style="Muted.TLabel").pack()
    ttk.Separator(root).pack(fill="x", padx=12, pady=(8, 0))

    # estado de conexion (dinamico): None -> "sin conectar"; si no, nombre modelo
    state_conn = [None]
    def render_status():
        status_var.set(tr("status_conn", name=state_conn[0]) if state_conn[0] else tr("status_disc"))
    reg(render_status)

    # selector de idioma, arriba a la izquierda
    lang_var = tk.StringVar(value=lang[0].upper())
    lang_combo = ttk.Combobox(root, textvariable=lang_var, values=["ES", "EN"],
                              state="readonly", width=4)
    lang_combo.place(relx=0.0, x=10, y=10, anchor="nw")

    def on_lang(_e=None):
        lang[0] = "es" if lang_var.get() == "ES" else "en"
        presets["lang"] = lang[0]; save_presets(presets)
        retranslate()
    lang_combo.bind("<<ComboboxSelected>>", on_lang)

    # boton "?" (Acerca de), arriba a la derecha
    def show_about():
        messagebox.showinfo(tr("about_title"), tr("about_text"))
    ttk.Button(root, text="?", width=3, style="About.TButton",
               command=show_about).place(relx=1.0, x=-10, y=10, anchor="ne")

    # indicador de BATERIA siempre visible (fuera de las pestanas). Se pulsa
    # sobre el propio texto o sobre el icono para actualizar. Color por nivel.
    batt_supported = [None]                  # None=desconocido, True/False tras conectar
    state_batt = [None]                      # None o (pct, cargando)
    bbar = ttk.Frame(root); bbar.pack(pady=(8, 0))
    batt_var = tk.StringVar()
    batt_lbl = tk.Label(bbar, textvariable=batt_var, bg=BG, fg=MUTED,
                        font=("Segoe UI", 12, "bold"), cursor="hand2")
    batt_lbl.pack(side="left")
    batt_refresh = tk.Label(bbar, text="\u27f3", bg=BG, fg=MUTED,
                            font=("Segoe UI", 12), cursor="hand2")
    batt_refresh.pack(side="left", padx=(6, 0))

    def on_batt_click(_e=None):
        if mouse.dev is not None and batt_supported[0]:
            do_read_battery()
    batt_lbl.bind("<Button-1>", on_batt_click)
    batt_refresh.bind("<Button-1>", on_batt_click)

    # =====================================================================
    # 5) UTILIDADES: log y envoltura de errores
    # =====================================================================
    def log(m):
        logbox.configure(state="normal"); logbox.insert("end", str(m) + "\n")
        logbox.see("end"); logbox.configure(state="disabled"); root.update_idletasks()

    def guard(fn):
        """Envuelve un handler para que cualquier excepcion vaya al log en vez
        de romper la interfaz."""
        def w(*a, **k):
            try: fn(*a, **k)
            except Exception as e: log(f"[ERROR] {e}")
        return w

    def render_batt():
        """Pinta el indicador de bateria segun el estado y colorea por nivel."""
        if not batt_supported[0]:            # None o False -> no disponible / --
            batt_var.set(tr("batt_na") if batt_supported[0] is False else tr("batt0"))
            batt_lbl.configure(fg=MUTED); batt_refresh.configure(fg=MUTED)
            return
        if state_batt[0] is None:
            batt_var.set(tr("batt0")); batt_lbl.configure(fg=MUTED)
            batt_refresh.configure(fg=MUTED); return
        pct, chg = state_batt[0]
        batt_var.set(tr("batt", pct=pct, chg=(tr("batt_charging") if chg else "")))
        col = GREEN if (chg or pct >= 50) else (YELL if pct >= 20 else RED)
        batt_lbl.configure(fg=col); batt_refresh.configure(fg=FG)
    reg(render_batt)

    @guard
    def do_read_battery():
        pct, chg = mouse.get_battery()
        state_batt[0] = (pct, chg); render_batt()
        log(tr("log_batt", pct=pct, chg=(tr("batt_charging") if chg else "")))

    # =====================================================================
    # 6) SELECTOR DE MODELO + CONEXION
    # =====================================================================
    mrow = ttk.Frame(root); mrow.pack(fill="x", padx=12, pady=(10, 2))
    reg_text(ttk.Label(mrow), "model_lbl").pack(side="left")
    model_names = [d["name"] for d in DEVICES]
    model_var = tk.StringVar(value=presets.get("last_model", model_names[0]))
    ttk.Combobox(mrow, textvariable=model_var, values=model_names,
                 state="readonly", width=34).pack(side="left", padx=6)

    def current_model():
        for d in DEVICES:
            if d["name"] == model_var.get():
                return d
        return DEVICES[0]

    @guard
    def do_connect():
        m = current_model()
        log(tr("log_connecting", name=m["name"]))
        mouse.connect(m, log=log)
        m = mouse.model
        state_conn[0] = m["name"]; render_status()
        presets["last_model"] = m["name"]; save_presets(presets)
        dpi_scale.configure(to=max(DPI_MIN, m["dpi_max"]))            # ajusta el slider al modelo
        batt_supported[0] = m["wireless"]               # habilita el indicador
        try:
            fw = mouse.get_firmware(); log(tr("log_fw", a=fw[0], b=fw[1]))
        except Exception as e:
            log(tr("log_fw_err", e=e))
        tracking[0] = False
        current_profile[0] = None
        last_dpi[0] = None
        last_detect[0] = None
        state_active[0] = ("idle",)
        state_dpi[0] = None
        render_active(); render_dpi(); render_track_btn()
        nb.tab(tab_perf, state="disabled" if mouse.lighting_only else "normal")
        if mouse.lighting_only:
            nb.select(tab_led)
        else:
            do_read_dpi()
        if m["wireless"]:
            do_read_battery()
        else:
            render_batt()                               # muestra "no disponible"
        if not mouse.lighting_only:
            detect_active()

    reg_text(ttk.Button(root, command=do_connect), "btn_connect").pack(fill="x", padx=12, pady=4)

    # =====================================================================
    # 7) PESTANAS
    # =====================================================================
    nb = ttk.Notebook(root); nb.pack(fill="both", expand=True, padx=8, pady=6)
    tab_perf = ttk.Frame(nb); nb.add(tab_perf, text="")
    tab_prof = tab_perf                     # perfiles van en la misma pestana
    tab_led  = ttk.Frame(nb); nb.add(tab_led, text="")
    reg(lambda: nb.tab(tab_perf, text=tr("tab_main")))
    reg(lambda: nb.tab(tab_led, text=tr("tab_led")))

    # ---- DPI (la bateria ahora vive arriba, siempre visible) -----------
    reg_text(ttk.Label(tab_perf, style="H.TLabel"), "dpi_hdr").pack(anchor="w", padx=12)
    drow = ttk.Frame(tab_perf); drow.pack(fill="x", padx=12)
    dpi_var = tk.IntVar(value=1600)
    dpi_scale = ttk.Scale(drow, from_=DPI_MIN, to=20000, orient="horizontal",
                          command=lambda v: dpi_var.set(int(float(v))))
    dpi_scale.set(1600); dpi_scale.pack(side="left", fill="x", expand=True)
    ttk.Entry(drow, textvariable=dpi_var, width=7, justify="right").pack(side="left", padx=(8, 0))

    def _sync(*_):
        try: dpi_scale.set(max(DPI_MIN, min(int(dpi_scale.cget("to")), dpi_var.get())))
        except Exception: pass
    dpi_var.trace_add("write", _sync)

    persist_var = tk.BooleanVar(value=True)
    reg_text(ttk.Checkbutton(tab_perf, variable=persist_var), "persist_chk").pack(anchor="w", padx=12, pady=(4, 0))

    cur_var = tk.StringVar()
    ttk.Label(tab_perf, textvariable=cur_var, style="Muted.TLabel").pack(anchor="w", padx=12)
    state_dpi = [None]                       # None o (x, y)
    def render_dpi():
        if state_dpi[0] is None: cur_var.set(tr("dpi_cur0"))
        else: cur_var.set(tr("dpi_cur", x=state_dpi[0][0], y=state_dpi[0][1]))
    reg(render_dpi)

    @guard
    def do_read_dpi():
        x, y = mouse.get_dpi()
        state_dpi[0] = (x, y); render_dpi(); dpi_var.set(x)
        log(tr("log_dpi_cur", x=x, y=y))

    @guard
    def do_set_dpi():
        code, (x, y) = mouse.set_dpi(dpi_var.get(), persist=persist_var.get())
        state_dpi[0] = (x, y); render_dpi()
        log(tr("log_dpi_set", x=x, st=st_name(code),
               tag=(tr("tag_saved") if persist_var.get() else tr("tag_temp"))))

    db = ttk.Frame(tab_perf); db.pack(fill="x", padx=12, pady=4)
    reg_text(ttk.Button(db, command=do_read_dpi), "btn_read_dpi").pack(side="left", expand=True, fill="x", padx=(0, 4))
    reg_text(ttk.Button(db, command=do_set_dpi), "btn_apply_dpi").pack(side="left", expand=True, fill="x", padx=(4, 0))

    ttk.Separator(tab_perf).pack(fill="x", padx=12, pady=6)

    # ---- Polling --------------------------------------------------------
    prow = ttk.Frame(tab_perf); prow.pack(fill="x", padx=12, pady=2)
    reg_text(ttk.Label(prow), "poll_lbl").pack(side="left")
    poll_var = tk.IntVar(value=1000)
    ttk.Combobox(prow, textvariable=poll_var, width=7, state="readonly",
                 values=[125, 500, 1000]).pack(side="left", padx=8)
    ttk.Label(prow, text="Hz").pack(side="left")

    @guard
    def do_set_poll():
        code = mouse.set_poll_rate(int(poll_var.get()))
        log(tr("log_poll", hz=poll_var.get(), st=st_name(code)))
    reg_text(ttk.Button(prow, command=do_set_poll), "btn_apply").pack(side="right")

    ttk.Separator(tab_perf).pack(fill="x", padx=12, pady=6)

    # ---- Presets de perfil ---------------------------------------------
    reg_text(ttk.Label(tab_prof, style="H.TLabel"), "presets_hdr").pack(anchor="w", padx=12, pady=(6, 0))
    reg_text(ttk.Label(tab_prof, style="Muted.TLabel", wraplength=320, justify="left"),
             "presets_hint").pack(anchor="w", padx=12)

    LBL_OFF = MUTED          # color normal de la etiqueta "Perfil N"
    LBL_ON  = GREEN          # verde: perfil activo

    active_var = tk.StringVar()
    ttk.Label(tab_prof, textvariable=active_var, style="Active.TLabel").pack(anchor="w", padx=12, pady=(2, 0))

    preset_vals = presets.get("dpi_presets", [400, 800, 1600, 3200, 6400])
    preset_vars = []
    profile_labels = []      # etiquetas "Perfil N" (para resaltar la activa)
    pf = ttk.Frame(tab_prof); pf.pack(fill="x", padx=12, pady=2)
    for i in range(5):
        row = ttk.Frame(pf); row.pack(fill="x", pady=1)
        lbl = tk.Label(row, width=8, anchor="w", fg=LBL_OFF, bg=BG)
        lbl.pack(side="left"); profile_labels.append(lbl)
        reg(lambda i=i, lbl=lbl: lbl.configure(text=f"{tr('profile')} {i+1}"))
        v = tk.IntVar(value=preset_vals[i] if i < len(preset_vals) else 800)
        preset_vars.append(v)
        ttk.Entry(row, textvariable=v, width=8, justify="right").pack(side="left", padx=4)
        ttk.Label(row, text="DPI").pack(side="left")

        def make_apply(idx):
            @guard
            def apply():
                code, (x, y) = mouse.set_dpi(preset_vars[idx].get(), persist=True)
                state_dpi[0] = (x, y); render_dpi()
                log(tr("log_preset", n=idx + 1, x=x, st=st_name(code)))
                detect_active()   # tras aplicar, ese pasa a ser el activo
            return apply
        reg_text(ttk.Button(row, command=make_apply(i)), "btn_apply_active").pack(side="right")

    def save_preset_vals(*_):
        presets["dpi_presets"] = [v.get() for v in preset_vars]; save_presets(presets)
    for v in preset_vars:
        v.trace_add("write", save_preset_vals)

    # ---- Deteccion / seguimiento del perfil activo ---------------------
    # ESTADO del perfil activo (para poder repintar al cambiar de idioma):
    #   ("idle",)            sin seguimiento
    #   ("track", i, dpi)    seguimiento activo, perfil i
    #   ("est",   i, dpi)    estimado por valor, perfil i
    #   ("unk",   dpi)       DPI actual no coincide con presets
    #   ("amb",   nums, dpi) varios perfiles comparten ese DPI
    state_active = [("idle",)]

    def render_active():
        s = state_active[0]
        for lbl in profile_labels:
            lbl.configure(fg=LBL_OFF)
        if s[0] == "idle":
            active_var.set(tr("active_idle"))
        elif s[0] in ("track", "est"):
            _, i, x = s
            profile_labels[i].configure(fg=LBL_ON)
            active_var.set(tr("active_track" if s[0] == "track" else "active_est", n=i + 1, dpi=x))
        elif s[0] == "unk":
            active_var.set(tr("active_unk", dpi=s[1]))
        elif s[0] == "amb":
            active_var.set(tr("active_amb", nums=s[1], dpi=s[2]))
    reg(render_active)

    last_detect = [None]     # ultima clave detectada (para no spamear el log)

    def detect_active(verbose=True):
        """Deduce el perfil activo comparando el DPI actual con los presets.
        No es lectura directa (Razer no la expone): es inferencia por valor."""
        if mouse.lighting_only:
            return
        try:
            x, _ = mouse.get_dpi()
        except Exception as e:
            if verbose: log(f"[ERROR] {e}")
            return
        matches = [i for i, v in enumerate(preset_vars) if v.get() == x]
        if len(matches) == 1:
            state_active[0] = ("est", matches[0], x); key = ("p", matches[0])
        elif not matches:
            state_active[0] = ("unk", x); key = ("unk", x)
        else:
            nums = ", ".join(str(i + 1) for i in matches)
            state_active[0] = ("amb", nums, x); key = ("amb", tuple(matches))
        render_active()
        # log solo si es manual o si el resultado cambio
        if verbose or key != last_detect[0]:
            if key[0] == "p":
                log(tr("log_est", n=key[1] + 1, x=x))
            elif key[0] == "unk":
                log(tr("log_unk", x=x))
            else:
                log(tr("log_amb", nums=", ".join(str(i + 1) for i in key[1]), x=x))
        last_detect[0] = key

    # ---- Seguimiento automatico (retroalimentacion) --------------------
    tracking = [False]        # ancla puesta -> seguimiento activo
    current_profile = [None]  # indice 0-4 del perfil que creemos activo
    last_dpi = [None]         # ultimo DPI visto (para detectar el cambio)

    def _known_values():
        """{valor_dpi: indice} de los perfiles con valor unico (para resync)."""
        counts = {}
        for v in preset_vars:
            counts[v.get()] = counts.get(v.get(), 0) + 1
        return {v.get(): i for i, v in enumerate(preset_vars) if counts[v.get()] == 1}

    def render_track_btn():
        track_btn.configure(text=tr("btn_reanchor") if tracking[0] else tr("btn_start"))

    def start_tracking():
        """Ancla inicial guiada: el usuario se pone en el Perfil 1 y confirma."""
        if mouse.dev is None:
            messagebox.showwarning(tr("dlg_noconn_title"), tr("dlg_noconn_msg"))
            return
        if not messagebox.askokcancel(tr("dlg_track_title"), tr("dlg_track_msg")):
            return
        try:
            x, _ = mouse.get_dpi()
        except Exception as e:
            log(f"[ERROR] {e}"); return
        current_profile[0] = 0
        last_dpi[0] = x
        preset_vars[0].set(x)                 # registra el DPI del Perfil 1
        tracking[0] = True
        render_track_btn()
        state_active[0] = ("track", 0, x); render_active()
        log(tr("log_track_start", x=x))
        vals = [v.get() for v in preset_vars]  # avisa de DPIs duplicados
        if any(vals.count(d) > 1 for d in vals if d != x):
            log(tr("log_dups"))

    def track_tick():
        """Un ciclo de seguimiento: si el DPI cambio, avanza y registra.
        Devuelve el indice del perfil nuevo si hubo cambio, o None."""
        try:
            x, _ = mouse.get_dpi()
        except Exception:
            return None
        if last_dpi[0] is None:
            last_dpi[0] = x; return None
        if x == last_dpi[0]:
            return None                        # sin cambios
        known = _known_values()
        if x in known:                         # valor ya conocido -> salta ahi
            current_profile[0] = known[x]
        else:                                  # valor nuevo -> avanza y registra
            current_profile[0] = (current_profile[0] + 1) % 5
            preset_vars[current_profile[0]].set(x)
        last_dpi[0] = x
        i = current_profile[0]
        state_active[0] = ("track", i, x); render_active()
        log(tr("log_change", n=i + 1, x=x))
        return i

    def recalibrate_on_focus():
        """Al recuperar el foco, si el DPI actual coincide con un perfil
        conocido, recoloca el contador ahi (auto-correccion silenciosa)."""
        if not tracking[0] or mouse.dev is None or mouse.lighting_only:
            return
        try:
            x, _ = mouse.get_dpi()
        except Exception:
            return
        known = _known_values()
        if x in known:
            current_profile[0] = known[x]; last_dpi[0] = x
            state_active[0] = ("track", known[x], x); render_active()

    drow2 = ttk.Frame(tab_prof); drow2.pack(fill="x", padx=12, pady=(4, 2))
    track_btn = ttk.Button(drow2, command=start_tracking)
    track_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
    reg(render_track_btn)
    reg_text(ttk.Button(drow2, command=detect_active), "btn_detect_val").pack(side="left", expand=True, fill="x", padx=(4, 0))

    auto_var = tk.BooleanVar(value=presets.get("auto_detect", True))
    def _save_auto(*_):
        presets["auto_detect"] = auto_var.get(); save_presets(presets)
    auto_var.trace_add("write", _save_auto)
    reg_text(ttk.Checkbutton(tab_prof, variable=auto_var), "chk_auto").pack(anchor="w", padx=12)

    # ---- Aviso emergente (toast) ---------------------------------------
    toast_win = [None]
    toast_after = [None]

    def show_toast(i):
        text = tr("toast", n=i + 1, x=preset_vars[i].get())
        tw = toast_win[0]
        if tw is None or not tw.winfo_exists():
            tw = tk.Toplevel(root)
            tw.overrideredirect(True)           # sin bordes
            tw.attributes("-topmost", True)     # siempre encima
            try: tw.attributes("-alpha", 0.93)  # semitransparente
            except Exception: pass
            lbl = tk.Label(tw, font=("Segoe UI", 15, "bold"), fg="#eafff0",
                           bg="#2ea043", padx=24, pady=16)
            lbl.pack(); tw._lbl = lbl; toast_win[0] = tw
        tw._lbl.configure(text=text)
        tw.update_idletasks()
        w, h = tw.winfo_reqwidth(), tw.winfo_reqheight()
        sw, sh = tw.winfo_screenwidth(), tw.winfo_screenheight()
        tw.geometry(f"+{sw - w - 28}+{sh - h - 70}")   # esquina inferior derecha
        tw.deiconify(); tw.lift()
        if toast_after[0]:
            try: root.after_cancel(toast_after[0])
            except Exception: pass
        toast_after[0] = root.after(2000, lambda: tw.winfo_exists() and tw.withdraw())

    notify_var = tk.BooleanVar(value=presets.get("notify_popup", False))
    def _save_notify(*_):
        presets["notify_popup"] = notify_var.get(); save_presets(presets)
        if notify_var.get():
            if mouse.dev is None:
                log(tr("log_notify_hint"))
            elif not tracking[0]:
                start_tracking()                # necesita ancla para funcionar
    notify_var.trace_add("write", _save_notify)
    reg_text(ttk.Checkbutton(tab_prof, variable=notify_var), "chk_notify").pack(anchor="w", padx=12)

    # =====================================================================
    # 8) PESTANA ILUMINACION
    # =====================================================================
    reg_text(ttk.Label(tab_led, style="H.TLabel"), "led_color_hdr").pack(anchor="w", padx=12, pady=(12, 2))

    led_color = [list(presets.get("led_color", [0, 255, 0]))]
    led_on = [True]

    def _hex(rgb):
        return "#%02x%02x%02x" % (rgb[0] & 0xFF, rgb[1] & 0xFF, rgb[2] & 0xFF)

    srow = ttk.Frame(tab_led); srow.pack(fill="x", padx=12, pady=2)
    swatch = tk.Label(srow, width=8, height=2, bg=_hex(led_color[0]), relief="flat",
                      bd=0, highlightthickness=1, highlightbackground=BORDER)
    swatch.pack(side="left")
    hex_var = tk.StringVar(value=_hex(led_color[0]))
    ttk.Entry(srow, textvariable=hex_var, width=10).pack(side="left", padx=8)
    ttk.Label(srow, text="(#RRGGBB)", style="Muted.TLabel").pack(side="left")

    def render_onoff():
        onoff_btn.configure(text=tr("btn_led_off") if led_on[0] else tr("btn_led_on"))

    @guard
    def apply_color(rgb=None):
        if rgb is None:                          # color escrito a mano (#RRGGBB)
            t = hex_var.get().strip().lstrip("#")
            if len(t) != 6:
                raise ValueError(tr("err_hex"))
            rgb = [int(t[0:2], 16), int(t[2:4], 16), int(t[4:6], 16)]
        mouse.set_color(*rgb)
        led_color[0] = list(rgb); led_on[0] = True
        swatch.configure(bg=_hex(rgb)); hex_var.set(_hex(rgb))
        presets["led_color"] = list(rgb); save_presets(presets)
        render_onoff()
        log(tr("log_color", hex=_hex(rgb)))

    # paleta rapida: (clave_i18n, color RGB)
    palette = [("col_red", [255, 0, 0]), ("col_green", [0, 255, 0]),
               ("col_blue", [0, 80, 255]), ("col_cyan", [0, 255, 255]),
               ("col_magenta", [255, 0, 255]), ("col_yellow", [255, 190, 0]),
               ("col_white", [255, 255, 255])]
    prow_c = ttk.Frame(tab_led); prow_c.pack(fill="x", padx=12, pady=2)
    for _key, _rgb in palette:
        reg_text(ttk.Button(prow_c, width=6, command=lambda c=_rgb: apply_color(c)),
                 _key).pack(side="left", padx=1, pady=1)

    reg_text(ttk.Button(tab_led, command=lambda: apply_color()), "btn_apply_color").pack(fill="x", padx=12, pady=(2, 8))

    # ---- Intensidad -----------------------------------------------------
    reg_text(ttk.Label(tab_led, style="H.TLabel"), "led_bright_hdr").pack(anchor="w", padx=12, pady=(6, 2))
    bright_var = tk.IntVar(value=presets.get("led_bright", 100))
    brow_l = ttk.Frame(tab_led); brow_l.pack(fill="x", padx=12)
    bscale = ttk.Scale(brow_l, from_=0, to=100, orient="horizontal",
                       command=lambda v: bright_var.set(int(float(v))))
    bscale.set(bright_var.get()); bscale.pack(side="left", fill="x", expand=True)
    ttk.Label(brow_l, textvariable=bright_var, width=4).pack(side="left")
    ttk.Label(brow_l, text="%").pack(side="left")

    @guard
    def apply_bright():
        mouse.set_brightness(bright_var.get())
        presets["led_bright"] = bright_var.get(); save_presets(presets)
        log(tr("log_bright", v=bright_var.get()))
    reg_text(ttk.Button(tab_led, command=apply_bright), "btn_apply_bright").pack(fill="x", padx=12, pady=(2, 8))

    # ---- Encender / apagar (un solo boton) -----------------------------
    @guard
    def toggle_led():
        if led_on[0]:
            mouse.set_light_off(); led_on[0] = False; log(tr("log_led_off"))
        else:
            mouse.set_color(*led_color[0]); led_on[0] = True; log(tr("log_led_on"))
        render_onoff()
    onoff_btn = ttk.Button(tab_led, command=toggle_led)
    onoff_btn.pack(fill="x", padx=12, pady=(10, 6))
    reg(render_onoff)

    # =====================================================================
    # 9) BUCLE DE SONDEO (solo primer plano; o siempre si el toast esta ON)
    # =====================================================================
    POLL_MS = 1500
    focused = [True]

    def _focus_in(_e):
        was = focused[0]; focused[0] = True
        if not was:
            recalibrate_on_focus()              # al volver, auto-corrige

    def _focus_out(_e):
        # se difiere: si el foco solo salto a otro widget de la app, sigue activo
        def recheck():
            try: focused[0] = (root.focus_displayof() is not None)
            except Exception: focused[0] = False
        root.after(120, recheck)

    root.bind("<FocusIn>", _focus_in)
    root.bind("<FocusOut>", _focus_out)

    def _window_active():
        try:
            if root.state() in ("iconic", "withdrawn"):   # minimizada/oculta
                return False
        except Exception:
            return False
        return focused[0]

    def auto_tick():
        if mouse.dev is not None and not mouse.lighting_only:
            notify_on = notify_var.get()
            # el toast exige sondear siempre; si no, solo en primer plano
            if notify_on or (auto_var.get() and _window_active()):
                if tracking[0]:
                    changed = track_tick()
                    if changed is not None and notify_on:
                        show_toast(changed)
                elif auto_var.get() and _window_active():
                    detect_active(verbose=False)
        root.after(POLL_MS, auto_tick)

    root.after(POLL_MS, auto_tick)

    # =====================================================================
    # 10) LOG + DONACION (Ko-fi)
    # =====================================================================
    ttk.Separator(root).pack(fill="x", padx=12, pady=(2, 4))
    reg_text(ttk.Label(root, style="Muted.TLabel"), "log_lbl").pack(anchor="w", padx=14)
    logbox = tk.Text(root, height=5, width=54, state="disabled", bg=LOGBG, fg=LOGFG,
                     font=("Consolas", 9), relief="flat", highlightthickness=0, bd=0, padx=8, pady=6)
    logbox.pack(fill="x", expand=False, padx=12, pady=(4, 8))

    def open_kofi(_e=None):
        try: webbrowser.open_new(KOFI_URL)
        except Exception as e: log(tr("log_browser_err", e=e))

    ttk.Separator(root).pack(fill="x", padx=12, pady=(2, 4))
    kofi_link = tk.Label(root, bg=BG, fg=MUTED, cursor="hand2",
                         font=("Segoe UI", 9, "underline"))
    kofi_link.pack(anchor="w", padx=12, pady=(0, 8))
    kofi_link.bind("<Button-1>", open_kofi)
    kofi_link.bind("<Enter>", lambda _e: kofi_link.configure(fg=ACCENT2))
    kofi_link.bind("<Leave>", lambda _e: kofi_link.configure(fg=MUTED))
    reg(lambda: kofi_link.configure(text=tr("kofi_link")))

    # mensajes iniciales del log (en el idioma activo)
    log(tr("log_steps1"))
    log(tr("log_steps2"))

    # =====================================================================
    # 11) TAMANO FIJO: medir el contenido y bloquear la ventana a ese tamano
    # =====================================================================
    root.update_idletasks()
    root.geometry(f"{max(480, root.winfo_reqwidth())}x{root.winfo_reqheight()}")
    root.resizable(False, False)

    root.mainloop()


# ---------------------------------------------------------------------------
# Modo consola
# ---------------------------------------------------------------------------
def run_cli():
    print("Modelos:")
    for i, d in enumerate(DEVICES):
        print(f"  {i:2d}) {d['name']}")
    try:
        idx = int(input("Numero de modelo: ").strip())
    except Exception:
        idx = 0
    m = DEVICES[max(0, min(len(DEVICES) - 1, idx))]
    mouse = RazerMouse()
    mouse.connect(m, log=print)
    try:
        fw = mouse.get_firmware(); print(f"Firmware v{fw[0]}.{fw[1]}")
    except Exception: pass
    try:
        x, y = mouse.get_dpi(); print(f"DPI actual: {x} x {y}")
    except Exception: pass
    print("\nComandos: dpi <v> | poll <125|500|1000> | bat | read | salir")
    while True:
        try: c = input("> ").strip().split()
        except (EOFError, KeyboardInterrupt): break
        if not c: continue
        try:
            if c[0] == "salir": break
            elif c[0] == "bat": p, ch = mouse.get_battery(); print(f"Bateria {p}%{' cargando' if ch else ''}")
            elif c[0] == "read": x, y = mouse.get_dpi(); print(f"DPI {x} x {y}")
            elif c[0] == "dpi" and len(c) == 2: st, (x, y) = mouse.set_dpi(int(c[1])); print(f"DPI -> {x} ({STATUS.get(st, hex(st))})")
            elif c[0] == "poll" and len(c) == 2: st = mouse.set_poll_rate(int(c[1])); print(f"Poll -> {c[1]} ({STATUS.get(st, hex(st))})")
            else: print("?")
        except Exception as e: print(f"[ERROR] {e}")
    mouse.close()


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        try:
            run_gui()
        except Exception as e:
            print(f"No se pudo abrir la GUI ({e}). Usa: py Non_Synapse_Mouse.py --cli")
