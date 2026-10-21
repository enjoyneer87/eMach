# thermal_viz 표준 출력 세트

`mlxperPJT/thermal/thermal_viz.py` — 어느 `.rth` 에도 재사용.

```
python thermal_viz.py <file.rth> <out_dir> [label] [clim_lo]      # 범용 CLI
python prius\scripts\render_prius_viz.py all                       # Prius 저/고부하 일괄
python freeflow\scripts\10_mapdl_dashboard_viz.py                  # e10 (FreeFlow 냉각회로 빌더)
```
재료번호 규약: 1 stator · 2 magnet · 3 coil(winding) · 4 shaft · 5 rotor.

## GIF (과도)
| 파일 | 내용 |
|---|---|
| `transient_3d_cut.gif` | 3D 반단면(외피 반쪽 clip + x=0 slice) — 대표 뷰 |
| `transient_dashboard.gif` | 좌: 3d_cut + 열등가회로 오버레이 / 우: 온도이력 + 현재시각 커서 |
| `transient_circuit_3d.gif` | 회로 3D 오버레이(노드색=온도) |
| `transient_core.gif` | z=0 정단면 전 부품 |
| `transient_coilmag.gif` | 코일+자석(코어 고스트) |
| `transient_coil_z0.gif` | 코일 z=0 슬라이스 |

## PNG (최종 t)
`contour_iso`, `contour_z0`, `cut_3d`, `coil_only`, `magnet_only`, `component_history`, `circuit_3d`.

## 알려진 상태
- matplotlib 3.10.8: `thermal_viz.py:456` `matplotlib.cm.get_cmap` 제거 → 회로 오버레이 계열
  (`circuit_3d_png/_gif`, `full_dashboard_gif`)만 실패. 수정: `matplotlib.colormaps[CMAP]`.
- 그림 제목에 한글을 넣으면 일부 환경에서 □□ 로 깨짐(산출 PNG 확인됨) → 제목은 영문 또는 한글 폰트 지정.
- 업로드: `rclone copy <local viz> gdrive:Prius_thermal_viz/<model>/viz` (git 에 이미지 커밋 금지).
