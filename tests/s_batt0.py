import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from simharness import *
R=[]
def ck(n,c,i=""): R.append(bool(c)); print(("PASS " if c else "FAIL ")+n+(f"  [{i}]" if not c else ""))
MODE = os.environ.get("SC", "zero")
def drv(root, api, sim):
    seen = []
    end = time.time() + 9
    while time.time() < end:
        root.update(); time.sleep(0.02)
        b = api["state_batt"][0]
        if b is not None and (not seen or seen[-1] != b): seen.append(b)
        txt = api["dev_sub"].cget("text")
        if (" 0 %" in txt or "· 0%" in txt) and ("LABEL", txt) not in seen: seen.append(("LABEL", txt))
    print("   battery values shown:", seen)
    ck(f"[{MODE}] never shows 0 % / wrong value", all(isinstance(v, tuple) and v[0] == sim.pct() for v in seen if v and v[0] != "LABEL") and not any(v[0]=="LABEL" for v in seen), seen)
    ck(f"[{MODE}] finally shows the real level", api["state_batt"][0] == (sim.pct(), False), api["state_batt"][0])
    ck(f"[{MODE}] connected", api["state_conn"][0] is not None)
write_cfg({"last_version": nsm.APP_VERSION, "welcomed": True, "lang_en_default": True, "batt_alert": True})
sim = SimMouse(seed=3)
if MODE == "zero": sim.zero_batt_n = 2
if MODE == "stale": sim.stale_p = 0.35
if MODE == "timeout": sim.timeout_until = time.time() + 3.0
if MODE == "busy": sim.busy_n = 12
if MODE == "all": sim.zero_batt_n = 2; sim.stale_p = 0.3; sim.empty_p = 0.1; sim.busy_n = 6
r = run(drv, sim)
if not r["ok"]: print(r["err"])
for e in ERRORS: print(e[:600])
print(f"{sum(R)}/{len(R)}  errors={len(ERRORS)}")
