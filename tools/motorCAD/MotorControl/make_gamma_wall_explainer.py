# -*- coding: utf-8 -*-
"""Build gamma_wall_explainer.html: phenomenon, theory, reproduction method, results, paths.
Figures are embedded (single file). Data: gamma_highspeed_result.md B2/B6, stage1_results.csv,
stage2_results.csv, stage2b_results.csv, lab_gamma_sweep.json, lab_stage3c.json, stage2c_results.csv.
python make_gamma_wall_explainer.py
"""
import base64
import csv
import json
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
    return '<figure><img src="data:image/png;base64,%s" alt="%s"><figcaption>%s</figcaption></figure>' % (b, cap, cap)


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
FEM-Parameterized PMSM을 <code>fem_motor_dq0</code> 변형(DQcartesian)으로 바꿔 Lab ψ<sub>d</sub>/ψ<sub>q</sub>를 회전자각 7점에 복제해 넣고, 토크는 Lab 축 토크 표를 썼다.
속도는 이상 각속도원으로 16 000 rpm 고정, 인버터는 이상 스위치 + 역병렬 다이오드(도통 강하 ≈ 0), 데드타임은 <b>실제 상보 게이트 블랭킹</b>(켜짐 에지를 t<sub>d</sub>만큼 지연, 블랭킹 동안 도통은 다이오드가 결정), 제어기는 <code>sim_e10_stage2</code>와 같은 50 µs 이산 MATLAB Function(지연 보상·1샘플 지연 포함), 10 kHz SVPWM 양 끝 갱신, 가변 스텝 ode23t(MaxStep 5 µs).</p>
<div class="scroll"><table><tr><th>지령</th><th>t<sub>d</sub></th><th>T 스크립트</th><th>T Simscape</th><th>차이</th><th>γ 스크립트 / Simscape</th><th>I rms</th><th>토크 리플 p-p [N·m]</th><th>포화</th><th>계산 시간</th></tr>{BODY}</table></div>
<p><b>스크립트 스위칭 모델이 검증됐다.</b> 무데드타임 두 점은 토크 0.05 % 이내, 진각 0.001° 이내로 같다. t<sub>d</sub> 3 µs는 60 N·m +0.15 %, 20 N·m −1.8 %(0.2 N·m)다.
차이는 데드타임 모형에서 온다 — 스크립트는 스위칭 순간의 전류 부호로 지연 여부를 정하고, Simscape는 블랭킹 구간 중 전류 영교차까지 다이오드가 결정한다. 20 N·m은 필요 전압이 한계의 99.9 %인 불량조건 점이라 작은 볼트·초 차이가 토크를 크게 움직인다(0.02 s로 짧게 돌리면 포화를 빠져나오지 못해 15.0 N·m — 교차 확인은 0.08 s 이상 필요).
4.3–4.4절의 데드타임 결론(−43 %/−16 %)은 Simscape에서도 −44 %/−15 %로 같다.</p>
<p class="mut">빌드 함정: 변형 선택은 <code>ComponentPath</code>가 아니라 <code>SourceFile</code>로 해야 저장·재로드 후에도 유지된다(초기 실행은 하니스 원래의 6극쌍 이상 모터를 조용히 돌렸다). 블록은 id 격자가 0을 포함한 대칭을 요구해 Lab 맵(−650…0 A)을 +650 A까지 연장했다(ψ<sub>d</sub> 선형, ψ<sub>q</sub>·토크는 id = 0 값 유지) — 운전점(−190…−290 A)은 닿지 않는다.</p>""".replace("{BODY}", body)

CSS = """
:root{--bg:#fbfaf7;--card:#fff;--fg:#1f2328;--mut:#5d6670;--line:#dcd7ce;--acc:#8a4b1f;--hl:#fff3e6;--ok:#1f7a45;--warn:#a86a12;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15171a;--card:#1d2024;--fg:#e8e5df;--mut:#a4abb2;--line:#383c42;--acc:#e0a36e;--hl:#2a2218;--ok:#6fd39a;--warn:#e3b25d;--bad:#f08a80}}
body{background:var(--bg);color:var(--fg);font:15px/1.7 system-ui,"Malgun Gothic","Apple SD Gothic Neo",sans-serif;margin:0}
main{max-width:1000px;margin:0 auto;padding:18px 16px 64px}
h1{font-size:23px;line-height:1.3;margin:6px 0}h2{font-size:19px;margin:34px 0 8px;padding-bottom:4px;border-bottom:2px solid var(--acc)}
h3{font-size:16px;margin:20px 0 6px}.mut{color:var(--mut)}
nav{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}nav a{border:1px solid var(--line);border-radius:999px;padding:3px 12px;color:var(--fg);text-decoration:none;font-size:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:12px 0}
.kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin:14px 0}
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
<p class="mut">대상: e10 구동모터 기준기(Motor-CAD Lab 포화맵), 16 krpm, 직류 720 V · 초판 2026-09-23, 같은 날 단계 2·2b·2c·3 추가 · PC1 · 근거: 2026-09-17~18 세션 b5dcb1f7(단계 0·1), 2026-09-23 세션(단계 2·3)</p>
<p>모델이 어떻게 만들어졌는지(플랜트·제어기·PWM·데드타임·교정표·Simscape·FMU의 이론과 구현)는 <a href="drive_model_study.html"><b>구동 시뮬레이션 모델 해설</b></a>에 따로 정리했다. 결과마다 아래 <b>파일 상자</b>에서 모델·스크립트·데이터를 바로 열 수 있다. <span class="mut">{LINK_NOTE}</span></p>
<div class="kpi">
<div>16 krpm 역기전력<b>1042 V rms</b><span class="mut">상전압 한계 285.1 V rms의 3.7배</span></div>
<div>16 krpm에서 전압이 허락하는 진각<b>≥ 85–88°</b><span class="mut">토크가 낮을수록 더 높다 (Lab FMU)</span></div>
<div>데드타임 3 µs, 여유 0, 보상 없음<b>20 N·m → −43 %</b><span class="mut">스위칭 모델 (단계 2)</span></div>
<div>전압 여유 5 % 교정표<b>오차 −6 % 이내</b><span class="mut">대가: 손실 +1–3 % (단계 2b·3)</span></div>
</div>
<nav><a href="#p">1 현상</a><a href="#t">2 발생 이론</a><a href="#m">3 재현 방법</a><a href="#r">4 결과 분석</a><a href="#c">5 결론</a><a href="#f">6 모델·코드 경로</a></nav>

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

