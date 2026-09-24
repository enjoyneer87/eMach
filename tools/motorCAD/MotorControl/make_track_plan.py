# -*- coding: utf-8 -*-
"""Build track_plan.html: remaining plan of the PC1 drive/loss track (진각 벽, 슬롯 고조파, 손실 규약), the thesis
schedule, done items, other open tracks — with a version-history tab.

The plan content is PLAN below. Every run compares PLAN with the last snapshot in track_plan_history.json and,
if anything changed, appends a new version (--note says what changed). The page opens on the latest plan; the
"버전 이력" tab lists every version with what changed, and any version opens in place (#v1, #v2, ...).

  python make_track_plan.py --note "무엇을 바꿨나" [--artifact OUT.html]
  -> track_plan.html (links to the sibling reports, for PC1 / Drive) and OUT.html (same page, report links as
     text, artifact skeleton without html/head/body tags). Publish: Thesis_SKKU/tools/publish_html_reports.py.
"""
import argparse
import datetime as dt
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HIST = HERE / "track_plan_history.json"
DEFENSE, PREDIST, CH7 = dt.date(2026, 11, 30), dt.date(2026, 11, 1), dt.date(2026, 9, 30)

PLAN = dict(
    today="2026-09-24",
    next=("제4부(구동 제어와의 연계) 구성안을 확정한다: 두 장(8·9장), 7장 뒤, 결론은 10장. 확정되면 PC1이 원고 골격과 "
          "1장·결론 연결 초안을 만들고, 병행해서 노치의 속도 범위 계산을 분리 실행으로 돌린다."),
    items=[
        dict(pri="P1", title="제4부 '구동 제어와의 연계' 구성과 원고",
             why="노치 등 제어 관련 결과는 분량과 깊이가 있어 별도 파트로 둔다(사용자 결정 09-24). 현재 6장은 대리모델 기반 "
                 "다목적 최적설계라서 여기에 넣을 자리가 아니다. 논문은 이미 3부 8장 구조이므로, 7장 뒤에 제4부를 신설하면 4부 10장이 된다.",
             next="아래 '제4부 구성안'을 확정한다(두 장 대 한 장, 위치). 확정되면 원고 골격(.tex 두 개)을 만들고 phdThesis_v2.tex와 "
                  "Overleaf 매니페스트에 넣는다. 1장 논문 구성·그림, 2장 311행의 한계 문장, 결론(→10장)의 기여·한계·향후 연구를 잇는다. "
                  "그다음 결과 페이지 4–5절과 해설 13–15절을 원고로 옮긴다.",
             out="8·9장 원고(약 30–38쪽), 1장·결론 연결", owner="사용자 확정 → PC1 초안",
             effort="골격 0.5일, 초안 5–7일", status="user",
             refs=[["gamma_wall_explainer.html", "j", "결과 4.9절"], ["drive_model_study.html", "harm", "해설 14절"]]),
        dict(pri="P1", title="노치의 속도 범위 확인 (16 krpm 밖)",
             why="노치 결론은 16 krpm 한 점에서만 확인했다. 저속에서는 고조파가 전류 루프 대역(1.6 kHz)에 가까워져 노치가 기본파 "
                 "제어를 흔들 수 있다. 제4부의 대책 절이 이 범위를 말해야 한다.",
             next="위치별 FEA 맵을 저속 운전 영역(더 큰 i_q)까지 넓혀 계산한다. 조화균형 계산기로 4·8·12·16 krpm을 걸러 켜는 문턱 "
                  "후보를 정하고, Simscape 2e로 확인한다.",
             out="노치 사용 속도 범위 (제4부 9장 대책 절)", owner="PC1", effort="FEA 3–6 h(분리 실행) + 실행 1 h",
             status="ready",
             refs=[["gamma_wall_explainer.html", "rem", "결과 4.9.8절"], ["drive_model_study.html", "remedy", "해설 14.2절"]]),
        dict(pri="P2", title="Motor-CAD 전압 출력이 2–4 % 높은 원인",
             why="Lab(414–419 V)과 E-Magnetic(20 N·m에서 411 V) 전압이 같은 자속으로 계산한 |R i + jω_e ψ|(401 V)보다 높다. "
                 "여유 계산의 기준점이 걸린 문제다.",
             next="E-Magnetic에서 말단 권선 인덕턴스와 교류 저항 항을 켜고 끄며 페이저 전압을 비교한다. Lab의 전압 정의도 확인한다.",
             out="원인 1줄 + 4.9.1절 갱신", owner="PC1", effort="0.5일", status="ready",
             refs=[["gamma_wall_explainer.html", "j", "결과 4.9.1절"]]),
        dict(pri="P2", title="FullFEA 축 토크 −0.32 N·m 차이 분리",
             why="Hybrid와 FullFEA 교류 동손이 같은 운전점에서 축 토크 −0.32 N·m 차이를 냈다. 기동 과도가 섞였을 수 있다.",
             next="주기 수를 늘려 과도를 뺀 뒤 다시 계산한다.", out="손실 규약 문서 4.2절 갱신", owner="PC1", effort="1–2 h",
             status="ready", refs=[["loss_torque_convention.html", "", "손실 규약 문서"]]),
        dict(pri="P2", title="정상상태 계산기의 데드타임 계수 보정",
             why="보상 없는 3 µs에서 계산기가 시간영역보다 진각을 0.1–0.5° 적게 낸다.",
             next="시간영역 결과로 (4/π)V_dc·t_d·f_pwm 계수를 보정하거나, 전류 영교차 몫을 넣는다.", out="qs_opsolver.py 갱신",
             owner="PC1", effort="1 h", status="ready", refs=[["drive_model_study.html", "qs", "해설 15절"]]),
        dict(pri="P2", title="조화균형 계산기 보강",
             why="약자속 루프 60 N·m에서 계산이 수렴하지 않았다. 공진 제어기, 조건부 적분, 축 우선 클램프는 아직 계산기에 없다.",
             next="빠진 제어기 구조를 넣고, 2e 결과로 다시 검증한다.", out="qs_harmonic_hb.py 갱신", owner="PC1",
             effort="0.5–1일", status="ready", refs=[["gamma_wall_explainer.html", "rem", "결과 4.9.8절"]]),
        dict(pri="P2", title="위치별 맵 앞먹임 시험 (노치의 대안)",
             why="위치별 맵으로 예측한 Δi(θ)를 측정 전류에서 빼면, 속도에 따라 노치를 조정하지 않아도 될 수 있다.",
             next="Simscape 2e 제어기에 선택지를 추가하고 조화균형 계산기에도 넣어 노치와 비교한다.", out="4.9.8절 보강",
             owner="PC1", effort="1–2 h", status="ready", refs=[["drive_model_study.html", "remedy", "해설 14.2절"]]),
        dict(pri="P2", title="PWM 측대파 코드 정비 (Liang 2014)",
             why="eMach tools/calcSideBandHarmonic.m은 SVPWM 측대파 전압·전류 모델이다. 예제 값 스크립트이고 버그가 몇 개 있다"
                 "(rpm 순서, H2 괄호, iq_2ws 누락, C25·C27). 첨두 전류와 PWM 교류손(대역분할 트랙)에 쓸 수 있다.",
             next="버그를 고치고 함수로 만든 뒤, 16 krpm 측대파를 계산해 슬롯 고조파 대역과 비교한다.", out="함수 + 검증 그림",
             owner="PC1", effort="0.5일", status="ready", refs=[]),
        dict(pri="P3", title="PC2와 손실 규약 남은 항목 공유",
             why="손실 규약 문서 6절에 PC2 몫이 남아 있다. eMach 전류맵 코드의 compMTPA 목적함수 점검, 회귀 케이스, 이중 계상 확인이다.",
             next="PC2가 문서 6절을 보고 진행한다. 커밋 e7391ad로 공유되었다.", out="PC2 점검 결과", owner="PC2",
             effort="PC2 판단", status="wait", refs=[["loss_torque_convention.html", "", "손실 규약 6절"]]),
        dict(pri="P3", title="파이프라인 코드를 ipmfea 패키지로",
             why="qs_opsolver, qs_harmonic_hb, fea_posmap 등이 캠페인 폴더(e10drive)에 스크립트로 있다. 코드는 패키지로 남긴다는 원칙이 있다.",
             next="재사용할 부분을 ipmfea 모듈로 옮기고 회귀 기준을 세운다.", out="ipmfea 모듈", owner="PC1", effort="1일",
             status="later", refs=[]),
        dict(pri="P3", title="단계 0 몬테카를로 스크립트 복원",
             why="당시 스크래치패드에만 있어 저장소에 남지 않았다.", next="결과 표(gamma_wall_mc.csv)로 다시 만들고 저장소에 넣는다.",
             out="스크립트", owner="PC1", effort="1 h", status="later", refs=[["gamma_wall_explainer.html", "r", "결과 4.1절"]]),
    ],
    part=dict(
        title="제4부 구성안 — 구동 제어와의 연계 (신설, 7장 뒤)",
        why=("현재 논문은 3부 8장이다: 제1부 배경·모델링(1–2장), 제2부 스케일링(3–5장), 제3부 최적설계와 통합(6–7장), 8장 결론. "
             "6장은 대리모델 기반 다목적 최적설계라 제어 내용이 들어갈 자리가 아니다. 모든 FEA가 정현파 전류원이고 제어기 연동은 "
             "하지 않는다는 한계(2장 311행)와, 결론의 '형상–제어 코디자인' 항목이 든 세 가정(지령 전류가 그대로 흐름, V_max를 전부 "
             "씀, 정현파 전류) 가운데 뒤의 둘을 이 트랙이 직접 다룬다. 그래서 7장 케이스의 설계를 실제로 운전할 수 있는가를 묻는 "
             "제4부로 두는 것이 흐름에 맞다."),
        chapters=[
            dict(no="8", title="고속 약자속 운전의 전압 여유", pages="15–18쪽", sections=[
                ["문제 — 현장의 진각 80° 벽 대 손실 최적 89.7°", "두 숫자가 서로 다른 제약임을 보인다", "결과 1절"],
                ["16 krpm 전압 방정식과 진각 창", "γ ≥ 85–88°, 특성전류점 −273 A, 전류·진각 격자의 전압", "결과 1–2절, 해설 4절"],
                ["구동 모델 사다리와 검증", "평균값 dq → 사건 구동 스위칭 → Simscape → Lab FMU. 스크립트 대 Simscape 0.05–1.8 %, 지연 인공물 정정",
                 "결과 3·4.2·4.3·4.7절, 해설 1–12절"],
                ["전압 여유를 먹는 요인", "데드타임(주기당 한 에지, 보상), 교류 동손 부하분(R_ac 0.050 Ω, 손실 규약), Lab 보간(직접 FEA로 검증)",
                 "결과 4.3·4.9.1·4.9.3절, 손실 규약 문서"],
                ["교정표의 전압 여유와 비용", "MCB·MBC·QS 표. 평균 맵에서는 5 %로 충분, 여유는 전류로 치름(20 N·m 손실 +3.5 %/5 %)",
                 "결과 4.4·4.9.5절"],
                ["오차의 비용은 손실이 아니라 토크", "Lab FMU로 되짚은 도달점 손실", "결과 4.5절"],
            ]),
            dict(no="9", title="슬롯 고조파와 전류 조절기", pages="15–20쪽", sections=[
                ["회전자 위치별 FEA 맵", "dq 6·12차, 토크 리플 47–75 N·m p-p, 실제 기계도 스큐 없음", "결과 4.9.2절, 해설 13절"],
                ["평균 토크는 그대로, 운전점이 옮겨진다", "Simscape 표 변형 A–D, 잔차 분석(0.5 N·m)", "결과 4.9.3–4.9.4절"],
                ["클램프와 안티와인드업의 기구", "정류 작용, mean(e) = δ/8.5 Ω, 틈과 리플", "해설 14.1절(그림 8)"],
                ["필요한 여유", "QS 표 5–30 %: 20 N·m에 25 %, 비용 +15 %", "결과 4.9.5절"],
                ["정상상태 계산기와 조화균형 확장", "QS·HB, Simscape 재현 RMS 0.7 N·m·0.04°", "결과 4.9.6절, 해설 15절"],
                ["대책", "노치(해결, 여유 5 %로 복귀), 기준 전류 디커플링, PR(역효과), 과변조(일부), 전압 피드백 약자속(손실 +18–31 %)",
                 "결과 4.9.8절, 해설 14.2절"],
                ["설계 절차에의 함의와 한계", "고속 손실 비교는 여유 k % 조건으로, 노치 속도 범위, Motor-CAD 전압 2–4 %", "이 계획 P1·P2"],
            ]),
        ],
        elsewhere=[
            "1장: '3부 8장' → '4부 10장', 논문 구성 문단과 그림 fig:thesis_flow에 제4부 추가",
            "2장 311–313행: '제어기–FEA 공동 시뮬레이션은 수행하지 않으며' 뒤에 제4부에서 다룬다는 한 문장",
            "4장 800행 부근: 약자속 운전각 재평가 문장과 제4부의 운전점 계산기 연결",
            "결론(8장 → 10장): 기여에 제4부 한 항목, 한계·향후 연구의 '형상–제어 코디자인' 항목 갱신",
            "phdThesis_v2.tex에 새 장 포함, tools/overleaf_manifest.py에 두 파일 추가",
        ],
        options=[
            "두 장(권장): 부는 둘 이상의 장으로 묶는 기존 구성(2·3·2장)과 맞고, 8장은 여유, 9장은 고조파로 주제가 나뉜다.",
            "한 장: 30쪽 남짓의 긴 장 하나. 부를 두기보다 7장 뒤 독립 장으로 두는 셈이다.",
        ],
    ),
    closed={"기준 모델의 스큐 여부 확인": "사용자 확인: 실제 기계에 스큐 없음, 결론 크기 그대로",
            "논문 반영 범위 결정과 원고 초안": "결정: 제어 관련은 별도 파트(제4부), 새 P1 항목으로 이어짐"},
    done=[
        ["09-17–18", "단계 0 몬테카를로, 단계 1 평균값 dq (지연 결론은 뒤에 인공물로 정정)", "gamma_wall_explainer.html", "r"],
        ["09-23", "단계 2 스위칭 모델 (데드타임 보상 2배 오류 수정), 2b MBC 교정 여유, 2c Simscape 교차 확인, 3 Lab FMU 손실", "gamma_wall_explainer.html", "r"],
        ["09-23", "구동 모델 해설 페이지, 결과별 파일 링크 상자, 손실 규약 문서에 Motor-CAD E-Magnetic·Lab 처리 보강", "drive_model_study.html", ""],
        ["09-23", "직접 FEA 위치별 맵 (174점 × 위치 120) → Lab 48점 보간 검증 (자속 0.9 %, 토크 0.8 %)", "gamma_wall_explainer.html", "j"],
        ["09-23", "단계 2d: 슬롯 고조파는 평균 토크가 아니라 제어기 운전점을 옮김 (여유 5 % 표 20 N·m −54 %), 필요 여유 25 %", "gamma_wall_explainer.html", "j"],
        ["09-23–24", "정상상태(QS) 계산기와 QS 기준표, 조화균형 확장 (Simscape 재현 RMS 0.7 N·m·0.04°), 클램프 해부", "drive_model_study.html", "qs"],
        ["09-24", "단계 2e 대책 시험: 측정 전류의 6·12차 노치로 해결 (여유 5 %로 복귀, 비용 없음)", "gamma_wall_explainer.html", "rem"],
        ["09-24", "HTML 보고서 Drive 게시 (판 기록·버전 상자), 커밋 e7391ad (eMach)·35f00f8 (Thesis_SKKU)", "", ""],
        ["09-24", "스큐 확인: 실제 e10 기계에 스큐 없음(사용자) → 결론 크기 그대로, 보고서 반영", "gamma_wall_explainer.html", "j"],
        ["09-24", "논문 반영 방향 결정: 제어 관련은 별도 파트(제4부)로 — 6장 확인 결과 대리모델 최적설계", "", ""],
    ],
    other=[
        ["P0", "원고·Overleaf·PDF 전달 정합", "Overleaf 변경과 최신 통합본 차이, 최신 PDF의 Drive 전달 확인"],
        ["P1", "2장 시제품 시험보고서", "역기전력 실측 파형·고조파, 손실 분리치 확보 → 2장 TODO(547행, 591–597행) 보완(사용자 자료 의존)"],
        ["P1", "D4 전체 손실맵 수신·검증", "4속도 × 4전류 16점 결과 수신 → 누락·설정·온도·재료 확인"],
        ["P1", "CDB 접근·D1 16 krpm 재평가", "공유 경로 확보·해시 대조(D4 검증 뒤)"],
        ["P2", "짧은 적층 3D 열 검증", "1/k_L 축척과 상용 열회로 차이의 범위·자원·판정 기준 정리"],
        ["P2", "코디자인 M2", "WLTC3에서 정적/시간영역 사이클 에너지 차이 정량화(맥 주도)"],
        ["대기", "JEET 심사", "게재 확정이 본심 신청 조건 — 10월 초 편집부 진행 문의"],
    ],
    sched=[
        ["2026-09-22", "2026-09-30", "7장 마감", "thesis"],
        ["2026-10-01", "2026-10-10", "6·5·3장", "thesis"],
        ["2026-10-11", "2026-10-25", "1–2·8장 + 통합 교정 → 3인 회람", "thesis"],
        ["2026-11-01", "2026-11-01", "사전 배포본", "mile"],
        ["2026-11-02", "2026-11-27", "발표 준비", "thesis"],
        ["2026-11-30", "2026-11-30", "본심 (11월 말)", "mile"],
        ["2026-09-24", "2026-09-26", "제4부 구성안 확정", "track"],
        ["2026-09-28", "2026-10-02", "제4부 골격·1장·결론 연결", "track"],
        ["2026-09-29", "2026-10-06", "노치 속도 범위", "track"],
        ["2026-10-05", "2026-10-20", "제4부 8·9장 초안", "track"],
        ["2026-10-07", "2026-10-16", "P2 검증 보강", "track2"],
    ],
    decisions=[
        "제4부를 두 장(8·9장, 권장)으로 할지 한 장으로 할지, 위치는 7장 뒤·결론 앞(결론은 10장)으로 확정.",
        "제4부 초안 시기: 10월 초 6·5·3장 일정과 병행해 PC1이 초안을 쓰는 안(위 일정 막대)에 동의하는가.",
        "원고 골격 생성과 phdThesis_v2.tex·Overleaf 매니페스트 변경을 진행해도 되는가(다른 세션의 원고 작업과 겹치지 않게).",
    ],
)

