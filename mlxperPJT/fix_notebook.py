"""Fix corrupted cell #VSC-0f8670c6 in pyMotorGeo_v1.ipynb"""
import json, re

nb_path = r"d:\KangDH\Emlab_emach\mlxperPJT\pyMotorGeo_v1.ipynb"

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find cell #VSC-0f8670c6
target_cell = None
for cell in nb['cells']:
    meta = cell.get('metadata', {})
    cid = meta.get('vscode', {}).get('languageId', '') or ''
    cell_id = cell.get('id', '')
    # Check source for the cell marker
    src = ''.join(cell.get('source', []))
    if 'CELL-02' in src and 'classify_half_unit_regions' in src:
        target_cell = cell
        break

if target_cell is None:
    print("ERROR: Target cell not found!")
    exit(1)

# Join all source lines
full_source = ''.join(target_cell['source'])

# Find the boundary: after "_compute_face_geometry(fi, origin)" in the classify function
# We want to keep everything before the stator classification and replace from there

# Marker: the clean code ends with this pattern
marker = "    # r_min, r_max, r_span 등 기하 특성 추가\n    for fi in s_faces:\n        _compute_face_geometry(fi, origin)\n"

idx = full_source.find(marker)
if idx < 0:
    print("ERROR: Could not find clean boundary marker!")
    exit(1)

clean_prefix = full_source[:idx + len(marker)]

