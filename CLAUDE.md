# eMach — Claude Code Context

> 이 레포지토리는 전기모터 설계 프레임워크 (eMach).  
> 연구자: 강도현 | 주 작업: `mlxperPJT/JEET/` (AC 손실 JEET 논문)

---

## 레포 구조

```
eMach/
├── +mcad/              Motor-CAD MATLAB 인터페이스 함수들
├── tools/
│   └── motorCAD/pyMCAD/  Python Motor-CAD 유틸리티 (fea_workflow, magnetic 등)
├── mlxperPJT/
│   └── JEET/           ★ 현재 주 작업 폴더 → JEET/CLAUDE.md 참조
└── Class/              모터 설계 클래스
```

## 현재 주 작업

→ **`mlxperPJT/JEET/CLAUDE.md`** 참조 (AC 손실 검증, SC Hybrid MS B 추출 진행 중)

## Python 환경

```
가상환경: pyMotorEnv_310  (일반 venv, conda 아님)
Motor-CAD COM: ansys.motorcad.core (ansys-motorcad 패키지)
pyMCAD 경로:  eMach/tools/motorCAD/
```

## 주요 MATLAB 함수 (+mcad/)

| 함수 | 역할 |
|---|---|
| `loadAcLossJson.m` | AC 손실 JSON → MATLAB 구조체 |
| `buildAcLossFactor.m` | AC 손실 → SyRE용 kAC(freq) 변환 |
| `getMCADLabDataFromMotFile.m` | .mot → Lab 맵 데이터 |
| `saveSyreFluxMap.m` | SyRE 플럭스맵 저장 |