STATUS = {"user": ("사용자 확인 필요", "st-user"), "ready": ("바로 진행 가능", "st-ready"),
          "wait": ("다른 PC 대기", "st-wait"), "later": ("본심 뒤 가능", "st-later")}

CSS = """
:root{--bg:#fbfaf7;--card:#ffffff;--fg:#1f2328;--mut:#5d6670;--line:#dcd7ce;--acc:#8a4b1f;--hl:#fff3e6;
--ready:#1f7a45;--ready-bg:#e6f3ea;--user:#8a4b1f;--user-bg:#fbeee2;--wait:#5b5fa8;--wait-bg:#ecedf7;--later:#6b6f76;
--later-bg:#eef0f2;--bar-thesis:#c9b8a3;--bar-track:#8a4b1f;--bar-track2:#c98a57;--today:#b3261e;--add:#1f7a45;--del:#b3261e}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#15171a;--card:#1d2024;
--fg:#e8e5df;--mut:#a4abb2;--line:#383c42;--acc:#e0a36e;--hl:#2a2218;--ready:#6fd39a;--ready-bg:#17301f;--user:#e0a36e;
--user-bg:#33251a;--wait:#a9adf0;--wait-bg:#23253d;--later:#a4abb2;--later-bg:#262a2f;--bar-thesis:#5a4d3f;
--bar-track:#e0a36e;--bar-track2:#9a6a44;--today:#f08a80;--add:#6fd39a;--del:#f08a80}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#15171a;--card:#1d2024;--fg:#e8e5df;--mut:#a4abb2;--line:#383c42;
--acc:#e0a36e;--hl:#2a2218;--ready:#6fd39a;--ready-bg:#17301f;--user:#e0a36e;--user-bg:#33251a;--wait:#a9adf0;
--wait-bg:#23253d;--later:#a4abb2;--later-bg:#262a2f;--bar-thesis:#5a4d3f;--bar-track:#e0a36e;--bar-track2:#9a6a44;
--today:#f08a80;--add:#6fd39a;--del:#f08a80}
body{background:var(--bg);color:var(--fg);font:15px/1.65 system-ui,"Malgun Gothic","Apple SD Gothic Neo","Noto Sans KR",sans-serif;margin:0}
.wrap{max-width:1040px;margin:0 auto;padding-inline:16px;padding-block:20px 56px}
h1{font-size:24px;line-height:1.3;margin:4px 0 4px;text-wrap:balance}
h2{font-size:18px;margin:34px 0 10px;padding-bottom:5px;border-bottom:2px solid var(--acc);text-wrap:balance}
h3{font-size:16px;margin:18px 0 6px}
.sub{color:var(--mut);margin:0 0 12px}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin:10px 0 4px;flex-wrap:wrap}
.tabs button{font:inherit;font-size:14.5px;background:none;border:0;border-bottom:3px solid transparent;color:var(--mut);
padding:6px 12px;cursor:pointer}
.tabs button[aria-selected="true"]{color:var(--fg);border-bottom-color:var(--acc);font-weight:700}
.tabs button:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
.banner{background:var(--wait-bg);color:var(--fg);border-radius:8px;padding:8px 12px;margin:12px 0;font-size:14px}
.banner button{font:inherit;font-size:13.5px;margin-left:8px;border:1px solid var(--line);background:var(--card);color:var(--fg);
border-radius:6px;padding:1px 8px;cursor:pointer}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:14px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.tile .k{font-size:12.5px;color:var(--mut);letter-spacing:.02em}
.tile .v{font-size:19px;font-weight:700;color:var(--acc);font-variant-numeric:tabular-nums;margin:2px 0}
.tile .d{font-size:13px;color:var(--mut)}
.next{background:var(--hl);border-radius:8px;padding:12px 14px;margin:10px 0}
.scroll{overflow-x:auto}
.items{list-style:none;padding:0;margin:0}
.item{border-bottom:1px solid var(--line);padding:12px 2px}
.item:first-child{border-top:1px solid var(--line)}
.ihead{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline}
.ititle{font-weight:700;font-size:15.5px}
.chip{display:inline-block;font-size:12px;line-height:1.5;padding:0 8px;border-radius:999px;border:1px solid var(--line);color:var(--mut);white-space:nowrap}
.p1{border-color:var(--acc);color:var(--acc);font-weight:700}
.st-ready{background:var(--ready-bg);color:var(--ready);border-color:transparent}
.st-user{background:var(--user-bg);color:var(--user);border-color:transparent}
.st-wait{background:var(--wait-bg);color:var(--wait);border-color:transparent}
.st-later{background:var(--later-bg);color:var(--later);border-color:transparent}
.row{display:grid;grid-template-columns:5.2em 1fr;gap:2px 10px;margin-top:6px;font-size:14px}
.row b{color:var(--mut);font-weight:600}
.refs{margin-top:6px;font-size:13px;display:flex;flex-wrap:wrap;gap:6px 12px}
.ref{color:var(--mut)}
.part{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:6px 16px 12px;margin:12px 0}
.part ol{margin:4px 0 10px;padding-left:1.4em}
.part li{margin:3px 0}
.part .src{color:var(--mut);font-size:12.5px}
code{font:12.5px/1.4 ui-monospace,Consolas,monospace;word-break:break-all}
table{border-collapse:collapse;width:100%;font-size:14px}
td,th{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{color:var(--mut);font-weight:600}
td.n{white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--mut)}
.chg{margin:4px 0 0;padding-left:1.2em;font-size:13.5px}
.chg .a{color:var(--add)}
.chg .r{color:var(--del)}
a{color:var(--acc)}
a:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
.mut{color:var(--mut)}
.small{font-size:13px}
.foot{margin-top:36px;font-size:13px;color:var(--mut)}
svg text{font-family:system-ui,"Malgun Gothic","Apple SD Gothic Neo",sans-serif}
"""

