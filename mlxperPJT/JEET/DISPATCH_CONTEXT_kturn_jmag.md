# DISPATCH CONTEXT — Kturn + JMAG 실행 요청 ⚡ 즉시 실행 필요

_생성: 2026-07-19 · 소스: Claude Desktop (Cowork)_
_대상: VS Code Claude Code 세션 — **아래 명령어를 터미널에서 즉시 실행해줘**_

## ⚡ 바로 실행할 명령어

```bash
cd D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET
python run_kturn_and_jmag.py
```

이 스크립트(`run_kturn_and_jmag.py`)가 **Kturn(Motor-CAD)과 JMAG(MATLAB -batch)를 동시에** 실행한다.

---

## 작업 1: Kturn AC 손실 해석

**목적**: 4턴, 8턴 모델의 AC 손실 맵 생성 (6턴 Ref/SC 모델과 동일한 방식)

**실행 방법**: 아래 bat 파일이 이미 준비됨

```bat
cd D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET
.\run_kturn_full.bat
```

**`run_kturn_full.bat` 내용**:
- Step 1: `figures\capture_slot_views.py` — Geometry;Winding 탭 캡처 (4/6/8턴)
- Step 2: 4턴 sweep — 690A×6÷4, 5전류×6위상×4속도 × Hybrid+FullFEA
- Step 3: 8턴 sweep — 345A×6÷8, 5전류×6위상×4속도 × Hybrid+FullFEA

**주의사항**:
- `--skip-gen` 플래그: .mot 파일이 이미 `D:\KangDH\Thesis\e10\refModel\`에 있음 (e10Turn4V261.mot, e10Turn8V261.mot)
- `open_new_instance=True` 이미 적용됨 — 기존 COM 충돌 없음
- 결과: `.\kturn_results\` 에 JSON 저장
- Python 환경: `C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\python.exe`

---

## 작업 2: JMAG MS SC B 추출 (`devSurfInterp4HYBMS.m`)

**목적**: JMAG SC 모델에서 MS(정자기) B 필드 추출 → Volpe Hybrid 식에 사용

**실행 방법**: MATLAB에서

```matlab
cd('E:\KDH\e10\MSConductorModel\e10MS_ConductorModel_SCL_Load~13')
% 또는 Case 폴더들이 있는 상위 폴더로 이동
run('D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\Other\devSurfInterp4HYBMS.m')
```

**데이터 경로**: `E:\KDH\e10\MSConductorModel\...\e10MS_ConductorModel_SCL_Load~13\Case*\`
- 파일 패턴: `*wire*MS*SCL*MagB*.mat`
- 30 cases (~2.4 GB), case_map: `e10MS_ConductorModel_SCL_Load13_case_map.csv`
- wireTable radius 176~179 mm = SCL k_r=2

**⚠️ Z:\Simulation 경로는 마운트 해제된 NAS — 절대 사용 금지**

---

## 완료 후 체크

- Kturn 결과: `kturn_results\kturn_4turn_*.json`, `kturn_results\kturn_8turn_*.json`
- JMAG 결과: `devSurfInterp4HYBMS.m` 산출물 (WireFitTable, B-field 보간 결과)
- 완료 시 `DISPATCH_CONTEXT_kturn_jmag_done.md` 로 결과 요약 저장 요청
