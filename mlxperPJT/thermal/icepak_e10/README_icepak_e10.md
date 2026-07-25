# e10 Icepak 열해석 — 결과 및 근본원인 (2026-07-25)

FreeFlow 오일냉각 모터 **e10**을 Icepak(전도 + 오일냉각)으로 JAC279식 하이브리드를 재현하려는 시도의 최종 정리. **정량 정답은 MAPDL(winding 152°C)** 이며, Icepak은 파이프라인·로터쪽 검증·근본원인 규명까지 도달했다.

프로젝트: `D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt`, 디자인 **`e10_net`**.

## 1. 구축한 것 (파이프라인)
- Maxwell 3D 형상 임포트(358 solids: 스테이터/로터/자석/샤프트/하이핀코일 144), 엔드턴 컷.
- 재료: 코일 **등방성 구리 k387**(type=simple), 스테이터 25, 함침 elan-UP142 k0.13/cp1700/ρ2170.
- 손실(총량, per-body 아님): coil 3350 / stator 585 / rotor 65 / magnet 24 W = 4024W.
- 함침 슬롯충전체 = `슬롯밴드(r71.2~91) − 스테이터 − 코일144` (구리fill 61%). 코일↔스테이터 브리지.
- 하우징(oil jacket): Al링 r99~110, 외면 자켓 84.4°C 고정(MAPDL JACKET 노드 미러).
- 냉각: 오일노드 고정온도 — 자켓84.4 / 스프레이(코일단)91.9 / 갭(로터OD)87 / 샤프트70.3.
- SteadyState·Transient(IcepakTransient dt45s→900s) 둘 다 솔브 성공(is_solved=True).

## 2. 근본원인 (확정) — 다물체 계면 비컨포멀 접촉저항
Icepak이 **임포트/부울로 만든 모든 다물체 계면을 비컨포멀(독립메시)로 처리** → 계면마다 거대한 인공 접촉저항.
**결정적 증거**: 알루미늄 하우징을 스테이터 OD에 부울로 붙였는데 **stator(1185°C) → housing(136°C) 계면 ΔT = 1049°C** (알루미늄 접촉이면 ~5°C여야 함).

그래서 함침(코일↔스테이터), 하우징(스테이터↔자켓), 접촉저항 개념 — **무엇을 해도** 물체간 전도가 필요한 슬롯쪽(coil→함침→stator→housing)은 계면마다 막혀 **winding이 폭주**한다.

## 3. 결과 (SteadyState, 하우징 포함)
| 부품 | Icepak | MAPDL | 판정 |
|---|---|---|---|
| rotor | 87.2 | 86.9 | ✅ (직접 fixT라 물체간 전도 불필요) |
| magnet | 94.5 | 86.9 | ✅ |
| shaft | 70.3 | 84.9 | (고정) |
| **stator** | **1185** | 126 | ❌ 비컨포멀 |
| **coil** | **2058** (steady) / 3080 (transient@900s) | 152 | ❌ 비컨포멀 (구리융점 초과=비물리) |

로터쪽(rotor/magnet/shaft)은 각자 표면에 직접 오일노드 fixT라 물리적. 슬롯쪽은 물체간 전도가 필요해 비컨포멀 저항에 막힘.

## 4. 규명된 pyaedt/Icepak 함정 (재사용 지식)
- **필드 추출**: field plot=`Temperature`, field calculator extremum=`Temp` (둘 다 시도). transient는 Time intrinsic 불안정.
- **Network 부적합**: `AssignNetworkBoundary`가 "Face has mesh on both sides / no hollow objects"로 solver input 실패 → 대류벽/고정온도 BC로 대체.
- **대류벽(HTC)은 TempOnly(유체없음)서 대류flux 미적용** → 고정온도 경계(`assign_stationary_wall_with_temperature`) 사용.
- **EndTip 18개** degenerate 바디가 메셔 크래시 → open마다 재삭제.
- **손실**은 총량 정확(4024W).
- ⚠️ 온도 비교는 **transient끼리·steady끼리** (steady 포화값을 transient 스냅샷과 비교 금지).

## 5. 결론 / 권고
- **정량 winding = MAPDL 152°C 확정** (병합 컨포멀메시라 계면저항 없음).
- Icepak에서 슬롯쪽까지 맞추려면 **물체간 컨포멀 메시 강제(assembly/union) 또는 전 계면 접촉전도 명시** = MAPDL 병합메시를 Icepak서 재구축하는 셈이라 실익 낮음.
- Icepak 성과: 전 파이프라인 블로커 해결 + 로터쪽 MAPDL 일치 + 근본원인 규명.

## 6. 스크립트
드라이버는 `scripts/`(대표본) 및 `../freeflow/scripts/15~18_icepak_e10_*.py`(데스크탑). 결과 JSON은 `../freeflow/data/e10_icepak_*.json`. 시각화는 gdrive `Prius_thermal_viz/e10/viz` + 모델폴더 `D:\KDH\simVary\Ansys_Thermal\e10_thermal_viz`.
