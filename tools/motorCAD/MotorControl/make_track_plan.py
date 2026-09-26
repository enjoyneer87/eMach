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

PLAN = {'today': '2026-09-26',
 'next': '09-26 후속: C-low 예열 250노드에서 P-low 310 N·m·3860 rpm으로 10초 부하 전이 관찰 완료. 10/5/2.5초 온도–손실 갱신을 비교했다. 5→2.5초의 끝점 최대 '
         '온도 차이 0.251763°C로 0.1°C 기준은 미충족이며, 종점 토크·이상적 전압 기준은 통과했다. 다음은 구간 내 DC 동손 온도 갱신과 별도 AC 추가 동손 갱신 검증. 10초는 허용 '
         '피크시간이 아니다. 인터뷰는 추후 일괄, Overleaf Pull은 사용자 수행.',
 'items': [{'pri': 'P1',
            'title': '7장 후속: 구간 내 동손 갱신과 독립 열망',
            'why': '예열 상태 승계와 세 갱신 간격 관찰을 완료했다. 2.5초 갱신의 10초 최고 133.605313°C, 권선 평균 116.068911°C. 5→2.5초 전체 노드 차이 '
                   '0.251763°C로 0.1°C 기준은 남는다. 원시 ZIP 278파일만으로 모든 감사 수치 재현.',
            'next': '전자기 구리 계수 0.003862/°C로 구간 내부 DC 동손의 온도 갱신을 검증하고 AC 추가 동손 갱신과 분리해 간격 민감도를 줄인다. 열 모델의 비활성 '
                    '0.00393/°C 설정을 그대로 켜지 않는다. native 권선 평균에 조건부인 DC식과 독립 공간 온도 대응을 구별한다. 독립 R/P/유체 경계, 내부 적분 시간 수렴, '
                    '인버터 연성·합의된 한계온도의 피크시간은 후속. 냉각 사양은 추후 일괄 인터뷰.',
            'out': '구간 내 DC/AC 손실 갱신·온도 교환 간격 및 독립 열망 검증 근거',
            'owner': 'PC1',
            'effort': '후속 검증',
            'status': 'ready',
            'refs': [['https://drive.google.com/file/d/1FH7hXSgJ0i48H__Cu5jPKIyRR7oGoklx/view',
                      '',
                      'C-low→P-low 상태 승계·3간격 관찰'],
                     ['https://drive.google.com/file/d/1RMK5pxVVgtpE49k9jt16BXdwn8nCYoKR/view?usp=drivesdk',
                      '',
                      'C-low 목표 토크 유지·온도 연성 검증'],
                     ['https://drive.google.com/file/d/1yS6qxznQ08YBbYXmrD8ZskvUfh4Gy5NU/view',
                      '',
                      '기준 C-low FEA·손실·상태 연결'],
                     ['https://drive.google.com/file/d/1te0IgXs_p_PJPcfmptvokqQUQoK6qiKJ/view',
                      '',
                      '물성 갱신 대조·C-low 입력 감사'],
                     ['https://drive.google.com/file/d/1cLjGX4i56XUg8xYFG620bLLMjT7xMLVX/view', '', '초기 정상상태 수렴 검사'],
                     ['https://drive.google.com/file/d/1HAncOaazlRcehBxnzdyl_ArWuP8GUZmd/view',
                      '',
                      'Motor-CAD 과도 대조']]},
           {'pri': 'P1',
            'title': '제4부 원고·제어 정책 일괄 인터뷰',
            'why': '8.7·9.7·9.8과 그림 19개, 구성도, 전체 검토 PDF를 완료했다. 새 P2 결과도 9장에 반영했다. 사용자 요청에 따라 인터뷰를 후속으로 모았다.',
            'next': '허용 오버슈트·정착 시간, 노치 전환 정책, 맵 앞먹임의 오차 시험 범위, 약자속 제한 결과의 본문 범위를 한 번에 검토한다. Overleaf 반영은 09-25 완료.',
            'out': '사용자 검토 결정',
            'owner': '사용자·PC1',
            'effort': '추후 일괄',
            'status': 'later',
            'refs': [['drive_model_study.html', 'p2-validation', '추가 검증']]},
           {'pri': 'P1',
            'title': 'PC2 후속: 원 사례 입력과 실제 손실 배분 검증',
            'why': '손실 방향·속도 단위·0손실·Rdc 전압·원형 전류 한계를 정비했다. 합성 해석해 및 전력수지 검사, SHA-256으로 고정한 e10 Lab 16조건 모두 통과했다. 두 배분은 '
                   '진단 사례다.',
            'next': '438.2 N·m 원 모터·Lab 표·MachineData·상첨두 전압 한계를 고정하고 재현한다. 실제 입력측/제동 배분과 AC 직렬 저항 모델 연결은 후속 검토한다.',
            'out': '전력수지 검사와 출처가 고정된 전류맵 회귀',
            'owner': 'PC1 (PC2 작업 인수)',
            'effort': '원 사례 입력 확인 후 산정',
            'status': 'later',
            'refs': [['loss_torque_convention.html', '', '손실 규약 6절']]},
           {'pri': 'P3',
            'title': '파이프라인 코드를 ipmfea 패키지로',
            'why': 'qs_opsolver, qs_harmonic_hb, fea_posmap 등이 캠페인 폴더(e10drive)에 스크립트로 있다. 코드는 패키지로 남긴다는 원칙이 있다.',
            'next': '재사용할 부분을 ipmfea 모듈로 옮기고 회귀 기준을 세운다.',
            'out': 'ipmfea 모듈',
            'owner': 'PC1',
            'effort': '1일',
            'status': 'later',
            'refs': []}],
 'part': {'title': '제4부 — 구동 제어와의 연계 (두 장 초안·그림·검토 PDF 완료)',
          'why': '제4부 신설 전 논문은 3부 8장이었다: 제1부 배경·모델링(1–2장), 제2부 스케일링(3–5장), 제3부 최적설계와 통합(6–7장), 8장 결론. 6장은 대리모델 기반 다목적 '
                 "최적설계라 제어 내용이 들어갈 자리가 아니다. 모든 FEA가 정현파 전류원이고 제어기 연동은 하지 않는다는 한계(2장 311행)와, 결론의 '형상–제어 코디자인' 항목이 든 세 "
                 '가정(지령 전류가 그대로 흐름, V_max를 전부 씀, 정현파 전류) 가운데 뒤의 둘을 이 트랙이 직접 다룬다. 그래서 7장 케이스의 설계를 실제로 운전할 수 있는가를 묻는 '
                 '제4부로 두는 것이 흐름에 맞다.',
          'chapters': [{'no': '8',
                        'title': '고속 약자속 운전의 전압 여유',
                        'pages': '15–18쪽',
                        'sections': [['문제 — 현장의 진각 80° 벽 대 손실 최적 89.7°', '두 숫자가 서로 다른 제약임을 보인다', '결과 1절'],
                                     ['16 krpm 전압 방정식과 진각 창',
                                      'γ ≥ 85–88°, 특성전류점 −273 A, 전류·진각 격자의 전압',
                                      '결과 1–2절, 해설 4절'],
                                     ['구동 모델 사다리와 검증',
                                      '평균값 dq → 사건 구동 스위칭 → Simscape → Lab FMU. 스크립트 대 Simscape 0.05–1.8 %, 지연 인공물 정정',
                                      '결과 3·4.2·4.3·4.7절, 해설 1–12절'],
                                     ['전압 여유를 먹는 요인',
                                      '데드타임(주기당 한 에지, 보상), 교류 동손 부하분(R_ac 0.050 Ω, 손실 규약), Lab 보간(직접 FEA로 검증)',
                                      '결과 4.3·4.9.1·4.9.3절, 손실 규약 문서'],
                                     ['교정표의 전압 여유와 비용',
                                      'MCB·MBC·QS 표. 평균 맵에서는 5 %로 충분, 여유는 전류로 치름(20 N·m 손실 +3.5 %/5 %)',
                                      '결과 4.4·4.9.5절'],
                                     ['오차의 비용은 손실이 아니라 토크', 'Lab FMU로 되짚은 도달점 손실', '결과 4.5절']]},
                       {'no': '9',
                        'title': '슬롯 고조파와 전류 조절기',
                        'pages': '15–20쪽',
                        'sections': [['회전자 위치별 FEA 맵',
                                      'dq 6·12차, 토크 리플 47–75 N·m p-p, 실제 기계도 스큐 없음',
                                      '결과 4.9.2절, 해설 13절'],
                                     ['평균 토크는 그대로, 운전점이 옮겨진다', 'Simscape 표 변형 A–D, 잔차 분석(0.5 N·m)', '결과 4.9.3–4.9.4절'],
                                     ['클램프와 안티와인드업의 기구', '정류 작용, mean(e) = δ/8.5 Ω, 틈과 리플', '해설 14.1절(그림 8)'],
                                     ['필요한 여유', 'QS 표 5–30 %: 20 N·m에 25 %, 비용 +15 %', '결과 4.9.5절'],
                                     ['정상상태 계산기와 조화균형 확장', 'QS·HB, Simscape 재현 RMS 0.7 N·m·0.04°', '결과 4.9.6절, 해설 15절'],
                                     ['대책',
                                      '노치, 기준 전류 디커플링, PR, 과변조, 약자속의 관찰 범위 및 장시간 실패, 맵 앞먹임과 지령 제한 추가 시험',
                                      '결과 4.9.8절, 해설 14.2절'],
                                     ['설계 절차에의 함의와 한계',
                                      '고속 손실 비교는 여유 k % 조건으로, 노치 속도 범위, Motor-CAD 전압 2–4 %',
                                      '이 계획 P1·P2']]}],
          'elsewhere': ["1장: '3부 8장' → '4부 10장', 논문 구성 문단과 그림 fig:thesis_flow에 제4부 추가",
                        "2장 311–313행: '제어기–FEA 공동 시뮬레이션은 수행하지 않으며' 뒤에 제4부에서 다룬다는 한 문장",
                        '4장 800행 부근: 약자속 운전각 재평가 문장과 제4부의 운전점 계산기 연결',
                        "결론(8장 → 10장): 기여에 제4부 한 항목, 한계·향후 연구의 '형상–제어 코디자인' 항목 갱신",
                        'phdThesis_v2.tex에 새 장 포함, tools/overleaf_manifest.py에 두 파일 추가'],
          'options': ['두 장 구성 확정: 8장은 전압 여유, 9장은 슬롯 고조파·전류 조절기. 7장 뒤 제4부, 결론은 10장.']},
 'closed': {'해설 보고서에 속도 범위·노치 설명 반영': '저속 과도 30건과 정상상태 설명 그림 5종, P2 추가 검증 모두 통합 완료.',
            '저속 노치 과도 시험 (계단 응답)': '완료 09-24: 6·8·10 krpm Simscape 30건, 별도 사본·원시 데이터·HTML/PDF·검사 기록. 잠정 8 krpm 경계는 '
                                   '미확정.',
            '기준 모델의 스큐 여부 확인': '사용자 확인: 실제 기계에 스큐 없음, 결론 크기 그대로',
            '논문 반영 범위 결정과 원고 초안': '결정: 제어 관련은 별도 파트(제4부), 새 P1 항목으로 이어짐',
            '노치의 속도 범위 확인 (16 krpm 밖)': '완료 09-24: Simscape 24건 + 조화균형, 노치 6–16 krpm 전 구간 ±2 %, 교차 위상 지연 6k −21.8° … '
                                        "16k −4.1° → '저속 노치 과도 시험'으로 이어짐",
            "제4부 '구동 제어와의 연계' 구성과 원고": "구성 확정(두 장, 7장 뒤, 결론 10장) → '원고 (인터뷰 형식)' 항목으로 이어짐",
            '제4부 본문·그림·검토 PDF': '8.7·9.7·9.8, 그림 19개, 구성도 완료. 전체 빌드와 제4부 시각 검토. 인터뷰는 추후 일괄.',
            '정상상태 속도 범위 설명 그림 통합': '같은 전류·여유 대 속도·g 대 A·노치 응답·단순 위상 여유 5종을 두 HTML에 통합.',
            'FullFEA 축 토크 주기 수 대조': '3주기 FullFEA−Hybrid −0.328057 N·m. 1주기 기동 과도만으로 차이는 설명되지 않음.',
            '데드타임 계수 보정 감사': '1.027468배 보정은 별도 검증점 RMSE를 악화시켜 채택하지 않음. 기본 4/π 유지.',
            '조화균형 계산기·제어 구조 확장': 'PR·조건부 적분·축 우선 제한·맵 앞먹임과 수렴 검사 보강. FW60의 장시간 실패를 확인하고 지령 제한 변형은 63.79 N·m 대 HB 64.11 '
                                 'N·m.',
            '위치별 맵 앞먹임 시험': '무데드타임 6점 −0.52~+1.59%, 후반 클램프 0%. 16k/20 N·m는 9.36→19.94 N·m, td3us는 19.25 N·m. 과도·모델 오차 '
                            '시험은 후속 범위.',
            'PWM 측대파 코드 정비': '함수화·누락 항·위상·계수 수정. 독립 합성 PWM 전압과 최대 0.233% 차이, 전체 dq 임피던스 검사 통과.',
            'E-Magnetic 전압 차이 감사': '저항 성분은 Rdc·Irms, AC 끄기 전압 불변. 78°에서는 출력 자속식과 일치. 90° 부근 인덕턴스 별도 평가점 확인. Lab 추가 차이도 '
                                   '별도 export 감사에서 해소.',
            'Lab 전압의 추가 차이 분리': '51×51 격자점 전압은 부하분 AC 저항 포함 dq 식과 1.4e-12 V 이내 일치. 88.01°의 418.86 V는 자속 기반 402.89 V + '
                                '크기 보간 12.79 V + AC 저항 3.18 V. dq 보간 후 크기는 406.39 V. 원자료·기준표 보존.',
            '단계 0 몬테카를로 코드 복원': '09-25 원 세션 Write와 후속 각도·전압 수정 기록에서 복원. 135/200 A, 각 21행의 전체 숫자 오차 0. 기존 표·그림 보존.',
            'PC2 손실식 수치 정비': '09-25 손실 전류 40 W 흡수, 40 W/100 rad/s=0.4 N·m, 합성 해석해 3.76e-7 A, 전력 잔차 1.08e-12 W. 기존 Lab '
                             'export 16조건 통과; 원 438.2 N·m 사례와 구분.',
            '7장 고정 열망 과도 계산기': '09-25 C>0 96개·C=0 150개·고정 경계 4개 보존. 독립 전체 DAE 시간 간격 수렴 및 합성 해석해 포함 29검사 통과. Motor-CAD '
                               '과도 대조·피크 시간 검증은 후속.',
            '7장 Motor-CAD 저장점 과도 대조': '09-25 두 허용오차의 총 610초 시나리오, 250노드·206시점 대조. 최대 0.04597°C, 솔버 민감도 0.03403°C. 실제 '
                                      '정격·C-low·피크시간 검증과 구분.',
            '초기 정상상태 수렴 민감도 검사': '완료 09-26: Percent의 절대 dT 입력 비활성 확인, Value 0.005/0.00005°C 두 실행. 내부 경계 변화 '
                                 '0.014786→0.00001015°C, 전체 drift 약 0.0275°C 잔존. 초기 수렴만으로 해소되지 않음을 확인.',
            '물성 갱신 주기 대조와 C-low 입력 감사': '완료 09-26: 새 Enabled·Disabled 2실행과 Automatic 비교. 최대 변화 '
                                        '0.027553/0.027472/0.027527°C. 종점 K 사후 재생과 입력 경로 6파일 감사·미확정 초안 완료. 독립 R(T) 및 '
                                        '물리 C-low 예열은 후속.',
            '기준 C-low 직접 FEA·단방향 열 연결': '완료 09-26: 3회 FEA로 155.000041 N·m·3860 rpm. 5성분 native 열 입력 대조, 250노드 정상상태·10초 '
                                        '유지, ZIP 단독 감사 재현 완료. 온도 연성·연속정격·피크 시간과 구별.',
            '기준 C-low 목표 토크 유지 온도 연성': '완료 09-26: 4회 반복 후 직접 EM/열/온도 재전달 검사. 154.998496 N·m, 온도 잔차 0.000215451°C, '
                                       '250노드 10초 상태 승계 및 ZIP 85파일 감사 재현. 원본 냉각·고정 진각의 수치 연성이며 정격 인증·피크시간과 구별.',
            '7장 후속: 예열 상태 승계와 독립 열망 갱신': '부분 완료 후 재편 09-26: 예열 250노드 승계와 10/5/2.5초 갱신 관찰 완료. 온도 0.1°C 기준 미충족·독립 열망 갱신은 '
                                         '새 동손 갱신 항목에서 계속한다. 피크 허용시간은 미평가.'},
 'done': [['09-17–18', '단계 0 몬테카를로, 단계 1 평균값 dq (지연 결론은 뒤에 인공물로 정정)', 'gamma_wall_explainer.html', 'r'],
          ['09-23',
           '단계 2 스위칭 모델 (데드타임 보상 2배 오류 수정), 2b MBC 교정 여유, 2c Simscape 교차 확인, 3 Lab FMU 손실',
           'gamma_wall_explainer.html',
           'r'],
          ['09-23',
           '구동 모델 해설 페이지, 결과별 파일 링크 상자, 손실 규약 문서에 Motor-CAD E-Magnetic·Lab 처리 보강',
           'drive_model_study.html',
           ''],
          ['09-23',
           '직접 FEA 위치별 맵 (174점 × 위치 120) → Lab 48점 보간 검증 (자속 0.9 %, 토크 0.8 %)',
           'gamma_wall_explainer.html',
           'j'],
          ['09-23',
           '단계 2d: 슬롯 고조파는 평균 토크가 아니라 제어기 운전점을 옮김 (여유 5 % 표 20 N·m −54 %), 필요 여유 25 %',
           'gamma_wall_explainer.html',
           'j'],
          ['09-23–24',
           '정상상태(QS) 계산기와 QS 기준표, 조화균형 확장 (Simscape 재현 RMS 0.7 N·m·0.04°), 클램프 해부',
           'drive_model_study.html',
           'qs'],
          ['09-24', '단계 2e 대책 시험: 측정 전류의 6·12차 노치로 해결 (여유 5 %로 복귀, 비용 없음)', 'gamma_wall_explainer.html', 'rem'],
          ['09-24', 'HTML 보고서 Drive 게시 (판 기록·버전 상자), 커밋 e7391ad (eMach)·35f00f8 (Thesis_SKKU)', '', ''],
          ['09-24', '스큐 확인: 실제 e10 기계에 스큐 없음(사용자) → 결론 크기 그대로, 보고서 반영', 'gamma_wall_explainer.html', 'j'],
          ['09-24', '논문 반영 방향 결정: 제어 관련은 별도 파트(제4부)로 — 6장 확인 결과 대리모델 최적설계', '', ''],
          ['09-24', '노치 속도 범위 6–16 krpm: Simscape 24건 + 조화균형, 설명 그림 5종 — 커밋 c908752 (eMach)', '', ''],
          ['09-24', '제4부 신설: 8·9장 골격과 본문(8.1–8.6, 9.1–9.6), 결론 10장, 1·2·4장 연결, 매니페스트 105 — 커밋 55d0324', '', ''],
          ['09-24', '원고 인터뷰 형식 시작: 1–6회차 24문항(누적 17 정답), 해설 HTML(Thesis_SKKU defense/, 아티팩트)', '', ''],
          ['09-24', '저속 과도 30건 완료: 노치의 오버슈트 증가와 위치별 맵 토크 추종 개선, 6 krpm 발산 없음. 결과·인계 기록 작성', '', ''],
          ['09-24',
           '저속 과도 보고서 Drive 첫 게시. 종합 결과 4.9.8절·모델 해설 14.2절에 수치·파형 통합, 저속 미시험·부작용 없음 문구 정정',
           'gamma_wall_explainer.html',
           'notch-transient'],
          ['09-24',
           'P1 원고·그림·PDF 완료, P2 Simscape 16건·Motor-CAD 8건·계산기·PWM 감사. 인터뷰는 추후 일괄. E-Magnetic와 Lab 전압 차이의 원인 분리까지 완료.',
           'drive_model_study.html',
           'p2-validation'],
          ['09-25',
           'PC2 손실식·Lab 16조건, 고정 열망 DAE 29검사, 몬테카를로 원 코드 복원 42행 일치. 새 FEA·실측·논문 정본 수치 교체 없음.',
           'loss_torque_convention.html',
           'pc2-takeover'],
          ['09-25',
           'Motor-CAD 실제 과도 2실행, 초기 연결·206시점 대조·관측 입력 조건부 재생, 6개 새 회귀 검사. 다음은 초기 수렴과 R/P/유체 경계 연동.',
           'https://drive.google.com/file/d/1HAncOaazlRcehBxnzdyl_ArWuP8GUZmd/view',
           ''],
          ['09-26',
           '물성 갱신 3방식·종점 K 사후 재생·C-low 형상 및 손실 입력 감사 완료. 원시 자료와 노드별 HTML 게시.',
           'https://drive.google.com/file/d/1te0IgXs_p_PJPcfmptvokqQUQoK6qiKJ/view',
           ''],
          ['09-26',
           'C-low 기준 형상 직접 FEA, native 손실 전달, 250노드 상태 승계·10초 유지 및 ZIP 단독 감사 재현 완료. 고정 전자기 온도 진단.',
           'https://drive.google.com/file/d/1yS6qxznQ08YBbYXmrD8ZskvUfh4Gy5NU/view',
           ''],
          ['09-26',
           'C-low 목표 토크 유지 온도 연성 수렴, 최종 직접 3단계 재검사, 250노드 10초 유지 및 ZIP 85파일 감사 재현 완료.',
           'https://drive.google.com/file/d/1RMK5pxVVgtpE49k9jt16BXdwn8nCYoKR/view?usp=drivesdk',
           ''],
          ['09-26',
           'C-low→P-low 예열 승계·10초 관찰 및 3간격 비교 완료. 온도 0.1°C 기준 미충족을 보존하고 ZIP 278파일 감사 재현·조건부 DC 온도식 대조 완료.',
           'https://drive.google.com/file/d/1FH7hXSgJ0i48H__Cu5jPKIyRR7oGoklx/view',
           '']],
 'other': [['완료',
            '원고·Overleaf 반영',
            '09-25 실제 프로젝트 GitHub 가져오기 완료. 서버 291쪽·오류 0건. Drive의 기존 293쪽 PDF는 대체 글꼴 로컬 검토본으로 구분'],
           ['P1', '2장 시제품 시험보고서', '역기전력 실측 파형·고조파, 손실 분리치 확보 → 2장 TODO(547행, 591–597행) 보완(사용자 자료 의존)'],
           ['완료', 'D4·D1 전달 자료', 'D4 16점 + 저전류 8점 + 16 krpm 3점 = 27점 보강 및 D1 재평가 완료. 약계자 8점도 완료. 실제 연속정격 확정과 구별'],
           ['P2',
            '열 후속·짧은 적층 3D 검증',
            'PC1에서 후처리·입력 계약 정리 가능. 원 CDB/전체장 NPZ는 moa/NAS에 있으며 PC1의 옛 CDB 경로는 여전히 없음. 온도 연성·저온절점·메시 검증 후 새 해석'],
           ['P1',
            '7장 시스템 코디자인',
            'C-low 온도 연성 수렴과 P-low 예열 승계·10초 관찰 완료. 5→2.5초 온도 차이 0.251763°C로 0.1°C 기준은 미충족. 구간 내 DC/AC 손실 갱신, 독립 '
            'R/P/유체·내부 시간 수렴·인버터·한계온도 기반 피크시간이 남는다. 공통 냉각 조건은 추후 일괄 인터뷰.'],
           ['P2',
            '기존 코디자인 M2 진단',
            'Mac 인계 후 PC1 통합 완료, 51a0959. 8조건 전류 전이 진단 완료. 남은 것은 긴 이력·시간 간격 수렴·양의 id 지도·부호 있는 회생·전 구간 연속성. 이미 완료된 창 '
            '재실행 제외'],
           ['별도', 'JEET 심사 대응', '심사 수신 후 별도 리뷰 세션에서 진행 중. 학위논문 트랙과 원고·검증·출판 범위를 구분하고 사용자 결정은 일괄 인터뷰로 유지']],
 'sched': [['2026-09-22', '2026-09-30', '7장 마감', 'thesis'],
           ['2026-10-01', '2026-10-10', '6·5·3장', 'thesis'],
           ['2026-10-11', '2026-10-25', '1–2·8장 + 통합 교정 → 3인 회람', 'thesis'],
           ['2026-11-01', '2026-11-01', '사전 배포본', 'mile'],
           ['2026-11-02', '2026-11-27', '발표 준비', 'thesis'],
           ['2026-11-30', '2026-11-30', '본심 (11월 말)', 'mile'],
           ['2026-09-24', '2026-09-24', '제4부 확정·골격·연결', 'track'],
           ['2026-09-24', '2026-09-24', '노치 속도 범위', 'track'],
           ['2026-09-24', '2026-09-24', '제4부 원고·그림·로컬 검토 PDF 완료', 'track'],
           ['2026-09-24', '2026-09-24', '저속 노치 과도 시험 완료 (30건)', 'track'],
           ['2026-09-24', '2026-09-24', 'P2 추가 시험·계산기·전압 출력 감사 완료', 'track2']],
 'decisions': ['노치 켜는 문턱: 미확정. 6·8·10 krpm 과도 시험 완료만으로 8 krpm을 안정 경계로 정할 수 없다. 허용 과도 지표·부하·전환 조건에 따라 판단.',
               '인터뷰 후속: 맵 앞먹임의 파라미터 오차·과도 범위, 약자속 지령 제한 결과의 본문 범위. 이번에 질문하지 않고 일괄 검토로 보류.']}

STATUS = {"user": ("사용자 확인 필요", "st-user"), "ready": ("바로 진행 가능", "st-ready"),
          "wait": ("다른 PC 대기", "st-wait"), "later": ("후속 일정", "st-later")}

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
