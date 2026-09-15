# eMach — Claude Code Context

> 이 레포지토리는 전기모터 설계 프레임워크 (eMach).  
> 연구자: 강도현 | 작업 갈래: `mlxperPJT/humanoid/` (휴머노이드 로봇, **이 워크트리에서 활성**) · `mlxperPJT/JEET/` (AC 손실 JEET 논문)

---

## 레포 구조

```
eMach/
├── +mcad/              Motor-CAD MATLAB 인터페이스 함수들
├── tools/
│   └── motorCAD/pyMCAD/  Python Motor-CAD 유틸리티 (fea_workflow, magnetic 등)
├── mlxperPJT/
│   ├── humanoid/       ★ 이 워크트리의 활성 작업 → humanoid/CLAUDE.md 참조
│   └── JEET/           AC 손실 JEET 논문 → JEET/CLAUDE.md 참조
└── Class/              모터 설계 클래스
```

## 현재 주 작업 — 휴머노이드 로봇 프로젝트 (2026-09-15~)

→ **`mlxperPJT/humanoid/CLAUDE.md`** 참조. 워크트리 `D:\KangDH\eMach-humanoid`,
브랜치 `feat/humanoid`. 주 도구는 **Motor-CAD + MATLAB/Simulink**.

JEET·M3 작업은 본 체크아웃 `D:\KangDH\EveryMotor\eMach`(브랜치 `devVeriACLoss`)에서 한다.

## 도구 환경

```
MATLAB:        R2026a (PATH 기본) — Simulink·Simscape 계열·Motor Control Blockset 라이선스 있음
Motor-CAD:     v261 (COM 등록 버전)
가상환경:      pyMotorEnv_310  (일반 venv, conda 아님)
Motor-CAD COM: ansys.motorcad.core (ansys-motorcad 패키지)
pyMCAD 경로:   eMach/tools/motorCAD/
```

## 주요 MATLAB 함수 (+mcad/)

| 함수 | 역할 |
|---|---|
| `loadAcLossJson.m` | AC 손실 JSON → MATLAB 구조체 |
| `buildAcLossFactor.m` | AC 손실 → SyRE용 kAC(freq) 변환 |
| `getMCADLabDataFromMotFile.m` | .mot → Lab 맵 데이터 |
| `saveSyreFluxMap.m` | SyRE 플럭스맵 저장 |