JS = """
<script>
(function(){
  var views = Array.prototype.slice.call(document.querySelectorAll('[data-view]'));
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tabs button'));
  function show(id){
    var target = document.getElementById(id) ? id : 'plan';
    views.forEach(function(v){ v.hidden = (v.id !== target); });
    var tab = target === 'history' ? 'history' : 'plan';
    tabs.forEach(function(b){ b.setAttribute('aria-selected', b.getAttribute('data-go') === tab ? 'true' : 'false'); });
  }
  document.addEventListener('click', function(e){
    var el = e.target.closest ? e.target.closest('[data-go]') : null;
    if (!el) return;
    e.preventDefault();
    var id = el.getAttribute('data-go');
    try { history.replaceState(null, '', '#' + id); } catch (err) {}
    show(id);
    window.scrollTo(0, 0);
  });
  function top(){ try { window.scrollTo(0, 0); } catch (err) {} }
  window.addEventListener('hashchange', function(){ show(location.hash.slice(1)); top(); });
  show(location.hash.slice(1) || 'plan');
  if (location.hash) { requestAnimationFrame(top); window.addEventListener('load', top); }   // keep the tabs in view
})();
</script>
"""


def esc(s):
    return html.escape(str(s), quote=True)


def D(s):
    return dt.date.fromisoformat(s)


