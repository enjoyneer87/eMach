# -*- coding: utf-8 -*-
"""
thermal_viz — 모터 열해석(.rth) 표준 시각화 패키지
====================================================

MAPDL 열해석 결과(file.rth)로부터 **규격화된 GIF/PNG 세트**를 재현성 있게 생성.
어떤 모델(IcepakFEA, Prius 워터재킷 등)에도 동일 규격으로 뽑도록 코드화.

핵심 기법 (real_transient_3d_cut.gif에서 확립)
---------------------------------------------
- 볼륨 clip 은 VTK 크래시 → **외피(surface) 반쪽 clip + 단면 slice 조합**으로 3D 컷어웨이.
  ext_half = solid.extract_surface().clip(normal=(1,0,0), invert=True)  # x<0 외피
  sl       = solid.slice(normal="x")                                    # x=0 단면
  두 mesh 를 함께 렌더, view_vector((1,-0.45,0.35)) 로 절단면 정면 조망.

재료 번호 규약(MAPDL): 1=stator 2=magnet 3=coil 4=shaft 5=rotor  (mats 인자로 변경가능)

표준 출력 세트 (STANDARD_SET)
-----------------------------
GIF (과도):
  transient_3d_cut.gif   3D 반단면 컷어웨이(외피+단면) — 대표 뷰
  transient_core.gif     z=0 정단면, 전 부품 온도컬러(가림 없음)
  transient_coilmag.gif  코일+자석 내부부품(스테이터/로터 반투명 고스트)
  transient_coil_z0.gif  코일 z=0 슬라이스
PNG (최종 t, 정적):
  contour_iso.png        3D iso 전체 표면 컨투어
  contour_z0.png         z=0 반경단면
  cut_3d.png             3D 반단면 컷어웨이(마지막 프레임)
  coil_only.png          코일 단독
  magnet_only.png        자석 단독(+로터 고스트)
  component_history.png  부품별 온도 시간이력

CLI:  python thermal_viz.py <file.rth> <out_dir> [label] [clim_lo]
"""
import os
import traceback
import numpy as np

MATS_DEFAULT = dict(stator=1, magnet=2, coil=3, shaft=4, rotor=5)
# transient_dashboard(3패널: 3d_cut+circuit+이력)는 circuit 정보가 필요해
# render_standard_viz 의 circuit 경로에서 생성(STANDARD_GIFS 미포함).
STANDARD_GIFS = ("transient_3d_cut", "transient_core", "transient_coilmag",
                 "transient_coil_z0")
STANDARD_PNGS = ("contour_iso", "contour_z0", "cut_3d", "coil_only", "magnet_only", "component_history")
CMAP = "inferno"
COMP_COLORS = {"Coil": "#2a78d6", "Magnet": "#e34948", "Rotor": "#1baf7a",
               "Stator": "#eda100", "Shaft": "#8a8878"}


def _sb(fmt="%.1f"):
    return dict(title="Temperature (degC)", title_font_size=14, label_font_size=12,
                n_labels=6, fmt=fmt, color="black")


