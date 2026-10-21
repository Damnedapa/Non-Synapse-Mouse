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
  - Interfaz bilingüe español / inglés (interruptor ES|EN en la barra lateral;
    inglés por defecto).
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
  - (v1.2.0) Interfaz nueva estilo Configuración de Windows 11 (modo oscuro):
    barra lateral, tarjetas-fila, interruptores, cambios que se aplican al
    momento, aviso de perfil con barra de 5 tramos y escalado nítido (DPI).
  - (v1.3.0) Ventana redimensionable (recuerda tamaño y posición), silueta del
    ratón suavizada, avisos de batería (arriba a la derecha), parpadeo del logo
    al cambiar de perfil, botón «sniper» asignable, menú de la bandeja con
    perfiles, selector de tema, bienvenida y novedades.
  - (v1.4.0) Sistema de temas (colores + forma de las piezas, temas propios en
    .json), modo claro, piezas redondeadas suavizadas (adiós dientes de sierra),
    selector de color con disco, botones en gris si su familia esta apagada,
    Ko-fi en la barra lateral y registro siempre en inglés. Depuración: solo
    se aceptan respuestas del ratón que contesten a la orden enviada y con
    estado OK (adiós al 0 % de batería falso), lecturas periódicas y cambios de
    DPI en hilos propios (la ventana no se congela), pulsaciones rápidas que ya
    no se pierden y configuración que se guarda de forma segura.
    (La 1.4.0 es la primera pública desde la 1.0.0: la 1.1, 1.2 y 1.3 fueron
    versiones internas de desarrollo.)
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
import math
import base64
import re

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

# --- Modo Mediavida (secreto: se desbloquea con el codigo Konami) ---------------
MV_BASE = "https://www.mediavida.com"     # solo para abrir enlaces en el navegador
MV_SPY_URL = MV_BASE + "/foro/spy"
MV_THREAD_URL = MV_BASE + "/foro/dev/non-synapse-mouse-configura-tu-raton-razer-sin-synapse-wind-739643"
KONAMI = ("up", "up", "down", "down", "left", "right", "left", "right", "b", "a")

# ---------------------------------------------------------------------------
# Datos de la aplicacion (version, repositorio, enlaces)
# ---------------------------------------------------------------------------
APP_NAME    = "Non-Synapse-Mouse"
APP_VERSION = "1.4.0"                        # versionado semantico MAYOR.MENOR.PARCHE
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
        "bad_status":    "El ratón no dio una respuesta válida ({st}).",
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
        "bad_status":    "The mouse didn't give a valid answer ({st}).",
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
    try:
        got = 0
        with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as fh:
            try:
                want = int(r.headers.get("Content-Length") or 0)
            except (TypeError, ValueError):
                want = 0
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                fh.write(chunk); got += len(chunk)
        if want and got != want:                       # descarga cortada: no se usa
            raise IOError(f"incomplete download ({got} of {want} bytes)")
        with open(tmp, "rb") as fh:
            if dest.lower().endswith(".exe") and fh.read(2) != b"MZ":
                raise IOError("the downloaded file is not a Windows program")
        os.replace(tmp, dest)
    except Exception:
        try: os.remove(tmp)
        except Exception: pass
        raise


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


class MouseBusy(RuntimeError):
    """El raton esta conectado pero no dio datos validos (dormido, ocupado,
    timeout del receptor). No significa que se haya desconectado."""


class RazerMouse:
    def __init__(self):
        self.dev = None
        self.model = None
        self.pid = None
        self.tx_cache = {}   # command_class -> transaction_id que funciona
        # Varios hilos hablan con el raton (interfaz, parpadeo del logo, sniper):
        # cada envio+lectura tiene que ser atomico o se mezclarian las respuestas.
        self._lock = threading.RLock()

    # --- transporte ------------------------------------------------------
    def _raw(self, dev, report, command_class, retries=5):
        with self._lock:
            return self._raw_unlocked(dev, report, command_class, retries)

    def _raw_unlocked(self, dev, report, command_class, retries=5):
        """Envia un informe y lee la respuesta. Solo vale una respuesta que
        haga eco de la clase Y del comando enviados (como comprueba OpenRazer):
        el receptor inalambrico a veces devuelve la respuesta ANTERIOR o un
        informe vacio mientras el raton se despierta, y eso daba lecturas
        falsas (p. ej. bateria al 0 % al arrancar)."""
        last = None
        for _ in range(retries):
            if dev.send_feature_report(bytes([0x00]) + bytes(report)) < 0:
                return None
            # Se lee hasta 3 veces ANTES de volver a enviar: reenviar una
            # escritura con VARSTORE gastaria otra escritura en la memoria.
            for k in range(3):
                time.sleep(0.06 if k == 0 else 0.04)
                raw = dev.get_feature_report(0x00, 91)
                if not raw:
                    continue
                resp = _normalize(raw, command_class)
                if len(resp) < 8 or resp[6] != report[6] or resp[7] != report[7]:
                    continue                      # no es la respuesta a ESTE comando
                last = resp
                if resp[0] in (0x00, 0x01):       # aun sin procesar / ocupado
                    time.sleep(0.04); continue
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
            # no se pudo averiguar (p. ej. raton dormido): se usa el de la clase
            # 0x00 SIN guardarlo, para volver a sondear la proxima vez
            return self.tx_cache.get(0x00, 0xFF)
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

    STATUS_OK = 0x02

    def _read(self, command_class, command_id, data_size, args=b""):
        """Lectura: si el raton no contesta OK (ocupado, fallo, timeout del
        receptor, no soportado), los datos no valen y se lanza un error en vez
        de devolver ceros."""
        r = self._cmd(command_class, command_id, data_size, args)
        if r[0] != self.STATUS_OK:
            raise MouseBusy(_m("bad_status", st=f"0x{r[0]:02X}"))
        return r

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
        r = self._read(0x00, 0x81, 0x02)
        return r[8], r[9]     # major, minor

    def get_battery(self):
        r = self._read(0x07, 0x80, 0x02)
        pct = round(r[9] / 255 * 100)
        c = self._read(0x07, 0x84, 0x02)
        return pct, bool(c[9])

    def get_dpi(self):
        r = self._read(0x04, 0x85, 0x07, bytes([VARSTORE]))
        x, y = (r[9] << 8) | r[10], (r[11] << 8) | r[12]
        if x < DPI_MIN or y < DPI_MIN:                 # 0 o basura: no es un DPI real
            raise MouseBusy(_m("bad_status", st="dpi=0"))
        return x, y

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
        r = self._read(0x00, 0x84, 0x02)
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

    def set_color(self, r, g, b, store=True):
        """Color fijo del LED. store=False (NOSTORE) no graba en la memoria del
        raton: se usa para el parpadeo, que cambia el color muchas veces."""
        led = self.model.get("led", LOGO_LED) if self.model else LOGO_LED
        # static: args = [varstore, led, effect=0x01, 0,0, 0x01, R, G, B]
        args = bytes([VARSTORE if store else NOSTORE, led, 0x01, 0x00, 0x00, 0x01,
                      r & 0xFF, g & 0xFF, b & 0xFF])
        return self._cmd_light(0x02, 0x09, args)

    def set_light_off(self, store=True):
        led = self.model.get("led", LOGO_LED) if self.model else LOGO_LED
        # none: args = [varstore, led, effect=0x00]
        return self._cmd_light(0x02, 0x06, bytes([VARSTORE if store else NOSTORE, led, 0x00]))

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
    def __init__(self, pid, on_press, on_other=None, on_release=None):
        self.pid = pid
        self.on_press = on_press          # se llama desde un hilo secundario
        self.on_release = on_release      # idem, al SOLTAR (lo usa el sniper)
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
            if self.on_release is not None:
                for c in prev - codes:    # y el flanco de soltar
                    try: self.on_release(c)
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
# Avisos de bateria (logica pura, sin interfaz: asi se puede probar aparte)
# ---------------------------------------------------------------------------
# Se avisa al cruzar cada uno de estos niveles (bajando). Para que una lectura
# que oscile ±1 % alrededor de un nivel no repita el aviso, un nivel solo se
# "rearma" cuando la bateria sube al menos BATT_REARM_MARGIN puntos por encima.
BATT_ALERT_LEVELS = (90, 80, 70, 60, 50, 40, 30, 20, 15, 10, 8, 6, 5, 4, 3, 2, 1)
BATT_REARM_MARGIN = 2


def battery_alert_step(pct, charging, alerted, first):
    """Decide si toca avisar. Devuelve (tipo, nuevo_conjunto_de_niveles_avisados).
    tipo: None, "open" (primera lectura tras abrir el programa) o "low"."""
    alerted = set(alerted)
    if charging:
        alerted.clear()                          # cargando: todo vuelve a quedar armado
        return ("open" if first else None), alerted
    crossed = [t for t in BATT_ALERT_LEVELS if pct <= t]
    alerted = {t for t in alerted if t >= pct - BATT_REARM_MARGIN}
    new = [t for t in crossed if t not in alerted]
    alerted.update(crossed)
    if first:
        return "open", alerted
    return ("low" if new else None), alerted


def battery_full_step(pct, charging, notified):
    """Aviso de carga completa. Devuelve (avisar, notificado_ahora)."""
    if not charging or pct < 95:
        return False, False
    if pct >= 100 and not notified:
        return True, True
    return False, notified


# Novedades que se muestran una vez tras actualizar (y desde Acerca de).
WHATS_NEW = {
    # Lo que ve quien actualiza. La 1.4.0 es la primera publica desde la 1.0.0,
    # asi que resume todo lo nuevo desde entonces.
    "1.4.0": {
        "en": [
            "Your 5 profiles work like Synapse: the mouse's profile button switches them instantly, and you edit them here.",
            "A wizard writes your profiles to the mouse's own memory, if you want them without the app.",
            "New Windows 11 style interface: resizable, crisp at any scaling, dark or light mode, and smooth edges.",
            "Button remapping (while the app is open) and a Sniper button: hold it and the DPI drops.",
            "Battery alerts at the top right of the screen, and the battery no longer shows 0 % by mistake while the mouse wakes up.",
            "Logo blink in the profile's colour when you change profile, and a colour picker with a colour wheel.",
            "System tray with profile switching, start with Windows, and updates from inside the app.",
            "Custom themes (.json): colours and the shape of the parts. English by default, Spanish one click away.",
        ],
        "es": [
            "Tus 5 perfiles funcionan como en Synapse: el botón de perfil del ratón los cambia al instante y los editas aquí.",
            "Un asistente graba tus perfiles en la memoria del propio ratón, si los quieres sin el programa.",
            "Interfaz nueva estilo Windows 11: redimensionable, nítida con cualquier escalado, modo oscuro o claro y bordes suaves.",
            "Remapeo de botones (con el programa abierto) y botón Sniper: lo mantienes y baja el DPI.",
            "Avisos de batería arriba a la derecha, y la batería ya no marca 0 % por error mientras el ratón se despierta.",
            "El logo parpadea con el color del perfil al cambiar de perfil, y selector de color con disco.",
            "Bandeja del sistema con cambio de perfil, inicio con Windows y actualizaciones desde el propio programa.",
            "Temas propios (.json): colores y forma de las piezas. Inglés por defecto, español a un clic.",
        ],
    },
}


# ---------------------------------------------------------------------------
# Modo Mediavida: utilidades sin interfaz (se pueden probar sin ventana).
# No se conecta a ningun sitio: el logo va dentro del programa.
# ---------------------------------------------------------------------------
class KonamiDetector:
    """Recibe teclas (keysym de Tk) y avisa cuando se completa
    arriba arriba abajo abajo izquierda derecha izquierda derecha B A."""
    def __init__(self, seq=KONAMI):
        self.seq = tuple(seq)
        self.hist = []

    def feed(self, keysym):
        """Se queda con las ultimas teclas y mira si acaban en la secuencia
        (asi da igual pulsar alguna de mas antes, p. ej. tres veces arriba)."""
        self.hist.append(str(keysym).lower())
        del self.hist[:-len(self.seq)]
        if tuple(self.hist) == self.seq:
            self.hist = []
            return True
        return False


class IntroSound:
    """Musiquilla del modo Mediavida. En Windows usa el reproductor que trae
    el sistema (MCI): no hace falta instalar nada y no bloquea la ventana."""
    ALIAS = "nsm_mv_intro"

    def __init__(self):
        self.playing = False

    def _mci(self, cmd):
        import ctypes
        return ctypes.windll.winmm.mciSendStringW(cmd, None, 0, None)

    def play(self, path, volume=650):
        if sys.platform != "win32" or not path or not os.path.exists(path):
            return False
        try:
            self.stop()
            if self._mci(f'open "{path}" type mpegvideo alias {self.ALIAS}') != 0:
                return False
            self._mci(f"setaudio {self.ALIAS} volume to {int(volume)}")
            self.playing = self._mci(f"play {self.ALIAS} from 0") == 0
            return self.playing
        except Exception:
            return False

    def stop(self):
        if sys.platform != "win32":
            return
        try:
            self._mci(f"close {self.ALIAS}")
        except Exception:
            pass
        self.playing = False


# ---------------------------------------------------------------------------
# Persistencia de presets
# ---------------------------------------------------------------------------
_PRESET_BOOLS = ("welcomed", "tray", "soft_remap", "profile_blink", "notify_popup", "led_on",
                 "learning", "lang_en_default", "control_verified", "control_mode", "check_updates",
                 "batt_full", "batt_alert", "ask_burn_on_exit", "tracking", "mv_unlocked", "mv_welcome")
_PRESET_STRS = ("theme", "last_page", "last_model", "last_version")


def _int_in(v, lo, hi):
    return isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi


def sanitize_presets(d):
    """Quita de la configuracion lo que no tenga el tipo o el rango esperado
    (archivo editado a mano, a medio escribir, de otra version...). Lo que se
    quita vuelve a su valor por defecto; el resto se respeta."""
    if not isinstance(d, dict):
        return {}
    out = dict(d)
    def drop(k):
        out.pop(k, None)
    for k in _PRESET_BOOLS:
        if k in out and not isinstance(out[k], bool):
            drop(k)
    for k in _PRESET_STRS:
        if k in out and not isinstance(out[k], str):
            drop(k)
    if out.get("lang") not in (None, "es", "en"): drop("lang")
    for k in ("mv_user", "mv_avatar", "mv_checked"):   # restos del modo Mediavida con red (dev)
        drop(k)
    if out.get("theme_mode") not in (None, "dark", "light"): drop("theme_mode")
    if "sniper_dpi" in out and not _int_in(out["sniper_dpi"], 100, 30000): drop("sniper_dpi")
    if "poll_rate" in out and out["poll_rate"] not in (125, 500, 1000): drop("poll_rate")
    if "led_bright" in out and not _int_in(out["led_bright"], 0, 100): drop("led_bright")
    if "active_profile" in out and out["active_profile"] is not None and not _int_in(out["active_profile"], 0, 4):
        drop("active_profile")
    lc = out.get("led_color")
    if "led_color" in out and not (isinstance(lc, list) and len(lc) == 3 and all(_int_in(c, 0, 255) for c in lc)):
        drop("led_color")
    wg = out.get("win_geom")
    if "win_geom" in out and not (isinstance(wg, list) and len(wg) == 4
                                  and all(isinstance(c, int) and not isinstance(c, bool) for c in wg)):
        drop("win_geom")
    for k in ("profiles", "dpi_presets", "burned_profiles"):
        v = out.get(k)
        if k in out:
            if isinstance(v, list) and len(v) == 5:
                out[k] = [x if _int_in(x, 100, 30000) else None for x in v]
            else:
                drop(k)
    bs = out.get("buttons_seen")
    if "buttons_seen" in out:
        if isinstance(bs, list):
            out["buttons_seen"] = [c for c in bs if _int_in(c, 1, 255)]
        else:
            drop("buttons_seen")
    ss = out.get("soft_seen")
    if "soft_seen" in out:
        if isinstance(ss, list):
            out["soft_seen"] = [c for c in ss if isinstance(c, str)]
        else:
            drop("soft_seen")
    for k in ("button_map", "soft_map"):
        m = out.get(k)
        if k in out:
            if isinstance(m, dict):
                clean = {}
                for kk, vv in m.items():
                    if not isinstance(vv, str):
                        continue
                    if k == "button_map":
                        try:
                            if not 1 <= int(kk) <= 255:
                                continue
                        except (TypeError, ValueError):
                            continue
                    clean[str(kk)] = vv
                out[k] = clean
            else:
                drop(k)
    return out


def load_presets():
    """Carga la configuracion. Si aun no existe la nueva pero si la antigua
    (junto al programa), usa la antigua: al guardar ya queda migrada. Si el
    archivo esta roto, se usa la copia de seguridad (.bak) del ultimo guardado
    bueno."""
    for path in (CONFIG_PATH, CONFIG_PATH + ".bak", LEGACY_CONFIG_PATH):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return sanitize_presets(data)
        except Exception:
            continue
    return {}

