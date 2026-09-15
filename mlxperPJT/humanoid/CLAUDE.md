# 휴머노이드 로봇 프로젝트 — Claude Code Context

> 시작: 2026-09-15 | 연구자: 강도현  
> 워크트리 `D:\KangDH\eMach-humanoid` · 브랜치 `feat/humanoid` (`devVeriACLoss` d30f0ab 에서 분기)  
> 주 도구: **Motor-CAD**(모터 설계·해석) + **MATLAB/Simulink**(시스템 레벨 시뮬레이션)

---

## 범위

휴머노이드 로봇 프로젝트. 모터는 Motor-CAD, 시스템은 MATLAB/Simulink 로 다룬다 (사용자 지정 주 도구).

관련 배경: 2026-08 세미나 자료와 학위논문 활용가능성 절에 "휴머노이드 액추에이터 엔지니어링 —
Joint Actuator 시스템 설계와 QDD(준직접구동) 개발" 항목이 있다.

### ❓ 미정 — 추측으로 채우지 말고 사용자에게 확인할 것

- 대상 로봇·관절 (아래 ARTEMIS 자산을 이어받는지 포함)
- 관절별 요구사양: 연속/피크 토크, 속도, 질량·외경·축길이 제약, 듀티 사이클
- 감속기 형식·기어비, DC 링크 전압, 상전류 한계, 냉각 조건
- Simulink 모델 충실도: 평균값 vs 스위칭 인버터, 상수 파라미터 vs Motor-CAD 자속맵 LUT

---

## 도구 환경 (2026-09-15 실측)

| 도구 | 경로·버전 | 비고 |
|---|---|---|
| MATLAB | `C:\Program Files\MATLAB\R2026a` (Update 2, PATH 기본) | 아래 라이선스 확인 |
| MATLAB 대안 | `R2025a` | Simulink·Simscape·Motor Control Blockset 설치. R2021a~R2024b 는 Simulink 미설치 |
| Motor-CAD | v261 `C:\Program Files\ANSYS Inc\v261\motorcad\MotorCAD.exe` | COM `MotorCAD.AppAutomation` → v261 (`MOTORCAD_ACTIVEX` = v261 `activex.bat`) |
| Python | venv `C:\Users\user\.ansys_python_venvs\pyMotorEnv_310` (3.10.11) | `ansys-motorcad-core` 0.8.4, numpy 2.2, scipy, pandas. MATLAB Engine 미설치 |

- **R2026a `license('test')` = 1**: Simulink, Simscape, Simscape Electrical, Simscape Multibody,
  Motor Control Blockset, Control System, Simulink Control Design, Simulink Design Optimization,
  Stateflow, Optimization, Signal Processing, Statistics and Machine Learning, Robotics System,
  Simulink Coder, Embedded Coder, MATLAB Coder
- **설치만 확인 (`ver`)**: Simscape Driveline, Powertrain Blockset, ROS Toolbox, Simulink 3D Animation,
  Simulink Real-Time, Requirements Toolbox, System Composer, Reinforcement Learning Toolbox
- MATLAB 기본 path 에 eMach 없음 (`startup.m` 없음, userpath = `C:\Users\user\Documents\MATLAB`)
- 레포에 Simulink 모델(.slx/.mdl) 없음 — 이 프로젝트에서 처음 만든다

---

## 기존 자산 — `D:\KangDH\Romela_ARTEMIS\` (2025-10, 레포 밖)

UCLA RoMeLa ARTEMIS 휴머노이드 관절 모터 작업. **이번 프로젝트와의 관계 미확인.**

