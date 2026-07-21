# Prius 열해석 산출물 위치 (코드=Git / 산출물=Google Drive)

이 패키지는 **코드만 Git(eMach)** 에 두고, **이미지·GIF·데이터는 Google Drive** 에
보관한다. (대용량 GIF ~21MB 로 Git 비대화 방지)

## Google Drive 폴더
**Prius_thermal_viz** — https://drive.google.com/drive/folders/1Kmimyt69kD5a-YhUGLPhj54NR1JdD2tg
(소유: phareal87@gmail.com)

## 업로드 상태

| 항목 | 위치 | 상태 |
|------|------|------|
| 데이터 JSON (`data/*.json`) | Drive 폴더 | ✅ 업로드됨 |
| ├ `prius_losses.json` | Drive | ✅ |
| ├ `fluent_prius_zone_temps.json` | Drive | ✅ |
| ├ `fluent_prius_250A_zone_temps.json` | Drive | ✅ |
| └ `icepak_prius_250A_temps.json` | Drive | ✅ |
| 이미지·GIF (`viz/**`, ~21MB) | Drive 폴더 | ⏳ 수동 업로드 필요 |

## 이미지·GIF 업로드 방법 (택1)
스크립트 환경엔 rclone/gdrive CLI 가 없어 자동 대량업로드 불가. 아래 중 하나:

1. **드래그-드롭(권장, 무설정)**: 브라우저에서 위 Drive 폴더를 열고, 로컬
   `D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\prius\viz\` 의 `waterjacket_low/`,
   `waterjacket_high/`, `comparison/` 폴더를 그대로 끌어다 놓기.
2. **rclone**: `rclone config` 로 gdrive 리모트(예: `gdrive:`) 1회 설정 후
   `rclone copy "D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\prius\viz" gdrive:Prius_thermal_viz/viz`

## 재생성
산출물은 코드로 언제든 재생성 가능(원본 `.rth` 결과 있을 때):
```
python scripts/render_prius_viz.py all      # 표준 GIF/PNG 세트 전량
```
표준 세트·기법은 `README_prius.md` 참조.
