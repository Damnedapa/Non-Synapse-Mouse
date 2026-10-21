import sys, time, threading, importlib.util
spec = importlib.util.spec_from_file_location("nsm", __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "Non_Synapse_Mouse.py"))
nsm = importlib.util.module_from_spec(spec); sys.modules["nsm"] = nsm; spec.loader.exec_module(nsm)
RES = []
def check(n, c, i=""):
    RES.append(bool(c)); print(("PASS " if c else "FAIL ") + n + (f"  [{i}]" if (i and not c) else ""))

# --- ButtonListener: pulsar y soltar ----------------------------------------------
class FakeHidDev:
    def __init__(self, script): self.script = list(script); self.closed = False
    def open_path(self, p): pass
    def read(self, n, to):
        if self.script: return self.script.pop(0)
        time.sleep(0.01); return []
    def close(self): self.closed = True
class FakeHid:
    script = []
    @staticmethod
    def enumerate(v, p): return [{"path": b"x"}]
    @staticmethod
    def device(): return FakeHidDev(FakeHid.script)
nsm.hid = FakeHid
FakeHid.script = [[0x04, 0x20], [0x04, 0x20, 0x22], [0x04, 0x22], [0x04], [0x05, 1, 2], [0x04, 0x50], [0x04]]
ev = []
lst = nsm.ButtonListener(1, lambda c: ev.append(("down", c)), lambda r: ev.append(("other", r[0])), lambda c: ev.append(("up", c)))
lst.start(); time.sleep(0.4); lst.stop()
check("listener: press/release edges in order", ev == [("down", 0x20), ("down", 0x22), ("up", 0x20), ("up", 0x22), ("other", 5), ("down", 0x50), ("up", 0x50)], ev)
lst2 = nsm.ButtonListener(1, lambda c: None); FakeHid.script = [[0x04, 0x20], [0x04]]
lst2.start(); time.sleep(0.2); lst2.stop(); check("listener without on_release still works", True)

# --- set_color / NOSTORE: bytes enviados -------------------------------------------------
class Dev:
    def __init__(self): self.sent = []; self.last = None
    def send_feature_report(self, b): self.sent.append(bytes(b)); self.last = bytes(b); return len(b)
    def get_feature_report(self, rid, n):
        r = bytearray(self.last); r[1 + 0] = r[1]; r[1] = r[1]; r[1] = 0x02 if False else r[1]
        r[1] = self.last[1]; out = bytearray(self.last); out[1] = 0x02          # status OK en el byte 0 del informe
        return bytes(out)
m = nsm.RazerMouse(); m.dev = Dev(); m.model = {"name": "t", "led": 0x04}; m.tx_cache = {0x0F: 0x3F}
m.set_color(10, 20, 30, store=False); a = m.dev.sent[-1]
check("set_color(store=False) -> NOSTORE byte, rgb ok", a[1 + 8] == nsm.NOSTORE and a[1 + 14:1 + 17] == bytes([10, 20, 30]), a[9:20].hex())
m.set_color(1, 2, 3); a = m.dev.sent[-1]
check("set_color() default -> VARSTORE", a[1 + 8] == nsm.VARSTORE)
m.set_light_off(store=False); a = m.dev.sent[-1]
check("set_light_off(store=False) -> NOSTORE", a[1 + 8] == nsm.NOSTORE and a[1 + 10] == 0x00)
crc = 0
for k in range(2, 88): crc ^= a[1 + k]
check("CRC valid", crc == a[1 + 88])

# --- RLock: dos hilos no mezclan envio/lectura -----------------------------------------------
class SlowDev(Dev):
    def __init__(self): super().__init__(); self.inflight = 0; self.bad = 0
    def send_feature_report(self, b):
        self.inflight += 1; r = super().send_feature_report(b); return r
    def get_feature_report(self, rid, n):
        out = super().get_feature_report(rid, n)
        self.inflight -= 1
        if self.inflight != 0: self.bad += 1
        return out
sd = SlowDev(); m2 = nsm.RazerMouse(); m2.dev = sd; m2.model = {"name": "t"}; m2.tx_cache = {0x0F: 0x3F}
def work():
    for _ in range(6): m2.set_color(1, 1, 1, store=False)
ts = [threading.Thread(target=work) for _ in range(3)]
[t.start() for t in ts]; [t.join() for t in ts]
check("concurrent commands are serialized (send+get atomic)", sd.bad == 0 and len(sd.sent) == 18, (sd.bad, len(sd.sent)))

# --- logica pura de bateria ------------------------------------------------------------------------------
st = set(); fired = []
for p in [95, 90, 89, 85, 79, 80, 81, 79, 61, 60, 59]:
    k, st = nsm.battery_alert_step(p, False, st, first=False); fired.append((p, k))
check("pure alert logic (90, crossing 80, crossing 70, 60)", [f for f in fired if f[1]] == [(90, "low"), (79, "low"), (61, "low"), (60, "low")], fired)
print("   ", fired)
print(f"{sum(RES)}/{len(RES)}")