def link(fname, anchor, label, local):
    if not fname:
        return ""
    href = fname + ("#" + anchor if anchor else "")
    if local:
        return '<a href="%s">%s</a>' % (esc(href), esc(label))
    return '<span class="ref">%s <code>%s</code></span>' % (esc(label), esc(href))


def timeline_svg(sched, today):
    d0, d1 = dt.date(2026, 9, 21), dt.date(2026, 12, 3)
    W, L, R = 980, 150, 16
    span = (d1 - d0).days
    X = lambda d: L + (W - L - R)*(d - d0).days/span
    rows = [("학위논문 일정", [s for s in sched if s[3] in ("thesis", "mile")]),
            ("이 트랙 (제안)", [s for s in sched if s[3] in ("track", "track2")])]
    out = []
    for m, lab in ((dt.date(2026, 10, 1), "10월"), (dt.date(2026, 11, 1), "11월"), (dt.date(2026, 12, 1), "12월")):
        out.append('<line x1="%.1f" y1="22" x2="%.1f" y2="%s" stroke="var(--line)" stroke-width="1"/>' % (X(m), X(m), "{H0}"))
        out.append('<text x="%.1f" y="16" font-size="12" fill="var(--mut)">%s</text>' % (X(m) + 3, lab))
    out.append('<text x="%.1f" y="16" font-size="12" fill="var(--mut)">9월</text>' % (X(d0) + 3))
    y = 34
    for name, items in rows:
        out.append('<text x="0" y="%d" font-size="12.5" fill="var(--mut)" font-weight="600">%s</text>' % (y + 14, name))
        for k, (s, e, lab, kind) in enumerate(items):          # one lane per item: labels never meet a bar
            s, e = D(s), D(e)
            yy = y + k*24
            if kind == "mile":
                cx = X(s)
                out.append('<path d="M%.1f %d l7 9 l-7 9 l-7 -9 z" fill="var(--acc)"/>' % (cx, yy))
                out.append('<text x="%.1f" y="%d" font-size="12" fill="var(--fg)" text-anchor="end">%s</text>'
                           % (cx - 10, yy + 13, esc(lab)))
            else:
                x0, x1 = X(s), X(e + dt.timedelta(days=1))
                col = {"thesis": "var(--bar-thesis)", "track": "var(--bar-track)", "track2": "var(--bar-track2)"}[kind]
                out.append('<rect x="%.1f" y="%d" width="%.1f" height="18" rx="3" fill="%s"/>' % (x0, yy, x1 - x0, col))
                tx, anchor = x1 + 5, "start"
                if tx > W - 180:
                    tx, anchor = x0 - 5, "end"
                out.append('<text x="%.1f" y="%d" font-size="12" fill="var(--fg)" text-anchor="%s">%s</text>'
                           % (tx, yy + 13, anchor, esc(lab)))
        y += len(items)*24 + 16
    xt = X(today)
    out.append('<line x1="%.1f" y1="22" x2="%.1f" y2="%d" stroke="var(--today)" stroke-width="1.6" stroke-dasharray="4 3"/>'
               % (xt, xt, y - 8))
    out.append('<text x="%.1f" y="%d" font-size="12" fill="var(--today)">오늘 %s</text>' % (xt + 4, y + 6, today.strftime("%m-%d")))
    body = "".join(out).replace("{H0}", str(y - 8))
    return ('<svg viewBox="0 0 %d %d" width="100%%" style="min-width:720px;display:block" role="img" '
            'aria-label="학위논문 일정과 이 트랙의 제안 일정">%s</svg>') % (W, y + 14, body)


