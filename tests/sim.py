# -*- coding: utf-8 -*-
"""Simulador del raton Razer A NIVEL DE PROTOCOLO (informes HID de 90 bytes).

Sustituye al modulo `hid` (hidapi): el programa usa su RazerMouse y su
ButtonListener REALES, y este simulador contesta como lo haria una Viper
Ultimate con su receptor inalambrico, incluidos sus fallos:

  busy_n        -> las siguientes N respuestas dicen "ocupado" (0x01)
  timeout_until -> hasta ese momento el receptor contesta "timeout" (0x04) con datos a cero
  zero_batt_n   -> las siguientes N lecturas de bateria dan 0 con estado OK (el bug del 0 %)
  stale_p       -> probabilidad de devolver la respuesta ANTERIOR (receptor lento)
  empty_p       -> probabilidad de devolver un informe vacio
  latency       -> retardo de cada lectura
  plugged       -> False = desenchufado (las llamadas fallan como en Windows)
  listener_ok   -> False = Windows no deja abrir las interfaces de botones
"""
import random, threading, time, queue

VID = 0x1532
PID = 0x007B                      # Viper Ultimate, receptor


class SimMouse:
    def __init__(self, seed=1):
        self.rng = random.Random(seed)
        self.lock = threading.Lock()
        self.fw = (1, 7)
        self.mode = 0x00
        self.dpi = (800, 800)
        self.onboard = [400, 800, 1600, 3200, 6400]     # perfiles internos del raton
        self.onboard_i = 1
        self.batt_raw = int(0.74 * 255)
        self.charging = False
        self.poll = 0x01
        self.led = {"effect": 1, "rgb": (0, 255, 0), "bright": 255, "stores": 0, "nostores": 0}
        self.tx = {0x00: 0xFF, 0x04: 0xFF, 0x07: 0xFF, 0x0F: 0x3F}
        # fallos
        self.busy_n = 0
        self.timeout_until = 0.0
        self.zero_batt_n = 0
        self.stale_p = 0.0
        self.empty_p = 0.0
        self.garbage_p = 0.0
        self.latency = 0.0
        self.plugged = True
        self.listener_ok = True
        self.flash_writes = 0             # escrituras en memoria (VARSTORE)
        self.events = _Broadcast(self)    # informes de entrada (Report 4), a TODAS las interfaces abiertas
        self.btn_devs = []
        self.cmd_log = []

    # --- el usuario fisico ----------------------------------------------------
    def press(self, code=0x50, hold=0.05):
        """Pulsa un boton especial. En modo driver avisa al PC (Report 4);
        en modo normal el raton cambia solo de perfil interno."""
        if self.mode == 0x03:
            self.events.put(bytes([0x04, code] + [0] * 14))
            time.sleep(hold)
            self.events.put(bytes([0x04] + [0] * 15))
        elif code in (0x50, 0x52):
            self.onboard_i = (self.onboard_i + 1) % 5
            v = self.onboard[self.onboard_i]
            self.dpi = (v, v)

    # --- protocolo ------------------------------------------------------------
    def answer(self, req):
        """req: 90 bytes del informe. Devuelve la respuesta (90 bytes)."""
        r = bytearray(req)
        cls, cid, tx = req[6], req[7], req[1]
        self.cmd_log.append((cls, cid))
        if self.rng.random() < self.garbage_p:
            return bytes(self.rng.randrange(256) for _ in range(90))
        if self.tx.get(cls, 0xFF) != tx:
            return bytes(90)                       # tid equivocado: el raton no contesta a eso
        if time.time() < self.timeout_until:
            r[0] = 0x04
            for i in range(8, 88): r[i] = 0
            return bytes(r)
        if self.busy_n > 0:
            self.busy_n -= 1
            r[0] = 0x01
            return bytes(r)
        r[0] = 0x02
        a = req[8:88]
        if cls == 0x00 and cid == 0x81:
            r[8], r[9] = self.fw
        elif cls == 0x00 and cid == 0x84:
            r[8] = self.mode
        elif cls == 0x00 and cid == 0x04:
            self.mode = a[0]
        elif cls == 0x00 and cid == 0x05:
            self.poll = a[0]
        elif cls == 0x04 and cid == 0x85:
            x, y = self.dpi
            r[9], r[10], r[11], r[12] = x >> 8, x & 0xFF, y >> 8, y & 0xFF
        elif cls == 0x04 and cid == 0x05:
            x, y = (a[1] << 8) | a[2], (a[3] << 8) | a[4]
            self.dpi = (x, y)
            if a[0] == 0x01:
                self.flash_writes += 1
                self.onboard[self.onboard_i] = x
        elif cls == 0x07 and cid == 0x80:
            if self.zero_batt_n > 0:
                self.zero_batt_n -= 1
                r[9] = 0
            else:
                r[9] = self.batt_raw
        elif cls == 0x07 and cid == 0x84:
            r[9] = 1 if self.charging else 0
        elif cls == 0x0F and cid == 0x02:
            store = a[0]
            if store: self.led["stores"] += 1
            else: self.led["nostores"] += 1
            self.led["effect"] = a[2]
            if a[2] == 0x01:
                self.led["rgb"] = (a[6], a[7], a[8])
        elif cls == 0x0F and cid == 0x04:
            self.led["bright"] = a[2]
        else:
            r[0] = 0x05                            # no soportado
        return bytes(r)

    def pct(self):
        return round(self.batt_raw / 255 * 100)


