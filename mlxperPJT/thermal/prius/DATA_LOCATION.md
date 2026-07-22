# Prius 열해석 산출물 위치 (코드=Git / 산출물=Google Drive)

이 패키지는 **코드만 Git(eMach)** 에 두고, **이미지·GIF·데이터는 Google Drive** 에
보관한다. (대용량 GIF ~21MB 로 Git 비대화 방지)

## Google Drive 폴더 (★ 모델기준 구조)
**Prius_thermal_viz**(프로젝트 산출물 루트) — https://drive.google.com/drive/folders/1Kmimyt69kD5a-YhUGLPhj54NR1JdD2tg
(소유: phareal87@gmail.com). 2026-07-22 부터 **결과는 모델별 하위폴더**로 정리:
```
Prius_thermal_viz/
├── prius/          # Prius 모터 결과
│   ├── viz/        (waterjacket_low/high, comparison)
│   ├── data/       (손실·존온도 JSON)
│   ├── fluent_trn/ (Fluent 전사로그)
│   └── legacy_mapdl_viz/  (옛 개발 viz: viz_real/aniso/ring)
└── e10/            # e10(=FreeFlow) 모터 결과
    ├── viz/        (형상·오일유동·mapdl/ 하이브리드 대시보드·온도장)
    └── data/       (e10 손실·하이브리드온도·커플드검증 JSON)
```
(코드는 툴/모델별로 repo에, **결과 이미지·GIF·데이터는 위 모델별 폴더에.**
로컬 `viz/`는 gdrive 업로드 후 삭제 — 스크립트로 재생성 가능.)

## 업로드 상태

| 항목 | 위치 | 상태 |
|------|------|------|
| 데이터 JSON (`data/*.json`) | Drive `Prius_thermal_viz/` | ✅ 업로드됨 (Git에도 유지 — 코드 실행용) |
| ├ `prius_losses.json` | Drive | ✅ |
| ├ `fluent_prius_zone_temps.json` | Drive | ✅ |
| ├ `fluent_prius_250A_zone_temps.json` | Drive | ✅ |
| └ `icepak_prius_250A_temps.json` | Drive | ✅ |
| 이미지·GIF (`viz/**`, 47개 20.2MiB) | Drive `Prius_thermal_viz/prius/viz/` | ✅ 업로드됨 (Git 언트랙, 로컬 보존) |

## Git 추적 정책
- **코드**(scripts, thermal_viz.py, README, 이 문서): Git 추적.
- **데이터 JSON**: Git 추적 유지(16KB, 코드 실행용) + Drive 백업.
- **이미지·GIF(`viz/`)**: `.gitignore` 로 Git 미추적. 로컬 디스크 + Drive 에 보관.
  (Git 이력에는 과거 커밋에 남아있어 복구 가능)

## 이미지·GIF 재업로드/동기화 (rclone)
`gdrive:` 리모트 설정됨(rclone v1.74.4, `C:\Users\moa\rclone\`). 재생성 후:
```
rclone copy "D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\prius\viz" gdrive:Prius_thermal_viz/prius/viz
```

## 재생성
산출물은 코드로 언제든 재생성 가능(원본 `.rth` 결과 있을 때):
```
python scripts/render_prius_viz.py all      # 표준 GIF/PNG 세트 전량
```
표준 세트·기법은 `README_prius.md` 참조.