class ThermalViz:
    """.rth 하나에 대한 표준 시각화 렌더러."""

    def __init__(self, rth_path, out_dir, label="", clim_lo=None, mats=None, fps=4, z_trim=None):
        import pyvista as pv
        from ansys.mapdl import reader as rd
        pv.OFF_SCREEN = True
        self.pv = pv
        self.label = label
        self.fps = fps
        self.out = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.M = dict(MATS_DEFAULT if mats is None else mats)

        self.res = rd.read_binary(rth_path)
        self.nsets = self.res.nsets
        self.times = np.asarray(self.res.time_values, float)
        g = self.res.grid.copy()
        self.solid = g.extract_cells(np.isin(g.celltypes, (10, 24)))
        # 원본 grid 노드 인덱스를 point_data "gid"로 실어 이후 모든 추출/클립에서
        # 보존한다. vtkOriginalPointIds 는 추출마다 부모기준으로 재생성되어
        # 이중추출(z_trim 등) 시 온도매핑이 깨지므로 직접 gid 를 들고다닌다.
        self.solid.point_data["gid"] = np.asarray(
            self.solid.point_data["vtkOriginalPointIds"]).astype(np.float64)
        # z_trim: 축방향 돌출부(예: 긴 샤프트) 제거 → 깔끔한 반단면.
        # 셀 중심 |z|<=z_trim 만 유지. (메시 단위 주의: Prius 는 미터)
        if z_trim is not None:
            cc = self.solid.cell_centers().points
            keep = np.where(np.abs(cc[:, 2]) <= float(z_trim))[0]
            self.solid = self.solid.extract_cells(keep)
        self.mats = np.asarray(self.solid.cell_data["ansys_material_type"])
        self.opid = np.rint(np.asarray(self.solid.point_data["gid"])).astype(np.int64)
        b = self.solid.bounds
        self.R = max(abs(b[0]), abs(b[1]), abs(b[2]), abs(b[3]))  # 반경 특성길이(circuit 스케일)
        _, Tend = self.res.nodal_temperature(self.nsets - 1)
        self.Tend = np.asarray(Tend, float)
        lo = float(np.nanmin(self.Tend[self.opid])) if clim_lo is None else float(clim_lo)
        self.clim = [lo, float(np.nanmax(self.Tend[self.opid]))]

        # 부품별 서브메시 + 원본 point id
        self._sub = {}
        for role, m in self.M.items():
            idx = np.where(self.mats == m)[0]
            if idx.size:
                sm = self.solid.extract_cells(idx)
                pid = np.rint(np.asarray(sm.point_data["gid"])).astype(np.int64)
                self._sub[role] = (sm, pid)
        gmats = [self.M[r] for r in ("stator", "rotor") if r in self.M]
        gidx = np.where(np.isin(self.mats, gmats))[0]
        self.ghost = self.solid.extract_cells(gidx).extract_surface() if gidx.size else None

        # 3d_cut 용 외피 반쪽 (gid 가 clip 통과해 보존; 절단점은 보간→반올림)
        ext = self.solid.extract_surface()
        self.ext_half = ext.clip(normal=(1, 0, 0), origin=(0, 0, 0), invert=True)
        self.epid = np.clip(
            np.rint(np.asarray(self.ext_half.point_data["gid"])).astype(np.int64),
            0, len(self.Tend) - 1)

    # ── 내부 헬퍼 ────────────────────────────────────────────────────────
    def _T(self, i):
        _, T = self.res.nodal_temperature(i)
        return np.asarray(T, float)

    def _maxes(self, T):
        return {r: float(np.nanmax(T[pid])) for r, (_, pid) in self._sub.items()}

    def _save_gif(self, name, frames):
        import imageio.v2 as imageio
        p = os.path.join(self.out, f"{name}.gif")
        imageio.mimsave(p, frames, fps=self.fps, loop=0)
        return p, os.path.getsize(p) / 1e6

    # ── ① 3D 반단면 컷어웨이 (대표) ──────────────────────────────────────
    def _render_cut3d_frame(self, T):
        self.ext_half.point_data["Temperature (degC)"] = T[self.epid]
        self.solid.point_data["Temperature (degC)"] = T[self.opid]
        sl = self.solid.slice(normal="x")
        pl = self.pv.Plotter(off_screen=True, window_size=(1000, 800))
        pl.set_background("white")
        pl.add_mesh(self.ext_half, scalars="Temperature (degC)", cmap=CMAP, clim=self.clim,
                    n_colors=14, lighting=True, ambient=0.6, diffuse=0.4, specular=0.0,
                    scalar_bar_args=_sb())
        pl.add_mesh(sl, scalars="Temperature (degC)", cmap=CMAP, clim=self.clim, n_colors=14,
                    lighting=False, show_scalar_bar=False)
        pl.view_vector((1, -0.45, 0.35), viewup=(0, 1, 0))
        pl.camera.zoom(1.05)
        return pl

    def cut3d_gif(self):
        frames = []
        for i in range(self.nsets):
            T = self._T(i); mx = self._maxes(T)
            pl = self._render_cut3d_frame(T)
            pl.add_text(f"t={self.times[i]:5.0f}s  half-section  {self.label}\n"
                        + "  ".join(f"{r[:4]} {mx[r]:.0f}" for r in ("coil", "stator", "rotor", "magnet") if r in mx) + "C",
                        font_size=12, color="black")
            frames.append(pl.screenshot(return_img=True)); pl.close()
        return self._save_gif("transient_3d_cut", frames)

    def cut3d_png(self):
        T = self.Tend; mx = self._maxes(T)
        pl = self._render_cut3d_frame(T)
        pl.add_text(f"half-section {self.label}  "
                    + "  ".join(f"{r[:4]} {mx[r]:.0f}" for r in ("coil", "stator", "rotor", "magnet") if r in mx) + "C",
                    font_size=12, color="black")
        p = os.path.join(self.out, "cut_3d.png"); pl.screenshot(p); pl.close()
        return p

    # ── ② z=0 정단면, 전 부품 ────────────────────────────────────────────
    def core_gif(self):
        frames = []
        for i in range(self.nsets):
            T = self._T(i); mx = self._maxes(T)
            self.solid.point_data["Temperature (degC)"] = T[self.opid]
            sl = self.solid.slice(normal="z", origin=(0, 0, 0))
            pl = self.pv.Plotter(off_screen=True, window_size=(950, 950)); pl.set_background("white")
            pl.add_mesh(sl, scalars="Temperature (degC)", cmap=CMAP, clim=self.clim, n_colors=16,
                        lighting=False, scalar_bar_args=_sb())
            pl.add_text(f"t={self.times[i]:5.0f}s  "
                        + "  ".join(f"{r[:4]} {mx[r]:.0f}" for r in ("stator", "coil", "rotor", "magnet") if r in mx)
                        + f"C  {self.label}", font_size=11, color="black")
            pl.view_xy(); pl.camera.zoom(1.3)
            frames.append(pl.screenshot(return_img=True)); pl.close()
        return self._save_gif("transient_core", frames)

    # ── ③ 코일+자석 내부부품 ─────────────────────────────────────────────
    def coilmag_gif(self):
        coil, cpid = self._sub["coil"]; mag, mpid = self._sub["magnet"]
        frames = []
        for i in range(self.nsets):
            T = self._T(i)
            coil.point_data["Temperature (degC)"] = T[cpid]
            mag.point_data["Temperature (degC)"] = T[mpid]
            pl = self.pv.Plotter(off_screen=True, window_size=(1000, 780)); pl.set_background("white")
            if self.ghost is not None:
                pl.add_mesh(self.ghost, color="#d9d6c8", opacity=0.08, lighting=True, ambient=0.5)
            pl.add_mesh(coil, scalars="Temperature (degC)", cmap=CMAP, clim=self.clim, n_colors=14,
                        lighting=True, ambient=0.6, diffuse=0.4, scalar_bar_args=_sb())
            pl.add_mesh(mag, scalars="Temperature (degC)", cmap=CMAP, clim=self.clim, n_colors=14,
                        lighting=True, ambient=0.6, diffuse=0.4, show_scalar_bar=False)
            pl.add_text(f"t={self.times[i]:5.0f}s coil {float(np.nanmax(T[cpid])):5.1f} | "
                        f"mag {float(np.nanmax(T[mpid])):5.1f}C  {self.label}", font_size=11, color="black")
            pl.view_vector((1, -0.4, 0.55), viewup=(0, 1, 0)); pl.camera.zoom(1.2)
            frames.append(pl.screenshot(return_img=True)); pl.close()
        return self._save_gif("transient_coilmag", frames)

    # ── ④ 코일 z=0 슬라이스 ──────────────────────────────────────────────
    def coil_z0_gif(self):
        coil, cpid = self._sub["coil"]
        frames = []
        for i in range(self.nsets):
            T = self._T(i); coil.point_data["Temperature (degC)"] = T[cpid]
            sl = coil.slice(normal="z", origin=(0, 0, 0))
            pl = self.pv.Plotter(off_screen=True, window_size=(950, 950)); pl.set_background("white")
            pl.add_mesh(sl, scalars="Temperature (degC)", cmap=CMAP, clim=self.clim, n_colors=16,
                        lighting=False, scalar_bar_args=_sb())
            pl.add_text(f"t={self.times[i]:5.0f}s coil {float(np.nanmax(T[cpid])):5.1f}C  {self.label}",
                        font_size=11, color="black")
            pl.view_xy(); pl.camera.zoom(1.3)
            frames.append(pl.screenshot(return_img=True)); pl.close()
        return self._save_gif("transient_coil_z0", frames)

    # ── PNG 컨투어 (최종 t) ──────────────────────────────────────────────
    def contour_png(self):
        self.solid.point_data["Temperature (degC)"] = self.Tend[self.opid]
        outs = []
        for fn, mesh, view, lit in [
                ("contour_iso.png", self.solid.extract_surface(), "iso", True),
                ("contour_z0.png", self.solid.slice(normal="z"), "xy", False)]:
            tv = mesh.point_data["Temperature (degC)"]
            pl = self.pv.Plotter(off_screen=True, window_size=(1150, 950)); pl.set_background("white")
            kw = dict(scalars="Temperature (degC)", cmap=CMAP, clim=self.clim, n_colors=14, scalar_bar_args=_sb())
            if lit: kw.update(smooth_shading=True, ambient=0.6, diffuse=0.4)
            else: kw.update(lighting=False)
            pl.add_mesh(mesh, **kw)
            pl.add_text(f"{self.label} @{self.times[-1]:.0f}s", font_size=11, color="black")
            pl.view_xy() if view == "xy" else pl.view_isometric()
            pl.camera.zoom(1.15); p = os.path.join(self.out, fn); pl.screenshot(p); pl.close()
            outs.append(p)
        return outs

    def component_png(self):
        outs = []
        for role, fn, tt, ghost in [("coil", "coil_only.png", "COIL", None),
                                    ("magnet", "magnet_only.png", "MAGNET", "rotor")]:
            if role not in self._sub: continue
            mesh, pid = self._sub[role]; tv = self.Tend[pid]
            mesh.point_data["Temperature (degC)"] = tv
            pl = self.pv.Plotter(off_screen=True, window_size=(1200, 950)); pl.set_background("white")
            if ghost and ghost in self._sub:
                pl.add_mesh(self._sub[ghost][0].extract_surface(), color="#d9d6c8", opacity=0.1, lighting=True, ambient=0.5)
            pl.add_mesh(mesh, scalars="Temperature (degC)", cmap=CMAP, clim=self.clim, n_colors=14,
                        lighting=True, ambient=0.55, diffuse=0.45, scalar_bar_args=_sb())
            pl.add_text(f"{tt} {self.label} (max {float(np.nanmax(tv)):.1f}C)", font_size=11, color="black")
            pl.view_vector((1, -0.4, 0.55), viewup=(0, 1, 0)); pl.camera.zoom(1.15)
            p = os.path.join(self.out, fn); pl.screenshot(p); pl.close(); outs.append(p)
        return outs

    _CAP = {"coil": "Coil", "magnet": "Magnet", "rotor": "Rotor", "stator": "Stator"}

    def _compute_hist(self, roles):
        """부품별 avg/max 온도 시간이력. pid 는 gid 기반이라 트림 후에도 정확."""
        pid = {r: np.unique(self._sub[r][1]) for r in roles}
        hist = {r: {"avg": [], "max": []} for r in roles}
        for i in range(self.nsets):
            T = self._T(i)
            for r in roles:
                v = T[pid[r]]
                hist[r]["avg"].append(float(np.nanmean(v)))
                hist[r]["max"].append(float(np.nanmax(v)))
        return hist

    def _draw_history(self, ax, hist, roles, cursor_i=None):
        """이력 곡선(+옵션: 현재시각 세로 커서·현재값 점)을 ax 에 그린다."""
        INK, GRIDC = "#333333", "#e5e5e0"
        for r in roles:
            c = COMP_COLORS[self._CAP[r]]
            ax.plot(self.times, hist[r]["max"], color=c, lw=2, label=f"{self._CAP[r]} max")
            ax.plot(self.times, hist[r]["avg"], color=c, lw=1.3, ls="--", alpha=0.7)
            if cursor_i is not None:
                ax.plot(self.times[cursor_i], hist[r]["max"][cursor_i], "o", color=c,
                        ms=8, mec="white", mew=1.0, zorder=5)
        if cursor_i is not None:
            ax.axvline(self.times[cursor_i], color=INK, lw=1.2, ls=":", alpha=0.85)
        ax.set_xlabel("Time, s", color=INK)
        ax.set_ylabel("Temperature, degC", color=INK)
        ax.grid(True, color=GRIDC, lw=0.8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.legend(frameon=False, fontsize=9, labelcolor=INK, ncol=2)

    def history_png(self):
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        roles = [r for r in ("coil", "magnet", "rotor", "stator") if r in self._sub]
        hist = self._compute_hist(roles)
        fig, ax = plt.subplots(figsize=(9.5, 6))
        self._draw_history(ax, hist, roles)
        for r in roles:
            ax.annotate(f"{hist[r]['max'][-1]:.1f}",
                        xy=(self.times[-1], hist[r]["max"][-1]),
                        xytext=(self.times[-1] * 1.01, hist[r]["max"][-1]),
                        va="center", fontsize=9, color="#333333")
        ax.set_title(f"{self.label} - component temperatures", color="#333333", fontsize=12)
        ax.set_xlim(0, self.times[-1] * 1.28)
        fig.tight_layout()
        p = os.path.join(self.out, "component_history.png")
        fig.savefig(p, dpi=150); plt.close(fig)
        return p

    # ── 합성 대시보드 GIF (3d_cut + 이력곡선/현재시각 커서) ─────────────────
    @staticmethod
    def _hstack(a, b):
        """두 이미지를 높이 맞춰 좌우 결합."""
        try:
            from PIL import Image
            H = max(a.shape[0], b.shape[0])

            def fit(img):
                im = Image.fromarray(img[..., :3].astype(np.uint8))
                w = max(1, int(round(im.width * H / im.height)))
                return np.asarray(im.resize((w, H)))
            return np.hstack([fit(a), fit(b)])
        except Exception:
            H = min(a.shape[0], b.shape[0])
            return np.hstack([a[:H, :, :3], b[:H, :, :3]])

    def combined_gif(self, label="", name="transient_dashboard"):
        """3d_cut(좌) + 부품 온도이력 곡선·현재시각 커서(우) 합성 대시보드 GIF.
        기존 3d_cut 프레임 렌더 + 이력곡선 렌더를 매 프레임 합치는 형태."""
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        roles = [r for r in ("coil", "magnet", "rotor", "stator") if r in self._sub]
        hist = self._compute_hist(roles)
        allmax = [m for r in roles for m in hist[r]["max"]]
        ylim = (self.clim[0] - 3, max(allmax) + 8)
        frames = []
        for i in range(self.nsets):
            T = self._T(i)
            pl = self._render_cut3d_frame(T)
            pl.add_text(f"t={self.times[i]:5.0f}s  half-section  {label}",
                        font_size=12, color="black")
            left = pl.screenshot(return_img=True); pl.close()
            fig, ax = plt.subplots(figsize=(6.2, max(4.0, left.shape[0] / 150.0)), dpi=150)
            self._draw_history(ax, hist, roles, cursor_i=i)
            ax.set_title(f"component temperatures   t={self.times[i]:.0f}s",
                         color="#333333", fontsize=11)
            ax.set_xlim(0, self.times[-1]); ax.set_ylim(*ylim)
            fig.tight_layout()
            fig.canvas.draw()
            right = np.asarray(fig.canvas.buffer_rgba())[..., :3]
            plt.close(fig)
            frames.append(self._hstack(left, right))
        return self._save_gif(name, frames)

    @staticmethod
    def _vstack(a, b):
        """두 이미지를 폭 맞춰 상하 결합."""
        try:
            from PIL import Image
            W = max(a.shape[1], b.shape[1])

            def fit(img):
                im = Image.fromarray(img[..., :3].astype(np.uint8))
                h = max(1, int(round(im.height * W / im.width)))
                return np.asarray(im.resize((W, h)))
            return np.vstack([fit(a), fit(b)])
        except Exception:
            W = min(a.shape[1], b.shape[1])
            return np.vstack([a[:, :W, :3], b[:, :W, :3]])

    def full_dashboard_gif(self, nodes, edges, node_T_fn, label="",
                           name="transient_dashboard"):
        """종합 대시보드 GIF: 좌[3d_cut 온도장 + 회로 오버레이] + 우[온도이력 곡선·커서].
        3d_cut 뷰 자체에 회로를 얹어 한 장면으로 만들고 이력곡선을 우측에 결합."""
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        roles = [r for r in ("coil", "magnet", "rotor", "stator") if r in self._sub]
        hist = self._compute_hist(roles)
        allmax = [m for r in roles for m in hist[r]["max"]]
        ylim = (self.clim[0] - 3, max(allmax) + 8)
        frames = []
        for i in range(self.nsets):
            T = self._T(i); ts = self.times[i]
            pl = self._render_cut3d_circuit(T, nodes, edges, node_T_fn(T), label,
                                            title_extra=f"  t={ts:.0f}s")
            left = pl.screenshot(return_img=True); pl.close()
            fig, ax = plt.subplots(figsize=(6.4, max(4.0, left.shape[0] / 150.0)),
                                   dpi=150)
            self._draw_history(ax, hist, roles, cursor_i=i)
            ax.set_title(f"component temperatures   t={ts:.0f}s",
                         color="#333333", fontsize=11)
            ax.set_xlim(0, self.times[-1]); ax.set_ylim(*ylim)
            fig.tight_layout(); fig.canvas.draw()
            right = np.asarray(fig.canvas.buffer_rgba())[..., :3]
            plt.close(fig)
            frames.append(self._hstack(left, right))
        return self._save_gif(name, frames)

    # ── 열등가회로 3D 오버레이 ───────────────────────────────────────────
    def _add_circuit(self, p, nodes, edges, node_T, tube_color="#b9b8ad"):
        """주어진 Plotter 에 회로 요소(튜브=엣지 저항, 색구=노드 온도, 라벨) 추가.

        nodes {name:(x,y,z)} 위치, edges [(a,b)] 연결, node_T {name:T}|None 온도.
        색 정규화는 self.clim 고정, 구·튜브 크기는 형상 반경 self.R 비례.
        """
        import matplotlib.cm as cm
        import matplotlib.colors as mcolors
        pv = self.pv
        R = self.R if self.R else 0.1
        r_tube, r_node, off = 0.017 * R, 0.085 * R, 0.11 * R
        for a, b in edges:
            if a in nodes and b in nodes:
                p.add_mesh(pv.Line(nodes[a], nodes[b]).tube(radius=r_tube),
                           color=tube_color, opacity=0.9)
        norm = mcolors.Normalize(self.clim[0], self.clim[1])
        cmap = cm.get_cmap(CMAP)

        def has(k):
            return node_T and k in node_T and node_T[k] is not None
        for k, xyz in nodes.items():
            col = cmap(norm(node_T[k]))[:3] if has(k) else "#8a8878"
            p.add_mesh(pv.Sphere(radius=r_node, center=xyz), color=col,
                       smooth_shading=True, ambient=0.45, diffuse=0.6)
        pts = np.array([nodes[k] for k in nodes]) + np.array([off, off * 0.8, 0.0])
        labels = [(f"{k} {node_T[k]:.1f}" if has(k) else k) for k in nodes]
        p.add_point_labels(pts, labels, font_size=13, text_color="black",
                           shape_color="white", shape_opacity=0.78,
                           always_visible=True, show_points=False)

    def _render_circuit(self, nodes, edges, node_T, label, title_extra=""):
        """회로 오버레이(반투명 형상+회로) 1프레임 → Plotter. PNG/GIF 공유."""
        pv = self.pv
        surf = self.solid.extract_surface()
        p = pv.Plotter(off_screen=True, window_size=(1400, 1050))
        p.set_background("white")
        p.add_mesh(surf, color="#c9c2ae", opacity=0.16, lighting=True,
                   smooth_shading=True, ambient=0.5)
        self._add_circuit(p, nodes, edges, node_T)
        p.add_text(f"{label} - thermal circuit overlay{title_extra}",
                   font_size=12, color="black")
        p.view_vector((1, -0.35, 0.45), viewup=(0, 1, 0)); p.camera.zoom(1.2)
        return p

    def _render_cut3d_circuit(self, T, nodes, edges, node_T, label, title_extra=""):
        """3d_cut 반단면 온도장 + 회로 오버레이를 한 장면에(대시보드 좌패널)."""
        self.ext_half.point_data["Temperature (degC)"] = T[self.epid]
        self.solid.point_data["Temperature (degC)"] = T[self.opid]
        sl = self.solid.slice(normal="x")
        p = self.pv.Plotter(off_screen=True, window_size=(1200, 1000))
        p.set_background("white")
        p.add_mesh(self.ext_half, scalars="Temperature (degC)", cmap=CMAP,
                   clim=self.clim, n_colors=14, lighting=True, ambient=0.6,
                   diffuse=0.4, specular=0.0, scalar_bar_args=_sb())
        p.add_mesh(sl, scalars="Temperature (degC)", cmap=CMAP, clim=self.clim,
                   n_colors=14, lighting=False, show_scalar_bar=False)
        self._add_circuit(p, nodes, edges, node_T, tube_color="#5c5b52")
        p.add_text(f"half-section + circuit  {label}{title_extra}",
                   font_size=12, color="black")
        p.view_vector((1, -0.42, 0.40), viewup=(0, 1, 0)); p.camera.zoom(1.0)
        return p

    def circuit_3d_png(self, nodes, edges, node_T=None, label="", fname="circuit_3d.png"):
        """열등가회로 3D 오버레이(최종 t 정적 PNG)."""
        p = self._render_circuit(nodes, edges, node_T, label,
                                  title_extra=" (node color = temperature)")
        pth = os.path.join(self.out, fname); p.screenshot(pth); p.close()
        return pth

    def circuit_3d_gif(self, nodes, edges, node_T_fn, label=""):
        """열등가회로 3D 오버레이 과도 GIF. node_T_fn(T)->{name:T} 로 매 프레임
        노드 온도(색·라벨) 갱신. 노드 위치는 고정, 색스케일은 self.clim 고정."""
        frames = []
        for i in range(self.nsets):
            T = self._T(i)
            p = self._render_circuit(nodes, edges, node_T_fn(T), label,
                                     title_extra=f"  t={self.times[i]:.0f}s")
            frames.append(p.screenshot(return_img=True)); p.close()
        return self._save_gif("transient_circuit_3d", frames)

    # ── 오케스트레이터 ───────────────────────────────────────────────────
    def render_all(self, gifs=STANDARD_GIFS, pngs=STANDARD_PNGS, log=print):
        done = []
        dispatch_gif = {"transient_3d_cut": self.cut3d_gif, "transient_core": self.core_gif,
                        "transient_coilmag": self.coilmag_gif,
                        "transient_coil_z0": self.coil_z0_gif}
        for g in gifs:
            try:
                p, mb = dispatch_gif[g](); done.append(p); log(f"  GIF {g}: {mb:.2f}MB")
            except Exception as e:
                log(f"  GIF {g} FAIL: {repr(e)[:120]}")
        for pngname in pngs:
            try:
                if pngname == "cut_3d": self.cut3d_png()
                elif pngname in ("contour_iso", "contour_z0"):
                    if pngname == "contour_iso": self.contour_png()  # 둘 다 생성
                elif pngname in ("coil_only", "magnet_only"):
                    if pngname == "coil_only": self.component_png()
                elif pngname == "component_history": self.history_png()
                log(f"  PNG {pngname}: ok")
            except Exception as e:
                log(f"  PNG {pngname} FAIL: {repr(e)[:120]}")
        return done


def render_standard_viz(rth_path, out_dir, label="", clim_lo=None, mats=None,
                        z_trim=None, gifs=STANDARD_GIFS, pngs=STANDARD_PNGS,
                        circuit_builder=None, log=print):
    """편의 함수: .rth → 표준 GIF/PNG 세트.

    circuit_builder: callable(tv)->{"nodes","edges","node_T"} 주면 circuit_3d 생성.
    (tv.R 등 형상정보로 노드 위치를 스케일해 만들 수 있게 tv 를 넘긴다.)
    """
    tv = ThermalViz(rth_path, out_dir, label=label, clim_lo=clim_lo, mats=mats,
                    z_trim=z_trim)
    log(f"[{label}] clim={[round(c,1) for c in tv.clim]} "
        f"nsets={tv.nsets} parts={list(tv._sub)} R={tv.R:.3f}")
    done = tv.render_all(gifs=gifs, pngs=pngs, log=log)
    if circuit_builder is not None:
        try:
            c = circuit_builder(tv)
            tv.circuit_3d_png(c.get("nodes", {}), c.get("edges", []),
                              node_T=c.get("node_T"), label=label)
            log("  PNG circuit_3d: ok")
            if c.get("node_T_fn"):
                tv.circuit_3d_gif(c["nodes"], c["edges"], c["node_T_fn"], label=label)
                log("  GIF transient_circuit_3d: ok")
                tv.full_dashboard_gif(c["nodes"], c["edges"], c["node_T_fn"],
                                      label=label)
                log("  GIF transient_dashboard(3panel): ok")
        except Exception as e:
            log(f"  circuit FAIL: {repr(e)[:120]}")
    return done


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(0)
    rth, out = sys.argv[1], sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else ""
    clo = float(sys.argv[4]) if len(sys.argv) > 4 else None
    try:
        render_standard_viz(rth, out, label=label, clim_lo=clo)
        print("DONE-OK")
    except Exception:
        traceback.print_exc()
    os._exit(0)
