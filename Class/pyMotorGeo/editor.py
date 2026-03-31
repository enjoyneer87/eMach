"""
pyMotorGeo.editor
=================
인터랙티브 영역 편집 GUI.
"""

import math
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Patch, Arc as MplArc
from matplotlib.path import Path
from typing import Dict, Tuple

from core import StatorRotorSplit
from regions import REGION_NAMES, REGION_COLORS, SHORT_NAMES, _compute_face_geometry
from plotting import _render_face_patch


def interactive_region_editor(half_unit_regions: Dict,
                              half_unit: Dict,
                              split: StatorRotorSplit,
                              origin: Tuple[float, float] = (0.0, 0.0),
                              figsize: Tuple = (14, 12)):
    """
    반슬롯/반극 영역을 인터랙티브로 선택·이름 변경·병합할 수 있는 GUI.
    
    기능:
      - 클릭하여 영역 선택 (노란 테두리 하이라이트)
      - 키보드: y=yoke, t=tooth, s=slot, o=slot_opening,
               r=rotor_core, m=magnet, a=air_barrier, h=shaft
      - 'p': 선택된 두 영역 병합
      - 'q': 종료
    
    Parameters
    ----------
    half_unit_regions : Dict
        classify_half_unit_regions 결과
    half_unit : Dict
        extract_half_unit 결과
    split : StatorRotorSplit
        고정자/회전자 분리 결과
    origin : Tuple[float, float]
        원점 좌표
    figsize : Tuple
        그림 크기
    
    Returns
    -------
    Dict
        편집 상태 (fig, ax, all_faces, state, half_unit_regions)
    """
    ox, oy = origin
    all_faces = (half_unit_regions['stator_faces'] +
                 half_unit_regions['rotor_faces'])

    for i, fi in enumerate(all_faces):
        fi['_id'] = i

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    ax.set_title('Interactive Region Editor — Click to select, press key to rename\n'
                 'y=Yoke t=Tooth s=Slot o=SlotOp r=RotCore m=Magnet a=AirBarrier h=Shaft | q=Quit',
                 fontsize=10)
    ax.grid(True, lw=0.3, alpha=0.4)

    patches_map = {}
    s_emap = half_unit_regions['stator_edge_map']
    r_emap = half_unit_regions['rotor_edge_map']

    # 와이어프레임
    for ei in half_unit['half_slot_stator'] + half_unit['half_pole_rotor']:
        xs = [p[0] for p in ei.points]
        ys = [p[1] for p in ei.points]
        if ei.etype == 'LINE':
            ax.plot(xs, ys, color='#999', lw=0.3, zorder=1)
        elif ei.etype == 'ARC' and ei.center and ei.radius:
            ax.add_patch(MplArc(
                ei.center, 2 * ei.radius, 2 * ei.radius,
                angle=0, theta1=ei.start_angle, theta2=ei.end_angle,
                ec='#999', lw=0.3, zorder=1))

    for ei in half_unit['concentric_circles']:
        if ei.etype == 'CIRCLE' and ei.center and ei.radius:
            ax.add_patch(plt.Circle(ei.center, ei.radius, fill=False,
                                    ec='#2ecc71', lw=0.6, zorder=1))

    def _draw_all():
        for pid, p in patches_map.items():
            p.remove()
        patches_map.clear()
        for fi in all_faces:
            emap = s_emap if fi.get('part') == 'stator' else r_emap
            patch, _ = _render_face_patch(ax, fi, emap, alpha=0.65, zorder=3)
            patches_map[fi['_id']] = patch
        for child in list(ax.texts):
            child.remove()
        for fi in all_faces:
            nv = len(fi['vertices'])
            cx = sum(v[0] for v in fi['vertices']) / nv
            cy = sum(v[1] for v in fi['vertices']) / nv
            label = f"{fi['_id']}:{SHORT_NAMES.get(fi.get('name'), '?')}"
            fs = 6 if fi.get('area', 0) < 50 else 8
            ax.text(cx, cy, label, fontsize=fs, ha='center', va='center',
                    fontweight='bold', zorder=5,
                    bbox=dict(boxstyle='round,pad=0.15', fc='white',
                              alpha=0.7, ec='none'))
        fig.canvas.draw_idle()

    _draw_all()

    state = {'selected': None, 'selected_ids': [], 'done': False}
    KEY_MAP = {
        'y': 'stator_yoke', 't': 'stator_tooth',
        's': 'slot', 'o': 'slot_opening',
        'r': 'rotor_core', 'm': 'magnet',
        'a': 'air_barrier', 'h': 'shaft',
    }

    def on_click(event):
        if event.inaxes != ax:
            return
        mx, my = event.xdata, event.ydata
        clicked_fi = None
        for fi in all_faces:
            path = Path(fi['vertices'])
            if path.contains_point((mx, my)):
                clicked_fi = fi
                break
        if clicked_fi is None:
            return
        fid = clicked_fi['_id']
        if state['selected'] is not None and state['selected'] in patches_map:
            patches_map[state['selected']].set_edgecolor('black')
            patches_map[state['selected']].set_linewidth(0.6)
        state['selected'] = fid
        if fid not in state['selected_ids']:
            state['selected_ids'].append(fid)
        patches_map[fid].set_edgecolor('yellow')
        patches_map[fid].set_linewidth(3.0)
        name = clicked_fi.get('name', 'unknown')
        print(f'  [선택] id={fid}, name={REGION_NAMES.get(name, name)}, '
              f'area={clicked_fi.get("area", 0):.1f}')
        fig.canvas.draw_idle()

    def on_key(event):
        if event.key == 'q':
            state['done'] = True
            plt.close(fig)
            return
        if state['selected'] is None:
            return
        sel_fi = next((f for f in all_faces if f['_id'] == state['selected']), None)
        if sel_fi is None:
            return
        if event.key in KEY_MAP:
            old_name = sel_fi.get('name', 'unknown')
            new_name = KEY_MAP[event.key]
            sel_fi['name'] = new_name
            print(f'  [이름변경] id={sel_fi["_id"]}: '
                  f'{REGION_NAMES.get(old_name, old_name)} → '
                  f'{REGION_NAMES.get(new_name, new_name)}')
            _draw_all()
        elif event.key == 'p':
            if len(state['selected_ids']) >= 2:
                id1 = state['selected_ids'][-2]
                id2 = state['selected_ids'][-1]
                fi1 = next((f for f in all_faces if f['_id'] == id1), None)
                fi2 = next((f for f in all_faces if f['_id'] == id2), None)
                if fi1 and fi2:
                    fi1['vertices'] = fi1['vertices'] + fi2['vertices']
                    fi1['area'] = fi1.get('area', 0) + fi2.get('area', 0)
                    _compute_face_geometry(fi1, origin)
                    all_faces.remove(fi2)
                    state['selected_ids'] = [id1]
                    state['selected'] = id1
                    print(f'  [병합] id={id1} + id={id2} → id={id1}')
                    _draw_all()

    fig.canvas.mpl_connect('button_press_event', on_click)
    fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show()

    return {
        'fig': fig, 'ax': ax,
        'all_faces': all_faces,
        'state': state,
        'half_unit_regions': half_unit_regions,
    }


def finalize_region_editor(editor_state: Dict):
    """
    인터랙티브 편집 완료 후 결과를 half_unit_regions에 반영합니다.
    GUI에서 편집을 마친 뒤 이 함수를 별도 셀에서 호출하세요.
    
    Parameters
    ----------
    editor_state : Dict
        interactive_region_editor 반환값
    
    Returns
    -------
    Dict
        업데이트된 half_unit_regions
    """
    all_faces = editor_state['all_faces']
    half_unit_regions = editor_state['half_unit_regions']

    half_unit_regions['stator_faces'] = [f for f in all_faces if f.get('part') == 'stator']
    half_unit_regions['rotor_faces'] = [f for f in all_faces if f.get('part') == 'rotor']
    print('\n[finalize_region_editor] 편집 확정 완료')
    for fi in all_faces:
        print(f'  id={fi["_id"]:2d}  {REGION_NAMES.get(fi.get("name"), "?"):20s}  '
              f'area={fi.get("area", 0):8.1f}')
    return half_unit_regions
