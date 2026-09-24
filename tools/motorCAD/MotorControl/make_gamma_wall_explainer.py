# -*- coding: utf-8 -*-
"""Build gamma_wall_explainer.html: phenomenon, theory, reproduction method, results, paths.
Figures are embedded (single file). Data: gamma_highspeed_result.md B2/B6, stage1_results.csv,
stage2_results.csv, stage2b_results.csv, lab_gamma_sweep.json, lab_stage3c.json, stage2c_results.csv.
python make_gamma_wall_explainer.py
"""
import base64
import csv
import json
import re
from pathlib import Path

from report_links import COPY_JS, FILES_CSS, LINK_NOTE, files_box, item

HERE = Path(__file__).resolve().parent
DRV = Path(r"D:\KangDH\Thesis\e10\work_lab_pc1\drive")
FMU = Path(r"D:\KangDH\Thesis\e10\work_lab_pc1\fmu")
EX = Path(r"D:\KangDH\Thesis\e10\work_lab_pc1\existing")
E10 = HERE / "e10drive"
RES = DRV / "stage1_results.csv"
DATA16 = DRV / "e10_stage1_data_16000_shaft.mat"
RUN2 = ("addpath('%s'); S = load('%s'); r = sim_e10_stage2(S, struct('Tref_fn', @(t) 20*(t>=0.005), "
        "'td', 3e-6, 'Tstop', 0.08)); plot(r.t*1e3, r.T)") % (E10, DATA16)

BOX0 = files_box("이 결과의 파일 — 단계 0", [
    item(EX / "gamma_wall_mc.csv", "몬테카를로 결과 (진각별 산포·반전·전압 초과)"),
    item(EX / "gamma_wall_mc_200A.csv", "같은 시험, 200 A"),
    item(EX / "gamma_wall_mc.png", "그림 1 원본", cmd=""),
    item(EX / "gammagrid_ref_hyb_fine16000.json", "재샘플에 쓴 16 krpm (I, γ) 격자 (Motor-CAD)", cmd="")],
    note="몬테카를로 스크립트는 당시 스크래치패드에 있어 남아 있지 않다(ipmfea로 옮길 예정).")
BOX1 = files_box("이 결과의 파일 — 단계 1 (평균값 dq Simulink)", [
    item(E10 / "build_e10_stage1.m", "Simulink 모델 생성 스크립트", cmd="addpath('%s'); S = load('%s'); build_e10_stage1(S)" % (E10, DATA16)),
    item(E10 / "e10_stage1.slx", "생성된 모델 (저장소 미추적)"),
    item(E10 / "sim_e10_stage1.m", "같은 모델의 스크립트판 (격자 실험용)"),
    item(E10 / "run_e10_stage1.m", "오프셋 × 지연 격자, 지연 보상, 상한 스캔", cmd="addpath('%s'); run_e10_stage1(16000)" % E10),
    item(RES, "결과 표"),
    item(DATA16, "플랜트·기준표·이득 (16 krpm, 축 토크 기준)"),
    item(DRV / "stage1_offset_delay.png", "그림 2 원본", cmd="")])
BOX2 = files_box("이 결과의 파일 — 단계 2 (스위칭 모델)", [
    item(E10 / "sim_e10_stage2.m", "스위칭 모델 본체 (사건 구동 SVPWM·데드타임·RK4)", cmd=RUN2),
    item(E10 / "run_e10_stage2.m", "68 격자 + 파형 6 (part = [i n] 배치 분할)", cmd="addpath('%s'); run_e10_stage2([], 0, [1 1])" % E10),
    item(E10 / "merge_e10_stage2.m", "배치 결과 합치기"),
    item(DRV / "stage2_results.csv", "격자 결과 (표·그림 3의 원자료)"),
    item(DRV / "stage2_traces.mat", "상전류 파형 (그림 4, THD)"),
    item(E10 / "plot_stage2.py", "그림 3·4와 THD 계산")])
BOX2B = files_box("이 결과의 파일 — 단계 2b (교정 전압 여유)", [
    item(E10 / "mbc_ref_from_lab.m", "MBC calibratepmsm 교정표 (VsMax 100/95/90 %)", cmd="addpath('%s'); M = mbc_ref_from_lab([], [1 0.95 0.9]);" % E10),
    item(DRV / "mbc_tables.mat", "교정표·TPA 결과 (MATLAB table 포함)"),
    item(E10 / "mcb_ref_from_lab.m", "비교 기준 MCB 기준표 생성"),
    item(DRV / "mcb_lut_shaft.mat", "MCB 기준표 (축 토크)"),
    item(E10 / "run_e10_stage2b.m", "교정표 4종 × 토크 × 데드타임", cmd="addpath('%s'); t = run_e10_stage2b();" % E10),
    item(DRV / "stage2b_results.csv", "결과 표 (그림 5 원자료)"),
    item(E10 / "plot_stage2b.py", "그림 5")])
