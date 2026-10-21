import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from simharness import *
SC = os.environ.get("SC", "ok")
write_cfg({"last_version": nsm.APP_VERSION, "welcomed": True, "lang_en_default": True, "control_verified": True})
sim = SimMouse(seed=1)
sim.latency = float(os.environ.get("LAT", "0.0"))
def drv(root, api, sim):
    wait_for(root, lambda: api["ctrl_on"][0], 10)
    if SC == "busy": sim.busy_n = 10**9
    if SC == "unplugged": sim.plugged = False
    if SC == "listener_off": pass
    worst = 0; t_end = time.time() + 12; gaps = []
    while time.time() < t_end:
        t0 = time.time(); root.update(); dt = time.time() - t0
        gaps.append(dt); time.sleep(0.005)
    gaps.sort()
    print(f"[{SC} lat={sim.latency}] worst UI freeze {gaps[-1]*1000:.0f} ms, p99 {gaps[int(len(gaps)*0.99)]*1000:.0f} ms, freezes>100ms: {sum(1 for g in gaps if g > 0.1)}")
run(drv, sim)