def render_plan(P, local, ver, latest):
    today = D(P["today"])
    items = P["items"]
    cnt = {k: sum(1 for i in items if i["pri"] == k) for k in ("P1", "P2", "P3")}
    t = []
    if not latest:
        t.append('<div class="banner"><b>v%d (%s)</b> 판을 보고 있다. 지금 계획이 아니다.'
                 '<button type="button" data-go="plan">최신 판으로</button><button type="button" data-go="history">버전 이력</button></div>'
                 % (ver["ver"], esc(ver["date"])))
    t.append('<div class="tiles">')
    t.append('<div class="tile"><div class="k">본심 (11월 말)</div><div class="v">D−%d</div><div class="d">사전 배포본 11/1까지 D−%d</div></div>'
             % ((DEFENSE - today).days, (PREDIST - today).days))
    t.append('<div class="tile"><div class="k">7장 마감 (9월 말)</div><div class="v">D−%d</div><div class="d">10월 초 6·5·3장</div></div>'
             % (CH7 - today).days)
    t.append('<div class="tile"><div class="k">이 트랙 남은 일</div><div class="v">%d건</div><div class="d">P1 %d · P2 %d · P3 %d</div></div>'
             % (len(items), cnt["P1"], cnt["P2"], cnt["P3"]))
    t.append('<div class="tile"><div class="k">완료</div><div class="v">%d건</div><div class="d">09-17부터, 근거는 결과 보고서</div></div>'
             % len(P["done"]))
    t.append('</div>')
    t.append('<div class="next"><b>다음 한 가지.</b> %s</div>' % esc(P["next"]))
    t.append('<h2>일정</h2><div class="scroll">%s</div>' % timeline_svg(P["sched"], today))
    t.append('<p class="mut small">학위논문 일정은 흐름 노트 §일정 개정(2026-09-06)의 12주 역산 요지다(정본은 그 노트). '
             '이 트랙 막대는 제안이다. JEET 게재 확정이 본심 신청 조건이며, 10월 초 편집부 진행 문의가 잡혀 있다.</p>')
    part = P.get("part")
    for pri, head in (("P1", "P1 — 논문 신뢰성·반영에 직접 필요"), ("P2", "P2 — 검증 보강"), ("P3", "P3 — 정리·공유")):
        t.append('<h2>%s</h2><ul class="items">' % head)
        for it in items:
            if it["pri"] != pri:
                continue
            sl, sc = STATUS[it["status"]]
            t.append('<li class="item"><div class="ihead"><span class="ititle">%s</span>'
                     '<span class="chip %s">%s</span><span class="chip %s">%s</span>'
                     '<span class="chip">%s</span><span class="chip">예상 %s</span></div>'
                     % (esc(it["title"]), "p1" if pri == "P1" else "", pri, sc, sl, esc(it["owner"]), esc(it["effort"])))
            t.append('<div class="row"><b>왜</b><span>%s</span><b>다음</b><span>%s</span><b>산출물</b><span>%s</span></div>'
                     % (esc(it["why"]), esc(it["next"]), esc(it["out"])))
            r = [link(f, a, l, local) for f, a, l in it["refs"]]
            if r:
                t.append('<div class="refs">%s</div>' % "".join(r))
            t.append('</li>')
        t.append('</ul>')
        if pri == "P1" and part:
            t.append(render_part(part))
    t.append('<h2>사용자 결정이 필요한 것</h2><ul>%s</ul>' % "".join("<li>%s</li>" % esc(d) for d in P["decisions"]))
    t.append('<h2>완료한 것 — 이 트랙</h2><div class="scroll"><table><tr><th>날짜</th><th>내용</th><th>근거</th></tr>')
    for d, txt, f, a in P["done"]:
        t.append('<tr><td class="n">%s</td><td>%s</td><td>%s</td></tr>' % (esc(d), esc(txt), link(f, a, "보고서", local)))
    t.append('</table></div>')
    t.append('<h2>다른 트랙의 열린 항목</h2><p class="mut small">Thesis_SKKU <code>RESUME.md</code>(2026-09-10 확인) 기준이다. '
             '이 계획에서 상태를 다시 확인하지 않았다.</p>')
    t.append('<div class="scroll"><table><tr><th>우선</th><th>항목</th><th>다음 행동</th></tr>')
    for pr, title, nxt in P["other"]:
        t.append('<tr><td class="n">%s</td><td>%s</td><td>%s</td></tr>' % (esc(pr), esc(title), esc(nxt)))
    t.append('</table></div>')
    return "\n".join(t)