# The new replacement code (from stator classification to end of cell)
new_suffix = '''
    # ═══════ 고정자 분류 ═══════
    s_by_area = sorted(s_faces, key=lambda f: f['area'], reverse=True)

    if s_by_area:
        for fi in s_faces:
            if abs(fi['r_max'] - r_stator_outer) < 2.0:
                fi['name'] = 'stator_yoke'
            elif is_inner and abs(fi['r_min'] - r_ag_out) < 3.0 and fi['area'] < 200:
                fi['name'] = 'slot_opening'
            elif not is_inner and abs(fi['r_max'] - r_ag_in) < 3.0 and fi['area'] < 200:
                fi['name'] = 'slot_opening'
            else:
                fi['name'] = '_stator_unclassified'

        unclassified_s = [fi for fi in s_faces if fi['name'] == '_stator_unclassified']
        if unclassified_s:
            unc_sorted = sorted(unclassified_s, key=lambda f: f['area'], reverse=True)
            unc_sorted[0]['name'] = 'slot'
            for fi in unc_sorted[1:]:
                if fi['r_span'] > 10 and fi['area'] > 50:
                    fi['name'] = 'stator_tooth'
                else:
                    fi['name'] = 'slot_opening'

        for fi in s_faces:
            if fi.get('name', '').startswith('_'):
                fi['name'] = 'slot_opening'

    # ═══════ 반극 회전자 영역 ═══════
    for fi in r_faces:
        _compute_face_geometry(fi, origin)

    r_by_area = sorted(r_faces, key=lambda f: f['area'], reverse=True)

    if r_by_area:
        for fi in r_faces:
            if is_inner:
                if fi['r_max'] <= r_shaft + 1.0:
                    fi['name'] = 'shaft'
                else:
                    fi['name'] = '_rotor_unclassified'
            else:
                fi['name'] = '_rotor_unclassified'

        unclassified_r = [fi for fi in r_faces if fi['name'] == '_rotor_unclassified']
        if unclassified_r:
            unc_r_sorted = sorted(unclassified_r, key=lambda f: f['area'], reverse=True)
            unc_r_sorted[0]['name'] = 'rotor_core'

            pockets = unc_r_sorted[1:]
            if pockets:
                pocket_areas = sorted([fi['area'] for fi in pockets], reverse=True)
                n_pockets = len(pockets)

                if topo == 'SPMSM':
                    for fi in pockets:
                        fi['name'] = 'magnet'
                elif topo == 'PMa-SynRM':
                    if n_pockets >= 2:
                        total_pa = sum(pocket_areas)
                        gaps = [(pocket_areas[i] - pocket_areas[i+1], i)
                                for i in range(n_pockets-1)]
                        max_gap, si = max(gaps, key=lambda x: x[0])
                        thresh = (pocket_areas[si] + pocket_areas[si+1]) / 2
                        small_a = sum(a for a in pocket_areas if a < thresh)
                        if small_a / total_pa < 0.3 and max_gap > pocket_areas[-1]:
                            for fi in pockets:
                                fi['name'] = 'magnet' if fi['area'] < thresh else 'air_barrier'
                        else:
                            for fi in pockets:
                                fi['name'] = 'air_barrier'
                    else:
                        pockets[0]['name'] = 'air_barrier'
                else:  # IPMSM
                    if n_pockets >= 2:
                        gaps = [(pocket_areas[i] - pocket_areas[i+1], i)
                                for i in range(n_pockets-1)]
                        if gaps:
                            max_gap, si = max(gaps, key=lambda x: x[0])
                            thresh = (pocket_areas[si] + pocket_areas[si+1]) / 2
                            if max_gap > pocket_areas[-1] * 0.5:
                                for fi in pockets:
                                    fi['name'] = 'magnet' if fi['area'] >= thresh else 'air_barrier'
                            else:
                                for fi in pockets:
                                    fi['name'] = 'magnet'
                        else:
                            for fi in pockets:
                                fi['name'] = 'magnet'
                    elif n_pockets == 1:
                        pockets[0]['name'] = 'magnet'

        for fi in r_faces:
            if fi.get('name', '').startswith('_'):
                fi['name'] = 'unknown'

    # ── 결과 요약 ──
    all_faces = s_faces + r_faces
    print(f'\\n[classify_half_unit_regions] 반슬롯/반극 기준 영역 분류 (topology={topo}):')
    print(f'  고정자(반슬롯): {len(s_faces)}개 영역')
    for fi in sorted(s_faces, key=lambda f: f['area'], reverse=True):
        print(f'    {REGION_NAMES.get(fi["name"], fi["name"]):20s} '
              f'area={fi["area"]:8.1f}  r=[{fi["r_min"]:.1f}~{fi["r_max"]:.1f}]')
    print(f'  회전자(반극):   {len(r_faces)}개 영역')
    for fi in sorted(r_faces, key=lambda f: f['area'], reverse=True):
        print(f'    {REGION_NAMES.get(fi["name"], fi["name"]):20s} '
              f'area={fi["area"]:8.1f}  r=[{fi["r_min"]:.1f}~{fi["r_max"]:.1f}]')

    return {
        'stator_faces': s_faces,
        'rotor_faces': r_faces,
        'stator_adj': shared_adj,
        'stator_edge_map': shared_emap,
        'rotor_adj': shared_adj,
        'rotor_edge_map': shared_emap,
    }


# ═══════════════════════════════════════════════════════════════
# 14) 반슬롯/반극 네이밍 시각화 + 재구성 + 인터랙티브 GUI
# ═══════════════════════════════════════════════════════════════

def _render_face_patch(ax, fi, edge_to_entity, alpha=0.7, zorder=3):
    """face 한 개를 ARC 반영하여 패치로 그립니다."""
    from matplotlib.patches import Polygon as MplPolygon
    verts = fi['vertices']
    nv = len(verts)
    name = fi.get('name', 'unknown')
    color = REGION_COLORS.get(name, '#D0D0D0')

    poly_pts = []
    for j in range(nv):
        k0 = verts[j]
        k1 = verts[(j + 1) % nv]
        edge_key = tuple(sorted([k0, k1]))
        ei = edge_to_entity.get(edge_key, None)
        seg_pts = _edge_to_patch_points(ei, k0, k1)
        if j == 0:
            poly_pts.extend(seg_pts)
        else:
            poly_pts.extend(seg_pts[1:])

    patch = MplPolygon(poly_pts, closed=True, fc=color,
                       ec='black', lw=0.6, alpha=alpha, zorder=zorder)
    ax.add_patch(patch)
    return patch, poly_pts


def _transform_face(fi, transform_fn):
    """face의 vertices를 좌표 변환한 새 face dict를 반환."""
    new_fi = dict(fi)
    new_fi['vertices'] = [transform_fn(v[0], v[1]) for v in fi['vertices']]
    return new_fi


def plot_named_half_unit(half_unit_regions, half_unit, split,
                         origin=(0.0, 0.0), figsize=(10, 10)):
    """반슬롯/반극의 네이밍된 영역을 시각화합니다."""
    from matplotlib.patches import Patch

    ox, oy = origin
    fig, axes = plt.subplots(1, 2, figsize=(figsize[0]*2, figsize[1]))

    for ax_idx, (part, title_str) in enumerate([
            ('stator', f'Half-Slot Stator ({half_unit["half_slot_deg"]:.1f}\\u00b0)'),
            ('rotor', f'Half-Pole Rotor ({half_unit["half_pole_deg"]:.1f}\\u00b0)')]):
        ax = axes[ax_idx]
        faces = half_unit_regions[f'{part}_faces']
        emap = half_unit_regions[f'{part}_edge_map']

        ents = (half_unit['half_slot_stator'] if part == 'stator'
                else half_unit['half_pole_rotor'])
        for ei in ents:
            xs = [p[0] for p in ei.points]
            ys = [p[1] for p in ei.points]
            if ei.etype == 'LINE':
                ax.plot(xs, ys, color='#888', lw=0.4, zorder=1)
            elif ei.etype == 'ARC' and ei.center and ei.radius:
                ax.add_patch(plt.matplotlib.patches.Arc(
                    ei.center, 2*ei.radius, 2*ei.radius,
                    angle=0, theta1=ei.start_angle, theta2=ei.end_angle,
                    ec='#888', lw=0.4, zorder=1))

        used_names = set()
        for fi in faces:
            _render_face_patch(ax, fi, emap)
            used_names.add(fi.get('name', 'unknown'))
            nv = len(fi['vertices'])
            cx = sum(v[0] for v in fi['vertices']) / nv
            cy = sum(v[1] for v in fi['vertices']) / nv
            label = SHORT_NAMES.get(fi.get('name'), '?')
            fs = 6 if fi['area'] < 50 else 8
            ax.text(cx, cy, label, fontsize=fs, ha='center', va='center',
                    fontweight='bold', zorder=5,
                    bbox=dict(boxstyle='round,pad=0.15', fc='white',
                              alpha=0.7, ec='none'))

        legend_els = [Patch(fc=REGION_COLORS.get(n, '#D0D0D0'), alpha=0.7, ec='k',
                            label=REGION_NAMES.get(n, n))
                      for n in sorted(used_names)]
        ax.legend(handles=legend_els, loc='upper left', fontsize=7)
        ax.set_aspect('equal')
        ax.set_title(title_str, fontsize=11, fontweight='bold')
        ax.grid(True, lw=0.3, alpha=0.4)

    plt.tight_layout()
    plt.show()
    return fig, axes


def plot_reconstructed_named(half_unit, half_unit_regions, split,
                             origin=(0.0, 0.0), coverage='period',
                             n_poles=None, n_slots=None,
                             period_deg=None, figsize=(12, 12)):
    """반슬롯/반극 영역을 mirror + circular pattern으로 재구성하여 시각화."""
    from matplotlib.patches import Polygon as MplPolygon, Patch

    ox, oy = origin
    half_slot_deg = half_unit['half_slot_deg']
    half_pole_deg = half_unit['half_pole_deg']
    slot_pitch = half_unit['slot_pitch_deg']
    pole_pitch = half_unit['pole_pitch_deg']
    ref_start = half_unit['ref_angle_start']

    if coverage == 'full':
        target_deg = 360.0
    elif coverage == 'period':
        target_deg = period_deg if period_deg else 90.0
    else:
        target_deg = float(coverage)

    n_slots_to_build = max(1, round(target_deg / slot_pitch))
    n_poles_to_build = max(1, round(target_deg / pole_pitch))

    fig, ax = plt.subplots(figsize=figsize)

    def _draw_transformed_face(fi, transform_fn):
        new_fi = _transform_face(fi, transform_fn)
        name = new_fi.get('name', 'unknown')
        color = REGION_COLORS.get(name, '#D0D0D0')
        patch = MplPolygon(new_fi['vertices'], closed=True, fc=color,
                           ec='black', lw=0.4, alpha=0.65, zorder=3)
        ax.add_patch(patch)

    def _make_mirror_fn(axis_deg):
        rad = math.radians(axis_deg)
        def fn(x, y):
            return _mirror_point(x, y, rad, ox, oy)
        return fn

    def _make_rotate_fn(angle_deg):
        rad = math.radians(angle_deg)
        def fn(x, y):
            return _rotate_point(x, y, rad, ox, oy)
        return fn

    # 고정자: 반슬롯 -> mirror -> 1슬롯 -> circular
    s_faces = half_unit_regions['stator_faces']
    s_emap = half_unit_regions['stator_edge_map']
    mirror_s_axis = ref_start + half_slot_deg

    for i in range(n_slots_to_build):
        rot_angle = i * slot_pitch
        for fi in s_faces:
            if i == 0:
                _render_face_patch(ax, fi, s_emap, alpha=0.65)
            else:
                _draw_transformed_face(fi, _make_rotate_fn(rot_angle))
            if i == 0:
                mirror_fn = _make_mirror_fn(mirror_s_axis)
            else:
                def mirror_then_rotate(x, y, _mf=_make_mirror_fn(mirror_s_axis),
                                       _rf=_make_rotate_fn(rot_angle)):
                    mx, my = _mf(x, y)
                    return _rf(mx, my)
                mirror_fn = mirror_then_rotate
            _draw_transformed_face(fi, mirror_fn)

    # 회전자: 반극 -> mirror -> 1극 -> circular
    r_faces = half_unit_regions['rotor_faces']
    r_emap = half_unit_regions['rotor_edge_map']
    mirror_r_axis = ref_start + half_pole_deg

    for i in range(n_poles_to_build):
        rot_angle = i * pole_pitch
        for fi in r_faces:
            if i == 0:
                _render_face_patch(ax, fi, r_emap, alpha=0.65)
            else:
                _draw_transformed_face(fi, _make_rotate_fn(rot_angle))
            if i == 0:
                mirror_fn = _make_mirror_fn(mirror_r_axis)
            else:
                def mirror_then_rotate(x, y, _mf=_make_mirror_fn(mirror_r_axis),
                                       _rf=_make_rotate_fn(rot_angle)):
                    mx, my = _mf(x, y)
                    return _rf(mx, my)
                mirror_fn = mirror_then_rotate
            _draw_transformed_face(fi, mirror_fn)

    # 동심원 경계
    for ei in half_unit['concentric_circles']:
        if ei.etype == 'CIRCLE' and ei.center and ei.radius:
            ax.add_patch(plt.Circle(ei.center, ei.radius, fill=False,
                                    ec='#2ecc71', lw=0.8, zorder=2))
        elif ei.etype == 'ARC' and ei.center and ei.radius:
            ax.add_patch(plt.matplotlib.patches.Arc(
                ei.center, 2*ei.radius, 2*ei.radius,
                angle=0, theta1=ref_start, theta2=ref_start + target_deg,
                ec='#2ecc71', lw=0.8, zorder=2))

    # 경계선
    concentric_r = sorted(set(
        round(ei.radius, 2)
        for ei in split.stator_entities + split.rotor_entities
        if ei.etype in ('CIRCLE', 'ARC') and ei.center
        and math.hypot(ei.center[0]-ox, ei.center[1]-oy) < 1e-3
        and ei.radius))
    r_max = max(concentric_r) * 1.05 if concentric_r else 130

    if target_deg < 360:
        a1 = math.radians(ref_start)
        a2 = math.radians(ref_start + target_deg)
        ax.plot([ox, ox+r_max*math.cos(a1)], [oy, oy+r_max*math.sin(a1)],
                'r--', lw=0.6, alpha=0.7)
        ax.plot([ox, ox+r_max*math.cos(a2)], [oy, oy+r_max*math.sin(a2)],
                'r--', lw=0.6, alpha=0.7)

    all_faces = s_faces + r_faces
    used_names = sorted(set(fi.get('name', 'unknown') for fi in all_faces))
    legend_elements = [Patch(fc=REGION_COLORS.get(n, '#D0D0D0'), alpha=0.7, ec='k',
                             label=REGION_NAMES.get(n, n))
                       for n in used_names]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9, framealpha=0.9)

    ax.set_aspect('equal')
    ax.set_title(f'Named Regions \\u2014 {coverage} ({target_deg:.0f}\\u00b0)\\n'
                 f'{n_slots_to_build} slots \\u00d7 {n_poles_to_build} poles',
                 fontsize=12, fontweight='bold')
    ax.grid(True, lw=0.3, alpha=0.4)
    plt.tight_layout()
    plt.show()
    return fig, ax


# ═══════════════════════════════════════════════════════════════
# 15) 인터랙티브 영역 편집 GUI
# ═══════════════════════════════════════════════════════════════
def interactive_region_editor(half_unit_regions, half_unit, split,
                              origin=(0.0, 0.0), figsize=(14, 12)):
    """
    반슬롯/반극 영역을 인터랙티브로 선택·이름 변경·병합할 수 있는 GUI.

    기능:
      - 클릭하여 영역 선택 (노란 테두리 하이라이트)
      - 키보드: y=yoke, t=tooth, s=slot, o=slot_opening,
               r=rotor_core, m=magnet, a=air_barrier, h=shaft
      - 'p': 선택된 두 영역 병합
      - 'q': 종료
    """
    from matplotlib.patches import Polygon as MplPolygon, Patch

    ox, oy = origin
    all_faces = (half_unit_regions['stator_faces'] +
                 half_unit_regions['rotor_faces'])

    for i, fi in enumerate(all_faces):
        fi['_id'] = i

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    ax.set_title('Interactive Region Editor \\u2014 Click to select, press key to rename\\n'
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
            ax.add_patch(plt.matplotlib.patches.Arc(
                ei.center, 2*ei.radius, 2*ei.radius,
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
            from matplotlib.path import Path
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
                  f'{REGION_NAMES.get(old_name, old_name)} \\u2192 '
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
                    print(f'  [병합] id={id1} + id={id2} \\u2192 id={id1}')
                    _draw_all()

    fig.canvas.mpl_connect('button_press_event', on_click)
    fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show()

    half_unit_regions['stator_faces'] = [f for f in all_faces if f.get('part') == 'stator']
    half_unit_regions['rotor_faces'] = [f for f in all_faces if f.get('part') == 'rotor']
    print('\\n[interactive_region_editor] 편집 완료')
    for fi in all_faces:
        print(f'  id={fi["_id"]:2d}  {REGION_NAMES.get(fi.get("name"), "?"):20s}  '
              f'area={fi.get("area",0):8.1f}')
    return half_unit_regions


print("\\u2705 CELL-02 함수 정의 완료 (반슬롯/반극 네이밍 + 인터랙티브 GUI 포함)")
'''

new_source = clean_prefix + new_suffix

# Convert to notebook source format (list of lines ending with \n)
lines = new_source.split('\n')
source_lines = []
for i, line in enumerate(lines):
    if i < len(lines) - 1:
        source_lines.append(line + '\n')
    else:
        if line:  # don't add empty last line
            source_lines.append(line)

target_cell['source'] = source_lines

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"SUCCESS: Cell source updated. {len(source_lines)} lines written.")
print(f"Clean prefix ends at char {len(clean_prefix)}, new suffix has {len(new_suffix)} chars")
