# -*- coding: utf-8 -*-
"""Start a NEW hidden Motor-CAD instance for a script (never attach to the user's window).

    from mc_launch import launch, mc_pids
    mc = launch(mot_path, tag)          # retries 3x ("Failed to find Motor-CAD port" when several start at once)

PIDs of the instances this helper started are appended to PIDS, so a later session can clean up only its
own orphans. Moved here from a session scratchpad (lab_existing.py, 2026-09-17) so that
export_lab_satmap.py and fea_posmap.py do not depend on a temporary file.
"""
import io
import os
import time

import psutil

PIDS = r"D:\KangDH\Thesis\e10\work_lab_pc1\motorcad_pids.txt"


def mc_pids():
    out = set()
    for p in psutil.process_iter(["name"]):
        try:
            if (p.info["name"] or "").lower() == "motorcad.exe":
                out.add(p.pid)
        except psutil.Error:
            pass
    return out


def launch(mot, tag):
    import ansys.motorcad.core as pymotorcad
    before = mc_pids()
    mc = None
    for attempt in range(1, 4):
        try:
            mc = pymotorcad.MotorCAD(open_new_instance=True, enable_success_variable=False)
            break
        except Exception as exc:
            print("[%s] start failed %d/3: %r" % (tag, attempt, exc), flush=True)
            for pid in sorted(mc_pids() - before):      # only instances left behind by this failed start
                try:
                    psutil.Process(pid).kill()
                except Exception:
                    pass
            time.sleep(30*attempt)
    if mc is None:
        raise RuntimeError("Motor-CAD failed to start 3 times")
    mine = sorted(mc_pids() - before)
    os.makedirs(os.path.dirname(PIDS), exist_ok=True)
    io.open(PIDS, "a", encoding="utf-8").write("%s %s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), tag, mine))
    for setter, args in (("set_variable", ("MessageDisplayState", 2)), ("set_visible", (False,))):
        try:
            getattr(mc, setter)(*args)
        except Exception:
            pass
    mc.load_from_file(mot)
    print("[%s] PID %s  mot=%s" % (tag, mine, os.path.basename(mot)), flush=True)
    return mc