def render_part(part):
    t = ['<div class="part"><h3>%s</h3><p>%s</p>' % (esc(part["title"]), esc(part["why"]))]
    for ch in part["chapters"]:
        t.append('<p><b>제%s장 %s</b> <span class="mut">(%s)</span></p><ol>' % (esc(ch["no"]), esc(ch["title"]), esc(ch["pages"])))
        for title, what, src in ch["sections"]:
            t.append('<li><b>%s</b> — %s <span class="src">[%s]</span></li>' % (esc(title), esc(what), esc(src)))
        t.append('</ol>')
    t.append('<p><b>다른 장에서 고칠 곳</b></p><ul>%s</ul>' % "".join("<li>%s</li>" % esc(e) for e in part["elsewhere"]))
    t.append('<p><b>선택지</b></p><ul>%s</ul></div>' % "".join("<li>%s</li>" % esc(o) for o in part["options"]))
    return "".join(t)


def diff(prev, cur):
    """what changed from prev plan to cur plan: [(kind, text)] with kind in add/del/chg/note"""
    if prev is None:
        return [("note", "첫 판")]
    out = []
    pi = {i["title"]: i for i in prev["items"]}
    ci = {i["title"]: i for i in cur["items"]}
    for k in ci:
        if k not in pi:
            out.append(("add", "새 항목: %s (%s)" % (k, ci[k]["pri"])))
    closed = cur.get("closed") or {}
    for k in pi:
        if k not in ci:
            if k in closed:
                out.append(("close", "닫은 항목: %s — %s" % (k, closed[k])))
            else:
                out.append(("del", "빠진 항목: %s" % k))
    for k in ci:
        if k in pi:
            a, b = pi[k], ci[k]
            ch = [f for f in ("pri", "status", "owner", "effort", "next", "why", "out") if a.get(f) != b.get(f)]
            if ch:
                lab = {"pri": "우선순위", "status": "상태", "owner": "담당", "effort": "예상", "next": "다음 행동",
                       "why": "이유", "out": "산출물"}
                s = ", ".join(lab[f] for f in ch)
                if "status" in ch:
                    s += " (%s → %s)" % (STATUS[a["status"]][0], STATUS[b["status"]][0])
                out.append(("chg", "바뀐 항목: %s — %s" % (k, s)))
    pd = {d[1] for d in prev["done"]}
    for d in cur["done"]:
        if d[1] not in pd:
            out.append(("add", "완료 추가: %s" % d[1]))
    if (prev.get("part") is None) != (cur.get("part") is None) or prev.get("part") != cur.get("part"):
        out.append(("chg", "제4부 구성안 %s" % ("신설" if prev.get("part") is None else "수정")))
    if prev["decisions"] != cur["decisions"]:
        out.append(("chg", "결정 목록 갱신"))
    if prev["sched"] != cur["sched"]:
        out.append(("chg", "일정 막대 갱신"))
    return out or [("note", "문구만 바뀜")]