def save_presets(data):
    """Guarda de forma segura: se escribe a un archivo temporal y se cambia por
    el bueno de golpe (si se va la luz a mitad, no queda un archivo roto). El
    anterior queda como .bak."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        if os.path.exists(CONFIG_PATH):
            try: os.replace(CONFIG_PATH, CONFIG_PATH + ".bak")
            except Exception: pass
        os.replace(tmp, CONFIG_PATH)
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
            # --- v1.3.0 ---
            "log_blink_unknown": "Parpadeo omitido: el programa aún no sabe cómo está el LED. Enciéndelo o apágalo una vez en Iluminación y funcionará.",
            "model_auto": "Auto-detectar (cualquiera)",
            "grp_battery": "Batería", "grp_appearance": "Apariencia", "grp_sniper": "Sniper",
            "batt_alert_title": "Avisos de batería",
            "batt_alert_desc": "Pop-ups de estado.",
            "batt_full_title": "Avisar al cargar del todo",
            "batt_full_desc": "Aviso cuando la batería llega al 100 % mientras carga.",
            "batt_test_btn": "Probar",
            "ba_level": "Nivel de batería", "ba_low": "Batería baja", "ba_crit": "Batería muy baja · conéctalo ya",
            "ba_charging": "Cargando", "ba_full": "Carga completa", "ba_full_sub": "Ya puedes desenchufarlo.",
            "log_batt_alert": "Aviso de batería: {pct} %",
            "theme_title": "Tema", "theme_desc": "Próximamente.", "theme_basic": "Básico",
            "dark_title": "Modo oscuro", "dark_desc": "Desactívalo para usar el modo claro.",
            "theme_restart_title": "Reinicia para aplicar el tema",
            "theme_restart_desc": "El programa se cierra y se vuelve a abrir solo. El ratón no pierde nada.",
            "theme_restart_btn": "Reiniciar ahora",
            "themes_custom_title": "Temas personalizados",
            "themes_custom_desc": "Archivos .json con colores y forma de las piezas. En la carpeta hay una plantilla y un ejemplo.",
            "themes_custom_btn": "Abrir carpeta",
            "nav_kofi": "Spot me a scoop",
            "btn_disabled_note": "Activa el remapeo para editar los botones.",
            "log_themes_folder": "Carpeta de temas: {path}",
            "mv_unl_title": "¡Modo Mediavida desbloqueado!",
            "mv_unl_sub": "Puedes desactivarlo en Ajustes, en Tema.", "mv_unl_ok": "Vale",
            "nav_mv_spy": "Spy", "nav_mv_thread": "Hilo en Mediavida",
            "log_mv_on": "Modo Mediavida activado.",
            "log_restart": "Reiniciando para aplicar el tema...",
            "blink_title": "Parpadear el logo al cambiar de perfil",
            "blink_desc": "Tres pulsos con el color del perfil y luego vuelve a como estaba.",
            "blink_test": "Probar", "grp_blink": "Indicador de perfil",
            "log_blink_fail": "El LED no admite colores temporales: se desactiva el parpadeo.",
            "sniper_title": "DPI del sniper",
            "sniper_desc": "Mientras mantengas el botón al que asignes «Sniper», el ratón baja a este DPI.",
            "act_sniper": "Sniper (DPI al mantener)",
            "log_sniper_on": "Sniper activado → {x} DPI", "log_sniper_off": "Sniper soltado → {x} DPI",
            "err_sniper": "El DPI del sniper debe estar entre {lo} y {hi}.",
            "tray_profiles": "Perfiles",
            "wl_title": "Te damos la bienvenida", "wl_sub": "Tres cosas antes de empezar",
            "wl_1": "Cierra Razer Synapse por completo (servicios incluidos) o desinstálalo. Si está abierto, puede bloquear los comandos.",
            "wl_2": "Enchufa el ratón (o su receptor). El programa lo encuentra solo; la barra lateral te dice cuándo está conectado.",
            "wl_3": "Tus perfiles viven en el programa. Con él abierto, el botón de perfil y los de DPI del ratón los cambian.",
            "wl_btn": "Entendido",
            "wn_title": "Novedades de la v{v}", "wn_link": "Novedades", "wn_desc": "Mira qué ha cambiado en esta versión.",
            "wn_show": "Ver",
            # --- v1.2.0: interfaz estilo Configuracion de Windows 11 ---
            "nav_profiles": "Perfiles", "nav_lighting": "Iluminación", "nav_buttons": "Botones",
            "nav_settings": "Ajustes", "nav_log": "Registro", "nav_about": "Acerca de",
            "active_hdr": "Perfil activo",
            "active_desc": "El botón de perfil del ratón pasa al siguiente; DPI abajo vuelve al anterior.",
            "active_small": "Perfil {n} · LED {color}",
            "my_profiles_hdr": "Tus perfiles",
            "prof_led_desc": "LED {color}", "prof_off_desc": "LED {color} · sin DPI, se salta",
            "btn_use": "Usar", "lbl_in_use": "En uso", "ph_off": "Apagado",
            "poll_title": "Frecuencia de sondeo",
            "poll_desc": "Cada cuánto informa el ratón al PC. Se aplica al momento.",
            "btn_burn_dots": "Grabar en el ratón…", "link_reset": "Restablecer valores",
            "led_title": "LED del logo", "led_desc": "Al encenderlo vuelve el último color.",
            "color_hdr": "Color", "color_cur": "Color actual",
            "color_cur_desc": "Pulsa Elegir para abrir el selector de color.",
            "color_pick_btn": "Elegir…", "picker_title": "Elegir color", "picker_bright": "Brillo",
            "picker_new": "Nuevo", "picker_cur": "Actual",
            "picker_note": "Los tonos oscuros se ven en el LED como el mismo color, pero más tenue.",
            "color_quick": "Colores rápidos", "bright_hdr": "Brillo", "bright_title": "Intensidad",
            "soft_title": "Remapeo por software",
            "soft_desc": "Solo con el programa abierto y aún no se guarda en el ratón. Algunos anticheats pueden detectarlo: desactívalo al jugar con ellos.",
            "soft_desc_na": "Solo disponible en Windows.",
            "grp_win_btns": "Botones estándar", "grp_mouse_btns": "Botones especiales",
            "grp_mouse_note": "Los gestiona el propio ratón; necesitan el modo control", "pressed": "Pulsado",
            "grp_mouse": "Ratón", "grp_system": "Sistema", "grp_updates": "Actualizaciones",
            "model_title": "Modelo", "model_desc": "«Auto-detectar» sirve para cualquier Razer.",
            "ctrl_title": "El programa controla los perfiles",
            "ctrl_desc": "Como Synapse. Si lo desactivas, el perfil se deduce por el DPI.",
            "notify_title": "Notificar el cambio de perfil",
            "notify_desc": "Aviso abajo a la derecha durante 2 segundos.",
            "ask_exit_title": "Al cerrar, ofrecer grabar en el ratón",
            "ask_exit_desc": "Solo si los perfiles han cambiado.",
            "tray_title": "Minimizar a la bandeja del sistema", "tray_desc": "Sigue funcionando junto al reloj.",
            "autostart_title": "Iniciar con Windows", "autostart_desc": "Se abre minimizado y se conecta solo.",
            "autostart_desc_na": "Solo disponible en Windows.",
            "lang_title": "Idioma",
            "updt_latest": "Estás al día", "updt_checking": "Buscando actualizaciones…",
            "updt_new": "Nueva versión disponible: {tag}", "updt_err": "No se pudo comprobar",
            "updt_idle": "Actualizaciones", "updt_dl": "Descargando {tag}…",
            "upd_check_btn": "Buscar actualizaciones",
            "upd_start_title": "Buscar actualizaciones al iniciar",
            "upd_start_desc": "Una consulta a GitHub. Sin telemetría.",
            "on": "Activado", "off": "Desactivado",
            "log_title": "Registro",
            "log_desc": "Lo que va haciendo el programa. Si algo falla, esto es lo que hay que mirar. Siempre en inglés, para que se entienda al reportar un error.",
            "btn_copy": "Copiar", "btn_report_plain": "Reportar un error",
            "report_desc": "Abre un issue en GitHub con la versión, el modelo y estas líneas. No se envía nada hasta que lo publiques.",
            "log_copied": "Registro copiado al portapapeles.",
            "about_app_desc": "Configurador ligero para ratones Razer, sin Synapse. Comunicación directa con el ratón, sin servicios en segundo plano intrusivos, sin cuenta y sin instalar drivers.",
            "links_hdr": "Enlaces", "link_repo": "Código fuente en GitHub", "why_hdr": "Por qué existe",
            "link_openrazer_desc": "La ingeniería inversa del protocolo Razer en la que se basa este programa.",
            "link_kofi_desc": "Ko-fi, si te resulta útil.",
            "license_hdr": "Licencia", "license_title": "GPL-3.0",
            "license_desc": "Software libre, se ofrece sin garantía. Proyecto independiente, no afiliado a Razer. «Razer», «Synapse» y «Chroma» son marcas de Razer Inc.",
            "searching": "Buscando el ratón…", "searching_desc": "Enchúfalo y cierra Razer Synapse.",
            "conn_only": "Conectado", "conn_batt": "Conectado · {pct} %",
            "conn_batt_chg": "Conectado · {pct} % · cargando",
            "toast_led": "Perfil {n} · LED {color}",
            "tip_profile": "Perfil {n} · {x} DPI", "tip_batt": "Batería {pct} %",
            "tip_batt_chg": "Batería {pct} % (cargando)",
            "burn_step2": "Paso {n} de {total}",
            "burn_msg_a": "Pulsa el botón de perfil de debajo del ratón hasta que el LED se ponga ",
            "burn_msg_b": ". Luego pulsa «Grabar este perfil».",
            "burn_will": "Se grabará", "burn_will_val": "{x} DPI · Perfil {n}",
            "burn_item": "Perfil {n} ({color}) · {x} DPI, {state}",
            "burn_checked": "comprobado", "burn_unchecked": "sin confirmar",
            "led_red": "rojo", "led_green": "verde", "led_blue": "azul",
            "led_turq": "turquesa", "led_yellow": "amarillo",
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
            "log_batt_doubt": "Lectura de batería dudosa ({pct} %): se vuelve a comprobar.",
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
            "btn_report": "Reportar un error",
            "bug_link": "Reportar un error",
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
            "prof_unknown": "DPI {x} no coincide con tus perfiles · «Restablecer valores» para reaprender",
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
            "log_prof_unknown": "El DPI {x} no coincide con ningún perfil. Si has cambiado tus perfiles, pulsa «Restablecer valores».",
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
            "btn_compat": "Ahora mismo no funcionan: activa «El programa controla los perfiles» en Ajustes.",
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
            "sb_x2": "Lateral izquierdo, adelante", "sb_x1": "Lateral izquierdo, atrás",
            "sb_tiltl": "Rueda inclinada a la izquierda", "sb_tiltr": "Rueda inclinada a la derecha",
            "bn_rside_up": "Lateral derecho, arriba", "bn_rside_dn": "Lateral derecho, abajo",
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
            # --- v1.3.0 ---
            "log_blink_unknown": "Blink skipped: the app doesn't know the LED's current state yet. Turn it on or off once in Lighting and it will work.",
            "model_auto": "Auto-detect (any Razer)",
            "grp_battery": "Battery", "grp_appearance": "Appearance", "grp_sniper": "Sniper",
            "batt_alert_title": "Battery alerts",
            "batt_alert_desc": "Status pop-ups.",
            "batt_full_title": "Notify when fully charged",
            "batt_full_desc": "A pop-up when the battery reaches 100 % while charging.",
            "batt_test_btn": "Test",
            "ba_level": "Battery level", "ba_low": "Battery low", "ba_crit": "Battery very low · plug it in now",
            "ba_charging": "Charging", "ba_full": "Fully charged", "ba_full_sub": "You can unplug it.",
            "log_batt_alert": "Battery alert: {pct} %",
            "theme_title": "Theme", "theme_desc": "Coming soon.", "theme_basic": "Basic",
            "dark_title": "Dark mode", "dark_desc": "Turn it off to use light mode.",
            "theme_restart_title": "Restart to apply the theme",
            "theme_restart_desc": "The app closes and opens again by itself. The mouse loses nothing.",
            "theme_restart_btn": "Restart now",
            "themes_custom_title": "Custom themes",
            "themes_custom_desc": ".json files with colors and the shape of the parts. The folder has a template and an example.",
            "themes_custom_btn": "Open folder",
            "nav_kofi": "Spot me a scoop",
            "btn_disabled_note": "Turn remapping on to edit the buttons.",
            "log_themes_folder": "Themes folder: {path}",
            "mv_unl_title": "Mediavida mode unlocked!",
            "mv_unl_sub": "You can turn it off in Settings, under Theme.", "mv_unl_ok": "OK",
            "nav_mv_spy": "Spy", "nav_mv_thread": "Mediavida thread",
            "log_mv_on": "Mediavida mode turned on.",
            "log_restart": "Restarting to apply the theme...",
            "blink_title": "Blink the logo on profile change",
            "blink_desc": "Three pulses in the profile's colour, then it goes back to how it was.",
            "blink_test": "Test", "grp_blink": "Profile indicator",
            "log_blink_fail": "The LED doesn't accept temporary colours: blinking is turned off.",
            "sniper_title": "Sniper DPI",
            "sniper_desc": "While you hold the button you assign \u201cSniper\u201d to, the mouse drops to this DPI.",
            "act_sniper": "Sniper (DPI while held)",
            "log_sniper_on": "Sniper on \u2192 {x} DPI", "log_sniper_off": "Sniper released \u2192 {x} DPI",
            "err_sniper": "Sniper DPI must be between {lo} and {hi}.",
            "tray_profiles": "Profiles",
            "wl_title": "Welcome", "wl_sub": "Three things before you start",
            "wl_1": "Close Razer Synapse completely (services included) or uninstall it. If it's running, it can block the commands.",
            "wl_2": "Plug in your mouse (or its dongle). The app finds it by itself; the sidebar tells you when it's connected.",
            "wl_3": "Your profiles live in the app. While it's open, the mouse's profile and DPI buttons switch them.",
            "wl_btn": "Got it",
            "wn_title": "What's new in v{v}", "wn_link": "What's new", "wn_desc": "See what changed in this version.",
            "wn_show": "View",
            # --- v1.2.0: Windows 11 Settings-style interface ---
            "nav_profiles": "Profiles", "nav_lighting": "Lighting", "nav_buttons": "Buttons",
            "nav_settings": "Settings", "nav_log": "Log", "nav_about": "About",
            "active_hdr": "Active profile",
            "active_desc": "The mouse's profile button goes to the next one; DPI down goes back.",
            "active_small": "Profile {n} · {color} LED",
            "my_profiles_hdr": "Your profiles",
            "prof_led_desc": "{color} LED", "prof_off_desc": "{color} LED · no DPI, skipped",
            "btn_use": "Use", "lbl_in_use": "In use", "ph_off": "Off",
            "poll_title": "Polling rate",
            "poll_desc": "How often the mouse reports to the PC. Applied instantly.",
            "btn_burn_dots": "Write to mouse…", "link_reset": "Reset values",
            "led_title": "Logo LED", "led_desc": "Turning it on brings back the last colour.",
            "color_hdr": "Colour", "color_cur": "Current colour",
            "color_cur_desc": "Press Choose to open the colour picker.",
            "color_pick_btn": "Choose…", "picker_title": "Choose a colour", "picker_bright": "Brightness",
            "picker_new": "New", "picker_cur": "Current",
            "picker_note": "Dark shades show on the LED as the same colour, just dimmer.",
            "color_quick": "Quick colours", "bright_hdr": "Brightness", "bright_title": "Intensity",
            "soft_title": "Software remapping",
            "soft_desc": "Only while the app is open, and not saved to the mouse yet. Some anti-cheats may detect it: turn it off when playing with them.",
            "soft_desc_na": "Only available on Windows.",
            "grp_win_btns": "Standard buttons", "grp_mouse_btns": "Special buttons",
            "grp_mouse_note": "Handled by the mouse itself; they need control mode", "pressed": "Pressed",
            "grp_mouse": "Mouse", "grp_system": "System", "grp_updates": "Updates",
            "model_title": "Model", "model_desc": "\u201cAuto-detect\u201d works for any Razer.",
            "ctrl_title": "The app controls the profiles",
            "ctrl_desc": "Like Synapse. If you turn it off, the profile is inferred from the DPI.",
            "notify_title": "Notify profile changes",
            "notify_desc": "Pop-up at the bottom right for 2 seconds.",
            "ask_exit_title": "On exit, offer to write to the mouse",
            "ask_exit_desc": "Only if the profiles have changed.",
            "tray_title": "Minimize to the system tray", "tray_desc": "Keeps working next to the clock.",
            "autostart_title": "Start with Windows", "autostart_desc": "Opens minimized and connects by itself.",
            "autostart_desc_na": "Only available on Windows.",
            "lang_title": "Language",
            "updt_latest": "You're up to date", "updt_checking": "Checking for updates…",
            "updt_new": "New version available: {tag}", "updt_err": "Couldn't check",
            "updt_idle": "Updates", "updt_dl": "Downloading {tag}…",
            "upd_check_btn": "Check for updates",
            "upd_start_title": "Check for updates on startup",
            "upd_start_desc": "One request to GitHub. No telemetry.",
            "on": "On", "off": "Off",
            "log_title": "Log",
            "log_desc": "What the app is doing. If something goes wrong, this is what to look at. Always in English, so it can be read when reporting a bug.",
            "btn_copy": "Copy", "btn_report_plain": "Report a bug",
            "report_desc": "Opens a GitHub issue with the version, the model and these lines. Nothing is sent until you publish it.",
            "log_copied": "Log copied to the clipboard.",
            "about_app_desc": "Lightweight configuration tool for Razer mice, without Synapse. Talks directly to the mouse: no intrusive background services, no account and no drivers to install.",
            "links_hdr": "Links", "link_repo": "Source code on GitHub", "why_hdr": "Why it exists",
            "link_openrazer_desc": "The reverse engineering of the Razer protocol this program is based on.",
            "link_kofi_desc": "Ko-fi, if you find it useful.",
            "license_hdr": "License", "license_title": "GPL-3.0",
            "license_desc": "Free software, provided without warranty. Independent project, not affiliated with Razer. \u201cRazer\u201d, \u201cSynapse\u201d and \u201cChroma\u201d are trademarks of Razer Inc.",
            "searching": "Looking for the mouse…", "searching_desc": "Plug it in and close Razer Synapse.",
            "conn_only": "Connected", "conn_batt": "Connected · {pct} %",
            "conn_batt_chg": "Connected · {pct} % · charging",
            "toast_led": "Profile {n} · {color} LED",
            "tip_profile": "Profile {n} · {x} DPI", "tip_batt": "Battery {pct} %",
            "tip_batt_chg": "Battery {pct} % (charging)",
            "burn_step2": "Step {n} of {total}",
            "burn_msg_a": "Press the profile button under the mouse until the LED turns ",
            "burn_msg_b": ". Then click \u201cWrite this profile\u201d.",
            "burn_will": "Will be written", "burn_will_val": "{x} DPI · Profile {n}",
            "burn_item": "Profile {n} ({color}) · {x} DPI, {state}",
            "burn_checked": "checked", "burn_unchecked": "unconfirmed",
            "led_red": "red", "led_green": "green", "led_blue": "blue",
            "led_turq": "turquoise", "led_yellow": "yellow",
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
            "log_batt_doubt": "Odd battery reading ({pct} %): checking again.",
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
            "btn_report": "Report a bug",
            "bug_link": "Report a bug",
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
            "prof_unknown": "DPI {x} doesn't match your profiles · \u201cReset values\u201d to relearn",
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
            "log_prof_unknown": "DPI {x} doesn't match any profile. If you changed your profiles, click \u201cReset values\u201d.",
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
            "sb_x2": "Left side, forward", "sb_x1": "Left side, back",
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
    first_run = not presets            # sin configuracion previa = primera vez que se abre
    RESTARTED = "--restarted" in sys.argv          # reabierto por el propio programa (tema)
    _got = acquire_single_instance()
    if not _got and RESTARTED:                     # la instancia anterior aun se esta cerrando
        for _ in range(25):
            release_single_instance(); time.sleep(0.2)
            _got = acquire_single_instance()
            if _got:
                break
    if not _got:
        _tmp = tk.Tk(); _tmp.withdraw()
        if presets.get("lang", "en") == "en":
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
    if not presets.get("lang_en_default"):
        # v1.3.0: el ingles pasa a ser el idioma por defecto. Una sola vez se
        # restablece a ingles (versiones anteriores guardaban 'es' sin que lo
        # eligieras); desde ahi, el idioma que elijas se respeta siempre.
        presets["lang"] = "en"; presets["lang_en_default"] = True
        save_presets(presets)
    lang = [presets.get("lang", "en")]          # idioma activo (holder mutable)
    set_core_lang("en")                          # el nucleo solo escribe en el registro: ingles

    def tr(key, **kw):
        """Texto en el idioma activo. Si falta la clave, cae al espanol y luego
        a la propia clave. Aplica .format(**kw) si se pasan huecos."""
        s = LANG.get(lang[0], {}).get(key) or LANG["es"].get(key, key)
        return s.format(**kw) if kw else s

    def trl(key, **kw):
        """Texto para el REGISTRO: siempre en ingles (asi un registro pegado en
        GitHub se entiende venga de donde venga, y no cambia con el idioma)."""
        s = LANG["en"].get(key) or LANG["es"].get(key, key)
        return s.format(**kw) if kw else s

    def st_name(code, lng=None):
        return STATUS_L.get(lng or lang[0], STATUS_L["es"]).get(code, hex(code))

    # =====================================================================
    # 2) TEMAS
    #    Un tema = COLORES (tokens) + FORMA de las piezas + fuente opcional.
    #    Nada de la interfaz lleva colores escritos a mano: todo sale de aqui.
    #    Las piezas redondeadas (interruptores, ES|EN, puntos, deslizadores...)
    #    las dibuja el "dibujante" (seccion 3b) con suavizado y con la forma
    #    que diga el tema: round | square | chamfer | diamond.
    #
    #    Temas propios: archivos .json en %APPDATA%\Non-Synapse-Mouse\themes
    #    (ver plantilla que se crea al pulsar "Abrir carpeta de temas"). Un tema
    #    propio parte de uno base y solo cambia lo que diga. Se aplica al reiniciar.
    # =====================================================================
    THEME_COLOR_KEYS = {
        "BG": "fondo de la ventana", "CARD": "tarjetas-fila", "CARD_BORDER": "borde de las tarjetas",
        "CTRL": "botones, combos, cajas; item de navegacion activo", "CTRL_HOVER": "control al pasar el raton",
        "CTRL_BORDER": "borde de los controles", "INPUT_LINE": "linea inferior de las cajas de texto",
        "INPUT_FOCUS": "caja de texto con foco", "FG": "texto principal", "FG2": "texto secundario",
        "FG3": "texto terciario / desactivado", "ACCENT": "acento", "ACCENT_HOVER": "acento al pasar el raton",
        "ON_ACCENT": "texto sobre el acento", "LOG_BG": "fondo del registro", "LOG_BORDER": "borde del registro",
        "SEG_OFF": "segmento apagado (barras)", "LOW_BATT": "bateria critica", "WARN_BATT": "bateria baja",
        "SCROLL": "barra de desplazamiento", "SCROLL_HOVER": "barra de desplazamiento (raton encima)",
        "SWITCH_OFF": "borde del interruptor apagado", "KNOB_OFF": "bolita del interruptor apagado",
        "DISABLED": "piezas desactivadas", "SLIDER_TRACK": "pista del deslizador",
        "SELECT_BG": "seleccion de texto", "PANEL": "recuadro interior de dialogos",
        "PANEL_BORDER": "borde del recuadro interior", "PROG_OFF": "pasos pendientes (barra de progreso)",
        "POPUP_BORDER": "borde de los avisos flotantes", "SWATCH_BORDER": "borde de las muestras de color",
        "LINK": "enlaces y texto en color de acento",
    }
    THEME_SHAPE_DEFAULT = {"style": "round", "corner": 6, "border": 1, "glow": False}
    THEME_STYLES = ("round", "square", "chamfer", "diamond")
    BUILTIN_THEMES = {
        "basic": {
            "name": {"es": "Básico", "en": "Basic"},
            "shape": dict(THEME_SHAPE_DEFAULT),
            "dark": {                       # estilo Configuracion de Windows 11, modo oscuro
                "BG": "#202020", "CARD": "#2B2B2B", "CARD_BORDER": "#1D1D1D",
                "CTRL": "#2D2D2D", "CTRL_HOVER": "#323232", "CTRL_BORDER": "#353535",
                "INPUT_LINE": "#8A8A8A", "INPUT_FOCUS": "#1F1F1F",
                "FG": "#FFFFFF", "FG2": "#C8C8C8", "FG3": "#9D9D9D",
                "ACCENT": "#44D62C", "ACCENT_HOVER": "#3CBF27", "ON_ACCENT": "#000000",
                "LOG_BG": "#1C1C1C", "LOG_BORDER": "#2E2E2E", "SEG_OFF": "#3A3A3A",
                "LOW_BATT": "#FF2E4D", "WARN_BATT": "#FFB900",
                "SCROLL": "#4A4A4A", "SCROLL_HOVER": "#6A6A6A",
                "SWITCH_OFF": "#9D9D9D", "KNOB_OFF": "#CFCFCF", "DISABLED": "#5A5A5A",
                "SLIDER_TRACK": "#9A9A9A", "SELECT_BG": "#3A3A3A",
                "PANEL": "#232323", "PANEL_BORDER": "#333333", "PROG_OFF": "#454545",
                "POPUP_BORDER": "#3A3A3A", "SWATCH_BORDER": "#3A3A3A", "LINK": "#44D62C",
            },
            "light": {                      # estilo Configuracion de Windows 11, modo claro
                "BG": "#F3F3F3", "CARD": "#FBFBFB", "CARD_BORDER": "#E5E5E5",
                "CTRL": "#FDFDFD", "CTRL_HOVER": "#F4F4F4", "CTRL_BORDER": "#D9D9D9",
                "INPUT_LINE": "#868686", "INPUT_FOCUS": "#FFFFFF",
                "FG": "#1B1B1B", "FG2": "#5C5C5C", "FG3": "#8A8A8A",
                "ACCENT": "#3CBF27", "ACCENT_HOVER": "#35AA22", "ON_ACCENT": "#000000",
                "LOG_BG": "#FFFFFF", "LOG_BORDER": "#E5E5E5", "SEG_OFF": "#DCDCDC",
                "LOW_BATT": "#D13438", "WARN_BATT": "#C98A00",
                "SCROLL": "#C2C2C2", "SCROLL_HOVER": "#9E9E9E",
                "SWITCH_OFF": "#5C5C5C", "KNOB_OFF": "#5C5C5C", "DISABLED": "#BDBDBD",
                "SLIDER_TRACK": "#8A8A8A", "SELECT_BG": "#CCE4F7",
                "PANEL": "#F3F3F3", "PANEL_BORDER": "#E0E0E0", "PROG_OFF": "#D6D6D6",
                "POPUP_BORDER": "#D0D0D0", "SWATCH_BORDER": "#C8C8C8", "LINK": "#1F7A12",
            },
        },
    }
    # Tema secreto: solo aparece tras el codigo Konami (modo Mediavida). Oscuro
    # como el del foro: casi negro, tarjetas grafito, grises calidos y el naranja
    # amarillento de sus detalles. El foro no tiene modo claro: se usa el mismo.
    _MV_PAL = {
                "BG": "#0B0A09", "CARD": "#242323", "CARD_BORDER": "#111111",
                "CTRL": "#2B2B2B", "CTRL_HOVER": "#343332", "CTRL_BORDER": "#3A3836",
                "INPUT_LINE": "#6E655A", "INPUT_FOCUS": "#1C1B1A",
                "FG": "#D0D0D0", "FG2": "#9E968F", "FG3": "#756E66",
                "ACCENT": "#FFA804", "ACCENT_HOVER": "#E89600", "ON_ACCENT": "#111111",
                "LOG_BG": "#111111", "LOG_BORDER": "#242323", "SEG_OFF": "#2B2B2B",
                "LOW_BATT": "#E5484D", "WARN_BATT": "#D66017",
                "SCROLL": "#3A3836", "SCROLL_HOVER": "#4D4A47",
                "SWITCH_OFF": "#756E66", "KNOB_OFF": "#9E968F", "DISABLED": "#3F3C39",
                "SLIDER_TRACK": "#4A4643", "SELECT_BG": "#4D2100",
                "PANEL": "#1A1918", "PANEL_BORDER": "#2B2B2B", "PROG_OFF": "#3A3836",
                "POPUP_BORDER": "#4D2100", "SWATCH_BORDER": "#3A3836", "LINK": "#FFA804",
            }
    BUILTIN_THEMES["mediavida"] = {
        "name": {"es": "Mediavida", "en": "Mediavida"},
        "shape": dict(THEME_SHAPE_DEFAULT),
        "dark": dict(_MV_PAL), "light": dict(_MV_PAL), "secret": True,
    }
    THEMES_DIR = os.path.join(CONFIG_DIR, "themes")
    theme_errors = []                                   # se escriben en el registro al arrancar

    def _valid_hex(v):
        return isinstance(v, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", v) is not None

    def load_user_themes():
        """Lee los .json de la carpeta de temas. Cada uno parte de un tema base
        (por defecto 'basic') y sobrescribe solo lo que trae. Lo que no se
        entiende se ignora (y se apunta en el registro)."""
        out = {}
        try:
            files = sorted(f for f in os.listdir(THEMES_DIR) if f.lower().endswith(".json"))
        except Exception:
            return out
        for fn in files:
            if fn.startswith("_"):
                continue                                 # plantilla / ejemplo: no son temas
            key = "user:" + os.path.splitext(fn)[0].lower()
            try:
                with open(os.path.join(THEMES_DIR, fn), encoding="utf-8") as f:
                    data = json.load(f)
                base = BUILTIN_THEMES.get(str(data.get("base", "basic")), BUILTIN_THEMES["basic"])
                th = {"name": data.get("name") or os.path.splitext(fn)[0],
                      "shape": dict(base["shape"]), "file": fn}
                sh = data.get("shape") or {}
                if sh.get("style") in THEME_STYLES: th["shape"]["style"] = sh["style"]
                for k_ in ("corner", "border"):
                    if isinstance(sh.get(k_), (int, float)) and 0 <= sh[k_] <= 40:
                        th["shape"][k_] = float(sh[k_])
                if isinstance(sh.get("glow"), bool): th["shape"]["glow"] = sh["glow"]
                if isinstance(data.get("font"), str): th["font"] = data["font"]
                for mode in ("dark", "light"):
                    pal = dict(base[mode])
                    for k_, v in (data.get(mode) or {}).items():
                        if k_ in THEME_COLOR_KEYS and _valid_hex(v):
                            pal[k_] = v.upper()
                        else:
                            theme_errors.append(f"Theme {fn}: ignored {mode}.{k_}={v!r}")
                    th[mode] = pal
                out[key] = th
            except Exception as e:
                theme_errors.append(f"Theme {fn}: not loaded ({e})")
        return out

    THEMES = dict(BUILTIN_THEMES)
    THEMES.update(load_user_themes())

    def theme_label(k):
        n = THEMES[k]["name"]
        return n.get(lang[0]) or n.get("en") or k if isinstance(n, dict) else str(n)

    MV_UNLOCKED = bool(presets.get("mv_unlocked"))      # modo Mediavida desbloqueado
    THEME_NAME = presets.get("theme", "basic")
    if THEME_NAME not in THEMES or (THEMES[THEME_NAME].get("secret") and not MV_UNLOCKED):
        THEME_NAME = "basic"
    MV_ACTIVE = MV_UNLOCKED and THEME_NAME == "mediavida"  # se ve el modo Mediavida
    THEME_MODE = "light" if presets.get("theme_mode") == "light" else "dark"
    THEME = THEMES[THEME_NAME]
    SHAPE = THEME["shape"]
    T = THEME[THEME_MODE]                               # paleta activa
    BG, CARD, CARD_BORDER = T["BG"], T["CARD"], T["CARD_BORDER"]
    CTRL, CTRL_HOVER, CTRL_BORDER = T["CTRL"], T["CTRL_HOVER"], T["CTRL_BORDER"]
    INPUT_LINE, INPUT_FOCUS = T["INPUT_LINE"], T["INPUT_FOCUS"]
    FG, FG2, FG3 = T["FG"], T["FG2"], T["FG3"]
    ACCENT, ACCENT_HOVER, ON_ACCENT = T["ACCENT"], T["ACCENT_HOVER"], T["ON_ACCENT"]
    LOG_BG, LOG_BORDER, SEG_OFF, LOW_BATT = T["LOG_BG"], T["LOG_BORDER"], T["SEG_OFF"], T["LOW_BATT"]
    WARN_BATT = T["WARN_BATT"]
    # compatibilidad con nombres antiguos que usa la logica copiada
    GREEN, MUTED = ACCENT, FG3

    # Escalado: el proceso se declara "DPI aware" ANTES de crear la ventana, y
    # todas las medidas en px del diseno pasan por px() (base 96 ppp).
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try: ctypes.windll.user32.SetProcessDPIAware()
            except Exception: pass

    root = tk.Tk()
    root.withdraw()                                  # se muestra al terminar de montar
    root.title(f"{APP_NAME} v{APP_VERSION}")
    _ico_path = os.path.join(getattr(sys, "_MEIPASS", _BASE_DIR), "icono.ico")
    if os.path.exists(_ico_path):
        try: root.iconbitmap(_ico_path)
        except Exception: pass
    root.configure(bg=BG)

    try:
        SCALE = max(1.0, root.winfo_fpixels("1i") / 96.0)
    except Exception:
        SCALE = 1.0

    def px(n):
        return int(round(n * SCALE))

    # --- tipografia: todo Segoe (viene con Windows); si no esta, cae a otra ---
    import tkinter.font as tkfont
    _fams = set(tkfont.families(root))

    def _pick(*names):
        for n in names:
            if n in _fams:
                return n
        return None

    F_TEXT = _pick("Segoe UI Variable Text", "Segoe UI") or "TkDefaultFont"
    _semi = _pick("Segoe UI Semibold", "Segoe UI Variable Text Semibold")
    _disp = _pick("Segoe UI Variable Display Semibold", "Segoe UI Semibold")
    _tfont = THEME.get("font")
    if _tfont and _tfont in _fams:                   # fuente del tema (si esta instalada)
        F_TEXT, _semi, _disp = _tfont, None, None
    F_MONO = _pick("Cascadia Mono", "Consolas", "DejaVu Sans Mono") or "TkFixedFont"
    F_ICON = _pick("Segoe Fluent Icons", "Segoe MDL2 Assets")   # None -> sin iconos

    def font(size, semibold=False, display=False):
        """size en px del diseno -> fuente Tk en pixeles reales (negativo)."""
        if display and _disp:
            return (_disp, -px(size))
        if semibold:
            return (_semi, -px(size)) if _semi else (F_TEXT, -px(size), "bold")
        return (F_TEXT, -px(size))

    FONT_TITLE = font(28, display=True)
    FONT_GROUP = font(14, semibold=True)
    FONT_ROW   = font(14)
    FONT_DESC  = font(12)
    FONT_BIG   = font(20, semibold=True)
    FONT_LOG   = (F_MONO, -px(12.5))

    def icon_font(size):
        return (F_ICON, -px(size)) if F_ICON else None

    # codigos de iconos (Segoe Fluent Icons / MDL2 Assets)
    IC = {"profiles": "\uE81E", "lighting": "\uEA80", "buttons": "\uE8AB", "settings": "\uE713",
          "log": "\uE8FD", "about": "\uE946", "refresh": "\uE72C", "copy": "\uE8C8",
          "open": "\uE8A7", "download": "\uE896", "warn": "\uE7BA", "power": "\uE7E8",
          "bright": "\uE706", "color": "\uE790", "lang": "\uE774", "sync": "\uE895",
          "bell": "\uEA8F", "monitor": "\uE7F4", "check": "\uE73E", "code": "\uE943",
          "doc": "\uE8A5", "speed": "\uEC4A", "heart": "\uEB51", "view": "\uE890"}

    def batt_glyph(pct, chg):
        """Icono de bateria (Battery0-10 / BatteryCharging0-10)."""
        n = max(0, min(10, int(round(pct / 10.0))))
        if chg:
            return "\uE83E" if n == 10 else chr(0xE85A + n)
        return "\uE83F" if n == 10 else chr(0xE850 + n)

    # --- estilos ttk (tema "clam", el mas personalizable) ---------------------
    st = ttk.Style()
    try: st.theme_use("clam")
    except Exception: pass
    st.configure(".", background=BG, foreground=FG, fieldbackground=CTRL,
                 bordercolor=CTRL_BORDER, font=FONT_ROW, focuscolor=BG)
    st.configure("TFrame", background=BG)
    st.configure("Btn.TButton", background=CTRL, foreground=FG, bordercolor=CTRL_BORDER,
                 lightcolor=CTRL, darkcolor=CTRL, relief="flat", padding=(px(12), px(5)),
                 font=FONT_ROW, focuscolor=CTRL)
    st.map("Btn.TButton", background=[("disabled", BG), ("pressed", CARD), ("active", CTRL_HOVER)],
           foreground=[("disabled", FG3)], lightcolor=[("active", CTRL_HOVER)],
           darkcolor=[("active", CTRL_HOVER)])
    st.configure("Accent.TButton", background=ACCENT, foreground=ON_ACCENT, bordercolor=ACCENT,
                 lightcolor=ACCENT, darkcolor=ACCENT, relief="flat", padding=(px(12), px(5)),
                 font=FONT_ROW, focuscolor=ACCENT)
    st.map("Accent.TButton", background=[("disabled", CTRL), ("pressed", ACCENT_HOVER), ("active", ACCENT_HOVER)],
           foreground=[("disabled", FG3)], lightcolor=[("active", ACCENT_HOVER)],
           darkcolor=[("active", ACCENT_HOVER)], bordercolor=[("active", ACCENT_HOVER)])
    st.configure("TCombobox", fieldbackground=CTRL, background=CTRL, foreground=FG,
                 arrowcolor=FG2, bordercolor=CTRL_BORDER, lightcolor=CTRL, darkcolor=CTRL,
                 relief="flat", padding=(px(8), px(4)), arrowsize=px(12))
    st.map("TCombobox", fieldbackground=[("disabled", CARD), ("readonly", CTRL)],
           foreground=[("disabled", FG3), ("readonly", FG)], arrowcolor=[("disabled", T["DISABLED"])],
           background=[("disabled", CARD), ("active", CTRL_HOVER)],
           selectbackground=[("readonly", CTRL)], selectforeground=[("readonly", FG)])
    st.configure("Vertical.TScrollbar", background=T["SCROLL"], troughcolor=BG, bordercolor=BG,
                 lightcolor=T["SCROLL"], darkcolor=T["SCROLL"], arrowcolor=FG3, gripcount=0,
                 relief="flat", width=px(10))
    st.map("Vertical.TScrollbar", background=[("active", T["SCROLL_HOVER"])])
    root.option_add("*TCombobox*Listbox.background", CTRL)
    root.option_add("*TCombobox*Listbox.foreground", FG)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", ON_ACCENT)
    root.option_add("*TCombobox*Listbox.borderWidth", 0)
    root.option_add("*TCombobox*Listbox.font", FONT_ROW)

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
        """Registra un callback de re-render y lo ejecuta una vez."""
        i18n.append(cb); cb()

    def retranslate():
        for cb in i18n:
            try: cb()
            except Exception: pass
        root.update_idletasks()                      # tamano fijo: no se recalcula

    # =====================================================================
    # 3b) PIEZAS DE INTERFAZ (tarjetas-fila, interruptor, deslizador, caja de
    #     texto, enlaces, silueta del raton). Todo plano: sin degradados.
    # =====================================================================
    def round_rect(cv, x1, y1, x2, y2, r, **kw):
        """Rectangulo redondeado en un Canvas (poligono suavizado)."""
        r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return cv.create_polygon(pts, smooth=True, **kw)

    # --- DIBUJANTE: piezas suaves con la forma que diga el tema ---------------
    # Tk no suaviza los bordes en Windows (de ahi los "dientes de sierra"). Cada
    # pieza redondeada se dibuja con Pillow 4 veces mas grande, se reduce con
    # LANCZOS y se pone en el lienzo como imagen con transparencia (vale para
    # cualquier fondo, claro u oscuro). Se guarda en cache.
    # La FORMA la decide el tema (SHAPE["style"]):
    #   round   -> pildoras y circulos (Windows 11)
    #   square  -> esquinas rectas
    #   chamfer -> esquinas cortadas en diagonal
    #   diamond -> rombos y puntas
    # Tipos de pieza:
    #   "pill" -> interruptor, ES|EN, pistas de deslizador
    #   "dot"  -> bolitas, puntos de color, avatar
    #   "box"  -> rectangulo con esquinas de radio r (muestras, logo, bateria)
    # Todas las piezas pasan por paint(); para un estilo nuevo basta con
    # ensenarle la forma a _shape_geom().
    try:
        from PIL import Image as _PImage, ImageDraw as _PDraw, ImageFilter as _PFilter, ImageChops as _PChops
        PAINT_OK = True
    except Exception:
        PAINT_OK = False
    _paint_cache = {}
    _SS = 4                                          # supermuestreo
    GP = px(4) if SHAPE.get("glow") else 0           # margen de los lienzos para que el halo no se corte

    def _hex_rgb(h):
        return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

    def _chamfer(x1, y1, x2, y2, c):
        return [(x1 + c, y1), (x2 - c, y1), (x2, y1 + c), (x2, y2 - c),
                (x2 - c, y2), (x1 + c, y2), (x1, y2 - c), (x1, y1 + c)]

    def _shape_geom(kind, x1, y1, x2, y2, r, k=1.0):
        """Geometria de una pieza segun el estilo del tema. k = escala (para el
        supermuestreo). Devuelve ('ellipse', None) | ('rrect', radio) | ('poly', puntos)."""
        w, h = x2 - x1, y2 - y1
        style = SHAPE.get("style", "round")
        corner = px(SHAPE.get("corner", 6)) * k
        if kind == "dot":
            if style == "round":
                return ("ellipse", None)
            if style == "square":
                return ("rrect", 0)
            if style == "diamond":
                cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                return ("poly", [(cx, y1), (x2, cy), (cx, y2), (x1, cy)])
            return ("poly", _chamfer(x1, y1, x2, y2, min(w, h) * 0.2))       # cuadrado con esquinas cortadas
        if kind == "pill":
            if style == "round":
                return ("rrect", min(w, h) / 2.0)
            if style == "square":
                return ("rrect", 0)
            if style == "diamond":
                c, cy = min(w, h) / 2.0, (y1 + y2) / 2.0
                return ("poly", [(x1 + c, y1), (x2 - c, y1), (x2, cy), (x2 - c, y2), (x1 + c, y2), (x1, cy)])
            return ("poly", _chamfer(x1, y1, x2, y2, min(min(w, h) / 2.0, corner)))
        # "box"
        if style == "round":
            return ("rrect", max(0, min(r, w / 2.0, h / 2.0)))
        if style == "square" or r <= 0:
            return ("rrect", 0)
        return ("poly", _chamfer(x1, y1, x2, y2, min(w / 2.0, h / 2.0, max(r, corner))))

    def _mask(kind, W, H, x1, y1, x2, y2, r, pts=None):
        """Mascara (L) a tamano supermuestreado de una pieza."""
        S = _SS
        m = _PImage.new("L", (W * S, H * S), 0)
        if x2 - x1 <= 0 or y2 - y1 <= 0:
            return m
        d = _PDraw.Draw(m)
        bx = (x1 * S, y1 * S, x2 * S - 1, y2 * S - 1)
        if pts is not None:
            d.polygon([(x * S, y * S) for (x, y) in pts], fill=255)
            return m
        g = _shape_geom(kind, bx[0], bx[1], bx[2], bx[3], r * S, k=S)
        if g[0] == "ellipse":
            d.ellipse(bx, fill=255)
        elif g[0] == "rrect":
            if g[1] > 0:
                d.rounded_rectangle(bx, radius=g[1], fill=255)
            else:
                d.rectangle(bx, fill=255)
        else:
            d.polygon(g[1], fill=255)
        return m

    def _layer(img, color, mask):
        lay = _PImage.new("RGBA", img.size, _hex_rgb(color) + (0,))
        lay.putalpha(mask)
        return _PImage.alpha_composite(img, lay)

    def shape_photo(kind, w, h, fill=None, outline=None, width=0, r=0, glow=None, pts=None):
        """PhotoImage con alfa de la pieza + margen (pad) que lleva alrededor."""
        key = (kind, w, h, fill, outline, round(width, 2), round(r, 2), glow,
               tuple(pts) if pts else None, SHAPE.get("style"), SHAPE.get("corner"))
        hit = _paint_cache.get(key)
        if hit is not None:
            return hit
        import io
        pad = px(6) if glow else 0
        W, H = w + 2 * pad, h + 2 * pad
        if pts is not None:
            pts = [(x + pad, y + pad) for (x, y) in pts]
        outer = _mask(kind, W, H, pad, pad, pad + w, pad + h, r, pts)
        inner = None
        if outline and width > 0:
            inner = _mask(kind, W, H, pad + width, pad + width, pad + w - width, pad + h - width,
                          max(0, r - width), None if pts is None else pts)
        outer = outer.resize((W, H), _PImage.LANCZOS)
        if inner is not None:
            inner = inner.resize((W, H), _PImage.LANCZOS)
        img = _PImage.new("RGBA", (W, H), (0, 0, 0, 0))
        if glow:
            g = outer.filter(_PFilter.GaussianBlur(pad * 0.55)).point(lambda v: int(v * 0.75))
            img = _layer(img, glow, g)
        if inner is not None:
            if fill:
                img = _layer(img, fill, inner)
            img = _layer(img, outline, _PChops.subtract(outer, inner))
        elif fill:
            img = _layer(img, fill, outer)
        buf = io.BytesIO(); img.save(buf, "PNG")
        ph = tk.PhotoImage(data=base64.b64encode(buf.getvalue()).decode("ascii"))
        _paint_cache[key] = (ph, pad)
        return ph, pad

    def paint(cv, kind, x1, y1, x2, y2, fill=None, outline=None, width=0, r=0, glow=False, tags=()):
        """Dibuja una pieza suave en el lienzo `cv` ocupando (x1, y1)-(x2, y2).
        glow=True: halo de neon si el tema lo pide (SHAPE['glow'])."""
        x1, y1 = int(round(x1)), int(round(y1))
        w, h = max(1, int(round(x2)) - x1), max(1, int(round(y2)) - y1)
        gl = (fill or outline) if (glow and SHAPE.get("glow")) else None
        width = max(0, width)
        if PAINT_OK:
            try:
                ph, pad = shape_photo(kind, w, h, fill, outline, width, r, gl)
                return cv.create_image(x1 - pad, y1 - pad, image=ph, anchor="nw", tags=tags)
            except Exception:
                pass
        # sin Pillow: primitivas del lienzo (con dientes, pero funciona)
        g = _shape_geom(kind, x1, y1, x1 + w, y1 + h, r)
        opts = dict(fill=(fill or ""), outline=(outline or ""), width=(width if outline else 0), tags=tags)
        if g[0] == "ellipse":
            return cv.create_oval(x1, y1, x1 + w, y1 + h, **opts)
        if g[0] == "rrect":
            if g[1] > 0:
                return round_rect(cv, x1, y1, x1 + w, y1 + h, g[1], **opts)
            return cv.create_rectangle(x1, y1, x1 + w, y1 + h, **opts)
        return cv.create_polygon([c for pt in g[1] for c in pt], **opts)

    def paint_poly(cv, pts, fill, tags=()):
        """Poligono libre suavizado (p. ej. el rayo de la bateria)."""
        xs, ys = [p_[0] for p_ in pts], [p_[1] for p_ in pts]
        x1, y1 = int(math.floor(min(xs))), int(math.floor(min(ys)))
        w, h = int(math.ceil(max(xs))) - x1 + 1, int(math.ceil(max(ys))) - y1 + 1
        if PAINT_OK:
            try:
                rel = tuple((round(x - x1, 2), round(y - y1, 2)) for (x, y) in pts)
                ph, _pad = shape_photo("poly", w, h, fill, pts=rel)
                return cv.create_image(x1, y1, image=ph, anchor="nw", tags=tags)
            except Exception:
                pass
        return cv.create_polygon([c for pt in pts for c in pt], fill=fill, outline="", tags=tags)

    def paint_arc(cv, x1, y1, x2, y2, start, extent, color, width, tags=()):
        """Arco suavizado (el indicador de 'conectando')."""
        w, h = int(round(x2 - x1)), int(round(y2 - y1))
        key = ("arc", w, h, int(start) % 360, int(extent), color, round(width, 2))
        hit = _paint_cache.get(key)
        if hit is None and PAINT_OK:
            try:
                import io
                S = _SS
                m = _PImage.new("L", (w * S, h * S), 0)
                ww = max(1, int(round(width * S)))
                # Pillow mide los angulos en sentido horario; Tk, antihorario
                _PDraw.Draw(m).arc((ww / 2, ww / 2, w * S - ww / 2 - 1, h * S - ww / 2 - 1),
                                   start=-(start + extent), end=-start, fill=255, width=ww)
                img = _layer(_PImage.new("RGBA", (w, h), (0, 0, 0, 0)), color,
                             m.resize((w, h), _PImage.LANCZOS))
                buf = io.BytesIO(); img.save(buf, "PNG")
                hit = tk.PhotoImage(data=base64.b64encode(buf.getvalue()).decode("ascii"))
                _paint_cache[key] = hit
            except Exception:
                hit = None
        if hit is not None:
            return cv.create_image(int(round(x1)), int(round(y1)), image=hit, anchor="nw", tags=tags)
        return cv.create_arc(x1, y1, x2, y2, start=start, extent=extent, style="arc",
                             outline=color, width=width, tags=tags)

    # --- imagenes de archivo (avatar, logo) ------------------------------------
    MV_LOGO = None                                      # se fija tras definir resource()

    def resource(name):
        """Archivo que va dentro del programa (junto al .py o dentro del .exe)."""
        return os.path.join(getattr(sys, "_MEIPASS", _BASE_DIR), name)

    MV_LOGO = resource("mv_logo.png")                   # va dentro del programa

    def image_frames(path, size, shaped=True, max_frames=150, radius=None):
        """Lista [(PhotoImage, ms)] de una imagen (GIF animado incluido),
        recortada en cuadrado, a `size` px y con la forma del tema. [] si falla."""
        if not PAINT_OK or not path or not os.path.exists(path):
            return []
        import io
        try:
            from PIL import ImageSequence
            src = _PImage.open(path)
            mask = None
            if shaped:
                mask = _mask("box", size, size, 0, 0, size, size, radius if radius is not None else px(4)).resize((size, size), _PImage.LANCZOS)
            out = []
            for k, fr in enumerate(ImageSequence.Iterator(src)):
                if k >= max_frames:
                    break
                f = fr.convert("RGBA")
                w, h = f.size
                side = min(w, h)
                f = f.crop(((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side))
                f = f.resize((size, size), _PImage.LANCZOS)
                if mask is not None:
                    f.putalpha(_PChops.multiply(f.getchannel("A"), mask))
                buf = io.BytesIO(); f.save(buf, "PNG")
                ms = fr.info.get("duration", 100) or 100
                out.append((tk.PhotoImage(data=base64.b64encode(buf.getvalue()).decode("ascii")),
                            max(20, int(ms))))
            return out
        except Exception:
            return []

    # --- silueta del raton (diseno de Javier) -------------------------------
    # Vectorizada a partir de su dibujo: linea central de cada trazo, simplificada
    # y llevada a un viewBox de 24x24. Se dibuja con curvas suaves, a cualquier
    # tamano y en cualquier color. No es el logo de Razer.
    _MOUSE_LINES = [
        [(6.97, 9.0), (6.93, 10.29), (6.77, 11.41), (6.37, 13.13), (5.57, 15.96), (5.37, 17.14), (5.28, 17.9), (5.28, 18.68), (5.5, 19.66), (5.81, 20.32), (6.35, 21.08), (7.04, 21.73), (7.87, 22.26), (8.76, 22.67), (9.76, 22.98), (10.87, 23.18), (12.41, 23.22), (13.24, 23.16), (14.71, 22.84), (15.64, 22.49), (16.51, 22.02), (17.23, 21.48), (17.83, 20.84), (18.19, 20.3), (18.54, 19.48), (18.7, 18.74), (18.7, 18.05), (18.61, 17.12), (18.23, 15.2), (17.56, 12.79), (17.2, 11.25), (17.05, 10.09), (17.0, 8.98)],
        [(12.01, 6.88), (12.23, 6.82), (12.46, 6.66), (12.64, 6.37), (12.72, 5.97), (12.7, 3.32), (12.55, 2.94), (12.32, 2.72), (12.01, 2.63)],
        [(11.99, 8.42), (11.99, 6.91)],
        [(7.0, 8.98), (7.53, 9.02), (8.47, 9.2), (9.6, 9.23), (10.25, 9.07), (11.3, 8.58), (11.99, 8.44)],
        [(11.97, 0.82), (11.59, 0.8), (11.43, 0.84), (10.14, 1.45), (8.85, 1.85), (8.04, 1.98), (6.44, 2.03), (6.26, 2.16), (6.06, 2.45), (5.95, 2.65), (5.88, 2.96), (5.9, 3.43), (6.55, 5.75), (6.82, 6.95), (6.97, 8.96)],
        [(12.01, 8.44), (12.84, 8.58), (13.86, 9.07), (14.42, 9.2), (15.44, 9.2), (17.0, 8.98)],
        [(11.99, 6.88), (11.68, 6.77), (11.45, 6.55), (11.3, 6.08), (11.3, 3.56), (11.34, 3.23), (11.5, 2.92), (11.68, 2.74), (11.97, 2.63)],
        [(11.99, 0.84), (11.99, 2.61)],
        [(12.01, 0.82), (12.43, 0.8), (12.59, 0.84), (13.93, 1.47), (14.98, 1.8), (15.89, 1.96), (17.56, 2.0), (17.69, 2.09), (17.92, 2.4), (18.1, 2.78), (18.12, 3.3), (17.98, 3.92), (17.25, 6.46), (17.07, 7.71), (17.0, 8.98)],
    ]

    def _catmull(pts, per_unit):
        """Interpola los puntos con una spline Catmull-Rom (curva suave que pasa
        por todos ellos). per_unit = muestras por unidad del viewBox."""
        P_ = [pts[0]] + list(pts) + [pts[-1]]
        out = []
        for i in range(1, len(pts)):
            p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
            seg = max(1, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) * per_unit))
            for n in range(seg):
                t = n / float(seg); t2 = t * t; t3 = t2 * t
                out.append(tuple(0.5 * (2 * p1[j] + (p2[j] - p0[j]) * t
                                        + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                        + (3 * p1[j] - p0[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
        out.append(tuple(pts[-1]))
        return out

    _mouse_cache = {}
    MOUSE_STROKE = 0.06           # grosor del trazo: fraccion del alto (min. 1,8 px)
    MOUSE_FILL = 0.94             # la silueta ocupa el 94 % del lienzo (margen para el trazo)

    def mouse_png(size, color, stroke=None):
        """PNG (bytes) de la silueta, `size` x `size` px, con antialias: se dibuja
        4-6 veces mas grande con pincel redondo y se reduce con LANCZOS. Pillow ya
        viene incluido con la bandeja del sistema. Devuelve None si no hay Pillow."""
        try:
            from PIL import Image, ImageDraw
        except Exception:
            return None
        import io
        ss = 6 if size <= 64 else 4
        big = size * ss
        k = big / 24.0 * MOUSE_FILL
        off = big / 2.0 - 12 * k
        r = max(1.8, (stroke if stroke else size * MOUSE_STROKE)) * ss / 2.0
        mask = Image.new("L", (big, big), 0)
        d = ImageDraw.Draw(mask)
        for pl in _MOUSE_LINES:
            for (x, y) in _catmull(pl, per_unit=max(8, ss * 3)):
                d.ellipse((x * k + off - r, y * k + off - r, x * k + off + r, y * k + off + r), fill=255)
        mask = mask.resize((size, size), Image.LANCZOS)
        rgb = tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        img = Image.new("RGBA", (size, size), rgb + (0,))
        img.putalpha(mask)
        buf = io.BytesIO(); img.save(buf, "PNG")
        return buf.getvalue()

    def mouse_photo(size, color):
        key = (size, color)
        ph = _mouse_cache.get(key)
        if ph is None:
            png = mouse_png(size, color)
            if png is None:
                return None
            ph = tk.PhotoImage(data=base64.b64encode(png).decode("ascii"))
            _mouse_cache[key] = ph
        return ph

    def draw_mouse(cv, cx, cy, size, color, tag="mouse"):
        """Dibuja la silueta centrada en (cx, cy) con alto `size` (px reales)."""
        cv.delete(tag)
        ph = mouse_photo(max(8, int(round(size))), color)
        if ph is not None:
            cv.create_image(cx, cy, image=ph, tags=tag)
            return
        k = size / 24.0                     # sin Pillow: lineas de Canvas (mas toscas)
        w = max(1.8, MOUSE_STROKE * size)
        ox, oy = cx - 12 * k, cy - 12 * k
        for pl in _MOUSE_LINES:
            flat = []
            for (x, y) in pl:
                flat += [ox + x * k, oy + y * k]
            cv.create_line(*flat, fill=color, width=w, capstyle="round", joinstyle="round",
                           smooth=True, splinesteps=12, tags=tag)

    def icon_label(parent, key, size=20, color=FG, bg=CARD):
        f = icon_font(size)
        if not f:
            return None
        return tk.Label(parent, text=IC[key], font=f, fg=color, bg=bg)

    class Toggle:
        """Interruptor tipo Windows 11 ligado a una BooleanVar existente.
        Etiqueta Activado/Desactivado a la izquierda (se retraduce)."""
        def __init__(self, parent, var, bg=CARD, enabled=True):
            self.var, self.bg, self.enabled = var, bg, enabled
            self.frame = tk.Frame(parent, bg=bg)
            self.lbl = tk.Label(self.frame, bg=bg, fg=FG, font=FONT_ROW)
            self.lbl.pack(side="left", padx=(0, px(12)))
            self.cv = tk.Canvas(self.frame, width=px(40) + 2 * GP, height=px(20) + 2 * GP, bg=bg,
                                highlightthickness=0, cursor="hand2")
            self.cv.pack(side="left")
            for w in (self.cv, self.lbl):
                w.bind("<Button-1>", self._click)
            var.trace_add("write", lambda *_: self.draw())
            reg(self.draw)

        def _click(self, _e=None):
            if self.enabled:
                self.var.set(not self.var.get())

        def set_enabled(self, on):
            self.enabled = bool(on); self.draw()

        def draw(self):
            on = bool(self.var.get())
            cv, W, H = self.cv, px(40), px(20)
            cv.delete("all")
            cv.configure(cursor=("hand2" if self.enabled else "arrow"))
            r = px(6)                                # radio de la bolita
            o = GP                                   # margen del halo
            if on and self.enabled:
                paint(cv, "pill", o, o, o + W, o + H, fill=ACCENT, glow=True)
                cx, knob = W - px(10), ON_ACCENT
            else:
                col = T["SWITCH_OFF"] if self.enabled else T["DISABLED"]
                paint(cv, "pill", o, o, o + W, o + H, outline=col, width=max(1, px(SHAPE.get("border", 1))))
                cx = (W - px(10)) if on else px(10)
                knob = T["KNOB_OFF"] if self.enabled else T["DISABLED"]
            paint(cv, "dot", o + cx - r, o + H / 2 - r, o + cx + r, o + H / 2 + r, fill=knob)
            self.lbl.configure(text=tr("on") if on else tr("off"),
                               fg=(FG if self.enabled else FG3))

    class Slider:
        """Deslizador propio: pista fina, parte recorrida y tirador en acento.
        on_release se llama al soltar (ahi se aplica al raton)."""
        def __init__(self, parent, var, lo=0, hi=100, width=220, bg=CARD, on_release=None):
            self.var, self.lo, self.hi, self.on_release, self.bg = var, lo, hi, on_release, bg
            self.W, self.H = px(width), px(24)
            self.cv = tk.Canvas(parent, width=self.W, height=self.H, bg=bg,
                                highlightthickness=0, cursor="hand2")
            self.cv.bind("<Button-1>", self._drag)
            self.cv.bind("<B1-Motion>", self._drag)
            self.cv.bind("<ButtonRelease-1>", self._release)
            var.trace_add("write", lambda *_: self.draw())
            self.draw()

        def _x(self, v):
            pad = px(9)
            return pad + (self.W - 2 * pad) * (v - self.lo) / float(self.hi - self.lo)

        def _drag(self, e):
            pad = px(9)
            frac = (e.x - pad) / float(max(1, self.W - 2 * pad))
            self.var.set(int(round(self.lo + max(0.0, min(1.0, frac)) * (self.hi - self.lo))))

        def _release(self, e):
            self._drag(e)
            if self.on_release:
                self.on_release()

        def draw(self):
            cv = self.cv; cv.delete("all")
            try: v = int(self.var.get())
            except Exception: v = self.lo
            y, x = self.H / 2, self._x(v)
            t2 = px(2)                                   # media pista (4 px)
            paint(cv, "pill", px(7), y - t2, self.W - px(7), y + t2, fill=T["SLIDER_TRACK"])
            if x - px(7) >= 2 * t2:
                paint(cv, "pill", px(7), y - t2, x, y + t2, fill=ACCENT)
            r1, r2 = px(9), px(5)
            paint(cv, "dot", x - r1, y - r1, x + r1, y + r1, fill=CTRL, outline=CTRL_BORDER, width=1)
            paint(cv, "dot", x - r2, y - r2, x + r2, y + r2, fill=ACCENT, glow=True)

    def text_box(parent, var, width_px, justify="left", bg=CARD, placeholder_key=None):
        """Caja de texto de Windows 11: fondo CTRL, linea inferior que se pone
        verde (2 px) con el foco. Devuelve (contenedor, entry)."""
        box = tk.Frame(parent, bg=CTRL, highlightthickness=1, highlightbackground=CTRL_BORDER,
                       width=px(width_px), height=px(32))
        box.pack_propagate(False)
        e = tk.Entry(box, textvariable=var, bg=CTRL, fg=FG, insertbackground=FG, relief="flat",
                     font=FONT_ROW, justify=justify, highlightthickness=0, bd=0)
        e.pack(fill="both", expand=True, padx=px(10))
        line = tk.Frame(box, bg=INPUT_LINE, height=1)
        line.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")
        ph = None
        if placeholder_key:
            ph = tk.Label(box, bg=CTRL, fg=FG3, font=FONT_ROW, cursor="xterm")
            reg(lambda: ph.configure(text=tr(placeholder_key)))
            def _ph(*_):
                if var.get() or root.focus_get() is e:
                    ph.place_forget()
                else:
                    ph.place(relx=(1.0 if justify == "right" else 0.0), x=(-px(10) if justify == "right" else px(10)),
                             rely=0.5, anchor=("e" if justify == "right" else "w"))
            var.trace_add("write", _ph)
            ph.bind("<Button-1>", lambda _e: e.focus_set())
            box.after_idle(_ph)
        def fin(_e=None):
            e.configure(bg=INPUT_FOCUS); box.configure(bg=INPUT_FOCUS)
            line.configure(bg=ACCENT, height=px(2))
            if ph: ph.place_forget()
        def fout(_e=None):
            e.configure(bg=CTRL); box.configure(bg=CTRL)
            line.configure(bg=INPUT_LINE, height=1)
            if ph and not var.get():
                ph.configure(bg=CTRL)
                ph.place(relx=(1.0 if justify == "right" else 0.0), x=(-px(10) if justify == "right" else px(10)),
                         rely=0.5, anchor=("e" if justify == "right" else "w"))
        e.bind("<FocusIn>", fin, add="+"); e.bind("<FocusOut>", fout, add="+")
        return box, e

    def link(parent, key, command, bg=BG, color=T["LINK"]):
        l = tk.Label(parent, bg=bg, fg=color, font=FONT_ROW, cursor="hand2")
        reg_text(l, key)
        l.bind("<Button-1>", lambda _e: command())
        l.bind("<Enter>", lambda _e: l.configure(font=FONT_ROW + ("underline",)))
        l.bind("<Leave>", lambda _e: l.configure(font=FONT_ROW))
        return l

    def autowrap(lbl, parent, margin=0, lo=200, hi=900):
        """Hace que el salto de linea de `lbl` siga al ancho de `parent`."""
        def f(e):
            w = max(px(lo), min(px(hi), e.width - px(margin)))
            if abs(w - int(float(lbl.cget("wraplength")))) > px(6):
                lbl.configure(wraplength=w)
        parent.bind("<Configure>", f, add="+")

    def page_title(parent, key):
        reg_text(tk.Label(parent, bg=BG, fg=FG, font=FONT_TITLE, anchor="w"), key).pack(
            fill="x", pady=(0, px(4)))

    def group_hdr(parent, key, first=False, note_key=None):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(px(6) if first else px(16), px(6)))
        reg_text(tk.Label(f, bg=BG, fg=FG, font=FONT_GROUP), key).pack(side="left")
        note = None
        if note_key:
            note = tk.Label(f, bg=BG, fg=FG2, font=FONT_DESC)
            reg_text(note, note_key).pack(side="left", padx=(px(10), 0))
        return f, note

    def stack(parent):
        """Contenedor de filas de un mismo grupo (separadas 2 px)."""
        f = tk.Frame(parent, bg=BG); f.pack(fill="x")
        return f

    class Card:
        """Tarjeta-fila: [icono] titulo/descripcion ............ [control]."""
        def __init__(self, parent, icon=None, title=None, desc=None, min_h=52, indent=False,
                     wrap=330):
            self.frame = tk.Frame(parent, bg=CARD, highlightthickness=1,
                                  highlightbackground=CARD_BORDER, highlightcolor=CARD_BORDER)
            self.frame.pack(fill="x", pady=(0, px(2)))
            inner = tk.Frame(self.frame, bg=CARD)
            inner.pack(fill="x", padx=px(16), pady=px(6))
            inner.grid_columnconfigure(1, weight=1)
            inner.grid_rowconfigure(0, minsize=px(min_h - 18))
            self.inner = inner
            self.icon = None
            if icon:
                self.icon = icon_label(inner, icon, 20)
                if self.icon:
                    self.icon.grid(row=0, column=0, sticky="w", padx=(0, px(16)))
            elif indent and F_ICON:
                tk.Frame(inner, bg=CARD, width=px(36)).grid(row=0, column=0)
            tx = tk.Frame(inner, bg=CARD); tx.grid(row=0, column=1, sticky="w")
            self.title = tk.Label(tx, bg=CARD, fg=FG, font=FONT_ROW, anchor="w", justify="left")
            self.title.pack(anchor="w")
            self.desc = tk.Label(tx, bg=CARD, fg=FG2, font=FONT_DESC, anchor="w", justify="left",
                                 wraplength=px(wrap))
            if title: reg_text(self.title, title)
            if desc:
                reg_text(self.desc, desc); self.desc.pack(anchor="w")
            self.ctrl = tk.Frame(inner, bg=CARD)
            self.ctrl.grid(row=0, column=2, sticky="e", padx=(px(12), 0))
            inner.bind("<Configure>", self._refit)

        def _refit(self, _e=None):
            """Ajusta el salto de linea de la descripcion al ancho real de la fila
            (la ventana se puede redimensionar)."""
            try:
                w = self.inner.winfo_width()
                if w <= 1:
                    return
                col0 = self.inner.grid_bbox(0, 0)[2]
                want = max(px(110), min(px(640), w - col0 - self.ctrl.winfo_reqwidth() - px(24)))
                if abs(want - int(float(self.desc.cget("wraplength")))) > px(6):
                    self.desc.configure(wraplength=want)
            except tk.TclError:
                pass

        def set_desc(self, text):
            if text:
                self.desc.configure(text=text)
                if not self.desc.winfo_ismapped(): self.desc.pack(anchor="w")
            else:
                self.desc.pack_forget()

    class ScrollPage:
        """Pagina con desplazamiento vertical si el contenido no cabe. La barra
        de scroll solo aparece cuando hace falta."""
        def __init__(self, parent):
            self.outer = tk.Frame(parent, bg=BG)
            self.cv = tk.Canvas(self.outer, bg=BG, highlightthickness=0, bd=0)
            self.sb = ttk.Scrollbar(self.outer, orient="vertical", command=self.cv.yview)
            self.cv.configure(yscrollcommand=self.sb.set)
            self.cv.pack(side="left", fill="both", expand=True)
            self.body = tk.Frame(self.cv, bg=BG)
            self._win = self.cv.create_window(0, 0, window=self.body, anchor="nw")
            self.body.bind("<Configure>", lambda _e: self._update())
            self.cv.bind("<Configure>", lambda e: (self.cv.itemconfigure(self._win, width=e.width),
                                                   self._update()))
            self.outer.bind("<Enter>", lambda _e: self._wheel(True))
            self.outer.bind("<Leave>", lambda _e: self._wheel(False))

        def _update(self):
            self.cv.configure(scrollregion=self.cv.bbox("all"))
            need = self.body.winfo_reqheight() > self.cv.winfo_height() + 2
            if need and not self.sb.winfo_ismapped():
                self.sb.pack(side="right", fill="y", before=self.cv)
            elif not need and self.sb.winfo_ismapped():
                self.sb.pack_forget(); self.cv.yview_moveto(0)

        def _wheel(self, on):
            if on:
                root.bind_all("<MouseWheel>", self._on_wheel)
                root.bind_all("<Button-4>", lambda _e: self.cv.yview_scroll(-1, "units"))
                root.bind_all("<Button-5>", lambda _e: self.cv.yview_scroll(1, "units"))
            else:
                root.unbind_all("<MouseWheel>"); root.unbind_all("<Button-4>"); root.unbind_all("<Button-5>")

        def _on_wheel(self, e):
            if self.sb.winfo_ismapped():
                self.cv.yview_scroll(int(-e.delta / 120), "units")

    def dark_titlebar(win):
        """Barra de titulo clara u oscura segun el tema (Windows 10 1809+ / 11)."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            win.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
            val = ctypes.c_int(0 if THEME_MODE == "light" else 1)      # modo claro u oscuro
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), 4) != 0:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(val), 4)
            r_, g_, b_ = (int(BG[i:i + 2], 16) for i in (1, 3, 5))
            col = ctypes.c_int((b_ << 16) | (g_ << 8) | r_)              # COLORREF = 0x00BBGGRR
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(col), 4)
        except Exception:
            pass

    def round_corners(win):
        """Esquinas redondeadas de Windows 11 para ventanas sin bordes."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            win.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
            pref = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(pref), 4)
        except Exception:
            pass

    # =====================================================================
    # 4) ESTRUCTURA: barra lateral fija + area de contenido con paginas
    # =====================================================================
    shell = tk.Frame(root, bg=BG); shell.pack(fill="both", expand=True)
    sidebar = tk.Frame(shell, bg=BG, width=px(272))
    sidebar.pack(side="left", fill="y"); sidebar.pack_propagate(False)
    side_in = tk.Frame(sidebar, bg=BG)
    side_in.pack(fill="both", expand=True, padx=(px(16), px(12)), pady=(px(8), px(16)))
    content = tk.Frame(shell, bg=BG)
    content.pack(side="left", fill="both", expand=True)
    pages_box = tk.Frame(content, bg=BG)
    pages_box.pack(fill="both", expand=True, padx=(px(20), px(32)), pady=(px(4), px(20)))
    pages_box.grid_rowconfigure(0, weight=1); pages_box.grid_columnconfigure(0, weight=1)

    PAGES = {}

    def new_page(name, scroll=True):
        if scroll:
            sp = ScrollPage(pages_box)
            sp.outer.grid(row=0, column=0, sticky="nsew")
            PAGES[name] = sp.outer
            return sp.body
        f = tk.Frame(pages_box, bg=BG); f.grid(row=0, column=0, sticky="nsew")
        PAGES[name] = f
        return f

    # --- bloque del dispositivo (como el avatar de Configuracion) ---------------
    dev = tk.Frame(side_in, bg=BG); dev.pack(fill="x", pady=(px(8), px(18)))
    dev_cv = tk.Canvas(dev, width=px(60), height=px(60), bg=BG, highlightthickness=0)
    dev_cv.pack(side="left")
    paint(dev_cv, "dot", 0, 0, px(60), px(60), fill=CTRL)
    dev_txt = tk.Frame(dev, bg=BG); dev_txt.pack(side="left", padx=(px(12), 0), fill="x")
    dev_l1 = tk.Frame(dev_txt, bg=BG); dev_l1.pack(anchor="w")
    spin_cv = tk.Canvas(dev_l1, width=px(14), height=px(14), bg=BG, highlightthickness=0)
    dev_name = tk.Label(dev_l1, bg=BG, fg=FG, font=FONT_GROUP, anchor="w", justify="left",
                        wraplength=px(150))
    dev_name.pack(side="left")
    dev_l2 = tk.Frame(dev_txt, bg=BG, cursor="hand2"); dev_l2.pack(anchor="w", pady=(px(2), 0))
    dev_batt_ic = tk.Label(dev_l2, bg=BG, fg=FG2, font=(icon_font(12) or FONT_DESC), cursor="hand2")
    dev_sub = tk.Label(dev_l2, bg=BG, fg=FG2, font=FONT_DESC, anchor="w", cursor="hand2",
                       wraplength=px(170), justify="left")
    dev_sub.pack(side="left")
    # modo Mediavida: el logo del foro en lugar del raton (redondeado)
    mv_logo_big = image_frames(MV_LOGO, px(60), radius=px(14)) if MV_ACTIVE else []

    spin_angle = [0]; spin_job = [None]

    def _spin():
        a = spin_angle[0]
        spin_cv.delete("all")
        paint_arc(spin_cv, px(1), px(1), px(13), px(13), a, 270, ACCENT, max(1, px(1.6)))
        spin_angle[0] = (a - 18) % 360
        spin_job[0] = root.after(60, _spin)

    def _spin_on(on):
        if on and spin_job[0] is None:
            spin_cv.pack(side="left", padx=(0, px(6)), before=dev_name)
            _spin()
        elif not on and spin_job[0] is not None:
            root.after_cancel(spin_job[0]); spin_job[0] = None
            spin_cv.pack_forget()

    # estado de conexion y bateria (los usa la logica copiada)
    state_conn = [None]
    batt_supported = [None]                  # None=desconocido, True/False tras conectar
    state_batt = [None]                      # None o (pct, cargando)

    def render_device():
        """Pinta el bloque del dispositivo de la barra lateral."""
        connected = bool(state_conn[0])
        if mv_logo_big:
            if not dev_cv.find_withtag("mvlogo"):
                dev_cv.delete("all")
                dev_cv.create_image(0, 0, image=mv_logo_big[0][0], anchor="nw", tags="mvlogo")
        else:
            draw_mouse(dev_cv, px(30), px(30), px(40), ACCENT if connected else FG3)
        if not connected:
            _spin_on(True)
            dev_name.configure(text=tr("searching"))
            dev_sub.configure(text=tr("searching_desc")); dev_batt_ic.pack_forget()
            return
        _spin_on(False)
        nm = str(state_conn[0])
        nm = nm[6:] if nm.startswith("Razer ") else nm
        dev_name.configure(text=nm)
        if batt_supported[0] and state_batt[0] is not None:
            pct, chg = state_batt[0]
            dev_sub.configure(text=tr("conn_batt_chg" if chg else "conn_batt", pct=pct))
            if F_ICON:
                dev_batt_ic.configure(text=batt_glyph(pct, chg),
                                      fg=(LOW_BATT if (pct < 20 and not chg) else FG2))
                dev_batt_ic.pack(side="left", padx=(0, px(6)), before=dev_sub)
        else:
            dev_sub.configure(text=tr("conn_only")); dev_batt_ic.pack_forget()
        update_tray_tip()

    def tray_status():
        """Perfil activo, DPI y bateria en una linea (tooltip y menu de la bandeja)."""
        try:
            if mouse.dev is None or not state_conn[0]:
                return tr("searching")
            parts = []
            cur = current[0]
            if cur is not None and profiles[cur]:
                parts.append(tr("tip_profile", n=cur + 1, x=profiles[cur]))
            if batt_supported[0] and state_batt[0] is not None:
                pct, chg = state_batt[0]
                parts.append(tr("tip_batt_chg" if chg else "tip_batt", pct=pct))
            return " · ".join(parts)
        except NameError:                     # aun montandose la ventana
            return ""

    def tray_tip():
        """Texto al pasar el raton por el icono de la bandeja. Windows corta los
        tooltips de la bandeja a 127 caracteres."""
        st_ = tray_status()
        return (f"{APP_NAME}\n{st_}" if st_ else APP_NAME)[:127]

    def update_tray_tip():
        """Refresca tooltip y menu si el icono de la bandeja esta visible."""
        try:
            icon = tray[0]
        except NameError:
            return
        if icon is not None:
            try:
                icon.title = tray_tip()
                icon.update_menu()
            except Exception:
                pass

    def render_status():
        render_device()

    def render_batt():
        render_device()
    reg(render_device)

    def on_batt_click(_e=None):
        if mouse.dev is not None and batt_supported[0]:
            do_read_battery()
    for _w in (dev_l2, dev_sub, dev_batt_ic):
        _w.bind("<Button-1>", on_batt_click)

    # --- navegacion ----------------------------------------------------------
    nav_items = {}
    current_page = [None]

    def nav_item(parent, name, icon, key):
        it = tk.Frame(parent, bg=BG, height=px(36), cursor="hand2")
        it.pack(fill="x", pady=(0, px(4))); it.pack_propagate(False)
        pill = tk.Canvas(it, width=px(3), height=px(16), bg=BG, highlightthickness=0)
        pill.place(x=0, rely=0.5, anchor="w")
        ic = tk.Label(it, text=(IC[icon] if F_ICON else ""), font=(icon_font(16) or FONT_ROW),
                      fg=FG2, bg=BG)
        ic.place(x=px(12), rely=0.5, anchor="w")
        tx = tk.Label(it, bg=BG, fg=FG, font=FONT_ROW)
        tx.place(x=px(12 + (30 if F_ICON else 0)), rely=0.5, anchor="w")
        reg_text(tx, key)
        parts = (it, pill, ic, tx)
        def repaint(hover=False):
            sel = current_page[0] == name
            bgc = CTRL if (sel or hover) else BG
            for w in parts: w.configure(bg=bgc)
            pill.delete("all")
            if sel:
                paint(pill, "pill", 0, 0, px(3), px(16), fill=ACCENT)
        for w in parts:
            w.bind("<Enter>", lambda _e: repaint(True))
            w.bind("<Leave>", lambda _e: repaint(False))
            w.bind("<Button-1>", lambda _e: show_page(name))
        nav_items[name] = repaint
        return it

    def set_language(code):
        """Cambia el idioma al momento (sin reiniciar) y lo recuerda."""
        if code == lang[0] or code not in ("es", "en"):
            return
        lang[0] = code
        presets["lang"] = code; save_presets(presets)
        retranslate()

    class LangSwitch:
        """Interruptor ES | EN (pildora con la mitad activa en acento)."""
        W, H = 88, 28

        def __init__(self, parent):
            self.frame = tk.Frame(parent, bg=BG, height=px(40))
            self.frame.pack(fill="x", pady=(0, px(4))); self.frame.pack_propagate(False)
            ic = tk.Label(self.frame, text=(IC["lang"] if F_ICON else ""),
                          font=(icon_font(16) or FONT_ROW), fg=FG2, bg=BG)
            ic.place(x=px(12), rely=0.5, anchor="w")
            tx = tk.Label(self.frame, bg=BG, fg=FG, font=FONT_ROW)
            tx.place(x=px(12 + (30 if F_ICON else 0)), rely=0.5, anchor="w")
            reg_text(tx, "lang_title")
            self.cv = tk.Canvas(self.frame, width=px(self.W) + 2 * GP, height=px(self.H) + 2 * GP, bg=BG,
                                highlightthickness=0, cursor="hand2")
            self.cv.place(relx=1.0, x=-px(6) + GP, rely=0.5, anchor="e")
            self.cv.bind("<Button-1>", self._click)
            reg(self.draw)

        def _click(self, e):
            set_language("es" if e.x - GP < px(self.W) / 2.0 else "en")

        def draw(self):
            cv, W, H, o = self.cv, px(self.W), px(self.H), GP
            cv.delete("all")
            paint(cv, "pill", o, o, o + W, o + H, fill=CTRL, outline=CTRL_BORDER, width=1)
            half = W / 2.0
            sel = 0 if lang[0] == "es" else 1
            x0 = px(3) if sel == 0 else half
            x1 = half if sel == 0 else W - px(3)
            paint(cv, "pill", o + x0, o + px(3), o + x1, o + H - px(3), fill=ACCENT, glow=True)
            for k, code in enumerate(("ES", "EN")):
                cv.create_text(o + half * (0.5 + k), o + H / 2.0, text=code, font=font(12, semibold=True),
                               fill=(ON_ACCENT if k == sel else FG2))

    nav_top = tk.Frame(side_in, bg=BG); nav_top.pack(fill="x")
    nav_bottom = tk.Frame(side_in, bg=BG); nav_bottom.pack(side="bottom", fill="x")
    lang_switch = LangSwitch(nav_bottom)         # encima de Registro / Acerca de
    for _n, _ic, _k in (("profiles", "profiles", "nav_profiles"), ("lighting", "lighting", "nav_lighting"),
                        ("buttons", "buttons", "nav_buttons"), ("settings", "settings", "nav_settings")):
        nav_item(nav_top, _n, _ic, _k)
    for _n, _ic, _k in (("log", "log", "nav_log"), ("about", "about", "nav_about")):
        nav_item(nav_bottom, _n, _ic, _k)

    def nav_link(parent, icon, key, command, image=None):
        """Entrada de la barra lateral que abre algo (no es una pagina).
        image: PhotoImage pequena en lugar del icono de la fuente."""
        it = tk.Frame(parent, bg=BG, height=px(36), cursor="hand2")
        it.pack(fill="x", pady=(0, px(4))); it.pack_propagate(False)
        if image is not None:
            ic = tk.Label(it, image=image, bg=BG)
            ic._img = image
        else:
            ic = tk.Label(it, text=(IC[icon] if F_ICON else ""), font=(icon_font(16) or FONT_ROW),
                          fg=T["LINK"], bg=BG)
        ic.place(x=px(12), rely=0.5, anchor="w")
        tx = tk.Label(it, bg=BG, fg=FG, font=FONT_ROW)
        tx.place(x=px(12 + (30 if (F_ICON or image is not None) else 0)), rely=0.5, anchor="w")
        reg_text(tx, key)
        parts = (it, ic, tx)
        for w in parts:
            w.bind("<Enter>", lambda _e: [p_.configure(bg=CTRL) for p_ in parts])
            w.bind("<Leave>", lambda _e: [p_.configure(bg=BG) for p_ in parts])
            w.bind("<Button-1>", lambda _e: command())
        return it
    kofi_nav = nav_link(nav_bottom, "heart", "nav_kofi", lambda: open_kofi())
    mv_logo_small = image_frames(MV_LOGO, px(18), shaped=False)
    mv_nav = None
    if MV_ACTIVE:                                      # solo en modo Mediavida, encima de Idioma
        mv_nav = nav_link(nav_bottom, "open", "nav_mv_thread", lambda: open_url(MV_THREAD_URL),
                          image=(mv_logo_small[0][0] if mv_logo_small else None))
        mv_nav.pack_configure(before=lang_switch.frame)
        mv_spy = nav_link(nav_top, "view", "nav_mv_spy", lambda: open_url(MV_SPY_URL))  # debajo de Ajustes

    def show_page(name):
        if name not in PAGES:
            return
        current_page[0] = name
        PAGES[name].tkraise()
        for _rp in nav_items.values(): _rp()
        presets["last_page"] = name; save_presets(presets)

    # =====================================================================
    # 5) REGISTRO (se crea el primero: log() escribe aunque no este a la vista)
    # =====================================================================
    pg_log = new_page("log", scroll=False)
    page_title(pg_log, "log_title")
    log_desc_lbl = tk.Label(pg_log, bg=BG, fg=FG2, font=font(13), anchor="w", justify="left",
                            wraplength=px(700))
    reg_text(log_desc_lbl, "log_desc").pack(fill="x", pady=(0, px(12)))
    autowrap(log_desc_lbl, pg_log, 8, lo=240, hi=1400)
    log_wrap = tk.Frame(pg_log, bg=LOG_BG, highlightthickness=1, highlightbackground=LOG_BORDER)
    log_wrap.pack(fill="both", expand=True)
    log_sb = ttk.Scrollbar(log_wrap, orient="vertical")

    def _log_scroll(lo, hi):
        """La barra solo aparece cuando el registro no cabe."""
        log_sb.set(lo, hi)
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            log_sb.pack_forget()
        elif not log_sb.winfo_ismapped():
            log_sb.pack(side="right", fill="y", before=logbox)
    logbox = tk.Text(log_wrap, state="disabled", bg=LOG_BG, fg=FG2, font=FONT_LOG, relief="flat",
                     highlightthickness=0, bd=0, padx=px(16), pady=px(12), wrap="word",
                     yscrollcommand=_log_scroll, insertbackground=FG, selectbackground=T["SELECT_BG"], selectforeground=FG)
    log_sb.configure(command=logbox.yview)
    logbox.pack(side="left", fill="both", expand=True)
    log_actions = tk.Frame(pg_log, bg=BG); log_actions.pack(fill="x", pady=(px(12), 0))
    log_note = tk.Label(pg_log, bg=BG, fg=FG2, font=FONT_DESC, anchor="w", justify="left",
                        wraplength=px(560))
    log_note.pack(fill="x", pady=(px(8), 0))
    autowrap(log_note, pg_log, 0, lo=240, hi=900)
    state_fw = ["?"]                         # firmware leido (para reportes)

    LOG_MAX_LINES = 1500                     # con el programa dias abierto, no crece sin fin

    def log(m):
        logbox.configure(state="normal"); logbox.insert("end", str(m) + "\n")
        try:
            n = int(logbox.index("end-1c").split(".")[0])
            if n > LOG_MAX_LINES:
                logbox.delete("1.0", f"{n - LOG_MAX_LINES + 1}.0")
        except Exception:
            pass
        logbox.see("end"); logbox.configure(state="disabled")

    def guard(fn):
        """Envuelve un handler para que cualquier excepcion vaya al log en vez
        de romper la interfaz."""
        def w(*a, **k):
            try: fn(*a, **k)
            except Exception as e: log(f"[ERROR] {e}")
        return w

    batt_doubt = {"val": None, "n": 0, "job": None}     # lectura dudosa pendiente de confirmar

    def battery_plausible(pct, chg):
        """Filtro de lecturas raras. El receptor inalambrico puede dar 0 % (o un
        salto enorme) mientras el raton se despierta o al arrancar. Una lectura
        asi solo se acepta si se repite en la siguiente lectura; mientras, se
        sigue mostrando el valor anterior (o nada)."""
        prev = state_batt[0]
        odd = (pct <= 0 and not chg) or pct > 100
        if prev is not None and not odd and chg == prev[1] and abs(pct - prev[0]) >= 25:
            odd = True                                 # salto de 25 puntos de golpe
        if not odd:
            batt_doubt["val"] = None; batt_doubt["n"] = 0
            return True
        dv = batt_doubt["val"]
        if dv is not None and dv[1] == chg and abs(dv[0] - pct) <= 3:   # se repite (mas o menos)
            batt_doubt["n"] += 1; batt_doubt["val"] = (pct, chg)
        else:
            batt_doubt["val"] = (pct, chg); batt_doubt["n"] = 1
        if batt_doubt["n"] >= 3 and pct <= 100:      # se repite: es real
            batt_doubt["val"] = None; batt_doubt["n"] = 0
            return True
        batt_retry_soon()
        return False

    def batt_retry_soon(ms=2500):
        """Vuelve a leer la bateria en un rato (una sola espera pendiente)."""
        if batt_doubt["job"] is not None:
            return
        def _again():
            batt_doubt["job"] = None
            if mouse.dev is not None and not refresh_battery_async():
                batt_retry_soon(500)                   # el hilo de E/S estaba ocupado
        try:
            batt_doubt["job"] = root.after(ms, _again)
        except Exception:
            batt_doubt["job"] = None

    @guard
    def do_read_battery():
        try:
            pct, chg = mouse.get_battery()
        except MouseBusy as e:
            log(f"[!] {e}"); batt_retry_soon(3000); return
        if not battery_plausible(pct, chg):
            log(trl("log_batt_doubt", pct=pct))
            return
        state_batt[0] = (pct, chg); render_batt()
        log(trl("log_batt", pct=pct, chg=(trl("batt_charging") if chg else "")))
        evaluate_battery(pct, chg)

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
                log(trl("log_connecting", name=m["name"]))
            mouse.connect(m, log=(log if manual else (lambda s: None)))
        except Exception as e:
            if manual or str(e) != last_conn_err[0]:
                log(f"[!] {e}")
            last_conn_err[0] = str(e)
            state_conn[0] = None; render_status()
            return False
        try:
            fw = mouse.get_firmware()
        except Exception:
            fw = None
        _after_connect(m, fw)
        refresh_battery()
        return True

    def _after_connect(m, fw):
        """Lo que se hace en la interfaz al conectar (en el hilo de Tk)."""
        last_conn_err[0] = None
        real = _model_for_pid(mouse.pid) or m          # modelo real (DPI max, LED...)
        mouse.model = real
        active_model[0] = real
        read_fails[0] = 0
        state_conn[0] = real["name"]; render_status()
        presets["last_model"] = model_var.get(); save_presets(presets)
        batt_supported[0] = real["wireless"]
        log(trl("log_connected_ok", name=real["name"]))
        if fw:
            state_fw[0] = f"v{fw[0]}.{fw[1]}"
        on_connected()                                 # toma el control de los perfiles

    def connect_async():
        """Intento de conexion automatico SIN congelar la ventana: la busqueda y
        el sondeo del raton van en el hilo de E/S."""
        m = current_model()
        last_conn_try[0] = time.time()

        def job():
            mouse.connect(m)
            try:
                fw = mouse.get_firmware()
            except Exception:
                fw = None
            return fw

        def done(st, res):
            if st != "ok":
                e = res
                if str(e) != last_conn_err[0]:
                    log(f"[!] {e}")
                last_conn_err[0] = str(e)
                if mouse.dev is None:
                    state_conn[0] = None; render_status()
                return
            if mouse.dev is None or wizard_active[0]:
                return
            _after_connect(m, res)
            last_batt[0] = 0.0                           # leer la bateria ya (en E/S)
        io_submit(job, done)

    def on_disconnected():
        stop_listener()
        sniper_state["active"] = False
        try: mouse.close()
        except Exception: pass
        state_conn[0] = None; render_status()
        state_batt[0] = None; render_batt()
        batt_doubt["val"] = None; batt_doubt["n"] = 0
        render_profiles()
        log(trl("log_disconnected"))

    def refresh_battery():
        """Lee la bateria sin llenar el log."""
        if mouse.dev is None or not batt_supported[0]:
            render_batt(); return
        try:
            res = ("ok", mouse.get_battery())
        except Exception as e:
            res = ("err", e)
        _batt_result(*res)

    def _batt_result(st, res):
        """Resultado de una lectura de bateria (venga del hilo que venga)."""
        if mouse.dev is None or not batt_supported[0]:
            render_batt(); return
        if st != "ok":
            # raton despertandose / receptor ocupado: se reintenta pronto en vez
            # de esperar al minuto (antes se quedaba sin bateria o con 0 %)
            render_batt(); batt_retry_soon(3000); return
        pct, chg = res
        if not battery_plausible(pct, chg):
            render_batt(); return
        state_batt[0] = (pct, chg)
        render_batt()
        evaluate_battery(pct, chg)

    def refresh_battery_async():
        if mouse.dev is None or not batt_supported[0]:
            return False
        return io_submit(mouse.get_battery, _batt_result)

    # =====================================================================
    # 7) PERFILES (estado, modos control/compatibilidad y pagina)
    # =====================================================================
    DEFAULT_PROFILES = [400, 800, 1600, 3200, 6400]
    # Colores de los perfiles INTERNOS del raton (LED de debajo), en el orden en
    # que los recorre su boton de perfil (Viper Ultimate): rojo, verde, azul,
    # turquesa, amarillo. El perfil N del programa se graba en el color N.
    PROFILE_COLORS = ["#FF2E4D", "#2BFF6E", "#2F86FF", "#00F0E1", "#FFE138"]   # neon, siempre planos
    PROFILE_TEXT   = ["#FFFFFF", "#14140F", "#FFFFFF", "#14140F", "#14140F"]  # por si hay texto encima
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
                             lambda raw: uiq.put(lambda r=raw: on_other_report(r)),
                             lambda code: uiq.put(lambda c=code: on_button_release(c)))
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
            log(trl("log_ctrl_verify"))
        else:
            log(trl("log_ctrl_on"))
        return True

    def release_control(announce=True):
        """Devuelve el raton a su modo normal (sus perfiles de fabrica)."""
        stop_listener()
        verify_deadline[0] = None
        sniper_state["active"] = False               # el DPI se reaplica al retomar el control
        if ctrl_on[0] and mouse.dev is not None:
            try: mouse.set_device_mode(RazerMouse.MODE_NORMAL)
            except Exception: pass
            if announce:
                log(trl("log_ctrl_restored"))
        ctrl_on[0] = False

    def fall_back(reason_key):
        """No se pudo usar el modo control: pasa a compatibilidad."""
        release_control(announce=False)
        log(trl(reason_key))
        start_compat()

    def on_connected():
        if ctrl_want[0] and take_control():
            pass
        else:
            if ctrl_want[0]:
                log(trl("log_ctrl_fail"))
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
                log(trl("log_learn_done", n=len(_enabled())))
            elif current[0] != prev and not initial:
                log(trl("log_prof_changed", n=current[0] + 1, x=x))
        elif learning[0]:
            empty = [i for i, v in enumerate(profiles) if not v]
            if empty:
                idx = empty[0]; profiles[idx] = x; current[0] = idx
                log(trl("log_learned", n=idx + 1, x=x))
                if len(empty) == 1:
                    learning[0] = False
                    log(trl("log_learn_done", n=5))
            else:
                learning[0] = False
                current[0] = None
        else:
            current[0] = None                   # no cuadra: se indica, no se toca nada
            if not initial and x != last_dpi[0]:
                log(trl("log_prof_unknown", x=x))
        last_dpi[0] = x
        _save_profiles(); render_profiles()
        if not initial and current[0] is not None and current[0] != prev:
            return current[0]
        return None

    # ---- escritor de DPI (hilo propio) -------------------------------------------
    # Los cambios de DPI de los perfiles y del sniper van por UN hilo y en orden:
    # la ventana no espera al raton (si el receptor esta ocupado, antes se podia
    # congelar mas de un segundo) y, si llegan varios seguidos, solo se manda el
    # ultimo. Nunca escribe en la memoria del raton (NOSTORE).
    dpi_q = queue.Queue()

    def set_dpi_async(x):
        dpi_q.put(int(x))

    def _dpi_worker():
        while True:
            x = dpi_q.get()
            if x is None:
                return
            while not dpi_q.empty():                 # solo importa el ultimo
                nxt = dpi_q.get_nowait()
                if nxt is None:
                    return
                x = nxt
            if mouse.dev is None:
                continue
            try:
                mouse.set_dpi(x, persist=False)
            except Exception as e:
                uiq.put(lambda e=e: log(f"[!] {e}"))
                # el bucle automatico vuelve a mandarlo si el raton no lo tiene

    # ---- aplicar perfiles (modo control) ---------------------------------------
    def apply_profile(i, announce=True):
        """Aplica el perfil i al raton (sin tocar su memoria interna)."""
        if i is None or not (0 <= i < 5) or not profiles[i] or mouse.dev is None:
            return
        if sniper_state["active"]:
            sniper_state["prev"] = profiles[i]           # al soltar el sniper vuelve a ESTE perfil
        else:
            set_dpi_async(profiles[i])
        current[0] = i; last_dpi[0] = profiles[i]
        _save_profiles(); render_profiles()
        if announce:
            log(trl("log_prof_changed", n=i + 1, x=profiles[i]))
            if notify_var.get():
                show_toast(i)
            blink_for(i)

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
        log(trl("log_btn_raw", rid=f"0x{raw[0]:02X}", data=" ".join(f"{b:02X}" for b in raw[:8])))

    def on_button(code):
        """Pulsacion recibida del raton (hilo de Tk, via cola)."""
        if not ctrl_on[0]:
            return
        if not verified[0]:
            verified[0] = True; verify_deadline[0] = None
            presets["control_verified"] = True; save_presets(presets)
            log(trl("log_ctrl_verified"))
        if code not in buttons_seen:                     # boton nuevo: aparece en la pestana
            buttons_seen.append(code)
            presets["buttons_seen"] = buttons_seen; save_presets(presets)
            log(trl("log_btn_new", name=btn_name(code)))
            build_btn_rows()
        flash_btn(code)
        exec_rep4(code)

    def on_button_release(code):
        """Un boton especial del raton se ha SOLTADO (lo necesita el sniper)."""
        if ctrl_on[0] and _rep4_action(code) == "sniper":
            sniper_q.put(False)

    LBL_OFF = FG3
    LBL_ON  = T["LINK"]
    LED_KEYS = ["led_red", "led_green", "led_blue", "led_turq", "led_yellow"]

    pg_prof = new_page("profiles")
    page_title(pg_prof, "nav_profiles")

    # --- tarjeta "Perfil activo" ---------------------------------------------
    act_card = Card(pg_prof, icon="profiles", title="active_hdr", min_h=68, wrap=300)
    act_big = tk.Label(act_card.ctrl, bg=CARD, fg=FG, font=FONT_BIG, anchor="e")
    act_big.pack(anchor="e")
    act_small = tk.Label(act_card.ctrl, bg=CARD, fg=FG2, font=FONT_DESC, anchor="e")
    act_small.pack(anchor="e")
    mode_lbl = tk.Label(pg_prof, bg=BG, fg=FG3, font=FONT_DESC, anchor="w")
    mode_lbl.pack(fill="x", pady=(px(6), 0))
    mode_var = tk.StringVar()
    mode_var.trace_add("write", lambda *_: mode_lbl.configure(text=mode_var.get()))
    active_var = tk.StringVar()

    # --- grupo "Tus perfiles" -------------------------------------------------
    group_hdr(pg_prof, "my_profiles_hdr")
    prof_stack = stack(pg_prof)
    row_dot, row_card, row_entry, row_side, prof_vars = [], [], [], [], []
    for i in range(5):
        c = Card(prof_stack, title=None, min_h=52, wrap=260)
        dot = tk.Canvas(c.inner, width=px(10), height=px(10), bg=CARD, highlightthickness=0)
        dot.grid(row=0, column=0, sticky="w", padx=(px(5), px(21)))
        v = tk.StringVar(value=(str(profiles[i]) if profiles[i] else ""))
        box, en = text_box(c.ctrl, v, 96, justify="right", placeholder_key="ph_off")
        box.pack(side="left")
        tk.Label(c.ctrl, text="DPI", bg=CARD, fg=FG2, font=FONT_ROW).pack(side="left", padx=(px(8), px(12)))
        side = tk.Frame(c.ctrl, bg=CARD, width=px(84), height=px(32))
        side.pack(side="left"); side.pack_propagate(False)
        en.bind("<Return>", lambda _e: save_profiles())
        v.trace_add("write", lambda *_, i=i: _render_row(i))
        row_dot.append(dot); row_card.append(c); row_entry.append(en); row_side.append(side)
        prof_vars.append(v)

    def _render_row(i):
        """Punto (relleno o solo contorno), descripcion y accion de una fila."""
        c, dot, side = row_card[i], row_dot[i], row_side[i]
        has = bool(profiles[i]) or bool(prof_vars[i].get().strip())
        col = PROFILE_COLORS[i]
        dot.delete("all")
        if has:
            paint(dot, "dot", 0, 0, px(10), px(10), fill=col)
        else:
            paint(dot, "dot", 0, 0, px(10), px(10), outline=col, width=max(1, px(1.5)))
        c.title.configure(text=f"{tr('profile')} {i + 1}")
        color = tr(LED_KEYS[i])
        c.set_desc(tr("prof_led_desc", color=color) if has else tr("prof_off_desc", color=color))
        for w in side.winfo_children(): w.destroy()
        if current[0] == i and profiles[i] and mouse.dev is not None:
            box = tk.Frame(side, bg=CARD); box.place(relx=1.0, rely=0.5, anchor="e")
            ic = icon_label(box, "check", 14, FG2)
            if ic: ic.pack(side="left", padx=(0, px(6)))
            tk.Label(box, text=tr("lbl_in_use"), bg=CARD, fg=FG2, font=FONT_ROW).pack(side="left")
        elif profiles[i] and ctrl_on[0]:
            b = ttk.Button(side, text=tr("btn_use"), style="Btn.TButton",
                           command=lambda i=i: on_click_profile(i))
            b.place(relx=1.0, rely=0.5, anchor="e")

    def render_profiles():
        mode_var.set(tr("mode_ctrl") if ctrl_on[0] else tr("mode_compat"))
        try: render_btn_note()
        except NameError: pass
        cur = current[0]
        if mouse.dev is None:
            state_txt = tr("prof_wait")
        elif ctrl_on[0] and not verified[0]:
            state_txt = tr("prof_verify")
        elif not ctrl_on[0] and learning[0]:
            state_txt = tr("prof_learning", n=len(_enabled()))
        elif cur is not None and profiles[cur]:
            state_txt = None
        else:
            state_txt = tr("prof_unknown", x=last_dpi[0])
        if state_txt is None:
            active_var.set(tr("prof_active", n=cur + 1, x=profiles[cur]))
            act_card.set_desc(tr("active_desc"))
            act_big.configure(text=f"{profiles[cur]} DPI")
            act_small.configure(text=tr("active_small", n=cur + 1, color=tr(LED_KEYS[cur])))
        else:
            active_var.set(state_txt)
            act_card.set_desc(state_txt)
            act_big.configure(text="\u2014"); act_small.configure(text="")
        for i in range(5):
            _render_row(i)
        update_tray_tip()
    reg(render_profiles)

    def on_click_profile(i):
        """Boton "Usar": en modo control activa ese perfil."""
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
                log(trl("err_dpi_range", n=i + 1, lo=DPI_MIN, hi=dmax)); return
            if not (DPI_MIN <= x <= dmax):
                log(trl("err_dpi_range", n=i + 1, lo=DPI_MIN, hi=dmax)); return
            new.append(x)
        if not any(new):
            log(trl("log_prof_none")); return
        vals = [x for x in new if x]
        if len(vals) != len(set(vals)):
            log(trl("log_dup_any"))
        changed_active = current[0] is not None and new[current[0]] != profiles[current[0]]
        profiles[:] = new
        if current[0] is None or not profiles[current[0]]:
            current[0] = _enabled()[0]; changed_active = True
        _save_profiles()
        log(trl("log_prof_saved"))
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
            log(trl("log_prof_reset"))
        else:
            profiles[:] = [None] * 5
            for v in prof_vars: v.set("")
            learning[0] = True; current[0] = None; last_dpi[0] = None
            _save_profiles()
            log(trl("log_relearn"))
            start_compat()
        render_profiles()

    def sync_entries():
        """Refleja en los campos lo aprendido en modo compatibilidad."""
        for i, v in enumerate(prof_vars):
            want = str(profiles[i]) if profiles[i] else ""
            if v.get() != want and root.focus_get() is not row_entry[i]:
                v.set(want)

    # --- frecuencia de sondeo (se aplica al elegir) -----------------------------
    poll_card = Card(pg_prof, icon="speed", title="poll_title", desc="poll_desc", wrap=300)
    poll_card.frame.pack_configure(pady=(px(20), px(2)))
    poll_var = tk.IntVar(value=presets.get("poll_rate", 1000))
    poll_show = tk.StringVar(value=f"{poll_var.get()} Hz")
    poll_combo = ttk.Combobox(poll_card.ctrl, textvariable=poll_show, state="readonly", width=10,
                              values=["1000 Hz", "500 Hz", "125 Hz"])
    poll_combo.pack()

    @guard
    def do_set_poll():
        code = mouse.set_poll_rate(int(poll_var.get()))
        presets["poll_rate"] = int(poll_var.get()); save_presets(presets)
        log(trl("log_poll", hz=poll_var.get(), st=st_name(code, "en")))

    def _on_poll(_e=None):
        poll_var.set(int(poll_show.get().split()[0]))
        do_set_poll()
    poll_combo.bind("<<ComboboxSelected>>", _on_poll)

    # --- acciones ------------------------------------------------------------
    pacts = tk.Frame(pg_prof, bg=BG); pacts.pack(fill="x", pady=(px(20), 0))
    reg_text(ttk.Button(pacts, style="Accent.TButton", command=save_profiles),
             "btn_save_prof").pack(side="left")
    reg_text(ttk.Button(pacts, style="Btn.TButton", command=lambda: start_wizard()),
             "btn_burn_dots").pack(side="left", padx=(px(8), 0))
    link(pacts, "link_reset", reset_profiles).pack(side="right")

    # --- asistente "Grabar en el raton" (dialogo estilo Windows 11) -------------
    # Mete tus perfiles en la MEMORIA INTERNA del raton, para que al cerrar el
    # programa el raton tenga los mismos perfiles con su LED de color. Como no se
    # puede elegir la ranura por software, se hace guiado: el raton vuelve a su
    # modo normal, el usuario pone el LED de debajo en el color que toca con el
    # boton de perfil, y el programa graba ahi el DPI (y lo comprueba leyendolo).
    def start_wizard(after=None):
        if mouse.dev is None:
            log(trl("log_burn_noconn")); return
        if wizard_active[0]:
            return
        save_profiles()                               # valida y guarda lo que haya en las casillas
        todo = _enabled()
        if not todo:
            return
        wizard_active[0] = True
        release_control(announce=False)              # el raton gestiona sus perfiles (LED activo)
        log(trl("log_burn_start"))

        win = tk.Toplevel(root); win.configure(bg=BG); win.resizable(False, False)
        win.title(tr("burn_title")); win.transient(root)
        try:
            if os.path.exists(_ico_path): win.iconbitmap(_ico_path)
        except Exception: pass
        W = px(460)
        top = tk.Frame(win, bg=CARD, width=W); top.pack(fill="x")
        topi = tk.Frame(top, bg=CARD); topi.pack(fill="x", padx=px(24), pady=px(24))
        t_title = tk.Label(topi, bg=CARD, fg=FG, font=FONT_BIG, anchor="w")
        t_title.pack(fill="x")
        t_step = tk.Label(topi, bg=CARD, fg=FG2, font=FONT_DESC, anchor="w")
        t_step.pack(fill="x", pady=(px(2), px(10)))
        prog = tk.Canvas(topi, height=px(3), bg=CARD, highlightthickness=0, width=W - px(48))
        prog.pack(fill="x", pady=(0, px(16)))
        msg = tk.Text(topi, bg=CARD, fg=FG, font=FONT_ROW, relief="flat", highlightthickness=0,
                      bd=0, wrap="word", height=3, width=42, cursor="arrow")
        msg.tag_configure("b", font=font(14, semibold=True))
        msg.pack(fill="x")
        will = tk.Frame(topi, bg=T["PANEL"], highlightthickness=1, highlightbackground=T["PANEL_BORDER"])
        will.pack(fill="x", pady=(px(14), 0))
        will_l = tk.Label(will, bg=T["PANEL"], fg=FG2, font=FONT_ROW)
        will_l.pack(side="left", padx=px(12), pady=px(10))
        will_r = tk.Label(will, bg=T["PANEL"], fg=FG, font=font(14, semibold=True))
        will_r.pack(side="right", padx=px(12), pady=px(10))
        dots = tk.Canvas(topi, height=px(14), bg=CARD, highlightthickness=0)
        # zona de confirmaciones: ALTO FIJO de una linea; cada confirmacion se
        # superpone a la anterior (la ultima queda arriba), asi la ventana no
        # crece y el boton nunca se sale de la vista
        done_box = tk.Frame(topi, bg=CARD, height=px(24)); done_box.pack(fill="x", pady=(px(10), 0))
        done_box.pack_propagate(False)
        foot = tk.Frame(win, bg=BG, highlightthickness=0); foot.pack(fill="x")
        tk.Frame(foot, bg=CARD_BORDER, height=1).pack(fill="x")
        fi = tk.Frame(foot, bg=BG); fi.pack(fill="x", padx=px(24), pady=px(20))
        fi.grid_columnconfigure(0, weight=1, uniform="b"); fi.grid_columnconfigure(1, weight=1, uniform="b")
        b_go = ttk.Button(fi, style="Accent.TButton"); b_go.grid(row=0, column=0, sticky="ew", padx=(0, px(4)))
        b_cancel = ttk.Button(fi, style="Btn.TButton", text=tr("btn_cancel"))
        b_cancel.grid(row=0, column=1, sticky="ew", padx=(px(4), 0))
        step = [0]
        done = []                                     # (indice, comprobado)

        def _draw_prog():
            prog.update_idletasks()
            w = max(prog.winfo_width(), W - px(48)); n = len(todo); gap = px(4)
            seg = (w - gap * (n - 1)) / float(n)
            prog.delete("all")
            for k in range(n):
                x = k * (seg + gap)
                prog.create_rectangle(x, 0, x + seg, px(3), outline="",
                                      fill=(ACCENT if k <= step[0] else T["PROG_OFF"]))

        def _draw_done():
            for w in done_box.winfo_children(): w.destroy()
            for (i, ok) in done:
                row = tk.Frame(done_box, bg=CARD); row.place(x=0, y=0, relwidth=1, relheight=1)
                row.lift()
                ic = icon_label(row, "check", 12, FG2)
                if ic: ic.pack(side="left", padx=(0, px(6)))
                tk.Label(row, bg=CARD, fg=FG2, font=FONT_DESC, anchor="w",
                         text=tr("burn_item", n=i + 1, color=tr(LED_KEYS[i]), x=profiles[i],
                                 state=tr("burn_checked" if ok else "burn_unchecked"))).pack(side="left")

        def show():
            msg.configure(state="normal"); msg.delete("1.0", "end")
            if step[0] >= len(todo):
                t_title.configure(text=tr("burn_done_title")); t_step.pack_forget(); prog.pack_forget()
                will.pack_forget()
                dots.pack(fill="x", pady=(px(4), px(12)), before=msg); dots.delete("all")
                for k, i in enumerate(todo):          # los colores grabados, en fila
                    x = k * px(18)
                    paint(dots, "dot", x, 0, x + px(12), px(12), fill=PROFILE_COLORS[i])
                msg.insert("end", tr("burn_done_msg"))
                msg.configure(state="disabled", height=2)
                _draw_done()
                b_cancel.grid_forget()
                b_go.configure(text=tr("btn_close"), command=finish)
                b_go.grid_configure(columnspan=2, padx=0)
                return
            i = todo[step[0]]
            t_title.configure(text=tr("burn_title"))
            t_step.configure(text=tr("burn_step2", n=step[0] + 1, total=len(todo)))
            _draw_prog()
            msg.tag_configure("dot", foreground=PROFILE_COLORS[i])
            msg.insert("end", tr("burn_msg_a"))
            msg.insert("end", "\u25CF ", "dot")
            msg.insert("end", tr(LED_KEYS[i]), "b")
            msg.insert("end", tr("burn_msg_b"))
            msg.configure(state="disabled")
            will_l.configure(text=tr("burn_will"))
            will_r.configure(text=tr("burn_will_val", x=profiles[i], n=i + 1))
            _draw_done()
            b_go.configure(text=tr("btn_burn_step"), command=burn)

        def burn():
            i = todo[step[0]]
            try:
                mouse.set_dpi(profiles[i], persist=True)      # VARSTORE: al perfil interno activo
                x, _ = mouse.get_dpi()
            except Exception as e:
                log(f"[!] {e}"); return
            ok = (x == profiles[i])
            done.append((i, ok))
            log(trl("log_burn_ok" if ok else "log_burn_check", color=trl(COLOR_KEYS[i]), x=profiles[i]))
            step[0] += 1
            show()

        def finish():
            wizard_active[0] = False
            try: win.grab_release()
            except Exception: pass
            try: win.destroy()
            except Exception: pass
            if step[0] >= len(todo):
                log(trl("log_burn_done"))
                presets["burned_profiles"] = list(profiles); save_presets(presets)
            else:
                log(trl("log_burn_cancel"))
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
        win.geometry(f"{W}x{win.winfo_reqheight()}+{root.winfo_rootx() + px(150)}+{root.winfo_rooty() + px(90)}")
        dark_titlebar(win)
        try: win.grab_set()
        except Exception: pass

    # =====================================================================
    # 7b) AJUSTES (se crea aqui: la logica del raton usa sus variables)
    # =====================================================================
    pg_set = new_page("settings")
    page_title(pg_set, "nav_settings")
    group_hdr(pg_set, "grp_mouse", first=True)
    set_mouse = stack(pg_set)

    model_card = Card(set_mouse, icon="settings", title="model_title", desc="model_desc", wrap=170)
    # el valor interno es el nombre del modelo; lo que se ve se traduce («Auto-detectar»)
    model_show = tk.StringVar()
    model_combo = ttk.Combobox(model_card.ctrl, textvariable=model_show, state="readonly", width=20)
    model_combo.pack(side="left")

    def _model_label(n):
        return tr("model_auto") if n == AUTO_NAME else n

    def _sync_model_combo():
        model_combo.configure(values=[_model_label(n) for n in model_names])
        model_show.set(_model_label(model_var.get()))
    reg(_sync_model_combo)

    def reconnect(_e=None):
        if mouse.dev is not None:
            release_control(announce=False)
            try: mouse.close()
            except Exception: pass
            state_conn[0] = None; render_status()
        connect_mouse(manual=True)
    def _on_model_sel(_e=None):
        k = model_combo.current()
        if 0 <= k < len(model_names):
            model_var.set(model_names[k])
        reconnect()
    model_combo.bind("<<ComboboxSelected>>", _on_model_sel)
    reg_text(ttk.Button(model_card.ctrl, style="Btn.TButton", command=reconnect, width=9),
             "btn_reconnect").pack(side="left", padx=(px(8), 0))

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
    c = Card(set_mouse, icon="sync", title="ctrl_title", desc="ctrl_desc")
    Toggle(c.ctrl, ctrl_var).frame.pack()

    notify_var = tk.BooleanVar(value=presets.get("notify_popup", False))
    def _save_notify(*_):
        presets["notify_popup"] = notify_var.get(); save_presets(presets)
    notify_var.trace_add("write", _save_notify)
    c = Card(set_mouse, icon="bell", title="notify_title", desc="notify_desc")
    Toggle(c.ctrl, notify_var).frame.pack()

    ask_exit_var = tk.BooleanVar(value=presets.get("ask_burn_on_exit", True))
    def _save_ask(*_):
        presets["ask_burn_on_exit"] = ask_exit_var.get(); save_presets(presets)
    ask_exit_var.trace_add("write", _save_ask)
    c = Card(set_mouse, icon="download", title="ask_exit_title", desc="ask_exit_desc")
    Toggle(c.ctrl, ask_exit_var).frame.pack()

    # --- avisos de bateria (la logica esta junto al aviso de perfil) ---------------
    group_hdr(pg_set, "grp_battery")
    set_batt = stack(pg_set)
    batt_alert_var = tk.BooleanVar(value=presets.get("batt_alert", True))
    batt_full_var = tk.BooleanVar(value=presets.get("batt_full", True))

    def _save_batt_opts(*_):
        presets["batt_alert"] = batt_alert_var.get(); presets["batt_full"] = batt_full_var.get()
        save_presets(presets)
    batt_alert_var.trace_add("write", _save_batt_opts); batt_full_var.trace_add("write", _save_batt_opts)
    c = Card(set_batt, icon="bell", title="batt_alert_title", desc="batt_alert_desc")
    reg_text(ttk.Button(c.ctrl, style="Btn.TButton", command=lambda: test_batt_popup(), width=8),
             "batt_test_btn").pack(side="left", padx=(0, px(12)))
    Toggle(c.ctrl, batt_alert_var).frame.pack(side="left")
    c = Card(set_batt, icon="power", title="batt_full_title", desc="batt_full_desc")
    Toggle(c.ctrl, batt_full_var).frame.pack()

    # --- apariencia: tema + claro/oscuro + temas propios ---------------------------
    # El tema se aplica al REINICIAR (la interfaz se monta con sus colores y
    # formas). Al cambiarlo aparece una tarjeta con "Reiniciar ahora".
    group_hdr(pg_set, "grp_appearance")
    set_look = stack(pg_set)
    c = Card(set_look, icon="color", title="theme_title", desc="theme_desc")
    theme_show = tk.StringVar()
    theme_combo = ttk.Combobox(c.ctrl, textvariable=theme_show, state="readonly", width=16)
    theme_combo.pack()
    _theme_keys = [k for k in THEMES if not THEMES[k].get("secret") or MV_UNLOCKED]
    theme_card = c
    mv_logo_card = image_frames(MV_LOGO, px(20), shaped=False)
    if MV_UNLOCKED and mv_logo_card:                   # el logo en lugar de la paleta
        if theme_card.icon is None:
            theme_card.icon = tk.Label(theme_card.inner, bg=CARD)
            theme_card.icon.grid(row=0, column=0, sticky="w", padx=(0, px(16)))
        theme_card.icon.configure(image=mv_logo_card[0][0], text="")
        theme_card.icon._img = mv_logo_card[0][0]

    def _sync_theme_combo():
        theme_combo.configure(values=[theme_label(k) for k in _theme_keys])
        k = presets.get("theme", THEME_NAME)
        theme_show.set(theme_label(k if k in THEMES else THEME_NAME))
    reg(_sync_theme_combo)

    restart_card = Card(set_look, icon="sync", title="theme_restart_title", desc="theme_restart_desc")
    reg_text(ttk.Button(restart_card.ctrl, style="Accent.TButton", command=lambda: restart_app()),
             "theme_restart_btn").pack()
    restart_card.frame.pack_forget()

    def _theme_pending():
        """Muestra 'Reiniciar ahora' si lo elegido no es lo que esta en pantalla."""
        want = (presets.get("theme", "basic"), presets.get("theme_mode", "dark"))
        if want != (THEME_NAME, THEME_MODE):
            if not restart_card.frame.winfo_ismapped():
                restart_card.frame.pack(fill="x", pady=(0, px(2)), after=dark_card.frame)
        elif restart_card.frame.winfo_ismapped():
            restart_card.frame.pack_forget()

    def _on_theme(_e=None):
        k = theme_combo.current()
        if 0 <= k < len(_theme_keys):
            presets["theme"] = _theme_keys[k]; save_presets(presets)
            _dark_avail(); _theme_pending()
    theme_combo.bind("<<ComboboxSelected>>", _on_theme)

    dark_var = tk.BooleanVar(value=(presets.get("theme_mode", THEME_MODE) != "light"))
    dark_card = Card(set_look, icon="bright", title="dark_title", desc="dark_desc")
    dark_tg = Toggle(dark_card.ctrl, dark_var); dark_tg.frame.pack()

    def _dark_avail():
        th = THEMES.get(presets.get("theme", THEME_NAME), {})
        dark_tg.set_enabled(not th.get("secret"))
    _dark_avail()

    def _on_dark(*_):
        presets["theme_mode"] = "dark" if dark_var.get() else "light"; save_presets(presets)
        _theme_pending()
    dark_var.trace_add("write", _on_dark)

    THEME_TEMPLATE_NOTE = (
        "Non-Synapse-Mouse theme template. Files starting with '_' are ignored: copy this file, "
        "rename it (e.g. neon.json), edit it and restart the app. Only what you write is changed; "
        "the rest comes from 'base'. Colors: #RRGGBB. shape.style: round | square | chamfer | diamond. "
        "shape.corner: size of rounded/cut corners (px). shape.border: outline width (px). "
        "shape.glow: neon halo around active parts. font: optional, must be installed in Windows.")

    def write_theme_files():
        """Crea la carpeta de temas con una plantilla completa y un ejemplo."""
        os.makedirs(THEMES_DIR, exist_ok=True)
        base = BUILTIN_THEMES["basic"]
        tpl = {"_readme": THEME_TEMPLATE_NOTE,
               "_colors": THEME_COLOR_KEYS,
               "name": "My theme", "base": "basic",
               "shape": dict(base["shape"]),
               "dark": dict(base["dark"]), "light": dict(base["light"])}
        neon = {"_readme": "Example. Rename to neon.json (without the '_') to try it.",
                "name": "Neon", "base": "basic",
                "shape": {"style": "chamfer", "corner": 7, "border": 1, "glow": True},
                "dark": {"BG": "#0B0B10", "CARD": "#14141C", "CARD_BORDER": "#26263A",
                         "CTRL": "#1B1B26", "CTRL_HOVER": "#232333", "CTRL_BORDER": "#2E2E44",
                         "FG": "#F2F2F2", "FG2": "#8DE9F0", "FG3": "#6B6B85",
                         "ACCENT": "#FCEE0A", "ACCENT_HOVER": "#E5D800", "ON_ACCENT": "#000000",
                         "LOG_BG": "#08080C", "LOG_BORDER": "#26263A", "SEG_OFF": "#2A2A3C",
                         "SWITCH_OFF": "#00E5FF", "KNOB_OFF": "#00E5FF", "SLIDER_TRACK": "#3A3A55",
                         "PANEL": "#101018", "PANEL_BORDER": "#26263A", "PROG_OFF": "#2A2A3C",
                         "POPUP_BORDER": "#FCEE0A", "SELECT_BG": "#2E2E44", "LINK": "#FCEE0A"}}
        for fn, data in (("_template.json", tpl), ("_example-neon.json", neon)):
            path = os.path.join(THEMES_DIR, fn)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def open_themes_folder():
        try:
            write_theme_files()
            if sys.platform == "win32":
                os.startfile(THEMES_DIR)                 # noqa (solo Windows)
            else:
                webbrowser.open("file://" + THEMES_DIR)
            log(trl("log_themes_folder", path=THEMES_DIR))
        except Exception as e:
            log(f"[!] {e}")

    c = Card(set_look, icon="code", title="themes_custom_title", desc="themes_custom_desc")
    reg_text(ttk.Button(c.ctrl, style="Btn.TButton", command=open_themes_folder),
             "themes_custom_btn").pack()

    # =====================================================================
    # 7c) BOTONES (remapeo)
    # =====================================================================
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
    PRESET_ACTIONS = (["default", "none", "next", "prev", "sniper", "p1", "p2", "p3", "p4", "p5",
                       "click_left", "click_right", "click_middle", "click_back", "click_forward",
                       "dblclick", "key:ctrl+c", "key:ctrl+v", "key:ctrl+x", "key:ctrl+z",
                       "key:ctrl+y", "key:enter", "key:esc", "key:tab", "key:space",
                       "key:alt+tab", "key:win+d", "key:printscreen", "key:media_play",
                       "key:media_next", "key:media_prev", "key:vol_up", "key:vol_down",
                       "key:vol_mute"])
    ACTION_KEYS = {"default": "act_default", "none": "act_none", "next": "act_next", "prev": "act_prev",
                   "sniper": "act_sniper",
                   "click_left": "act_lclick", "click_right": "act_rclick", "click_middle": "act_mclick",
                   "click_back": "act_back", "click_forward": "act_forward", "dblclick": "act_dbl",
                   "key:ctrl+c": "act_copy", "key:ctrl+v": "act_paste", "key:ctrl+x": "act_cut",
                   "key:ctrl+z": "act_undo", "key:ctrl+y": "act_redo", "key:enter": "act_enter",
                   "key:esc": "act_esc", "key:tab": "act_tab", "key:space": "act_space",
                   "key:alt+tab": "act_alttab", "key:win+d": "act_desktop",
                   "key:printscreen": "act_prtsc", "key:media_play": "act_play",
                   "key:media_next": "act_nexttrk", "key:media_prev": "act_prevtrk",
                   "key:vol_up": "act_volup", "key:vol_down": "act_voldn", "key:vol_mute": "act_mute"}
    NO_RELEASE_BTNS = {"wheel_up", "wheel_down", "tilt_l", "tilt_r"}    # sin evento de "soltar"
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

    # ---- sniper: DPI bajo mientras se mantiene un boton -----------------------------
    # Se puede asignar a cualquier boton con evento de "soltar" (laterales, central,
    # y los que avisa el raton). Al pulsar baja al DPI del sniper; al soltar vuelve
    # al del perfil activo. Las ordenes pasan por una cola a un hilo propio para
    # respetar el orden y no bloquear ni el gancho de Windows ni la interfaz.
    sniper_dpi = [int(presets.get("sniper_dpi", 400))]
    sniper_state = {"active": False, "prev": None}
    sniper_q = queue.Queue()

    def _sniper_worker():
        while True:
            job = sniper_q.get()
            if job is None:
                return
            try:
                if job and not sniper_state["active"]:
                    if mouse.dev is None:
                        continue
                    cur = current[0]
                    prev = profiles[cur] if (cur is not None and profiles[cur]) else last_dpi[0]
                    dmax = (active_model[0] or current_model())["dpi_max"]
                    x = max(DPI_MIN, min(dmax, sniper_dpi[0]))
                    sniper_state["active"] = True; sniper_state["prev"] = prev
                    set_dpi_async(x)
                    uiq.put(lambda x=x: log(trl("log_sniper_on", x=x)))
                elif (not job) and sniper_state["active"]:
                    prev = sniper_state["prev"]
                    sniper_state["active"] = False
                    if prev and mouse.dev is not None:
                        set_dpi_async(prev); last_dpi[0] = prev
                        uiq.put(lambda x=prev: log(trl("log_sniper_off", x=x)))
            except Exception as e:
                sniper_state["active"] = False
                uiq.put(lambda e=e: log(f"[ERROR] {e}"))

    def _rep4_action(code):
        a = button_map.get(code, "default")
        return DEFAULT_BTN_MAP.get(code, "none") if a == "default" else a

    last_prof_act = [0.0]

    def exec_action(a, down, has_up, debounce=True):
        """Ejecuta una accion. down/has_up permiten mantener pulsado (teclas y
        clics se sueltan cuando se suelta el boton original). debounce: un giro
        de rueda manda varias senales seguidas y solo debe cambiar UN perfil;
        los botones del raton (Report 4) llegan limpios y no lo necesitan."""
        if a in ("none", "default"):
            return
        if a == "sniper":
            if has_up:                                     # la rueda no tiene "soltar"
                sniper_q.put(bool(down))
            return
        if a in ("next", "prev") or (a.startswith("p") and a[1:].isdigit()):
            now = time.time()
            if down and (not debounce or now - last_prof_act[0] >= 0.25):   # un giro de rueda = un solo cambio
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
        a = _rep4_action(code)
        if a == "sniper":
            sniper_q.put(True)                             # se suelta en on_button_release
            return
        exec_action(a, True, False, debounce=False)    # pulsaciones rapidas: ninguna se pierde

    # --- gancho de Windows ---
    remapper = SoftRemapper(get_action=lambda b: soft_map.get(b, "default"),
                            on_ui=lambda b: uiq.put(lambda b=b: on_soft_seen(b)),
                            do_action=exec_action)
    SOFT_OK = SoftRemapper.supported()

    pg_btn = new_page("buttons")
    page_title(pg_btn, "nav_buttons")
    soft_var = tk.BooleanVar(value=bool(presets.get("soft_remap", False)) and SOFT_OK)
    soft_card = Card(pg_btn, icon="warn", title="soft_title",
                     desc=("soft_desc" if SOFT_OK else "soft_desc_na"), min_h=64, wrap=300)
    soft_card.frame.pack_configure(pady=(px(8), px(2)))
    soft_toggle = Toggle(soft_card.ctrl, soft_var, enabled=SOFT_OK)
    soft_toggle.frame.pack()

    def _toggle_soft(*_):
        presets["soft_remap"] = soft_var.get(); save_presets(presets)
        if soft_var.get():
            if remapper.start():
                log(trl("log_soft_on"))
            else:
                log(trl("log_soft_fail")); soft_var.set(False)
        else:
            remapper.stop(); log(trl("log_soft_off"))
        build_btn_rows()
    soft_var.trace_add("write", _toggle_soft)

    group_hdr(pg_btn, "grp_sniper")
    sn_card = Card(pg_btn, icon="speed", title="sniper_title", desc="sniper_desc")
    sn_var = tk.StringVar(value=str(sniper_dpi[0]))
    sn_box, sn_en = text_box(sn_card.ctrl, sn_var, 96, justify="right")
    sn_box.pack(side="left")
    tk.Label(sn_card.ctrl, text="DPI", bg=CARD, fg=FG2, font=FONT_ROW).pack(side="left", padx=(px(8), 0))

    def save_sniper(_e=None):
        dmax = (active_model[0] or current_model())["dpi_max"]
        try:
            x = int(sn_var.get().strip())
        except ValueError:
            x = 0
        if not (DPI_MIN <= x <= dmax):
            log(trl("err_sniper", lo=DPI_MIN, hi=dmax)); sn_var.set(str(sniper_dpi[0])); return
        sniper_dpi[0] = x; presets["sniper_dpi"] = x; save_presets(presets)
    sn_en.bind("<Return>", save_sniper); sn_en.bind("<FocusOut>", save_sniper)

    win_hdr, _wn = group_hdr(pg_btn, "grp_win_btns")
    win_note_lbl = tk.Label(win_hdr, bg=BG, fg=FG3, font=FONT_DESC)
    win_rows = stack(pg_btn)
    _, mouse_note = group_hdr(pg_btn, "grp_mouse_btns", note_key="grp_mouse_note")
    btn_note = tk.Label(pg_btn, bg=BG, fg=FG2, font=FONT_DESC, anchor="w", justify="left",
                        wraplength=px(540))
    autowrap(btn_note, pg_btn, 8, lo=240, hi=900)
    mouse_rows = stack(pg_btn)
    btn_flash = {}

    _btn_ctrl_seen = [None]

    def _render_sniper_dim():
        """El sniper solo sirve si hay donde asignarlo: remapeo o modo control."""
        dim = not (soft_var.get() or ctrl_on[0])
        sn_card.title.configure(fg=(FG3 if dim else FG))
        sn_en.configure(state=("disabled" if dim else "normal"), disabledbackground=CTRL,
                        disabledforeground=FG3)

    def render_btn_note():
        if _btn_ctrl_seen[0] is not None and _btn_ctrl_seen[0] != ctrl_on[0]:
            _btn_ctrl_seen[0] = ctrl_on[0]
            build_btn_rows()                       # cambia el modo: las filas se (des)activan
            return
        _btn_ctrl_seen[0] = ctrl_on[0]
        _render_sniper_dim()
        if SOFT_OK and not soft_var.get():
            win_note_lbl.configure(text=tr("btn_disabled_note"))
            win_note_lbl.pack(side="left", padx=(px(10), 0))
        else:
            win_note_lbl.pack_forget()
        if ctrl_on[0]:
            btn_note.pack_forget()
        else:
            btn_note.configure(text=tr("btn_compat"))
            btn_note.pack(fill="x", pady=(0, px(8)), before=mouse_rows)

    def _row(parent, key, name, cur, is_soft, store):
        # en gris e inseleccionable si esa familia de botones esta apagada:
        # los de Windows dependen del remapeo; los del raton, del modo control
        dim = (not soft_var.get()) if is_soft else (not ctrl_on[0])
        c = Card(parent, min_h=42)
        c.title.configure(text=name, fg=(FG3 if dim else FG))
        ind = tk.Frame(c.ctrl, bg=CARD)
        ind.pack(side="left", padx=(0, px(10)))
        acts = [a for a in PRESET_ACTIONS if not (a == "sniper" and key in NO_RELEASE_BTNS)]
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
        cb = ttk.Combobox(c.ctrl, state="readonly", width=27, values=labels, height=16)
        cb.current(acts.index(cur) if cur in acts else 0)
        cb.pack(side="left")
        if dim:
            cb.configure(state="disabled")

        def on_sel(_e, key=key, cb=cb, acts=acts, name=name, labels=labels):
            a = acts[cb.current()]
            if a == "custom":
                from tkinter import simpledialog
                txt = simpledialog.askstring(tr("custom_title"), tr("custom_prompt"), parent=root)
                if not txt or parse_combo(txt) is None:
                    if txt:
                        log(trl("log_custom_bad", keys=txt))
                    build_btn_rows(); return
                a = "key:" + "+".join(p.strip().lower() for p in txt.replace("-", "+").split("+") if p.strip())
            store[key] = a
            if is_soft:
                presets["soft_map"] = dict(soft_map)
            else:
                presets["button_map"] = {str(k): v for k, v in button_map.items()}
            save_presets(presets)
            log(trl("log_btn_set", name=name, act=(labels[acts.index(a)] if a in acts else act_label(a))))
            build_btn_rows()
        cb.bind("<<ComboboxSelected>>", on_sel)
        btn_flash[key] = ind

    def build_btn_rows():
        for box in (win_rows, mouse_rows):
            for w in box.winfo_children():
                w.destroy()
        btn_flash.clear()
        for b in SOFT_BUTTONS:
            if b in SOFT_ONLY_IF_SEEN and b not in soft_seen:
                continue
            _row(win_rows, b, tr(SOFT_NAME_KEYS[b]), soft_map.get(b, "default"), True, soft_map)
        for code in buttons_seen:
            _row(mouse_rows, code, btn_name(code), button_map.get(code, "default"), False, button_map)
        render_btn_note()
    reg(build_btn_rows)

    def on_soft_seen(b):
        if b in SOFT_ONLY_IF_SEEN and b not in soft_seen:
            soft_seen.add(b)
            presets["soft_seen"] = sorted(soft_seen); save_presets(presets)
            build_btn_rows()
        flash_btn(b)

    def flash_btn(key):
        """Indicador de pulsacion: punto verde + "Pulsado" durante ~600 ms."""
        ind = btn_flash.get(key)
        if ind is None or not ind.winfo_exists(): return
        for w in ind.winfo_children(): w.destroy()
        d = tk.Canvas(ind, width=px(6), height=px(6), bg=CARD, highlightthickness=0)
        paint(d, "dot", 0, 0, px(6), px(6), fill=ACCENT)
        d.pack(side="left", padx=(0, px(6)))
        tk.Label(ind, text=tr("pressed"), bg=CARD, fg=FG2, font=FONT_DESC).pack(side="left")
        def clear():
            if ind.winfo_exists():
                for w in ind.winfo_children(): w.destroy()
        root.after(600, clear)

    render_btn_note()

    if soft_var.get():
        root.after(500, lambda: (remapper.start() and log(trl("log_soft_on"))) or None)

    # ---- Aviso de cambio de perfil (tarjeta gris de Windows) --------------------
    toast_win = [None]
    toast_after = [None]

    def show_toast(i):
        x_dpi = profiles[i] or last_dpi[0]
        tw = toast_win[0]
        if tw is None or not tw.winfo_exists():
            tw = tk.Toplevel(root)
            tw.overrideredirect(True)           # sin bordes
            tw.attributes("-topmost", True)     # siempre encima (sin transparencia)
            tw.configure(bg=T["POPUP_BORDER"])
            card = tk.Frame(tw, bg=CARD, width=px(320)); card.pack(padx=1, pady=1)
            hdr = tk.Frame(card, bg=CARD); hdr.pack(fill="x", padx=px(16), pady=(px(12), 0))
            hcv = tk.Canvas(hdr, width=px(14), height=px(14), bg=CARD, highlightthickness=0)
            hcv.pack(side="left"); draw_mouse(hcv, px(7), px(7), px(14), FG2)
            tk.Label(hdr, text=APP_NAME, bg=CARD, fg=FG2, font=FONT_DESC).pack(side="left", padx=(px(8), 0))
            b_pct = tk.Label(hdr, bg=CARD, fg=FG2, font=FONT_DESC)      # bateria, arriba a la derecha
            b_pct.pack(side="right")
            b_ic = tk.Label(hdr, bg=CARD, fg=FG2, font=(icon_font(12) or FONT_DESC))
            b_ic.pack(side="right", padx=(0, px(4)))
            body = tk.Frame(card, bg=CARD); body.pack(fill="x", padx=px(16), pady=(px(12), px(14)))
            circ = tk.Canvas(body, width=px(32), height=px(24), bg=CARD, highlightthickness=0)
            circ.pack(side="left", padx=(0, px(10)))
            txt = tk.Frame(body, bg=CARD); txt.pack(side="left")
            l1 = tk.Frame(txt, bg=CARD); l1.pack(anchor="w")
            big = tk.Label(l1, bg=CARD, fg=FG, font=FONT_BIG); big.pack(side="left")
            tk.Label(l1, text=" DPI", bg=CARD, fg=FG2, font=font(13)).pack(side="left", anchor="s", pady=(0, px(2)))
            sub = tk.Label(txt, bg=CARD, fg=FG2, font=FONT_DESC); sub.pack(anchor="w")
            bar = tk.Canvas(card, height=px(4), width=px(320), bg=CARD, highlightthickness=0)
            bar.pack(fill="x")
            tw._parts = (circ, big, sub, bar, b_ic, b_pct); toast_win[0] = tw
            tw.update_idletasks(); round_corners(tw)
        circ, big, sub, bar, b_ic, b_pct = tw._parts
        if batt_supported[0] and state_batt[0] is not None:
            pct, chg = state_batt[0]
            b_pct.configure(text=f"{pct} %")
            b_ic.configure(text=(batt_glyph(pct, chg) if F_ICON else ""),
                           fg=(LOW_BATT if (pct < 20 and not chg) else FG2))
        else:
            b_pct.configure(text=""); b_ic.configure(text="")
        col = PROFILE_COLORS[i]
        circ.delete("all"); paint(circ, "dot", px(4), 0, px(28), px(24), fill=col)
        big.configure(text=str(x_dpi))
        sub.configure(text=tr("toast_led", n=i + 1, color=tr(LED_KEYS[i])))
        bar.delete("all")
        W, gap = px(320), px(2); seg = (W - 4 * gap) / 5.0
        for k in range(5):
            x0 = k * (seg + gap)
            bar.create_rectangle(x0, 0, x0 + seg, px(4), outline="", fill=(col if k <= i else SEG_OFF))
        tw.update_idletasks()
        w, h = tw.winfo_reqwidth(), tw.winfo_reqheight()
        sw, sh = tw.winfo_screenwidth(), tw.winfo_screenheight()
        tw.geometry(f"+{sw - w - 28}+{sh - h - 70}")   # esquina inferior derecha
        tw.deiconify(); tw.lift()
        if toast_after[0]:
            try: root.after_cancel(toast_after[0])
            except Exception: pass
        toast_after[0] = root.after(2000, lambda: tw.winfo_exists() and tw.withdraw())

    # ---- Avisos de bateria -------------------------------------------------------
    # Ventana aparte, ARRIBA a la derecha (el aviso de perfil va abajo). Sale al
    # cruzar 90, 80 ... 10, 8 ... 1 %, al llegar a 100 % cargando y siempre una vez
    # al abrir el programa. La decision esta en battery_alert_step (funcion pura).
    batt_win = [None]
    batt_after = [None]
    batt_alerted = set()
    batt_first = [True]
    batt_full_done = [False]

    def draw_battery(cv, x, y, w, h, pct, color, chg):
        """Icono de bateria dibujado a mano: contorno, relleno por nivel y rayo si carga."""
        nub = max(2, px(3))
        body_w = w - nub
        paint(cv, "box", x, y, x + body_w, y + h, outline=FG2, width=max(1, px(1.5)), r=px(4))
        paint(cv, "box", x + body_w + 1, y + h * 0.3, x + w, y + h * 0.7, fill=FG2, r=px(1))
        pad = px(3.5)
        full_w = body_w - 2 * pad
        fw = int(full_w * max(0, min(100, pct)) / 100.0)
        if pct > 0:
            fw = max(px(2), fw)
            paint(cv, "box", x + pad, y + pad, x + pad + fw, y + h - pad, fill=color, r=px(2))
        if chg:                                           # rayo
            cx, cy = x + body_w / 2.0, y + h / 2.0
            u = h / 10.0
            bolt = [(0.6, -3.6), (-1.8, 0.4), (-0.1, 0.4), (-0.6, 3.6), (1.8, -0.5), (0.1, -0.5)]
            paint_poly(cv, [(cx + bx * u * 1.3, cy + by * u * 1.3) for (bx, by) in bolt], CARD)   # contorno
            paint_poly(cv, [(cx + bx * u, cy + by * u) for (bx, by) in bolt], FG)

    def _hide_batt_popup(_e=None):
        tw = batt_win[0]
        if batt_after[0] is not None:
            try: root.after_cancel(batt_after[0])
            except Exception: pass
            batt_after[0] = None
        if tw is not None and tw.winfo_exists():
            tw.withdraw()

    def show_batt_popup(pct, chg, kind):
        """kind: 'open' | 'low' | 'full'."""
        tw = batt_win[0]
        if tw is None or not tw.winfo_exists():
            tw = tk.Toplevel(root)
            tw.overrideredirect(True)
            tw.attributes("-topmost", True)
            tw.configure(bg=T["POPUP_BORDER"])
            card = tk.Frame(tw, bg=CARD); card.pack(padx=1, pady=1)
            hdr = tk.Frame(card, bg=CARD); hdr.pack(fill="x", padx=px(16), pady=(px(12), 0))
            hcv = tk.Canvas(hdr, width=px(14), height=px(14), bg=CARD, highlightthickness=0)
            hcv.pack(side="left"); draw_mouse(hcv, px(7), px(7), px(14), FG2)
            tk.Label(hdr, text=APP_NAME, bg=CARD, fg=FG2, font=FONT_DESC).pack(side="left", padx=(px(8), 0))
            body = tk.Frame(card, bg=CARD); body.pack(fill="x", padx=px(16), pady=(px(12), px(14)))
            bcv = tk.Canvas(body, width=px(60), height=px(30), bg=CARD, highlightthickness=0)
            bcv.pack(side="left", padx=(0, px(14)))
            txt = tk.Frame(body, bg=CARD); txt.pack(side="left", fill="x", expand=True)
            big = tk.Label(txt, bg=CARD, fg=FG, font=FONT_BIG, anchor="w"); big.pack(anchor="w")
            sub = tk.Label(txt, bg=CARD, fg=FG2, font=FONT_ROW, anchor="w", justify="left",
                           wraplength=px(205)); sub.pack(anchor="w")
            note = tk.Label(txt, bg=CARD, fg=FG3, font=FONT_DESC, anchor="w", justify="left",
                            wraplength=px(205)); note.pack(anchor="w")
            bar = tk.Canvas(card, height=px(4), width=px(320), bg=CARD, highlightthickness=0)
            bar.pack(fill="x")
            for w_ in (tw, card, hdr, hcv, body, bcv, txt, big, sub, note, bar):
                w_.bind("<Button-1>", _hide_batt_popup)
            tw._parts = (bcv, big, sub, note, bar); batt_win[0] = tw
            tw.update_idletasks(); round_corners(tw)
        bcv, big, sub, note, bar = tw._parts
        if kind == "full":
            col, s1, s2 = ACCENT, tr("ba_full"), tr("ba_full_sub")
        else:
            col = ACCENT if pct > 20 else (WARN_BATT if pct > 10 else LOW_BATT)
            if chg:
                col = ACCENT
            s1 = tr("ba_level") if (pct > 20 or chg) else (tr("ba_low") if pct > 10 else tr("ba_crit"))
            s2 = tr("ba_charging") if chg else ""
        big.configure(text=f"{pct} %", fg=(FG if (chg or pct > 10) else LOW_BATT))
        sub.configure(text=s1); note.configure(text=s2)
        if s2:
            note.pack(anchor="w")
        else:
            note.pack_forget()
        bcv.delete("all"); draw_battery(bcv, px(2), px(3), px(54), px(24), pct, col, chg)
        bar.delete("all")
        W = px(320)
        bar.create_rectangle(0, 0, W, px(4), outline="", fill=SEG_OFF)
        bar.create_rectangle(0, 0, int(W * max(0, min(100, pct)) / 100.0), px(4), outline="", fill=col)
        tw.update_idletasks()
        w, h = tw.winfo_reqwidth(), tw.winfo_reqheight()
        sw = tw.winfo_screenwidth()
        tw.geometry(f"+{sw - w - 28}+{px(48)}")           # esquina superior derecha
        tw.deiconify(); tw.lift()
        if batt_after[0] is not None:
            try: root.after_cancel(batt_after[0])
            except Exception: pass
        batt_after[0] = root.after(9000 if (pct <= 20 and not chg) else 6000, _hide_batt_popup)

    def evaluate_battery(pct, chg):
        """Se llama tras cada lectura de bateria y decide si hay que avisar."""
        if not batt_supported[0]:
            return
        first = batt_first[0]; batt_first[0] = False
        kind, new = battery_alert_step(pct, chg, batt_alerted, first)
        batt_alerted.clear(); batt_alerted.update(new)
        if kind == "open" and RESTARTED:            # reinicio para el tema: no repetir el aviso
            kind = None
        full, batt_full_done[0] = battery_full_step(pct, chg, batt_full_done[0])
        if full and batt_full_var.get():
            show_batt_popup(pct, chg, "full"); return
        if kind and batt_alert_var.get():
            if kind == "low":
                log(trl("log_batt_alert", pct=pct))
            show_batt_popup(pct, chg, "low" if kind == "low" else "open")

    def test_batt_popup():
        if batt_supported[0] and state_batt[0] is not None:
            pct, chg = state_batt[0]
        else:
            pct, chg = 42, False
        show_batt_popup(pct, chg, "open")

    # al salir del programa (aunque sea por un error), devolver el raton a su
    # modo normal para no dejar su boton de perfil "muerto"
    import atexit
    atexit.register(lambda: release_control(announce=False))

    # =====================================================================
    # 8) ILUMINACION (todo se aplica al momento: sin botones "Aplicar")
    # =====================================================================
    pg_led = new_page("lighting")
    page_title(pg_led, "nav_lighting")
    led_color = [list(presets.get("led_color", [0, 255, 0]))]
    led_on = [bool(presets.get("led_on", True))]
    led_var = tk.BooleanVar(value=led_on[0])         # interruptor <-> led_on

    def _hex(rgb):
        return "#%02x%02x%02x" % (rgb[0] & 0xFF, rgb[1] & 0xFF, rgb[2] & 0xFF)

    c = Card(pg_led, icon="power", title="led_title", desc="led_desc")
    c.frame.pack_configure(pady=(px(8), px(2)))
    Toggle(c.ctrl, led_var).frame.pack()

    group_hdr(pg_led, "color_hdr")
    col_stack = stack(pg_led)
    c = Card(col_stack, icon="color", title="color_cur", desc="color_cur_desc", wrap=320)
    swatch = tk.Canvas(c.ctrl, width=px(32), height=px(32), bg=CARD, highlightthickness=0,
                       cursor="hand2")
    swatch.pack(side="left", padx=(0, px(10)))
    hex_var = tk.StringVar(value=_hex(led_color[0]))
    hex_lbl = tk.Label(c.ctrl, textvariable=hex_var, bg=CARD, fg=FG2, font=FONT_LOG, width=8, anchor="w")
    hex_lbl.pack(side="left", padx=(0, px(10)))
    pick_btn = ttk.Button(c.ctrl, style="Btn.TButton", command=lambda: open_color_picker())
    reg_text(pick_btn, "color_pick_btn").pack(side="left")
    swatch.bind("<Button-1>", lambda _e: open_color_picker())

    def _draw_swatch():
        swatch.delete("all")
        paint(swatch, "box", 0, 0, px(32), px(32), fill=_hex(led_color[0]), outline=T["SWATCH_BORDER"],
              width=1, r=px(4))

    def render_onoff():
        if led_var.get() != led_on[0]:
            led_var.set(led_on[0])

    @guard
    def apply_color(rgb=None):
        if rgb is None:                          # color escrito a mano (#RRGGBB)
            t = hex_var.get().strip().lstrip("#")
            if len(t) != 6:
                raise ValueError(tr("err_hex"))
            rgb = [int(t[0:2], 16), int(t[2:4], 16), int(t[4:6], 16)]
        led_color[0] = list(rgb); led_on[0] = True
        hex_var.set(_hex(rgb)); _draw_swatch(); _draw_palette()
        presets["led_color"] = list(rgb); presets["led_on"] = True; save_presets(presets)
        mouse.set_color(*rgb)
        render_onoff()
        log(trl("log_color", hex=_hex(rgb)))

    # --- selector de color: disco (tono + saturacion) y barra de brillo ---------
    # El disco es siempre un circulo (es una rueda de color, no una pieza del
    # tema). Se dibuja una vez con Pillow en modo HSV y se guarda en cache.
    import colorsys

    def _disc_photo(D):
        key = ("disc", D)
        hit = _paint_cache.get(key)
        if hit is not None:
            return hit
        if not PAINT_OK:
            return None
        import io
        N = D * 2                                          # supermuestreo del borde
        hue = _PImage.new("L", (N, N), 0)
        dh = _PDraw.Draw(hue)
        for a in range(360):                               # angulo en sentido horario = tono
            dh.pieslice((0, 0, N - 1, N - 1), a, a + 1.6, fill=int(a / 360.0 * 255))
        sat = _PImage.radial_gradient("L").point(lambda v: min(255, int(v * 181 / 128.0))).resize((N, N))
        val = _PImage.new("L", (N, N), 255)
        img = _PImage.merge("HSV", (hue, sat, val)).convert("RGBA")
        m = _PImage.new("L", (N, N), 0)
        _PDraw.Draw(m).ellipse((0, 0, N - 1, N - 1), fill=255)
        img.putalpha(m)
        img = img.resize((D, D), _PImage.LANCZOS)
        buf = io.BytesIO(); img.save(buf, "PNG")
        ph = tk.PhotoImage(data=base64.b64encode(buf.getvalue()).decode("ascii"))
        _paint_cache[key] = ph
        return ph

    def _bar_photo(W, H, h, s_):
        """Barra de brillo: de negro al color elegido (tono h, saturacion s_)."""
        key = ("vbar", W, H, round(h, 3), round(s_, 3), SHAPE.get("style"))
        hit = _paint_cache.get(key)
        if hit is not None:
            return hit
        if not PAINT_OK:
            return None
        import io
        row = _PImage.new("RGB", (256, 1))
        row.putdata([tuple(int(c_ * 255) for c_ in colorsys.hsv_to_rgb(h, s_, v / 255.0)) for v in range(256)])
        img = row.resize((W, H)).convert("RGBA")
        img.putalpha(_mask("pill", W, H, 0, 0, W, H, 0).resize((W, H), _PImage.LANCZOS))
        buf = io.BytesIO(); img.save(buf, "PNG")
        ph = tk.PhotoImage(data=base64.b64encode(buf.getvalue()).decode("ascii"))
        for k_ in [k_ for k_ in _paint_cache if isinstance(k_, tuple) and k_ and k_[0] == "vbar"]:
            del _paint_cache[k_]                       # solo hace falta la barra del color actual
        _paint_cache[key] = ph
        return ph

    picker_win = [None]

    def open_color_picker():
        """Ventana para elegir el color del LED: disco + brillo + codigo hex
        (editable en los dos sentidos). 'Aplicar' lo manda al raton."""
        if picker_win[0] is not None and picker_win[0].winfo_exists():
            picker_win[0].lift(); return
        r0, g0, b0 = led_color[0]
        hsv = list(colorsys.rgb_to_hsv(r0 / 255.0, g0 / 255.0, b0 / 255.0))   # [h, s, v] 0..1
        win = tk.Toplevel(root); win.configure(bg=BG); win.resizable(False, False)
        win.title(tr("picker_title")); win.transient(root)
        picker_win[0] = win
        try:
            if os.path.exists(_ico_path): win.iconbitmap(_ico_path)
        except Exception: pass
        D, BW, BH = px(220), px(220), px(14)
        DP = px(9)                                         # margen para que el marcador no se corte
        top = tk.Frame(win, bg=CARD); top.pack(fill="x")
        ti = tk.Frame(top, bg=CARD); ti.pack(fill="x", padx=px(24), pady=px(22))
        tk.Label(ti, text=tr("picker_title"), bg=CARD, fg=FG, font=FONT_BIG, anchor="w").pack(fill="x")
        body = tk.Frame(ti, bg=CARD); body.pack(fill="x", pady=(px(16), 0))
        left = tk.Frame(body, bg=CARD); left.pack(side="left", anchor="n")
        disc = tk.Canvas(left, width=D + 2 * DP, height=D + 2 * DP, bg=CARD, highlightthickness=0,
                         cursor="crosshair")
        disc.pack()
        tk.Label(left, text=tr("picker_bright"), bg=CARD, fg=FG2, font=FONT_DESC, anchor="w").pack(
            fill="x", pady=(px(14), px(4)))
        bar = tk.Canvas(left, width=BW, height=BH + px(8), bg=CARD, highlightthickness=0, cursor="hand2")
        bar.pack(padx=DP)
        right = tk.Frame(body, bg=CARD); right.pack(side="left", anchor="n", padx=(px(24), 0), fill="y")
        prev = tk.Canvas(right, width=px(120), height=px(64), bg=CARD, highlightthickness=0)
        prev.pack(anchor="w")
        lab = tk.Frame(right, bg=CARD); lab.pack(fill="x", pady=(px(4), 0))
        tk.Label(lab, text=tr("picker_new"), bg=CARD, fg=FG2, font=FONT_DESC).pack(side="left")
        tk.Label(lab, text=tr("picker_cur"), bg=CARD, fg=FG3, font=FONT_DESC).pack(side="right")
        tk.Label(right, text="Hex", bg=CARD, fg=FG2, font=FONT_DESC, anchor="w").pack(
            fill="x", pady=(px(18), px(4)))
        pk_hex = tk.StringVar(value=_hex(led_color[0]))
        hb, he = text_box(right, pk_hex, 120)
        hb.pack(anchor="w")
        note = tk.Label(right, text=tr("picker_note"), bg=CARD, fg=FG3, font=FONT_DESC,
                        justify="left", anchor="w", wraplength=px(150))
        note.pack(fill="x", pady=(px(14), 0))
        foot = tk.Frame(win, bg=BG); foot.pack(fill="x")
        tk.Frame(foot, bg=CARD_BORDER, height=1).pack(fill="x")
        fi = tk.Frame(foot, bg=BG); fi.pack(fill="x", padx=px(24), pady=px(18))
        fi.grid_columnconfigure(0, weight=1, uniform="b"); fi.grid_columnconfigure(1, weight=1, uniform="b")
        busy = [False]

        def cur_rgb():
            return [int(round(c_ * 255)) for c_ in colorsys.hsv_to_rgb(*hsv)]

        def redraw(sync_hex=True):
            disc.delete("all")
            ph = _disc_photo(D)
            if ph is not None:
                disc.create_image(DP, DP, image=ph, anchor="nw")
            else:
                disc.create_oval(DP, DP, DP + D - 1, DP + D - 1, fill=CTRL, outline=CTRL_BORDER)
            R = D / 2.0
            a = math.radians(hsv[0] * 360.0)
            mx = DP + R + hsv[1] * (R - px(2)) * math.cos(a)
            my = DP + R + hsv[1] * (R - px(2)) * math.sin(a)
            k = px(7)
            paint(disc, "dot", mx - k - 1, my - k - 1, mx + k + 1, my + k + 1, outline="#000000", width=1)
            paint(disc, "dot", mx - k, my - k, mx + k, my + k, outline="#FFFFFF", width=max(2, px(2)))
            bar.delete("all")
            y0 = px(4)
            bp = _bar_photo(BW, BH, hsv[0], hsv[1])
            if bp is not None:
                bar.create_image(0, y0, image=bp, anchor="nw")
            else:
                bar.create_rectangle(0, y0, BW, y0 + BH, fill=_hex(cur_rgb()), outline="")
            kx = px(7) + hsv[2] * (BW - px(14))
            kr = px(9)
            paint(bar, "dot", kx - kr, y0 + BH / 2.0 - kr, kx + kr, y0 + BH / 2.0 + kr,
                  fill=_hex(cur_rgb()), outline="#FFFFFF", width=max(2, px(2)))
            prev.delete("all")
            half = px(60)
            paint(prev, "box", 0, 0, half, px(64), fill=_hex(cur_rgb()), r=px(4))
            paint(prev, "box", half, 0, px(120), px(64), fill=_hex(led_color[0]), r=px(4))
            if sync_hex:
                busy[0] = True; pk_hex.set(_hex(cur_rgb())); busy[0] = False

        def on_disc(e):
            R = D / 2.0
            dx, dy = e.x - DP - R, e.y - DP - R
            hsv[0] = (math.degrees(math.atan2(dy, dx)) % 360.0) / 360.0
            sat = min(1.0, math.hypot(dx, dy) / (R - px(2)))
            hsv[1] = 0.0 if sat < 0.04 else (1.0 if sat > 0.96 else sat)   # iman al centro y al borde
            if hsv[2] < 0.05:
                hsv[2] = 1.0                               # si estaba en negro, que se vea el color
            redraw()

        def on_bar(e):
            hsv[2] = max(0.0, min(1.0, (e.x - px(7)) / float(max(1, BW - px(14)))))
            redraw()

        def on_hex(*_):
            if busy[0]:
                return
            t = pk_hex.get().strip().lstrip("#")
            if re.fullmatch(r"[0-9A-Fa-f]{6}", t):
                r_, g_, b_ = int(t[0:2], 16), int(t[2:4], 16), int(t[4:6], 16)
                hsv[:] = list(colorsys.rgb_to_hsv(r_ / 255.0, g_ / 255.0, b_ / 255.0))
                redraw(sync_hex=False)

        def close(_e=None):
            picker_win[0] = None
            try: win.grab_release()
            except Exception: pass
            win.destroy()

        def ok(_e=None):
            rgb = cur_rgb()
            close()
            apply_color(rgb)

        for ev in ("<Button-1>", "<B1-Motion>"):
            disc.bind(ev, on_disc); bar.bind(ev, on_bar)
        pk_hex.trace_add("write", on_hex)
        he.bind("<Return>", ok)
        win.bind("<Escape>", close)
        b_ok = ttk.Button(fi, style="Accent.TButton", text=tr("btn_apply"), command=ok)
        b_ok.grid(row=0, column=0, sticky="ew", padx=(0, px(4)))
        ttk.Button(fi, style="Btn.TButton", text=tr("btn_cancel"), command=close).grid(
            row=0, column=1, sticky="ew", padx=(px(4), 0))
        win.protocol("WM_DELETE_WINDOW", close)
        redraw()
        win.update_idletasks()
        win.geometry(f"+{root.winfo_rootx() + px(160)}+{root.winfo_rooty() + px(80)}")
        dark_titlebar(win)
        try: win.grab_set()
        except Exception: pass
        return win

    # paleta rapida: colores puros que se mandan al LED (no se tocan)
    palette = [("col_red", [255, 0, 0]), ("col_green", [0, 255, 0]),
               ("col_blue", [0, 80, 255]), ("col_cyan", [0, 255, 255]),
               ("col_magenta", [255, 0, 255]), ("col_yellow", [255, 190, 0]),
               ("col_white", [255, 255, 255])]
    c = Card(col_stack, title="color_quick", indent=True)
    pal_cv = tk.Canvas(c.ctrl, width=px(7 * 26 + 6 * 6 + 8), height=px(34), bg=CARD, highlightthickness=0)
    pal_cv.pack()

    def _draw_palette():
        pal_cv.delete("all")
        for k, (_key, rgb) in enumerate(palette):
            x = px(4) + k * px(32); y = px(4)
            if list(rgb) == list(led_color[0]):
                paint(pal_cv, "box", x - px(3), y - px(3), x + px(29), y + px(29),
                      outline=FG, width=px(2), r=px(6))
            paint(pal_cv, "box", x, y, x + px(26), y + px(26), fill=_hex(rgb), r=px(4))

    def _pal_click(e):
        k = int((e.x - px(4)) // px(32))
        if 0 <= k < len(palette):
            apply_color(palette[k][1])
    pal_cv.bind("<Button-1>", _pal_click)
    pal_cv.configure(cursor="hand2")
    _draw_swatch(); _draw_palette()

    group_hdr(pg_led, "bright_hdr")
    c = Card(pg_led, icon="bright", title="bright_title")
    bright_var = tk.IntVar(value=presets.get("led_bright", 100))

    @guard
    def apply_bright():
        mouse.set_brightness(bright_var.get())
        presets["led_bright"] = bright_var.get(); save_presets(presets)
        log(trl("log_bright", v=bright_var.get()))
    Slider(c.ctrl, bright_var, 0, 100, 220, on_release=apply_bright).cv.pack(side="left")
    bval = tk.Label(c.ctrl, bg=CARD, fg=FG, font=FONT_ROW, width=5, anchor="e")
    bval.pack(side="left", padx=(px(8), 0))
    bright_var.trace_add("write", lambda *_: bval.configure(text=f"{bright_var.get()} %"))
    bval.configure(text=f"{bright_var.get()} %")

    @guard
    def toggle_led():
        if led_on[0]:
            mouse.set_light_off(); led_on[0] = False; log(trl("log_led_off"))
        else:
            mouse.set_color(*led_color[0]); led_on[0] = True; log(trl("log_led_on"))
        presets["led_on"] = led_on[0]; save_presets(presets)
        render_onoff()

    def _led_switch(*_):
        if led_var.get() != led_on[0]:           # lo ha movido el usuario
            toggle_led()
            if led_var.get() != led_on[0]:       # no se pudo: el interruptor vuelve
                led_var.set(led_on[0])
    led_var.trace_add("write", _led_switch)

    # ---- parpadeo del logo al cambiar de perfil -------------------------------------
    # Tres pulsos con el color del perfil ("tin tin tin", como un intermitente) y el
    # LED vuelve a como estaba. Usa NOSTORE (no graba en la memoria del raton). Como
    # el raton no permite LEER el color actual, solo se parpadea si el programa SABE
    # como esta el LED (lo aplico el usuario alguna vez); si no, al terminar no
    # sabriamos dejarlo como estaba.
    group_hdr(pg_led, "grp_blink")
    blink_var = tk.BooleanVar(value=presets.get("profile_blink", True))

    def _save_blink(*_):
        presets["profile_blink"] = blink_var.get(); save_presets(presets)
    blink_var.trace_add("write", _save_blink)
    blink_q = queue.Queue()
    blink_gen = [0]
    blink_ok = [True]
    blink_warned = [False]

    c = Card(pg_led, icon="lighting", title="blink_title", desc="blink_desc")
    reg_text(ttk.Button(c.ctrl, style="Btn.TButton",
                        command=lambda: blink_for(current[0] if current[0] is not None else 0, force=True),
                        width=8),
             "blink_test").pack(side="left", padx=(0, px(12)))
    Toggle(c.ctrl, blink_var).frame.pack(side="left")

    def _rgb_of(h):
        return [int(h[k:k + 2], 16) for k in (1, 3, 5)]

    def blink_for(i, force=False):
        """Pide un parpadeo con el color del perfil i (si procede)."""
        if i is None or mouse.dev is None or wizard_active[0] or not blink_ok[0]:
            return
        if not (force or blink_var.get()) or bright_var.get() <= 0:
            return
        if "led_on" not in presets:
            if not blink_warned[0]:
                blink_warned[0] = True
                log(trl("log_blink_unknown"))
            return
        blink_gen[0] += 1
        blink_q.put((blink_gen[0], i))

    def _restore_led():
        if led_on[0]:
            mouse.set_color(*led_color[0], store=False)
        else:
            mouse.set_light_off(store=False)

    def _blink_worker():
        while True:
            job = blink_q.get()
            if job is None:
                return
            while not blink_q.empty():              # solo importa la peticion mas reciente
                nxt = blink_q.get_nowait()
                if nxt is None:
                    return
                job = nxt
            gen, i = job
            rgb = _rgb_of(PROFILE_COLORS[i])
            started = False

            def _accepted(r):
                """El raton contesta con un estado: 3 = fallo, 5 = no soportado."""
                code = r[0] if isinstance(r, (bytes, bytearray)) else r
                return code not in (0x03, 0x05)
            try:
                for _ in range(3):
                    if gen != blink_gen[0]:
                        break
                    if not _accepted(mouse.set_color(*rgb, store=False)):
                        raise RuntimeError("NOSTORE rechazado")
                    started = True
                    time.sleep(0.14)
                    mouse.set_color(0, 0, 0, store=False)
                    time.sleep(0.10)
            except Exception:
                if not started:
                    blink_ok[0] = False             # el LED no admite colores temporales
                    uiq.put(lambda: log(trl("log_blink_fail")))
            finally:
                if started and gen == blink_gen[0]:  # si viene otro parpadeo, el restaura al final
                    try:
                        _restore_led()
                    except Exception:
                        pass

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

    # --- hilo de E/S: las lecturas periodicas no congelan la ventana -----------
    # Hablar con el raton tarda (cada orden espera su respuesta, y si el
    # receptor esta ocupado reintenta). Antes se hacia en el hilo de la ventana
    # y la congelaba 0,1-0,7 s cada 3 s. Ahora un hilo hace la lectura y deja el
    # resultado en `uiq`; la decision se toma en el hilo de Tk.
    io_q = queue.Queue()
    io_busy = [False]

    def io_submit(fn, done):
        """Encola una lectura. done(estado, resultado) se llama en el hilo de Tk
        con estado 'ok' | 'busy' (raton dormido/ocupado) | 'err'. Solo una
        lectura a la vez: si ya hay una en marcha, devuelve False."""
        if io_busy[0]:
            return False
        io_busy[0] = True
        io_q.put((fn, done))
        return True

    def _io_worker():
        while True:
            job = io_q.get()
            if job is None:
                return
            fn, done = job
            try:
                res = ("ok", fn())
            except MouseBusy as e:
                res = ("busy", e)
            except Exception as e:
                res = ("err", e)

            def fin(res=res, done=done):
                io_busy[0] = False
                done(*res)
            uiq.put(fin)

    def _mode_done(st, res):
        if not ctrl_on[0] or mouse.dev is None or wizard_active[0]:
            return
        if st == "busy":
            return                                     # dormido / ocupado: se mira en el siguiente
        if st == "err":
            _read_fail(); return
        read_fails[0] = 0
        mode, x = res
        if mode != RazerMouse.MODE_DRIVER:
            log(trl("log_ctrl_reapply"))
            try: mouse.set_device_mode(RazerMouse.MODE_DRIVER)
            except Exception: pass
            apply_profile(current[0], announce=False)
        elif (current[0] is not None and profiles[current[0]]
              and x != profiles[current[0]] and not sniper_state["active"]):
            apply_profile(current[0], announce=False)

    def _compat_done(st, res):
        if ctrl_on[0] or mouse.dev is None or wizard_active[0] or sniper_state["active"]:
            return
        if st == "busy":
            return                                     # dormido / ocupado: no es desconexion
        if st == "err":
            _read_fail(); return
        read_fails[0] = 0
        changed = compat_process(res)
        sync_entries()
        if changed is not None:
            if notify_var.get():
                show_toast(changed)
            blink_for(changed)

    def auto_tick():
        try:
            now = time.time()
            if wizard_active[0]:
                pass                                   # el asistente manda: no tocar el raton
            elif mouse.dev is None:
                if now - last_conn_try[0] >= RECONNECT_S and not io_busy[0]:
                    connect_async()
            elif ctrl_on[0]:
                if verify_deadline[0] and not _window_active():
                    verify_deadline[0] += POLL_MS / 1000.0   # la cuenta atras solo corre con la ventana visible
                if verify_deadline[0] and now > verify_deadline[0]:
                    fall_back("log_ctrl_noevents")
                elif listener[0] is not None and not listener[0].alive():
                    fall_back("log_ctrl_fail")
                elif now - last_mode_check[0] >= MODE_CHECK_S:
                    if io_submit(lambda: (mouse.get_device_mode(), mouse.get_dpi()[0]), _mode_done):
                        last_mode_check[0] = now
            else:
                notify_on = notify_var.get()
                if not sniper_state["active"] and (notify_on or _window_active()):
                    io_submit(lambda: mouse.get_dpi()[0], _compat_done)
            need_batt = _window_active() or batt_alert_var.get() or batt_full_var.get()
            if (mouse.dev is not None and not wizard_active[0] and need_batt
                    and now - last_batt[0] >= BATT_S):
                if refresh_battery_async():
                    last_batt[0] = now
        except Exception as e:
            log(f"[ERROR] {e}")
        finally:
            root.after(POLL_MS, auto_tick)

    root.after(POLL_MS, auto_tick)

    # =====================================================================
    # 9b) AJUSTES: bandeja, arranque con Windows, idioma, actualizaciones.
    #     Los hilos secundarios (red, bandeja) NUNCA tocan widgets: dejan
    #     funciones en `uiq` y el hilo de Tk las ejecuta (pump_ui).
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

    def quit_app(then=None):
        if tray[0] is not None:
            try: tray[0].stop()
            except Exception: pass
            tray[0] = None
        try: intro.stop()                   # la musica del modo Mediavida
        except Exception: pass
        try: remapper.stop()                # quita el gancho de Windows
        except Exception: pass
        blink_q.put(None); sniper_q.put(None); io_q.put(None); dpi_q.put(None)   # paran los hilos auxiliares
        release_control(announce=False)     # el raton vuelve a su modo normal
        try: mouse.close()
        except Exception: pass
        if then is not None:
            try: then()
            except Exception: pass
        root.destroy()

    def restart_app():
        """Cierra limpio y vuelve a abrir el programa (para aplicar el tema)."""
        def _relaunch():
            release_single_instance()
            if getattr(sys, "frozen", False):
                args = [sys.executable]
            else:
                args = [sys.executable, os.path.abspath(__file__)]
            env = dict(os.environ)
            env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"   # .exe de PyInstaller: proceso nuevo e independiente
            env.pop("_MEIPASS2", None)
            subprocess.Popen(args + ["--restarted"], close_fds=True, env=env)
        log(trl("log_restart"))
        quit_app(then=_relaunch)

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
        def _profile_action(k):
            # pystray exige exactamente (icon, item): sin argumentos por defecto
            return lambda icon, item: uiq.put(lambda: on_click_profile(k))

        def _profile_items():
            for k in _enabled():
                yield pystray.MenuItem(
                    lambda item, k=k: f"{tr('profile')} {k + 1} · {profiles[k]} DPI",
                    _profile_action(k),
                    checked=lambda item, k=k: current[0] == k,
                    radio=True,
                    enabled=lambda item: bool(ctrl_on[0]))       # solo en modo control

        menu = pystray.Menu(
            pystray.MenuItem(lambda item: tray_status() or APP_NAME, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: tr("tray_profiles"), pystray.Menu(_profile_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: tr("tray_show"), lambda i, it: uiq.put(show_window), default=True),
            pystray.MenuItem(lambda item: tr("tray_quit"), lambda i, it: uiq.put(request_quit)),
        )
        icon = pystray.Icon(APP_NAME, _tray_image(), tray_tip(), menu)
        tray[0] = icon
        icon.run_detached()                      # corre en su propio hilo
        log(trl("log_tray"))

    _tray_ok_after = [time.time() + 4.0]      # nunca a la bandeja durante el arranque
    def on_unmap(e):
        if time.time() < _tray_ok_after[0]:
            return
        # los bindings de la ventana raiz tambien reciben eventos de sus hijos:
        # solo nos interesa cuando se minimiza la ventana principal
        if e.widget is root and tray_var.get() and TRAY_OK:
            root.after(10, lambda: root.state() == "iconic" and to_tray())
    root.bind("<Unmap>", on_unmap, add="+")

    group_hdr(pg_set, "grp_system")
    set_sys = stack(pg_set)
    tray_var = tk.BooleanVar(value=bool(presets.get("tray", False)) and TRAY_OK)
    def _save_tray(*_):
        presets["tray"] = tray_var.get(); save_presets(presets)
    tray_var.trace_add("write", _save_tray)
    c = Card(set_sys, icon="monitor", title="tray_title", desc=("tray_desc" if TRAY_OK else "opt_tray_na"))
    Toggle(c.ctrl, tray_var, enabled=TRAY_OK).frame.pack()

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
            log(trl("log_autostart_on" if want else "log_autostart_off"))
        except Exception as e:
            log(trl("log_autostart_err", e=e))
            _autostart_busy[0] = True            # revierte la casilla sin re-disparar
            autostart_var.set(not want)
            _autostart_busy[0] = False
    autostart_var.trace_add("write", _toggle_autostart)

    c = Card(set_sys, icon="power", title="autostart_title",
             desc=("autostart_desc" if AUTOSTART_OK else "autostart_desc_na"))
    Toggle(c.ctrl, autostart_var, enabled=AUTOSTART_OK).frame.pack()

    # --- actualizaciones ---------------------------------------------------
    group_hdr(pg_set, "grp_updates")
    set_upd = stack(pg_set)
    upd_card = Card(set_upd, icon="refresh", title=None, desc=None, wrap=250)
    upd_btn = ttk.Button(upd_card.ctrl, style="Btn.TButton", command=lambda: check_updates(True))
    upd_btn.pack(side="left")
    install_btn = ttk.Button(upd_card.ctrl, style="Accent.TButton", command=lambda: install_update())
    reg(lambda: (upd_btn.configure(text=tr("upd_check_btn")), install_btn.configure(text=tr("btn_install_upd"))))

    upd_start_var = tk.BooleanVar(value=presets.get("check_updates", True))
    def _save_upd(*_):
        presets["check_updates"] = upd_start_var.get(); save_presets(presets)
    upd_start_var.trace_add("write", _save_upd)
    c = Card(set_upd, icon="sync", title="upd_start_title", desc="upd_start_desc")
    Toggle(c.ctrl, upd_start_var).frame.pack()

    # estado de la comprobacion (para repintar al cambiar de idioma):
    #   ("idle",) ("checking",) ("latest",) ("err",) ("new", tag, page, exe_url) ("dl", tag)
    state_upd = [("idle",)]

    def render_upd():
        st_ = state_upd[0]
        titles = {"checking": tr("updt_checking"), "latest": tr("updt_latest"), "err": tr("updt_err")}
        if st_[0] == "new":
            t = tr("updt_new", tag=st_[1])
        elif st_[0] == "dl":
            t = tr("updt_dl", tag=st_[1])
        else:
            t = titles.get(st_[0], tr("updt_idle"))
        upd_card.title.configure(text=t, fg=(T["LINK"] if st_[0] == "new" else FG))
        upd_card.set_desc(tr("about_ver", v=APP_VERSION))
        if st_[0] == "new":
            if not install_btn.winfo_ismapped():
                install_btn.pack(side="left", padx=(px(8), 0))
        else:
            install_btn.pack_forget()
        upd_btn.state(["disabled"] if st_[0] in ("checking", "dl") else ["!disabled"])
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
            log(trl("log_upd_new", tag=tag, v=APP_VERSION))
            if manual:
                install_update()
        else:
            state_upd[0] = ("latest",); render_upd()
            if manual:
                log(trl("log_upd_latest", v=APP_VERSION))
                messagebox.showinfo(tr("dlg_uptodate_title"), tr("dlg_uptodate_msg", v=APP_VERSION))

    def _upd_error(e, manual):
        state_upd[0] = ("err",); render_upd()
        if manual:
            log(trl("log_upd_err", e=e))

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
            except Exception as e: log(trl("log_browser_err", e=e))
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
        log(trl("log_upd_saved", path=dest))
        if messagebox.askyesno(tr("dlg_upd_done_title"), tr("dlg_upd_done_msg", path=dest)):
            try:
                release_single_instance()   # si no, la nueva creeria que ya hay una abierta
                env = dict(os.environ)
                env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"   # la nueva arranca como proceso independiente
                env.pop("_MEIPASS2", None)
                subprocess.Popen([dest], close_fds=True, env=env)
                quit_app()
            except Exception as e:
                log(trl("log_upd_dl_err", e=e))

    def _upd_dl_error(e, prev_state):
        state_upd[0] = prev_state; render_upd()
        log(trl("log_upd_dl_err", e=e))

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
        log(trl("log_bug_opened"))
        try: webbrowser.open_new(url)
        except Exception as e: log(trl("log_browser_err", e=e))

    # =====================================================================
    # 10) ACERCA DE  y  acciones del Registro
    # =====================================================================
    def open_kofi(_e=None):
        try: webbrowser.open_new(KOFI_URL)
        except Exception as e: log(trl("log_browser_err", e=e))

    def open_url(u):
        try: webbrowser.open_new(u)
        except Exception as e: log(trl("log_browser_err", e=e))

    def copy_log():
        root.clipboard_clear(); root.clipboard_append(logbox.get("1.0", "end").rstrip())
        log(trl("log_copied"))

    reg_text(ttk.Button(log_actions, style="Btn.TButton", command=copy_log), "btn_copy").pack(side="left")
    reg_text(ttk.Button(log_actions, style="Btn.TButton", command=report_bug),
             "btn_report_plain").pack(side="left", padx=(px(8), 0))
    reg_text(log_note, "report_desc")

    pg_about = new_page("about")
    page_title(pg_about, "nav_about")
    ab = tk.Frame(pg_about, bg=CARD, highlightthickness=1, highlightbackground=CARD_BORDER)
    ab.pack(fill="x", pady=(px(8), 0))
    abi = tk.Frame(ab, bg=CARD); abi.pack(fill="x", padx=px(16), pady=px(16))
    ab_head = tk.Frame(abi, bg=CARD); ab_head.pack(anchor="w")
    ab_logo = tk.Canvas(ab_head, width=px(48), height=px(48), bg=CARD, highlightthickness=0)
    ab_logo.pack(side="left", padx=(0, px(16)))
    paint(ab_logo, "box", 0, 0, px(48), px(48), fill=CTRL, r=px(6))
    draw_mouse(ab_logo, px(24), px(24), px(32), ACCENT)
    ab_names = tk.Frame(ab_head, bg=CARD); ab_names.pack(side="left")
    tk.Label(ab_names, text=APP_NAME, bg=CARD, fg=FG, font=FONT_BIG, anchor="w").pack(anchor="w")
    reg_text(tk.Label(ab_names, bg=CARD, fg=FG2, font=FONT_DESC, anchor="w"), "about_ver",
             v=APP_VERSION).pack(anchor="w")
    ab_desc = tk.Label(abi, bg=CARD, fg=FG2, font=FONT_ROW, anchor="w", justify="left",
                       wraplength=px(520))
    reg_text(ab_desc, "about_app_desc").pack(anchor="w", pady=(px(14), 0))
    autowrap(ab_desc, abi, 0, lo=240, hi=820)

    group_hdr(pg_about, "why_hdr")
    why = tk.Frame(pg_about, bg=CARD, highlightthickness=1, highlightbackground=CARD_BORDER)
    why.pack(fill="x")
    why_lbl = tk.Label(why, bg=CARD, fg=FG2, font=FONT_ROW, anchor="w", justify="left",
                       wraplength=px(530))
    reg_text(why_lbl, "about_text").pack(fill="x", padx=px(16), pady=px(14))
    autowrap(why_lbl, why, 32, lo=240, hi=820)

    group_hdr(pg_about, "links_hdr")
    links = stack(pg_about)

    def link_row(parent, title_key, desc, url, title_text=None):
        c = Card(parent, icon=None, title=title_key, desc=None, wrap=440)
        if title_text: c.title.configure(text=title_text)
        if desc: reg(lambda: c.set_desc(tr(desc)))
        ic = icon_label(c.ctrl, "open", 16, FG2)
        if ic: ic.pack()
        parts = [c.frame, c.inner, c.title, c.desc, c.ctrl] + ([ic] if ic else []) + list(c.title.master.winfo_children())
        def hov(on):
            col = CTRL_HOVER if on else CARD
            for w in parts + [c.title.master]:
                try: w.configure(bg=col)
                except Exception: pass
        for w in parts + [c.title.master]:
            w.configure(cursor="hand2")
            w.bind("<Enter>", lambda _e: hov(True)); w.bind("<Leave>", lambda _e: hov(False))
            w.bind("<Button-1>", lambda _e: open_url(url))
        return c
    _repo_short = REPO_URL.replace("https://", "")
    c = link_row(links, "link_repo", None, REPO_URL); c.set_desc(_repo_short)
    link_row(links, None, "link_openrazer_desc", "https://github.com/openrazer/openrazer", title_text="OpenRazer")
    link_row(links, None, "link_kofi_desc", KOFI_URL, title_text="Spot me a protein scoop")

    group_hdr(pg_about, "license_hdr")
    Card(pg_about, icon="doc", title="license_title", desc="license_desc", wrap=480)

    def info_dialog(title, sub, items, btn_text):
        """Dialogo informativo sencillo (bienvenida / novedades), no bloquea."""
        win = tk.Toplevel(root); win.configure(bg=BG); win.resizable(False, False)
        win.title(APP_NAME); win.transient(root)
        try:
            if os.path.exists(_ico_path): win.iconbitmap(_ico_path)
        except Exception: pass
        W = px(480)
        top = tk.Frame(win, bg=CARD); top.pack(fill="x")
        ti = tk.Frame(top, bg=CARD); ti.pack(fill="x", padx=px(24), pady=px(24))
        head = tk.Frame(ti, bg=CARD); head.pack(fill="x")
        cv = tk.Canvas(head, width=px(48), height=px(48), bg=CARD, highlightthickness=0)
        cv.pack(side="left", padx=(0, px(14))); draw_mouse(cv, px(24), px(24), px(44), ACCENT)
        tt = tk.Frame(head, bg=CARD); tt.pack(side="left", fill="x")
        tk.Label(tt, text=title, bg=CARD, fg=FG, font=FONT_BIG, anchor="w").pack(anchor="w")
        if sub:
            tk.Label(tt, text=sub, bg=CARD, fg=FG2, font=FONT_DESC, anchor="w").pack(anchor="w")
        body = tk.Frame(ti, bg=CARD); body.pack(fill="x", pady=(px(18), 0))
        for t in items:
            row = tk.Frame(body, bg=CARD); row.pack(fill="x", pady=(0, px(9)))
            dot = tk.Canvas(row, width=px(8), height=px(8), bg=CARD, highlightthickness=0)
            dot.pack(side="left", anchor="n", padx=(0, px(12)), pady=(px(6), 0))
            paint(dot, "dot", 0, 0, px(8), px(8), fill=ACCENT)
            tk.Label(row, text=t, bg=CARD, fg=FG, font=FONT_ROW, anchor="w", justify="left",
                     wraplength=W - px(48) - px(22)).pack(side="left", fill="x", expand=True)
        foot = tk.Frame(win, bg=BG); foot.pack(fill="x")
        tk.Frame(foot, bg=CARD_BORDER, height=1).pack(fill="x")
        fi = tk.Frame(foot, bg=BG); fi.pack(fill="x", padx=px(24), pady=px(20))
        ttk.Button(fi, text=btn_text, style="Accent.TButton", command=win.destroy).pack(fill="x")
        win.update_idletasks()
        h = win.winfo_reqheight()
        x = root.winfo_rootx() + max(0, (root.winfo_width() - W) // 2)
        y = root.winfo_rooty() + max(0, (root.winfo_height() - h) // 3)
        win.geometry(f"{W}x{h}+{x}+{y}")
        dark_titlebar(win)
        return win

    def show_welcome():
        return info_dialog(tr("wl_title"), tr("wl_sub"), [tr("wl_1"), tr("wl_2"), tr("wl_3")], tr("wl_btn"))

    def show_whats_new():
        items = WHATS_NEW.get(APP_VERSION, {}).get(lang[0]) or WHATS_NEW.get(APP_VERSION, {}).get("en")
        if not items:
            return None
        return info_dialog(tr("wn_title", v=APP_VERSION), "", items, tr("btn_close"))

    wn_card = Card(pg_about, icon="sync", title="wn_link", desc="wn_desc")
    reg_text(ttk.Button(wn_card.ctrl, style="Btn.TButton", command=show_whats_new), "wn_show").pack()

    # mensajes iniciales del log: siempre en ingles (lo que venga despues
    # sigue el idioma elegido)
    log("Welcome! Close Razer Synapse and plug in your mouse.")
    log("While open, the app runs your profiles: switch them with the mouse's profile button and edit them here.")
    for _te in theme_errors:
        log("[!] " + _te)
    if THEME_NAME.startswith("user:"):
        log(f"Theme: {theme_label(THEME_NAME)} ({THEME_MODE})")

    # =====================================================================
    # 11) TAMANO: por defecto mas grande, redimensionable y con memoria
    #     (el contenido se recoloca solo: las tarjetas reajustan sus textos y
    #     cada pagina muestra una barra de desplazamiento si no cabe).
    # =====================================================================
    _sw, _sh = root.winfo_screenwidth(), root.winfo_screenheight()
    MIN_W, MIN_H = px(800), px(640 if MV_ACTIVE else 600)   # una entrada mas en la barra
    root.minsize(min(MIN_W, _sw), min(MIN_H, _sh))
    _wa_h = _sh - px(70)                  # alto util aproximado (sin barra de tareas)
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes as _wt
            _r = _wt.RECT()
            if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(_r), 0):   # SPI_GETWORKAREA
                _wa_h = _r.bottom - _r.top
        except Exception:
            pass
    # lo mas alto que quepa (hasta 900 px) para que casi ninguna pagina necesite scroll
    DEF_W, DEF_H = min(px(1120), _sw - px(60)), min(px(900), _wa_h - px(40))

    def _initial_geometry():
        w, h = DEF_W, DEF_H
        x, y = (_sw - w) // 2, max(0, (_sh - h) // 3)
        g = presets.get("win_geom")
        try:
            gw, gh, gx, gy = [int(v) for v in g]
            if MIN_W <= gw <= _sw and MIN_H <= gh <= _sh:
                w, h = gw, gh
                # que la ventana quede a la vista (un monitor puede haber desaparecido)
                if -w + px(120) < gx < _sw - px(120) and 0 <= gy < _sh - px(80):
                    x, y = gx, gy
        except Exception:
            pass
        return f"{w}x{h}+{x}+{y}"

    root.geometry(_initial_geometry())
    root.resizable(True, True)
    _geom_job = [None]

    def _save_geom():
        _geom_job[0] = None
        try:
            if root.state() != "normal":
                return
            presets["win_geom"] = [root.winfo_width(), root.winfo_height(), root.winfo_x(), root.winfo_y()]
            save_presets(presets)
        except Exception:
            pass

    def _on_root_cfg(e):
        if e.widget is not root:
            return
        if _geom_job[0] is not None:
            try: root.after_cancel(_geom_job[0])
            except Exception: pass
        _geom_job[0] = root.after(700, _save_geom)
    root.bind("<Configure>", _on_root_cfg, add="+")
    show_page(presets.get("last_page", "profiles") if presets.get("last_page") in PAGES else "profiles")
    root.deiconify()
    dark_titlebar(root)

    # =====================================================================
    # 12) ARRANQUE
    # =====================================================================
    root.after(150, pump_ui)                     # ejecuta lo que dejan los hilos
    threading.Thread(target=_blink_worker, daemon=True).start()     # parpadeo del logo
    threading.Thread(target=_io_worker, daemon=True).start()        # lecturas periodicas
    threading.Thread(target=_dpi_worker, daemon=True).start()       # cambios de DPI
    threading.Thread(target=_sniper_worker, daemon=True).start()    # sniper

    def _startup_dialogs():
        """Primera vez: bienvenida. Tras actualizar: novedades. Una sola vez."""
        if "--minimized" in sys.argv:             # arranque con Windows: no molestar
            return
        if first_run and not presets.get("welcomed"):
            presets["welcomed"] = True; presets["last_version"] = APP_VERSION; save_presets(presets)
            show_welcome()
        elif presets.get("last_version") != APP_VERSION:
            presets["last_version"] = APP_VERSION; save_presets(presets)
            show_whats_new()
    root.after(1200, _startup_dialogs)
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

    root.after(300, connect_async)                    # conexion automatica (sin congelar)

    # =====================================================================
    # 13) MODO MEDIAVIDA (secreto)
    #     Codigo Konami con la ventana en primer plano -> se desbloquea y se
    #     pone el tema "Mediavida" y el programa se reinicia para aplicarlo.
    #     Al volver suena la intro y sale el aviso. No se conecta a nada: el
    #     logo y la musica van dentro del programa. Se quita eligiendo otro
    #     tema en Ajustes.
    # =====================================================================
    intro = IntroSound()
    konami = KonamiDetector()
    mv_dialog = [None]
    mv_going = [False]                                 # ya se esta reiniciando

    def open_mv_unlocked():
        """Aviso de 'modo desbloqueado' con los colores del foro."""
        if mv_dialog[0] is not None and mv_dialog[0].winfo_exists():
            mv_dialog[0].lift(); return mv_dialog[0]
        C = _MV_PAL
        st.configure("MVA.TButton", background=C["ACCENT"], foreground=C["ON_ACCENT"], bordercolor=C["ACCENT"],
                     lightcolor=C["ACCENT"], darkcolor=C["ACCENT"], relief="flat", padding=(px(12), px(5)),
                     font=FONT_ROW, focuscolor=C["ACCENT"])
        st.map("MVA.TButton", background=[("active", C["ACCENT_HOVER"])],
               lightcolor=[("active", C["ACCENT_HOVER"])], darkcolor=[("active", C["ACCENT_HOVER"])],
               bordercolor=[("active", C["ACCENT_HOVER"])])
        win = tk.Toplevel(root); win.configure(bg=C["BG"]); win.resizable(False, False)
        win.title(APP_NAME); win.transient(root); mv_dialog[0] = win
        try:
            if os.path.exists(_ico_path): win.iconbitmap(_ico_path)
        except Exception: pass
        W = px(440)
        top = tk.Frame(win, bg=C["CARD"]); top.pack(fill="x")
        ti = tk.Frame(top, bg=C["CARD"]); ti.pack(fill="x", padx=px(24), pady=px(24))
        cv = tk.Canvas(ti, width=px(64), height=px(64), bg=C["CARD"], highlightthickness=0)
        cv.pack(side="left", padx=(0, px(18)))
        fr = image_frames(MV_LOGO, px(64), radius=px(14))
        if fr:
            cv._img = fr[0][0]; cv.create_image(0, 0, image=fr[0][0], anchor="nw")
        tt = tk.Frame(ti, bg=C["CARD"]); tt.pack(side="left", fill="x")
        tk.Label(tt, text=tr("mv_unl_title"), bg=C["CARD"], fg=C["FG"], font=FONT_BIG, anchor="w").pack(anchor="w")
        tk.Label(tt, text=tr("mv_unl_sub"), bg=C["CARD"], fg=C["FG2"], font=FONT_DESC, anchor="w",
                 justify="left", wraplength=W - px(130)).pack(anchor="w", pady=(px(2), 0))
        foot = tk.Frame(win, bg=C["BG"]); foot.pack(fill="x")
        tk.Frame(foot, bg=C["SELECT_BG"], height=1).pack(fill="x")
        fi = tk.Frame(foot, bg=C["BG"]); fi.pack(fill="x", padx=px(24), pady=px(18))

        def close(_e=None):
            mv_dialog[0] = None
            try: win.grab_release()
            except Exception: pass
            try: win.destroy()
            except Exception: pass
        b_ok = ttk.Button(fi, style="MVA.TButton", text=tr("mv_unl_ok"), command=close)
        b_ok.pack(side="right")
        win.bind("<Escape>", close); win.bind("<Return>", close); win.protocol("WM_DELETE_WINDOW", close)
        win.update_idletasks()
        W = max(W, win.winfo_reqwidth())
        win.geometry(f"{W}x{win.winfo_reqheight()}+{root.winfo_rootx() + px(170)}+{root.winfo_rooty() + px(110)}")
        try:                                         # barra de titulo oscura, como el foro
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
            v = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(v), 4)
            col = ctypes.c_int(0x00090A0B)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(col), 4)
        except Exception:
            pass
        try: win.grab_set()
        except Exception: pass
        b_ok.focus_set()
        return win

    def _konami_key(e):
        if not konami.feed(getattr(e, "keysym", "")):
            return
        if MV_ACTIVE:                                  # ya esta puesto: solo la musiquilla
            intro.play(resource("mv_intro.mp3")); return
        if mv_going[0] or wizard_active[0]:            # nunca a mitad de grabar en el raton
            return
        mv_going[0] = True
        presets.update({"mv_unlocked": True, "theme": "mediavida", "theme_mode": "dark",
                        "mv_welcome": True})
        save_presets(presets)
        log(trl("log_mv_on"))
        restart_app()                                  # el tema se aplica al arrancar
    root.bind_all("<KeyPress>", _konami_key, add="+")

    if MV_ACTIVE and presets.pop("mv_welcome", None):  # recien desbloqueado: intro + aviso
        save_presets(presets)

        def _mv_welcome():
            show_window()
            intro.play(resource("mv_intro.mp3"))
            open_mv_unlocked()
        root.after(700, _mv_welcome)
    elif presets.pop("mv_welcome", None):              # (por si quedo puesto sin el tema)
        save_presets(presets)

    if os.environ.get("NSM_TEST_API"):               # solo para las pruebas automaticas
        globals()["_TEST_API"] = dict(locals())

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
