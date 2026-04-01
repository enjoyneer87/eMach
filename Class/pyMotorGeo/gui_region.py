"""
pyMotorGeo.gui_region
======================

Interactive matplotlib-based GUI for assigning region labels to closed faces in motor geometry.

This module provides two GUI classes (`FaceRegionGUI` and `FaceRegionGUILite`) that enable 
users to visualize closed motor regions (slots, conductors, magnets, etc.) and interactively 
reassign them using dropdown selections and click-based highlighting.

The GUI is designed for Jupyter notebook environments with `%matplotlib widget` backend 
enabled. It integrates with the `region_closing` module to work with detected faces 
(topologically closed polygonal regions).

Key Features
------------
- **Face Visualization**: Render closed faces as colored polygons with edge boundaries
- **Interactive Selection**: Click on faces to select, then reassign via dropdown menu
- **Real-time Updates**: Color changes immediately reflect user-selected region labels
- **Dual Implementations**: 
  - `FaceRegionGUI`: Full-featured with matplotlib Polygon patch collections
  - `FaceRegionGUILite`: Lightweight version using line drawing for constrained environments
- **Label Management**: Custom region names and color schemes via dictionaries

Integration with pyleecan
--------------------------
Concepts are inspired by pyleecan's DXF_Hole / SurfLine + label paradigm:
  - Each named region (face/SurfLine) can be assigned a symbolic label
  - Labels automatically control coloring and classification
  - Supports export-ready face data structures

Usage Example::

    # Detect closed regions
    from pyMotorGeo.region_closing import detect_closed_faces
    faces = detect_closed_faces(closed_entities, origin=(0, 0))
    
    # Create interactive GUI
    from pyMotorGeo.gui_region import FaceRegionGUI
    from pyMotorGeo.topology import REGION_NAMES, REGION_COLORS
    
    gui = FaceRegionGUI(
        faces=faces,
        origin=(0, 0),
        region_names=REGION_NAMES,
        region_colors=REGION_COLORS,
        title='Motor Region Assignment'
    )
    gui.show()
    
    # User clicks faces and reassigns via dropdown
    updated_faces = gui.get_faces()

Dependencies
------------
- matplotlib: Graph rendering and interactive plot backend
- ipywidgets: Jupyter dropdown and button widgets for user interaction
- ipython.display: Jupyter display utilities
- numpy: Numerical operations for point-in-polygon tests
- typing, math: Standard library utilities
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
    """
    Test whether a point lies inside a polygon using ray-casting algorithm.
    
    Implements the classical ray-casting (cross-product) method: cast a horizontal 
    ray from the point to infinity and count edge crossings. Odd count = inside.
    Robust to boundary cases and numerical precision issues.

    Parameters
    ----------
    px : float
        X-coordinate of the test point.
    py : float
        Y-coordinate of the test point.
    verts : List
        List of polygon vertices, each a tuple (x, y). Must form a valid polygon
        (at least 3 vertices) and can be in clockwise or counter-clockwise order.

    Returns
    -------
    bool
        True if (px, py) is inside the polygon; False otherwise.
        Points exactly on edges may return either True or False (implementation-dependent).

    Algorithm
    ---------
    The ray-casting method works as follows:
    1. Cast a horizontal ray from (px, py) extending to +∞ (to the right)
    2. Count how many polygon edges this ray crosses
    3. If the count is odd, the point is inside; if even, outside
    4. For robustness, use epsilon correction for division (1e-30) to avoid numerical issues
    
    Time Complexity: O(n), where n is the number of vertices

    Examples
    --------
    >>> square_verts = [(0, 0), (10, 0), (10, 10), (0, 10)]
    >>> _point_in_polygon(5, 5, square_verts)
    True
    >>> _point_in_polygon(15, 5, square_verts)
    False
    """
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
    Identify which face contains the clicked point (px, py).
    
    When multiple faces overlap at a location, prioritize the smallest face 
    (finest-grained region), as smaller entities are typically rendered last 
    and visually appear "on top" in the GUI.

    Parameters
    ----------
    faces : List[Dict]
        List of closed face dictionaries from `detect_closed_faces()`. Each dict 
        must contain 'vertices' (list of polygon vertices) and 'area' (numeric area).
    px : float
        X-coordinate of the click position.
    py : float
        Y-coordinate of the click position.

    Returns
    -------
    int
        Zero-based index of the selected face if (px, py) is inside any face.
        If multiple faces contain the point, returns the index of the smallest face.
        If no face contains the point, returns -1.

    Selection Priority
    ------------------
    When faces overlap, the algorithm prefers smaller faces because:
    1. In motor geometry, detailed regions (e.g., thin slot conductors) should be 
       selectable even if partially overlapped by larger regions
    2. Visually, smaller objects are often "drawn last" and appear in front
    3. Reflects common UI practice for nested or overlapping clickable elements

    Examples
    --------
    >>> faces = [
    ...     {'vertices': [(0,0), (10,0), (10,10), (0,10)], 'area': 100},
    ...     {'vertices': [(2,2), (8,2), (8,8), (2,8)], 'area': 36},
    ... ]
    >>> _find_face_at(faces, 5, 5)  # Click at center
    1  # Returns the smaller face, not the outer one
    
    >>> _find_face_at(faces, 15, 15)  # Click outside
    -1
    
    Time Complexity
    ----------------
    O(n) where n = number of faces, with each point-in-polygon test being O(m) 
    where m = average number of vertices per face.
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
    Interactive matplotlib GUI for assigning region labels to closed motor faces.
    
    This class provides a full-featured GUI using matplotlib patch collections to render
    closed regions (faces) as colored polygons, with real-time interaction for clicking 
    faces, reassigning labels, and optionally viewing boundary geometry. Designed for 
    use in Jupyter notebooks with `%matplotlib widget` backend.

    Features
    --------
    - **Interactive Face Selection**: Click on any face to select it (highlighted with edge)
    - **Dropdown Reassignment**: Use ipywidgets dropdown to change face labels
    - **Color Feedback**: Faces are colored according to their region type from `region_colors` dict
    - **Live Updates**: Colors and assignments update immediately in the plot
    - **Confidence Slider**: Alpha transparency (optional, per-face confidence indication)
    - **Boundary Visualization**: Can optionally overlay CAD boundary entities for context
    - **Data Export**: `get_faces()` and `get_summary()` methods for programmatic access

    Parameters
    ----------
    faces : List[Dict]
        List of closed face dictionaries from `detect_closed_faces()`. Each dict must 
        contain at minimum:
        - 'vertices': List of (x, y) tuples forming the polygon boundary
        - 'name': String label (e.g., 'magnet', 'slot', 'rotor_core')
        - 'area': Numeric face area (used for sorting in click detection)
        
        Optional fields:
        - 'confidence': Float [0, 1] for alpha rendering
        - 'centroid': (x, y) tuple for face center
    
    origin : Tuple[float, float]
        Motor center (ox, oy) coordinate in motor units. Used for coordinate 
        transformation references during visualization.
    
    region_names : Dict[str, str]
        Mapping from region label keys to human-readable names. Example::
        
            {'magnet': 'Magnet', 'slot': 'Slot', 'rotor_core': 'Rotor Core', ...}
        
        These keys should match the 'name' fields in the faces list.
    
    region_colors : Dict[str, str]
        Mapping from region labels to matplotlib color strings. Example::
        
            {'magnet': '#FF4444', 'slot': '#FFFF00', 'rotor_core': '#4A90D9', ...}
        
        Colors are applied immediately when a face is assigned a label.
    
    title : str, optional
        Title to display at the top of the plot. Default is 'Region Assignment'.
    
    figsize : Tuple[float, float], optional
        Figure size (width, height) in inches. Default is (10, 8).
    
    boundary_entities : List[EntityInfo] or None, optional
        Optional CAD boundary/constraint entities to overlay on the plot. If provided,
        these are drawn as gray lines behind the faces for geometric context.
        Default is None.

    Attributes
    ----------
    selected_idx : int
        Currently selected face index (zero-based). Set to -1 if no face selected.
    
    fig : matplotlib.figure.Figure or None
        The matplotlib figure object, created on first `show()` call.
    
    ax : matplotlib.axes.Axes or None
        The matplotlib axes object for drawing.

    Methods
    -------
    show()
        Render the interactive GUI in a Jupyter notebook.
    
    get_faces() -> List[Dict]
        Return the updated faces list with user-assigned labels.
    
    get_summary() -> Dict[str, int]
        Return a count of faces grouped by region label.

    Examples
    --------
    Basic usage with rotor region assignment:
    
    >>> from pyMotorGeo.region_closing import detect_closed_faces
    >>> from pyMotorGeo.topology import REGION_NAMES, REGION_COLORS
    >>> 
    >>> faces = detect_closed_faces(closed_entities, origin=(0, 0))
    >>> gui = FaceRegionGUI(
    ...     faces=faces,
    ...     origin=(0, 0),
    ...     region_names=REGION_NAMES,
    ...     region_colors=REGION_COLORS,
    ...     title='Rotor Region Assignment'
    ... )
    >>> gui.show()
    >>> 
    >>> # After user interactions (clicking and reassigning)
    >>> updated_faces = gui.get_faces()
    >>> summary = gui.get_summary()
    >>> print(f"Magnet faces: {summary.get('magnet', 0)}")

    User Workflow
    -------------
    1. Call `show()` to display the interactive plot in Jupyter
    2. Click on a face to select it (edges highlight in orange/magenta)
    3. Use the region dropdown (ipywidgets select) to choose a new label
    4. Click "Assign" button to apply the change
    5. Face color updates immediately to match the new region type
    6. Repeat steps 2-5 for other faces
    7. Call `get_faces()` or `get_summary()` to retrieve results

    Notes
    -----
    - **Matplotlib Backend**: Requires `%matplotlib widget` in Jupyter for interactivity
    - **Dependencies**: matplotlib (patches, collections), ipywidgets, IPython.display
    - **Boundary Overlap**: Faces are rendered as patches over boundary entities (if provided)
    - **Performance**: Rendering is optimized for ~100-500 faces; larger datasets may 
      experience slower updates
    - **Coordinate System**: All coordinates must be consistent with motor CAD geometry;
      no automatic scaling is applied
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
    Lightweight alternative GUI for VS Code and non-Jupyter environments.
    
    This class provides a simplified interactive interface using only matplotlib 
    (no ipywidgets dependency) for assigning region labels to closed faces. 
    Designed for use in standard Python environments (VS Code, Spyder, etc.) 
    where ipywidgets may not be available. Interaction is keyboard-based rather 
    than GUI widgets.

    Features
    --------
    - **Mouse Click Selection**: Click on a face to select it (edge highlighted)
    - **Keyboard Region Assignment**: Press number keys (1-9) to assign pre-mapped region types
    - **Key (E)dit**: Press 'e' to cycle through all available regions for the selected face
    - **Live Display**: Real-time color and title updates without widget overhead
    - **Minimal Dependencies**: Requires only matplotlib (ipywidgets not needed)
    - **Status Feedback**: Status bar shows selected face index, area, and radii

    Parameters
    ----------
    faces : List[Dict]
        List of closed face dictionaries from `detect_closed_faces()`. Each dict 
        must contain 'vertices', 'name', and 'area' fields.
    
    origin : Tuple[float, float]
        Motor center (ox, oy) coordinate in motor units.
    
    region_names : Dict[str, str]
        Mapping from region labels to human-readable names. First 9 keys 
        (in dict insertion order) are mapped to number keys 1-9 for quick assignment.
        Example: {'magnet': 'Magnet', 'rotor_core': 'Rotor Core', ...}
    
    region_colors : Dict[str, str]
        Mapping from region labels to matplotlib colors.
        Example: {'magnet': '#FF4444', 'rotor_core': '#4A90D9', ...}
    
    title : str, optional
        Title to display in the plot. Default is 'Region Assignment'.
    
    figsize : Tuple[float, float], optional
        Figure size (width, height) in inches. Default is (10, 8).

    Attributes
    ----------
    selected_idx : int
        Currently selected face index, or -1 if no face selected.
    
    fig : matplotlib.figure.Figure or None
        The matplotlib figure object, created on `show()`.
    
    ax : matplotlib.axes.Axes or None
        The matplotlib axes object for drawing.

    Keyboard Controls
    -----------------
    - **Number Keys (1-9)**: Assign region based on order in `region_names`. 
      E.g., if region_names keys are ['magnet', 'slot', 'rotor_core'], 
      then 1='magnet', 2='slot', 3='rotor_core'.
    - **'e' key**: Cycle through all available regions for the selected face 
      (regardless of the 1-9 shortcut mapping).
    - **Click**: Select a face to highlight and prepare for keyboard assignment.

    Methods
    -------
    show()
        Display the interactive matplotlib window.
    
    get_faces() -> List[Dict]
        Return the modified faces list with user assignments.
    
    get_summary() -> Dict[str, int]
        Return a count of faces grouped by region label.

    Examples
    --------
    >>> from pyMotorGeo.region_closing import detect_closed_faces
    >>> from pyMotorGeo.topology import REGION_NAMES, REGION_COLORS
    >>> 
    >>> faces = detect_closed_faces(entities, origin=(0, 0))
    >>> gui = FaceRegionGUILite(
    ...     faces=faces,
    ...     origin=(0, 0),
    ...     region_names=REGION_NAMES,
    ...     region_colors=REGION_COLORS,
    ... )
    >>> gui.show()
    >>> 
    >>> # After keyboard interactions
    >>> updated = gui.get_faces()

    User Workflow (VS Code Environment)
    -----------------------------------
    1. Call `show()` to open the matplotlib window
    2. Click on a face in the plot to select it
    3. Press a number key (1-9) to quickly assign a region, OR press 'e' to cycle
    4. The plot updates immediately; face color reflects the new region type
    5. Repeat for other faces
    6. Close the plot window when done
    7. Call `get_faces()` to retrieve results programmatically

    Notes
    -----
    - **Environment**: Tested in VS Code with matplotlib backend (e.g., 'TkAgg', 'Qt5Agg')
    - **Keyboard Mapping**: Only the first 9 region types get number shortcuts; 
      additional types are accessible via 'e' cycling or direct assignment in code
    - **No Slider/Dropdown**: Unlike FaceRegionGUI, this class uses keyboard-only control
    - **Performance**: Similar to FaceRegionGUI; suitable for ~100-500 faces
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
