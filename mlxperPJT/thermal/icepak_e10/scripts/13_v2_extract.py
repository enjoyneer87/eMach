# -*- coding: utf-8 -*-
"""V2(e10bars, 클립 discrete 바) STEADY 이미 풀림 → 빠른 온도추출.
코일 리스트 통째 1콜(실패시 샘플링). stator/rotor/magnet/shaft.
"""
import os, json, traceback
SP=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ=r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
LOG=os.path.join(SP,"e10_v2_extract.txt")
_l=open(LOG,"w",encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a)+"\n"); _l.flush()
stator="Stator_Lamination_Primitive"; rotor="Rotor_Lamination_Primitive"; shaft="Shaft"
try:
    from ansys.aedt.core import Icepak
    DES2=open(os.path.join(SP,"v2_design.txt")).read().strip()
    ipk=Icepak(project=PROJ,design=DES2,version="2026.1",non_graphical=True,new_desktop=True)
    P("opened",DES2,ipk.solution_type,"solved:",ipk.setups[0].is_solved if ipk.setups else "?")
    names=list(ipk.modeler.object_names)
    coils=[n for n in names if n.startswith("Ph")]; magnets=[n for n in names if "Magnet" in n]
    sol=ipk.existing_analysis_sweeps[0] if ipk.existing_analysis_sweeps else "SolveSS : SteadyState"
    P("sweep",sol,"coils",len(coils))
    def gextr(o):
        for q in ("Temp","Temperature"):
            try:
                r=ipk.post.get_field_extremum(o,"Max","Volume",q,setup=sol)
                if isinstance(r,(list,tuple)): return round(float(r[1]),1)
            except Exception: pass
        return None
    # 코일 max: 리스트 통째 1콜 시도
    cmax=gextr(coils)
    P("coil list-call max:",cmax)
    if cmax is None:
        # 샘플 20바
        vals=[gextr(c) for c in coils[::7]]
        vals=[v for v in vals if v is not None]
        cmax=max(vals) if vals else None
        P("coil sampled max:",cmax,"n",len(vals))
    res={"_model":"V2 Icepak: discrete 구리바 k387(엔드턴 클립, active바)+함침k0.13+대류벽 오일회로, STEADY",
         "_note":"전체하이핀은 메시불가(엔드턴 39264facet) → z±75 클립. 슬롯내 discrete 구리+함침 전도 검증.",
         "coil":cmax,"stator":gextr(stator),"rotor":gextr(rotor),"shaft":gextr(shaft)}
    if magnets: res["magnet"]=gextr(magnets[0])
    P("V2 STEADY:",res)
    json.dump(res,open(os.path.join(SP,"e10_v2_steady.json"),"w"),indent=2,ensure_ascii=False)
    # downstream(대시보드)용 data 폴더에도 at_900s 포맷으로
    OUT=r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_icepak_v2_bars.json"
    d2={"_model":res["_model"],"_note":res["_note"],"_basis":"STEADY(포화)=transient@900s 등가",
        "at_900s":{"coil":{"max":cmax},"stator":{"max":res["stator"]},"rotor":{"max":res["rotor"]},
                   "shaft":{"max":res["shaft"]},"magnet":{"max":res.get("magnet")}}}
    json.dump(d2,open(OUT,"w",encoding="utf-8"),indent=2,ensure_ascii=False)
    P("saved",OUT)
    if cmax is not None and cmax<800: P("VERDICT: V2-COOLED-OK (discrete 클립바 컨포멀!) coil=",cmax)
    elif cmax is not None: P("VERDICT: V2-RUNAWAY coil=",cmax)
    else: P("VERDICT: V2-NO-TEMP")
    P("DONE")
except Exception:
    P("EXC:",traceback.format_exc())
finally:
    try: ipk.release_desktop(close_projects=True,close_desktop=True)
    except Exception: pass
os._exit(0)
