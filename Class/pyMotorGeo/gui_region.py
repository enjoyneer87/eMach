"""
pyMotorGeo.gui_region
======================
닫힌 영역(face) 기반 인터랙티브 영역 할당 GUI.

matplotlib widget backend + ipywidgets 기반.
%matplotlib widget 환경에서 사용.

detect_closed_faces()로 탐지된 face(다각형)을 채색 표시하고,
클릭하면 해당 face를 선택 → 드롭다운으로 이름 재할당 → 즉시 색상 반영.

pyleecan의 DXF_Hole / SurfLine + label 개념을 참고:
  - 닫힌 영역(= SurfLine) 단위로 이름(label) 할당
  - 이름에 따라 색상이 자동으로 변경

사용 예시::

    from pyMotorGeo.region_closing import (
        detect_closed_faces, auto_name_faces, REGION_NAMES, REGION_COLORS,
    )
    from pyMotorGeo.gui_region import FaceRegionGUI

    faces = detect_closed_faces(closed_entities, origin)
    auto_name_faces(faces, r_shaft, r_rotor_outer, r_stator_inner, r_stator_outer)

    gui = FaceRegionGUI(faces, origin, REGION_NAMES, REGION_COLORS,
                        title='Rotor + Stator Region Assignment')
    gui.show()
    # ... 클릭 → face 선택 → 드롭다운 → 할당
    result = gui.get_faces()
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional

# 선택적 import (GUI 의존성)
_HAS_GUI = False
try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.collections import PatchCollection
    from matplotlib.lines import Line2D
    from matplotlib.path import Path
    import ipywidgets as widgets
    from IPython.display import display, clear_output
    _HAS_GUI = True
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════════
# 유틸리티
# ═══════════════════════════════════════════════════════════════

def _point_in_polygon(px: float, py: float, verts: List) -> bool:
    """Ray-casting 알고리즘으로 점이 다각형 내부인지 판정."""
    n = len(verts)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = verts[i]
        xj, yj = verts[j]
        if ((yi > py) != (yj > py)) and \
           (px < (xj - xi) * (py - yi) / (yj - yi + 1e-30) + xi):
            inside = not inside
        j = i
    return inside


def _find_face_at(faces: List[Dict], px: float, py: float) -> int:
    """
    클릭 좌표 (px, py)가 포함된 face 인덱스 반환.
    여러 face가 겹치면 면적이 가장 작은(= 가장 세밀한) face 우선.
    없으면 -1.
    """
    candidates = []
    for i, fi in enumerate(faces):
        verts = fi['vertices']
        if _point_in_polygon(px, py, verts):
            candidates.append((i, fi['area']))
    if not candidates:
        return -1
    # 면적이 작은 face 우선 (작은 영역이 큰 영역 위에 그려짐)
    candidates.sort(key=lambda t: t[1])
    return candidates[0][0]


# ═══════════════════════════════════════════════════════════════
# 메인 GUI 클래스: 닫힌 영역(face) 기반
# ═══════════════════════════════════════════════════════════════

class FaceRegionGUI:
    """
    닫힌 영역(face)을 시각화하고 이름을 할당하는 인터랙티브 GUI.

    Parameters
    ----------
    faces : List[Dict]
        detect_closed_faces() 결과. 각 dict에 'vertices', 'name' 포함.
    origin : Tuple[float, float]
        원점 좌표
    region_names : Dict[str, str]
        {'magnet': 'Magnet', 'rotor_core': 'Rotor Core', ...}
    region_colors : Dict[str, str]
        {'magnet': '#FF4444', ...}
    title : str
    figsize : Tuple[float, float]
    boundary_entities : List[EntityInfo] or None
        경계선 엔티티를 추가로 그리려면 전달
    """

    def __init__(self,
                 faces: List[Dict],
                 origin: Tuple[float, float],
                 region_names: Dict[str, str],
                 region_colors: Dict[str, str],
                 title: str = 'Region Assignment',
                 figsize: Tuple[float, float] = (10, 8),
                 boundary_entities=None):
        if not _HAS_GUI:
            raise ImportError(
                "GUI 의존성이 필요합니다: matplotlib, ipywidgets, IPython\n"
                "  pip install matplotlib ipywidgets ipympl"
            )
        self.faces = faces
        self.origin = origin
        self.region_names = region_names
        self.region_colors = region_colors
        self.title = title
        self.figsize = figsize
        self.boundary_entities = boundary_entities or []
        self.selected_idx = -1

        self.fig = None
        self.ax = None
        self._patches = []   # MplPolygon 리스트 (face 순서 대응)
        self._fig_output = None
        self._idx_slider = None
        self._region_dd = None
        self._assign_btn = None
        self._status = None

    # ── 내부 드로잉 ──────────────────────────────────────────

    def _draw_all(self):
        """face를 채색 다각형으로 그리고 선택된 face를 하이라이트."""
        ax = self.ax
        ax.clear()
        self._patches = []

        # 1) face를 면적 큰 순서(뒤) → 작은 순서(앞)로 그리기
        sorted_indices = sorted(range(len(self.faces)),
                                key=lambda i: self.faces[i]['area'],
                                reverse=True)

        for idx in sorted_indices:
            fi = self.faces[idx]
            name = fi.get('name', 'unknown')
            color = self.region_colors.get(name, '#D0D0D0')
            verts = fi['vertices']
            poly = MplPolygon(verts, closed=True,
                              facecolor=color, edgecolor='#333333',
                              linewidth=0.5, alpha=0.75)
            ax.add_patch(poly)
            self._patches.append((idx, poly))

            # face 번호 + 이름 라벨 (centroid에 표시)
            cx, cy = fi.get('centroid', (0, 0))
            if 'centroid' not in fi and fi['vertices']:
                cx = sum(v[0] for v in verts) / len(verts)
                cy = sum(v[1] for v in verts) / len(verts)
            short = self._short_name(name)
            ax.text(cx, cy, f'{idx}\n{short}',
                    fontsize=5, ha='center', va='center',
                    color='#222222', weight='bold',
                    bbox=dict(boxstyle='round,pad=0.15',
                              facecolor='white', alpha=0.6, lw=0))

        # 2) 선택된 face 하이라이트
        if 0 <= self.selected_idx < len(self.faces):
            fi = self.faces[self.selected_idx]
            verts = fi['vertices']
            hl = MplPolygon(verts, closed=True,
                            facecolor='none', edgecolor='lime',
                            linewidth=3.5, linestyle='-', zorder=10)
            ax.add_patch(hl)

        # 3) 경계선 엔티티 (옵션)
        for ei in self.boundary_entities:
            if ei.points:
                xs, ys = zip(*ei.points)
                ax.plot(xs, ys, color='#555555', lw=0.3, alpha=0.4)

        # 4) 범례 (고유 이름만)
        seen = set()
        handles = []
        for fi in self.faces:
            n = fi.get('name', 'unknown')
            if n not in seen:
                seen.add(n)
                c = self.region_colors.get(n, '#D0D0D0')
                label = self.region_names.get(n, n)
                handles.append(Line2D([0], [0], color=c, lw=8,
                                      alpha=0.75, label=label))
        if handles:
            ax.legend(handles=handles, fontsize=6, loc='upper right')

        # 5) 원점 표시
        ax.plot(*self.origin, 'r*', ms=6, zorder=20)
        ax.set_aspect('equal')

        sel_info = ''
        if 0 <= self.selected_idx < len(self.faces):
            fi = self.faces[self.selected_idx]
            sel_info = (f'  |  Face #{self.selected_idx}  '
                        f'→ {fi.get("name", "?")}  '
                        f'(area={fi["area"]:.1f})')
        ax.set_title(f'{self.title}{sel_info}', fontsize=9)

        self.fig.canvas.draw_idle()

    def _short_name(self, name: str) -> str:
        """표시용 약칭."""
        _map = {
            'stator_yoke': 'Yoke', 'stator_tooth': 'Tooth',
            'slot': 'Slot', 'slot_opening': 'SlotOp',
            'airgap': 'Gap', 'rotor_core': 'Core',
            'magnet': 'Mag', 'air_barrier': 'AirB',
            'shaft': 'Shaft', 'unknown': '?',
        }
        return _map.get(name, name[:6])

    # ── 이벤트 핸들러 ────────────────────────────────────────

    def _on_click(self, event):
        """마우스 클릭 → 해당 face 선택."""
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        px, py = event.xdata, event.ydata
        idx = _find_face_at(self.faces, px, py)
        if idx >= 0:
            self.selected_idx = idx
            self._idx_slider.value = idx
            fi = self.faces[idx]
            tag = fi.get('name', 'unknown')
            if tag in [opt for opt in self._region_dd.options]:
                self._region_dd.value = tag
            self._status.value = (
                f'선택: Face #{idx}  '
                f'→ {self.region_names.get(tag, tag)}  '
                f'(area={fi["area"]:.1f}, '
                f'r=[{fi["r_min"]:.1f}~{fi["r_max"]:.1f}])'
            )
            self._draw_all()

    def _on_assign(self, btn):
        """할당 버튼 → face 이름 변경 + 즉시 색상 반영."""
        idx = self._idx_slider.value
        new_name = self._region_dd.value
        if 0 <= idx < len(self.faces):
            old_name = self.faces[idx].get('name', '?')
            self.faces[idx]['name'] = new_name
            self.selected_idx = idx
            old_label = self.region_names.get(old_name, old_name)
            new_label = self.region_names.get(new_name, new_name)
            self._status.value = (
                f'✔ Face #{idx}: {old_label} → {new_label}'
            )
            self._draw_all()

    def _on_slider_change(self, change):
        """슬라이더 변경 → face 선택 + 하이라이트."""
        idx = change['new']
        if 0 <= idx < len(self.faces):
            self.selected_idx = idx
            fi = self.faces[idx]
            tag = fi.get('name', 'unknown')
            if tag in [opt for opt in self._region_dd.options]:
                self._region_dd.value = tag
            self._status.value = (
                f'선택: Face #{idx}  '
                f'→ {self.region_names.get(tag, tag)}  '
                f'(area={fi["area"]:.1f})'
            )
            self._draw_all()

    # ── 공개 메서드 ──────────────────────────────────────────

    def show(self):
        """GUI를 표시합니다."""
        # 위젯 생성
        n_faces = len(self.faces)
        self._idx_slider = widgets.IntSlider(
            value=0, min=0,
            max=max(n_faces - 1, 0),
            step=1, description='Face #:',
            layout=widgets.Layout(width='300px'),
        )
        self._region_dd = widgets.Dropdown(
            options=list(self.region_names.keys()),
            value=list(self.region_names.keys())[0],
            description='Region:',
            layout=widgets.Layout(width='220px'),
        )
        self._assign_btn = widgets.Button(
            description='할당 (Assign)',
            button_style='warning',
            layout=widgets.Layout(width='130px'),
        )
        self._status = widgets.Label(
            value=f'닫힌 영역을 클릭하여 선택 → 이름 할당 ({n_faces}개 face)'
        )

        # 이벤트 연결
        self._assign_btn.on_click(self._on_assign)
        self._idx_slider.observe(self._on_slider_change, names='value')

        controls = widgets.HBox([
            self._idx_slider, self._region_dd, self._assign_btn,
        ])

        self._fig_output = widgets.Output()
        with self._fig_output:
            self.fig, self.ax = plt.subplots(figsize=self.figsize)
            self.fig.canvas.mpl_connect('button_press_event', self._on_click)
            self._draw_all()
            plt.show()

        display(widgets.VBox([
            widgets.HTML(
                f'<b>{self.title}</b> — '
                f'닫힌 영역(face)을 클릭하여 선택 → 이름(region) 할당  '
                f'(총 {n_faces}개 영역)'
            ),
            controls,
            self._status,
            self._fig_output,
        ]))

    def get_faces(self) -> List[Dict]:
        """현재 face 할당 결과 반환."""
        return self.faces

    def get_summary(self) -> Dict[str, int]:
        """이름별 face 수 요약."""
        from collections import Counter
        return dict(Counter(f.get('name', 'unknown') for f in self.faces))


# ═══════════════════════════════════════════════════════════════
# VS Code용 간단 인터랙티브 클래스 (ipywidgets 불필요)
# ═══════════════════════════════════════════════════════════════

class FaceRegionGUILite:
    """
    VS Code 호환 인터랙티브 GUI.
    
    ipywidgets 없이 matplotlib만 사용:
    - 클릭: face 선택
    - 숫자키 1-9: 영역 이름 할당
    - 키보드 단축키로 region 변경
    
    Parameters
    ----------
    faces : List[Dict]
        detect_closed_faces() 결과
    origin : Tuple[float, float]
    region_names : Dict[str, str]
    region_colors : Dict[str, str]
    title : str
    figsize : Tuple[float, float]
    """
    
    def __init__(self,
                 faces: List[Dict],
                 origin: Tuple[float, float],
                 region_names: Dict[str, str],
                 region_colors: Dict[str, str],
                 title: str = 'Region Assignment',
                 figsize: Tuple[float, float] = (10, 8)):
        self.faces = faces
        self.origin = origin
        self.region_names = region_names
        self.region_colors = region_colors
        self.title = title
        self.figsize = figsize
        self.selected_idx = -1
        
        self.fig = None
        self.ax = None
        self._patches = []
        
        # 키보드 단축키 매핑 (1-9)
        self._key_map = {}
        for i, key in enumerate(list(region_names.keys())[:9]):
            self._key_map[str(i + 1)] = key
    
    def _short_name(self, name: str) -> str:
        """표시용 약칭."""
        _map = {
            'stator_yoke': 'Yoke', 'stator_tooth': 'Tooth',
            'slot': 'Slot', 'slot_opening': 'SlotOp',
            'airgap': 'Gap', 'rotor_core': 'Core',
            'magnet': 'Mag', 'air_barrier': 'AirB',
            'shaft': 'Shaft', 'unknown': '?',
        }
        return _map.get(name, name[:6])
    
    def _draw_all(self):
        """face를 채색 다각형으로 그리고 선택된 face를 하이라이트."""
        ax = self.ax
        ax.clear()
        self._patches = []
        
        # 면적 큰 순서(뒤) → 작은 순서(앞)
        sorted_indices = sorted(range(len(self.faces)),
                                key=lambda i: self.faces[i]['area'],
                                reverse=True)
        
        for idx in sorted_indices:
            fi = self.faces[idx]
            name = fi.get('name', 'unknown')
            color = self.region_colors.get(name, '#D0D0D0')
            verts = fi['vertices']
            poly = MplPolygon(verts, closed=True,
                              facecolor=color, edgecolor='#333333',
                              linewidth=0.5, alpha=0.75)
            ax.add_patch(poly)
            self._patches.append((idx, poly))
            
            # face 번호 + 이름 라벨
            cx, cy = fi.get('centroid', (0, 0))
            if 'centroid' not in fi and fi['vertices']:
                cx = sum(v[0] for v in verts) / len(verts)
                cy = sum(v[1] for v in verts) / len(verts)
            short = self._short_name(name)
            ax.text(cx, cy, f'{idx}\n{short}',
                    fontsize=5, ha='center', va='center',
                    color='#222222', weight='bold',
                    bbox=dict(boxstyle='round,pad=0.15',
                              facecolor='white', alpha=0.6, lw=0))
        
        # 선택된 face 하이라이트
        if 0 <= self.selected_idx < len(self.faces):
            fi = self.faces[self.selected_idx]
            verts = fi['vertices']
            hl = MplPolygon(verts, closed=True,
                            facecolor='none', edgecolor='lime',
                            linewidth=3.5, linestyle='-', zorder=10)
            ax.add_patch(hl)
        
        # 범례
        seen = set()
        handles = []
        for fi in self.faces:
            n = fi.get('name', 'unknown')
            if n not in seen:
                seen.add(n)
                c = self.region_colors.get(n, '#D0D0D0')
                label = self.region_names.get(n, n)
                handles.append(Line2D([0], [0], color=c, lw=8,
                                      alpha=0.75, label=label))
        if handles:
            ax.legend(handles=handles, fontsize=6, loc='upper right')
        
        ax.plot(*self.origin, 'r*', ms=6, zorder=20)
        ax.set_aspect('equal')
        
        # 타이틀에 선택 정보 + 단축키 안내
        sel_info = ''
        if 0 <= self.selected_idx < len(self.faces):
            fi = self.faces[self.selected_idx]
            sel_info = f'  |  Face #{self.selected_idx} → {fi.get("name", "?")}'
        
        shortcut_info = '  [1-9: assign region]'
        ax.set_title(f'{self.title}{sel_info}{shortcut_info}', fontsize=9)
        
        self.fig.canvas.draw_idle()
    
    def _on_click(self, event):
        """마우스 클릭 → face 선택."""
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        px, py = event.xdata, event.ydata
        idx = _find_face_at(self.faces, px, py)
        if idx >= 0:
            self.selected_idx = idx
            fi = self.faces[idx]
            print(f"★ 선택: Face #{idx} → {self.region_names.get(fi['name'], fi['name'])}  "
                  f"(area={fi['area']:.1f}, r=[{fi['r_min']:.1f}~{fi['r_max']:.1f}])")
            self._draw_all()
    
    def _on_key(self, event):
        """키보드 → 영역 할당."""
        if event.key in self._key_map:
            new_name = self._key_map[event.key]
            if 0 <= self.selected_idx < len(self.faces):
                old_name = self.faces[self.selected_idx].get('name', '?')
                self.faces[self.selected_idx]['name'] = new_name
                old_label = self.region_names.get(old_name, old_name)
                new_label = self.region_names.get(new_name, new_name)
                print(f"✔ Face #{self.selected_idx}: {old_label} → {new_label}")
                self._draw_all()
        elif event.key == 'n':
            # 다음 face 선택
            if len(self.faces) > 0:
                self.selected_idx = (self.selected_idx + 1) % len(self.faces)
                fi = self.faces[self.selected_idx]
                print(f"★ 선택: Face #{self.selected_idx} → {self.region_names.get(fi['name'], fi['name'])}")
                self._draw_all()
        elif event.key == 'p':
            # 이전 face 선택
            if len(self.faces) > 0:
                self.selected_idx = (self.selected_idx - 1) % len(self.faces)
                fi = self.faces[self.selected_idx]
                print(f"★ 선택: Face #{self.selected_idx} → {self.region_names.get(fi['name'], fi['name'])}")
                self._draw_all()
    
    def show(self):
        """인터랙티브 GUI 표시."""
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)
        self.fig.canvas.mpl_connect('key_press_event', self._on_key)
        self._draw_all()
        
        # 단축키 안내 출력
        print("=" * 60)
        print(f"인터랙티브 영역 할당 ({len(self.faces)}개 face)")
        print("=" * 60)
        print("• 클릭: face 선택")
        print("• n/p: 다음/이전 face")
        print("• 숫자키 1-9: 영역 할당")
        for key, name in self._key_map.items():
            print(f"    {key}: {self.region_names.get(name, name)}")
        print("=" * 60)
        
        plt.show()
        return self.fig, self.ax
    
    def get_faces(self) -> List[Dict]:
        return self.faces
    
    def get_summary(self) -> Dict[str, int]:
        from collections import Counter
        return dict(Counter(f.get('name', 'unknown') for f in self.faces))