def render_history(H):
    t = ['<h2>버전 이력</h2><p class="mut small">판은 생성기를 다시 돌릴 때 내용이 바뀌었으면 하나씩 쌓인다. '
         '"보기"를 누르면 그 판의 계획이 이 페이지 안에서 열린다.</p>']
    t.append('<div class="scroll"><table><tr><th>판</th><th>날짜</th><th>설명</th><th>바뀐 점</th><th></th></tr>')
    for k in range(len(H) - 1, -1, -1):
        v = H[k]
        ch = diff(H[k - 1]["data"] if k > 0 else None, v["data"])
        cls = {"add": "a", "close": "a", "del": "r", "chg": "", "note": ""}
        lis = "".join('<li class="%s">%s</li>' % (cls[kind], esc(txt)) for kind, txt in ch)
        go = "plan" if k == len(H) - 1 else "v%d" % v["ver"]
        t.append('<tr><td class="n">v%d%s</td><td class="n">%s</td><td>%s</td><td><ul class="chg">%s</ul></td>'
                 '<td class="n"><a href="#%s" data-go="%s">보기</a></td></tr>'
                 % (v["ver"], " (최신)" if k == len(H) - 1 else "", esc(v["date"]), esc(v["note"]), lis, go, go))
    t.append('</table></div>')
    return "\n".join(t)


