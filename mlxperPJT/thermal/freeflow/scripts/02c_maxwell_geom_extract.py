# -*- coding: utf-8 -*-
"""e10 Maxwell 2D에서 로터적층/자석/샤프트/스테이터/권선 2D 단면 폴리곤 추출 -> JSON."""
import os, json, traceback
SP=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
AEDT=r"D:\KDH\simVary\e10_20251226\e10_User_2D_GF0_RD1AS0AC1WG0HCT1HET0_ANSYSEM_2D.aedt"
LOG=os.path.join(SP,"e10_geom.txt"); OUT=os.path.join(SP,"e10_geom.json")
_l=open(LOG,"w",encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a)+"\n"); _l.flush()
try:
    from ansys.aedt.core import Maxwell2d
    P("opening", AEDT)
    app=Maxwell2d(project=AEDT, non_graphical=True, new_desktop=True, close_on_exit=False)
    P("design:", app.design_name, "type:", app.solution_type)
    mdl=app.modeler
    objs=mdl.object_names
    P("n objects:", len(objs))
    data={"objects":{}}
    for nm in objs:
        try:
            o=mdl[nm]
            mat=getattr(o,"material_name",None)
            # 2D 객체 정점(폴리곤): edges->vertices
            verts=[]
            try:
                for v in o.vertices:
                    verts.append([float(v.position[0]), float(v.position[1])])
            except Exception: pass
            bb=None
            try: bb=[float(x) for x in o.bounding_box]
            except Exception: pass
            data["objects"][nm]=dict(material=mat, nverts=len(verts), verts=verts, bbox=bb)
            P(f"  {nm}: mat={mat} nverts={len(verts)} bbox={bb}")
        except Exception as e:
            P(f"  {nm}: ERR {repr(e)[:80]}")
    json.dump(data, open(OUT,"w",encoding="utf-8"), indent=1, ensure_ascii=False)
    P("saved", OUT)
    P("DONE-OK")
    try: app.release_desktop(close_projects=False, close_desktop=True)
    except Exception: pass
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    _l.close(); os._exit(0)