BOX3 = files_box("이 결과의 파일 — 단계 3 (Motor-CAD Lab FMU)", [
    item(Path(r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot"), "Motor-CAD 기준 모델 (Lab 빌드 포함)", cmd=""),
    item(E10 / "export_lab_model.py", "새 Motor-CAD 창에서 .lab 내보내기"),
    item(FMU / "e10Turn6V261.lab", "FMU 입력 Lab 모델", cmd=""),
    item(Path(r"C:\Program Files\ANSYS Inc\v261\motorcad\FMU\Ansys_Motor-CAD_Lab_BPM.fmu"), "Lab BPM FMU (FMI 2.0)", cmd=""),
    item(E10 / "lab_fmu.py", "FMU 래퍼 (모드 0/1/2) — 실행하면 16 krpm 20 N·m 예제"),
    item(E10 / "lab_gamma_sweep.py", "진각 강제 스윕 (그림 6)"),
    item(FMU / "lab_gamma_sweep.json", "스윕 결과", cmd=""),
    item(E10 / "lab_stage3c.py", "스위칭 모델 도달점의 손실 (그림 7)"),
    item(FMU / "lab_stage3c.json", "3(c) 결과", cmd=""),
    item(E10 / "plot_lab_gamma_sweep.py", "그림 6"),
    item(E10 / "plot_stage3c.py", "그림 7")])
BOX2C = files_box("이 결과의 파일 — 단계 2c (Simscape)", [
    item(DRV / "stage2c" / "e10_stage2c.slx", "Simscape 모델 — 열어서 블록 구성 확인"),
    item(E10 / "build_e10_stage2c.m", "하니스를 복사·개조해 모델 생성"),
    item(E10 / "run_e10_stage2c.m", "4 경우 실행·비교 (경우당 11–22 s)", cmd="addpath('%s'); R = run_e10_stage2c();" % E10),
    item(DRV / "stage2c_results.csv", "비교 결과"),
    item(Path(r"D:\KangDH\Thesis\e10\work_lab_pc1\mw_examples\ex1\HEVPMSMDriveTestHarness.slx"), "원본 MathWorks 예제")])


def img(name, cap):
    b = base64.b64encode((HERE / name).read_bytes()).decode()
    return '<figure><img src="data:image/png;base64,%s" alt="%s"><figcaption>%s</figcaption></figure>' % (b, re.sub(r"<[^>]+>", "", cap), cap)


rows = list(csv.DictReader(open(RES, encoding="utf-8")))


def cell(T, off, dly):
    for r in rows:
        if r["kind"] == "offset_delay" and float(r["T_ref"]) == T and float(r["offset_deg"]) == off \
                and float(r["delay_samples"]) == dly:
            return float(r["err_pct"]), float(r["sat_pct"]), float(r["gamma"])
    return None


od = ""
for T in (20, 60):
    for off in (0, 1, 2):
        cs = [cell(T, off, d) for d in (0, 1, 2)]
        tds = "".join('<td class="%s">%+.0f %%%s</td>' % ("bad" if abs(e) > 50 else ("warn" if abs(e) > 10 else "ok"), e,
                                                          " (포화 %.0f %%)" % s if s > 1 else "") for e, s, g in cs)
        od += "<tr><td>%d N·m</td><td>%d°</td>%s</tr>" % (T, off, tds)


def cls(e):
    return "bad" if abs(e) > 50 else ("warn" if abs(e) > 10 else "ok")


# ---- 단계 2 (스위칭) 표
s2 = list(csv.DictReader(open(DRV / "stage2_results.csv", encoding="utf-8")))


def s2get(kind, **kw):
    for r in s2:
        if r["kind"] == kind and all(float(r[k]) == v for k, v in kw.items()):
            return r
    return None


dt_rows = ""
for T in (5, 20, 60, 85):
    tds = ""
    for td in (0, 1, 2, 3):
        e = float(s2get("deadtime", T_ref=T, td_us=td)["err_pct"])
        tds += '<td class="%s">%+.0f %%</td>' % (cls(e), e)
    for td in (2, 3):
        e = float(s2get("dt_comp", T_ref=T, td_us=td)["err_pct"])
        tds += '<td class="%s">%+.0f %%</td>' % (cls(e), e)
    dt_rows += "<tr><td>%d N·m</td>%s</tr>" % (T, tds)

od2 = ""
for T in (20, 60):
    for off in (0, 1, 2):
        tds = ""
        for nd in (0, 1, 2):
            r = s2get("offset_delay", T_ref=T, offset_deg=off, delay_samples=nd)
            e, s = float(r["err_pct"]), float(r["sat_pct"])
            tds += '<td class="%s">%+.0f %%%s</td>' % (cls(e), e, " (포화 %.0f %%)" % s if s > 1 else "")
        od2 += "<tr><td>%d N·m</td><td>%d°</td>%s</tr>" % (T, off, tds)

ceil_rows = ""
for T in (5, 20, 40, 60, 80, 100):
    a, b = s2get("ceiling", T_ref=T, td_us=0), s2get("ceiling", T_ref=T, td_us=2)
    ceil_rows += "<tr><td>%d N·m</td><td>%.1f</td><td>%.2f°</td><td>%.1f</td><td>%.1f</td><td>%.2f°</td></tr>" % (
        T, float(a["T"]), float(a["gamma"]), float(a["I_rms"]), float(b["T"]), float(b["gamma"]))

thd = json.load(open(HERE / "stage2_thd.json"))
thd_txt = ", ".join("%g N·m %.1f→%.1f %%" % (T, [x for x in thd if x["T_ref"] == T and x["td_us"] == 0][0]["THD_pct"],
                                              [x for x in thd if x["T_ref"] == T and x["td_us"] == 3][0]["THD_pct"])
                    for T in (5, 20, 60))

# ---- 단계 2b (교정 여유)
s2b = list(csv.DictReader(open(DRV / "stage2b_results.csv", encoding="utf-8")))
j3c = {p["tag"]: p for p in json.load(open(FMU / "lab_stage3c.json"))["points"]}


def s2bget(tb, T, td, dc):
    for r in s2b:
        if r["table"] == tb and float(r["T_ref"]) == T and float(r["td_us"]) == td and float(r["dt_comp"]) == dc:
            return r


mb_rows = ""
for tb, lab in (("MCB", "MCB (여유 ≈ 0)"), ("MBC 100", "MBC VsMax 100 %"), ("MBC 95", "MBC VsMax 95 %"),
                ("MBC 90", "MBC VsMax 90 %")):
    tds = ""
    for T in (5, 20, 60):
        for td, dc in ((0, 0), (3, 0), (3, 1)):
            e = float(s2bget(tb, T, td, dc)["err_pct"])
            tds += '<td class="%s">%+.0f %%</td>' % (cls(e), e)
    r20 = s2bget(tb, 20, 0, 0)
    p = j3c["s2bref|%s|T20" % tb]
    tds += "<td>%.1f A · %.2f°</td><td>%.0f V</td><td>%+.1f %%</td>" % (
        float(r20["I_ref_rms"]), float(r20["gamma_ref"]), p["Phase_Voltage_RMS"], 100*(p["P_loss"]/p["opt_P_loss"] - 1))
    mb_rows += "<tr><td>%s</td>%s</tr>" % (lab, tds)

# ---- 단계 3 (Lab FMU 진각 스윕)
sw = json.load(open(FMU / "lab_gamma_sweep.json"))
sw_rows = ""
for rpm in (16000.0, 8000.0, 4000.0):
    for T in (20.0, 60.0):
        o = [x for x in sw["optimum"] if x["rpm"] == rpm and x["T_req"] == T][0]
        feas = [p["gamma"] for p in sw["sweep"] if p["rpm"] == rpm and p["T_req"] == T and p["V_feasible"]]
        p80 = [p for p in sw["sweep"] if p["rpm"] == rpm and p["T_req"] == T and p["gamma"] == 80][0]
        sw_rows += "<tr><td>%d rpm</td><td>%d N·m</td><td>%.2f°</td><td>%.1f A</td><td>%.1f kW</td><td>%s</td><td>%s</td></tr>" % (
            rpm, T, o["Phase_Advance"], o["Stator_Current_Phase_RMS"], o["P_loss"]/1e3,
            ("%g–%g°" % (min(feas), max(feas))) if feas else "없음",
            ("%+.0f %%" % (100*(p80["P_loss"]/o["P_loss"] - 1))) if p80["V_feasible"] else
            "전압 초과 (%.0f V)" % p80["Phase_Voltage_RMS"])

# ---- 단계 2c (Simscape 교차 확인, 있으면)
s2c_path = DRV / "stage2c_results.csv"
s2c_html = '<p class="mut">Simscape 교차 확인은 아직 결과 파일이 없다.</p>'
if s2c_path.exists():
    s2c = list(csv.DictReader(open(s2c_path, encoding="utf-8")))
    body = "".join(
        "<tr><td>%s N·m</td><td>%s µs</td><td>%.2f</td><td>%.2f</td><td class=\"%s\">%+.2f %%</td><td>%.2f° / %.2f°</td>"
        "<td>%.1f / %.1f A</td><td>%.2f / %.2f</td><td>%.0f / %.0f %%</td><td>%.0f s</td></tr>" % (
            r["T_ref"], r["td_us"], float(r["script_T"]), float(r["T"]),
            "ok" if abs(float(r["dT_pct"])) < 1 else "warn", float(r["dT_pct"]),
            float(r["script_gamma"]), float(r["gamma"]), float(r["script_I_rms"]), float(r["I_rms"]),
            float(r["script_T_ripple_pp"]), float(r["T_ripple_pp"]), float(r["script_sat_pct"]), float(r["sat_pct"]),
            float(r["run_s"])) for r in s2c)
    s2c_html = """<p>MathWorks <i>HEV PMSM Drive Test Harness</i>를 코드로 복사·개조해(<code>build_e10_stage2c.m</code>) 스크립트 스위칭 모델과 같은 운전점을 돌렸다.
FEM-Parameterized PMSM을 <code>fem_motor_dq0</code> 변형(DQcartesian)으로 바꿨다. 블록이 회전자각 축을 요구해 같은 2-D Lab ψ<sub>d</sub>/ψ<sub>q</sub> 맵을 회전자각 7점에 그대로 복제했다. 즉 회전자 위치 의존성(슬롯 고조파·코깅)은 없다. 토크는 Lab 축 토크 표를 썼다.
속도는 이상 각속도원으로 16 000 rpm 고정, 인버터는 이상 스위치 + 역병렬 다이오드(도통 강하 ≈ 0), 데드타임은 <b>실제 상보 게이트 블랭킹</b>(켜짐 에지를 t<sub>d</sub>만큼 지연, 블랭킹 동안 도통은 다이오드가 결정), 제어기는 <code>sim_e10_stage2</code>와 같은 50 µs 이산 MATLAB Function(지연 보상·1샘플 지연 포함), 10 kHz SVPWM 양 끝 갱신, 가변 스텝 ode23t(MaxStep 5 µs).</p>
<div class="scroll"><table><tr><th>지령</th><th>t<sub>d</sub></th><th>T 스크립트</th><th>T Simscape</th><th>차이</th><th>γ 스크립트 / Simscape</th><th>I rms</th><th>토크 리플 p-p [N·m]</th><th>포화</th><th>계산 시간</th></tr>{BODY}</table></div>
<p><b>스크립트 스위칭 모델이 검증됐다.</b> 무데드타임 두 점은 토크 0.05 % 이내, 진각 0.001° 이내로 같다. t<sub>d</sub> 3 µs는 60 N·m +0.15 %, 20 N·m −1.8 %(0.2 N·m)다.
차이는 데드타임 모형에서 온다 — 스크립트는 스위칭 순간의 전류 부호로 지연 여부를 정하고, Simscape는 블랭킹 구간 중 전류 영교차까지 다이오드가 결정한다. 20 N·m은 필요 전압이 한계의 99.9 %인 불량조건 점이라 작은 볼트·초 차이가 토크를 크게 움직인다(0.02 s로 짧게 돌리면 포화를 빠져나오지 못해 15.0 N·m — 교차 확인은 0.08 s 이상 필요).
4.3–4.4절의 데드타임 결론(−43 %/−16 %)은 Simscape에서도 −44 %/−15 %로 같다.</p>
<p class="mut">빌드 함정: 변형 선택은 <code>ComponentPath</code>가 아니라 <code>SourceFile</code>로 해야 저장·재로드 후에도 유지된다(초기 실행은 하니스 원래의 6극쌍 이상 모터를 조용히 돌렸다). 블록은 id 격자가 0을 포함한 대칭을 요구해 Lab 맵(−650…0 A)을 +650 A까지 연장했다(ψ<sub>d</sub> 선형, ψ<sub>q</sub>·토크는 id = 0 값 유지) — 운전점(−190…−290 A)은 닿지 않는다.</p>""".replace("{BODY}", body)

# ---- 4.9 종합 판단: 직접 FEA 맵, 손실 규약, 슬롯 고조파(단계 2d), 정상상태 계산기
FP = Path(r"D:\KangDH\Thesis\e10\work_lab_pc1\fea_pos")
EMC = Path(r"D:\KangDH\Thesis\e10\work_lab_pc1\emag_check")
PA = json.load(open(FP / "posmap_band_analysis.json"))
fea_rows = "".join(
    "<tr><td>%d N·m</td><td>%.2f°</td><td>%.1f / %.1f</td><td>%.1f / %.1f</td><td>%.2f / %.2f</td><td>%.2f / %.2f</td>"
    "<td>%.1f / %.1f</td><td>%.0f</td><td>%.0f / %.0f</td></tr>" % (
        o["T_ref"], o["gamma"], 1e3*o["psi_d_fea"], 1e3*o["psi_d_lab"], 1e3*o["psi_q_fea"], 1e3*o["psi_q_lab"],
        o["T_em_fea"], o["T_em_lab"], o["dTdg_fea"], o["dTdg_lab"], o["V_fea"], o["V_lab"], o["V_lab_export"],
        o["T_ripple_pp_fea"], o["T_ripple_pp_lab"]) for o in PA["ops"])
o20 = [o for o in PA["ops"] if o["T_ref"] == 20][0]
hm_ops = {o["T_ref"]: o for o in PA["ops"]}


def s2d_load(*names):
    out = []
    for n in names:
        p = DRV / n
        if p.exists():
            out += list(csv.DictReader(open(p, encoding="utf-8")))
    return out


S2D = s2d_load("stage2d_results.csv", "stage2d_results_mbc90.csv")
S2Q = s2d_load("stage2d_results_qs.csv")


def s2d(rows, vn, tb, T, td):
    for r in rows:
        if r["variant"] == vn and r["table"] == tb and float(r["T_ref"]) == T and float(r["td_us"]) == td:
            return r
    return None


def ecell(r, sat=False):
    if r is None:
        return "<td class=\"mut\">–</td>"
    e = float(r["err_pct"])
    txt = "%+.0f %%" % e if abs(e) >= 10 else "%+.1f %%" % e
    s = float(r["sat_pct"])
    return '<td class="%s">%s%s</td>' % (cls(e) if abs(e) > 5 else "ok", txt,
                                        ' <span class="mut">(포화 %.0f)</span>' % s if sat and s >= 1 else "")


V_NAMES = [("lab_rep", "A — Lab 맵, 기존 축 토크, R<sub>dc</sub>"), ("lab_conv", "B — A + 손실 규약 축 토크 + R<sub>ac,eff</sub>"),
           ("fea_avg", "C — B의 운전 대역을 직접 FEA 위치 평균으로"), ("fea_pos", "D — C를 회전자 위치별(슬롯 고조파)로"),
           ("fea_pos_ff", "D<sub>ff</sub> — D + 기준 전류 디커플링")]
V_COLS = [("MCB", 20, 0), ("MCB", 20, 3), ("MCB", 60, 0), ("MBC 95", 20, 0), ("MBC 95", 20, 3), ("MBC 95", 60, 0),
          ("MBC 90", 20, 0), ("MBC 90", 60, 0)]
var_rows = "".join("<tr><td>%s</td>%s</tr>" % (lab, "".join(ecell(s2d(S2D, vn, tb, T, td), sat=True)
                                                              for tb, T, td in V_COLS)) for vn, lab in V_NAMES)
var_head = "".join("<th>%s<br>%d N·m%s</th>" % (tb, T, ", 3 µs" if td else "") for tb, T, td in V_COLS)

HM = json.load(open(FP / "qs_harmonic_margin.json"))


def hmget(vn, tb, T, td=0.0):
    for x in HM:
        if x["variant"] == vn and x["table"] == tb and x["T_ref"] == T and x["td_us"] == td:
            return x


res_rows = ""
for tb in ("MCB", "MBC 95", "MBC 90"):
    for T in (5, 20, 60):
        c, d, f = hmget("fea_avg", tb, T), hmget("fea_pos", tb, T), hmget("fea_pos_ff", tb, T)
        if d is None:
            continue
        res_rows += ("<tr><td>%s</td><td>%d N·m</td><td>%.1f %%</td><td>%.2f°</td><td>%.2f° → %.2f°</td><td>%.0f %%</td>"
                     "<td>%.2f / %.2f</td><td>%.1f %%</td><td>%s</td></tr>") % (
            tb, T, 100*d["m_table"], d["gamma_ref"], c["gamma_sim"] if c else float("nan"), d["gamma_sim"], d["sat"],
            d["T_sim"], d["T_map"], 100*d["m_eq"],
            "%.2f° · %.1f N·m" % (d["gamma_pred"], d["T_pred"]) if "gamma_pred" in d and tb != "MBC 95" else "(교정점)")
res_max = max(abs(x["T_sim"] - x["T_map"]) for x in HM if x["td_us"] == 0)
res_max3 = max(abs(x["T_sim"] - x["T_map"]) for x in HM if x["td_us"] == 3)

def need_margin(vn, T, td=0, tol=5.0):
    """smallest QS-table margin [%] with |error| <= tol"""
    for tb in QS_TABS:
        r = s2d(S2Q, vn, tb, T, td)
        if r is not None and abs(float(r["err_pct"])) <= tol:
            return 100 - float(tb.split()[1])
    return None


EM = json.load(open(EMC / "emag_loss_check.json"))
S2Q = S2Q + s2d_load("stage2d_results_qs2.csv", "stage2d_results_qs3.csv")
QS_TABS = [t for t in ("QS 95", "QS 90", "QS 85", "QS 80", "QS 75", "QS 70") if any(r["table"] == t for r in S2Q)]
margin_rows = ""
for vn, lab in (("fea_avg", "C 평균 맵"), ("fea_pos", "D 위치별 맵"), ("fea_pos_ff", "D<sub>ff</sub> 기준 전류 디커플링")):
    for T, td in ((5, 0), (20, 0), (60, 0), (20, 3)):
        cells = [s2d(S2Q, vn, tb, T, td) for tb in QS_TABS]
        if not any(cells):
            continue
        margin_rows += "<tr><td>%s</td><td>%d N·m%s</td>%s</tr>" % (lab, T, ", 3 µs" if td else "",
                                                                  "".join(ecell(c, sat=True) for c in cells))
margin_head = "".join("<th>%d %%</th>" % (100 - int(t.split()[1])) for t in QS_TABS)
COST = json.load(open(FP / "qs_margin_cost.json"))


def cost(T, m):
    base = [c for c in COST if c["T"] == T and c["margin"] == 5]
    x = [c for c in COST if c["T"] == T and c["margin"] == m]
    return (x[0]["I_rms"], 100*(x[0]["P_loss"]/base[0]["P_loss"] - 1), x[0]["P_loss"]) if x and base else None


cost_rows = ""
for m in sorted(set(c["margin"] for c in COST)):
    tds = ""
    for T in (5, 20, 60):
        c = cost(T, m)
        tds += "<td>%.1f A · %.1f kW (%+.1f %%)</td>" % (c[0], c[2]/1e3, c[1]) if c else "<td class=\"mut\">표 밖</td>"
    cost_rows += "<tr><td>%d %%</td>%s</tr>" % (m, tds)
dg_d = [d["gamma_sim"] - c["gamma_sim"] for d, c in ((hmget("fea_pos", tb, T), hmget("fea_avg", tb, T))
                                                      for tb in ("MBC 95", "MBC 90") for T in (5, 20, 60)) if d and c]
m20 = {tb: 100*hmget("fea_pos", tb, 20)["m_eq"] for tb in ("MCB", "MBC 95", "MBC 90")}
p90 = hmget("fea_pos", "MBC 90", 20)
BOX49 = files_box("이 결과의 파일 — 직접 FEA 맵, 단계 2d, 정상상태 계산기", [
    item(E10 / "fea_posmap.py", "Motor-CAD 새 창에서 회전자 위치별 FEA 포화맵 계산 (조각·재개 가능)"),
    item(E10 / "mc_launch.py", "Motor-CAD 새 인스턴스 기동·PID 기록 (사용자 창은 건드리지 않음)"),
    item(FP / "posmap_band_00.mat", "FEA 대역 맵 조각 (00–05, 조각당 i_q 한 값 × i_d 29점 × 위치 121)"),
    item(E10 / "fea_posmap_analyze.py", "Lab 대조, 고조파, 운전점 파형, Simscape 표(stage2d_tables.mat)"),
    item(FP / "posmap_band_analysis.json", "대조·고조파 결과 (그림 8·9 원자료)", cmd=""),
    item(DRV / "stage2d_tables.mat", "Simscape 표 변형 B·C·D (V_lab_conv, V_fea_avg, V_fea_pos)"),
    item(E10 / "patch_stage2c_ctrl.m", "저장된 Simscape 모델 제어기에 기준 전류 디커플링 선택지 추가"),
    item(E10 / "run_e10_stage2d.m", "표 변형 × 기준표(MCB, MBC, QS) × 토크 × 데드타임",
         cmd="addpath('%s'); R = run_e10_stage2d([20 0], 0.08, [], {'fea_pos'}, 'try.csv', {'QS 80'});" % E10),
    item(DRV / "stage2d_results.csv", "A–D, D_ff × MCB·MBC 95 결과"),
    item(DRV / "stage2d_results_mbc90.csv", "MBC 90 결과"),
    item(DRV / "stage2d_results_qs.csv", "QS 표(여유 5–20 %) 결과 (그림 11 원자료)"),
    item(DRV / "stage2d_results_qs2.csv", "QS 표 여유 25 % 결과"),
    item(DRV / "stage2d_results_qs3.csv", "QS 표 여유 30 % 결과 (60 N·m는 표 밖)"),
    item(DRV / "run_stage2d_qs.m", "QS 표 실행 배치 (Start-Process로 분리 실행)"),
    item(E10 / "qs_opsolver.py", "정상상태 운전점 계산기 + QS 기준표 생성 (--tables)",
         cmd="python \"%s\" --map fea --tables 0.05,0.10,0.15,0.20" % (E10 / "qs_opsolver.py")),
    item(DRV / "qs_tables.mat", "QS 기준표 (여유 5–30 %)"),
    item(E10 / "qs_harmonic_margin.py", "D 실현점의 남은 여유, 고정 여유 예측 시험, 여유의 손실 비용"),
    item(E10 / "qs_harmonic_hb.py", "조화균형 확장: 고조파 전류·제어기 반응·클램프 평균·안티와인드업 평형 (그림 13)",
         cmd='python "%s"' % (E10 / "qs_harmonic_hb.py")),
    item(FP / "qs_harmonic_hb.json", "조화균형 계산 대 Simscape 전 경우", cmd=""),
    item(E10 / "emag_loss_check.py", "E-Magnetic 손실·축 토크 규약 확인 (Hybrid 대 FullFEA)"),
    item(E10 / "plot_fea_check.py", "그림 8–13")])

HB = json.load(open(FP / "qs_harmonic_hb.json"))
hb_qs = [x for x in HB if x["variant"] != "fea_avg" and x["table"].startswith("QS")]
hb_rms = (sum((x["T_shaft"] - x["sim_T"])**2 for x in hb_qs)/len(hb_qs))**0.5
hb_rmsg = (sum((x["gamma"] - x["sim_gamma"])**2 for x in hb_qs)/len(hb_qs))**0.5
hb_mcb5 = [x for x in HB if x["variant"] == "fea_pos" and x["table"] == "MCB" and x["T_ref"] == 5 and x["td_us"] == 0][0]


S2E = s2d_load("stage2e_results_D.csv", "stage2e_results_C.csv")
HBR = json.load(open(FP / "qs_hb_remedies.json")) if (FP / "qs_hb_remedies.json").exists() else []


def s2e(rem, vn, tb, T, td=0):
    for r in S2E:
        if r["remedy"] == rem and r["variant"] == vn and r["table"] == tb and float(r["T_ref"]) == T \
                and float(r["td_us"]) == td:
            return r


def hbr(rem, tb, T, td=0):
    for h in HBR:
        if h["remedy"] == rem and h["table"] == tb and h["T_ref"] == T and h["td_us"] == td:
            return h


REM_NAMES = [("base", "대책 없음"), ("notch", "③ 노치 (6차·접힌 12차)"), ("pr6", "③ 6차 공진(PR) 억누르기"),
             ("hex", "④ 과변조 (육각형 한계)"), ("fw", "⑤ 전압 피드백 약자속")]
REM_COLS = [("QS 95", 5, 0), ("QS 95", 20, 0), ("QS 95", 60, 0), ("QS 95", 20, 3), ("QS 85", 5, 0), ("QS 85", 20, 0),
            ("QS 85", 60, 0)]


def rem_cost(rn):
    b, r = s2e("base", "fea_pos", "QS 95", 20), s2e(rn, "fea_pos", "QS 95", 20)
    if not (b and r):
        return "–"
    t = ("%+.0f %%" % (100*(float(r["I_rms"])/float(b["I_rms"]) - 1))).replace("-", "−")
    if float(r["idfw"]) < -0.5:
        t += " (Δi<sub>d</sub> −%.0f A)" % abs(float(r["idfw"]))
    return t


rem_rows = "".join("<tr><td>%s</td>%s<td>%s</td></tr>" % (
    lab, "".join(ecell(s2e(rn, "fea_pos", tb, T, td), sat=True) for tb, T, td in REM_COLS), rem_cost(rn))
    for rn, lab in REM_NAMES)
rem_head = "".join("<th>여유 %d %%<br>%d N·m%s</th>" % (100 - int(tb.split()[1]), T, ", 3 µs" if td else "")
                   for tb, T, td in REM_COLS)


def need_margin_hb(vn, T, tol=5.0):
    for tb in QS_TABS:
        x = [h for h in HB if h["variant"] == vn and h["table"] == tb and h["T_ref"] == T and h["td_us"] == 0]
        if x and abs(100*(x[0]["T_shaft"]/T - 1)) <= tol:
            return "%d %%" % (100 - int(tb.split()[1]))
    return "30 % 초과"


def nm_txt(vn, T, td=0):
    m = need_margin(vn, T, td)
    return ("%d %%" % m) if m is not None else ("%d %%에서도 못 미침" % (100 - int(QS_TABS[-1].split()[1])))


def err(vn, tb, T, td=0):
    r = s2d(S2D + S2Q, vn, tb, T, td)
    return float(r["err_pct"]) if r else float("nan")


def pm(x, nd=0):
    """signed number with a true minus sign for prose"""
    t = ("%+." + str(nd) + "f") % x
    return t.replace("-", "−")


sec49 = f"""
<h3 id="j">4.9 종합 판단 — 직접 FEA 맵, 손실 규약, 슬롯 고조파, 정상상태 계산기 (09-23 밤)</h3>
<p>4.8절의 두 한계를 직접 FEA로 메웠다. Motor-CAD E-Magnetic의 포화맵 내보내기를 <b>FEA·회전자 위치별</b>(전기각 한 주기 120점)로 바꿔 16 krpm 운전 대역(i<sub>d</sub> −364…0 A 29점 × i<sub>q</sub> −13…52 A 첨두 6점 = 174점, 점당 36 s)을 새로 풀었다. 교류 동손은 Hybrid, 철손·자석손은 16 krpm 손실맵이다. 이 맵으로 ① Lab 보간을 검증하고 ② Simscape 모델(단계 2c)에 ψ<sub>d</sub>, ψ<sub>q</sub>(i<sub>d</sub>, i<sub>q</sub>, θ)를 넣어 슬롯 고조파를 포함시켰다. 축 토크와 저항은 PC2의 손실 귀속 규약(<a href="loss_torque_convention.html">손실의 토크 귀속 규약</a>)을 따른다. 제동 손실(기계손, 회전자 철손, 자석손, 무부하 고정자 철손, 무부하 교류 동손)은 토크에서 뺀다. 부하분 교류 동손은 입력측 손실이므로 직렬 저항 R<sub>ac,eff</sub> = (P<sub>ac</sub> − P<sub>ac,NL</sub>)/(1.5|i|²) ≈ 0.050 Ω로 넣었다(R 0.079 → 0.128 Ω). Motor-CAD E-Magnetic·Lab이 같은 손실을 실제로 어떻게 나누는지는 그 문서 4.1–4.3절에 정리했다.</p>
<div class="card"><b>이 절에 나오는 이름.</b>
<ul>
<li><b>기준표</b>: 토크 지령을 전류 지령 (i<sub>d</sub>*, i<sub>q</sub>*)로 바꾸는 표. 제어기가 이 표를 보고 전류를 지령한다. 표를 만들 때 필요 전압을 한계보다 얼마나 낮게 두었는지가 <b>전압 여유</b>다.
<ul>
<li><b>MCB</b>: MATLAB Motor Control Blockset(<code>mcb.generateMotorLUT</code>)으로 만든 표다. 전압 한계선 위에 놓여 여유가 0이다.</li>
<li><b>MBC 95·90</b>: Model-Based Calibration Toolbox(<code>calibratepmsm</code>)의 VsMax 95·90 % 표다. Lab 맵과 R<sub>dc</sub> 기준이라 이 절의 모델에서는 여유가 이름과 조금 다르다.</li>
<li><b>QS 95·90·85·80·75·70</b>: <b>QS는 quasi-static(준정적, 정상상태)의 약자</b>다. 과도 해석 없이 운전점마다 정상상태 방정식을 푸는 이 연구의 계산기 <code>qs_opsolver.py</code>로 만든 표다. 운전점마다 필요 전압 |R i + jω<sub>e</sub>ψ|을 한계 403.2 V의 95…70 %에 정확히 맞춘 최소 전류점이다(FEA 평균 맵 + 교류 저항 기준). 숫자는 한계 대비 백분율이고 <b>여유 = 100 − 숫자</b>다. 예를 들어 QS 95는 여유 5 %다.</li>
</ul></li>
<li><b>전동기 표 변형 A–D</b>(Simscape 모델에 넣는 전동기 데이터):
<ul>
<li>A: Lab 맵, 기존 축 토크</li>
<li>B: A + 손실 규약·교류 저항</li>
<li>C: B의 운전 대역을 직접 FEA 위치 평균으로</li>
<li><b>D: C를 회전자 위치별(슬롯 고조파 포함)로</b>. D<sub>ff</sub>는 D에서 디커플링을 기준 전류로 계산한 것이다.</li>
</ul></li>
<li><b>조화균형(HB) 계산</b>: 정상상태 계산기에 슬롯 고조파와 제어기 구조를 넣은 확장이다(4.9.6절).</li>
</ul></div>

<h3>4.9.1 Lab 보간은 운전 영역에서 맞다</h3>
{img("fea_lab_check.png", "그림 8. 직접 FEA(위치 평균) 대 Lab 보간, 16 krpm 운전 대역: (a) 전자기 토크 차이, (b) 필요 전압 |R i + jω<sub>e</sub>ψ| 차이, (c) 기준표 운전점의 진각 민감도")}
<div class="scroll"><table><tr><th>MCB 표 점</th><th>γ</th><th>ψ<sub>d</sub> FEA / Lab [mWb]</th><th>ψ<sub>q</sub> [mWb]</th><th>T<sub>em</sub> [N·m]</th><th>dT/dγ [N·m/°]</th><th>|R i + jω<sub>e</sub>ψ| [V 첨두]</th><th>Lab 내보내기 전압</th><th>토크 리플 p-p [N·m]</th></tr>{fea_rows}</table></div>
<p><b>Lab 48점 보간은 16 krpm 운전 영역에서 맞다.</b> 기준표 운전점에서 자속은 0.3–0.9 %, 전자기 토크는 0.8 %, dT/dγ는 0.06 N·m/°, 필요 전압은 0.4–0.7 % 안에서 같다(FEA 쪽이 1.3–2.6 V 낮다). 단계 0–3의 수치는 그대로 선다. 남는 불일치는 Motor-CAD 자신이 내놓는 전압이다. Lab 내보내기 전압(414–419 V)과 E-Magnetic 페이저 상전압(20 N·m에서 {EM["T20_hyb"]["PhasorRmsPhaseVoltage"]*2**0.5:.0f} V 첨두)은 같은 자속으로 계산한 |R i + jω<sub>e</sub>ψ|({o20["V_fea"]:.0f} V)보다 2–4 % 높다. 4.6절에서 본 차이가 이것이다. 부하분 교류 저항을 넣어도 {o20["V_fea_Rac"]:.0f} V라 다 설명되지 않는다. 원인은 아직 모른다.</p>

<h3>4.9.2 슬롯 고조파 — 평균 토크보다 큰 리플</h3>
{img("fea_harmonics.png", "그림 9. 회전자 위치별 FEA(16 krpm 기준표 운전점, 정현 전류): (a) 토크 파형, (b) 20 N·m점 dq 자속 고조파, (c) 토크 고조파")}
<ul>
<li>dq 자속에는 전기 6차와 12차가 있다. 20 N·m점에서 ψ<sub>q</sub>의 12차 진폭은 {1e3*o20["harmonics"]["psi_q"]["12"]:.1f} mWb로 평균 ψ<sub>q</sub>({1e3*o20["psi_q_fea"]:.1f} mWb)의 {100*o20["harmonics"]["psi_q"]["12"]/o20["psi_q_fea"]:.0f} %다. ψ<sub>d</sub>는 6·12차가 각 {1e3*o20["harmonics"]["psi_d"]["6"]:.1f}·{1e3*o20["harmonics"]["psi_d"]["12"]:.1f} mWb다. 16 krpm에서 6차는 6.4 kHz, 12차는 12.8 kHz다.</li>
<li>정현 전류일 때 토크 리플은 47–75 N·m p-p(Lab 계산 47–71)다. 5–20 N·m 운전점에서는 리플이 평균 토크보다 크다. 12차 진폭만 16–28 N·m다.</li>
<li>정현 전류를 억지로 흘리려면 상전압 첨두가 기본파의 3.2–3.6배(1.3–1.5 kV)여야 한다. 인버터는 그 전압을 낼 수 없으므로 실제 전류가 고조파를 품는다. 크기는 대략 Δi ≈ Δψ/L이다. 12차 ψ<sub>q</sub> 10 mWb를 L<sub>q</sub> 1.6 mH로 나누면 약 6 A다.</li>
<li><b>스큐:</b> 실제 e10 기계에는 스큐가 없다(사용자 확인, 09-24). 기준 모델도 스큐 없이 계산됐으므로(<code>SkewType = 0</code>) 아래 결론의 크기는 그대로다. 참고로 3단 스텝 스큐(±2.81° 기계각 = ±11.25° 전기각)를 넣으면 토크 12차는 (1 + 2 cos 135°)/3 ≈ −0.14배로 준다.</li>
</ul>

<h3>4.9.3 한 요인씩 — Simscape 단계 2d</h3>
<p>단계 2c의 Simscape 모델에서 전동기 표만 바꿔 넣었다(<code>run_e10_stage2d.m</code>, 모델 작업공간 변수 교체). 제어기·인버터·데드타임은 그대로다.</p>
{img("stage2d_variants.png", "그림 10. 단계 2d: 전동기 표를 A→D로 한 요인씩 바꾼 토크 오차(16 krpm, 데드타임 보상 없음, 회색 ±5 %)")}
<div class="scroll"><table><tr><th>전동기 표</th>{var_head}</tr>{var_rows}</table></div>
<ul>
<li><b>손실 규약(A→B).</b> 교류 동손 부하분을 직렬 저항으로 넣으면 그만큼 전압을 먹는다. 여유 0 표(MCB)에서는 20 N·m가 {pm(err("lab_rep", "MCB", 20), 1)} → {pm(err("lab_conv", "MCB", 20), 1)} %로 나빠지고 포화가 0 → 100 %가 된다. 5 % 여유 표(MBC 95)에서는 {pm(err("lab_rep", "MBC 95", 20), 1)} → {pm(err("lab_conv", "MBC 95", 20), 1)} %로 여유가 흡수한다. 교류 동손 모델은 고속 진각을 거의 바꾸지 않지만(Δγ ≤ 0.25°) 전압 여유는 먹는다.</li>
<li><b>직접 FEA 평균 맵(B→C).</b> 여유가 있는 표에서는 0.5 %p 안에서 같다(4.9.1과 같은 결론). 여유 0 표의 차이({pm(err("lab_conv", "MCB", 20), 1)} → {pm(err("fea_avg", "MCB", 20), 1)} %)는 한계선 위 운전점이 불량조건이라 생긴다.</li>
<li><b>슬롯 고조파(C→D).</b> 5 % 여유 표에서도 20 N·m가 {pm(err("fea_avg", "MBC 95", 20), 1)} → {pm(err("fea_pos", "MBC 95", 20), 0)} %, 60 N·m가 {pm(err("fea_avg", "MBC 95", 60), 1)} → {pm(err("fea_pos", "MBC 95", 60), 0)} %다(데드타임 0). 10 % 여유(MBC 90)에서도 {pm(err("fea_pos", "MBC 90", 20), 0)} %, {pm(err("fea_pos", "MBC 90", 60), 0)} %다. 전압 포화는 전체 샘플의 47–81 %에서 걸린다. 다른 어떤 요인보다 크다.</li>
</ul>

<h3>4.9.4 고조파는 평균 토크를 깎지 않고 운전점을 옮긴다</h3>
<div class="scroll"><table><tr><th>표</th><th>지령</th><th>표의 여유</th><th>기준 γ</th><th>실현 γ C → D</th><th>D 포화</th><th>D 토크 / 평균 맵 토크(D 실현점)</th><th>D 실현점에 남은 여유 m<sub>eq</sub></th><th>고정 여유 예측 (MBC 95 D로 교정)</th></tr>{res_rows}</table></div>
<p><b>같은 전류에서 평균 토크는 그대로다.</b> D의 평균 토크는 D가 실제로 도달한 평균 (I, γ)에서 평균 맵이 주는 토크와 {res_max:.1f} N·m 안에서 같다(데드타임 3 µs 포함 {res_max3:.1f} N·m). 고조파가 바꾸는 것은 <b>제어기가 도달하는 운전점</b>이다. 전류 크기는 그대로 두고 진각만 {min(dg_d):.1f}–{max(dg_d):.1f}° 커진다(여유 있는 표, C 대비). 20 N·m에서 dT/dγ ≈ −11 N·m/°이므로 1°면 −11 N·m다.</p>
<p><b>기구: 클램프에서 잘린 고조파 명령이 평균 전류 오차가 된다.</b> 고조파 전류의 주파수는 전류 제어 대역(1.6 kHz)보다 높다. 6차는 6.4 kHz이고, 12차 12.8 kHz는 20 kHz 샘플링에서 7.2 kHz로 접힌다. 그래도 PI의 비례 이득(K<sub>p,d</sub> 8.5 Ω, K<sub>p,q</sub> 16 Ω)과 측정 전류 디커플링(ω<sub>e</sub>L<sub>q</sub> 10.7 Ω, ω<sub>e</sub>L<sub>d</sub> 5.7 Ω)을 그대로 통과한다. 고조파 전류가 6 A면 명령 전압에 약 100 V의 고조파가 실린다. 명령 크기가 403 V 클램프를 넘는 순간마다 잘리고, 역산 안티와인드업(K<sub>aw</sub> = R/L<sub>d</sub>)이 잘린 몫을 적분기에 되먹인다. 정상상태에서는 적분기 입력의 평균이 0이어야 하므로</p>
<div class="eq">K<sub>i</sub>·mean(e) + K<sub>aw</sub>·mean(v<sub>clamp</sub> − v<sub>cmd</sub>) = 0 &nbsp;⇒&nbsp; mean(e) = (K<sub>aw</sub>/K<sub>i</sub>)·mean(v<sub>cmd</sub> − v<sub>clamp</sub>) = mean(v<sub>cmd</sub> − v<sub>clamp</sub>) / 8.5 Ω &nbsp; (K<sub>i,d</sub> = K<sub>p,d</sub>R/L<sub>d</sub>, K<sub>i,q</sub> = K<sub>p,q</sub>R/L<sub>q</sub>, 두 축 모두 8.5 Ω)</div>
<p>즉 평균 클리핑 결손 20 V가 약 2.4 A의 정상 전류 오차가 된다. 20 N·m 기준 i<sub>q</sub>* 6.8 A의 1/3이다. 이 식으로 세 결과가 설명된다. ① <b>기준 전류 디커플링</b>(D<sub>ff</sub>)은 고조파 명령의 한 경로를 끊어 피해를 약 1/3 줄인다: MBC 95 20 N·m {pm(err("fea_pos", "MBC 95", 20), 0)} → {pm(err("fea_pos_ff", "MBC 95", 20), 0)} %, MBC 90 {pm(err("fea_pos", "MBC 90", 20), 0)} → {pm(err("fea_pos_ff", "MBC 90", 20), 0)} %. ② 여유가 커지면 잘리는 시간이 줄어 오차가 준다. ③ 필요한 여유는 고정된 전압량이 아니다. D 실현점에 남은 평균 여유 m<sub>eq</sub>는 20 N·m에서 {m20["MCB"]:.1f} / {m20["MBC 95"]:.1f} / {m20["MBC 90"]:.1f} %(MCB / MBC 95 / MBC 90)로 표의 여유와 함께 커진다. 그래서 MBC 95의 D에서 교정한 고정 여유를 정상상태 계산기에 넣으면 MBC 90은 기준점으로 돌아온다고 예측하지만({p90["T_pred"]:.1f} N·m), Simscape는 {p90["T_sim"]:.1f} N·m다. 고조파의 피해는 전동기의 정상상태 성질이 아니라 제어기와 고조파 전류의 상호작용이다. 그래서 제어기 구조를 함께 넣으면 정상상태로 계산할 수 있다(4.9.6절).</p>
<p class="mut">PI 이득을 1/10로 낮춘 실험(<code>_slow</code>)은 0.4 s 안에 수렴하지 않아 결론에 쓰지 않았다. 과변조(육각형 한계까지)를 허용하면 명령 봉우리 일부를 낼 수 있지만 이 모델은 원형 클램프(선형 한계의 0.97)만 쓴다.</p>

<h3>4.9.5 고조파를 견디는 데 필요한 여유</h3>
<p>MBC 표는 Lab 맵과 R<sub>dc</sub>로 만들어서, 2d 모델(FEA 맵 + R<sub>ac</sub>)에서의 실제 여유가 이름과 조금 다르다(MBC 95는 20 N·m에서 {100*hmget("fea_avg", "MBC 95", 20)["m_table"]:.1f} %). 그래서 정상상태 계산기로 같은 모델에서 전압을 정확히 V<sub>clamp</sub>(1 − m)에 둔 최소 전류 표(QS 표)를 만들어 여유만 바꿔 돌렸다.</p>
{img("stage2d_margin.png", "그림 11. 기준표 전압 여유별 토크 오차: 속 찬 점은 QS 표(여유 정확히 5–30 %), 빈 점은 MCB·MBC 95·MBC 90 표. C는 고조파 없음, D는 위치별 맵, D<sub>ff</sub>는 D + 기준 전류 디커플링")}
<div class="scroll"><table><tr><th>전동기 표</th><th>지령</th>{margin_head}</tr>{margin_rows}</table></div>
<p>{{MARGIN_SUMMARY}}</p>
<p><b>여유의 값은 전류와 손실로 치른다.</b> QS 표 점의 16 krpm 전체 손실(직접 FEA 대역 손실맵, 여유 5 % 대비):</p>
<div class="scroll"><table><tr><th>여유</th><th>5 N·m</th><th>20 N·m</th><th>60 N·m</th></tr>{cost_rows}</table></div>

<h3>4.9.6 정상상태 계산기의 자리</h3>
{img("qs_vs_td.png", "그림 12. 정상상태 운전점 계산기(유효 전압한계) 대 시간영역 스위칭 모델 — Lab 맵, MCB 기준표, 교류 저항 제외")}
<p><code>qs_opsolver.py</code>는 시간영역 없이 운전점을 찾는다. 유효 전압한계 |v<sub>ss</sub> + Δv<sub>dt</sub>| ≤ V<sub>clamp</sub>(1 − m)에서 v<sub>ss</sub> = (R<sub>dc</sub> + R<sub>ac,eff</sub>) i + jω<sub>e</sub>ψ(i), Δv<sub>dt</sub> = (4/π)V<sub>dc</sub>t<sub>d</sub>f<sub>pwm</sub>·i/|i|로 둔다. 평균 맵 모델(스크립트·Simscape A–C)의 실현점을 데드타임 0에서는 진각 0.02° 안에서, 보상 없는 3 µs에서는 0.1–0.5° 안에서 재현한다. 기준표 생성에도 쓴다(QS 표). <span class="mut">09-23 밤 수정: 최소 전류점 탐색을 진각 격자에서 (i<sub>d</sub>, i<sub>q</sub>) 격자로 바꿨다. 90° 근처에서는 작은 토크를 내는 전류가 0.01°마다 수십 A씩 변해 진각 격자가 해를 놓쳤다. 기존 결과는 전류 0.5–3 A, 진각 0.01° 이내로 바뀌었다.</span></p>
<p><b>슬롯 고조파는 고정 여유로는 옮겨지지 않지만, 제어기 구조를 넣은 조화균형으로는 정상상태에서 계산된다</b>(<code>qs_harmonic_hb.py</code>, 09-24 추가). 계산은 네 단계다.</p>
<ol>
<li><b>고조파 전류.</b> 인버터가 기본파만 내면 정상상태에서 dq 자속은 평균에 머물고, 고조파는 전류가 떠안는다. ψ(i<sub>0</sub> + Δi(x), x) = ψ̄(i<sub>0</sub>)이므로 Δi(x) ≈ −L<sub>inc</sub><sup>−1</sup>[ψ(i<sub>0</sub>, x) − ψ̄(i<sub>0</sub>)]다(위치별 FEA 맵, x는 회전자 위치).</li>
<li><b>제어기의 반응.</b> 조절기는 Δi를 20 kHz로 샘플해 비례 경로와 디커플링으로 명령 리플 Δv = (−K<sub>p</sub> + D)Δi를 만들고, 한 샘플 뒤에 가한다. 이 리플이 다시 고조파 전류를 바꾼다. 지연 때문에 6.4 kHz에서는 거의 반대 위상으로 되먹이고, 12차 12.8 kHz는 7.2 kHz로 접힌다. 이 루프는 작은 선형 주기 모델(샘플 75개 = 전기 4주기)을 정상상태까지 돌려 샘플 시점의 Δi로 구한다.</li>
<li><b>클램프 평균.</b> 명령 v = V̄ + Δv가 |v| ≤ V<sub>max</sub>에서 잘린다. 잘린 몫의 평균 δ(V̄) = mean[v − clamp(v)]를 전기 한 주기에 대해 구한다. 편향과 주기 신호가 함께 들어간 포화 소자의 직류 출력으로, 이중 입력 기술함수와 같은 발상이다.</li>
<li><b>평형.</b> 역산 안티와인드업 적분기의 평균 입력이 0이어야 하므로 i* − i<sub>0</sub> = (K<sub>aw</sub>/K<sub>i</sub>)·δ다. 플랜트 평균에서는 V̄ − δ = R i<sub>0</sub> + jω<sub>e</sub>ψ̄(i<sub>0</sub>) + Δv<sub>dt</sub>(i<sub>0</sub>)다. 미지수는 V̄와 i<sub>0</sub>의 네 성분이고 식도 넷이다.</li>
</ol>
{img("qs_hb_vs_simscape.png", "그림 13. 조화균형 계산 대 Simscape 단계 2d: (a) 모든 경우의 실현 축 토크, (b)–(d) QS 표 여유별 토크 오차(점 Simscape, 선 계산; 실선 기본 제어기, 점선 기준 전류 디커플링)")}
<p><b>Simscape를 재현한다.</b> 여유를 둔 QS 표의 고조파 {len(hb_qs)}건에서 토크 RMS 오차 {hb_rms:.1f} N·m, 진각 RMS 오차 {hb_rmsg:.2f}°이고, 계산은 경우당 약 0.4 s다(Simscape 약 15 s). 2단계(제어기의 반응)를 빼면 기본 제어기의 20 N·m가 0.4–1.3 N·m 낙관적으로 나왔다. 측정 전류 디커플링 경로가 지연 때문에 고조파 전류를 키우기 때문이다. 크게 어긋나는 곳은 여유 0 MCB 표의 5 N·m처럼 90°를 넘어 역토크로 무너진 점뿐이다(Simscape {pm(hb_mcb5["sim_T"], 0).lstrip("+")} N·m, 계산 {pm(hb_mcb5["T_shaft"], 0).lstrip("+")} N·m). 이 점은 불량조건이라 방향만 맞고 크기는 틀린다. 필요한 여유도 계산기로 찾을 수 있다. ±5 % 기준으로 20 N·m는 D {need_margin_hb("fea_pos", 20)}, D<sub>ff</sub> {need_margin_hb("fea_pos_ff", 20)}, 60 N·m는 D {need_margin_hb("fea_pos", 60)}, 5 N·m는 D {need_margin_hb("fea_pos", 5)}다(Simscape: 25 %, 20 %, 15 %, 30 %).</p>
<p class="mut">한계: 제어기 구조(비례 이득, 디커플링 방식, 지연, 원형 클램프, 역산 안티와인드업)를 계산기에 그대로 적어 넣어야 한다. 노치·공진 제어기나 과변조처럼 다른 구조는 그 구조를 새로 넣어야 한다. PWM 측대파와 데드타임 고조파는 넣지 않았다. 입력인 위치별 맵은 스큐 없는 실제 기계와 같은 조건이다(4.9.2절).</p>
<p>실무 순서는 이렇게 바뀐다. ① 계산기로 여유 m의 표를 만든다. ② 조화균형 확장으로 그 여유에서 슬롯 고조파 오차를 보고 필요한 여유를 고른다. ③ 최종 후보만 위치별 맵 시간영역 모델(D)로 확인한다.</p>

<h3>4.9.7 요인별 정리 (16 krpm)</h3>
<div class="scroll"><table><tr><th>요인</th><th>기구</th><th>20 N·m 오차: 여유 0 / 5 %</th><th>여유로 흡수?</th><th>대책</th></tr>
<tr><td>데드타임 3 µs</td><td>기본파 27.5 V가 전류 반대 방향으로 빠짐</td><td class="bad">−43 % / −6 %</td><td>5 %면 대부분</td><td>보상 + 여유(5 % + 보상이면 −2 %)</td></tr>
<tr><td>입력측 교류 동손</td><td>R<sub>ac,eff</sub> 0.050 Ω의 전압 강하</td><td class="warn">{pm(err("lab_conv", "MCB", 20), 1)} % / {pm(err("lab_conv", "MBC 95", 20), 1)} %</td><td>예</td><td>표 생성 때 R에 넣기</td></tr>
<tr><td>Lab 48점 보간</td><td>직접 FEA 대비 오차</td><td class="ok">1 % 이하</td><td>—</td><td>불필요</td></tr>
<tr><td>슬롯 고조파</td><td>제어기가 고조파 전류에 반응 → 클램프에서 잘림 → 평균 전류 오차</td><td class="bad">{pm(err("fea_pos", "MCB", 20), 0)} % / {pm(err("fea_pos", "MBC 95", 20), 0)} %</td><td>큰 여유에서만 ({nm_txt("fea_pos", 20)})</td><td><b>피드백의 6·12차 노치로 해결</b>(여유 5 %로 복귀, 비용 없음, 4.9.8절)</td></tr>
<tr><td>레졸버 오프셋 1°</td><td>각도 오차</td><td class="bad">−57 % / 미시험</td><td>아니오 (각도 오차는 전압과 무관)</td><td>오프셋 교정</td></tr></table></div>
{BOX49}

<h3 id="rem">4.9.8 대책 시험 — 노치, 공진 제어기, 과변조, 전압 피드백 약자속 (단계 2e, 09-24)</h3>
<p>단계 2c 모델을 복사한 <code>e10_stage2e.slx</code>의 제어기에 네 대책을 선택지로 넣고(<code>build_e10_stage2e.m</code>, 모두 끄면 2d와 같은 결과), 위치별 맵(D)·기본 제어기로 여유 5 %·15 % QS 표에서 돌렸다.</p>
<ul>
<li><b>③ 노치:</b> 측정 dq 전류에서 6차(6.4 kHz)와 20 kHz 샘플에서 접힌 12차(7.2 kHz)를 2차 노치(극 반지름 0.9)로 뺀다. PI 오차와 디커플링 모두 거른 전류를 쓴다. 1.6 kHz 전류 루프에 주는 위상 지연은 −4°다. 고조파 전류는 흐르게 두고 조절기만 못 보게 하는 방식이다.</li>
<li><b>③ 6차 공진(PR):</b> 반대로 6차 전류를 억누른다. 위상 보상 π/2 + 1.5ω<sub>0</sub>T<sub>s</sub>(지연 1.5샘플), K<sub>r</sub> 150 Ω, 앞 샘플이 잘렸으면 공진기 입력 0(조건부 적분).</li>
<li><b>④ 과변조:</b> 원형 클램프 대신 육각형 한계(0.97 × V<sub>dc</sub>/√3 / cos(mod(φ, 60°) − 30°), 방향 유지). 꼭짓점 쪽에서 봉우리를 최대 466 V까지 낸다.</li>
<li><b>⑤ 전압 피드백 약자속:</b> 명령이 한계를 넘은 만큼 i<sub>d</sub>*를 더 깊게 한다. Δi<sub>d</sub> ← Δi<sub>d</sub> + T<sub>s</sub>[−K<sub>fw</sub>(|v| − V<sub>lim</sub>)<sup>+</sup> − K<sub>leak</sub>Δi<sub>d</sub>], K<sub>fw</sub> 200 A/(V·s), K<sub>leak</sub> 2 s<sup>−1</sup>.</li>
</ul>
<p><b>대책이 무엇이고 어떻게 넣나.</b> 4.9.4절의 사슬은 고조파 전류 → 조절기가 명령 리플로 바꿈 → 클램프에서 잘림 → 안티와인드업이 평균 오차로 바꿈이다. 대책은 이 사슬의 어느 고리를 끊느냐로 나뉜다. ②·③노치는 둘째 고리(명령 리플)를, ④는 셋째 고리(잘림)를 줄인다. ⑤는 틈을 키워 잘림을 피한다. ③PR은 첫째 고리(고조파 전류)를 없애려 하지만, 그러려면 고조파 전압이 필요하다.</p>
<div class="scroll"><table><tr><th>대책</th><th>무엇을 하나</th><th>제어기 어디에</th><th>넣는 법 (이 시험의 값)</th><th>주의</th></tr>
<tr><td>② 기준 전류 디커플링</td><td>디커플링 전향 항 −ω<sub>e</sub>L<sub>q</sub>i<sub>q</sub>, ω<sub>e</sub>(L<sub>d</sub>i<sub>d</sub> + λ<sub>m</sub>)을 측정 전류 대신 기준 전류로 계산한다. 고조파 전류가 ω<sub>e</sub>L(최대 10.7 Ω)로 증폭돼 명령에 실리는 경로를 끊는다.</td><td>PI 출력에 더하는 전향 항</td><td>i<sub>df</sub> = i<sub>d</sub>*, i<sub>qf</sub> = i<sub>q</sub>* (<code>P.ffRef = 1</code>)</td><td>비례 경로(K<sub>p</sub>)의 리플은 남아 피해가 약 1/3만 준다. 과도 중에는 디커플링이 덜 정확하다.</td></tr>
<tr><td>③ 노치</td><td>측정 전류에서 슬롯 고조파 주파수만 깎는다. 조절기는 고조파 전류를 보지 못하고, 전류에는 고조파가 그대로 흐른다(억누르지 않음).</td><td>전류 측정·dq 변환 직후, PI와 디커플링 앞</td><td>d·q 축마다 2차 노치 두 개를 직렬로 둔다. H(z) = g(1 − 2cos w<sub>0</sub> z<sup>−1</sup> + z<sup>−2</sup>)/(1 − 2r cos w<sub>0</sub> z<sup>−1</sup> + r<sup>2</sup>z<sup>−2</sup>)이고 g는 직류 이득을 1로 맞춘다. w<sub>1</sub> = 6ω<sub>e</sub>T<sub>s</sub>, w<sub>2</sub>는 12ω<sub>e</sub>T<sub>s</sub>를 [0, π]로 접은 값이다(16 krpm에서 6.4 kHz와 7.2 kHz). r = 0.9.</td><td>w는 속도에 따라 매 샘플 다시 계산한다. 고조파가 전류 루프 대역에 가까운 저속에서는 끈다(시험하지 않음). 차수는 기계마다 위치별 FEA로 확인한다(이 기계는 dq 6·12차).</td></tr>
<tr><td>③ 공진(PR)</td><td>특정 주파수에 무한 이득을 두어 그 고조파 전류를 0으로 만든다.</td><td>PI와 병렬</td><td>y[n] = 2cos w<sub>0</sub>·y[n−1] − y[n−2] + 2K<sub>r</sub>T<sub>s</sub>[cos φ·e[n] − cos(w<sub>0</sub> − φ)·e[n−1]]. φ = π/2 + 1.5w<sub>0</sub>(지연 1.5샘플 보상), K<sub>r</sub> = 150 Ω. 앞 샘플이 잘렸으면 입력을 0으로 둔다.</td><td>억누르는 데 필요한 고조파 전압(수백 V)이 남은 전압보다 커서 고속에서는 역효과다. 전압이 남는 저·중속의 토크 리플 저감용이다.</td></tr>
<tr><td>④ 과변조</td><td>원(선형 한계) 대신 인버터가 실제로 낼 수 있는 육각형까지 명령을 허용한다.</td><td>전압 한계(클램프)</td><td>한계 = k·V<sub>dc</sub>/√3 / cos(mod(φ, 60°) − 30°). φ는 정지 좌표계의 전압각(회전자각 + 지연 보상각 + ∠v)이고 k = 0.97이다. 방향은 유지하고 크기만 자른다.</td><td>평균 명령이 원을 넘으면 저차(5·7차) 전압 고조파가 생긴다. 리플 봉우리가 육각형보다 크면 효과가 작다.</td></tr>
<tr><td>⑤ 전압 피드백 약자속</td><td>명령이 한계를 넘는 만큼 i<sub>d</sub>*를 더 음으로 옮겨 필요 전압을 스스로 낮춘다. 여유를 자동으로 잡는 셈이다.</td><td>기준표 출력의 i<sub>d</sub>*에 더함</td><td>Δi<sub>d</sub> ← min(0, Δi<sub>d</sub> + T<sub>s</sub>[−K<sub>fw</sub>(|v| − V<sub>lim</sub>)<sup>+</sup> − K<sub>leak</sub>Δi<sub>d</sub>]), K<sub>fw</sub> = 200 A/(V·s), K<sub>leak</sub> = 2 s<sup>−1</sup></td><td>여유를 전류로 치른다. 누설이 느리면 과도 뒤 i<sub>d</sub>가 깊게 남고, 빠르면 잘림이 남는다. 루프 대역은 전류 루프보다 한참 낮게 둔다. Kwon·Sul(2006)의 안티와인드업 약자속과 같은 계열이다.</td></tr>
</table></div>
<p class="mut">제어기 코드(MATLAB Function 발췌)와 실제 드라이브에 옮기는 절차는 <a href="drive_model_study.html#remedy">모델 해설 14.2절</a>에 있다.</p>
{img("stage2e_remedies.png", "그림 14. 슬롯 고조파 대책 시험(Simscape 단계 2e, 위치별 맵, 16 krpm): 여유 5 %·15 % 표의 토크 오차(막대 Simscape, 흰 마름모 조화균형 계산), 여유 5 % 표의 정확도 대 손실")}
<div class="scroll"><table><tr><th>대책</th>{rem_head}<th>전류 (여유 5 %, 20 N·m)</th></tr>{rem_rows}</table></div>
<ul>
<li><b>노치가 문제를 없앤다.</b> 여유 5 % 표에서 5/20/60 N·m 오차가 {pm(float(s2e("notch", "fea_pos", "QS 95", 5)["err_pct"]), 1)} / {pm(float(s2e("notch", "fea_pos", "QS 95", 20)["err_pct"]), 1)} / {pm(float(s2e("notch", "fea_pos", "QS 95", 60)["err_pct"]), 1)} %이고 클램프에 걸린 샘플은 0 %다. 고조파 없는 맵(C)의 −2.3 / −1.3 / −1.4 %와 같다. 전류·손실 비용은 없다. 고조파 없는 C에 노치를 넣어도 결과가 바뀌지 않는다(부작용 없음). 토크 리플은 그대로다({float(s2e("notch", "fea_pos", "QS 95", 20)["T_ripple_pp"]):.0f} N·m p-p). 고조파 전류를 억누르지 않고 흐르게 두기 때문이다. <b>이 제어기에 노치를 넣으면 필요한 여유는 평균 맵과 같은 5 %로 돌아온다.</b> 데드타임 3 µs 무보상일 때 {pm(float(s2e("notch", "fea_pos", "QS 95", 20, 3)["err_pct"]), 1)} %는 C와 같은 데드타임 몫이고 보상으로 줄어든다(4.4절).</li>
<li><b>억누르면 더 나빠진다.</b> 6차 공진 제어기는 여유 5 % 표에서 20 N·m를 {pm(float(s2e("base", "fea_pos", "QS 95", 20)["err_pct"]), 0)} → {pm(float(s2e("pr6", "fea_pos", "QS 95", 20)["err_pct"]), 0)} %로 악화시킨다. 7 A의 6차 전류를 없애려면 6차 전압이 d축 약 240 V, q축 약 450 V 필요한데, 남는 전압은 수십 V다. 여유 15 %에서만 조금 낫다({pm(float(s2e("base", "fea_pos", "QS 85", 20)["err_pct"]), 0)} → {pm(float(s2e("pr6", "fea_pos", "QS 85", 20)["err_pct"]), 0)} %). 고속에서 고조파 전류를 억누르는 방향은 맞지 않는다.</li>
<li><b>과변조는 일부만 돕는다.</b> 20 N·m {pm(float(s2e("base", "fea_pos", "QS 95", 20)["err_pct"]), 0)} → {pm(float(s2e("hex", "fea_pos", "QS 95", 20)["err_pct"]), 0)} %, 60 N·m {pm(float(s2e("base", "fea_pos", "QS 95", 60)["err_pct"]), 0)} → {pm(float(s2e("hex", "fea_pos", "QS 95", 60)["err_pct"]), 0)} %. 봉우리 일부는 육각형 꼭짓점 쪽에서 낼 수 있지만, 리플 봉우리(약 110 V)가 육각형이 더 주는 몫(0–62 V)보다 크다. 토크 리플은 거의 그대로다(20 N·m {float(s2e("hex", "fea_pos", "QS 95", 20)["T_ripple_pp"]):.0f} 대 {float(s2e("base", "fea_pos", "QS 95", 20)["T_ripple_pp"]):.0f} N·m p-p). 저차 전압 고조파가 얼마나 느는지는 측정하지 않았다.</li>
<li><b>약자속 루프는 토크를 맞추지만 비싸다.</b> 여유 5 % 표에서 오차 {pm(float(s2e("fw", "fea_pos", "QS 95", 5)["err_pct"]), 1)} / {pm(float(s2e("fw", "fea_pos", "QS 95", 20)["err_pct"]), 1)} / {pm(float(s2e("fw", "fea_pos", "QS 95", 60)["err_pct"]), 1)} %로 맞추지만, i<sub>d</sub>를 {abs(float(s2e("fw", "fea_pos", "QS 95", 20)["idfw"])):.0f} A(60 N·m {abs(float(s2e("fw", "fea_pos", "QS 95", 60)["idfw"])):.0f} A) 더 깊게 넣어 전류가 10–18 %, 손실이 18–31 % 는다. 토크 리플도 커진다(20 N·m {float(s2e("fw", "fea_pos", "QS 95", 20)["T_ripple_pp"]):.0f} N·m p-p). 결국 여유를 자동으로 잡는 셈이다. 누설이 느려 고조파 없는 C에서도 기동 과도 뒤 i<sub>d</sub>가 최대 {abs(float(s2e("fw", "fea_avg", "QS 95", 60)["idfw"])):.0f} A 더 깊게 남았다.</li>
<li><b>조화균형 계산이 결과를 미리 맞혔다.</b> 노치(오차 0), 과변조(20 N·m −39 % 대 Simscape −40 %), 약자속(5·20 N·m)을 맞혔다. 약자속 60 N·m만 계산이 수렴하지 않았다. 공진 제어기는 계산기에 넣지 않았다.</li>
</ul>
<p><b>정리:</b> 고속 저토크의 슬롯 고조파 문제는 전동기가 아니라 제어기 문제이고, 조절기가 고조파 전류를 못 보게 하는 노치로 풀린다. 노치 주파수는 속도에 따라 옮겨야 한다(6ω<sub>e</sub>와 샘플링에 접힌 12ω<sub>e</sub>). 이 시험은 16 krpm 한 속도에서만 했다.</p>
{files_box("이 결과의 파일 — 단계 2e (대책 시험)", [
    item(E10 / "build_e10_stage2e.m", "2c 모델을 복사해 제어기에 대책 선택지(P.notch, P.pr6, P.hex, P.fw) 추가"),
    item(DRV / "stage2e" / "e10_stage2e.slx", "대책 선택지가 든 Simscape 모델 — 제어기 'ctrl' 코드 확인"),
    item(E10 / "run_e10_stage2e.m", "대책 × 표 변형 × 기준표 × 토크 × 데드타임 (대책 조합은 'notch+fw')",
         cmd="addpath('%s'); R = run_e10_stage2e([20 0], 0.08, [], {{'fea_pos'}}, 'try.csv', {{'QS 95'}}, {{'base', 'notch'}});" % E10),
    item(DRV / "run_stage2e_a.m", "이 절의 실행 배치"),
    item(DRV / "stage2e_results_D.csv", "위치별 맵(D) 결과"),
    item(DRV / "stage2e_results_C.csv", "평균 맵(C)에서 부작용 확인"),
    item(E10 / "qs_harmonic_hb.py", "조화균형 계산의 대책 선택지 (python qs_harmonic_hb.py remedies)",
         cmd='python "%s" remedies' % (E10 / "qs_harmonic_hb.py")),
    item(FP / "qs_hb_remedies.json", "조화균형 계산의 대책 예측", cmd="")])}
"""

CSS = """
:root{--bg:#fbfaf7;--card:#fff;--fg:#1f2328;--mut:#5d6670;--line:#dcd7ce;--acc:#8a4b1f;--hl:#fff3e6;--ok:#1f7a45;--warn:#a86a12;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15171a;--card:#1d2024;--fg:#e8e5df;--mut:#a4abb2;--line:#383c42;--acc:#e0a36e;--hl:#2a2218;--ok:#6fd39a;--warn:#e3b25d;--bad:#f08a80}}
body{background:var(--bg);color:var(--fg);font:15px/1.7 system-ui,"Malgun Gothic","Apple SD Gothic Neo",sans-serif;margin:0}
main{max-width:1000px;margin:0 auto;padding:18px 16px 64px}
h1{font-size:23px;line-height:1.3;margin:6px 0}h2{font-size:19px;margin:34px 0 8px;padding-bottom:4px;border-bottom:2px solid var(--acc)}
h3{font-size:16px;margin:20px 0 6px}.mut{color:var(--mut)}
nav{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}nav a{border:1px solid var(--line);border-radius:999px;padding:3px 12px;color:var(--fg);text-decoration:none;font-size:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:12px 0}
.kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:10px;margin:14px 0}
.kpi div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px}.kpi b{display:block;font-size:20px;color:var(--acc)}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13.5px;margin:6px 0}
td,th{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left}th{color:var(--mut);font-weight:600}
td.ok{color:var(--ok)}td.warn{color:var(--warn)}td.bad{color:var(--bad);font-weight:600}
.eq{font-family:ui-monospace,Consolas,monospace;background:var(--hl);padding:8px 10px;border-radius:6px;overflow-x:auto;font-size:13.5px}
figure{margin:12px 0}img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px;background:#fff}
figcaption{font-size:13px;color:var(--mut)}code{font-size:13px;word-break:break-all}
""" + FILES_CSS

doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>고속 저토크 진각 벽</title><style>{CSS}</style></head><body><main>
<h1>고속 저토크에서 진각 80° 벽 — 현상, 이론, 재현, 결과</h1>
<p class="mut">대상: e10 구동모터 기준기(Motor-CAD Lab 포화맵), 16 krpm, 직류 720 V · 초판 2026-09-23, 같은 날 단계 2·2b·2c·3 추가, 밤에 직접 FEA 위치별 맵·손실 규약·슬롯 고조파(단계 2d)·정상상태 계산기로 종합 판단(4.9절) · PC1 · 근거: 2026-09-17~18 세션 b5dcb1f7(단계 0·1), 2026-09-23 세션(단계 2·3·2d)</p>
<p>모델이 어떻게 만들어졌는지(플랜트·제어기·PWM·데드타임·교정표·Simscape·FMU의 이론과 구현)는 <a href="drive_model_study.html"><b>구동 시뮬레이션 모델 해설</b></a>에 따로 정리했다. 결과마다 아래 <b>파일 상자</b>에서 모델·스크립트·데이터를 바로 열 수 있다. <span class="mut">{LINK_NOTE}</span></p>
<div class="kpi">
<div>16 krpm 역기전력<b>1042 V rms</b><span class="mut">상전압 한계 285.1 V rms의 3.7배</span></div>
<div>16 krpm에서 전압이 허락하는 진각<b>≥ 85–88°</b><span class="mut">토크가 낮을수록 더 높다 (Lab FMU)</span></div>
<div>데드타임 3 µs, 여유 0, 보상 없음<b>20 N·m → −43 %</b><span class="mut">스위칭 모델 (단계 2)</span></div>
<div>전압 여유 5 % 교정표<b>오차 −6 % 이내</b><span class="mut">평균 맵 기준. 대가: 손실 +1–3 % (단계 2b·3)</span></div>
<div>슬롯 고조파 포함(직접 FEA 위치별 맵)<b>20 N·m {pm(err("fea_pos", "MBC 95", 20), 0)} %</b><span class="mut">여유 5 % 표, 데드타임 0. 평균 토크가 아니라 제어기 운전점이 틀어진다. 피드백의 6·12차 노치로 해결 (4.9.8절)</span></div>
</div>
<nav><a href="#p">1 현상</a><a href="#t">2 발생 이론</a><a href="#m">3 재현 방법</a><a href="#r">4 결과 분석</a><a href="#j">4.9 종합 판단</a><a href="#rem">4.9.8 대책 시험</a><a href="#c">5 결론</a><a href="#f">6 모델·코드 경로</a></nav>

<div class="card"><b>초판 정정 (같은 날).</b> ① 초판은 16 krpm 상전압(rms)을 첨두값 한계 720/√3 = 415.7 V와 비교했다. 맞는 비교 대상은 rms 한계다 — 선형 SVPWM 상한 720/√6 = 293.9 V rms, Lab이 쓰는 값 285.1 V rms(첨두 403.2 V). 단계 1·2 모델은 처음부터 403.2 V 첨두를 썼으므로 계산 결과는 바뀌지 않고 1절 해석만 바뀐다: 16 krpm에서 필요한 진각은 “83–85° 이상”이 아니라 <b>저토크 88–89°, 60 N·m 86–87°, 최대 토크 약 85°</b>다. ② 단계 1의 “지연 2샘플이면 루프 붕괴”는 전압 지연을 회전 좌표계에서 준 모델의 인공물이었다. 정지 좌표계에서 전압을 유지하는 단계 2에서는 보상된 지연 0–2샘플의 차이가 1 % 이하다(4.3절). ③ 초판의 데드타임 보상식은 매 반주기 sign(i)·V<sub>dc</sub>t<sub>d</sub>/T<sub>s</sub>를 더했는데, 실제로 밀리는 에지는 캐리어 주기마다 한 번이라 <b>손실의 2배를 보상</b>했다. 에지가 밀리는 반주기에서만 보정하도록 고치자 여유 없는 표에서 보상 효과가 작아졌다(20 N·m, 3 µs: −5 % → −16 %). 결론 3(전압 여유가 핵심)은 오히려 강해진다. 같은 이유로 2.2절 데드타임 전압 크기를 43 V에서 21.6 V(평균)로 고쳤다. ④ 2.1절의 “특성전류점 i<sub>d</sub> ≈ −196 A”는 틀렸다. −191 A는 i<sub>q</sub> = 0에서 16 krpm 전압 타원의 오른쪽 끝이고, 특성전류점(λ<sub>d</sub> = 0)은 −273 A다.</div>

<h2 id="p">1. 현상</h2>
<p>현장에서는 “고속 저토크에서는 진각(전류 위상각, q축 기준)을 80° 이상 넣기 어렵다”고 한다. 반면 손실 최소화로 푼 e10의 16 krpm 설정점은
1 N·m에서 <b>89.7°</b>, 전 토크 구간 86.8–89.6°다. 둘이 어긋나 보이지만 <b>서로 다른 제약</b>을 말한다.
계산값은 이상적 정상상태에서의 손실 최적점이고, 현장의 80°는 인버터·제어기가 실제로 유지할 수 있는 각의 한계다.</p>
<div class="card"><b>이 기계에서는 오히려 85° 아래로 갈 수 없다.</b> 16 krpm, 전류·진각 지정(전압 한계 미적용) 격자의 상전압 [V rms]:
<div class="scroll"><table><tr><th>I \\ γ</th><th>60°</th><th>70°</th><th>75°</th><th>80°</th><th>85°</th><th>89°</th></tr>
<tr><td>138 A</td><td>1086</td><td>815</td><td>659</td><td><b>499</b></td><td>352</td><td>278</td></tr>
<tr><td>230 A</td><td>1316</td><td>1020</td><td>824</td><td><b>600</b></td><td>359</td><td>194</td></tr>
<tr><td>322 A</td><td>1498</td><td>1249</td><td>1077</td><td><b>879</b></td><td>681</td><td>573</td></tr></table></div>
상전압 한계는 285.1 V rms다(720 V, 선형 SVPWM 상한 293.9 V rms에서 여유). γ = 80°에서는 어떤 전류로도 한계를 맞출 수 없고, 85°도 138 A에서는 352 V로 넘는다. Lab FMU로 토크를 고정하고 진각을 강제한 스윕(4.5절)에서 전압을 만족하는 진각은 20 N·m에서 88.5–89°, 60 N·m에서 86–87°뿐이다. 80°에서 멈추라는 규칙을 그대로 쓰면 16 krpm 운전 자체가 불가능하다(과변조·6-스텝 전이, 제어를 놓치면 무제어 발전).</div>

<h2 id="t">2. 발생 이론 — 벽은 모터가 아니라 제어기 쪽에 있다</h2>
<h3>2.1 약자속 심부의 전압 방정식</h3>
<div class="eq">v<sub>d</sub> = R i<sub>d</sub> − ω<sub>e</sub> λ<sub>q</sub>(i<sub>d</sub>,i<sub>q</sub>), &nbsp; v<sub>q</sub> = R i<sub>q</sub> + ω<sub>e</sub> λ<sub>d</sub>(i<sub>d</sub>,i<sub>q</sub>), &nbsp; |v| ≤ 403.2 V 첨두 (285.1 V rms)
<br>i<sub>d</sub> = −I sin γ, i<sub>q</sub> = I cos γ &nbsp; (γ = 90°에서 순수 −d축 전류)</div>
<p>고속에서는 ω<sub>e</sub>λ<sub>m</sub>이 전압 한계를 크게 넘으므로, λ<sub>d</sub> = λ<sub>m</sub> + L<sub>d</sub>i<sub>d</sub>를 −d축 전류로 깎아야 한다.
토크가 작을수록 i<sub>q</sub>가 작아 전류 벡터는 −d축(γ → 90°)에 붙고, 운전점은 16 krpm 전압 한계 타원의 오른쪽 끝(i<sub>q</sub> = 0에서 i<sub>d</sub> ≈ −191 A pk, 전류가 가장 작은 쪽) 근처가 된다. 타원 중심인 특성전류점(λ<sub>d</sub> = 0)은 i<sub>d</sub> ≈ −273 A pk다(<a href="drive_model_study.html#region">해설 4절</a>).
이 영역에서 손실의 대부분은 토크와 무관한 약자속 전류(약 135 A rms)가 만든다 — 1 N·m에도 10 kW.</p>
<h3>2.2 왜 제어기는 그 각을 유지하기 어려운가</h3>
<div class="scroll"><table><tr><th>원인</th><th>기구</th><th>e10 16 krpm 크기</th></tr>
<tr><td>① 각도 민감도</td><td>저토크에서 T ≈ k·I cos γ의 기울기가 크다. 각도 오차가 곧 토크 오차가 되고, 90°를 넘으면 부호가 뒤집혀 제동한다.</td><td>dT/dγ = −10.4 N·m/° (138 A), −20.4 N·m/° (230 A) → 1 N·m 운전점에서 0.1° 오차가 토크 100 %</td></tr>
<tr><td>② 연산 지연</td><td>전류 샘플–PWM 갱신 사이 지연 동안 회전자가 돈다. 보상하지 않으면 전압 벡터가 그만큼 앞서거나 뒤진다.</td><td>전기 1066.7 Hz. 단일 갱신(100 µs) 1.5주기 = 전기각 58°; 양 끝 갱신(50 µs) 1샘플 + 유지 반샘플 = 29°</td></tr>
<tr><td>③ 전압 포화</td><td>약자속 심부에서 전류 PI 출력이 한계에 붙는다(와인드업). 실제 전류 벡터는 지령이 아니라 전압 제약이 정하고, 포화된 PI는 인버터 오차(데드타임)를 보정하지 못한다.</td><td>여유 0 기준표에서 데드타임 2 µs면 포화율 100 % (4.3절)</td></tr>
<tr><td>④ 데드타임</td><td>전류 부호에 따라 한 에지가 캐리어 주기마다 한 번 t<sub>d</sub>만큼 밀려(i &gt; 0이면 켜짐, i &lt; 0이면 꺼짐) 상전압 평균이 −sign(i)·V<sub>dc</sub>t<sub>d</sub>/T<sub>pwm</sub>만큼 바뀐다. 이 사각파 오차의 기본파는 전류 벡터 반대 방향이다. 깊은 약자속에서는 변조율이 한계에 붙어 있어 이 몫을 채울 전압이 없다.</td><td>t<sub>d</sub> = 3 µs, 10 kHz → 상 평균 21.6 V, 기본파 약 27.5 V (한계 403 V 첨두의 약 7 %). 20 N·m에서 진각이 0.7° 밀려 토크 −43 %</td></tr>
<tr><td>⑤ 파라미터 불확실성</td><td>레졸버 오프셋, 자석 온도에 따른 λ<sub>m</sub> 드리프트, 맵 오차. MTPV 경계에서 여유를 두고 리미터를 건다.</td><td>레졸버 오프셋 보정 오차 통상 1–2°</td></tr>
<tr><td>⑥ 열·효율</td><td>뜨거운 자석에 순수 −d축 전류를 계속 흘린다. 인버터 도통·스위칭 손실만 쌓인다.</td><td>1 N·m에 138 A: 직류 4.3 + 교류 2.8 + 철손 2.7 ≈ 10 kW, 역률 ≈ 0</td></tr></table></div>
<p><b>정리:</b> 아래쪽 벽은 전압(γ가 작으면 한계 초과), 위쪽 벽은 토크 정밀도(γ가 90°에 가까우면 오차가 제동으로 넘어감)다. 그 사이 폭은 각도 오차 예산과 교정표의 전압 여유가 정한다. “80°”라는 숫자는 기계 상수가 아니라 특정 인버터·센서·제어 구조에서의 경험값이다.</p>

<h2 id="m">3. 재현 방법</h2>
<div class="scroll"><table><tr><th>단계</th><th>모델</th><th>재현되는 원인</th><th>상태</th></tr>
<tr><td>0</td><td>(I, γ) 격자 위 각도 오차 몬테카를로 — Motor-CAD 추가 계산 없이 토크·전압 격자를 재샘플</td><td>①⑤ 오차 → 토크 산포·부호 반전·전압 초과</td><td>완료 (09-17)</td></tr>
<tr><td>1</td><td>평균값 dq Simulink (스위칭 없음, 이산 FOC, T<sub>s</sub> = 50 µs)</td><td>②③⑤ 지연, 전류 PI 포화, 레졸버 오프셋</td><td>완료 (09-18), 지연 결론은 단계 2로 대체</td></tr>
<tr><td>2</td><td>스위칭 모델 — 사건 구동 스크립트: 10 kHz 중앙정렬 삼각파, 양 끝 갱신(T<sub>s</sub> 50 µs), SVPWM(min-max 주입), 전류 부호 의존 데드타임 0–3 µs, 정지 좌표계 전압 유지, 같은 Lab 맵 플랜트(RK4)</td><td>②③④⑤, 상전류 리플·THD</td><td><b>완료 (09-23)</b></td></tr>
<tr><td>2b</td><td>단계 2에 교정표 교체: MCB 표(여유 0) 대 MBC <code>calibratepmsm</code> 표(VsMax 100/95/90 %)</td><td>교정 전압 여유 ↔ ③④ 내성</td><td><b>완료 (09-23)</b></td></tr>
<tr><td>2c</td><td>Simscape Electrical 교차 확인 — MathWorks HEV PMSM Drive Test Harness 개조(FEM-Parameterized PMSM dq0 변형에 Lab 맵, 이상 스위치 + 다이오드 인버터, 실제 게이트 블랭킹, 같은 제어기)</td><td>스크립트 스위칭 모델 검증</td><td><b>완료 (09-23)</b> — 토크 0.05–1.8 % 일치, 4.7절</td></tr>
<tr><td>3</td><td>Motor-CAD Lab BPM FMU (FMI 2.0 co-simulation, fmpy) — 모드 0(토크·속도, Lab 자체 최적) / 모드 2(전류·진각 강제)</td><td>진각별 손실(교류 동손 하이브리드 맵 포함)·전압, 스위칭 모델이 도달한 운전점의 손실 비용</td><td><b>완료 (09-23)</b></td></tr></table></div>
<h3>3.1 플랜트·제어기 (단계 1·2 공통)</h3>
<div class="eq">플랜트(연속): dλ<sub>d</sub>/dt = v<sub>d</sub> − R i<sub>d</sub> + ω<sub>e</sub>λ<sub>q</sub>, &nbsp; dλ<sub>q</sub>/dt = v<sub>q</sub> − R i<sub>q</sub> − ω<sub>e</sub>λ<sub>d</sub>
<br>(i<sub>d</sub>, i<sub>q</sub>) = 역맵(λ<sub>d</sub>, λ<sub>q</sub>) — Motor-CAD Lab 자속맵 2-D 룩업(포화·교차포화 포함), T<sub>축</sub> = 토크맵(i<sub>d</sub>, i<sub>q</sub>) (철손·자석손 토크 환산을 뺀 축 토크)
<br>제어기(이산): 토크 지령 → 기준표 i<sub>d</sub>*(T,ω), i<sub>q</sub>*(T,ω) → 전류 PI + 디커플링 + 안티와인드업 → |v| ≤ 403.2 V 제한 → 지연 보상 ω<sub>e</sub>(n+½)T<sub>s</sub> → n샘플 지연
<br>단계 2 전압 경로: dq → 제어기 각도로 αβ → SVPWM 듀티 → 폴 전압 ±V<sub>dc</sub>/2 (데드타임으로 밀린 스위칭 포함) → 기계 각도로 dq → 플랜트</div>
<ul>
<li><b>플랜트 데이터:</b> Motor-CAD Lab export(<code>export_lab_satmap.py</code>). Lab export는 iq ≥ 0 한 사분면뿐이라 λ<sub>d</sub> 우함수·λ<sub>q</sub>/토크 기함수로 대칭 확장했다.</li>
<li><b>기준표·이득:</b> MATLAB Motor Control Blockset <code>mcb.generateMotorLUT</code>(FluxDQ, 약자속 'vclmt')와 <code>mcb.getPIControllerParameters</code>. 이 표는 Lab 자체 궤적과 진각 0.4° 안에서 일치하고, <b>전압 한계선 위에 놓여 여유가 없다</b>(Lab FMU로 보면 표 점의 상전압이 285.1 V 한계보다 0–3 % 높다).</li>
<li><b>MBC 교정표:</b> Model-Based Calibration Toolbox <code>calibratepmsm</code>(MathWorks 예제 “Generate Current Controller Calibration Tables for Flux-Based Motor Controllers”). 교정 데이터는 Lab 맵을 2배 촘촘하게 보간해(6.5 A 격자) 2000/4000/8000/16000 rpm에서 V<sub>s</sub> = |R i + jω<sub>e</sub>λ|로 만들었다. 16 krpm 표는 VsMax에 정확히 붙으므로 VsMax 95 %는 5 % 전압 여유를 뜻한다. <b>단서:</b> 16 krpm에서 약 20 N·m 아래는 최적화가 수렴하지 않아(ExitFlag ≤ 0) 격자 표가 한계 2–4배 전압의 점으로 채워졌다 — 2b에서는 수렴한 해만 쓰고 저토크는 선형 외삽했다.</li>
<li><b>검증 앵커</b>: λ<sub>m</sub> 0.22 Vs(역기전력 1042 V rms), 1 N·m 손실 최적 89.70°·135.6 A, dT/dγ −10.4/−20.4 N·m/°, 16 krpm 최대 축 토크 87.8 N·m(Lab 88.0). 단계 2: 무데드타임에서 반주기 평균 인가 전압과 지령의 차 ~1e−10 V, T<sub>s</sub> → 0 수렴, Lab FMU로 되짚은 토크가 스위칭 모델 토크와 1–4 % 안에서 일치.</li>
</ul>

<h2 id="r">4. 결과 분석</h2>
<h3>4.1 단계 0 — 운전창이 양쪽에서 조여온다</h3>
{img("gamma_wall_mc.png", "그림 1. 각도 오차 몬테카를로(16 krpm, 135 A rms, 2만 시행; 오프셋 ±1.5° 균일 + 지연 잔차 σ 2° + 자속 드리프트): 지령 진각별 토크 산포, 부호 반전 확률, 전압 한계 초과 확률")}
<div class="scroll"><table><tr><th>γ 지령</th><th>무오차 토크</th><th>토크 산포</th><th>부호 반전</th><th>전압 초과</th></tr>
<tr><td>80°</td><td>101.3 N·m</td><td>±21 %</td><td>0 %</td><td class="bad">92.6 %</td></tr>
<tr><td>84°</td><td>61.0</td><td>±37 %</td><td>0.4 %</td><td class="warn">35.0 %</td></tr>
<tr><td>86°</td><td>40.3</td><td>±57 %</td><td>4.0 %</td><td>9.8 %</td></tr>
<tr><td>88°</td><td>19.1</td><td>±117 %</td><td class="warn">20.0 %</td><td>1.5 %</td></tr>
<tr><td>89.7° (손실 최적)</td><td>1.1</td><td>±1376 %</td><td class="bad">48.3 %</td><td>0.1 %</td></tr></table></div>
<p>보통 수준의 오차에서 실용 운전창은 <b>84–87°</b>다. <b>벽의 위치는 계측·지연 예산의 함수</b>다.</p>
{BOX0}

<h3>4.2 단계 1 — 평균값 모델 (09-18)</h3>
{img("stage1_offset_delay.png", "그림 2. 단계 1 폐루프(16 krpm): (a) 레졸버 오프셋 × 연산 지연별 토크 오차, (b) 전압 포화율, (c) 폐루프 상한")}
<div class="scroll"><table><tr><th>토크 지령</th><th>레졸버 오프셋</th><th>지연 0 샘플</th><th>1 샘플</th><th>2 샘플</th></tr>{od}</table></div>
<p>오프셋 결론(1°에서 20 N·m −57 %, 60 N·m −25 %)은 단계 2에서 그대로 재현됐다. 지연 열(2샘플 붕괴)은 인공물이다 — 아래 4.3, 원리는 <a href="drive_model_study.html#delay">해설 6절</a>.</p>
{BOX1}

<h3>4.3 단계 2 — 스위칭 인버터와 데드타임</h3>
{img("stage2_summary.png", "그림 3. 단계 2 스위칭 모델(16 krpm, 10 kHz SVPWM 양 끝 갱신, MCB 기준표): (a) 데드타임별 실현 토크와 보상, (b) 레졸버 오프셋 × 보상된 연산 지연, (c) 폐루프 상한과 실현 진각, (d) 지연 보상 on/off")}
<div class="scroll"><table><tr><th>토크 지령</th><th>t<sub>d</sub> 0</th><th>1 µs</th><th>2 µs</th><th>3 µs</th><th>2 µs + 보상</th><th>3 µs + 보상</th></tr>{dt_rows}</table></div>
<ul>
<li><b>데드타임은 여유 없는 약자속에서 토크를 깎는다.</b> 보상 없이 2 µs면 20 N·m −25 %, 3 µs면 −43 %; 60 N·m은 −10/−16 %. 전류 PI가 전압 한계에 붙어(포화 100 %) 잃어버린 전압을 되찾지 못하기 때문이다. 오차의 상대 크기는 토크가 낮을수록(진각이 90°에 가까울수록) 크다.</li>
<li><b>데드타임 보상은 여유가 없으면 반만 듣는다.</b> 에지가 밀리는 반주기에서만 듀티를 t<sub>d</sub>/T<sub>s</sub> 보정하면(주기 평균 sign(i)·V<sub>dc</sub>t<sub>d</sub>/T<sub>pwm</sub>) t<sub>d</sub> 2 µs에서는 20 N·m −25 → −5 %, 60 N·m −10 → −3 %로 대부분 돌아온다. 3 µs에서는 20 N·m −43 → −16 %, 60 N·m −16 → −5 %에 그치고 전압 포화가 81–89 % 남는다. 5 N·m은 보상해도 실패한다(−240 %). 원인 후보는 샘플 전류 부호가 영교차 부근에서 틀리는 몫(샘플당 전기각 19°)과 한계선 위 운전점의 불량조건인데, 둘은 아직 분리하지 않았다.</li>
<li><b>5 N·m은 이상 인버터(t<sub>d</sub> 0)에서도 실패한다</b>(−4.3 N·m, 포화 100 %). MCB 표가 전압 한계선 위에 있어 리플만으로도 포화된다 — 여유 문제이며 4.4절에서 풀린다.</li>
<li><b>보상된 지연은 무해하다.</b> td 2 µs에서 지연 0/1/2샘플의 토크 차이는 1 % 이하. 단계 1의 붕괴는 전압을 회전 좌표계에서 지연시킨 탓이다(회전자가 도는 동안 전압 벡터도 같이 돌아가 버려 지연이 사라지지 않는다). 대신 <b>지연 보상을 끄면</b> 1샘플만으로 20 N·m가 −610 %(역토크)로 붕괴한다.</li>
<li><b>레졸버 오프셋은 인버터와 무관하게 지배적이다.</b></li>
</ul>
<div class="scroll"><table><tr><th>토크 지령</th><th>오프셋</th><th>지연 0 (보상)</th><th>1</th><th>2</th></tr>{od2}</table></div>
<p><b>폐루프 상한과 실현 진각</b>(MCB 표, 지연 1샘플 보상):</p>
<div class="scroll"><table><tr><th>지령</th><th>실현 T (t<sub>d</sub> 0)</th><th>γ</th><th>I rms</th><th>실현 T (t<sub>d</sub> 2 µs)</th><th>γ</th></tr>{ceil_rows}</table></div>
<p>16 krpm에서 실현 진각은 한 번도 84.7° 아래로 내려가지 않는다. 지령을 100 N·m까지 올려도 토크는 87(t<sub>d</sub> 0)·83 N·m(2 µs)에서 멈추고 γ는 84.7–84.9°에 머문다 — 전류(194 A)는 한계 460 A의 절반도 안 되는데 전압이 막는다. 상전류 THD는 10 kHz(전기 한 주기에 캐리어 9.4주기)에서 {thd_txt}로 데드타임의 영향이 작다(그림 4) — 이 운전점에서 데드타임은 파형이 아니라 기본파 크기를 깎는다.</p>
{img("stage2_currents.png", "그림 4. 단계 2 상전류(마지막 전기 2주기), t<sub>d</sub> 0 대 3 µs")}
{BOX2}

<h3>4.4 단계 2b — 교정표의 전압 여유가 내성을 정한다</h3>
{img("stage2b_margin.png", "그림 5. 단계 2b: 같은 스위칭 모델에 교정표만 바꿔 넣음. (a) 5 N·m, (b) 20 N·m 토크 오차(회색 ±5 %), (c) 표 점의 Lab 손실 − 같은 토크의 Lab 최적 손실. MCB·MBC 100 %가 음수인 것은 그 점이 Lab 계산으로는 전압 한계를 0–3 % 넘기 때문이다")}
<div class="scroll"><table><tr><th rowspan="2">기준표</th><th colspan="3">5 N·m</th><th colspan="3">20 N·m</th><th colspan="3">60 N·m</th><th colspan="3">20 N·m 표 점 (Lab FMU)</th></tr>
<tr><th>t<sub>d</sub> 0</th><th>3 µs</th><th>3 µs + 보상</th><th>t<sub>d</sub> 0</th><th>3 µs</th><th>3 µs + 보상</th><th>t<sub>d</sub> 0</th><th>3 µs</th><th>3 µs + 보상</th><th>I · γ</th><th>상전압</th><th>손실 대 최적</th></tr>{mb_rows}</table></div>
<ul>
<li><b>5 % 여유면 데드타임 3 µs를 보상 없이도 견딘다</b>: 20 N·m −6 %, 60 N·m −4 %, 5 N·m도 추종(+7 % / −24 %). 10 % 여유면 5 N·m도 −10 % 안.</li>
<li><b>여유가 있어야 보상이 제대로 듣는다.</b> 5 % 여유 표에 보상까지 더하면 20 N·m −2 %, 60 N·m −1.6 %, 5 N·m +0.5 %다. 여유 없는 표에서 같은 보상을 하면 −16 %, −5 %, −240 %다.</li>
<li><b>여유의 값은 진각이 아니라 전류로 치른다.</b> 20 N·m에서 진각은 88.01° → 88.05°(95 %) → 88.10°(90 %)로 0.1°도 안 바뀌고, 전류가 138.4 → 141.3 → 144.2 A로 늘어 Lab 손실이 +2.9 % / +6.6 %(60 N·m +2.3 % / +6.9 %) 늘어난다. 약자속 심부에서는 −d축 전류를 조금 더 넣어 전압을 내리는 것이 여유를 만드는 유일한 방법이기 때문이다.</li>
<li>MBC 표 끝(72 N·m, VsMax 90 %에서 도달 가능한 최대의 98 %로 잡은 격자)을 넘는 80 N·m 지령은 표 끝으로 잘려 −11 %다. 이는 표 설계의 선택이며 여유 자체의 효과가 아니다.</li>
</ul>
{BOX2B}

<h3>4.5 단계 3 — Lab FMU로 본 진각별 비용</h3>
{img("stage3_lab_gamma_sweep.png", "그림 6. Lab FMU(모드 2): 토크를 고정하고 진각을 강제할 때 필요한 전류로 푼 전체 손실(위)과 상전압(아래). ★ Lab 자체 최적(모드 0), × 전압 한계 초과, 빨간 점선 80°")}
<div class="scroll"><table><tr><th>속도</th><th>토크</th><th>Lab 최적 γ</th><th>전류</th><th>손실</th><th>전압을 만족하는 γ</th><th>γ = 80°의 손실 증가</th></tr>{sw_rows}</table></div>
<p>16 krpm에서는 80°가 아예 불가능하고, 8 krpm 60 N·m에서는 82° 이상, 4 krpm에서는 모든 진각이 가능하지만 80°는 최적(8.6°/19.4°) 대비 손실이 +109 %/+316 %다. <b>“80° 이상 올리지 말라”는 규칙이 해가 없는 곳은 전압 여유가 있는 저·중속뿐</b>이고, 그곳에서는 애초에 그렇게 큰 진각이 필요 없다.</p>
{img("stage3c_losses.png", "그림 7. 단계 3(c): 스위칭 모델이 실제로 도달한 (I, γ)를 Lab FMU로 되짚은 손실. (a) 화살표는 지령 토크 → 실현 토크, 회색 선은 같은 토크의 Lab 최적 손실, (b) 실현 N·m당 손실")}
<p><b>고속에서 오차의 비용은 손실이 아니라 토크다.</b> 데드타임·오프셋으로 도달점이 바뀌어도 손실은 거의 그대로이고(실현 토크 기준 Lab 최적 대비 −1.5~+4 %; 예외는 60 N·m 레졸버 오프셋 1°에서 +8 %, 2°에서 +17 %), 토크만 줄어든다. 약자속 전류가 손실을 정하기 때문이다. 그래서 20 N·m 지령에서 t<sub>d</sub> 3 µs는 실현 N·m당 손실을 574 → 926 W/(N·m)로 61 % 키운다.</p>
{BOX3}

<h3>4.6 전압 계산의 모델 간 차이</h3>
<p>스위칭 모델이 285.1 V에 붙여 둔 운전점을 Lab FMU로 되짚으면 상전압이 286–295 V로 0.5–3 % 높다(토크는 1–4 % 안에서 일치). 단계 1·2 플랜트의 V = |R i + jω<sub>e</sub>λ|가 Lab의 전압 계산(단자 전압에 포함하는 항)보다 약간 낮다. 방향은 “여유가 더 필요하다”는 쪽이므로 4.4절 결론을 강화한다.</p>

<h3>4.7 단계 2c — Simscape 교차 확인</h3>
{s2c_html}
{BOX2C}

<h3>4.8 모델 한계 — 단계 0–3이 공유하던 것 (4.9절에서 확인)</h3>
<div class="card"><ul>
<li><b>공간 고조파가 없다.</b> Lab export는 전류점마다 평균 ψ<sub>d</sub>, ψ<sub>q</sub>, 토크만 주고 회전자 위치 차원이 없다. 그래서 단계 0–3의 스크립트·Simscape 모델은 슬롯 고조파·코깅·역기전력 고조파가 없는 기계를 푼다. Lab이 빌드 점에서 계산해 둔 토크 리플은 16 krpm 기준표 운전점에서 약 48–71 N·m p-p로, 평균 토크와 같거나 크다. <b>→ 4.9절: 직접 FEA 위치별 맵을 넣으면 평균 토크는 같은 전류에서 그대로지만, 제어기가 고조파 전류에 반응해 운전점이 틀어진다. 이 효과가 데드타임보다 크다.</b></li>
<li><b>16 krpm 영역은 FEA 한 칸 안의 보간이다.</b> Lab 포화 모델의 FEA는 48점(전류 0–651 A 첨두 6점 × 진각 0–90° 8점, 12.86° 간격)이다. 운전 영역(195–250 A, 84–90°)은 130·260 A × 77.1°·90° 사이 한 칸에 들어간다. 맵, FMU, 단계 0 격자가 모두 같은 Lab 모델에서 나왔으므로 서로 맞는다고 이 보간이 검증되지는 않는다. <b>→ 4.9.1절: 운전 대역 직접 FEA와 자속 0.9 %, 토크 0.8 %, dT/dγ 0.06 N·m/° 안에서 같다. 보간은 맞다.</b></li>
</ul></div>
{sec49}

<h2 id="c">5. 결론</h2>
<div class="card">
<ol>
<li><b>e10의 16 krpm에서는 80°가 상한이 아니라 하한 쪽 문제다.</b> 전압이 γ ≥ 85–88°를 강제한다(1절, 4.5절). 폐루프 최대 토크에서도 실현 진각은 84.7°다. 운전 대역 직접 FEA가 Lab 보간을 확인했으므로(4.9.1절) 이 수치는 맵 오차가 아니다.</li>
<li><b>위쪽 벽은 정밀도다. 요인은 셋이다.</b> 88° 근처 저토크 운전점에서 ① 레졸버 오프셋 1°는 −57 %, ② 여유 없는 표에서 데드타임 3 µs는 −43 %(보상해도 −16 %), ③ 슬롯 고조파는 5 % 여유 표에서도 {pm(err("fea_pos", "MBC 95", 20), 0)} %다. ①은 인버터로 못 고친다. ②는 5 % 여유 + 보상이면 −2 %로 풀린다. ③은 평균 토크가 아니라 제어기 운전점의 문제다. 클램프에서 잘린 고조파 명령이 역산 안티와인드업을 거쳐 평균 전류 오차가 된다(4.9.4절). 측정 전류에서 6차·접힌 12차를 노치로 빼면 사라진다(4.9.8절).</li>
<li><b>교정표의 전압 여유가 핵심 설계 변수다. 다만 필요한 크기는 무엇을 모델에 넣느냐에 달렸다.</b> 평균 맵에서는 5 %면 데드타임 3 µs를 보상 없이 견딘다(오차 ≤ 6 %, 손실 +1–3 %). 슬롯 고조파와 이 제어기 구조에서는 20 N·m ±5 % 안에 드는 여유가 {nm_txt("fea_pos", 20)}다(기준 전류 디커플링이면 {nm_txt("fea_pos_ff", 20)}). 그러나 조절기가 슬롯 고조파를 못 보게 하는 노치를 넣으면 5 %로 충분하다(4.9.8절). 전압 피드백 약자속도 토크는 맞추지만 손실이 18–31 % 늘고, 공진 제어기로 억누르면 더 나빠진다. 여유는 진각이 아니라 전류와 손실로 치른다. 20 N·m 손실은 여유 5 %마다 약 +3.5 %씩 는다(4.9.5절).</li>
<li><b>현장의 “80°”는</b> 역기전력/전압 비가 낮은 기계, 여유를 넉넉히 둔 교정표, 1–2° 각도 오차 예산에서 굳어진 경험값으로 해석하는 것이 맞다. 이 기계에 그대로 적용하면 16 krpm 운전이 불가능하다. 고속 저토크를 다루기 어렵다는 현장 감각 자체는 4.9절의 고조파–제어기 상호작용과도 맞는다.</li>
<li><b>논문 인용 시:</b> 89.7° 같은 손실 최적 진각은 제어기가 유지하는 각이 아니다. 고속 손실 비교는 “전압 여유 k %를 둔 교정표” 기준으로 적어야 한다. 교류 동손 모델이 고속 진각을 거의 바꾸지 않는다(Δγ ≤ 0.25°)는 결론은 여유를 두면 오히려 강화된다(여유는 전류로 치르고 진각은 안 바뀐다). 단, 교류 동손 부하분은 입력측 손실이라 전압을 먹으므로 교정표를 만들 때 저항에 넣어야 한다.</li>
<li><b>방법:</b> 정상상태 계산기(<code>qs_opsolver.py</code>)는 평균 맵·교류 저항·데드타임까지는 시간영역 결과를 0.02–0.5° 안에서 재현하고 교정표를 만든다. 슬롯 고조파의 영향은 고정 여유로는 옮겨지지 않는다. 그러나 제어기 구조를 넣은 조화균형 확장(<code>qs_harmonic_hb.py</code>)은 Simscape를 토크 {hb_rms:.1f} N·m, 진각 {hb_rmsg:.2f}° 안에서 재현한다(4.9.6절). 표 설계와 여유 선택은 계산기로 하고, 시간영역 모델은 최종 확인에 쓴다.</li>
<li><b>열린 문제:</b> Motor-CAD 전압 출력이 |R i + jω<sub>e</sub>ψ|보다 2–4 % 높은 원인, 노치를 속도에 따라 옮기는 구현과 16 krpm 밖(다른 속도·토크)에서의 확인. 스큐는 실제 기계에 없음을 확인했다(09-24).</li>
</ol></div>

<h2 id="f">6. 모델·코드·데이터 경로 (PC1)</h2>
<p>결과별 파일은 4절 각 소절 끝의 파일 상자에 있다. 아래는 전체 목록이다. 모델 구조와 이론은 <a href="drive_model_study.html">구동 시뮬레이션 모델 해설</a>.</p>
<div class="scroll"><table><tr><th>구분</th><th>경로</th><th>내용</th></tr>
<tr><td>저장소</td><td><code>D:\\KangDH\\EveryMotor\\eMach</code> 브랜치 <code>docs/loss-torque-convention</code></td><td>코드는 <code>tools\\motorCAD\\MotorControl\\e10drive\\</code>, 데이터·생성 모델은 저장소 밖 <code>D:\\KangDH\\Thesis\\e10\\work_lab_pc1\\</code></td></tr>
<tr><td>단계 1</td><td><code>tools\\motorCAD\\MotorControl\\e10drive\\build_e10_stage1.m</code>, <code>run_e10_stage1.m</code>, <code>sim_e10_stage1.m</code></td><td>평균값 dq 플랜트 + 이산 FOC</td></tr>
<tr><td>단계 2 스위칭 모델</td><td><code>e10drive\\sim_e10_stage2.m</code></td><td>사건 구동 SVPWM·데드타임·Lab 맵 플랜트; 옵션 <code>ref</code>로 기준표 교체</td></tr>
<tr><td>단계 2 실행</td><td><code>e10drive\\run_e10_stage2.m</code> (<code>part = [i n]</code>으로 독립 배치 분할) + <code>merge_e10_stage2.m</code>, 그림 <code>plot_stage2.py</code></td><td>68 격자 + 파형 6; 배치 6개 병렬로 1분 이내</td></tr>
<tr><td>단계 2b</td><td><code>e10drive\\mbc_ref_from_lab.m</code> (calibratepmsm), <code>run_e10_stage2b.m</code>, 그림 <code>plot_stage2b.py</code></td><td>MBC 표 3종 → <code>drive\\mbc_tables.mat</code>; 결과 <code>drive\\stage2b_results.csv</code></td></tr>
<tr><td>단계 2c</td><td><code>e10drive\\build_e10_stage2c.m</code>, <code>run_e10_stage2c.m</code></td><td>HEV PMSM Drive Test Harness 개조 → <code>drive\\stage2c\\e10_stage2c.slx</code>; 원본 예제 <code>work_lab_pc1\\mw_examples\\ex1\\</code></td></tr>
<tr><td>단계 3</td><td><code>e10drive\\export_lab_model.py</code> → <code>work_lab_pc1\\fmu\\e10Turn6V261.lab</code>; <code>lab_fmu.py</code>(FMU 래퍼), <code>lab_gamma_sweep.py</code>, <code>lab_stage3c.py</code>, 그림 <code>plot_lab_gamma_sweep.py</code>, <code>plot_stage3c.py</code></td><td>FMU: <code>C:\\Program Files\\ANSYS Inc\\v261\\motorcad\\FMU\\Ansys_Motor-CAD_Lab_BPM.fmu</code>; venv <code>work_lab_pc1\\fmu\\fmuenv</code>(fmpy 0.3.32); 결과 <code>lab_gamma_sweep.json</code>, <code>lab_stage3c.json</code></td></tr>
<tr><td>직접 FEA 위치별 맵</td><td><code>e10drive\\fea_posmap.py</code> (+ <code>mc_launch.py</code>), 분석 <code>fea_posmap_analyze.py</code></td><td>Motor-CAD 새 창, 모델 사본 <code>work_lab_pc1\\fea_pos\\e10_fea_pos.mot</code> → <code>posmap_band_00–05.mat</code>, <code>posmap_band_analysis.json</code>, Simscape 표 <code>drive\\stage2d_tables.mat</code></td></tr>
<tr><td>단계 2d</td><td><code>e10drive\\run_e10_stage2d.m</code>, <code>patch_stage2c_ctrl.m</code></td><td>표 변형 A–D·D<sub>ff</sub> × 기준표 MCB/MBC/QS → <code>drive\\stage2d_results*.csv</code></td></tr>
<tr><td>정상상태 계산기</td><td><code>e10drive\\qs_opsolver.py</code>, <code>qs_harmonic_margin.py</code>, 조화균형 확장 <code>qs_harmonic_hb.py</code></td><td><code>fea_pos\\qs_*.json</code>, <code>drive\\qs_tables.mat</code>, <code>fea_pos\\qs_margin_cost.json</code>, <code>fea_pos\\qs_harmonic_hb.json</code></td></tr>
<tr><td>E-Magnetic 손실 규약 확인</td><td><code>e10drive\\emag_loss_check.py</code></td><td><code>work_lab_pc1\\emag_check\\emag_loss_check.json</code> (결과는 loss_torque_convention.html 4.1–4.2절)</td></tr>
<tr><td>그림 8–13</td><td><code>e10drive\\plot_fea_check.py</code></td><td><code>fea_lab_check.png</code>, <code>fea_harmonics.png</code>, <code>stage2d_variants.png</code>, <code>stage2d_margin.png</code>, <code>qs_vs_td.png</code>, <code>qs_hb_vs_simscape.png</code></td></tr>
<tr><td>결과 데이터</td><td><code>D:\\KangDH\\Thesis\\e10\\work_lab_pc1\\drive\\</code></td><td><code>stage1_results.csv</code>, <code>stage2_results.csv</code>, <code>stage2_traces.mat</code>, <code>stage2b_results.csv</code>, <code>stage2c_results.csv</code>, <code>stage2d_results*.csv</code></td></tr>
<tr><td>이 페이지</td><td><code>tools\\motorCAD\\MotorControl\\gamma_wall_explainer.html</code> ← <code>make_gamma_wall_explainer.py</code> (+ <code>report_links.py</code>)</td><td>재생성 가능</td></tr></table></div>
{files_box("페이지 생성기", [item(HERE / "make_gamma_wall_explainer.py", "이 페이지 생성"), item(HERE / "report_links.py", "파일 상자 도우미"), item(HERE / "drive_model_study.html", "모델 해설 페이지", cmd="")])}
</main>{COPY_JS}</body></html>"""
def series(vn, T, td=0):
    return [(100 - int(tb.split()[1]), float(r["err_pct"])) for tb in QS_TABS for r in [s2d(S2Q, vn, tb, T, td)] if r]


c_all = [e for T in (5, 20, 60) for m, e in series("fea_avg", T)]
d20 = series("fea_pos", 20)
n20 = need_margin("fea_pos", 20)
c20 = cost(20, n20) if n20 else None
margin_summary = (
    "평균 맵(C)은 여유 %d–%d %%에서 모두 %s…%s %%로 여유와 무관하다(데드타임 3 µs 무보상이면 약 −5 %%). "
    "<b>위치별 맵(D)은 여유를 늘릴수록 나아지지만 느리다.</b> 20 N·m 오차가 여유 %s에서 %s다. "
    "±5 %% 안에 드는 여유는 D가 60 N·m %s, 20 N·m %s, 5 N·m %s이고, 기준 전류 디커플링(D<sub>ff</sub>)이면 %s, %s, %s다. "
    "%s") % (
    min(m for T in (5, 20, 60) for m, e in series("fea_avg", T)), max(m for T in (5, 20, 60) for m, e in series("fea_avg", T)),
    pm(max(c_all), 1), pm(min(c_all), 1), "/".join("%d" % m for m, e in d20) + " %",
    " / ".join(pm(e, 0 if abs(e) >= 1 else 1) for m, e in d20) + " %",
    nm_txt("fea_pos", 60), nm_txt("fea_pos", 20), nm_txt("fea_pos", 5),
    nm_txt("fea_pos_ff", 60), nm_txt("fea_pos_ff", 20), nm_txt("fea_pos_ff", 5),
    ("<b>이 제어기 구조로 16 krpm 20 N·m를 ±5 %% 안에서 다루려면 평균 맵이 요구하는 여유(5 %%)의 %d배가 필요하고, "
     "그 대가는 20 N·m 손실 %+.0f %%(여유 5 %% 표 대비)다.</b>" % (round(n20/5), c20[1])) if c20 else
    "<b>이 제어기 구조로는 시험한 가장 큰 여유에서도 16 krpm 20 N·m가 ±5 % 안에 들지 않는다.</b>")
doc = doc.replace("{MARGIN_SUMMARY}", margin_summary)
(HERE / "gamma_wall_explainer.html").write_text(doc, encoding="utf-8")
print("wrote", HERE / "gamma_wall_explainer.html")