<h2 id="c">5. 결론</h2>
<div class="card">
<ol>
<li><b>e10의 16 krpm에서는 80°가 상한이 아니라 하한 쪽 문제다.</b> 전압이 γ ≥ 85–88°를 강제한다(1절, 4.5절). 폐루프 최대 토크에서도 실현 진각은 84.7°다.</li>
<li><b>위쪽 벽은 정밀도다.</b> 88° 근처 저토크 운전점에서 레졸버 오프셋 1°는 −60 %, 여유 없는 표에서 데드타임 3 µs는 −43 %다(보상해도 −16 %). 전자는 인버터로 못 고치고, 후자는 전압 여유가 있어야 고쳐진다(5 % 여유 + 보상이면 −2 %).</li>
<li><b>교정표의 전압 여유가 핵심 설계 변수다.</b> 5 %면 데드타임 3 µs를 보상 없이 견디고(오차 ≤ 6 %) 손실은 +1–3 %; 10 %면 +4–9 %. 진각은 0.1°도 움직이지 않는다.</li>
<li><b>현장의 “80°”는</b> 역기전력/전압 비가 낮은 기계, 여유를 넉넉히 둔 교정표, 1–2° 각도 오차 예산에서 굳어진 경험값으로 해석하는 것이 맞다. 이 기계에 그대로 적용하면 16 krpm 운전이 불가능하다.</li>
<li><b>논문 인용 시:</b> 89.7° 같은 손실 최적 진각은 제어기가 유지하는 각이 아니다. 고속 손실 비교는 “전압 여유 k %를 둔 교정표” 기준으로 적어야 하며, 교류 동손 모델이 고속 진각을 거의 바꾸지 않는다(Δγ ≤ 0.25°)는 결론은 여유를 두면 오히려 강화된다(여유는 전류로 치르고 진각은 안 바뀐다).</li>
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
<tr><td>결과 데이터</td><td><code>D:\\KangDH\\Thesis\\e10\\work_lab_pc1\\drive\\</code></td><td><code>stage1_results.csv</code>, <code>stage2_results.csv</code>, <code>stage2_traces.mat</code>, <code>stage2b_results.csv</code>, <code>stage2c_results.csv</code></td></tr>
<tr><td>이 페이지</td><td><code>tools\\motorCAD\\MotorControl\\gamma_wall_explainer.html</code> ← <code>make_gamma_wall_explainer.py</code> (+ <code>report_links.py</code>)</td><td>재생성 가능</td></tr></table></div>
{files_box("페이지 생성기", [item(HERE / "make_gamma_wall_explainer.py", "이 페이지 생성"), item(HERE / "report_links.py", "파일 상자 도우미"), item(HERE / "drive_model_study.html", "모델 해설 페이지", cmd="")])}
</main>{COPY_JS}</body></html>"""
(HERE / "gamma_wall_explainer.html").write_text(doc, encoding="utf-8")
print("wrote", HERE / "gamma_wall_explainer.html")
