# -*- coding: utf-8 -*-
"""e10 Icepak analyze=False 원인 규명: 엔진 메시지(GetMessages) + generate_mesh 명시 + 재솔브."""
import os, glob, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
LOG = os.path.join(SP, "e10_ipk_whyfail.txt")
_l = open(LOG, "w", encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a)+"\n"); _l.flush()
def dump_msgs(ipk, tag):
    for sev in (2,1):
        try:
            m = ipk.odesktop.GetMessages(ipk.project_name, ipk.design_name, sev) or []
            P(f"--- [{tag}] GetMessages sev{sev} ({len(m)}) ---")
            for x in list(m)[-20:]: P("   ", str(x)[:300])
        except Exception as e: P(f"[{tag}] GetMessages sev{sev} EXC", repr(e)[:80])
try:
    from ansys.aedt.core import Icepak
    ipk = Icepak(project=PROJ, design="e10_net", version="2026.1",
                 non_graphical=True, new_desktop=True)
    P("opened. soltype:", ipk.solution_type, "problem:", ipk.problem_type, "setups:", ipk.setup_names)
    dump_msgs(ipk, "on-open")

    # 명시적 메시 생성
    setup = ipk.setup_names[0] if ipk.setup_names else None
    P("setup:", setup)
    try:
        mok = ipk.mesh.generate_mesh(setup)
        P("generate_mesh:", mok)
    except Exception as e: P("generate_mesh EXC:", repr(e)[:150])
    dump_msgs(ipk, "after-mesh")

    # 재솔브 시도
    try:
        ok = ipk.analyze_setup(setup, cores=8)
        P("analyze:", ok)
    except Exception as e: P("analyze EXC:", repr(e)[:150])
    dump_msgs(ipk, "after-analyze")
    try: P("is_solved:", ipk.setups[0].is_solved)
    except Exception: pass
    NDIR = PROJ.replace(".aedt",".aedtresults")+r"\e10_net.results"
    tot=sum(os.path.getsize(f) for f in glob.glob(os.path.join(NDIR,"**","*"),recursive=True) if os.path.isfile(f))
    P("결과크기 MB:", round(tot/1e6,1))
    P("DONE-OK")
    ipk.release_desktop(close_projects=True, close_desktop=True)
except Exception:
    P("EXC:", traceback.format_exc())
os._exit(0)