class _Broadcast:
    """Como en Windows: cada informe de entrada llega a cada handle abierto."""
    def __init__(self, sim): self.sim = sim
    def put(self, data):
        for d in list(self.sim.btn_devs):
            if not d.closed:
                d.q.put(data)
    def qsize(self):
        return sum(d.q.qsize() for d in self.sim.btn_devs if not d.closed)


class SimDev:
    def __init__(self, sim, kind):
        self.sim, self.kind = sim, kind
        self.pending = None
        self.prev = None
        self.closed = False
        self.q = queue.Queue()

    def open_path(self, path):
        if not self.sim.plugged:
            raise OSError("open failed")
        if path == b"btn" and not self.sim.listener_ok:
            raise OSError("access denied")
        if path == b"ctl":
            pass
        if path == b"btn":
            self.sim.btn_devs.append(self)

    def send_feature_report(self, data):
        if self.closed or not self.sim.plugged:
            return -1
        with self.sim.lock:
            self.prev = self.pending
            self.pending = self.sim.answer(bytes(data[1:91]))
        return len(data)

    def get_feature_report(self, rid, n):
        if self.closed or not self.sim.plugged:
            raise OSError("read error")
        if self.sim.latency:
            time.sleep(self.sim.latency)
        rng = self.sim.rng
        if rng.random() < self.sim.empty_p:
            return []
        resp = self.pending
        if self.prev is not None and rng.random() < self.sim.stale_p:
            resp = self.prev                         # el receptor da la respuesta anterior
        if resp is None:
            return []
        return [0x00] + list(resp)                   # Windows antepone el id de informe

    def read(self, n, timeout_ms):
        if self.closed:
            raise OSError("closed")
        if not self.sim.plugged:
            raise OSError("device disconnected")
        if not self.sim.listener_ok:
            raise OSError("access denied")           # Windows no deja leer esta interfaz
        if self.kind != b"btn":                      # por esta interfaz no llegan botones
            time.sleep(timeout_ms / 1000.0)
            return []
        try:
            return list(self.q.get(timeout=timeout_ms / 1000.0))
        except queue.Empty:
            return []

    def close(self):
        self.closed = True
        try: self.sim.btn_devs.remove(self)
        except ValueError: pass


class SimHid:
    """Sustituto del modulo `hid`."""
    sim = None

    @classmethod
    def enumerate(cls, vid=0, pid=0):
        s = cls.sim
        if s is None or not s.plugged:
            return []
        if pid not in (0, PID):
            return []
        return [{"product_id": PID, "path": b"ctl", "interface_number": 0},
                {"product_id": PID, "path": b"btn", "interface_number": 1}]

    @classmethod
    def device(cls):
        return _Opener(cls.sim)


class _Opener:
    """hid.device() + open_path(): el tipo se decide al abrir."""
    def __init__(self, sim):
        self.sim = sim
        self._d = None

    def open_path(self, path):
        self._d = SimDev(self.sim, path)
        self._d.open_path(path)

    def __getattr__(self, name):
        return getattr(self._d, name)
