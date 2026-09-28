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
  - Conexión y reconexión automáticas.
  - MODO CONTROL (como Synapse): el programa pone el ratón en "modo driver",
    escucha su botón de perfil/DPI y aplica sus 5 perfiles (guardados en el
    programa). Exacto e instantáneo. Al cerrar, el ratón vuelve a su modo normal
    y a sus perfiles internos, que nunca se tocan.
  - MODO COMPATIBILIDAD (si Windows no deja escuchar el botón): deduce el
    perfil por el DPI sin sobrescribir nunca nada.
  - (v1.1.0) Pestaña Opciones: minimizar a la bandeja del sistema, arrancar
    con Windows (minimizado), buscar e instalar actualizaciones desde GitHub,
    y botón para reportar errores (abre un "issue" con los datos ya rellenos).
  - (v1.1.0) El registro (log) y los errores siguen el idioma elegido.
  - (v1.1.0) Configuración en %APPDATA%/Non-Synapse-Mouse (se migra sola la
    antigua), seguimiento de perfiles recordado entre sesiones, una sola
    instancia a la vez y detección mientras la ventana esté visible.

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
    Opcional, para la bandeja del sistema:  py -m pip install pystray pillow
    (sin ellos el programa funciona igual; solo se desactiva esa casilla)

RED: lo único que se conecta a internet es la comprobación de actualizaciones
    (una consulta de lectura a api.github.com, desactivable en Opciones), la
    descarga de la actualización si el usuario la acepta, y los enlaces que el
    usuario abre en su navegador (Ko-fi, reportar error).

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
import threading
import queue
import subprocess
import urllib.request
import urllib.parse
import platform

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
# La configuracion se guarda en una carpeta FIJA del usuario, para que no se
# pierda al mover el .exe, al compilar uno nuevo (sale en dist\) o al
# actualizar:  Windows -> %APPDATA%\Non-Synapse-Mouse\razer_presets.json
# Si existe una configuracion antigua junto al programa (v1.0.0), se migra sola.
LEGACY_CONFIG_PATH = os.path.join(_BASE_DIR, "razer_presets.json")
if sys.platform == "win32" and os.environ.get("APPDATA"):
    CONFIG_DIR = os.path.join(os.environ["APPDATA"], "Non-Synapse-Mouse")
else:
    CONFIG_DIR = _BASE_DIR
CONFIG_PATH = os.path.join(CONFIG_DIR, "razer_presets.json")
KOFI_URL = "https://ko-fi.com/damneddamm"

# ---------------------------------------------------------------------------
# Datos de la aplicacion (version, repositorio, enlaces)
# ---------------------------------------------------------------------------
APP_NAME    = "Non-Synapse-Mouse"
APP_VERSION = "1.1.0"                        # versionado semantico MAYOR.MENOR.PARCHE
GITHUB_REPO = "Damnedapa/Non-Synapse-Mouse"
REPO_URL    = f"https://github.com/{GITHUB_REPO}"
ISSUES_URL  = f"{REPO_URL}/issues/new"
RELEASES_URL = f"{REPO_URL}/releases/latest"
API_LATEST  = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


# ---------------------------------------------------------------------------
# Mensajes del NUCLEO (clase RazerMouse) en los dos idiomas.
# Antes estaban fijos en castellano y por eso el log salia siempre en espanol.
# La interfaz llama a set_core_lang() al arrancar y al cambiar de idioma.
# ---------------------------------------------------------------------------
_CORE_LANG = ["es"]

CORE_MSG = {
    "es": {
        "not_connected": "No conectado. Pulsa «Detectar / Probar conexión».",
        "no_response":   "El ratón no respondió.",
        "no_hidapi":     "Falta el paquete 'hidapi'. Instálalo con:  py -m pip install hidapi",
        "autodetect":    "Autodetección: buscando cualquier ratón Razer...",
        "enum_fail":     "No se pudieron enumerar los dispositivos Razer: {e}",
        "pid_enum":      "  (PID {pid} no enumerable: {e})",
        "not_found":     "No se encontró el ratón. Comprueba que esté encendido y conectado.",
        "probing":       "{n} interfaz(es) a probar; buscando la que responde...",
        "if_open_fail":  "  interfaz {i}: no se pudo abrir ({e})",
        "connected":     "Conectado (PID {pid} {conn}) · transaction_id 0x{tx}",
        "if_no_resp":    "  interfaz {i}: sin respuesta válida",
        "none_resp":     "Se abrieron las interfaces pero ninguna respondió. Cierra Synapse por completo (servicios incluidos) y reintenta.",
        "bad_poll":      "La tasa de sondeo debe ser 125, 500 o 1000 Hz.",
        "light_fail":    "El ratón no aceptó el comando de iluminación.",
    },
    "en": {
        "not_connected": "Not connected. Press \u201cDetect / Test connection\u201d.",
        "no_response":   "The mouse didn't respond.",
        "no_hidapi":     "The 'hidapi' package is missing. Install it with:  py -m pip install hidapi",
        "autodetect":    "Auto-detection: looking for any Razer mouse...",
        "enum_fail":     "Couldn't enumerate Razer devices: {e}",
        "pid_enum":      "  (PID {pid} not enumerable: {e})",
        "not_found":     "Mouse not found. Check that it's turned on and connected.",
        "probing":       "{n} interface(s) to probe; looking for the one that responds...",
        "if_open_fail":  "  interface {i}: couldn't open ({e})",
        "connected":     "Connected (PID {pid} {conn}) · transaction_id 0x{tx}",
        "if_no_resp":    "  interface {i}: no valid response",
        "none_resp":     "Interfaces opened but none responded. Close Synapse completely (services included) and retry.",
        "bad_poll":      "Polling rate must be 125, 500 or 1000 Hz.",
        "light_fail":    "The mouse didn't accept the lighting command.",
    },
}


def set_core_lang(lang):
    """Fija el idioma de los mensajes del nucleo ('es' o 'en')."""
    _CORE_LANG[0] = lang if lang in CORE_MSG else "es"


def _m(key, **kw):
    """Mensaje del nucleo en el idioma activo (con huecos opcionales)."""
    txt = CORE_MSG[_CORE_LANG[0]].get(key) or CORE_MSG["es"].get(key, key)
    return txt.format(**kw) if kw else txt


# ---------------------------------------------------------------------------
# Utilidades: version, actualizaciones y arranque con Windows
# ---------------------------------------------------------------------------
def parse_version(tag):
    """'v1.2.3' -> (1, 2, 3). Tolera prefijos/sufijos raros; devuelve (0,) si falla."""
    nums = []
    for part in str(tag).strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        if not digits:
            break
        nums.append(int(digits))
    return tuple(nums) if nums else (0,)


