# eMach — Codex Context

> 이 레포지토리는 전기모터 설계 프레임워크 (eMach).  
> 연구자: 강도현 | 이 워크트리: 휴머노이드 프로젝트(HumanX)용 **범용 도구** · JEET 논문은 본 체크아웃

---

## 레포 구조

```
eMach/
├── +mcad/              Motor-CAD MATLAB 인터페이스 함수들
├── tools/
│   └── motorCAD/pyMCAD/  Python Motor-CAD 유틸리티 (fea_workflow, magnetic 등)
├── mlxperPJT/
│   └── JEET/           AC 손실 JEET 논문 → JEET/CLAUDE.md 참조
└── Class/              모터 설계 클래스
```

## 이 워크트리의 용도 — HumanX 용 범용 도구 (2026-09-15~)

워크트리 `D:\KangDH\eMach-humanoid`, 브랜치 `feat/humanoid`. 휴머노이드 프로젝트 자체(컨텍스트·데이터 규격·결과)는
비공개 레포 `D:\KangDH\HumanX` 에 있고(Claude·Codex 공용 컨텍스트는 그 레포의 CLAUDE.md), HumanX 의
`simulink/setupHumanX.m` 이 이 워크트리를 MATLAB path 에 올린다.

- 여기에는 다른 프로젝트에도 쓸 Motor-CAD ↔ MATLAB/Simulink 도구만 둔다.
- **이 레포(enjoyneer87/eMach)는 공개 fork 다** — 프로젝트 데이터·요구사양·결과를 커밋하지 않는다.
- JEET·M3 작업은 본 체크아웃 `D:\KangDH\EveryMotor\eMach`(브랜치 `devVeriACLoss`)에서 한다.

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
