import sys, os, threading, tempfile, importlib.util, http.server
spec = importlib.util.spec_from_file_location("nsm", __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "Non_Synapse_Mouse.py"))
nsm = importlib.util.module_from_spec(spec); sys.modules["nsm"] = nsm; spec.loader.exec_module(nsm)
R=[]
def ck(n,c,i=""): R.append(bool(c)); print(("PASS " if c else "FAIL ")+n+(f"  [{i}]" if not c else ""))
GOOD = b"MZ" + os.urandom(200000)
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/good.exe":
            self.send_response(200); self.send_header("Content-Length", str(len(GOOD))); self.end_headers(); self.wfile.write(GOOD)
        elif self.path == "/cut.exe":
            self.send_response(200); self.send_header("Content-Length", str(len(GOOD))); self.end_headers(); self.wfile.write(GOOD[:5000])
        elif self.path == "/html.exe":
            b = b"<html>rate limited</html>"; self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
d = tempfile.mkdtemp()
os.environ.pop("http_proxy", None); os.environ.pop("HTTP_PROXY", None); os.environ["no_proxy"] = "127.0.0.1"
nsm.download_file(f"http://127.0.0.1:{port}/good.exe", os.path.join(d, "a.exe"))
ck("download: complete file saved", open(os.path.join(d, "a.exe"), "rb").read() == GOOD)
for name, label in (("cut", "truncated"), ("html", "not an exe")):
    try:
        nsm.download_file(f"http://127.0.0.1:{port}/{name}.exe", os.path.join(d, name + ".exe")); ok = False
    except Exception as e:
        ok = True
    ck(f"download: {label} is rejected", ok and not os.path.exists(os.path.join(d, name + ".exe")))
    ck(f"download: {label} leaves no .part", not os.path.exists(os.path.join(d, name + ".exe.part")))
pv = nsm.parse_version
ck("version: 1.4.0 > 1.0.0", pv("v1.4.0") > pv("v1.0.0"))
ck("version: 1.10.0 > 1.9.3", pv("v1.10.0") > pv("1.9.3"))
ck("version: junk tag is (0,)", pv("latest") == (0,))
ck("version: suffix tolerated", pv("v1.4.0-beta") == (1, 4, 0))
# configuracion: guardado atomico + .bak
nsm.CONFIG_DIR = d; nsm.CONFIG_PATH = os.path.join(d, "c.json"); nsm.LEGACY_CONFIG_PATH = os.path.join(d, "legacy.json")
nsm.save_presets({"a": 1}); nsm.save_presets({"lang": "es"})
open(nsm.CONFIG_PATH, "w").write('{"lang": "e')                     # archivo roto (corte de luz)
ck("config: broken file -> last good backup", nsm.load_presets() == {"a": 1}, nsm.load_presets())
ck("config: sanitize drops wrong types", nsm.sanitize_presets({"lang": 3, "tray": "yes", "sniper_dpi": 450, "profiles": [800, "x", 0, 1600, 99999]}) ==
   {"sniper_dpi": 450, "profiles": [800, None, None, 1600, None]})
ck("config: a list instead of a dict -> {}", nsm.sanitize_presets([1, 2]) == {})
srv.shutdown()
print(f"{sum(R)}/{len(R)}")