def fetch_latest_release(timeout=6):
    """Consulta la API publica de GitHub. Devuelve (tag, url_pagina, url_exe o None).
    Solo hace una peticion GET de lectura; no envia ningun dato del usuario."""
    req = urllib.request.Request(API_LATEST, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{APP_NAME}/{APP_VERSION}",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    tag = data.get("tag_name", "")
    page = data.get("html_url", RELEASES_URL)
    exe_url = None
    for a in data.get("assets", []):
        if str(a.get("name", "")).lower().endswith(".exe"):
            exe_url = a.get("browser_download_url")
            break
    return tag, page, exe_url


def download_file(url, dest, timeout=60):
    """Descarga url -> dest (via fichero temporal, para no dejar uno a medias)."""
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as fh:
        while True:
            chunk = r.read(65536)
            if not chunk:
                break
            fh.write(chunk)
    os.replace(tmp, dest)


# Arranque con Windows: valor en HKCU\...\Run (solo afecta al usuario actual,
# no necesita permisos de administrador).
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_RUN_NAME = APP_NAME


def autostart_supported():
    return sys.platform == "win32"


def _autostart_command():
    """Comando que Windows ejecutara al iniciar sesion (arranca minimizado)."""
    if getattr(sys, "frozen", False):                      # .exe
        return f'"{sys.executable}" --minimized'
    exe = sys.executable                                   # script: usa pythonw (sin consola)
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.path.exists(pyw):
        exe = pyw
    return f'"{exe}" "{os.path.abspath(__file__)}" --minimized'


def autostart_enabled():
    if not autostart_supported():
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as k:
            winreg.QueryValueEx(k, _RUN_NAME)
        return True
    except Exception:
        return False


def set_autostart(enable):
    """Activa/desactiva el arranque con Windows. Lanza excepcion si falla."""
    if not autostart_supported():
        raise RuntimeError("Windows only")
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if enable:
            winreg.SetValueEx(k, _RUN_NAME, 0, winreg.REG_SZ, _autostart_command())
        else:
            try:
                winreg.DeleteValue(k, _RUN_NAME)
            except FileNotFoundError:
                pass


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
            raise RuntimeError(_m("not_connected"))
        tx = self._get_tx(command_class)
        resp = self._raw(self.dev, build_report(command_class, command_id, data_size, args, tx), command_class)
        if resp is None:
            raise RuntimeError(_m("no_response"))
        return resp

    # --- conexion --------------------------------------------------------
    def connect(self, model, log=lambda s: None):
        if hid is None:
            raise RuntimeError(_m("no_hidapi"))
        self.close()
        self.model = model
        self.tx_cache = {}

        # reunir candidatos (interfaces HID a probar)
        candidates = []
        if model["pids"] is None:               # auto-detectar cualquier Razer
            log(_m("autodetect"))
            try:
                for info in hid.enumerate(RAZER_VID, 0):
                    candidates.append((info.get("product_id"), info))
            except Exception as e:
                raise RuntimeError(_m("enum_fail", e=e))
            known = {p for d in DEVICES if d["pids"] for p in d["pids"]}
            candidates.sort(key=lambda c: 0 if c[0] in known else 1)
        else:
            for pid in model["pids"]:
                try:
                    for info in hid.enumerate(RAZER_VID, pid):
                        candidates.append((pid, info))
                except Exception as e:
                    log(_m("pid_enum", pid=f"{pid:04X}", e=e))

        if not candidates:
            raise RuntimeError(_m("not_found"))

        log(_m("probing", n=len(candidates)))
        for pid, info in candidates:
            try:
                d = hid.device(); d.open_path(info["path"])
            except Exception as e:
                log(_m("if_open_fail", i=info.get('interface_number'), e=e)); continue
            tx = self._probe_tx(d, 0x00)         # sondea firmware
            if tx is not None:
                self.dev = d; self.pid = pid; self.tx_cache[0x00] = tx
                conn = ""
                if model["pids"]:
                    conn = model["pids"].get(pid, "")
                log(_m("connected", pid=f"{pid:04X}", conn=conn, tx=f"{tx:02X}"))
                return True
            try: d.close()
            except Exception: pass
            log(_m("if_no_resp", i=info.get('interface_number')))

        raise RuntimeError(_m("none_resp"))

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
        r = self._cmd(0x07, 0x80, 0x02)
        pct = round(r[9] / 255 * 100)
        c = self._cmd(0x07, 0x84, 0x02)
        return pct, bool(c[9])

    def get_dpi(self):
        r = self._cmd(0x04, 0x85, 0x07, bytes([VARSTORE]))
        return (r[9] << 8) | r[10], (r[11] << 8) | r[12]

    def set_dpi(self, dpi_x, dpi_y=None, persist=True):
        dpi_max = self.model["dpi_max"] if self.model else 30000
        dpi_y = dpi_x if dpi_y is None else dpi_y
        dpi_x = max(DPI_MIN, min(dpi_max, int(dpi_x)))
        dpi_y = max(DPI_MIN, min(dpi_max, int(dpi_y)))
        store = VARSTORE if persist else NOSTORE
        args = bytes([store, (dpi_x >> 8) & 0xFF, dpi_x & 0xFF,
                      (dpi_y >> 8) & 0xFF, dpi_y & 0xFF, 0, 0])
        r = self._cmd(0x04, 0x05, 0x07, args)
        return r[0], (dpi_x, dpi_y)

    # --- modo del dispositivo (como Synapse) ------------------------------
    # 0x00 = normal: el raton gestiona sus perfiles internos con su boton.
    # 0x03 = driver: el raton NO cambia de perfil solo; avisa al PC de cada
    #        pulsacion de sus botones especiales ("Report 4") y el programa
    #        decide. Es lo que hace Synapse. Documentado en OpenRazer.
    MODE_NORMAL = 0x00
    MODE_DRIVER = 0x03

    def set_device_mode(self, mode):
        r = self._cmd(0x00, 0x04, 0x02, bytes([mode & 0xFF, 0x00]))
        return r[0]

    def get_device_mode(self):
        r = self._cmd(0x00, 0x84, 0x02)
        return r[8]

    def set_poll_rate(self, hz):
        if hz not in POLL_ARG:
            raise ValueError(_m("bad_poll"))
        r = self._cmd(0x00, 0x05, 0x01, bytes([POLL_ARG[hz]]))
        return r[0]

    # --- iluminacion (clase 0x0F; en la Viper Ultimate usa tid 0x3F) -----
    def _cmd_light(self, command_id, data_size, args):
        """Comandos de LED. La clase 0x0F no tiene lectura para sondear el
        transaction_id, asi que se prueba al enviar (el propio 'aplicar' hace
        de sonda): el primer tid cuya respuesta hace eco de la clase 0x0F vale."""
        if self.dev is None:
            raise RuntimeError(_m("not_connected"))
        order = list(TX_LIGHT_CANDIDATES)
        if 0x0F in self.tx_cache:
            order.insert(0, self.tx_cache[0x0F])
        for tx in order:
            resp = self._raw(self.dev, build_report(0x0F, command_id, data_size, args, tx), 0x0F)
            if resp and resp[6] == 0x0F and resp[0] != 0x05:   # 0x05 = no soportado
                self.tx_cache[0x0F] = tx
                return resp
        raise RuntimeError(_m("light_fail"))

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
# Escucha de botones especiales del raton ("Report 4" de OpenRazer).
# En modo driver, cada pulsacion del boton de perfil / DPI llega como un
# informe de entrada que empieza por 0x04 seguido de los codigos pulsados:
#   0x50 perfil · 0x52 ciclo DPI · 0x20 DPI+ · 0x21 DPI-
# Se abren TODAS las interfaces HID del raton que el sistema deje leer y cada
# una se escucha en su propio hilo. Si Windows no deja abrir ninguna, el
# programa lo detecta y pasa a modo compatibilidad.
# ---------------------------------------------------------------------------
REP4_PROFILE = 0x50
REP4_DPI_CYCLE = 0x52
REP4_DPI_UP = 0x20
REP4_DPI_DN = 0x21


class ButtonListener:
    def __init__(self, pid, on_press, on_other=None):
        self.pid = pid
        self.on_press = on_press          # se llama desde un hilo secundario
        self.on_other = on_other          # informes desconocidos (diagnostico)
        self._run = False
        self._threads = []
        self._devs = []

    def start(self):
        """Abre las interfaces legibles. Devuelve cuantas se abrieron."""
        if hid is None or self.pid is None:
            return 0
        self._run = True
        try:
            infos = hid.enumerate(RAZER_VID, self.pid)
        except Exception:
            infos = []
        for info in infos:
            try:
                d = hid.device()
                d.open_path(info["path"])
            except Exception:
                continue                  # Windows bloquea algunas (normal)
            self._devs.append(d)
            t = threading.Thread(target=self._loop, args=(d,), daemon=True)
            self._threads.append(t)
            t.start()
        return len(self._devs)

    def _loop(self, d):
        prev = set()
        while self._run:
            try:
                data = d.read(64, 250)    # espera hasta 250 ms
            except Exception:
                break                     # interfaz no legible o desconectada
            if not data:
                continue
            if data[0] != 0x04:
                if self.on_other is not None:
                    try: self.on_other(bytes(data[:16]))
                    except Exception: pass
                continue
            codes = {c for c in data[1:16] if c}
            for c in codes - prev:        # solo el flanco de pulsacion
                try: self.on_press(c)
                except Exception: pass
            prev = codes

    def alive(self):
        return any(t.is_alive() for t in self._threads)

    def stop(self):
        self._run = False
        for d in self._devs:
            try: d.close()
            except Exception: pass
        self._devs, self._threads = [], []


# ---------------------------------------------------------------------------
# REMAPEO POR SOFTWARE (solo Windows)
# Un "gancho" de raton de bajo nivel (WH_MOUSE_LL, como AutoHotkey) intercepta
# los botones que Windows deja tocar (central, laterales, inclinacion de la
# rueda), bloquea la pulsacion original y ejecuta otra accion (teclas, clics,
# cambio de perfil...). Solo funciona con el programa abierto y NO se guarda
# en la memoria del raton. Los clics izquierdo/derecho NO se remapean nunca
# (seguridad). Los eventos inyectados por nosotros se dejan pasar (sin bucles).
# AVISO: algunos anticheats pueden detectar este tipo de ganchos/inyeccion.
# ---------------------------------------------------------------------------
SOFT_BUTTONS = ["middle", "wheel_up", "wheel_down", "x2", "x1", "tilt_l", "tilt_r"]
SOFT_ONLY_IF_SEEN = {"tilt_l", "tilt_r"}      # la inclinacion solo aparece si el raton la tiene

WM_MBUTTONDOWN, WM_MBUTTONUP = 0x0207, 0x0208
WM_XBUTTONDOWN, WM_XBUTTONUP = 0x020B, 0x020C
WM_MOUSEWHEEL, WM_MOUSEHWHEEL = 0x020A, 0x020E
LLMHF_INJECTED = 0x01


def decode_mouse_msg(wparam, mouse_data):
    """(mensaje de Windows, mouseData) -> (boton, pulsado/soltado, tiene_soltar)
    o (None, None, None) si no es un boton remapeable."""
    if wparam in (WM_MBUTTONDOWN, WM_MBUTTONUP):
        return "middle", wparam == WM_MBUTTONDOWN, True
    if wparam in (WM_XBUTTONDOWN, WM_XBUTTONUP):
        xb = (mouse_data >> 16) & 0xFFFF
        if xb in (1, 2):
            return ("x1" if xb == 1 else "x2"), wparam == WM_XBUTTONDOWN, True
    if wparam == WM_MOUSEWHEEL:                     # rueda vertical: cada "clic" de giro
        delta = (mouse_data >> 16) & 0xFFFF
        if delta >= 0x8000:
            delta -= 0x10000
        if delta:
            return ("wheel_up" if delta > 0 else "wheel_down"), True, False
    if wparam == WM_MOUSEHWHEEL:
        delta = (mouse_data >> 16) & 0xFFFF
        if delta >= 0x8000:
            delta -= 0x10000
        if delta:
            return ("tilt_r" if delta > 0 else "tilt_l"), True, False
    return None, None, None


# Teclas virtuales de Windows para las combinaciones ("ctrl+shift+s", "f13"...)
VK = {"ctrl": 0x11, "shift": 0x10, "alt": 0x12, "win": 0x5B,
      "enter": 0x0D, "esc": 0x1B, "tab": 0x09, "space": 0x20, "backspace": 0x08,
      "delete": 0x2E, "insert": 0x2D, "home": 0x24, "end": 0x23, "pgup": 0x21,
      "pgdn": 0x22, "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
      "printscreen": 0x2C, "capslock": 0x14,
      "media_play": 0xB3, "media_next": 0xB0, "media_prev": 0xB1, "media_stop": 0xB2,
      "vol_up": 0xAF, "vol_down": 0xAE, "vol_mute": 0xAD}
for _c in "abcdefghijklmnopqrstuvwxyz":
    VK[_c] = ord(_c.upper())
for _d in "0123456789":
    VK[_d] = ord(_d)
for _n in range(1, 25):
    VK[f"f{_n}"] = 0x6F + _n
EXTENDED_VK = {0x2E, 0x2D, 0x24, 0x23, 0x21, 0x22, 0x26, 0x28, 0x25, 0x27, 0x5B,
               0xB3, 0xB0, 0xB1, 0xB2, 0xAF, 0xAE, 0xAD}
_ALIASES = {"control": "ctrl", "ctl": "ctrl", "mayus": "shift", "escape": "esc",
            "return": "enter", "intro": "enter", "supr": "delete", "del": "delete",
            "windows": "win", "espacio": "space", "arriba": "up", "abajo": "down",
            "izquierda": "left", "derecha": "right", "re pag": "pgup", "av pag": "pgdn"}


def parse_combo(text):
    """'Ctrl + Shift + S' -> [0x11, 0x10, 0x53]  ·  None si no es valida."""
    parts = [p.strip().lower() for p in str(text).replace("-", "+").split("+") if p.strip()]
    if not parts or len(parts) > 5:
        return None
    out = []
    for p in parts:
        p = _ALIASES.get(p, p)
        if p not in VK:
            return None
        out.append(VK[p])
    return out


class SoftRemapper:
    """Gancho global de raton (hilo propio con bucle de mensajes).
    `get_action(boton)` -> id de accion ('default' = no tocar).
    `on_ui(boton)`      -> aviso a la interfaz (puntito verde).
    `do_action(accion, pulsado, tiene_soltar)` -> ejecuta (en otro hilo)."""

    def __init__(self, get_action, on_ui, do_action):
        self.get_action = get_action
        self.on_ui = on_ui
        self.do_action = do_action
        self._thread = None
        self._tid = None
        self._hook = None
        self._proc = None
        self._jobs = queue.Queue()
        self._worker = None
        self.ok = False

    @staticmethod
    def supported():
        return sys.platform == "win32"

    # --- decision (rapida: se ejecuta dentro del gancho) ------------------
    def handle(self, wparam, mouse_data, flags):
        """True = bloquear el evento original."""
        if flags & LLMHF_INJECTED:
            return False                          # nuestro propio evento: dejar pasar
        btn, down, has_up = decode_mouse_msg(wparam, mouse_data)
        if btn is None:
            return False
        if down:
            try: self.on_ui(btn)
            except Exception: pass
        action = self.get_action(btn)
        if not action or action == "default":
            return False
        self._jobs.put((action, down, has_up))
        return True

    def _work(self):
        while True:
            job = self._jobs.get()
            if job is None:
                return
            try: self.do_action(*job)
            except Exception: pass

    # --- instalacion del gancho (solo Windows) ------------------------------
    def start(self):
        if not self.supported() or self._thread is not None:
            return self.ok
        self._worker = threading.Thread(target=self._work, daemon=True); self._worker.start()
        ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(ready,), daemon=True)
        self._thread.start()
        ready.wait(2.0)
        return self.ok

    def _run(self, ready):
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        class MSLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [("pt_x", ctypes.c_int32), ("pt_y", ctypes.c_int32), ("mouseData", ctypes.c_uint32),
                        ("flags", ctypes.c_uint32), ("time", ctypes.c_uint32),
                        ("dwExtraInfo", ctypes.c_size_t)]
        LRESULT = ctypes.c_ssize_t
        HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
        user32.SetWindowsHookExW.restype = ctypes.c_void_p
        user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        user32.CallNextHookEx.restype = LRESULT
        user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE

        def proc(n_code, wparam, lparam):
            try:
                if n_code == 0:
                    info = ctypes.cast(lparam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    if self.handle(wparam, info.mouseData, info.flags):
                        return 1
            except Exception:
                pass
            return user32.CallNextHookEx(None, n_code, wparam, lparam)

        self._proc = HOOKPROC(proc)                    # guardar referencia (evita que se libere)
        self._tid = kernel32.GetCurrentThreadId()
        self._hook = user32.SetWindowsHookExW(14, self._proc, kernel32.GetModuleHandleW(None), 0)  # 14 = WH_MOUSE_LL
        self.ok = bool(self._hook)
        ready.set()
        if not self.ok:
            return
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg)); user32.DispatchMessageW(ctypes.byref(msg))
        user32.UnhookWindowsHookEx(self._hook)
        self._hook = None

    def stop(self):
        if self._thread is not None and self._tid:
            try:
                import ctypes
                ctypes.windll.user32.PostThreadMessageW(self._tid, 0x0012, 0, 0)   # WM_QUIT
            except Exception:
                pass
        self._jobs.put(None)
        self._thread = None; self._tid = None; self.ok = False


def send_input_keys(vks, down):
    """Pulsa (down=True) o suelta (False) una lista de teclas virtuales."""
    import ctypes
    from ctypes import wintypes
    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_uint16), ("wScan", ctypes.c_uint16), ("dwFlags", ctypes.c_uint32),
                    ("time", ctypes.c_uint32), ("dwExtraInfo", ctypes.c_size_t)]
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_int32), ("dy", ctypes.c_int32), ("mouseData", ctypes.c_uint32),
                    ("dwFlags", ctypes.c_uint32), ("time", ctypes.c_uint32), ("dwExtraInfo", ctypes.c_size_t)]
    class _U(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]
    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_uint32), ("u", _U)]
    seq = vks if down else list(reversed(vks))
    arr = (INPUT * len(seq))()
    for k, vk in enumerate(seq):
        flags = (0 if down else 0x0002) | (0x0001 if vk in EXTENDED_VK else 0)   # KEYUP / EXTENDED
        arr[k].type = 1                                                        # INPUT_KEYBOARD
        arr[k].u.ki = KEYBDINPUT(vk, 0, flags, 0, 0)
    ctypes.windll.user32.SendInput(len(seq), arr, ctypes.sizeof(INPUT))


MOUSE_FLAGS = {"click_left": (0x0002, 0x0004, 0), "click_right": (0x0008, 0x0010, 0),
               "click_middle": (0x0020, 0x0040, 0), "click_back": (0x0080, 0x0100, 1),
               "click_forward": (0x0080, 0x0100, 2)}


def send_input_mouse(action, down):
    import ctypes
    from ctypes import wintypes
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_int32), ("dy", ctypes.c_int32), ("mouseData", ctypes.c_uint32),
                    ("dwFlags", ctypes.c_uint32), ("time", ctypes.c_uint32), ("dwExtraInfo", ctypes.c_size_t)]
    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_uint16), ("wScan", ctypes.c_uint16), ("dwFlags", ctypes.c_uint32),
                    ("time", ctypes.c_uint32), ("dwExtraInfo", ctypes.c_size_t)]
    class _U(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]
    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_uint32), ("u", _U)]
    fdown, fup, xdata = MOUSE_FLAGS[action]
    inp = INPUT(); inp.type = 0                                                # INPUT_MOUSE
    inp.u.mi = MOUSEINPUT(0, 0, xdata, fdown if down else fup, 0, 0)
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


# ---------------------------------------------------------------------------
# Persistencia de presets
# ---------------------------------------------------------------------------
def load_presets():
    """Carga la configuracion. Si aun no existe la nueva pero si la antigua
    (junto al programa), usa la antigua: al guardar ya queda migrada."""
    for path in (CONFIG_PATH, LEGACY_CONFIG_PATH):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            continue
    return {}

def save_presets(data):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Una sola instancia (Windows): si ya hay una abierta (p. ej. en la bandeja),
# no se abre otra, porque dos programas hablando a la vez con el raton se
# pisan las lecturas.
# ---------------------------------------------------------------------------
_INSTANCE_MUTEX = []

def acquire_single_instance():
    """True si somos la unica instancia (o si no es Windows)."""
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        h = k32.CreateMutexW(None, False, "Local\\NonSynapseMouse_SingleInstance")
        if not h:
            return True
        _INSTANCE_MUTEX.append((k32, h))
        return ctypes.get_last_error() != 183          # 183 = ERROR_ALREADY_EXISTS
    except Exception:
        return True

