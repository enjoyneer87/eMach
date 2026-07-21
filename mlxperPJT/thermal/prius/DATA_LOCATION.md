# Prius 열해석 산출물 위치 (코드=Git / 산출물=Google Drive)

이 패키지는 **코드만 Git(eMach)** 에 두고, **이미지·GIF·데이터는 Google Drive** 에
보관한다. (대용량 GIF ~21MB 로 Git 비대화 방지)

## Google Drive 폴더
**Prius_thermal_viz** — https://drive.google.com/drive/folders/1Kmimyt69kD5a-YhUGLPhj54NR1JdD2tg
(소유: phareal87@gmail.com)

## 업로드 상태

| 항목 | 위치 | 상태 |
|------|------|------|
| 데이터 JSON (`data/*.json`) | Drive `Prius_thermal_viz/` | ✅ 업로드됨 (Git에도 유지 — 코드 실행용) |
| ├ `prius_losses.json` | Drive | ✅ |
| ├ `fluent_prius_zone_temps.json` | Drive | ✅ |
| ├ `fluent_prius_250A_zone_temps.json` | Drive | ✅ |
| └ `icepak_prius_250A_temps.json` | Drive | ✅ |
| 이미지·GIF (`viz/**`, 47개 20.2MiB) | Drive `Prius_thermal_viz/viz/` | ✅ 업로드됨 (Git 언트랙, 로컬 보존) |

## Git 추적 정책
- **코드**(scripts, thermal_viz.py, README, 이 문서): Git 추적.
- **데이터 JSON**: Git 추적 유지(16KB, 코드 실행용) + Drive 백업.
- **이미지·GIF(`viz/`)**: `.gitignore` 로 Git 미추적. 로컬 디스크 + Drive 에 보관.
  (Git 이력에는 과거 커밋에 남아있어 복구 가능)

## 이미지·GIF 재업로드/동기화 (rclone)
`gdrive:` 리모트 설정됨(rclone v1.74.4, `C:\Users\moa\rclone\`). 재생성 후:
```
rclone copy "D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\prius\viz" gdrive:Prius_thermal_viz/viz
```

## 재생성
산출물은 코드로 언제든 재생성 가능(원본 `.rth` 결과 있을 때):
```
python scripts/render_prius_viz.py all      # 표준 GIF/PNG 세트 전량
```
표준 세트·기법은 `README_prius.md` 참조.
