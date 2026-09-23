# -*- coding: utf-8 -*-
"""Build drive_model_study.html: a study note on the e10 drive simulation models (theory + implementation).

Companion to gamma_wall_explainer.html (results). Figures come from e10drive/plot_study_figs.py
(+ export_study_data.m); file boxes come from report_links.py.
python make_drive_model_study.py
"""
import base64
import html
import re
from pathlib import Path

from report_links import COPY_JS, FILES_CSS, FMU_PY, LINK_NOTE, files_box, item

HERE = Path(__file__).resolve().parent
E10 = HERE / "e10drive"
DRV = Path(r"D:\KangDH\Thesis\e10\work_lab_pc1\drive")
FMU = Path(r"D:\KangDH\Thesis\e10\work_lab_pc1\fmu")
DATA16 = DRV / "e10_stage1_data_16000_shaft.mat"
SLX2C = DRV / "stage2c" / "e10_stage2c.slx"
MOT = Path(r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot")
FMU_FILE = Path(r"C:\Program Files\ANSYS Inc\v261\motorcad\FMU\Ansys_Motor-CAD_Lab_BPM.fmu")
HARNESS = Path(r"D:\KangDH\Thesis\e10\work_lab_pc1\mw_examples\ex1\HEVPMSMDriveTestHarness.slx")


def img(name, cap):
    b = base64.b64encode((HERE / name).read_bytes()).decode()
    return '<figure><img src="data:image/png;base64,%s" alt="%s"><figcaption>%s</figcaption></figure>' % (
        b, html.escape(re.sub("<[^>]+>", "", cap), quote=True), cap)


def code(src, title=""):
    t = '<div class="codet">%s</div>' % title if title else ""
    return '%s<pre class="code">%s</pre>' % (t, html.escape(src.strip("\n")))


def cmd(text, label="복사"):
    return ('<div class="cmd"><pre>%s</pre><button class="cp" data-copy="%s">%s</button></div>'
            % (html.escape(text), html.escape(text, quote=True), label))


# ------------------------------------------------------------------ block diagram (inline SVG)
def _svg_text(s):
    """'i_d*' -> i<tspan dy=3>d</tspan><tspan dy=-3>*</tspan>; '_{..}' groups allowed."""
    out, i = "", 0
    parts = re.split(r"(_\{[^}]*\}|_[^\s_])", s)
    pending_up = False
    for p in parts:
        if not p:
            continue
        if p.startswith("_"):
            sub = p[2:-1] if p.startswith("_{") else p[1:]
            out += '<tspan dy="3" font-size="9">%s</tspan>' % html.escape(sub)
            pending_up = True
        else:
            if pending_up:
                out += '<tspan dy="-3">%s</tspan>' % html.escape(p)
                pending_up = False
            else:
                out += html.escape(p)
    return out


def svg_block_diagram():
    P = []

    def band(x, y, w, h, label, lx=10):
        P.append('<rect class="sv-band" x="%d" y="%d" width="%d" height="%d" rx="10"/>' % (x, y, w, h))
        P.append('<text class="sv-bandlab" x="%d" y="%d">%s</text>' % (x + lx, y + 17, _svg_text(label)))

    def box(x, y, w, h, lines, cls="sv-blk"):
        P.append('<rect class="%s" x="%d" y="%d" width="%d" height="%d" rx="6"/>' % (cls, x, y, w, h))
        lh = 15
        y0 = y + h/2 - (len(lines) - 1)*lh/2 + 4
        for k, ln in enumerate(lines):
            P.append('<text class="sv-t" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (x + w/2, y0 + k*lh, _svg_text(ln)))

    def arrow(pts, label=None, lx=0, ly=0):
        P.append('<path class="sv-ar" d="M%s" marker-end="url(#svar)"/>' % " L".join("%d,%d" % q for q in pts))
        if label:
            P.append('<text class="sv-lab" x="%d" y="%d">%s</text>' % (lx, ly, _svg_text(label)))

    def mark(x, y, n):
        P.append('<circle class="sv-mk" cx="%d" cy="%d" r="10"/><text class="sv-mkt" x="%d" y="%d" text-anchor="middle">%s</text>'
                 % (x, y, x, y + 4, n))

    band(10, 8, 980, 152, "제어기 — 이산 시간, T_s = 50 µs (캐리어 골·꼭짓점마다 샘플·갱신)")
    band(10, 172, 980, 118, "변조·인버터 — 사건 구동 (스위칭 에지를 정확한 시각에)", lx=110)
    band(10, 302, 980, 160, "플랜트 — 연속 시간 (사건 사이 RK4, h ≤ 2 µs), Motor-CAD Lab 자속·토크맵", lx=370)
    y, h, w = 60, 58, 120
    xs = [20, 158, 296, 434, 572, 710, 848]
    labels = [["토크 지령", "T*"], ["기준표", "i_d*(T), i_q*(T)", "MCB / MBC"], ["PI + 디커플링", "+ 안티와인드업"],
              ["|v| ≤ 403.2 V", "벡터 크기 제한"], ["지연 보상", "각 +ω_e(n+½)T_s"], ["dq → αβ", "θ̂ = θ + θ_{err}"],
              ["n샘플 지연", "(지령 대기열)"]]
    for x, lab in zip(xs, labels):
        box(x, y, w, h, lab)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow([(a + w, y + h//2), (b - 2, y + h//2)])
    mark(434 + w - 4, y + 2, "③")
    mark(710 + w - 4, y + 2, "⑤")
    mark(848 + w - 4, y + 2, "②")
    yb = 214
    xb = [848, 710, 572, 434, 296]
    lb = [["SVPWM", "min-max 영상분"], ["삼각파 비교", "10 kHz, 양 끝 갱신"], ["데드타임 t_d", "에지 지연 (전류 부호)"],
          ["인버터 폴 전압", "±V_{dc}/2 (720 V)"], ["상전압 → αβ", "중성점 부동"]]
    for x, lab in zip(xb, lb):
        box(x, yb, w, h, lab)
    arrow([(908, y + h), (908, yb - 2)])
    for a, b in zip(xb[:-1], xb[1:]):
        arrow([(a, yb + h//2), (b + w + 2, yb + h//2)])
    mark(572 + w - 4, yb + 2, "④")
    box(20, yb, 150, h, ["전류 샘플", "abc → dq (θ̂)"])
    yc = 354
    box(158, yc, 132, 60, ["αβ → dq", "θ = ω_e t (속도 고정)"])
    box(308, yc, 212, 60, ["자속 적분 (상태 λ_d, λ_q)", "dλ/dt = v − R i − jω_e λ"])
    box(538, yc, 118, 60, ["역맵", "i = f⁻¹(λ)"])
    box(674, yc, 132, 60, ["축 토크맵", "T = g(i)"])
    box(824, yc, 146, 60, ["축 토크 출력", "반주기 평균"], cls="sv-out")
    mark(674 + 132 - 4, yc + 2, "①")
    arrow([(356, yb + h), (356, 330), (224, 330), (224, yc - 2)])
    arrow([(290, yc + 30), (306, yc + 30)])
    arrow([(520, yc + 30), (536, yc + 30)])
    arrow([(656, yc + 30), (672, yc + 30)])
    arrow([(806, yc + 30), (822, yc + 30)])
    arrow([(597, yc + 60), (597, 446), (95, 446), (95, yb + h + 2)], label="전류 i", lx=440, ly=440)
    arrow([(95, yb), (95, 144), (356, 144), (356, y + h + 2)], label="î (측정 전류)", lx=120, ly=139)
    defs = ('<defs><marker id="svar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path class="sv-arh" d="M0,0 L10,5 L0,10 z"/></marker></defs>')
    return ('<div class="scroll"><svg class="bd" viewBox="0 0 1000 470" role="img" aria-label="e10 구동 시뮬레이션 블록 구조">'
            + defs + "".join(P) + "</svg></div>")


# ------------------------------------------------------------------ file boxes
RUN2 = ("addpath('%s');\nS = load('%s');\nr = sim_e10_stage2(S, struct('Tref_fn', @(t) 20*(t>=0.005), 'td', 3e-6, 'Tstop', 0.08));\n"
        "plot(r.t*1e3, r.T); xlabel('시간 [ms]'); ylabel('축 토크 [N·m]')") % (E10, DATA16)
RUN2B = ("M = load('%s');\nres = M.out(2).raw.results;            %% VsMax 95 %%\n"
         "g = sortrows(res(res.n == 16000 & res.ExitFlags > 0, :), 'Trq');\n"
         "ref = struct('T', g.Trq, 'id', g.Id, 'iq', g.Iq);\n"
         "r2 = sim_e10_stage2(S, struct('Tref_fn', @(t) 30*(t>=0.005), 'td', 3e-6, 'Tstop', 0.08, 'ref', ref));\n"
         "mean(r2.T(round(0.85*end):end))") % (DRV / "mbc_tables.mat")
RUN2C = "addpath('%s');\nopen_system('%s');\nR = run_e10_stage2c([30 3e-6]);   %% [토크 N·m, 데드타임 s] 한 경우" % (E10, SLX2C)
RUNFMU = '"%s" "%s"' % (FMU_PY, E10 / "lab_fmu.py")
RUNQS = 'python "%s" --map fea --tables 0.05,0.15' % (E10 / "qs_opsolver.py")
RUN2D = ("addpath('%s');\nR = run_e10_stage2d([20 0], 0.08, [], {'fea_avg', 'fea_pos', 'fea_pos_ff'}, 'try.csv', "
         "{'QS 85'})") % E10

B_PLANT = files_box("파일 — 플랜트 데이터", [
    item(MOT, "Motor-CAD 기준 모델 e10Turn6V261 (Lab 빌드 포함)", cmd=""),
    item(E10 / "export_lab_satmap.py", "Lab Saturation & Loss Map을 dq 격자로 내보내기"),
    item(E10 / "prep_e10_maps_lab.m", "속도별 맵 → e10_plant_lab.mat (M(iq, id) 저장)"),
    item(E10 / "prep_e10_stage1.m", "대칭 확장·역맵 i(λ) 생성"),
    item(E10 / "apply_mcb_reference.m", "MCB 기준표 + 대칭 확장 조합"),
    item(DRV / "e10_plant_lab.mat", "플랜트 맵 (2/4/8/16 krpm 축 토크 포함)"),
    item(DATA16, "16 krpm 시뮬레이션 입력 (맵·역맵·기준표·제원)")])
B_REGION = files_box("파일 — 운전 영역 그림", [
    item(E10 / "export_study_data.m", "그림용 배열 내보내기 (MATLAB table → 배열)", cmd="addpath('%s'); export_study_data" % E10),
    item(DRV / "study_data.mat", "맵·MCB·MBC 16 krpm 배열 (v7)"),
    item(E10 / "plot_study_figs.py", "이 페이지 그림 6장"),
    item(Path(r"D:\KangDH\Thesis\e10\work_lab_pc1\existing\lab_points_16k.csv"), "Lab 자체 16 krpm 운전점 궤적")])
B_CTRL = files_box("파일 — 제어기", [
    item(E10 / "sim_e10_stage2.m", "제어기 코드 (84–97행)", cmd=RUN2),
    item(E10 / "sim_e10_stage1.m", "단계 1 스크립트판 (같은 제어기, dq 지연)"),
    item(E10 / "build_e10_stage1.m", "단계 1 Simulink 모델 생성", cmd="addpath('%s'); S = load('%s'); build_e10_stage1(S)" % (E10, DATA16)),
    item(E10 / "e10_stage1.slx", "생성된 단계 1 모델")])
B_TIME = files_box("파일 — 이산 시간·변조·데드타임", [
    item(E10 / "sim_e10_stage2.m", "샘플(79–84행), 지연 대기열(94–97), SVPWM(99–101), 데드타임 보상(102–112), 사건 목록(115–)", cmd=RUN2),
    item(DRV / "stage2_results.csv", "지연·보상·데드타임 격자 결과"),
    item(DRV / "stage2_traces.mat", "상전류 파형"),
    item(E10 / "plot_stage2.py", "결과 그림·THD")])
B_EVENT = files_box("파일 — 사건 구동 적분", [
    item(E10 / "sim_e10_stage2.m", "integrate() · fdot() 보조 함수 (파일 끝)", cmd=RUN2),
    item(E10 / "run_e10_stage2.m", "격자 실행 (part = [i n]으로 독립 배치 분할)", cmd="addpath('%s'); run_e10_stage2([], 0, [1 1])" % E10),
    item(E10 / "merge_e10_stage2.m", "배치 결과 합치기")])
B_LUT = files_box("파일 — 기준표", [
    item(E10 / "mcb_ref_from_lab.m", "MCB mcb.generateMotorLUT (FluxDQ, vclmt)"),
    item(DRV / "mcb_lut_shaft.mat", "MCB 기준표 (축 토크)"),
    item(E10 / "mbc_ref_from_lab.m", "MBC calibratepmsm (VsMax 100/95/90 %)", cmd="addpath('%s'); M = mbc_ref_from_lab([], [1 0.95 0.9]);" % E10),
    item(DRV / "mbc_tables.mat", "MBC 표 + TPA 결과"),
    item(E10 / "run_e10_stage2b.m", "표 4종을 스위칭 모델에 넣어 비교", cmd="addpath('%s'); t = run_e10_stage2b();" % E10)])
B_SIM = files_box("파일 — Simscape 모델", [
    item(SLX2C, "모델 — 제어기 'ctrl'·변조기 'modg' MATLAB Function, 모델 작업공간 Tref_Nm·td_s·Tstop"),
    item(E10 / "build_e10_stage2c.m", "하니스 복사·개조 스크립트 (블록 교체 과정이 코드로 남아 있음)"),
    item(E10 / "run_e10_stage2c.m", "경우별 실행·스크립트 모델과 비교", cmd=RUN2C),
    item(DRV / "stage2c_results.csv", "비교 결과"),
    item(HARNESS, "원본 MathWorks HEV PMSM Drive Test Harness")])
B_FMU = files_box("파일 — Lab FMU", [
    item(E10 / "export_lab_model.py", "새 Motor-CAD 창에서 .lab 내보내기 (사용자 창은 건드리지 않음)"),
    item(FMU / "e10Turn6V261.lab", "FMU가 읽는 Lab 모델", cmd=""),
    item(FMU_FILE, "Ansys Motor-CAD Lab BPM FMU", cmd=""),
    item(E10 / "lab_fmu.py", "FMU 래퍼 (모드 0/1/2)", cmd=RUNFMU),
    item(E10 / "lab_gamma_sweep.py", "진각 강제 스윕"),
    item(E10 / "lab_stage3c.py", "스위칭 모델 도달점의 손실"),
    item(FMU / "lab_gamma_sweep.json", "스윕 결과", cmd=""),
    item(FMU / "lab_stage3c.json", "3(c) 결과", cmd="")])
FP = Path(r"D:\KangDH\Thesis\e10\work_lab_pc1\fea_pos")
B_POS = files_box("파일 — 직접 FEA 위치별 맵", [
    item(E10 / "fea_posmap.py", "위치별 FEA 포화맵 (새 Motor-CAD 창, 모델 사본, 조각·재개)",
         cmd='python "%s" --tag band' % (E10 / "fea_posmap.py")),
    item(E10 / "mc_launch.py", "숨은 Motor-CAD 인스턴스 기동, PID 기록"),
    item(FP / "posmap_band_00.mat", "조각 00 (i_q = −13 A, i_d 29점 × 위치 121)"),
    item(E10 / "fea_posmap_analyze.py", "정렬·Park 변환·Lab 대조·고조파·Simscape 표 생성"),
    item(FP / "posmap_band_analysis.json", "대조·고조파·운전점 파형", cmd=""),
    item(DRV / "stage2d_tables.mat", "Simscape 표 V_lab_conv · V_fea_avg · V_fea_pos")])
B_HARM = files_box("파일 — 고조파와 제어기 (단계 2d)", [
    item(E10 / "patch_stage2c_ctrl.m", "저장된 모델의 'ctrl'에 P.ffRef(기준 전류 디커플링) 추가"),
    item(E10 / "run_e10_stage2d.m", "표 변형 × 기준표 × 토크 × 데드타임",
         cmd="addpath('%s'); R = run_e10_stage2d([20 0], 0.08, [], {'fea_pos', 'fea_pos_ff'}, 'try.csv', {'QS 85'});" % E10),
    item(DRV / "stage2d_results.csv", "A–D·D_ff × MCB·MBC 95"),
    item(DRV / "stage2d_results_qs.csv", "C·D·D_ff × QS 표(여유 5–20 %; 25·30 %는 _qs2·_qs3.csv)"),
    item(E10 / "qs_harmonic_margin.py", "D 실현점의 남은 여유와 고정 여유 예측 시험"),
    item(E10 / "plot_fea_check.py", "그림 (stage2d_margin.png 등)")])
B_QS = files_box("파일 — 정상상태 운전점 계산기", [
    item(E10 / "qs_opsolver.py", "계산기 (Maps, best_point, held_point, ref_tables)",
         cmd='python "%s" --map fea --td 3e-6 --margin 0.05' % (E10 / "qs_opsolver.py")),
    item(DRV / "qs_tables.mat", "QS 기준표 (여유 5–30 %, Tv·idRef·iqRef)"),
    item(FP / "qs_fea_td3_m0.05.json", "계산 결과 예 (FEA 맵, 데드타임 3 µs, 여유 5 %)", cmd=""),
    item(FP / "qs_margin_cost.json", "QS 표 점의 16 krpm 손실 (여유의 비용)", cmd=""),
    item(E10 / "qs_harmonic_hb.py", "슬롯 고조파 조화균형 확장 — 실행하면 Simscape 2d 전 경우와 비교",
         cmd='python "%s"' % (E10 / "qs_harmonic_hb.py")),
    item(FP / "qs_harmonic_hb.json", "조화균형 계산 대 Simscape", cmd="")])
B_REM = files_box("파일 — 대책 시험 (단계 2e)", [
    item(E10 / "build_e10_stage2e.m", "2c 모델 복사 + 제어기에 대책 선택지 추가 (코드 전체)",
         cmd="addpath('%s'); build_e10_stage2e();" % E10),
    item(DRV / "stage2e" / "e10_stage2e.slx", "대책 선택지가 든 Simscape 모델 — 'ctrl' 블록 열기"),
    item(E10 / "run_e10_stage2e.m", "대책 이름 'base' 'notch' 'pr6' 'hex' 'fw' 'ffref', 조합 'notch+fw'",
         cmd="addpath('%s'); R = run_e10_stage2e([20 0], 0.08, [], {'fea_pos'}, 'try.csv', {'QS 95'}, {'base', 'notch'});" % E10),
    item(DRV / "stage2e_results_D.csv", "위치별 맵(D) 결과"),
    item(E10 / "qs_harmonic_hb.py", "조화균형 계산의 대책 선택지 (notch, hexk, fw)",
         cmd='python "%s" remedies' % (E10 / "qs_harmonic_hb.py"))])
B_GEN = files_box("파일 — 이 페이지", [
    item(HERE / "make_drive_model_study.py", "이 페이지 생성기"),
    item(E10 / "plot_study_figs.py", "그림 6장"),
    item(HERE / "report_links.py", "파일 상자 도우미"),
    item(HERE / "gamma_wall_explainer.html", "결과 페이지", cmd="")])

# ------------------------------------------------------------------ code excerpts (from sim_e10_stage2.m)
C_PLANT = """
function df = fdot(Gid, Giq, f, vab, Rph, we, t)
i = fluxToI(Gid, Giq, f);            % 역맵: (λd, λq) -> (id, iq)
v = rot(vab, -we*t);                 % 정지 좌표계 전압을 회전자 좌표계로
df = [v(1) - Rph*i(1) + we*f(2);     % dλd/dt = vd - R id + ωe λq
      v(2) - Rph*i(2) - we*f(1)];    % dλq/dt = vq - R iq - ωe λd
end"""
C_CTRL = """
ed = idc - i_meas(1);  eq = iqr - i_meas(2);
vu = complex(Kpd*ed, Kpq*eq) + X + complex(-we*Lq*i_meas(2), we*(Ld*i_meas(1) + lam));
vmag = abs(vu);
if vmag > Vmax, vs = vu*Vmax/vmag; sat = 1; else, vs = vu; sat = 0; end
X = X + Ts*(complex(Kid*ed, Kiq*eq) + Kaw*(vs - vu));   % 역계산 안티와인드업
vc = vs*exp(1i*thc);                                     % 지연 보상 thc = we*(n_delay+0.5)*Ts
vab_cmd = rot([real(vc); imag(vc)], theta0 + th);        % 제어기 각도(오프셋 포함)로 αβ
vab_q = [vab_q(:, 2:end), vab_cmd];  vab_app = vab_q(:, 1);   % n_delay 샘플 대기열"""
C_MOD = """
vabc = clarkeInv(vab_app);
vzs = -(max(vabc) + min(vabc))/2;           % min-max 영상분 = SVPWM
duty = 0.5 + (vabc + vzs)/Vdc;
if dtComp && td > 0                         % 에지가 밀리는 반주기에서만 보정
    if mod(n-1, 2) == 0, duty = duty + (i_abc > 0)*td/Ts;    % 상승 반주기: 켜짐 에지
    else,                duty = duty - (i_abc < 0)*td/Ts;    % 하강 반주기: 꺼짐 에지
    end
end"""
C_REM = """
% (3) 노치: dq 변환 직후, PI·디커플링 앞 - 조절기가 슬롯 고조파 전류를 못 보게 한다
if P.notch > 0
    [idm, zd] = biq2(idm, zn(1:4), P.nb1, P.na1, P.nb2, P.na2);
    [iqm, zq] = biq2(iqm, zn(5:8), P.nb1, P.na1, P.nb2, P.na2);
    zn = [zd; zq];
end
idr = interp1(P.Tv, P.idRef, Tc) + idfw;        % (5) 약자속 루프가 더하는 id
iqr = interp1(P.Tv, P.iqRef, Tc);
ed = idr - idm;  eq = iqr - iqm;
if P.ffRef > 0, idf = idr; iqf = iqr; else, idf = idm; iqf = iqm; end   % (2) 기준 전류 디커플링
vud = P.Kpd*ed + X(1) - P.we*P.Lq*iqf;
vuq = P.Kpq*eq + X(2) + P.we*(P.Ld*idf + P.lam);
% (3) 6차 공진(PR): 앞 샘플이 잘렸으면 입력 0 (조건부 적분)
if P.pr6 > 0
    edi = ed*(1 - satPrev);  eqi = eq*(1 - satPrev);  cw = 2*cos(P.prw);
    yd = cw*zr(1) - zr(2) + 2*P.prKd*P.Ts*(P.prc0*edi - P.prc1*zr(3));
    yq = cw*zr(4) - zr(5) + 2*P.prKq*P.Ts*(P.prc0*eqi - P.prc1*zr(6));
    zr = [yd; zr(1); edi; yq; zr(4); eqi];
    vud = vud + yd;  vuq = vuq + yq;
end
vmag = sqrt(vud^2 + vuq^2);
% (4) 한계: 원(기본) 또는 육각형(과변조, 방향 유지)
if P.hex > 0
    ph = th0 + P.thc + atan2(vuq, vud);                 % 정지 좌표계 전압각
    vlim = P.khex*P.Vdc/sqrt(3)/cos(mod(ph, pi/3) - pi/6);
else
    vlim = P.Vmax;
end
if vmag > vlim, vsd = vud*vlim/vmag; vsq = vuq*vlim/vmag; sat = 1; else, vsd = vud; vsq = vuq; sat = 0; end
satPrev = sat;
X(1) = X(1) + P.Ts*(P.Kid*ed + P.Kaw*(vsd - vud));     % 역산 안티와인드업
X(2) = X(2) + P.Ts*(P.Kiq*eq + P.Kaw*(vsq - vuq));
% (5) 전압 피드백 약자속: 잘린 만큼 id* 를 더 깊게, 누설로 천천히 되돌림
if P.fw > 0
    idfw = min(0, idfw + P.Ts*(-P.Kfw*max(vmag - vlim, 0) - P.Kleak*idfw));
end

function [y, z] = biq2(x, z, b1, a1, b2, a2)   % 두 biquad 직렬 (직접형 II 전치)
y1 = b1(1)*x + z(1);  z(1) = b1(2)*x - a1(2)*y1 + z(2);  z(2) = b1(3)*x - a1(3)*y1;
y  = b2(1)*y1 + z(3); z(3) = b2(2)*y1 - a2(2)*y + z(4);  z(4) = b2(3)*y1 - a2(3)*y;
end"""
C_NOTCH = """
% 노치 계수 - 속도(we)가 바뀌면 다시 계산한다
w1  = mod(6*we*Ts, 2*pi);                                % 6차: 16 krpm 에서 6.4 kHz
w12 = mod(12*we*Ts, 2*pi);  w2 = min(w12, 2*pi - w12);   % 12차 12.8 kHz -> 20 kHz 샘플에서 7.2 kHz
[b1, a1] = notchC(w1, 0.9);  [b2, a2] = notchC(w2, 0.9);
phi = pi/2 + 1.5*w1;                                     % PR 의 지연 보상 위상

function [b, a] = notchC(w0, r)
b = [1, -2*cos(w0), 1];  a = [1, -2*r*cos(w0), r^2];
b = b*sum(a)/sum(b);                                     % 직류 이득 1
end"""
C_EVENT = """
% 반주기 안: 다음 사건 = min(지령 에지, 데드타임으로 밀린 에지, 반주기 끝)
[flux, Tseg, Vseg] = integrate(Gid, Giq, GT, flux, pole, Vdc, Rph, we, t, tNext, hmax);
...
if td > 0                                   % 지령 에지가 데드타임에 걸리는가
    ix = clarkeInv(rot(fluxToI(Gid, Giq, flux), we*t));
    delayed = (sNew == 1 && ix(x) > 0) || (sNew == 0 && ix(x) < 0);
    if delayed, pend(x, :) = [t + td, sNew]; continue; end
end
pole(x) = sNew;

function [flux, Tint, Vint] = integrate(...)   % 폴 상태 고정 구간 [ta, tb]
vp = Vdc*(pole - 0.5);  vn = vp - mean(vp);    % 중성점 부동 상전압
vab = [vn(1); (vn(2) - vn(3))/sqrt(3)];
ns = max(1, ceil((tb - ta)/hmax));            % RK4 부분 스텝 ≤ h_max""".replace("...", "…")

CSS = """
:root{--bg:#fbfaf7;--card:#fff;--fg:#1f2328;--mut:#5d6670;--line:#dcd7ce;--acc:#8a4b1f;--hl:#fff3e6;--ok:#1f7a45;--warn:#a86a12;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15171a;--card:#1d2024;--fg:#e8e5df;--mut:#a4abb2;--line:#383c42;--acc:#e0a36e;--hl:#2a2218;--ok:#6fd39a;--warn:#e3b25d;--bad:#f08a80}}
:root[data-theme="dark"]{--bg:#15171a;--card:#1d2024;--fg:#e8e5df;--mut:#a4abb2;--line:#383c42;--acc:#e0a36e;--hl:#2a2218;--ok:#6fd39a;--warn:#e3b25d;--bad:#f08a80}
body{background:var(--bg);color:var(--fg);font:15px/1.75 system-ui,"Malgun Gothic","Apple SD Gothic Neo",sans-serif;margin:0}
main{max-width:1000px;margin:0 auto;padding:18px 16px 64px}
h1{font-size:23px;line-height:1.3;margin:6px 0}h2{font-size:19px;margin:36px 0 8px;padding-bottom:4px;border-bottom:2px solid var(--acc)}
h3{font-size:16px;margin:20px 0 6px}.mut{color:var(--mut)}a{color:var(--acc)}
nav{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}nav a{border:1px solid var(--line);border-radius:999px;padding:2px 11px;color:var(--fg);text-decoration:none;font-size:13.5px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:12px 0}
.kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:14px 0}
.kpi div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:9px 12px;font-size:13.5px}.kpi b{display:block;font-size:19px;color:var(--acc)}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13.5px;margin:6px 0}
td,th{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}td:first-child,th:first-child{white-space:nowrap}th{color:var(--mut);font-weight:600}
.eq{font-family:"Cambria Math","Times New Roman",serif;background:var(--hl);padding:9px 12px;border-radius:6px;overflow-x:auto;font-size:15px;line-height:1.9;margin:8px 0}
figure{margin:12px 0}img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px;background:#fff}
figcaption{font-size:13px;color:var(--mut)}code{font-size:13px;word-break:break-all}
.codet{font-size:12.5px;color:var(--mut);margin-top:10px}
pre.code{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:8px 10px;overflow-x:auto;font:12.5px/1.5 ui-monospace,Consolas,monospace;margin:4px 0 10px}
.cmd{position:relative;margin:6px 0}.cmd pre{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:8px 70px 8px 10px;overflow-x:auto;font:12.5px/1.5 ui-monospace,Consolas,monospace;margin:0}
.cmd button.cp{position:absolute;top:6px;right:6px}
details.q{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:6px 12px;margin:8px 0}
details.q summary{cursor:pointer;font-weight:600}
.note{border-left:4px solid var(--warn);padding:6px 12px;background:var(--card);border-radius:0 8px 8px 0;margin:10px 0}
svg.bd{width:100%;min-width:760px;height:auto;font-family:system-ui,"Malgun Gothic",sans-serif}
.sv-band{fill:none;stroke:var(--line);stroke-width:1.5;stroke-dasharray:6 4}
.sv-bandlab{fill:var(--mut);font-size:12.5px;font-weight:600}
.sv-blk{fill:var(--card);stroke:var(--fg);stroke-opacity:.5;stroke-width:1.2}
.sv-out{fill:var(--hl);stroke:var(--acc);stroke-width:1.4}
.sv-t{fill:var(--fg);font-size:12px}.sv-lab{fill:var(--mut);font-size:11.5px}
.sv-ar{fill:none;stroke:var(--mut);stroke-width:1.5}.sv-arh{fill:var(--mut)}
.sv-mk{fill:var(--acc)}.sv-mkt{fill:#fff;font-size:12px;font-weight:700}
""" + FILES_CSS

wTs = 19.2
body = f"""
<h1>e10 구동 시뮬레이션 모델 해설 — 이론과 구현</h1>
<p class="mut">진각 벽 연구(<a href="gamma_wall_explainer.html">결과 페이지</a>)에 쓴 모델들이 무엇을 풀고 왜 그렇게 만들었는지 정리한 스터디 노트 · 대상 e10 기준기(Motor-CAD Lab 맵), 16 krpm, 직류 720 V · 2026-09-23 PC1</p>
<p>각 절은 <b>이론 → 구현(실제 코드 발췌) → 파일</b> 순서다. 파일 상자에서 모델·스크립트·데이터를 바로 열 수 있다. <span class="mut">{LINK_NOTE}</span></p>
<div class="kpi">
<div>전기 주파수<b>1066.7 Hz</b>4극쌍 × 16 krpm</div>
<div>샘플·갱신<b>20 kHz</b>샘플당 전기각 {wTs}°</div>
<div>캐리어<b>10 kHz</b>펄스비 9.4</div>
<div>전류 루프 대역<b>1.59 kHz</b>K<sub>p</sub>/L = 10<sup>4</sup> rad/s</div>
<div>상전압 한계<b>403.2 V 첨두</b>= 285.1 V rms</div>
</div>
<nav><a href="#ladder">1 모델 사다리</a><a href="#arch">2 전체 구조</a><a href="#plant">3 플랜트</a><a href="#region">4 운전 영역</a><a href="#ctrl">5 제어기</a><a href="#delay">6 이산 시간·지연</a><a href="#pwm">7 변조</a><a href="#dead">8 데드타임</a><a href="#event">9 사건 구동 적분</a><a href="#lut">10 기준표</a><a href="#simscape">11 Simscape</a><a href="#fmu">12 Lab FMU</a><a href="#posmap">13 위치별 FEA 맵</a><a href="#harm">14 고조파와 제어기</a><a href="#qs">15 정상상태 계산기</a><a href="#vv">16 검증</a><a href="#try">17 직접 해보기</a><a href="#ref">18 참고</a></nav>

<h2 id="ladder">1. 모델 사다리 — 무엇을 어느 모델로 보나</h2>
<div class="scroll"><table><tr><th>단계</th><th>모델</th><th>시간 해상도</th><th>담는 것</th><th>빠진 것</th><th>비용</th></tr>
<tr><td>0</td><td>(I, γ) 격자 몬테카를로</td><td>정상상태</td><td>각도 오차 → 토크·전압 산포</td><td>동특성, 제어</td><td>수 초</td></tr>
<tr><td>1</td><td>평균값 dq (Simulink·스크립트)</td><td>이산 제어 50 µs + 연속 플랜트</td><td>PI 포화, 레졸버 오프셋</td><td>스위칭, 데드타임; 지연을 dq에서 걸어 물리와 다름(6절)</td><td>수 초</td></tr>
<tr><td>2</td><td>사건 구동 스위칭 스크립트</td><td>스위칭 에지 정확, RK4 ≤ 2 µs</td><td>SVPWM, 데드타임, 지연의 실제 기하, 전류 리플</td><td>다이오드 도통 세부, 직류단 동특성, 손실, 공간 고조파(슬롯·코깅)</td><td>0.08 s에 약 2 s</td></tr>
<tr><td>2b</td><td>단계 2 + 교정표 교체</td><td>같음</td><td>교정 전압 여유의 효과</td><td>—</td><td>같음</td></tr>
<tr><td>2c</td><td>Simscape Electrical (HEV 하니스 개조)</td><td>가변 스텝 ode23t</td><td>실제 게이트 블랭킹·다이오드·회로망</td><td>손실(이상 스위치), 공간 고조파(맵을 각도별로 복제)</td><td>경우당 11–22 s</td></tr>
<tr><td>3</td><td>Motor-CAD Lab FMU</td><td>준정적 운전점</td><td>손실(교류 동손 하이브리드 맵·철손·기계손), Lab 전압</td><td>과도, 제어</td><td>호출당 약 1 s</td></tr>
<tr><td>2d</td><td>단계 2c + 직접 FEA 위치별 맵(13절)</td><td>같음</td><td>슬롯 고조파(dq 6·12차), 손실 규약 축 토크, 입력측 교류 저항</td><td>손실(이상 스위치), 과변조</td><td>경우당 11–23 s</td></tr>
<tr><td>QS</td><td>정상상태 운전점 계산기(15절)</td><td>정상상태</td><td>유효 전압한계(클램프 − 데드타임 − 교류 저항), 여유를 정확히 둔 기준표</td><td>제어기 동특성, 고조파–제어기 상호작용(14절)</td><td>표 한 벌 수 초</td></tr></table></div>
<p><b>설계 원칙:</b> 단계 0–3은 같은 플랜트 데이터(Lab 자속·토크맵)를 쓴다. 단계 사이 차이는 <b>전압이 어떻게 만들어지고 걸리는지</b>에만 있다. 그래서 결과가 바뀌면 원인을 한 가지로 좁힐 수 있다. 예를 들어 단계 1→2에서 지연 결론이 바뀐 것은 전압 인가 방식 하나 때문이다. 단계 2d도 같은 원칙이다. 모델은 그대로 두고 전동기 표만 A→D로 한 요인씩 바꾼다(손실 규약 → 직접 FEA 평균 → 위치별).</p>

<h2 id="arch">2. 전체 구조 — 세 가지 시간 영역</h2>
{svg_block_diagram()}
<p class="mut">동그라미 번호는 결과 페이지 2.2절의 원인 번호와 같다: ① 각도 민감도(토크맵에서 dT/dγ가 큼), ② 연산 지연, ③ 전압 포화, ④ 데드타임, ⑤ 레졸버 오프셋.</p>
<ul>
<li><b>제어기(이산)</b>: 캐리어 골과 꼭짓점마다(50 µs) 전류를 읽고 전압 지령을 한 번 계산한다. 실제 DSP 제어와 같은 구조다.</li>
<li><b>변조·인버터(사건 구동)</b>: 듀티를 스위칭 시각으로 바꾸고, 데드타임에 걸린 에지는 t<sub>d</sub>만큼 뒤로 민다. 에지 시각을 정확히 다루는 것이 이 모델의 핵심이다(9절).</li>
<li><b>플랜트(연속)</b>: 폴 상태가 바뀌지 않는 구간마다 자속 미분방정식을 RK4로 적분한다.</li>
</ul>
{img("study_freq_ladder.png", "그림 1. 16 krpm 운전점의 주파수 사다리. 기본파(1067 Hz)가 전류 루프 대역(1.59 kHz) 바로 아래에 있고, 전기 한 주기에 캐리어가 9.4번뿐이다 — 저속 드라이브의 ‘연속 시간 근사’가 통하지 않는 영역")}
<p>이 비율이 16 krpm 문제를 어렵게 만든다. 샘플 한 번에 회전자가 전기각 {wTs}° 돌기 때문에 “샘플 사이 회전은 무시한다”는 근사가 안 된다(6절). 지연 1.5 T<sub>s</sub> = 75 µs는 전류 루프 교차 주파수에서 위상 43°를 먹어, 위상 여유가 약 47°로 줄어든다.</p>

<h2 id="plant">3. 플랜트 — 자속을 상태로 둔 dq 모델</h2>
<div class="eq">v<sub>dq</sub> = R i<sub>dq</sub> + dλ<sub>dq</sub>/dt + ω<sub>e</sub> J λ<sub>dq</sub>, &nbsp; J = [0 −1; 1 0]
<br>⇒ dλ<sub>d</sub>/dt = v<sub>d</sub> − R i<sub>d</sub> + ω<sub>e</sub> λ<sub>q</sub>, &nbsp;&nbsp; dλ<sub>q</sub>/dt = v<sub>q</sub> − R i<sub>q</sub> − ω<sub>e</sub> λ<sub>d</sub>
<br>i<sub>dq</sub> = f<sup>−1</sup>(λ<sub>d</sub>, λ<sub>q</sub>) (역맵), &nbsp; T<sub>축</sub> = g(i<sub>d</sub>, i<sub>q</sub>) (Lab 축 토크맵)</div>
<ul>
<li><b>왜 전류가 아니라 자속을 상태로 두나.</b> 포화·교차포화 맵에서 인덕턴스는 증분 인덕턴스 행렬 L<sub>inc</sub>(i) = ∂λ/∂i로 매 순간 바뀐다. 전류를 상태로 두면 매 스텝 이 행렬을 수치 미분해 뒤집어야 한다. 자속을 상태로 두면 미분방정식에는 선형 부분(R, ω<sub>e</sub> 결합)만 남고, 비선형은 출력 룩업(역맵)으로 옮겨 간다. 대가는 순맵 λ(i)를 λ 격자로 뒤집은 역맵 표가 필요하다는 것이다. 왕복 오차는 약 0.06 A였다(Simscape 비교에서 확인).</li>
<li><b>좌표 규약.</b> 진폭 불변 Clarke 변환(i<sub>α</sub> = i<sub>a</sub>)이라 모든 dq 양은 상 첨두값이다. 전압 한계 403.2 V 첨두는 Lab이 720 V에서 쓰는 상전압 한계 285.1 V rms에 해당한다. 선형 SVPWM 상한 V<sub>dc</sub>/√3 = 415.7 V 첨두(293.9 V rms)보다 3 % 낮다.</li>
<li><b>토크.</b> 자속에서 바로 나오는 전자기 토크는 T<sub>em</sub> = (3/2) p (λ<sub>d</sub> i<sub>q</sub> − λ<sub>q</sub> i<sub>d</sub>)다. 모델은 대신 Lab의 <b>축 토크맵</b>을 쓴다. 이 맵은 철손·자석손을 토크로 환산해 뺀 값이다. 질문이 “축에 나오는 토크”이기 때문이다. 20 N·m 운전점에서 T<sub>em</sub>은 약 2 N·m 크다.</li>
<li><b>맵 대칭 확장.</b> Lab export는 i<sub>q</sub> ≥ 0 한 사분면뿐이다. 그래서 λ<sub>d</sub>는 i<sub>q</sub>에 대해 우함수, λ<sub>q</sub>와 토크는 기함수로 펼쳤다. 펼치지 않으면 과도 중 i<sub>q</sub>가 0을 스칠 때 맵 경계에 붙어 γ = 90.00°에서 멈춘다.</li>
<li><b>제원.</b> p = 4, R = 0.0786 Ω(80 °C), λ<sub>m</sub> = 0.2195 Wb(16 krpm 역기전력 1042 V rms), 전류 한계 460 A rms. 속도는 고정이다(다이나모 조건, 기계 방정식 없음).</li>
</ul>
<div class="note"><b>한계 — 회전자 위치 의존성과 FEA 해상도 (13–14절에서 확인).</b>
<ul>
<li><b>공간 고조파가 없다.</b> Lab의 Saturation & Loss Map export는 전류점마다 평균 ψ<sub>d</sub>, ψ<sub>q</sub>, 토크(51×51)만 주고 회전자 위치 차원이 없다. 그래서 단계 0–3의 스크립트와 Simscape는 슬롯 고조파·코깅·역기전력 고조파가 없는 기계를 푼다. <b>→ 13절의 위치별 FEA 맵으로 단계 2d에서 넣었다.</b></li>
<li><b>빠진 토크 리플의 크기.</b> Lab은 빌드 점에서 토크 리플 크기(첨두–첨두)만 계산해 둔다. 16 krpm 기준표 운전점에서 약 48 N·m(20 N·m 지령)–71 N·m(80 N·m 지령) p-p로 평균 토크와 같거나 크다(직접 FEA 47–75 N·m). 이 성분은 전기 주파수의 6의 배수(6.4 kHz 이상)라 전류 루프(1.6 kHz)가 보정할 수 없다. <b>그래도 무해하지 않다.</b> 제어기가 이 고조파 전류에 반응하면 전압 한계에서 평균 운전점이 틀어진다(14절).</li>
<li><b>FEA 해상도.</b> Lab 포화 모델은 FEA 48점을 보간한다. 전류 0/130/260/390/520/651 A 첨두 × 진각 0–90° 8점(12.86° 간격)이다. 16 krpm 운전 영역(195–250 A, 84–90°)은 130·260 A × 77.1°·90° 네 점 사이 한 칸 안에 있다. 맵, FMU, 단계 0 격자가 모두 같은 Lab 모델에서 나왔으므로 서로 맞는다고 이 보간이 검증되지는 않는다. <b>→ 운전 대역 직접 FEA와 자속 0.9 %, 토크 0.8 %, dT/dγ 0.06 N·m/° 안에서 같다(13절). 보간은 맞다.</b></li>
<li><b>교차 확인 하나.</b> Lab이 적어 둔 단락전류 <code>Isc_MotorLAB</code> = 272.67 A가, 맵에서 구한 λ<sub>d</sub> = 0 점 −272.7 A 첨두와 일치한다.</li>
</ul></div>
{code(C_PLANT, "구현 — sim_e10_stage2.m 의 fdot (플랜트 미분방정식)")}
{B_PLANT}

<h2 id="region">4. 운전 영역 — 전류 원, 전압 타원, MTPA와 약자속</h2>
<div class="eq">전류 한계: &nbsp; i<sub>d</sub><sup>2</sup> + i<sub>q</sub><sup>2</sup> ≤ I<sub>max</sub><sup>2</sup> &nbsp;(650.5 A 첨두)
<br>전압 한계: &nbsp; |v| ≈ ω<sub>e</sub> |λ(i)| ≤ V<sub>max</sub> &nbsp;⇔&nbsp; |λ(i)| ≤ V<sub>max</sub>/ω<sub>e</sub> = 0.0602 Wb (16 krpm)
<br>선형 근사: &nbsp; (λ<sub>m</sub> + L<sub>d</sub> i<sub>d</sub>)<sup>2</sup> + (L<sub>q</sub> i<sub>q</sub>)<sup>2</sup> ≤ (V<sub>max</sub>/ω<sub>e</sub>)<sup>2</sup> &nbsp;— 중심 i<sub>ch</sub> = −λ<sub>m</sub>/L<sub>d</sub>인 타원</div>
<p>16 krpm에서 허용 자속은 0.0602 Wb로, 무부하 자석 자속 0.2195 Wb의 27 %다. <b>자석 자속의 73 %를 −d축 전류로 지워야</b> 한다. 속도가 오르면 전압 타원은 특성전류점 쪽으로 오그라든다. 특성전류점은 λ<sub>d</sub> = 0인 점으로, 선형 근사로는 −258 A, 포화 맵으로는 −273 A 첨두다. 이 점이 전류 원 안에 있어 이 기계는 이론상 속도 한계가 없다. 대신 고속에서는 모든 운전점이 이 작은 타원 안에 몰린다.</p>
<ul>
<li><b>MTPA</b>(전류당 최대 토크): 저속에서 전압 여유가 있을 때의 궤적.</li>
<li><b>약자속(FW)</b>: 전압 타원과 토크 등고선의 교점 가운데 전류가 가장 작은 점. MCB·MBC 기준표가 16 krpm에서 고르는 점이다.</li>
<li><b>MTPV</b>(전압당 최대 토크): 타원 안에서 토크가 최대인 점. 16 krpm 폐루프 상한 약 87 N·m가 여기다.</li>
</ul>
{img("study_idiq_plane.png", "그림 2. i<sub>d</sub>–i<sub>q</sub> 평면(Lab 맵). (a) 속도별 전압 한계와 MTPA. (b) 16 krpm 확대: 저토크 운전점은 타원 중심(특성전류점 −273 A)이 아니라 전류가 가장 작은 오른쪽 끝(i<sub>q</sub> = 0에서 −191 A)에 붙는다. MCB 표는 100 % 선 위에 있고, MBC 95/90 % 표는 안쪽 등전압선을 따라 −d축 쪽으로 옮겨 간다")}
<p><b>γ가 90°에 붙는 이유.</b> 토크가 작으면 i<sub>q</sub>가 작고, 전압을 맞추려면 i<sub>d</sub>는 약 −190 A 아래로 줄일 수 없다. 그래서 γ = atan(−i<sub>d</sub>/i<sub>q</sub>)가 90°로 간다. 그림 3은 이 자리에서 진각 1°의 값이 얼마나 비싼지 보여 준다.</p>
{img("study_sensitivity.png", "그림 3. 같은 전류에서 진각만 바꿀 때: (a) 토크는 1°에 11–13 N·m 변한다(20 N·m 운전점에서 1°가 56 %). (b) 상전압은 γ가 커질수록 줄어든다 — 운전점은 한계선을 막 만족하는 자리다. 전압이 모자라면(데드타임 등) 운전점이 γ가 큰 쪽으로 밀려나는 이유가 이 기울기다")}
<p><b>여유는 전류로 산다.</b> 전압 여유를 k만큼 만들려면 λ<sub>d</sub>를 ΔV/ω<sub>e</sub>만큼 더 깎아야 한다. 즉 Δi<sub>d</sub> ≈ kV<sub>max</sub>/(ω<sub>e</sub>L<sub>d</sub>)다. 5 %면 20 V / (6702 × 0.85 mH) ≈ 3.5 A 첨두 ≈ 2.5 A rms이고, 시뮬레이션 관측값은 +2.9 A rms(138.4 → 141.3)다. 이때 진각은 0.04°만 바뀐다. −d축 전류를 더 넣는 것은 γ를 거의 그대로 두고 전류 크기만 키우는 일이기 때문이다.</p>
{B_REGION}

<h2 id="ctrl">5. 전류 제어기 — PI, 디커플링, 안티와인드업, 벡터 제한</h2>
<div class="eq">e = i* − î &nbsp; (제어기 좌표 θ̂ = θ + θ<sub>err</sub>)
<br>v<sub>u</sub> = K<sub>p</sub> e + x + v<sub>ff</sub>, &nbsp;&nbsp; v<sub>ff</sub> = [ −ω<sub>e</sub> L<sub>q</sub> î<sub>q</sub> , &nbsp; ω<sub>e</sub>(L<sub>d</sub> î<sub>d</sub> + λ<sub>m</sub>) ]
<br>v<sub>s</sub> = v<sub>u</sub> · min(1, V<sub>max</sub>/|v<sub>u</sub>|) &nbsp;&nbsp;(크기만 자르고 방향은 유지)
<br>x ← x + T<sub>s</sub> [ K<sub>i</sub> e + K<sub>aw</sub> (v<sub>s</sub> − v<sub>u</sub>) ] &nbsp;&nbsp;(역계산 안티와인드업)</div>
<ul>
<li><b>이득.</b> K<sub>p,d</sub> = 8.5 Ω, K<sub>p,q</sub> = 16 Ω(MCB <code>mcb.getPIControllerParameters</code>, Modulus Optimum, T<sub>s</sub> = 50 µs). K<sub>i</sub> = K<sub>p</sub>R/L로 잡으면 PI 영점이 RL 극을 상쇄한다. 그러면 각 축 개루프가 K<sub>p</sub>/(Ls)가 되어 폐루프는 대역 ω<sub>c</sub> = K<sub>p</sub>/L인 1차계다. 두 축 모두 8.5/0.85 mH = 16/1.6 mH = 10<sup>4</sup> rad/s(1.59 kHz)다. K<sub>aw</sub> = R/L<sub>d</sub>다.</li>
<li><b>명목 인덕턴스.</b> 디커플링과 이득에는 상수 L<sub>d</sub> = 0.85 mH, L<sub>q</sub> = 1.6 mH를 쓴다. 플랜트는 전체 맵이므로 디커플링은 완전하지 않고, 남는 차이는 적분기가 흡수한다.</li>
<li><b>포화될 때 일어나는 일.</b> |v<sub>u</sub>| &gt; V<sub>max</sub>이면 조절기는 원하는 벡터를 만들 수 없다. 전류는 “전압이 맞는 곳”으로 흘러간다. 16 krpm에서 그곳은 γ가 더 큰 쪽이다(그림 3b). 이 한 가지 기구로 세 현상이 설명된다: MCB 표의 5 N·m 실패, 데드타임의 큰 토크 손실, 여유를 두면 둘 다 사라지는 것. 클램프와 안티와인드업이 평균 오차를 만드는 방식은 <a href="#clamp">14.1절</a>에 자세히 적었다.</li>
<li><b>빠진 것.</b> 속도 루프가 없다(속도 고정). 전압 크기 피드백 약자속 루프(K<sub>fw</sub>)는 코드에 있지만 꺼져 있다. 즉 기준표만으로 약자속을 한다. 상용 제어기는 전압 피드백 약자속을 흔히 쓰고, 그 루프 대역이 도달 가능한 각을 제한할 수 있다. 이 효과는 이 모델에 없다.</li>
</ul>
{code(C_CTRL, "구현 — sim_e10_stage2.m 87–97행")}
{B_CTRL}

<h2 id="delay">6. 이산 시간과 연산 지연 — 샘플 사이 회전을 무시할 수 없다</h2>
<ul>
<li><b>샘플 시점.</b> 캐리어 골과 꼭짓점에서 전류를 읽는다. 대칭 PWM에서는 전류 리플이 바로 그 순간 평균값을 지나므로, 필터 없이 평균 전류를 얻는다.</li>
<li><b>지연의 기하.</b> 샘플 k에서 계산한 전압은 n반주기 뒤부터 한 반주기 동안 <b>정지 좌표계에 고정된 벡터</b>로 걸린다. 인버터는 한 PWM 구간 동안 평균 전압 벡터 하나만 만들 수 있기 때문이다. 그동안 회전자는 계속 돈다. 그래서 회전자 좌표계에서 본 전압 벡터는 ω<sub>e</sub>(t − t<sub>k</sub>)만큼 뒤처진다. n = 1이면 인가 구간 동안 −{wTs}° ~ −{2*wTs:.1f}°, 평균 −{1.5*wTs:.1f}°다.</li>
<li><b>보상.</b> 지령을 ω<sub>e</sub>(n+½)T<sub>s</sub>만큼 미리 돌려 둔다(Bae·Sul 2003). 평균 오차는 0이 되고 ±{wTs/2:.1f}° 리플만 남는다.</li>
</ul>
{img("study_delay.png", "그림 4. (a) 1샘플 지연의 회전자 좌표계 각 오차와 보상. (b) 모형별 평균 각 오차. 단계 1은 전압을 회전 좌표계에서 지연시켜 물리적 회전이 없었는데도 보상각을 더했으므로, 보상각(+29°, 2샘플이면 +48°)이 그대로 오차가 됐다 — ‘2샘플 붕괴’의 정체")}
<div class="note"><b>단계 1 인공물 요약.</b> dq 좌표계에서 지연을 걸면 전압 벡터가 회전자와 함께 돌아 “회전에 의한 각 오차”가 생기지 않는다. 그 모형에 실제 드라이브용 보상(ω<sub>e</sub>(n+½)T<sub>s</sub>)을 걸면 보상이 오히려 오차가 된다. 단계 2(정지 좌표계 유지)에서는 보상된 지연 0–2샘플의 토크 차이가 1 % 이하다. 반대로 보상을 끄면 1샘플만으로 20 N·m가 역토크로 붕괴한다(결과 페이지 4.3절).</div>
{B_TIME}

<h2 id="pwm">7. 변조 — 중앙정렬 PWM과 min-max SVPWM</h2>
<div class="eq">v<sub>zs</sub> = −[max(v<sub>a</sub>*, v<sub>b</sub>*, v<sub>c</sub>*) + min(v<sub>a</sub>*, v<sub>b</sub>*, v<sub>c</sub>*)]/2, &nbsp;&nbsp; d<sub>x</sub> = ½ + (v<sub>x</sub>* + v<sub>zs</sub>)/V<sub>dc</sub>
<br>선형 범위: |v| ≤ V<sub>dc</sub>/√3 = 415.7 V (육각형 내접원) &nbsp;— 정현파 PWM V<sub>dc</sub>/2 = 360 V보다 15.5 % 넓다</div>
<ul>
<li><b>min-max 영상분 주입</b>은 영벡터 000/111을 반씩 나누는 고전 SVPWM과 같다. 상 지령에 공통 영상분을 더해도 선간 전압은 그대로이고, 최대·최소 상을 가운데로 모아 선형 범위를 넓힌다. 진폭 403 V 정현 지령이 ±360 V 안에 들어간다(그림 5b의 최대 349 V).</li>
<li><b>중앙정렬 비교.</b> 상승 반주기에는 캐리어가 1 − d를 넘는 순간 상단이 켜지고, 하강 반주기에는 다시 내려오는 순간 꺼진다. 펄스는 꼭짓점을 중심으로 d·T<sub>pwm</sub> 폭이다. <b>양 끝 갱신</b>이라 골과 꼭짓점마다 새 듀티가 들어간다(T<sub>s</sub> = T<sub>pwm</sub>/2 = 50 µs).</li>
<li><b>과변조 없음.</b> 제어기 한계 403.2 V가 415.7 V보다 작으므로 변조기는 항상 선형 범위다. 듀티 클립은 데드타임 보상을 더할 때만 생길 수 있다. 실제 드라이브는 16 krpm에서 과변조·6-스텝으로 전압을 더 끌어 쓰기도 한다. 이 연구의 결론은 선형 변조를 전제로 한다.</li>
<li><b>중성점 부동.</b> 폴 전압 V<sub>dc</sub>(s<sub>x</sub> − ½)에서 세 상 평균을 빼면 상전압이 된다(Y 결선, 중성점 비접지).</li>
</ul>
{img("study_svpwm.png", "그림 5. (a) 8개 스위칭 상태가 만드는 육각형과 세 한계(선형 415.7 V, 제어기 403.2 V, 정현파 PWM 360 V). (b) min-max 영상분을 더한 변조 지령 — 403 V 정현 지령의 최대가 349 V로 내려와 듀티 0–1 안에 든다")}
{code(C_MOD, "구현 — sim_e10_stage2.m 99–112행 (SVPWM과 데드타임 보상)")}

<h2 id="dead">8. 데드타임 — 캐리어 주기마다 한 번 밀리는 에지</h2>
{img("study_pwm_timing.png", "그림 6. 중앙정렬 캐리어, 양 끝 갱신, 게이트 지령과 실제 폴 전압. i<sub>a</sub> &gt; 0이면 켜짐 에지만(주황, 잃는 볼트·초), i<sub>a</sub> &lt; 0이면 꺼짐 에지만(청록, 얻는 볼트·초) t<sub>d</sub>만큼 늦다 — 한 캐리어 주기에 한 번씩")}
<ul>
<li><b>물리.</b> 암 단락을 막기 위해 두 스위치를 t<sub>d</sub> 동안 모두 끈다. 그동안 어느 다이오드가 도통할지는 전류 방향이 정한다. i &gt; 0에서 상단을 켜라는 지령이 나오면, 상단이 실제로 켜질 때까지 하단 다이오드가 도통해 폴이 낮게 남는다 → V<sub>dc</sub>t<sub>d</sub>를 잃는다. i &gt; 0에서 상단을 끄면 하단 다이오드가 즉시 도통하므로 오차가 없다. i &lt; 0이면 방향이 반대다.</li>
<li><b>크기.</b> 밀리는 에지가 캐리어 주기마다 하나이므로 상 평균 오차는 다음과 같다.
<div class="eq">ΔV̄<sub>x</sub> = −sign(i<sub>x</sub>) · V<sub>dc</sub> t<sub>d</sub> / T<sub>pwm</sub> = −sign(i<sub>x</sub>) · 21.6 V &nbsp;(t<sub>d</sub> = 3 µs, 10 kHz, 720 V)
<br>기본파: (4/π) · 21.6 = 27.5 V, 전류 벡터 반대 방향 (+ 5·7차 → dq에서 6차 리플)</div>
V<sub>dc</sub>t<sub>d</sub>/T<sub>s</sub>로 세면 에지를 두 번 센 것이다. 초판 모델의 보상식이 이 실수로 2배였다.</li>
<li><b>왜 토크가 크게 줄어드나.</b> 27.5 V는 한계의 약 7 %뿐이다. 그런데 여유 없는 표에서는 조절기가 이미 포화돼 있어 잃은 전압을 채우지 못한다. 운전점이 전압이 덜 드는 쪽(γ가 큰 쪽, 그림 3b)으로 0.67° 밀리고, dT/dγ ≈ −12 N·m/°라 20 N·m에서 −8 N·m(−43 %)가 된다.</li>
<li><b>보상.</b> 에지가 밀리는 반주기에서만 듀티를 t<sub>d</sub>/T<sub>s</sub> 보정한다: 상승 반주기에서 i &gt; 0이면 +, 하강 반주기에서 i &lt; 0이면 −. 한계가 두 가지다. ① 부호는 샘플 전류로 정하므로 영교차 부근(샘플당 전기각 19°)에서 틀릴 수 있다. ② 보상 전압을 낼 여유가 있어야 한다. 그래서 여유 없는 표에서는 3 µs 보상 후에도 20 N·m −16 %가 남고, 5 % 여유 표에서는 −2 %가 된다.</li>
<li><b>Simscape와의 차이.</b> Simscape(2c)는 게이트를 실제로 둘 다 끄고 다이오드가 도통을 정한다. 블랭킹 중 전류가 0을 지나는 경우까지 물리대로 계산된다. 스크립트의 “에지 시점 부호” 규칙과 비교하면 토크 차이는 0.15–1.8 %였다.</li>
</ul>

<h2 id="event">9. 사건 구동 적분 — 에지 시각을 정확히</h2>
<p>반주기마다 다음을 반복한다.</p>
<ol>
<li>반주기 시작에 전류 샘플 → 제어기 → 대기열 → SVPWM 듀티.</li>
<li>각 상의 지령 에지 목록을 만든다: 반주기 시작 상태 + 에지 한 개. 상승이면 t<sub>k</sub> + (1−d)T<sub>s</sub>, 하강이면 t<sub>k</sub> + dT<sub>s</sub>.</li>
<li>다음 사건 = min(다음 지령 에지, 데드타임으로 밀린 에지, 반주기 끝)까지 현재 폴 상태로 적분한다. 폴 상태가 고정된 구간이므로 αβ 전압은 상수다. 회전자 좌표계에서는 R(−ω<sub>e</sub>t)로 돌려 RK4로 적분한다(부분 스텝 ≤ h<sub>max</sub> = 2 µs).</li>
<li>사건 처리: 지령 에지가 데드타임 규칙에 걸리면 t + t<sub>d</sub>로 미뤄 대기시킨다. 대기 중에 새 지령이 오면 목표만 바꾸거나 취소한다.</li>
<li>반주기 평균 토크(사다리꼴 적분), 반주기 끝 전류, 진단용 “인가 전압 − 지령” 볼트·초를 기록한다.</li>
</ol>
<p><b>왜 고정 스텝이 아닌가.</b> 에지는 임의 시각에 온다. 고정 스텝(예: 1 µs)은 에지를 격자로 반올림해 반주기 50 µs에 최대 2 %의 볼트·초 오차를 만든다. 이는 데드타임 효과(3 µs = 6 %)와 같은 크기다. 사건 구동이면 에지가 정확하다. 검증: t<sub>d</sub> = 0에서 반주기 평균 인가 전압과 지령의 차는 약 10<sup>−10</sup> V다. 0.08 s 모의가 약 2 s에 끝난다.</p>
{code(C_EVENT, "구현 — sim_e10_stage2.m 사건 루프와 integrate() (발췌)")}
{B_EVENT}

<h2 id="lut">10. 기준표 — MCB와 MBC 교정</h2>
<ul>
<li><b>MCB</b> <code>mcb.generateMotorLUT(pmsm, inverter, 'idiqLUTs')</code>: <code>PMSMLUT.method = 'FluxDQ'</code>로 우리 λ<sub>d</sub>, λ<sub>q</sub>, 토크 표를 그대로 넣고, 약자속은 'vclmt'(전압 제약)로 푼다. 출력은 i<sub>d</sub>*(T, n), i<sub>q</sub>*(T, n) 격자이고, 16 krpm 열을 쓴다. Lab 자체 궤적과 진각 0.4° 안에서 일치한다. 대신 점을 전압 한계선 <b>위에</b> 놓는다. 우리 플랜트 기준 한계의 99.6–101.8 %, Lab 기준으로는 0–3 % 초과다.</li>
<li><b>MBC</b> <code>calibratepmsm(mbcData, IsMax, VsMax, 'TableType', 'SpeedTorque', 'Breakpoints', {{[], Tbp}})</code>: 교정 데이터(n, Id, Iq, Is, Vs, Trq, Flux, FluxMax)로 대리 모델을 맞춘다. 그다음 각 격자점에서 TPA 최적(T = T*, |I| ≤ IsMax, V<sub>s</sub> ≤ VsMax 조건에서 |I| 최소)을 푼다. 교정 데이터는 Lab 맵을 2배 촘촘하게 보간해(6.5 A) 2/4/8/16 krpm에서 V<sub>s</sub> = |R i + jω<sub>e</sub>λ|로 만들었다. 16 krpm 해는 VsMax에 정확히 붙으므로 VsMax 95 %가 곧 5 % 여유다.</li>
<li><b>함정 셋.</b> ① 플랜트 맵이 M(i<sub>q</sub>, i<sub>d</sub>)로 전치 저장돼 있다(51×51 정사각이라 틀려도 오류가 안 난다). ② 13 A 격자는 16 krpm 전압 한계 근처에서 한 칸에 70 V 이상 변해 보간이 필요했다. ③ 16 krpm 약 20 N·m 아래는 최적화가 수렴하지 않는다(ExitFlag ≤ 0). 이때 표가 한계 2–4배 전압의 점으로 채워지므로, 수렴한 해만 쓰고 외삽했다.</li>
<li>그림 2(b)에서 세 표를 비교할 수 있다. 여유 5/10 %는 같은 토크에서 −d축 쪽으로 약 4/8 A(첨두) 옮긴 궤적이다.</li>
</ul>
{B_LUT}

<h2 id="simscape">11. Simscape 모델 (단계 2c) — 회로로 다시 풀기</h2>
<ul>
<li><b>출발점.</b> MathWorks <i>HEV PMSM Drive Test Harness</i>. 원래는 이상 정현 자속 전동기, id* = 0 제어, 2 kHz SPWM이라 16 krpm e10을 돌릴 수 없다. <code>build_e10_stage2c.m</code>이 복사본의 블록을 코드로 바꾼다.</li>
<li><b>전동기.</b> FEM-Parameterized PMSM을 <code>fem_motor_dq0</code> 변형(ψ<sub>d</sub>, ψ<sub>q</sub>(i<sub>d</sub>, i<sub>q</sub>, θ), DQcartesian)으로 바꿨다. 이 블록은 회전자각을 포함한 3-D 표를 요구한다. 그래서 <b>같은 2-D Lab 맵을 회전자각 7점(기계각 0–90°, 15° 간격 = 전기 한 주기)에 그대로 복제</b>했다. 저장된 모델에서 각도 방향 차이가 0임을 확인했다. 따라서 이 모델도 스크립트처럼 슬롯 고조파·코깅·역기전력 고조파가 없는 정현 분포 기계이고, 포화·교차포화만 반영한다(3절 한계). 토크는 Lab 축 토크 표를 쓴다. 블록이 대칭 i<sub>d</sub> 격자(0 포함)를 요구해 +650 A까지 연장했다(운전점은 닿지 않음). 변형 선택은 <code>SourceFile</code>로 해야 저장 후에도 유지된다. <code>ComponentPath</code>로 바꾸면 재로드 때 원래 3-D 변형으로 되돌아간다.</li>
<li><b>인버터.</b> Ideal Semiconductor Switch 6개(R<sub>on</sub> 10 µΩ) + 역병렬 다이오드 6개(V<sub>f</sub> 0.1 mV)라 도통 강하는 ≈ 0이다. 직류 720 V 전원은 1 mΩ 저항을 거쳐 1 mF 커패시터에 연결된다. <b>데드타임은 실제 상보 게이트 블랭킹</b>이다: 켜짐 에지를 t<sub>d</sub> 늦추고, 블랭킹 중 도통은 다이오드가 정한다.</li>
<li><b>제어·변조.</b> 스크립트와 같은 50 µs 제어기(MATLAB Function 'ctrl'). 변조기('modg')는 에지 시각을 계산하고, 연속 비교기와 영교차 검출이 그 시각에 게이트를 바꾼다. 게이트 켜짐 시간과 듀티의 차는 10<sup>−10</sup> µs 이하다.</li>
<li><b>기계·솔버.</b> 이상 각속도원으로 1675.5 rad/s(16 krpm)을 주고 이상 토크 센서로 축 토크를 잰다. 솔버는 가변 스텝 ode23t(MaxStep 5 µs, RelTol 10<sup>−4</sup>)이고, 경우당 11–22 s 걸린다.</li>
<li><b>열어 볼 곳.</b> 모델 작업공간 변수 <code>Tref_Nm</code>, <code>td_s</code>, <code>Tstop</code>, <code>Ts_c</code>; MATLAB Function 'ctrl'·'modg' 코드; 전동기 블록 파라미터.</li>
<li><b>단계 2d — 모델은 그대로, 표만 교체.</b> <code>run_e10_stage2d.m</code>은 모델 작업공간 변수 <code>E10</code>(전동기 표)과 <code>P</code>(제어기·기준표)를 <code>Simulink.SimulationInput.setVariable(…, 'Workspace', mdl)</code>로 실행마다 바꾼다. 모델 파일은 건드리지 않는다. 표 변형은 A(Lab 복제) → B(손실 규약 축 토크 + R<sub>ac,eff</sub>) → C(운전 대역을 직접 FEA 위치 평균으로) → D(위치별)다. 블록의 표 조건은 i<sub>d</sub>·i<sub>q</sub> 격자가 모두 0을 포함한 ± 대칭이고 회전자각이 4점 이상이어야 한다는 것이다. 그래서 평균 표(B·C)도 같은 값을 5개 각도에 복제했고, D는 전기 한 주기 121점이다. 제어기에는 <code>P.ffRef</code>(1이면 디커플링을 측정 전류 대신 기준 전류로) 선택지를 넣었다(<code>patch_stage2c_ctrl.m</code>, 14절).</li>
</ul>
{B_SIM}

<h2 id="fmu">12. Motor-CAD Lab FMU (단계 3) — 준정적 손실 계산기</h2>
<ul>
<li><b>무엇인가.</b> Ansys Motor-CAD Lab BPM FMU(FMI 2.0 co-simulation)다. 한 스텝마다 .lab 모델로 정상상태 운전점을 푼다. 포화·손실 맵, 교류 동손 하이브리드 맵, 철손, 기계손, 온도 입력이 들어 있다. 파라미터는 <code>ModelFilePath</code>(.lab)와 <code>OperatingPointDefinition</code>이다: 0 = 토크·속도(Lab이 최적 운전점을 고름), 1 = 최대 전류·속도, 2 = 전류·진각·속도 강제.</li>
<li><b>주의.</b> 모드 2는 전압 한계를 강제하지 않는다. 그래서 상전압 ≤ 285.12 V rms인지 따로 검사했다. 호출당 약 1 s(인스턴스 생성 + 1스텝)이고, 프로세스 6개로 병렬 실행했다.</li>
<li><b>쓰임.</b> ① 토크 고정 진각 스윕: 진각을 강제하고 전류를 이분법으로 풀었다(결과 페이지 그림 6). ② 스위칭 모델이 실제 도달한 (I, γ)를 모드 2로 되짚고, 같은 토크의 모드 0 최적과 비교했다(그림 7).</li>
<li><b>알려진 차이.</b> 같은 운전점에서 Lab 상전압이 플랜트의 |R i + jω<sub>e</sub>λ|보다 0.5–3 % 높다. Lab이 단자 전압에 넣는 항 차이로 보이며, 여유가 더 필요하다는 방향이다.</li>
<li><b>.lab 내보내기.</b> pymotorcad로 <b>새 숨은 Motor-CAD 인스턴스</b>를 띄워 <code>export_lab_model</code>을 부른다. 사용자가 열어 둔 창은 쓰지 않는다.</li>
</ul>
{B_FMU}

<h2 id="posmap">13. 직접 FEA 위치별 맵 — 슬롯 고조파를 표에 넣는 법</h2>
<ul>
<li><b>어디서 나오나.</b> Motor-CAD E-Magnetic의 Saturation Map export를 FEA로, 회전자 위치별로 돌린다(<code>fea_posmap.py</code>). 설정은 <code>SaturationMap_CalculationMethod = 1</code>(FEA), <code>SaturationMap_ResultType = 1</code>(회전자 위치에 따라 변함), <code>SaturationMap_FEACalculationType = 1</code>(전기 한 주기 전체), <code>SaturationMap_InputDefinition = 1</code>(D/Q 전류)이고, 위치는 전기 한 주기 120점이다. Hybrid 교류 동손, 자석 80 °C, 전체 모델(대칭 미사용), 16 krpm 손실맵을 같이 계산해 점당 36 s가 걸린다. 16 krpm 운전 대역 i<sub>d</sub> −364…0(13 A 간격 29점) × i<sub>q</sub> −13…52 A 첨두(6점) = 174점을 i<sub>q</sub> 한 값씩 6조각으로 나눠 약 1시간 45분에 풀었다.</li>
<li><b>함정 둘.</b> ① 이 export는 <b>i<sub>d</sub> 격자에 0이 반드시 있어야</b> 한다("requires a point at Id = 0"). 그래서 조각은 i<sub>d</sub>가 아니라 i<sub>q</sub>로 나눈다. ② 사용자가 열어 둔 Motor-CAD 창은 쓰지 않는다. <code>mc_launch.py</code>가 숨은 새 인스턴스를 띄우고 PID를 기록하며, 계산은 모델 사본(<code>work_lab_pc1\\fea_pos\\e10_fea_pos.mot</code>)에서 한다.</li>
<li><b>출력과 정렬.</b> 결과는 <code>Angular_Flux_Linkage_D/Q</code>, <code>Angular_Electromagnetic_Torque</code>, 상 자속 파형 같은 <code>Angular_*</code> 배열(전류점 × 위치)이다. 위치 x(Motor-CAD 회전자 위치, 전기각)와 d축 각의 관계는 무부하 상 자속의 기본파 위상으로 구했고 θ<sub>d</sub> = x + 60°다. 상 자속을 이 각으로 Park 변환하면 Motor-CAD의 dq 자속과 d축 0.42 mWb, q축 0.03 mWb 안에서 같다(평균 ψ<sub>d</sub>의 1 % 미만, <code>fea_posmap_analyze.py</code>).</li>
<li><b>검증 결과.</b> 위치 평균은 Lab 48점 보간과 자속 0.9 %, 토크 0.8 %, dT/dγ 0.06 N·m/°, 필요 전압 0.7 % 안에서 같다(결과 페이지 4.9.1절). 위치별 성분은 dq 6·12차다. 20 N·m점에서 ψ<sub>q</sub> 12차 10.4 mWb(평균의 62 %), 토크 리플 50 N·m p-p다.</li>
<li><b>Simscape 표로.</b> 대역 밖은 Lab 표를 그대로 두고, 대역 안만 FEA 값으로 바꿔 <code>drive\\stage2d_tables.mat</code>(69 × 29 × 5 또는 121)을 만든다. i<sub>q</sub> 격자는 0을 포함한 ± 대칭이 되도록 음수 쪽을 Lab 대칭 확장으로 채운다.</li>
<li><b>스큐.</b> 기준 모델은 스큐 없이 계산된 것으로 보인다(<code>SkewType = 0</code>). 3단 스텝 스큐(±11.25° 전기각)를 켜면 12차가 약 0.14배로 준다. 실제 기계의 스큐 여부가 14절 결론의 크기를 좌우한다.</li>
</ul>
{B_POS}

<h2 id="harm">14. 고조파와 전류 제어기 — 클램프와 안티와인드업이 만드는 평균 오차</h2>
<p>위치별 맵을 넣으면(단계 2d의 D) 같은 전류에서의 평균 토크는 그대로다. 그런데 5 % 여유 표의 20 N·m가 −60 %로 무너진다. 원인은 전동기가 아니라 제어기 쪽에 있다.</p>
<ol>
<li><b>고조파 전류.</b> 인버터는 기본파 전압만 낸다. 고조파 자속 Δψ는 전압원 아래에서 고조파 전류 Δi ≈ Δψ/L을 만든다. 12차 ψ<sub>q</sub> 10 mWb / L<sub>q</sub> 1.6 mH ≈ 6 A다.</li>
<li><b>샘플링과 접힘.</b> 20 kHz 샘플링(나이퀴스트 10 kHz)에서 6차 6.4 kHz는 그대로, 12차 12.8 kHz는 7.2 kHz로 접혀 보인다. 둘 다 전류 루프 대역(1.6 kHz)보다 높아 적분기는 반응하지 않는다.</li>
<li><b>비례 경로와 디커플링.</b> 그러나 비례 이득(K<sub>p,d</sub> 8.5 Ω, K<sub>p,q</sub> 16 Ω)과 측정 전류 디커플링(ω<sub>e</sub>L<sub>q</sub> 10.7 Ω, ω<sub>e</sub>L<sub>d</sub> 5.7 Ω)은 그대로 통과시킨다. 6 A면 명령 전압에 약 100 V의 고조파가 실린다.</li>
<li><b>클램프.</b> 기본파 명령이 한계에 가까우면 명령 크기가 403.2 V 원 클램프를 주기적으로 넘고 그 순간 잘린다(5 % 여유 표에서 샘플의 약 60 %).</li>
<li><b>안티와인드업이 잘린 몫을 평균 오차로 바꾼다.</b> 역산(back-calculation) 안티와인드업은 적분기에 K<sub>aw</sub>(v<sub>clamp</sub> − v<sub>cmd</sub>)를 더한다. 정상상태에서 적분기 입력의 평균은 0이어야 한다.</li>
</ol>
<div class="eq">K<sub>i</sub>·mean(e) + K<sub>aw</sub>·mean(v<sub>clamp</sub> − v<sub>cmd</sub>) = 0 &nbsp;⇒&nbsp; mean(e) = (K<sub>aw</sub>/K<sub>i</sub>)·mean(v<sub>cmd</sub> − v<sub>clamp</sub>)
<br>이 제어기: K<sub>i,d</sub> = K<sub>p,d</sub>R/L<sub>d</sub>, K<sub>i,q</sub> = K<sub>p,q</sub>R/L<sub>q</sub>, K<sub>aw</sub> = R/L<sub>d</sub> ⇒ 두 축 모두 mean(e) = mean(잘린 전압)/8.5 Ω</div>
<p>평균 20 V가 잘리면 전류 평균이 약 2.4 A 틀어진다. 20 N·m의 i<sub>q</sub>* 6.8 A에는 1/3이다. 틀어지는 방향은 전압이 덜 드는 쪽(γ 증가)이고, 이것이 운전점을 옮긴다. 16 krpm에서 dT/dγ ≈ −11 N·m/°라 진각 1°가 −11 N·m다.</p>
<ul>
<li><b>여유는 고정량으로 환산되지 않는다.</b> 잘리는 시간은 기본파 명령과 한계 사이의 틈이 정하고, 틈이 넓어질수록 급격히 준다. 그래서 D가 도달한 점에 남은 평균 여유는 표의 여유와 함께 커진다(20 N·m에서 MCB 5.0 %, MBC 95 8.1 %, MBC 90 11.7 %). 이 값을 정상상태 계산기에 고정 여유로 넣으면 다른 표의 결과를 예측하지 못한다(결과 페이지 4.9.4절).</li>
<li><b>대책과 시험 결과</b>(Simscape 단계 2e, 결과 페이지 4.9.8절).
<ul>
<li>① 표의 여유를 늘린다: 20 N·m에 25 %가 필요하고 손실이 +15 %다.</li>
<li>② 디커플링을 기준 전류로 계산한다(<code>P.ffRef = 1</code>): 피해가 약 1/3 준다.</li>
<li>③ 피드백에서 6차와 접힌 12차를 노치로 뺀다: <b>문제가 사라진다.</b> 여유 5 %에서 오차가 −1…−3 %로 고조파 없는 맵과 같고, 클램프에 걸린 샘플이 0 %이며 비용도 없다. 같은 ③이라도 공진(PR) 제어기로 억누르면 더 나빠진다(−54 → −65 %). 필요한 고조파 전압이 수백 V이기 때문이다.</li>
<li>④ 과변조(육각형 한계): 일부만 돕는다(−54 → −40 %).</li>
<li>⑤ 전압 피드백 약자속: 토크는 ±2 % 안으로 맞추지만, i<sub>d</sub>를 20–38 A 더 깊게 넣어 손실이 18–31 % 는다.</li>
</ul></li>
</ul>
{img("stage2d_margin.png", "그림 7. 기준표 전압 여유별 토크 오차(Simscape 단계 2d, 16 krpm). C는 평균 맵, D는 위치별 맵, D<sub>ff</sub>는 기준 전류 디커플링")}
<h3 id="clamp">14.1 조절기 클램프 자세히</h3>
<p><b>무엇을 하나.</b> 전류 PI가 만든 dq 전압 명령 v<sub>u</sub> = K<sub>p</sub>e + x + v<sub>ff</sub>를 변조기에 넘기기 전에 크기만 자른다: v<sub>s</sub> = v<sub>u</sub>·min(1, V<sub>max</sub>/|v<sub>u</sub>|). 방향은 그대로다. V<sub>max</sub> = 403.2 V 첨두는 선형 SVPWM 한계 V<sub>dc</sub>/√3 = 415.7 V의 0.97배(Lab의 변조율 0.97과 같음)다. 인버터가 실제로 낼 수 있는 범위는 육각형(꼭짓점 2V<sub>dc</sub>/3 = 480 V, 6-스텝 기본파 (2/π)V<sub>dc</sub> = 458 V)이지만, 원 안(선형 영역)만 쓰면 기본파가 명령과 같고 저차 전압 고조파가 생기지 않는다.</p>
<p><b>왜 두나.</b> ① 변조기가 선형 영역을 벗어나지 않게 한다(과변조의 5·7차 전압 방지). ② 포화를 명시적으로 만들어 안티와인드업이 알 수 있게 한다. ③ 남긴 3 %는 데드타임·샘플 사이 회전 같은 오차 몫이다.</p>
<p><b>자르는 모양.</b> 원형 비례 축소(이 모델)는 방향을 지키므로 잘린 몫이 명령 방향으로 나뉜다. 축 우선 방식은 한 축을 먼저 보장하고 나머지를 잘라, 어느 축 전류가 오차를 떠안을지를 정한다. 육각형 투영(과변조)은 원 밖 육각형까지 써서 전압을 더 내지만 저차 전압 고조파를 만든다.</p>
<p><b>안티와인드업과 짝이다.</b> 잘린 동안에도 적분기가 오차를 계속 적분하면(와인드업) 포화가 풀릴 때 크게 넘친다. 이 모델은 역산식 x ← x + T<sub>s</sub>[K<sub>i</sub>e + K<sub>aw</sub>(v<sub>s</sub> − v<sub>u</sub>)]을 쓴다(K<sub>aw</sub> = R/L<sub>d</sub>). 다른 대표 방식은 포화 중 적분을 멈추는 조건부 적분이다. 역산식의 정상상태 성질이 이 절의 핵심이다. 적분기 입력의 평균이 0이어야 하므로 mean(e) = (K<sub>aw</sub>/K<sub>i</sub>)·mean(v<sub>u</sub> − v<sub>s</sub>) = δ/8.5 Ω이다. 평균적으로 잘린 전압 δ가 곧 평균 전류 오차가 된다. 고조파가 없으면 평균 명령이 한계 안일 때 δ = 0이라 오차도 0이다. 평균 명령이 한계 위면(여유 0 표 + 데드타임) 매 샘플이 잘려 δ가 크다(MCB 표의 실패).</p>
{img("clamp_anatomy.png", "그림 8. 조절기 클램프 해부(16 krpm, 20 N·m, 위치별 맵, 기본 제어기, 조화균형 계산): (a) 전압 평면의 명령 샘플과 잘리는 몫, (b) 전기 한 주기 동안의 명령 크기, (c) 틈과 평균 잘린 전압")}
<p><b>고조파가 들어가면 클램프는 정류기가 된다.</b> 여유 5 % 표의 20 N·m에서 평균 명령은 395 V로 한계보다 8 V 안쪽이다. 평균만 보는 정상상태 전압 검사로는 여유가 있다. 그런데 슬롯 고조파 전류(7–11 A)가 비례 이득과 디커플링을 지나 명령에 반경 방향 ±110–120 V 리플을 싣고, 샘플의 52 %가 한계를 넘는다(그림 8a). 잘리는 것은 항상 바깥쪽 봉우리뿐이다(그림 8b). 그래서 반파 정류처럼 교류 리플에서 직류 δ = (−4.7, +25.6) V가 생긴다. 역산 안티와인드업이 이 직류를 적분기에 넣어 평균 전류 오차 (−0.56, +3.0) A가 남는다. 16 krpm 약자속에서 명령은 거의 q축(v<sub>q</sub> 384 V, v<sub>d</sub> −93 V)이라 δ도 q축이고, i<sub>q</sub>가 6.8 A에서 3.8 A로 준다. 토크는 i<sub>q</sub>에 거의 비례하므로 20 N·m가 10 N·m가 된다. 전류 크기(대부분 i<sub>d</sub>)는 거의 그대로라 손실은 줄지 않는다.</p>
<p><b>틈과 리플.</b> δ는 틈 g = V<sub>max</sub> − |V̄|와 리플 진폭 A의 비로 정해진다. 단일 정현 근사로 δ = (A/π)(sin φ<sub>0</sub> − (g/A)φ<sub>0</sub>), φ<sub>0</sub> = arccos(g/A)이고, g ≥ A이면 0이다. 이 운전점의 A는 약 109 V(V<sub>max</sub>의 27 %)라 여유 25–30 %에서야 잘림이 사라진다(그림 8c; Simscape는 25 %에서 −3 %, 30 %에서 −0.4 %). 이 곡선이 비선형이라 고정 여유로는 환산되지 않는다(Q9).</p>
<p><b>설계 손잡이와 시험 결과</b>(결과 페이지 4.9.8절).</p>
<ol>
<li><b>틈을 키운다.</b> 표 여유를 늘리고 손실로 치른다. 20 N·m에 25 %가 필요하고 손실이 +15 %다.</li>
<li><b>리플을 줄인다.</b> 기준 전류 디커플링은 피해를 약 1/3 줄인다. <b>피드백에서 6차와 접힌 12차를 노치로 빼면 리플이 명령에 실리지 않는다. 잘림이 0 %가 되고, 여유 5 %로 고조파 없는 맵과 같은 정확도가 나온다.</b> 위치별 맵으로 예측한 Δi(θ)를 측정 전류에서 빼는 앞먹임도 같은 원리다(미시험). 고속에서는 고조파 전류를 억누르려 하면 안 된다. 6차 공진 제어기로 억누르자 오히려 나빠졌다(−54 → −65 %).</li>
<li><b>클램프 모양을 바꾼다.</b> 과변조(육각형)는 봉우리 일부만 내서 −54 → −40 %에 그쳤다. 축 우선순위는 시험하지 않았다.</li>
<li><b>안티와인드업 방식을 바꾼다.</b> 조건부 적분은 시험하지 않았다.</li>
<li><b>전압 피드백 약자속을 쓴다.</b> i<sub>d</sub>를 더 깊게 넣어 스스로 틈을 만든다. 토크는 맞추지만 손실이 18–31 % 는다.</li>
</ol>
<p>이 선택지들은 조화균형 계산기(15절)로 먼저 거를 수 있다. 계산기는 노치·과변조·약자속의 결과를 미리 맞혔다.</p>
{B_HARM}

<h3 id="remedy">14.2 대책을 제어기에 넣는 법</h3>
<p>14절의 사슬은 네 고리다. ① 고조파 전류가 흐른다. ② 조절기가 그것을 명령 리플로 바꾼다. ③ 클램프가 봉우리를 자른다. ④ 안티와인드업이 잘린 몫을 평균 전류 오차로 바꾼다. 대책은 어느 고리를 끊느냐로 나뉜다.</p>
<ul>
<li><b>노치</b>와 <b>기준 전류 디커플링</b>은 ② 고리를 끊는다. 조절기가 고조파 전류를 명령으로 옮기지 못하게 한다.</li>
<li><b>과변조</b>는 ③ 고리를 줄인다. 자르는 한계 자체를 넓힌다.</li>
<li><b>전압 피드백 약자속</b>은 평균 명령을 낮춰 ③의 틈을 키운다.</li>
<li><b>공진(PR)</b>은 ① 고리, 즉 고조파 전류 자체를 없애려 한다. 그러려면 그만큼의 고조파 전압을 내야 한다.</li>
</ul>
<p>이 시험의 제어기(<code>build_e10_stage2e.m</code>가 Simscape 모델 'ctrl' 블록에 넣는 코드)에서 대책 부분만 발췌했다.</p>
{code(C_REM, "구현 — e10_stage2e.slx 제어기 'ctrl' 발췌 (P.notch, P.pr6, P.hex, P.fw)")}
{code(C_NOTCH, "노치 계수 — run_e10_stage2e.m")}
<p><b>노치를 실제 드라이브에 옮기는 절차.</b></p>
<ol>
<li><b>고조파 차수와 크기를 확인한다.</b> 위치별 FEA 맵(13절)이나 역기전력 측정으로 dq 고조파를 본다. 이 기계는 6·12차가 크다. 슬롯·극 조합이 다른 기계는 차수가 다를 수 있다.</li>
<li><b>조절기가 보는 주파수를 계산한다.</b> dq 좌표의 고조파 주파수는 f<sub>h</sub> = h·f<sub>e</sub>다. 샘플 주파수 f<sub>s</sub>(여기서는 20 kHz)에서 조절기가 보는 주파수는 f<sub>h</sub>를 접은 |f<sub>h</sub> − f<sub>s</sub>·round(f<sub>h</sub>/f<sub>s</sub>)|다. 16 krpm에서 12차 12.8 kHz는 7.2 kHz로 보인다. 노치 각주파수는 w = 2π·(접힌 주파수)·T<sub>s</sub>이고, 속도가 바뀌므로 매 샘플 다시 계산한다.</li>
<li><b>켤 속도 범위를 정한다.</b> 접힌 주파수가 전류 루프 대역(1.6 kHz)보다 충분히 높을 때만 켠다. 저속에서는 고조파가 대역 가까이 내려와 노치가 기본파 제어를 흔든다. 여기서는 16 krpm만 시험해서 문턱값은 정하지 않았다.</li>
<li><b>위상 여유를 확인한다.</b> r = 0.9에서 두 노치가 1.6 kHz에 주는 위상 지연은 −4°다. r을 1에 가깝게 하면 노치가 좁아져 위상 손실이 줄지만, 계수가 실제 속도를 늦게 따라가면 고조파를 놓친다.</li>
<li><b>먼저 계산기로, 다음에 시간영역으로 확인한다.</b> 조화균형 계산기(<code>qs_harmonic_hb.py</code>, 15절)로 목표 속도·토크를 수 초에 거르고, 후보만 Simscape 2e(<code>run_e10_stage2e.m</code>)로 확인한다.</li>
</ol>
<p class="mut">노치는 토크 리플을 줄이지 않는다. 고조파 전류를 흐르게 두기 때문이다. 리플까지 줄이려면 고조파 전압이 필요하고, 그 전압이 남는 저·중속에서 PR이나 고조파 전류 주입을 쓴다.</p>
<p><b>나머지 대책을 쓸 때.</b></p>
<ul>
<li><b>기준 전류 디커플링</b>은 한 줄 변경(<code>P.ffRef = 1</code>)이다. 피해가 1/3만 준다.</li>
<li><b>PR</b>은 지연 보상 위상 φ = π/2 + 1.5w<sub>0</sub>를 틀리면 불안정하다(부호가 반대면 발산). 포화 중에는 입력을 끊어야 한다.</li>
<li><b>과변조</b>는 한계식만 바꾸면 되지만, 평균 명령이 원을 넘는 영역에서는 5·7차 전압이 생긴다.</li>
<li><b>전압 피드백 약자속</b>은 K<sub>fw</sub>로 반응 속도를, K<sub>leak</sub>로 복귀를 정한다. 루프 대역이 전류 루프보다 한참 낮아야 한다.</li>
</ul>
{B_REM}

<h2 id="qs">15. 정상상태 운전점 계산기(QS) — 시간영역 없이 전압 한계를 푼다</h2>
<p><b>QS는 quasi-static(준정적)의 약자</b>다. 전류가 과도를 거쳐 자리 잡는 과정을 풀지 않고, 운전점마다 정상상태 방정식(평균 전압식 + 토크식)만 푼다는 뜻이다. 그래서 경우당 수 ms–수백 ms로 끝난다(시간영역 모델은 수 초–수십 초). 이 계산기(<code>qs_opsolver.py</code>)로 만든 기준표를 <b>QS 표</b>라 부른다. 이름의 숫자는 필요 전압을 한계 403.2 V의 몇 %에 두었는지다. 예를 들어 <b>QS 95는 여유 5 %, QS 80은 여유 20 %</b>다. MBC 표의 VsMax 95 %와 같은 표기지만, QS 표는 FEA 평균 맵과 교류 저항을 넣은 같은 모델에서 전압을 정확히 그 값에 맞춘다.</p>
<div class="eq">T<sub>축</sub>(i<sub>d</sub>, i<sub>q</sub>) = T<sub>em</sub> − (P<sub>기계</sub> + P<sub>fe,회전자</sub> + P<sub>자석</sub> + P<sub>fe,고정자,NL</sub> + P<sub>ac,NL</sub>)/ω<sub>m</sub> = T*
<br>|v<sub>ss</sub> + Δv<sub>dt</sub>| ≤ V<sub>clamp</sub>(1 − m), &nbsp; v<sub>ss</sub> = (R<sub>dc</sub> + R<sub>ac</sub>(i)) i + jω<sub>e</sub>ψ(i), &nbsp; R<sub>ac</sub>(i) = (P<sub>ac</sub> − P<sub>ac,NL</sub>)/(1.5|i|²)
<br>Δv<sub>dt</sub> = (4/π) V<sub>dc</sub> t<sub>d</sub> f<sub>pwm</sub> · i/|i| &nbsp; (보상 없는 데드타임 사각파의 기본파: 명령이 이만큼 더 커야 한다)</div>
<ul>
<li><b>두 질문.</b> <code>best_point</code>는 토크 T*를 내는 최소 전류 가능점이다(유효 한계로 교정표를 만들면 고를 점). <code>held_point</code>는 한계를 넘는 기준점(i<sub>d</sub>*, i<sub>q</sub>*)이 주어졌을 때, 포화된 조절기가 같은 전류 크기로 γ를 키워 한계선에 닿는 점이다. 시간영역 결과와 비교하는 쪽이 이것이다.</li>
<li><b>왜 (i<sub>d</sub>, i<sub>q</sub>) 격자인가.</b> 90° 근처에서 작은 토크를 내는 전류는 진각 0.01°마다 수십 A씩 변한다(T ∝ I cos γ). 진각 격자를 쓰면 최소 전류 해를 건너뛰고, 제동 손실이 전류와 함께 커져 T(I)가 단조가 아니므로 이분법도 엉뚱한 교차점을 잡는다. i<sub>d</sub>를 고정하면 T는 i<sub>q</sub>에 대해 단조이므로, (i<sub>d</sub>, i<sub>q</sub>) 격자에서 T와 |v|를 한 번 계산해 두고 i<sub>d</sub>마다 T* 교차를 보간한다(표 한 벌 수 초).</li>
<li><b>검증.</b> 평균 맵 시간영역 모델(스크립트·Simscape A–C)의 실현점을 데드타임 0에서 진각 0.02°, 보상 없는 3 µs에서 0.1–0.5° 안에서 재현한다. 여유를 정확히 둔 QS 표를 C(평균 맵)에 넣으면 여유와 무관하게 오차 −1…−3 %다.</li>
<li><b>슬롯 고조파 확장 — 조화균형(<code>qs_harmonic_hb.py</code>).</b> 14절의 기구를 정상상태 식으로 옮긴다. ① 고조파 전류: 인버터가 기본파만 내면 자속이 평균에 머무므로 Δi(x) ≈ −L<sub>inc</sub><sup>−1</sup>[ψ(i<sub>0</sub>, x) − ψ̄(i<sub>0</sub>)]다. ② 제어기의 반응: 샘플된 Δi가 비례 경로·디커플링을 지나 한 샘플 뒤 가해지고 다시 Δi를 바꾼다. 작은 선형 주기 모델(샘플 75개 = 전기 4주기)로 푸므로 12차의 접힘까지 들어간다. ③ 클램프 평균: 잘린 몫 δ(V̄) = mean[v − clamp(v)], v = V̄ + Δv. ④ 평형: i* − i<sub>0</sub> = (K<sub>aw</sub>/K<sub>i</sub>)δ, V̄ − δ = R i<sub>0</sub> + jω<sub>e</sub>ψ̄(i<sub>0</sub>) + Δv<sub>dt</sub>. 여유를 둔 표의 Simscape 고조파 46건을 토크 RMS 0.7 N·m, 진각 0.04° 안에서 재현하고, 경우당 약 0.4 s다. ②를 빼면 측정 전류 디커플링 제어기에서 0.4–1.3 N·m 낙관적이다.</li>
<li><b>담지 못하는 것.</b> 제어기 동특성(과도), 그리고 계산기에 적어 넣지 않은 제어기 구조(노치·공진 제어기, 과변조, 전압 피드백 약자속). 여유 0 표처럼 90°를 넘어 무너진 점은 방향만 맞는다. 최종 후보는 위치별 맵 시간영역 모델로 확인한다.</li>
<li><b>MBC <code>calibratepmsm</code>과의 관계.</b> 둘 다 전압 한계 아래 최소 손실·전류 점을 고른다. QS 표는 교류 저항과 데드타임을 한계식에 직접 넣고, 16 krpm 저토크에서 수렴 실패가 없다. MBC 95 표의 실제 여유는 2d 모델에서 20 N·m 4.3 %다(Lab 맵·R<sub>dc</sub>로 만들었기 때문).</li>
</ul>
{B_QS}

<h2 id="vv">16. 검증 체계 — 무엇으로 모델을 믿나</h2>
<div class="scroll"><table><tr><th>대상</th><th>확인</th><th>결과</th></tr>
<tr><td>플랜트 맵</td><td>λ<sub>m</sub>, 16 krpm 역기전력</td><td>0.2195 Wb, 1042 V rms</td></tr>
<tr><td>기준표</td><td>MCB 16 krpm 표 대 Lab 자체 궤적</td><td>진각 0.4° 이내</td></tr>
<tr><td>플랜트 + 전압 한계</td><td>16 krpm 최대 축 토크</td><td>87.8 대 Lab 88.0 N·m (0.2 %)</td></tr>
<tr><td>변조기</td><td>t<sub>d</sub> = 0에서 반주기 평균 인가 전압 − 지령</td><td>약 10<sup>−10</sup> V</td></tr>
<tr><td>인버터·데드타임</td><td>스크립트 대 Simscape (실제 블랭킹)</td><td>t<sub>d</sub> 0: 0.05 %, t<sub>d</sub> 3 µs: 0.15–1.8 %</td></tr>
<tr><td>플랜트 대 Lab</td><td>스위칭 모델 도달점을 FMU로 되짚은 토크</td><td>1–4 % 이내; 전압은 Lab이 0.5–3 % 높음</td></tr>
<tr><td>지연 모형</td><td>보상된 지연 0/1/2샘플</td><td>차이 1 % 이하 (단계 1 결론 기각)</td></tr>
<tr><td>맵의 FEA 근거</td><td>Lab 48점 보간 대 운전 대역 직접 FEA(위치 평균)</td><td>자속 0.9 %, 토크 0.8 %, dT/dγ 0.06 N·m/°, 전압 0.7 % 이내 (13절)</td></tr>
<tr><td>공간 고조파</td><td>회전자 위치별 자속(단계 2d D)</td><td>같은 전류에서 평균 토크는 1.2 N·m 안에서 불변. 대신 제어기 운전점이 틀어짐 (14절)</td></tr>
<tr><td>정상상태 계산기</td><td>평균 맵 시간영역 실현점</td><td>진각 0.02°(t<sub>d</sub> 0), 0.1–0.5°(3 µs 무보상) (15절)</td></tr>
<tr><td>Motor-CAD 전압 출력</td><td>Lab·E-Magnetic 전압 대 같은 자속의 |R i + jω<sub>e</sub>ψ|</td><td class="warn">Motor-CAD가 2–4 % 높음, 원인 미확정</td></tr>
<tr><td>스큐</td><td>기준 모델 설정</td><td class="warn">SkewType 0 (스큐 없음으로 보임) — 실제 기계 확인 필요</td></tr></table></div>
<p class="mut">교훈: 한 모델만 믿지 않는다. 두 모델이 같은 원인에 대해 다른 답을 내면, 둘 사이에 다른 부분 하나를 찾는다. 단계 1→2의 지연, 보상식 2배 오류가 그렇게 나왔다.</p>

<h2 id="try">17. 직접 해보기</h2>
<h3>17.1 스위칭 모델 한 점 돌리기 (MATLAB R2026a, 약 2 s)</h3>
{cmd(RUN2)}
<p>바꿔 볼 옵션: <code>'td'</code> 0/1e-6/3e-6, <code>'dt_comp'</code> 1, <code>'th_err'</code> 1(레졸버 오프셋 °), <code>'n_delay'</code> 2, <code>'delay_comp'</code> 0, <code>'Tpwm'</code> 5e-5(20 kHz). 결과 구조체 <code>r</code>에는 <code>t, T, id, iq, gamma, Irms, V, sat, verr</code>가 있다.</p>
<h3>17.2 교정표를 바꿔 넣기 (MBC VsMax 95 %)</h3>
{cmd(RUN2B)}
<h3>17.3 Simscape 모델 열고 한 경우 돌리기 (약 15 s)</h3>
{cmd(RUN2C)}
<h3>17.4 Lab FMU로 운전점 하나 계산하기 (fmpy 가상환경)</h3>
{cmd(RUNFMU)}
<h3>17.5 이 페이지 그림 다시 그리기</h3>
{cmd('python "%s"' % (E10 / "plot_study_figs.py"))}
<h3>17.6 정상상태 계산기로 여유 15 % 기준표 만들기 (수 초)</h3>
{cmd(RUNQS)}
<p>결과는 <code>drive\\qs_tables.mat</code>의 <code>QS95</code>, <code>QS85</code>(필드 <code>Tv, idRef, iqRef</code>)다. 같은 파일을 덮어쓰므로 이미 있는 표를 모두 다시 쓰려면 여유를 전부 나열한다. <code>--map lab</code>이면 Lab 맵, <code>--norac</code>이면 교류 저항을 뺀다.</p>
<h3>17.7 Simscape 2d 한 경우 — 위치별 맵 + 여유 15 % 표 (약 30 s)</h3>
{cmd(RUN2D)}
<p>세 줄은 같은 표·같은 제어기에서 전동기 표만 다르다(평균 맵, 위치별 맵, 위치별 맵 + 기준 전류 디커플링). 결과 표의 <code>sat_pct</code>(클램프에 걸린 샘플 비율)와 <code>gamma</code>를 비교해 보라.</p>
<h3>17.8 생각해 볼 질문</h3>
<details class="q"><summary>Q1. 왜 전류를 캐리어 골·꼭짓점에서 샘플하나?</summary><p>대칭 중앙정렬 PWM에서는 전류 리플의 평균 통과 시점이 골과 꼭짓점이다. 그래서 그 순간 값이 곧 평균 전류이고, 아날로그 필터(와 그 지연) 없이 평균 전류를 얻는다.</p></details>
<details class="q"><summary>Q2. 이상 인버터(t<sub>d</sub> = 0)인데도 MCB 표의 5 N·m가 실패하는 이유는?</summary><p>MCB 표의 5 N·m 점은 우리 플랜트 기준 전압 한계의 101.4 %에 있다. 조절기가 포화되면 전류는 전압이 맞는 곳으로 흘러간다. 16 krpm에서 그곳은 γ가 큰 쪽이라 γ가 90°를 넘고 역토크(−4.3 N·m)가 된다. 5 % 여유 표에서는 +7 %로 추종한다.</p></details>
<details class="q"><summary>Q3. 데드타임 오차 전압은 7 %인데 토크는 왜 43 %나 줄어드나?</summary><p>포화된 조절기는 잃은 전압을 채울 수 없고, 운전점은 전압이 덜 드는 방향(γ 증가, 그림 3b)으로 0.67° 밀린다. 20 N·m 부근에서 dT/dγ ≈ −12 N·m/°이므로 −8 N·m다. 작은 전압 오차가 큰 각도 민감도를 만나 확대된다.</p></details>
<details class="q"><summary>Q4. 전압 여유 5 %가 왜 전류 +2 %인가?</summary><p>|v| ≈ ω<sub>e</sub>|λ|이고 λ<sub>d</sub>를 깎는 수단은 i<sub>d</sub>뿐이다: Δi<sub>d</sub> ≈ ΔV/(ω<sub>e</sub>L<sub>d</sub>) = 20 V/(6702 × 0.85 mH) ≈ 3.5 A 첨두 ≈ 2.5 A rms. 138 A 대비 약 2 %다(관측 +2.9 A).</p></details>
<details class="q"><summary>Q5. 단계 1에서 “지연 2샘플이면 붕괴”가 나온 진짜 이유는?</summary><p>dq 좌표계 지연에는 회전이 없는데 보상각 ω<sub>e</sub>(n+½)T<sub>s</sub> = 48°를 더했다. 보상이 인공 각 오차 48°가 된 것이다(그림 4b).</p></details>
<details class="q"><summary>Q6. 스크립트와 Simscape가 20 N·m, 3 µs에서만 1.8 % 다른 이유는?</summary><p>블랭킹 중 전류가 0을 지나면, 스크립트는 에지 시점의 부호로만 판정하고 Simscape는 다이오드가 실제 전류로 판정한다. 20 N·m은 필요 전압이 한계의 99.9 %인 불량조건 점이라 작은 볼트·초 차이가 크게 보인다.</p></details>
<details class="q"><summary>Q7. 속도를 고정한 것이 결론에 영향을 주나?</summary><p>이 연구는 정상 운전점의 도달 가능성과 정밀도를 본다. 차량 관성은 전기 시상수(ms)보다 훨씬 느리므로 16 krpm 고정은 합리적이다. 속도 루프·기계 공진·가감속 중 약자속 과도는 범위 밖이다.</p></details>
<details class="q"><summary>Q8. 고조파는 평균 토크를 바꾸지 않는데 왜 토크가 60 % 줄어드나?</summary><p>같은 평균 전류에서의 평균 토크는 그대로다(1.2 N·m 이내). 줄어드는 것은 제어기가 도달하는 평균 전류다. 고조파 전류가 비례 이득과 디커플링을 지나 명령 전압에 약 100 V의 고조파를 싣고, 명령이 클램프에서 잘린다. 역산 안티와인드업이 잘린 몫의 평균을 적분기에 넣어 평균 전류 오차 mean(잘린 전압)/8.5 Ω가 남는다. 그 방향이 γ를 키우는 쪽이고, dT/dγ ≈ −11 N·m/°라 토크가 크게 준다(14절).</p></details>
<details class="q"><summary>Q9. 고조파가 먹는 전압을 고정 여유로 계산기에 넣으면 안 되나?</summary><p>안 된다. 잘리는 시간은 기본파 명령과 한계 사이의 틈에 비선형으로 달려 있다. 그래서 D가 도달한 점에 남는 평균 여유는 표의 여유와 함께 커진다(5.0 → 8.1 → 11.7 %). MBC 95에서 교정한 값을 MBC 90에 쓰면 토크를 19.9 N·m로 예측하지만 실제는 12.9 N·m다. 고정된 전압량이 아니라 클리핑 평균 δ(V̄)라는 함수로 넣어야 한다. 그렇게 넣은 것이 15절의 조화균형 확장이고, MBC 90을 13.7 N·m로 계산한다.</p></details>
<details class="q"><summary>Q10. 계산기가 진각 격자 대신 (i<sub>d</sub>, i<sub>q</sub>) 격자로 최소 전류점을 찾는 이유는?</summary><p>γ ≈ 89.8°에서 T* = 0–5 N·m를 내는 전류는 γ 0.01°마다 수십 A씩 변한다(i<sub>q</sub> = I cos γ가 아주 작기 때문). 진각 0.02° 격자에서는 최소 전류 해 사이를 건너뛰어, 전압 한계보다 훨씬 안쪽의 큰 전류 점을 고른다. i<sub>d</sub>를 고정하면 T는 i<sub>q</sub>에 대해 단조라 교차점이 하나다.</p></details>

<h2 id="ref">18. 참고 문헌·자료</h2>
<ul>
<li>S.-K. Sul(설승기), <i>Control of Electric Machine Drive Systems</i>, Wiley–IEEE Press, 2011 — 전류 제어, 디지털 지연, 데드타임, 약자속 전반.</li>
<li>B.-H. Bae, S.-K. Sul, “A compensation method for time delay of full-digital synchronous frame current regulator of PWM AC drives,” <i>IEEE Trans. Ind. Appl.</i>, vol. 39, no. 3, 2003 — 1.5 T<sub>s</sub> 지연과 회전 보상(6절).</li>
<li>J.-W. Choi, S.-K. Sul, “Inverter output voltage synthesis using novel dead time compensation,” <i>IEEE Trans. Power Electron.</i>, vol. 11, no. 2, 1996 — 데드타임 전압 오차와 보상(8절).</li>
<li>D. G. Holmes, T. A. Lipo, <i>Pulse Width Modulation for Power Converters: Principles and Practice</i>, Wiley–IEEE Press, 2003 — 영상분 주입 SVPWM, 중앙정렬 PWM(7절).</li>
<li>MathWorks — <a href="https://kr.mathworks.com/help/mbc/mbc_gs/generate-current-controller-calibration-tables-for-flux-based-motor-controllers.html">Generate Current Controller Calibration Tables for Flux-Based Motor Controllers</a>(calibratepmsm), <a href="https://kr.mathworks.com/help/sps/ug/hev-pmsm-drive-test-harness.html">HEV PMSM Drive Test Harness</a>, Motor Control Blockset <code>mcb.generateMotorLUT</code>, Simscape Electrical FEM-Parameterized PMSM 도움말.</li>
<li>Ansys Motor-CAD 2026 R1 도움말 — Lab, Saturation and Loss Maps export(FEA, 회전자 위치별 결과), Lab BPM FMU.</li>
<li>K. J. Åström, T. Hägglund, <i>Advanced PID Control</i>, ISA, 2006 — 역산(back-calculation) 안티와인드업(14절).</li>
<li>D. N. Zmood, D. G. Holmes, “Stationary frame current regulation of PWM inverters with zero steady-state error,” <i>IEEE Trans. Power Electron.</i>, vol. 18, no. 3, 2003 — 공진(PR) 전류 제어기, 특정 고조파를 따로 다루는 방법(14절 대책 ③).</li>
<li>J.-M. Kim, S.-K. Sul, “Speed control of interior permanent magnet synchronous motor drive for the flux weakening operation,” <i>IEEE Trans. Ind. Appl.</i>, vol. 33, no. 1, 1997 — 전압 피드백 약자속(14절 대책 ⑤).</li>
</ul>
{B_GEN}
"""

doc = ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
       '<title>구동 모델 해설</title><style>' + CSS + '</style></head><body><main>' + body + '</main>' + COPY_JS + '</body></html>')
(HERE / "drive_model_study.html").write_text(doc, encoding="utf-8")
print("wrote", HERE / "drive_model_study.html")