def release_single_instance():
    """Libera el bloqueo (antes de lanzar la version nueva al actualizar)."""
    while _INSTANCE_MUTEX:
        k32, h = _INSTANCE_MUTEX.pop()
        try: k32.CloseHandle(h)
        except Exception: pass


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
            "status_disc": "Buscando el ratón…",
            "status_conn": "Conectado · {name}",
            "model_lbl": "Modelo:",
            "btn_connect": "Detectar / Probar conexión",
            "tab_main": "Perfiles",
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
            "chk_auto": "Detección automática con la ventana visible",
            "chk_notify": "Aviso emergente al cambiar de perfil",
            "led_color_hdr": "Color del LED (logo)",
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
            "log_unk": "El DPI actual {x} no coincide con ningún preset. Pulsa «Empezar seguimiento» para que aprenda tus perfiles.",
            "log_track_resume": "Seguimiento reanudado: estás en el Perfil {n} ({x} DPI).",
            "log_track_lost": "No se pudo reanudar el seguimiento (el DPI actual {x} no coincide con ningún perfil). Pulsa «Reanclar».",
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
            # --- v1.1.0: opciones, actualizaciones, bandeja, errores ---
            "tab_opts": "Opciones",
            "sys_hdr": "Sistema",
            "opt_tray": "Minimizar a la bandeja del sistema",
            "opt_tray_na": "Bandeja no disponible (falta el paquete pystray)",
            "opt_autostart": "Arrancar con Windows (minimizado)",
            "opt_autostart_na": "Arrancar con Windows (solo en Windows)",
            "upd_hdr": "Actualizaciones",
            "opt_upd_start": "Buscar actualizaciones al iniciar",
            "btn_check_upd": "Buscar ahora",
            "btn_install_upd": "Descargar e instalar",
            "upd_idle": "Versión instalada: v{v}",
            "upd_checking": "Buscando actualizaciones...",
            "upd_latest": "Estás al día (v{v}).",
            "upd_new": "Nueva versión disponible: {tag}",
            "upd_err": "No se pudo comprobar (¿sin conexión?).",
            "upd_downloading": "Descargando {tag}...",
            "help_hdr": "Ayuda",
            "btn_report": "\U0001F41E  Reportar un error",
            "bug_link": "\U0001F41E Reportar un error",
            "dlg_upd_title": "Actualización disponible",
            "dlg_upd_msg": "Hay una versión nueva ({tag}); tienes la v{v}.\n\n¿Descargarla ahora? Se guardará junto al programa actual y tu configuración se conserva.",
            "dlg_upd_script": "Estás usando el script de Python: se abrirá la página de la nueva versión para que descargues el código.",
            "dlg_uptodate_title": "Sin actualizaciones",
            "dlg_uptodate_msg": "Ya tienes la última versión (v{v}).",
            "dlg_upd_done_title": "Descarga completada",
            "dlg_upd_done_msg": "Nueva versión descargada en:\n{path}\n\n¿Abrirla ahora y cerrar esta?",
            "tray_show": "Mostrar",
            "tray_quit": "Salir",
            "about_ver": "Versión {v}",
            "log_upd_new": "Hay una versión nueva disponible: {tag} (tienes la v{v}). Mira la pestaña Opciones.",
            "log_upd_latest": "Estás al día (v{v}).",
            "log_upd_err": "No se pudieron buscar actualizaciones: {e}",
            "log_upd_dl_err": "Error al descargar la actualización: {e}",
            "log_upd_saved": "Actualización guardada en: {path}",
            "log_autostart_on": "Arranque con Windows activado.",
            "log_autostart_off": "Arranque con Windows desactivado.",
            "log_autostart_err": "No se pudo cambiar el arranque con Windows: {e}",
            "log_tray": "Minimizado en la bandeja del sistema (junto al reloj).",
            "log_bug_opened": "Abriendo el formulario de errores en GitHub...",
            # --- v1.1.0: modo automatico ---
            "prof_hdr": "Perfiles",
            "prof_wait": "Buscando el ratón… (conéctalo y cierra Razer Synapse)",
            "prof_learning": "Aprendiendo tus perfiles: pulsa el botón de perfil del ratón hasta dar la vuelta completa ({n}/5)",
            "prof_active": "Perfil activo: Perfil {n} · {x} DPI",
            "prof_unknown": "DPI {x} no coincide con tus perfiles · «Restablecer perfiles» para reaprender",
            "btn_apply_prof": "Aplicar DPI al perfil activo",
            "mouse_hdr": "Ratón",
            "btn_reconnect": "Reconectar",
            "btn_relearn": "Reaprender perfiles",
            "log_connected_ok": "Conectado: {name}",
            "log_disconnected": "Ratón desconectado o dormido. Lo vuelvo a buscar solo.",
            "log_learned": "Perfil {n} aprendido: {x} DPI",
            "log_learn_done": "Perfiles aprendidos ({n}). A partir de aquí va solo.",
            "log_prof_changed": "Perfil {n} · {x} DPI",
            "log_prof_updated": "El Perfil {n} ahora tiene {x} DPI",
            "log_prof_unknown": "El DPI {x} no coincide con ningún perfil. Si has cambiado tus perfiles, pulsa «Restablecer perfiles».",
            "log_dpi_applied": "Perfil {n} → {x} DPI ({st}), guardado en el ratón",
            "log_dpi_applied_nop": "DPI → {x} ({st})",
            "log_dup": "Aviso: el Perfil {n} ya tiene {x} DPI; con dos perfiles iguales no puedo distinguirlos.",
            "log_relearn": "Reaprendiendo: pulsa el botón de perfil del ratón hasta dar la vuelta completa.",
            # --- modo control (como Synapse) ---
            "mode_ctrl": "Modo control: el programa gestiona tus perfiles",
            "mode_compat": "Modo compatibilidad: perfil detectado por el DPI",
            "prof_verify": "Pulsa el botón de perfil del ratón para comprobar que te escucho…",
            "btn_save_prof": "Guardar perfiles",
            "btn_reset_prof": "Restablecer perfiles",
            "chk_control": "El programa controla los perfiles (como Synapse)",
            "log_ctrl_on": "Modo control: el botón de perfil del ratón lo gestiona el programa.",
            "log_ctrl_verify": "Modo control activado. Pulsa el botón de perfil del ratón para confirmarlo.",
            "log_ctrl_verified": "¡Te escucho! El botón de perfil ya lo controla el programa.",
            "log_ctrl_fail": "No puedo escuchar el botón del ratón en este equipo; uso el modo compatibilidad.",
            "log_ctrl_noevents": "No ha llegado ninguna pulsación; uso el modo compatibilidad. Puedes reintentarlo en Opciones.",
            "log_ctrl_restored": "Ratón devuelto a su modo normal (sus perfiles internos).",
            "log_ctrl_reapply": "El ratón se había reiniciado; retomo el control y reaplico el perfil.",
            "log_prof_saved": "Perfiles guardados.",
            "log_prof_reset": "Perfiles restablecidos a los valores por defecto.",
            "log_prof_none": "Tiene que haber al menos un perfil con DPI.",
            "log_dup_any": "Aviso: hay perfiles con el mismo DPI.",
            "err_dpi_range": "DPI no válido en el Perfil {n} (entre {lo} y {hi}, o vacío para desactivarlo).",
            "btn_burn": "Grabar en el ratón",
            "btn_burn_step": "Grabar este perfil",
            "btn_cancel": "Cancelar",
            "btn_close": "Cerrar",
            "col_turq": "Turquesa", "col_yellow": "Amarillo",
            "burn_title": "Grabar perfiles en el ratón",
            "burn_step": "Perfil {n} de {total}",
            "burn_msg": "Pulsa el botón de perfil del ratón hasta que el LED de debajo se ponga {color}.\n\nLuego pulsa «Grabar este perfil» (se grabarán {x} DPI del Perfil {n}).",
            "burn_done_title": "¡Grabado!",
            "burn_done_msg": "Cuando cierres el programa, el ratón tendrá estos perfiles con sus colores.",
            "log_burn_noconn": "Conecta el ratón para poder grabar los perfiles.",
            "log_burn_start": "Grabando perfiles en el ratón: sigue los pasos de la ventana.",
            "log_burn_ok": "Grabado en el perfil {color} del ratón: {x} DPI ✓",
            "log_burn_check": "Enviado al perfil {color}: {x} DPI (no he podido confirmarlo al leerlo).",
            "log_burn_done": "Perfiles grabados en el ratón.",
            "log_burn_cancel": "Grabación cancelada.",
            "log_btn_raw": "Señal desconocida del ratón: informe {rid} · {data}",
            "tab_btn": "Mapeo",
            "btn_hint": "Pulsa los botones del ratón: los que el ratón le comunique al programa aparecen aquí y puedes asignarles una acción. Los clics, laterales estándar y la rueda los gestiona Windows y no se pueden remapear aquí.",
            "btn_compat": "Ahora mismo no funcionan: activa «El programa controla los perfiles» en Opciones.",
            "bn_profile": "Botón de perfil", "bn_dpicycle": "Botón de ciclo de DPI",
            "bn_dpiup": "DPI +", "bn_dpidn": "DPI −", "bn_sniper": "Botón sniper",
            "bn_tiltl": "Rueda a la izquierda", "bn_tiltr": "Rueda a la derecha",
            "bn_scroll": "Botón de la rueda (modo)", "bn_unknown": "Botón {code}",
            "act_next": "Siguiente perfil", "act_prev": "Perfil anterior", "act_none": "Nada",
            "log_btn_new": "Nuevo botón detectado: {name}. Asígnale una acción en la pestaña Botones.",
            "log_btn_set": "{name} → {act}",
            "map_warn": "⚠ Por software: solo con el programa abierto, aún NO se guarda en el ratón y algunos anticheats pueden detectarlo.",
            "chk_soft": "Activar remapeo por software (desactívalo al jugar con anticheat)",
            "chk_soft_na": "Remapeo por software (solo en Windows)",
            "log_soft_on": "Remapeo por software activado.",
            "log_soft_off": "Remapeo por software desactivado.",
            "log_soft_fail": "No he podido activar el remapeo por software.",
            "sb_middle": "Pulsar rueda", "sb_wup": "Rueda arriba", "sb_wdn": "Rueda abajo",
            "sb_x2": "Lateral izquierdo arriba (adelante)", "sb_x1": "Lateral izquierdo abajo (atrás)",
            "sb_tiltl": "Rueda inclinada a la izquierda", "sb_tiltr": "Rueda inclinada a la derecha",
            "bn_rside_up": "Lateral derecho arriba", "bn_rside_dn": "Lateral derecho abajo",
            "map_hdr_rep4": "Botones que el ratón avisa al programa (necesitan «El programa controla los perfiles» activado en Opciones):",
            "act_default": "Función normal", "act_default_rep4": "Por defecto ({act})", "act_lclick": "Clic izquierdo", "act_rclick": "Clic derecho",
            "act_mclick": "Clic central", "act_back": "Atrás", "act_forward": "Adelante",
            "act_dbl": "Doble clic", "act_copy": "Copiar (Ctrl+C)", "act_paste": "Pegar (Ctrl+V)",
            "act_cut": "Cortar (Ctrl+X)", "act_undo": "Deshacer (Ctrl+Z)", "act_redo": "Rehacer (Ctrl+Y)",
            "act_enter": "Intro", "act_esc": "Esc", "act_tab": "Tabulador", "act_space": "Espacio",
            "act_alttab": "Cambiar ventana (Alt+Tab)", "act_desktop": "Mostrar escritorio (Win+D)",
            "act_prtsc": "Captura de pantalla", "act_play": "Reproducir / pausa",
            "act_nexttrk": "Pista siguiente", "act_prevtrk": "Pista anterior",
            "act_volup": "Subir volumen", "act_voldn": "Bajar volumen", "act_mute": "Silenciar",
            "act_keys": "Teclas: {keys}", "act_custom": "Tecla personalizada…",
            "custom_title": "Tecla personalizada",
            "custom_prompt": "Escribe la tecla o combinación, por ejemplo:\n  ctrl+shift+s   ·   alt+f4   ·   f13   ·   win+e",
            "log_custom_bad": "No entiendo «{keys}». Usa por ejemplo ctrl+shift+s, alt+f4, f13 o win+e.",
            "chk_ask_exit": "Al cerrar, preguntar si grabar los perfiles en el ratón",
            "dlg_exit_title": "Grabar en el ratón",
            "dlg_exit_msg": "¿Quieres grabar tus perfiles en la memoria del ratón antes de salir?\n\nAsí los tendrás con el programa cerrado o en otro PC (son unos pasos guiados, uno por color).\n\nSí = grabar y salir · No = salir sin grabar · Cancelar = no salir",
        },
        "en": {
            "status_disc": "Looking for the mouse…",
            "status_conn": "Connected · {name}",
            "model_lbl": "Model:",
            "btn_connect": "Detect / Test connection",
            "tab_main": "Profiles",
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
            "chk_auto": "Auto-detection while the window is visible",
            "chk_notify": "Pop-up when the profile changes",
            "led_color_hdr": "LED color (logo)",
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
            "log_unk": "Current DPI {x} matches no preset. Press \u201cStart tracking\u201d so it learns your profiles.",
            "log_track_resume": "Tracking resumed: you are on Profile {n} ({x} DPI).",
            "log_track_lost": "Couldn't resume tracking (current DPI {x} matches no profile). Press \u201cRe-anchor\u201d.",
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
            # --- v1.1.0: settings, updates, tray, bug report ---
            "tab_opts": "Settings",
            "sys_hdr": "System",
            "opt_tray": "Minimize to system tray",
            "opt_tray_na": "Tray unavailable (pystray package missing)",
            "opt_autostart": "Start with Windows (minimized)",
            "opt_autostart_na": "Start with Windows (Windows only)",
            "upd_hdr": "Updates",
            "opt_upd_start": "Check for updates on startup",
            "btn_check_upd": "Check now",
            "btn_install_upd": "Download and install",
            "upd_idle": "Installed version: v{v}",
            "upd_checking": "Checking for updates...",
            "upd_latest": "You're up to date (v{v}).",
            "upd_new": "New version available: {tag}",
            "upd_err": "Couldn't check (offline?).",
            "upd_downloading": "Downloading {tag}...",
            "help_hdr": "Help",
            "btn_report": "\U0001F41E  Report a bug",
            "bug_link": "\U0001F41E Report a bug",
            "dlg_upd_title": "Update available",
            "dlg_upd_msg": "A new version is available ({tag}); you have v{v}.\n\nDownload it now? It will be saved next to the current program and your settings are kept.",
            "dlg_upd_script": "You're running the Python script: the new version's page will open so you can download the code.",
            "dlg_uptodate_title": "No updates",
            "dlg_uptodate_msg": "You already have the latest version (v{v}).",
            "dlg_upd_done_title": "Download complete",
            "dlg_upd_done_msg": "New version downloaded to:\n{path}\n\nOpen it now and close this one?",
            "tray_show": "Show",
            "tray_quit": "Quit",
            "about_ver": "Version {v}",
            "log_upd_new": "A new version is available: {tag} (you have v{v}). See the Settings tab.",
            "log_upd_latest": "You're up to date (v{v}).",
            "log_upd_err": "Couldn't check for updates: {e}",
            "log_upd_dl_err": "Error downloading the update: {e}",
            "log_upd_saved": "Update saved to: {path}",
            "log_autostart_on": "Start with Windows enabled.",
            "log_autostart_off": "Start with Windows disabled.",
            "log_autostart_err": "Couldn't change start with Windows: {e}",
            "log_tray": "Minimized to the system tray (next to the clock).",
            "log_bug_opened": "Opening the bug report form on GitHub...",
            # --- v1.1.0: automatic mode ---
            "prof_hdr": "Profiles",
            "prof_wait": "Looking for the mouse… (plug it in and close Razer Synapse)",
            "prof_learning": "Learning your profiles: press the mouse's profile button until you've gone all the way round ({n}/5)",
            "prof_active": "Active profile: Profile {n} · {x} DPI",
            "prof_unknown": "DPI {x} doesn't match your profiles · \u201cReset profiles\u201d to relearn",
            "btn_apply_prof": "Apply DPI to active profile",
            "mouse_hdr": "Mouse",
            "btn_reconnect": "Reconnect",
            "btn_relearn": "Relearn profiles",
            "log_connected_ok": "Connected: {name}",
            "log_disconnected": "Mouse disconnected or asleep. I'll keep looking for it.",
            "log_learned": "Profile {n} learned: {x} DPI",
            "log_learn_done": "Profiles learned ({n}). From now on it runs on its own.",
            "log_prof_changed": "Profile {n} · {x} DPI",
            "log_prof_updated": "Profile {n} now has {x} DPI",
            "log_prof_unknown": "DPI {x} doesn't match any profile. If you changed your profiles, click \u201cReset profiles\u201d.",
            "log_dpi_applied": "Profile {n} → {x} DPI ({st}), saved to the mouse",
            "log_dpi_applied_nop": "DPI → {x} ({st})",
            "log_dup": "Warning: Profile {n} already has {x} DPI; with two identical profiles I can't tell them apart.",
            "log_relearn": "Relearning: press the mouse's profile button until you've gone all the way round.",
            # --- control mode (like Synapse) ---
            "mode_ctrl": "Control mode: the app manages your profiles",
            "mode_compat": "Compatibility mode: profile detected by DPI",
            "prof_verify": "Press the mouse's profile button so I can check I hear you…",
            "btn_save_prof": "Save profiles",
            "btn_reset_prof": "Reset profiles",
            "chk_control": "The app controls the profiles (like Synapse)",
            "log_ctrl_on": "Control mode: the mouse's profile button is handled by the app.",
            "log_ctrl_verify": "Control mode on. Press the mouse's profile button to confirm it.",
            "log_ctrl_verified": "I hear you! The profile button is now controlled by the app.",
            "log_ctrl_fail": "I can't listen to the mouse's button on this PC; using compatibility mode.",
            "log_ctrl_noevents": "No button press arrived; using compatibility mode. You can retry in Settings.",
            "log_ctrl_restored": "Mouse returned to its normal mode (its own onboard profiles).",
            "log_ctrl_reapply": "The mouse had reset; taking control again and reapplying the profile.",
            "log_prof_saved": "Profiles saved.",
            "log_prof_reset": "Profiles reset to defaults.",
            "log_prof_none": "At least one profile needs a DPI value.",
            "log_dup_any": "Warning: some profiles have the same DPI.",
            "err_dpi_range": "Invalid DPI in Profile {n} (between {lo} and {hi}, or empty to disable it).",
            "btn_burn": "Write to mouse",
            "btn_burn_step": "Write this profile",
            "btn_cancel": "Cancel",
            "btn_close": "Close",
            "col_turq": "Turquoise", "col_yellow": "Yellow",
            "burn_title": "Write profiles to the mouse",
            "burn_step": "Profile {n} of {total}",
            "burn_msg": "Press the mouse's profile button until the LED underneath turns {color}.\n\nThen click \u201cWrite this profile\u201d ({x} DPI from Profile {n} will be written).",
            "burn_done_title": "Done!",
            "burn_done_msg": "When you close the app, the mouse will keep these profiles with their colours.",
            "log_burn_noconn": "Connect the mouse to write the profiles.",
            "log_burn_start": "Writing profiles to the mouse: follow the steps in the window.",
            "log_burn_ok": "Written to the mouse's {color} profile: {x} DPI ✓",
            "log_burn_check": "Sent to the {color} profile: {x} DPI (couldn't confirm by reading it back).",
            "log_burn_done": "Profiles written to the mouse.",
            "log_burn_cancel": "Writing cancelled.",
            "log_btn_raw": "Unknown signal from the mouse: report {rid} · {data}",
            "tab_btn": "Mapping",
            "btn_hint": "Press your mouse buttons: the ones the mouse reports to the app show up here and you can assign them an action. Clicks, standard side buttons and the wheel are handled by Windows and can't be remapped here.",
            "btn_compat": "Not working right now: enable \u201cThe app controls the profiles\u201d in Settings.",
            "bn_profile": "Profile button", "bn_dpicycle": "DPI cycle button",
            "bn_dpiup": "DPI +", "bn_dpidn": "DPI −", "bn_sniper": "Sniper button",
            "bn_tiltl": "Wheel tilt left", "bn_tiltr": "Wheel tilt right",
            "bn_scroll": "Wheel mode button", "bn_unknown": "Button {code}",
            "act_next": "Next profile", "act_prev": "Previous profile", "act_none": "Nothing",
            "log_btn_new": "New button detected: {name}. Assign it an action in the Buttons tab.",
            "log_btn_set": "{name} → {act}",
            "map_warn": "⚠ Software-based: only while the app is open, NOT saved to the mouse yet, and some anti-cheats may detect it.",
            "chk_soft": "Enable software remapping (turn it off when playing with anti-cheat)",
            "chk_soft_na": "Software remapping (Windows only)",
            "log_soft_on": "Software remapping enabled.",
            "log_soft_off": "Software remapping disabled.",
            "log_soft_fail": "Couldn't enable software remapping.",
            "sb_middle": "Wheel click", "sb_wup": "Wheel up", "sb_wdn": "Wheel down",
            "sb_x2": "Left side, upper (forward)", "sb_x1": "Left side, lower (back)",
            "sb_tiltl": "Wheel tilt left", "sb_tiltr": "Wheel tilt right",
            "bn_rside_up": "Right side, upper", "bn_rside_dn": "Right side, lower",
            "map_hdr_rep4": "Buttons the mouse reports to the app (need \u201cThe app controls the profiles\u201d enabled in Settings):",
            "act_default": "Normal function", "act_default_rep4": "Default ({act})", "act_lclick": "Left click", "act_rclick": "Right click",
            "act_mclick": "Middle click", "act_back": "Back", "act_forward": "Forward",
            "act_dbl": "Double click", "act_copy": "Copy (Ctrl+C)", "act_paste": "Paste (Ctrl+V)",
            "act_cut": "Cut (Ctrl+X)", "act_undo": "Undo (Ctrl+Z)", "act_redo": "Redo (Ctrl+Y)",
            "act_enter": "Enter", "act_esc": "Esc", "act_tab": "Tab", "act_space": "Space",
            "act_alttab": "Switch window (Alt+Tab)", "act_desktop": "Show desktop (Win+D)",
            "act_prtsc": "Screenshot", "act_play": "Play / pause",
            "act_nexttrk": "Next track", "act_prevtrk": "Previous track",
            "act_volup": "Volume up", "act_voldn": "Volume down", "act_mute": "Mute",
            "act_keys": "Keys: {keys}", "act_custom": "Custom key…",
            "custom_title": "Custom key",
            "custom_prompt": "Type the key or combination, for example:\n  ctrl+shift+s   ·   alt+f4   ·   f13   ·   win+e",
            "log_custom_bad": "I don't understand \u201c{keys}\u201d. Use e.g. ctrl+shift+s, alt+f4, f13 or win+e.",
            "chk_ask_exit": "On exit, ask whether to write the profiles to the mouse",
            "dlg_exit_title": "Write to mouse",
            "dlg_exit_msg": "Do you want to write your profiles to the mouse's memory before leaving?\n\nThat way you'll have them with the app closed or on another PC (a few guided steps, one per colour).\n\nYes = write and exit · No = exit without writing · Cancel = don't exit",
        },
    }
    # Nombres de los codigos de estado del raton, por idioma
    STATUS_L = {
        "es": {0: "nuevo", 1: "ocupado", 2: "OK", 3: "fallo", 4: "timeout", 5: "no soportado"},
        "en": {0: "new", 1: "busy", 2: "OK", 3: "fail", 4: "timeout", 5: "unsupported"},
    }

    presets = load_presets()
    if not acquire_single_instance():
        _tmp = tk.Tk(); _tmp.withdraw()
        if presets.get("lang", "es") == "en":
            messagebox.showinfo("Non-Synapse-Mouse",
                "Non-Synapse-Mouse is already running.\n"
                "Look for it in the system tray (next to the clock).")
        else:
            messagebox.showinfo("Non-Synapse-Mouse",
                "Non-Synapse-Mouse ya está abierto.\n"
                "Búscalo en la bandeja del sistema (junto al reloj).")
        _tmp.destroy()
        return
    mouse = RazerMouse()
    lang = [presets.get("lang", "es")]          # idioma activo (holder mutable)
    set_core_lang(lang[0])                       # los mensajes del nucleo siguen al idioma

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
    root.title(f"{APP_NAME} v{APP_VERSION}")
    # icono de la ventana/barra de tareas: icono.ico empaquetado en el .exe
    # (PyInstaller --add-data) o junto al script. Si no esta, se queda el de Tk.
    _ico_path = os.path.join(getattr(sys, "_MEIPASS", _BASE_DIR), "icono.ico")
    if os.path.exists(_ico_path):
        try: root.iconbitmap(_ico_path)
        except Exception: pass
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
        set_core_lang(lang[0])                   # mensajes del nucleo (log/errores)
        retranslate()
    lang_combo.bind("<<ComboboxSelected>>", on_lang)

    # boton "?" (Acerca de), arriba a la derecha
    def show_about():
        messagebox.showinfo(tr("about_title"),
                            tr("about_text") + "\n\n" + tr("about_ver", v=APP_VERSION))
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
    state_fw = ["?"]                         # firmware leido (para reportes)

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
    # 6) CONEXION AUTOMATICA
    #    No hay boton de conectar: al abrir se busca el raton y, si no esta o
    #    se desconecta (o se duerme), se reintenta solo cada pocos segundos.
    # =====================================================================
    AUTO_NAME = DEVICES[-1]["name"]                      # "Auto-detectar..."
    model_names = [d["name"] for d in DEVICES]
    model_var = tk.StringVar(value=presets.get("last_model", AUTO_NAME))
    if model_var.get() not in model_names:
        model_var.set(AUTO_NAME)
    active_model = [None]        # modelo realmente conectado (dict de DEVICES)
    last_conn_try = [0.0]        # momento del ultimo intento de conexion
    last_conn_err = [None]       # ultimo error mostrado (para no repetirlo)
    read_fails = [0]             # lecturas fallidas seguidas (-> desconectado)

    def current_model():
        for d in DEVICES:
            if d["name"] == model_var.get():
                return d
        return DEVICES[-1]

    def _model_for_pid(pid):
        """Con 'Auto-detectar', averigua que modelo es por su PID USB."""
        for d in DEVICES:
            if d["pids"] and pid in d["pids"]:
                return d
        return None

    def connect_mouse(manual=False):
        """Intenta conectar. manual=True -> registro detallado (boton Reconectar).
        En los intentos automaticos solo se registra cada error distinto una vez."""
        m = current_model()
        last_conn_try[0] = time.time()
        try:
            if manual:
                log(tr("log_connecting", name=m["name"]))
            mouse.connect(m, log=(log if manual else (lambda s: None)))
        except Exception as e:
            if manual or str(e) != last_conn_err[0]:
                log(f"[!] {e}")
            last_conn_err[0] = str(e)
            state_conn[0] = None; render_status()
            return False
        last_conn_err[0] = None
        real = _model_for_pid(mouse.pid) or m          # modelo real (DPI max, LED...)
        mouse.model = real
        active_model[0] = real
        read_fails[0] = 0
        state_conn[0] = real["name"]; render_status()
        presets["last_model"] = model_var.get(); save_presets(presets)
        batt_supported[0] = real["wireless"]
        log(tr("log_connected_ok", name=real["name"]))
        try:
            fw = mouse.get_firmware(); state_fw[0] = f"v{fw[0]}.{fw[1]}"
        except Exception:
            pass
        refresh_battery()
        on_connected()                                 # toma el control de los perfiles
        return True

    def on_disconnected():
        stop_listener()
        try: mouse.close()
        except Exception: pass
        state_conn[0] = None; render_status()
        state_batt[0] = None; render_batt()
        render_profiles()
        log(tr("log_disconnected"))

    def refresh_battery():
        """Lee la bateria sin llenar el log (se llama sola cada minuto)."""
        if mouse.dev is None or not batt_supported[0]:
            render_batt(); return
        try:
            pct, chg = mouse.get_battery()
            state_batt[0] = (pct, chg)
        except Exception:
            pass
        render_batt()

    # =====================================================================
    # 7) PESTANAS + PERFILES
    #
    #    DOS MODOS:
    #    - CONTROL (por defecto, como Synapse): el programa pone el raton en
    #      "modo driver". El raton deja de cambiar de perfil solo y avisa al
    #      programa de cada pulsacion del boton de perfil / DPI; el programa
    #      aplica el perfil siguiente. Exacto e instantaneo. Tus 5 perfiles se
    #      guardan en el programa y se aplican al abrirlo. Los perfiles de
    #      fabrica del raton NO se tocan (el DPI se aplica sin guardar en su
    #      memoria) y al cerrar el programa el raton vuelve a su modo normal.
    #    - COMPATIBILIDAD (si Windows no deja escuchar el boton, o si lo
    #      desactivas): el perfil se deduce por el DPI que usa el raton. Nunca
    #      sobrescribe valores por su cuenta.
    # =====================================================================
    nb = ttk.Notebook(root); nb.pack(fill="both", expand=True, padx=8, pady=6)
    tab_perf = ttk.Frame(nb); nb.add(tab_perf, text="")
    tab_led  = ttk.Frame(nb); nb.add(tab_led, text="")
    tab_btn  = ttk.Frame(nb); nb.add(tab_btn, text="")
    tab_opts = ttk.Frame(nb); nb.add(tab_opts, text="")
    reg(lambda: nb.tab(tab_perf, text=tr("tab_main")))
    reg(lambda: nb.tab(tab_led, text=tr("tab_led")))
    reg(lambda: nb.tab(tab_btn, text=tr("tab_btn")))
    reg(lambda: nb.tab(tab_opts, text=tr("tab_opts")))

    DEFAULT_PROFILES = [400, 800, 1600, 3200, 6400]
    # Colores de los perfiles INTERNOS del raton (LED de debajo), en el orden en
    # que los recorre su boton de perfil (Viper Ultimate): rojo, verde, azul,
    # turquesa, amarillo. El perfil N del programa se graba en el color N.
    PROFILE_COLORS = ["#ff3b30", "#34c759", "#2f7bff", "#2ad4c8", "#ffd60a"]
    PROFILE_TEXT   = ["#ffffff", "#0b1f0f", "#ffffff", "#062a27", "#2a2200"]  # texto legible encima
    COLOR_KEYS     = ["col_red", "col_green", "col_blue", "col_turq", "col_yellow"]
    wizard_active = [False]      # el asistente de grabado esta en marcha

    # ---- estado --------------------------------------------------------------
    def _load_profiles():
        p = presets.get("profiles")
        if isinstance(p, list) and len(p) == 5:
            vals = [int(v) if v else None for v in p]
            if any(vals):
                return vals
        old = presets.get("dpi_presets")                 # migracion v1.0.0
        if presets.get("tracking") and isinstance(old, list) and len(old) == 5:
            return [int(v) for v in old]
        return list(DEFAULT_PROFILES)

    profiles = _load_profiles()
    current = [presets.get("active_profile", 0)]         # perfil activo (0-4) o None
    if current[0] is None or not (0 <= current[0] < 5) or not profiles[current[0]]:
        current[0] = next((i for i, v in enumerate(profiles) if v), 0)
    learning = [bool(presets.get("learning", False))]   # solo modo compatibilidad
    last_dpi = [None]
    ctrl_want = [bool(presets.get("control_mode", True))]   # el usuario quiere modo control
    ctrl_on = [False]            # el raton esta AHORA en modo driver con nosotros al mando
    verified = [bool(presets.get("control_verified", False))]  # ya se recibio algun boton
    verify_deadline = [None]
    listener = [None]
    last_mode_check = [0.0]

    def _save_profiles():
        presets["profiles"] = profiles
        presets["active_profile"] = current[0]
        presets["learning"] = learning[0]
        save_presets(presets)

    def _enabled():
        return [i for i, v in enumerate(profiles) if v]

    def _known():
        """{dpi: indice} de los perfiles con DPI unico."""
        vals = [v for v in profiles if v]
        return {v: i for i, v in enumerate(profiles) if v and vals.count(v) == 1}

    # ---- modo control: tomar y soltar el raton ---------------------------------
    def start_listener():
        stop_listener()
        lst = ButtonListener(mouse.pid,
                             lambda code: uiq.put(lambda c=code: on_button(c)),
                             lambda raw: uiq.put(lambda r=raw: on_other_report(r)))
        n = lst.start()
        listener[0] = lst
        return n

    def stop_listener():
        if listener[0] is not None:
            listener[0].stop()
            listener[0] = None

    def take_control():
        """Pone el raton en modo driver y aplica el perfil activo del programa.
        Devuelve False si no se puede escuchar el boton (-> compatibilidad)."""
        if mouse.dev is None:
            return False
        if start_listener() == 0:
            stop_listener()
            return False
        try:
            mouse.set_device_mode(RazerMouse.MODE_DRIVER)
        except Exception:
            stop_listener()
            return False
        ctrl_on[0] = True
        last_mode_check[0] = time.time()
        apply_profile(current[0], announce=False)
        if not verified[0]:
            verify_deadline[0] = time.time() + 25      # 25 s para pulsar el boton
            log(tr("log_ctrl_verify"))
        else:
            log(tr("log_ctrl_on"))
        return True

    def release_control(announce=True):
        """Devuelve el raton a su modo normal (sus perfiles de fabrica)."""
        stop_listener()
        verify_deadline[0] = None
        if ctrl_on[0] and mouse.dev is not None:
            try: mouse.set_device_mode(RazerMouse.MODE_NORMAL)
            except Exception: pass
            if announce:
                log(tr("log_ctrl_restored"))
        ctrl_on[0] = False

    def fall_back(reason_key):
        """No se pudo usar el modo control: pasa a compatibilidad."""
        release_control(announce=False)
        log(tr(reason_key))
        start_compat()

    def on_connected():
        if ctrl_want[0] and take_control():
            pass
        else:
            if ctrl_want[0]:
                log(tr("log_ctrl_fail"))
            start_compat()
        render_profiles()

    # ---- modo compatibilidad (deteccion por DPI, blindada) ---------------------
    def start_compat():
        ctrl_on[0] = False
        try:
            x, _ = mouse.get_dpi()
            if x > 0:
                compat_process(x, initial=True)
        except Exception:
            pass
        render_profiles()

    def compat_process(x, initial=False):
        """Deduce el perfil por el DPI. NUNCA sobrescribe un perfil ya conocido:
        si el DPI no cuadra, solo lo indica. Devuelve el indice si cambio."""
        if not initial and x == last_dpi[0]:
            return None
        prev = current[0]
        known = _known()
        if x in known:
            current[0] = known[x]
            if learning[0] and not initial and prev is not None and current[0] != prev:
                learning[0] = False
                log(tr("log_learn_done", n=len(_enabled())))
            elif current[0] != prev and not initial:
                log(tr("log_prof_changed", n=current[0] + 1, x=x))
        elif learning[0]:
            empty = [i for i, v in enumerate(profiles) if not v]
            if empty:
                idx = empty[0]; profiles[idx] = x; current[0] = idx
                log(tr("log_learned", n=idx + 1, x=x))
                if len(empty) == 1:
                    learning[0] = False
                    log(tr("log_learn_done", n=5))
            else:
                learning[0] = False
                current[0] = None
        else:
            current[0] = None                   # no cuadra: se indica, no se toca nada
            if not initial and x != last_dpi[0]:
                log(tr("log_prof_unknown", x=x))
        last_dpi[0] = x
        _save_profiles(); render_profiles()
        if not initial and current[0] is not None and current[0] != prev:
            return current[0]
        return None

    # ---- aplicar perfiles (modo control) ---------------------------------------
    def apply_profile(i, announce=True):
        """Aplica el perfil i al raton (sin tocar su memoria interna)."""
        if i is None or not (0 <= i < 5) or not profiles[i] or mouse.dev is None:
            return
        try:
            mouse.set_dpi(profiles[i], persist=False)
        except Exception as e:
            log(f"[ERROR] {e}"); return
        current[0] = i; last_dpi[0] = profiles[i]
        _save_profiles(); render_profiles()
        if announce:
            log(tr("log_prof_changed", n=i + 1, x=profiles[i]))
            if notify_var.get():
                show_toast(i)

    def step_profile(delta):
        en = _enabled()
        if not en:
            return
        cur = current[0] if current[0] in en else en[0]
        apply_profile(en[(en.index(cur) + delta) % len(en)])

    seen_unknown = set()             # para apuntar cada senal desconocida una sola vez

    def on_other_report(raw):
        """Informe del raton que no es el de botones especiales. Se apunta una vez
        por tipo, para descubrir que mandan botones remapeados (diagnostico)."""
        key = ("r", raw[0])
        if key in seen_unknown or len(seen_unknown) > 20:
            return
        seen_unknown.add(key)
        log(tr("log_btn_raw", rid=f"0x{raw[0]:02X}", data=" ".join(f"{b:02X}" for b in raw[:8])))

    def on_button(code):
        """Pulsacion recibida del raton (hilo de Tk, via cola)."""
        if not ctrl_on[0]:
            return
        if not verified[0]:
            verified[0] = True; verify_deadline[0] = None
            presets["control_verified"] = True; save_presets(presets)
            log(tr("log_ctrl_verified"))
        if code not in buttons_seen:                     # boton nuevo: aparece en la pestana
            buttons_seen.append(code)
            presets["buttons_seen"] = buttons_seen; save_presets(presets)
            log(tr("log_btn_new", name=btn_name(code)))
            build_btn_rows()
        flash_btn(code)
        exec_rep4(code)

    # ---- interfaz de la pestana Perfiles ----------------------------------------
    LBL_OFF = MUTED
    LBL_ON  = GREEN
    mode_var = tk.StringVar()
    ttk.Label(tab_perf, textvariable=mode_var, style="Muted.TLabel").pack(anchor="w", padx=12, pady=(10, 0))
    active_var = tk.StringVar()
    ttk.Label(tab_perf, textvariable=active_var, style="Active.TLabel",
              wraplength=500, justify="left").pack(anchor="w", padx=12, pady=(2, 8))

    pf = ttk.Frame(tab_perf); pf.pack(fill="x", padx=12)
    pf.columnconfigure(2, minsize=96)
    row_mark, row_name, row_entry, prof_vars = [], [], [], []
    for i in range(5):
        mk = tk.Label(pf, width=2, anchor="w", bg=BG, fg=LBL_ON, font=("Segoe UI", 10, "bold"))
        dot = tk.Label(pf, text="\u25CF", bg=BG, fg=PROFILE_COLORS[i], font=("Segoe UI", 13))
        dot.grid(row=i, column=1, sticky="w", padx=(0, 6))
        nm = tk.Label(pf, anchor="w", bg=BG, fg=LBL_OFF, font=("Segoe UI", 10), cursor="hand2")
        v = tk.StringVar(value=(str(profiles[i]) if profiles[i] else ""))
        en = ttk.Entry(pf, textvariable=v, width=8, justify="right")
        un = ttk.Label(pf, text="DPI")
        mk.grid(row=i, column=0, sticky="w", pady=2)
        nm.grid(row=i, column=2, sticky="w", pady=2)
        en.grid(row=i, column=3, sticky="w", pady=2)
        un.grid(row=i, column=4, sticky="w", padx=(6, 0), pady=2)
        nm.bind("<Button-1>", lambda _e, i=i: on_click_profile(i))
        en.bind("<Return>", lambda _e: save_profiles())
        row_mark.append(mk); row_name.append(nm); row_entry.append(en); prof_vars.append(v)

    def render_profiles():
        for i in range(5):
            on = (current[0] == i)
            row_mark[i].configure(text=("\u25B6" if on else ""))
            row_name[i].configure(text=f"{tr('profile')} {i + 1}",
                                  fg=(LBL_ON if on else (FG if profiles[i] else LBL_OFF)),
                                  font=("Segoe UI", 10, "bold" if on else "normal"))
        mode_var.set(tr("mode_ctrl") if ctrl_on[0] else tr("mode_compat"))
        try: render_btn_note()
        except NameError: pass
        if mouse.dev is None:
            active_var.set(tr("prof_wait"))
        elif ctrl_on[0] and not verified[0]:
            active_var.set(tr("prof_verify"))
        elif not ctrl_on[0] and learning[0]:
            active_var.set(tr("prof_learning", n=len(_enabled())))
        elif current[0] is not None and profiles[current[0]]:
            active_var.set(tr("prof_active", n=current[0] + 1, x=profiles[current[0]]))
        else:
            active_var.set(tr("prof_unknown", x=last_dpi[0]))
    reg(render_profiles)

    def on_click_profile(i):
        """Clic en el nombre: en modo control activa ese perfil."""
        if ctrl_on[0] and profiles[i]:
            apply_profile(i)

    def save_profiles(_e=None):
        """Lee los 5 campos, valida y guarda. Si cambia el perfil activo, lo aplica."""
        dmax = (active_model[0] or current_model())["dpi_max"]
        new = []
        for i, v in enumerate(prof_vars):
            t = v.get().strip()
            if not t:
                new.append(None); continue
            try:
                x = int(t)
            except ValueError:
                log(tr("err_dpi_range", n=i + 1, lo=DPI_MIN, hi=dmax)); return
            if not (DPI_MIN <= x <= dmax):
                log(tr("err_dpi_range", n=i + 1, lo=DPI_MIN, hi=dmax)); return
            new.append(x)
        if not any(new):
            log(tr("log_prof_none")); return
        vals = [x for x in new if x]
        if len(vals) != len(set(vals)):
            log(tr("log_dup_any"))
        changed_active = current[0] is not None and new[current[0]] != profiles[current[0]]
        profiles[:] = new
        if current[0] is None or not profiles[current[0]]:
            current[0] = _enabled()[0]; changed_active = True
        _save_profiles()
        log(tr("log_prof_saved"))
        if mouse.dev is not None and changed_active:
            if ctrl_on[0]:
                apply_profile(current[0], announce=False)
            else:                                # compatibilidad: al perfil interno activo
                try:
                    mouse.set_dpi(profiles[current[0]], persist=True)
                    last_dpi[0] = profiles[current[0]]
                except Exception as e:
                    log(f"[ERROR] {e}")
        render_profiles()

    def reset_profiles():
        """Restablece: modo control -> valores por defecto; compatibilidad ->
        borra y vuelve a aprender dando una vuelta con el boton de perfil."""
        if ctrl_on[0]:
            profiles[:] = list(DEFAULT_PROFILES)
            learning[0] = False
            for i, v in enumerate(prof_vars): v.set(str(profiles[i]))
            current[0] = 0
            apply_profile(0, announce=False)
            log(tr("log_prof_reset"))
        else:
            profiles[:] = [None] * 5
            for v in prof_vars: v.set("")
            learning[0] = True; current[0] = None; last_dpi[0] = None
            _save_profiles()
            log(tr("log_relearn"))
            start_compat()
        render_profiles()

    def sync_entries():
        """Refleja en los campos lo aprendido en modo compatibilidad."""
        for i, v in enumerate(prof_vars):
            want = str(profiles[i]) if profiles[i] else ""
            if v.get() != want and root.focus_get() is not row_entry[i]:
                v.set(want)

    pbtn = ttk.Frame(tab_perf); pbtn.pack(fill="x", padx=12, pady=(8, 2))
    reg_text(ttk.Button(pbtn, command=save_profiles), "btn_save_prof").pack(side="left", expand=True, fill="x", padx=(0, 4))
    reg_text(ttk.Button(pbtn, command=lambda: start_wizard()), "btn_burn").pack(side="left", expand=True, fill="x", padx=(4, 0))

    # ---- Asistente "Grabar en el raton" ------------------------------------------
    # Mete tus perfiles en la MEMORIA INTERNA del raton, para que al cerrar el
    # programa el raton tenga los mismos perfiles con su LED de color. Como no se
    # puede elegir la ranura por software, se hace guiado: el raton vuelve a su
    # modo normal, el usuario pone el LED de debajo en el color que toca con el
    # boton de perfil, y el programa graba ahi el DPI (y lo comprueba leyendolo).
    def start_wizard(after=None):
        if mouse.dev is None:
            log(tr("log_burn_noconn")); return
        if wizard_active[0]:
            return
        save_profiles()                               # valida y guarda lo que haya en las casillas
        todo = _enabled()
        if not todo:
            return
        wizard_active[0] = True
        was_ctrl = ctrl_on[0]
        release_control(announce=False)              # el raton gestiona sus perfiles (LED activo)
        log(tr("log_burn_start"))

        win = tk.Toplevel(root); win.configure(bg=BG); win.resizable(False, False)
        win.title(tr("burn_title")); win.transient(root)
        try:
            if os.path.exists(_ico_path): win.iconbitmap(_ico_path)
        except Exception: pass
        step = [0]
        done = []
        title = ttk.Label(win, style="H.TLabel"); title.pack(anchor="w", padx=16, pady=(14, 4))
        cv = tk.Canvas(win, width=64, height=64, bg=BG, highlightthickness=0); cv.pack(pady=4)
        msg = ttk.Label(win, wraplength=360, justify="center"); msg.pack(padx=16, pady=(4, 6))
        res = ttk.Label(win, style="Muted.TLabel", wraplength=360, justify="center"); res.pack(padx=16)
        bts = ttk.Frame(win); bts.pack(fill="x", padx=16, pady=(10, 14))
        b_cancel = ttk.Button(bts, text=tr("btn_cancel")); b_cancel.pack(side="left", expand=True, fill="x", padx=(0, 4))
        b_go = ttk.Button(bts); b_go.pack(side="left", expand=True, fill="x", padx=(4, 0))

        def show():
            if step[0] >= len(todo):
                title.configure(text=tr("burn_done_title"))
                cv.delete("all")
                for k, i in enumerate(todo):          # los colores grabados, en fila
                    cv.create_oval(4 + k * 12, 26, 14 + k * 12, 36, fill=PROFILE_COLORS[i], outline="")
                msg.configure(text=tr("burn_done_msg"))
                res.configure(text=", ".join(done))
                b_cancel.pack_forget()
                b_go.configure(text=tr("btn_close"), command=finish)
                return
            i = todo[step[0]]
            title.configure(text=tr("burn_step", n=step[0] + 1, total=len(todo)))
            cv.delete("all"); cv.create_oval(8, 8, 56, 56, fill=PROFILE_COLORS[i], outline="")
            msg.configure(text=tr("burn_msg", color=tr(COLOR_KEYS[i]).upper(), n=i + 1, x=profiles[i]))
            b_go.configure(text=tr("btn_burn_step"), command=burn)

        def burn():
            i = todo[step[0]]
            try:
                mouse.set_dpi(profiles[i], persist=True)      # VARSTORE: al perfil interno activo
                x, _ = mouse.get_dpi()
            except Exception as e:
                res.configure(text=f"[!] {e}"); return
            ok = (x == profiles[i])
            done.append(f"{tr(COLOR_KEYS[i])} {profiles[i]}{' ✓' if ok else ' ?'}")
            log(tr("log_burn_ok" if ok else "log_burn_check", color=tr(COLOR_KEYS[i]), x=profiles[i]))
            step[0] += 1
            res.configure(text=", ".join(done))
            show()

        def finish():
            wizard_active[0] = False
            try: win.destroy()
            except Exception: pass
            if step[0] >= len(todo):
                log(tr("log_burn_done"))
                presets["burned_profiles"] = list(profiles); save_presets(presets)
            else:
                log(tr("log_burn_cancel"))
            if after is not None:                    # p. ej. cerrar el programa
                root.after(100, after); return
            if mouse.dev is not None and ctrl_want[0]:
                if not take_control():
                    fall_back("log_ctrl_fail")
            elif mouse.dev is not None:
                start_compat()
            render_profiles()

        b_cancel.configure(command=finish)
        win.protocol("WM_DELETE_WINDOW", finish)
        show()
        win.update_idletasks()
        win.geometry(f"+{root.winfo_rootx() + 60}+{root.winfo_rooty() + 120}")
        try: win.grab_set()
        except Exception: pass

    reset_link = tk.Label(tab_perf, bg=BG, fg=MUTED, cursor="hand2", font=("Segoe UI", 9, "underline"))
    reset_link.pack(anchor="e", padx=12, pady=(4, 0))
    reset_link.bind("<Button-1>", lambda _e: reset_profiles())
    reset_link.bind("<Enter>", lambda _e: reset_link.configure(fg=ACCENT2))
    reset_link.bind("<Leave>", lambda _e: reset_link.configure(fg=MUTED))
    reg(lambda: reset_link.configure(text="\u21BB " + tr("btn_reset_prof")))

    ttk.Separator(tab_perf).pack(fill="x", padx=12, pady=8)

    # ---- Tasa de sondeo -------------------------------------------------------
    prow = ttk.Frame(tab_perf); prow.pack(fill="x", padx=12, pady=(0, 10))
    reg_text(ttk.Label(prow), "poll_lbl").pack(side="left")
    poll_var = tk.IntVar(value=presets.get("poll_rate", 1000))
    ttk.Combobox(prow, textvariable=poll_var, width=7, state="readonly",
                 values=[125, 500, 1000]).pack(side="left", padx=8)
    ttk.Label(prow, text="Hz").pack(side="left")

    @guard
    def do_set_poll():
        code = mouse.set_poll_rate(int(poll_var.get()))
        presets["poll_rate"] = int(poll_var.get()); save_presets(presets)
        log(tr("log_poll", hz=poll_var.get(), st=st_name(code)))
    reg_text(ttk.Button(prow, command=do_set_poll), "btn_apply").pack(side="right")

    # ---- Opciones > Raton ---------------------------------------------------------
    reg_text(ttk.Label(tab_opts, style="H.TLabel"), "mouse_hdr").pack(anchor="w", padx=12, pady=(12, 2))
    mrow = ttk.Frame(tab_opts); mrow.pack(fill="x", padx=12)
    reg_text(ttk.Label(mrow), "model_lbl").pack(side="left")
    model_combo = ttk.Combobox(mrow, textvariable=model_var, values=model_names,
                               state="readonly", width=26)
    model_combo.pack(side="left", padx=6)

    def reconnect(_e=None):
        if mouse.dev is not None:
            release_control(announce=False)
            try: mouse.close()
            except Exception: pass
            state_conn[0] = None; render_status()
        connect_mouse(manual=True)
    model_combo.bind("<<ComboboxSelected>>", reconnect)
    reg_text(ttk.Button(mrow, command=reconnect), "btn_reconnect").pack(side="right")

    ctrl_var = tk.BooleanVar(value=ctrl_want[0])
    def _toggle_ctrl(*_):
        ctrl_want[0] = ctrl_var.get()
        presets["control_mode"] = ctrl_want[0]; save_presets(presets)
        if mouse.dev is None:
            return
        if ctrl_want[0] and not ctrl_on[0]:
            if not take_control():
                fall_back("log_ctrl_fail")
        elif not ctrl_want[0] and ctrl_on[0]:
            release_control()
            start_compat()
        render_profiles()
    ctrl_var.trace_add("write", _toggle_ctrl)
    reg_text(ttk.Checkbutton(tab_opts, variable=ctrl_var), "chk_control").pack(anchor="w", padx=12, pady=(4, 0))

    notify_var = tk.BooleanVar(value=presets.get("notify_popup", False))
    def _save_notify(*_):
        presets["notify_popup"] = notify_var.get(); save_presets(presets)
    notify_var.trace_add("write", _save_notify)
    reg_text(ttk.Checkbutton(tab_opts, variable=notify_var), "chk_notify").pack(anchor="w", padx=12, pady=(0, 0))
    ask_exit_var = tk.BooleanVar(value=presets.get("ask_burn_on_exit", True))
    def _save_ask(*_):
        presets["ask_burn_on_exit"] = ask_exit_var.get(); save_presets(presets)
    ask_exit_var.trace_add("write", _save_ask)
    reg_text(ttk.Checkbutton(tab_opts, variable=ask_exit_var), "chk_ask_exit").pack(anchor="w", padx=12, pady=(0, 0))

    ttk.Separator(tab_opts).pack(fill="x", padx=12, pady=8)

    # ---- Pestana Mapeo ------------------------------------------------------------
    # Dos familias de botones:
    #  1) Botones que Windows deja interceptar (central, laterales, inclinacion de
    #     la rueda): remapeo POR SOFTWARE con un gancho de Windows. Desactivado por
    #     defecto; funciona con el programa abierto; aun no se guarda en el raton.
    #  2) Botones especiales que el raton comunica al programa en modo control
    #     (perfil, DPI, y los remapeados en Synapse si el raton los comunica).
    #     Aparecen solos al pulsarlos.
    # Los clics izquierdo y derecho no se remapean nunca (seguridad).
    DEFAULT_BTN_MAP = {REP4_PROFILE: "next", REP4_DPI_CYCLE: "next",
                       REP4_DPI_UP: "next", REP4_DPI_DN: "prev"}
    PRESET_ACTIONS = (["default", "none", "next", "prev", "p1", "p2", "p3", "p4", "p5",
                       "click_left", "click_right", "click_middle", "click_back", "click_forward",
                       "dblclick", "key:ctrl+c", "key:ctrl+v", "key:ctrl+x", "key:ctrl+z",
                       "key:ctrl+y", "key:enter", "key:esc", "key:tab", "key:space",
                       "key:alt+tab", "key:win+d", "key:printscreen", "key:media_play",
                       "key:media_next", "key:media_prev", "key:vol_up", "key:vol_down",
                       "key:vol_mute"])
    ACTION_KEYS = {"default": "act_default", "none": "act_none", "next": "act_next", "prev": "act_prev",
                   "click_left": "act_lclick", "click_right": "act_rclick", "click_middle": "act_mclick",
                   "click_back": "act_back", "click_forward": "act_forward", "dblclick": "act_dbl",
                   "key:ctrl+c": "act_copy", "key:ctrl+v": "act_paste", "key:ctrl+x": "act_cut",
                   "key:ctrl+z": "act_undo", "key:ctrl+y": "act_redo", "key:enter": "act_enter",
                   "key:esc": "act_esc", "key:tab": "act_tab", "key:space": "act_space",
                   "key:alt+tab": "act_alttab", "key:win+d": "act_desktop",
                   "key:printscreen": "act_prtsc", "key:media_play": "act_play",
                   "key:media_next": "act_nexttrk", "key:media_prev": "act_prevtrk",
                   "key:vol_up": "act_volup", "key:vol_down": "act_voldn", "key:vol_mute": "act_mute"}
    SOFT_NAME_KEYS = {"middle": "sb_middle", "wheel_up": "sb_wup", "wheel_down": "sb_wdn",
                      "x1": "sb_x1", "x2": "sb_x2", "tilt_l": "sb_tiltl", "tilt_r": "sb_tiltr"}
    BTN_NAME_KEYS = {REP4_PROFILE: "bn_profile", REP4_DPI_CYCLE: "bn_dpicycle",
                     REP4_DPI_UP: "bn_dpiup", REP4_DPI_DN: "bn_dpidn", 0x51: "bn_sniper",
                     0x22: "bn_tiltl", 0x23: "bn_tiltr", 0x54: "bn_scroll"}

    def _valid_action(a):
        return isinstance(a, str) and (a in PRESET_ACTIONS or
                                       (a.startswith("key:") and parse_combo(a[4:]) is not None))

    button_map = {int(k): v for k, v in presets.get("button_map", {}).items() if _valid_action(v)}
    soft_map = {k: v for k, v in presets.get("soft_map", {}).items() if k in SOFT_BUTTONS and _valid_action(v)}
    soft_seen = set(presets.get("soft_seen", []))      # botones "si existen" ya vistos
    buttons_seen = [int(c) for c in presets.get("buttons_seen", [REP4_PROFILE])][:10]

    def btn_name(code):
        # En las Viper (ambidiestras, sin rueda inclinable) los codigos que OpenRazer
        # llama "inclinacion" (0x22/0x23 = atras/adelante) son los LATERALES DERECHOS.
        mdl = (active_model[0] or current_model())["name"]
        if "Viper" in mdl and code in (0x22, 0x23):
            return tr("bn_rside_dn" if code == 0x22 else "bn_rside_up")
        k = BTN_NAME_KEYS.get(code)
        return tr(k) if k else tr("bn_unknown", code=f"0x{code:02X}")

    def act_label(a):
        if a in ACTION_KEYS:
            return tr(ACTION_KEYS[a])
        if a.startswith("p") and a[1:].isdigit():
            return f"{tr('profile')} {a[1]}"
        if a.startswith("key:"):
            return tr("act_keys", keys=a[4:])
        return a

    def run_action(a):
        """Acciones de perfil (siempre en el hilo de Tk)."""
        if a == "next": step_profile(+1)
        elif a == "prev": step_profile(-1)
        elif a.startswith("p") and a[1:].isdigit():
            i = int(a[1]) - 1
            if profiles[i]: apply_profile(i)

    last_prof_act = [0.0]

    def exec_action(a, down, has_up):
        """Ejecuta una accion. down/has_up permiten mantener pulsado (teclas y
        clics se sueltan cuando se suelta el boton original)."""
        if a in ("none", "default"):
            return
        if a in ("next", "prev") or (a.startswith("p") and a[1:].isdigit()):
            now = time.time()
            if down and now - last_prof_act[0] >= 0.25:     # un giro de rueda = un solo cambio
                last_prof_act[0] = now
                uiq.put(lambda a=a: run_action(a))
            return
        if not SoftRemapper.supported():
            return
        if a == "dblclick":
            if down:
                for _ in range(2):
                    send_input_mouse("click_left", True); send_input_mouse("click_left", False)
            return
        if a in MOUSE_FLAGS:
            if has_up:
                send_input_mouse(a, down)
            elif down:
                send_input_mouse(a, True); send_input_mouse(a, False)
            return
        if a.startswith("key:"):
            vks = parse_combo(a[4:])
            if not vks:
                return
            if has_up:
                send_input_keys(vks, down)
            elif down:
                send_input_keys(vks, True); send_input_keys(vks, False)

    def exec_rep4(code):
        a = button_map.get(code, "default")
        if a == "default":
            a = DEFAULT_BTN_MAP.get(code, "none")
        exec_action(a, True, False)

    # --- gancho de Windows ---
    remapper = SoftRemapper(get_action=lambda b: soft_map.get(b, "default"),
                            on_ui=lambda b: uiq.put(lambda b=b: on_soft_seen(b)),
                            do_action=exec_action)
    SOFT_OK = SoftRemapper.supported()

    st.configure("Warn.TLabel", background=BG, foreground=YELL)
    reg_text(ttk.Label(tab_btn, style="Warn.TLabel", wraplength=510, justify="left"),
             "map_warn").pack(anchor="w", padx=12, pady=(10, 4))
    soft_var = tk.BooleanVar(value=bool(presets.get("soft_remap", False)) and SOFT_OK)
    soft_chk = ttk.Checkbutton(tab_btn, variable=soft_var, state=("normal" if SOFT_OK else "disabled"))
    soft_chk.pack(anchor="w", padx=12)
    reg(lambda: soft_chk.configure(text=tr("chk_soft" if SOFT_OK else "chk_soft_na")))

    def _toggle_soft(*_):
        presets["soft_remap"] = soft_var.get(); save_presets(presets)
        if soft_var.get():
            if remapper.start():
                log(tr("log_soft_on"))
            else:
                log(tr("log_soft_fail")); soft_var.set(False)
        else:
            remapper.stop(); log(tr("log_soft_off"))
    soft_var.trace_add("write", _toggle_soft)

    btn_rows = ttk.Frame(tab_btn); btn_rows.pack(fill="x", padx=12, pady=(6, 0))
    btn_rows.columnconfigure(1, minsize=200)
    btn_flash = {}
    btn_note = ttk.Label(tab_btn, style="Muted.TLabel", wraplength=510, justify="left")

    def render_btn_note():
        if ctrl_on[0]:
            btn_note.pack_forget()
        else:
            btn_note.configure(text=tr("btn_compat"))
            btn_note.pack(anchor="w", padx=12, pady=(6, 0))

    def _row(r, key, name, cur, is_soft, store):
        fl = tk.Label(btn_rows, text="\u25CF", bg=BG, fg=LBL_OFF, font=("Segoe UI", 11))
        fl.grid(row=r, column=0, sticky="w", padx=(0, 6), pady=1)
        ttk.Label(btn_rows, text=name).grid(row=r, column=1, sticky="w", pady=1)
        acts = list(PRESET_ACTIONS)
        if cur.startswith("key:") and cur not in acts:
            acts.append(cur)                       # combinacion personalizada guardada
        acts.append("custom")
        def _lab(a):
            if a == "custom":
                return tr("act_custom")
            if a == "default" and not is_soft:          # especial: decir que hace por defecto
                return tr("act_default_rep4", act=act_label(DEFAULT_BTN_MAP.get(key, "none")))
            return act_label(a)
        labels = [_lab(a) for a in acts]
        cb = ttk.Combobox(btn_rows, state="readonly", width=24, values=labels, height=16)
        cb.current(acts.index(cur) if cur in acts else 0)
        cb.grid(row=r, column=2, sticky="w", pady=1)

        def on_sel(_e, key=key, cb=cb, acts=acts, name=name, labels=labels):
            a = acts[cb.current()]
            if a == "custom":
                from tkinter import simpledialog
                txt = simpledialog.askstring(tr("custom_title"), tr("custom_prompt"), parent=root)
                if not txt or parse_combo(txt) is None:
                    if txt:
                        log(tr("log_custom_bad", keys=txt))
                    build_btn_rows(); return
                a = "key:" + "+".join(p.strip().lower() for p in txt.replace("-", "+").split("+") if p.strip())
            store[key] = a
            if is_soft:
                presets["soft_map"] = dict(soft_map)
            else:
                presets["button_map"] = {str(k): v for k, v in button_map.items()}
            save_presets(presets)
            log(tr("log_btn_set", name=name, act=(labels[acts.index(a)] if a in acts else act_label(a))))
            build_btn_rows()
        cb.bind("<<ComboboxSelected>>", on_sel)
        btn_flash[key] = fl

    def build_btn_rows():
        for w in btn_rows.winfo_children():
            w.destroy()
        btn_flash.clear()
        r = 0
        for b in SOFT_BUTTONS:
            if b in SOFT_ONLY_IF_SEEN and b not in soft_seen:
                continue
            _row(r, b, tr(SOFT_NAME_KEYS[b]), soft_map.get(b, "default"), True, soft_map); r += 1
        ttk.Separator(btn_rows).grid(row=r, column=0, columnspan=3, sticky="ew", pady=(6, 2)); r += 1
        ttk.Label(btn_rows, text=tr("map_hdr_rep4"), style="Muted.TLabel", wraplength=500,
                  justify="left").grid(row=r, column=0, columnspan=3, sticky="w", pady=(0, 2)); r += 1
        for code in buttons_seen:
            _row(r, code, btn_name(code), button_map.get(code, "default"), False, button_map); r += 1
        render_btn_note()
    reg(build_btn_rows)

    def on_soft_seen(b):
        if b in SOFT_ONLY_IF_SEEN and b not in soft_seen:
            soft_seen.add(b)
            presets["soft_seen"] = sorted(soft_seen); save_presets(presets)
            build_btn_rows()
        flash_btn(b)

    def flash_btn(key):
        fl = btn_flash.get(key)
        if fl is None or not fl.winfo_exists(): return
        fl.configure(fg=GREEN)
        root.after(600, lambda: fl.winfo_exists() and fl.configure(fg=LBL_OFF))

    render_btn_note()

    if soft_var.get():
        root.after(500, lambda: (remapper.start() and log(tr("log_soft_on"))) or None)

    # ---- Aviso emergente (toast) ---------------------------------------------
    toast_win = [None]
    toast_after = [None]

    def show_toast(i):
        text = tr("toast", n=i + 1, x=profiles[i] or last_dpi[0])
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
        tw._lbl.configure(text=text, bg=PROFILE_COLORS[i], fg=PROFILE_TEXT[i])
        tw.update_idletasks()
        w, h = tw.winfo_reqwidth(), tw.winfo_reqheight()
        sw, sh = tw.winfo_screenwidth(), tw.winfo_screenheight()
        tw.geometry(f"+{sw - w - 28}+{sh - h - 70}")   # esquina inferior derecha
        tw.deiconify(); tw.lift()
        if toast_after[0]:
            try: root.after_cancel(toast_after[0])
            except Exception: pass
        toast_after[0] = root.after(2000, lambda: tw.winfo_exists() and tw.withdraw())

    # al salir del programa (aunque sea por un error), devolver el raton a su
    # modo normal para no dejar su boton de perfil "muerto"
    import atexit
    atexit.register(lambda: release_control(announce=False))

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
        led_color[0] = list(rgb); led_on[0] = True
        swatch.configure(bg=_hex(rgb)); hex_var.set(_hex(rgb))
        presets["led_color"] = list(rgb); save_presets(presets)
        mouse.set_color(*rgb)
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
    # 9) BUCLE AUTOMATICO (cada 1,5 s)
    #    - Sin raton: reintenta conectar cada 5 s.
    #    - Modo control: comprueba cada 3 s que el raton sigue en modo driver
    #      (si se ha dormido/reiniciado, retoma el control y reaplica el
    #      perfil) y vigila la desconexion. Funciona aunque este en la bandeja.
    #      Si nunca llega ninguna pulsacion en 25 s tras activarlo por primera
    #      vez, pasa a compatibilidad.
    #    - Modo compatibilidad: lee el DPI con la ventana visible (o siempre si
    #      el aviso emergente esta activo).
    #    - Bateria: se refresca sola cada minuto con la ventana visible.
    # =====================================================================
    POLL_MS = 1500
    RECONNECT_S = 5
    MODE_CHECK_S = 3
    BATT_S = 60
    last_batt = [time.time()]

    def _window_active():
        try:
            return root.state() not in ("iconic", "withdrawn")
        except Exception:
            return False

    def _read_fail():
        read_fails[0] += 1
        if read_fails[0] >= 3:
            read_fails[0] = 0
            ctrl_on[0] = False
            on_disconnected()

    def auto_tick():
        try:
            now = time.time()
            if wizard_active[0]:
                pass                                   # el asistente manda: no tocar el raton
            elif mouse.dev is None:
                if now - last_conn_try[0] >= RECONNECT_S:
                    connect_mouse(manual=False)
            elif ctrl_on[0]:
                if verify_deadline[0] and not _window_active():
                    verify_deadline[0] += POLL_MS / 1000.0   # la cuenta atras solo corre con la ventana visible
                if verify_deadline[0] and now > verify_deadline[0]:
                    fall_back("log_ctrl_noevents")
                elif listener[0] is not None and not listener[0].alive():
                    fall_back("log_ctrl_fail")
                elif now - last_mode_check[0] >= MODE_CHECK_S:
                    last_mode_check[0] = now
                    try:
                        mode = mouse.get_device_mode()
                        x, _ = mouse.get_dpi()
                    except Exception:
                        _read_fail()
                    else:
                        read_fails[0] = 0
                        if mode != RazerMouse.MODE_DRIVER:
                            log(tr("log_ctrl_reapply"))
                            try: mouse.set_device_mode(RazerMouse.MODE_DRIVER)
                            except Exception: pass
                            apply_profile(current[0], announce=False)
                        elif current[0] is not None and profiles[current[0]] and x != profiles[current[0]]:
                            apply_profile(current[0], announce=False)
            else:
                notify_on = notify_var.get()
                if notify_on or _window_active():
                    try:
                        x, _ = mouse.get_dpi()
                        if x <= 0:
                            raise RuntimeError("DPI 0")
                    except Exception:
                        _read_fail()
                    else:
                        read_fails[0] = 0
                        changed = compat_process(x)
                        sync_entries()
                        if changed is not None and notify_on:
                            show_toast(changed)
            if mouse.dev is not None and _window_active() and now - last_batt[0] >= BATT_S:
                last_batt[0] = now
                refresh_battery()
        except Exception as e:
            log(f"[ERROR] {e}")
        finally:
            root.after(POLL_MS, auto_tick)

    root.after(POLL_MS, auto_tick)

    # =====================================================================
    # 9b) PESTANA OPCIONES: bandeja, arranque con Windows, actualizaciones,
    #     reporte de errores. Los hilos secundarios (red, bandeja) NUNCA tocan
    #     widgets: dejan funciones en `uiq` y el hilo de Tk las ejecuta (pump_ui).
    # =====================================================================
    uiq = queue.Queue()

    def pump_ui():
        try:
            while True:
                uiq.get_nowait()()
        except queue.Empty:
            pass
        except Exception as e:
            log(f"[ERROR] {e}")
        root.after(150, pump_ui)

    # --- bandeja del sistema (pystray + Pillow, opcionales) --------------
    try:
        import pystray
        from PIL import Image, ImageDraw
        TRAY_OK = True
    except Exception:
        TRAY_OK = False
    tray = [None]

    def _tray_image():
        """Imagen de la bandeja: icono.ico si existe; si no, se dibuja uno."""
        try:
            if os.path.exists(_ico_path):
                return Image.open(_ico_path)
        except Exception:
            pass
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((2, 2, 62, 62), fill=(69, 247, 46, 255))
        d.ellipse((22, 22, 42, 42), fill=(0, 0, 0, 255))
        d.line((14, 14, 50, 50), fill=(255, 0, 0, 255), width=8)
        d.line((50, 14, 14, 50), fill=(255, 0, 0, 255), width=8)
        return img

    def show_window():
        if tray[0] is not None:
            try: tray[0].stop()
            except Exception: pass
            tray[0] = None
        root.deiconify(); root.state("normal"); root.lift()
        try: root.focus_force()
        except Exception: pass

    def quit_app():
        if tray[0] is not None:
            try: tray[0].stop()
            except Exception: pass
            tray[0] = None
        try: remapper.stop()                # quita el gancho de Windows
        except Exception: pass
        release_control(announce=False)     # el raton vuelve a su modo normal
        try: mouse.close()
        except Exception: pass
        root.destroy()

    def request_quit():
        """Al cerrar: si hay perfiles sin grabar en el raton, ofrece grabarlos
        (asistente de colores) antes de salir."""
        if (ask_exit_var.get() and mouse.dev is not None and not wizard_active[0]
                and presets.get("burned_profiles") != profiles):
            show_window()
            ans = messagebox.askyesnocancel(tr("dlg_exit_title"), tr("dlg_exit_msg"))
            if ans is None:                           # Cancelar: no se cierra
                return
            if ans:
                start_wizard(after=quit_app)
                return
        quit_app()

    def to_tray():
        if not TRAY_OK or tray[0] is not None:
            return
        root.withdraw()
        menu = pystray.Menu(
            pystray.MenuItem(tr("tray_show"), lambda i, it: uiq.put(show_window), default=True),
            pystray.MenuItem(tr("tray_quit"), lambda i, it: uiq.put(request_quit)),
        )
        icon = pystray.Icon(APP_NAME, _tray_image(), f"{APP_NAME} v{APP_VERSION}", menu)
        tray[0] = icon
        icon.run_detached()                      # corre en su propio hilo
        log(tr("log_tray"))

    def on_unmap(e):
        # los bindings de la ventana raiz tambien reciben eventos de sus hijos:
        # solo nos interesa cuando se minimiza la ventana principal
        if e.widget is root and tray_var.get() and TRAY_OK:
            root.after(10, lambda: root.state() == "iconic" and to_tray())
    root.bind("<Unmap>", on_unmap, add="+")

    reg_text(ttk.Label(tab_opts, style="H.TLabel"), "sys_hdr").pack(anchor="w", padx=12, pady=(12, 2))
    tray_var = tk.BooleanVar(value=bool(presets.get("tray", False)) and TRAY_OK)
    def _save_tray(*_):
        presets["tray"] = tray_var.get(); save_presets(presets)
    tray_var.trace_add("write", _save_tray)
    tray_chk = ttk.Checkbutton(tab_opts, variable=tray_var,
                               state=("normal" if TRAY_OK else "disabled"))
    tray_chk.pack(anchor="w", padx=12)
    reg(lambda: tray_chk.configure(text=tr("opt_tray" if TRAY_OK else "opt_tray_na")))

    # --- arranque con Windows ---------------------------------------------
    AUTOSTART_OK = autostart_supported()
    autostart_var = tk.BooleanVar(value=autostart_enabled())
    _autostart_busy = [False]
    def _toggle_autostart(*_):
        if _autostart_busy[0]:
            return
        want = autostart_var.get()
        try:
            set_autostart(want)
            log(tr("log_autostart_on" if want else "log_autostart_off"))
        except Exception as e:
            log(tr("log_autostart_err", e=e))
            _autostart_busy[0] = True            # revierte la casilla sin re-disparar
            autostart_var.set(not want)
            _autostart_busy[0] = False
    autostart_var.trace_add("write", _toggle_autostart)
    auto_chk = ttk.Checkbutton(tab_opts, variable=autostart_var,
                               state=("normal" if AUTOSTART_OK else "disabled"))
    auto_chk.pack(anchor="w", padx=12)
    reg(lambda: auto_chk.configure(text=tr("opt_autostart" if AUTOSTART_OK else "opt_autostart_na")))

    ttk.Separator(tab_opts).pack(fill="x", padx=12, pady=8)

    # --- actualizaciones ---------------------------------------------------
    reg_text(ttk.Label(tab_opts, style="H.TLabel"), "upd_hdr").pack(anchor="w", padx=12, pady=(0, 2))
    upd_start_var = tk.BooleanVar(value=presets.get("check_updates", True))
    def _save_upd(*_):
        presets["check_updates"] = upd_start_var.get(); save_presets(presets)
    upd_start_var.trace_add("write", _save_upd)
    reg_text(ttk.Checkbutton(tab_opts, variable=upd_start_var), "opt_upd_start").pack(anchor="w", padx=12)

    # estado de la comprobacion (para repintar al cambiar de idioma):
    #   ("idle",) ("checking",) ("latest",) ("err",) ("new", tag, page, exe_url) ("dl", tag)
    state_upd = [("idle",)]
    upd_var = tk.StringVar()
    upd_lbl = ttk.Label(tab_opts, textvariable=upd_var, style="Muted.TLabel")
    upd_lbl.pack(anchor="w", padx=12, pady=(4, 2))

    def render_upd():
        st = state_upd[0]
        if st[0] == "checking":
            upd_var.set(tr("upd_checking")); upd_lbl.configure(style="Muted.TLabel")
        elif st[0] == "latest":
            upd_var.set(tr("upd_latest", v=APP_VERSION)); upd_lbl.configure(style="Muted.TLabel")
        elif st[0] == "err":
            upd_var.set(tr("upd_err")); upd_lbl.configure(style="Muted.TLabel")
        elif st[0] == "new":
            upd_var.set(tr("upd_new", tag=st[1])); upd_lbl.configure(style="Active.TLabel")
        elif st[0] == "dl":
            upd_var.set(tr("upd_downloading", tag=st[1])); upd_lbl.configure(style="Muted.TLabel")
        else:
            upd_var.set(tr("upd_idle", v=APP_VERSION)); upd_lbl.configure(style="Muted.TLabel")
        try:
            install_btn.configure(state=("normal" if st[0] == "new" else "disabled"))
        except NameError:
            pass
    reg(render_upd)

    def check_updates(manual=False):
        if state_upd[0][0] in ("checking", "dl"):
            return
        state_upd[0] = ("checking",); render_upd()

        def worker():
            try:
                tag, page, exe_url = fetch_latest_release()
                uiq.put(lambda: _upd_result(tag, page, exe_url, manual))
            except Exception as e:
                uiq.put(lambda e=e: _upd_error(e, manual))
        threading.Thread(target=worker, daemon=True).start()

    def _upd_result(tag, page, exe_url, manual):
        if parse_version(tag) > parse_version(APP_VERSION):
            state_upd[0] = ("new", tag, page, exe_url); render_upd()
            log(tr("log_upd_new", tag=tag, v=APP_VERSION))
            if manual:
                install_update()
        else:
            state_upd[0] = ("latest",); render_upd()
            if manual:
                log(tr("log_upd_latest", v=APP_VERSION))
                messagebox.showinfo(tr("dlg_uptodate_title"), tr("dlg_uptodate_msg", v=APP_VERSION))

    def _upd_error(e, manual):
        state_upd[0] = ("err",); render_upd()
        if manual:
            log(tr("log_upd_err", e=e))

    def install_update():
        """Descarga el .exe nuevo junto al actual (sin borrar el viejo) y ofrece
        abrirlo. Con el script de Python, abre la pagina de la version."""
        st = state_upd[0]
        if st[0] != "new":
            return
        _, tag, page, exe_url = st
        if not getattr(sys, "frozen", False) or not exe_url:
            messagebox.showinfo(tr("dlg_upd_title"), tr("dlg_upd_script"))
            try: webbrowser.open_new(page)
            except Exception as e: log(tr("log_browser_err", e=e))
            return
        if not messagebox.askyesno(tr("dlg_upd_title"), tr("dlg_upd_msg", tag=tag, v=APP_VERSION)):
            return
        safe_tag = "".join(ch for ch in tag if ch.isalnum() or ch in "._-") or "new"
        dest = os.path.join(os.path.dirname(sys.executable), f"{APP_NAME}_{safe_tag}.exe")
        state_upd[0] = ("dl", tag); render_upd()

        def worker():
            try:
                download_file(exe_url, dest)
                uiq.put(lambda: _upd_downloaded(dest, st))
            except Exception as e:
                uiq.put(lambda e=e: _upd_dl_error(e, st))
        threading.Thread(target=worker, daemon=True).start()

    def _upd_downloaded(dest, prev_state):
        state_upd[0] = prev_state; render_upd()
        log(tr("log_upd_saved", path=dest))
        if messagebox.askyesno(tr("dlg_upd_done_title"), tr("dlg_upd_done_msg", path=dest)):
            try:
                release_single_instance()   # si no, la nueva creeria que ya hay una abierta
                subprocess.Popen([dest], close_fds=True)
                quit_app()
            except Exception as e:
                log(tr("log_upd_dl_err", e=e))

    def _upd_dl_error(e, prev_state):
        state_upd[0] = prev_state; render_upd()
        log(tr("log_upd_dl_err", e=e))

    ubtns = ttk.Frame(tab_opts); ubtns.pack(fill="x", padx=12, pady=(2, 4))
    reg_text(ttk.Button(ubtns, command=lambda: check_updates(True)), "btn_check_upd").pack(
        side="left", expand=True, fill="x", padx=(0, 4))
    install_btn = ttk.Button(ubtns, command=install_update, state="disabled")
    install_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))
    reg(lambda: install_btn.configure(text=tr("btn_install_upd")))
    render_upd()

    # --- reportar errores (enlace fijo abajo a la derecha) --------------------- ----------------------------------------------------
    def report_bug(_e=None):
        """Abre un 'issue' nuevo en GitHub con los datos tecnicos ya rellenos
        (version, sistema, modelo, firmware y las ultimas lineas del log).
        No se envia nada automaticamente: el usuario lo revisa en el navegador."""
        try:
            tail = logbox.get("1.0", "end").strip().splitlines()[-15:]
        except Exception:
            tail = []
        body = (
            "**What happened? / ¿Qué ha pasado?**\n\n\n"
            "**Steps to reproduce / Pasos para reproducirlo**\n1. \n\n"
            "---\n**Environment (auto)**\n"
            f"- App: v{APP_VERSION} ({'exe' if getattr(sys, 'frozen', False) else 'script'})\n"
            f"- OS: {platform.platform()}\n"
            f"- Model: {model_var.get()}\n"
            f"- Firmware: {state_fw[0]}\n"
            f"- Language: {lang[0]}\n\n"
            "**Last log lines**\n```\n" + "\n".join(tail) + "\n```\n"
        )
        url = ISSUES_URL + "?" + urllib.parse.urlencode({"title": "[Bug] ", "body": body[:6000]})
        log(tr("log_bug_opened"))
        try: webbrowser.open_new(url)
        except Exception as e: log(tr("log_browser_err", e=e))


    # =====================================================================
    # 10) LOG + DONACION (Ko-fi) + REPORTAR ERROR
    # =====================================================================
    ttk.Separator(root).pack(fill="x", padx=12, pady=(2, 4))
    reg_text(ttk.Label(root, style="Muted.TLabel"), "log_lbl").pack(anchor="w", padx=14)
    logbox = tk.Text(root, height=5, width=54, state="disabled", bg=LOGBG, fg=LOGFG,
                     font=("Consolas", 9), relief="flat", highlightthickness=0, bd=0, padx=8, pady=6,
                     wrap="word")
    logbox.pack(fill="x", expand=False, padx=12, pady=(4, 8))

    def open_kofi(_e=None):
        try: webbrowser.open_new(KOFI_URL)
        except Exception as e: log(tr("log_browser_err", e=e))

    ttk.Separator(root).pack(fill="x", padx=12, pady=(2, 4))
    foot = ttk.Frame(root); foot.pack(fill="x", padx=12, pady=(0, 8))
    kofi_link = tk.Label(foot, bg=BG, fg=MUTED, cursor="hand2",
                         font=("Segoe UI", 9, "underline"))
    kofi_link.pack(side="left")
    kofi_link.bind("<Button-1>", open_kofi)
    kofi_link.bind("<Enter>", lambda _e: kofi_link.configure(fg=ACCENT2))
    kofi_link.bind("<Leave>", lambda _e: kofi_link.configure(fg=MUTED))
    reg(lambda: kofi_link.configure(text=tr("kofi_link")))

    bug_link = tk.Label(foot, bg=BG, fg=MUTED, cursor="hand2",
                        font=("Segoe UI", 9, "underline"))
    bug_link.pack(side="right")
    bug_link.bind("<Button-1>", report_bug)
    bug_link.bind("<Enter>", lambda _e: bug_link.configure(fg=ACCENT2))
    bug_link.bind("<Leave>", lambda _e: bug_link.configure(fg=MUTED))
    reg(lambda: bug_link.configure(text=tr("bug_link")))

    # mensajes iniciales del log (en el idioma activo)
    # instrucciones iniciales: siempre en ingles (lo que venga despues sigue
    # el idioma elegido)
    log("Welcome! Close Razer Synapse and plug in your mouse.")
    log("While open, the app runs your profiles: switch them")
    log("with the mouse's profile button, edit them here.")

    # =====================================================================
    # 11) TAMANO FIJO: medir el contenido y bloquear la ventana a ese tamano
    # =====================================================================
    root.update_idletasks()
    root.geometry(f"{max(480, root.winfo_reqwidth())}x{root.winfo_reqheight()}")
    root.resizable(False, False)

    # =====================================================================
    # 12) ARRANQUE
    # =====================================================================
    root.after(150, pump_ui)                     # ejecuta lo que dejan los hilos
    root.protocol("WM_DELETE_WINDOW", request_quit)  # pregunta si grabar y cierra limpio

    # si el arranque con Windows esta activo, refresca la ruta (por si el .exe
    # se ha movido o se ha actualizado a otro nombre)
    if autostart_enabled():
        try: set_autostart(True)
        except Exception: pass

    if upd_start_var.get():
        root.after(2500, lambda: check_updates(False))

    # lanzado por el arranque de Windows: a la bandeja (o minimizado) y conecta
    if "--minimized" in sys.argv:
        if TRAY_OK:
            root.after(50, to_tray)
        else:
            root.iconify()

    root.after(300, lambda: connect_mouse(manual=False))   # conexion automatica

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