def page(H, local):
    last = H[-1]
    t = ['<div class="wrap">', '<h1>구동 트랙 진행 계획</h1>',
         '<p class="sub">PC1 구동·손실 트랙(진각 벽, 슬롯 고조파, 손실 규약)의 남은 일과 학위논문 일정 · 최신 판 v%d (%s) · '
         '생성기 <code>make_track_plan.py</code></p>' % (last["ver"], esc(last["date"])),
         '<nav class="tabs" role="tablist"><button type="button" role="tab" data-go="plan" aria-selected="true">계획 (v%d)</button>'
         '<button type="button" role="tab" data-go="history" aria-selected="false">버전 이력 (%d)</button></nav>' % (last["ver"], len(H)),
         '<section id="plan" data-view>%s</section>' % render_plan(last["data"], local, last, True),
         '<section id="history" data-view hidden>%s</section>' % render_history(H)]
    for v in H[:-1]:
        t.append('<section id="v%d" data-view hidden>%s</section>' % (v["ver"], render_plan(v["data"], local, v, False)))
    rep = [("gamma_wall_explainer.html", "", "진각 벽 결과 보고서"), ("drive_model_study.html", "", "구동 모델 해설"),
           ("loss_torque_convention.html", "", "손실 토크 귀속 규약")]
    t.append('<p class="foot">관련 보고서: %s. Drive 사본은 <code>J:\\내 드라이브\\Thesis_SKKU_sync\\html_reports\\index.html</code>. '
             '계획은 <code>eMach\\tools\\motorCAD\\MotorControl\\make_track_plan.py</code>의 PLAN을 고쳐 다시 만들고, 판 기록은 '
             '<code>track_plan_history.json</code>에 쌓인다.</p>'
             % " · ".join(link(f, a, l, local) if local else '<span class="ref">%s</span>' % esc(l) for f, a, l in rep))
    t.append('</div>')
    return "\n".join(t) + JS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--note", default="")
    ap.add_argument("--artifact", default="")
    ap.add_argument("--amend", action="store_true", help="replace the newest version (not yet published) instead of adding")
    a = ap.parse_args()
    H = json.load(open(HIST, encoding="utf-8")) if HIST.exists() else []
    if a.amend and H and H[-1]["data"] != PLAN:
        H[-1]["data"] = json.loads(json.dumps(PLAN))
        if a.note:
            H[-1]["note"] = a.note
        json.dump(H, open(HIST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("amended v%d" % H[-1]["ver"])
    if not H or H[-1]["data"] != PLAN:
        if not a.note and H:
            raise SystemExit("PLAN changed: pass --note to describe the new version")
        H.append(dict(ver=len(H) + 1, date=dt.datetime.now().strftime("%Y-%m-%d %H:%M"), note=a.note or "첫 판",
                      data=json.loads(json.dumps(PLAN))))
        json.dump(H, open(HIST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("new version v%d" % H[-1]["ver"])
    local = ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,'
             'initial-scale=1"><title>구동 트랙 진행 계획</title><style>%s</style></head><body>%s</body></html>' % (CSS, page(H, True)))
    (HERE / "track_plan.html").write_text(local, encoding="utf-8")
    out = Path(a.artifact) if a.artifact else HERE / "track_plan_artifact.html"
    out.write_text('<title>구동 트랙 진행 계획</title>\n<style>%s</style>\n%s' % (CSS, page(H, False)), encoding="utf-8")
    print("wrote", HERE / "track_plan.html", "and", out, "(%d versions)" % len(H))


if __name__ == "__main__":
    main()