| 파일 | 실제 내용 (2026-09-15 확인) |
|---|---|
| `Hip_Roll_Yaw_U10_20251021.mot` | Motor-CAD 2025.2.2.1 저장본. `BPMOR`(외전형 BPM), `Slot_Number=18`, `Pole_Number=4`, `Stator_Lam_Dia=130` |
| `Hip_Yaw.ipynb` | pymotorcad 로 36슬롯/40극 형상 변수 일괄 설정. 저장 셀이 설정 셀보다 앞에 있고, 위 .mot 저장값도 노트북 설정값이 아니다 |
| `PyMCAD4Artemis.ipynb` | 72슬롯/80극(회전자 외경 186.5 mm)·36슬롯/40극 변수표. 저장 경로 `D:\KDH\artemis\Tibia_20251021.mot` 는 이 PC 에 없음 |
| `ARTEMIS_TLA_T-POSE.step`, `.x_b` | 로봇 전체 CAD (173 MB / 99 MB) |
| `23R1_ROM_Std.aedt` | AEDT 23R1 프로젝트 |

---

## Motor-CAD → MATLAB 연결 (eMach 에 이미 있는 것)

| 함수 | 역할 |
|---|---|
| `+mcad/getMcadActiveXTableFromMotFile.m` | .mot 텍스트 파싱 (v261 카탈로그 `loadActiveXCatalog`, 버전 불일치 경고) |
| `+mcad/getMCADLabDataFromMotFile.m` | .mot 에 저장된 Lab 맵 → 테이블 (자속 컬럼 `PsiDModel_Lab`/`PsiQModel_Lab`) |
| `+mcad/fromMCAD_lab_json.m` | Lab 자속 + AC 손실 JSON → dq 자속맵 (`FluxMap_dq`) |
| `+mcad/importExternalTxtLabModel.m` | Lab Link=Custom + 외부 LabLink.txt 모델 로드 |
| `+mcad/addLabInternalCustomLoss.m` | Lab Internal Custom Loss 등록 (ActiveX) |

Simulink 쪽 연결(자속맵 → 모터 블록 파라미터 등)은 없다 — 위 "Simulink 모델 충실도" 결정 후 만든다.

---

## 작업 규칙

### MATLAB / Simulink

- **path**: 이 워크트리의 함수를 쓰는 스크립트는 자기 위치 기준으로 `addpath` 한다. 본 체크아웃
  `D:\KangDH\EveryMotor\eMach` 가 같은 MATLAB 세션 path 에 같이 있으면 동명 함수가 섞인다
  (나중에 addpath 한 쪽이 우선).
- **실행**: Claude 가 직접 확인할 때는 `matlab -batch "스크립트명"` (헤드리스). 사용자는 GUI 에서 셀 단위 실행.
- **.mat**: Python 이 읽을 파일은 `save(..., '-v7')` 명시 — 기본 저장 포맷이 v7.3 (R2026a 에서도
  확인)이라 `scipy.io.loadmat` 이 못 읽는다.
- `slprj/`, `*.slxc`, `*.asv` 는 루트 `.gitignore` 에서 이미 제외.

### Motor-CAD

- Python 은 공식 API `from ansys.motorcad.core import MotorCAD` (`load_from_file`, `set_variable`,
  `get_variable`, `check_if_geometry_is_valid(1)`, `save_to_file`). raw win32com `Dispatch` 로는
  레거시 메서드가 안 보인다.
- 변수명은 추측하지 말고 레포 루트 `ActiveXParametersMotorCADv261.txt` 에서 확인. 틀린 이름은
  `set_variable` 이 조용히 실패하므로 설정 후 `get_variable` 로 read-back.
- Python `print` 에 cp949 밖 문자(—, ≈, ✓, Δ) 금지 — 콘솔 UnicodeEncodeError. 한글은 안전.
- Motor-CAD 는 .mot 옆에 동명 결과 폴더를 만든다. 루트 `.gitignore` 에 일반 규칙이 없으니 커밋 전 확인.

---

## 진행 상황

### ✅ 2026-09-15

- 워크트리·브랜치 생성, 도구 환경 실측 (위 표)

### 🔜 다음

- "미정" 항목 사용자 확인 → 첫 대상 관절·모터 결정
