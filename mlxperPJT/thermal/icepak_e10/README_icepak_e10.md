# e10 Icepak 열해석 — 권선 폭주 해결 및 MAPDL 교차검증 (2026-07-26)

FreeFlow 오일냉각 모터 **e10**을 Icepak(FVM 전도 + 오일냉각 열등가회로)으로 JAC279식 하이브리드를 재현하고, **MAPDL(FEM)과 같은 모델·조건·시간스케일에서 교차검증**한 최종 정리.

> **결론(요지):** 초기의 권선 폭주(2000~3000°C)는 **비물리 아티팩트가 아니라 다물체 계면 비컨포멀 접촉** 때문이었고, **권선을 네이티브-카브 균질체(band−stator)로 만들어 스테이터에 컨포멀**하게 하고 **냉각을 (동작 안 하는 Network 대신) 대류벽(HTC)으로** 걸면 **정상화**된다. Icepak transient@900s **권선 136.5°C**로 **MAPDL 152.2°C와 10% 이내 일치**. 반면 **discrete 구리바(Maxwell import)는 함침을 carve해도 여전히 비컨포멀 → 폭주(2376°C, 비물리)**.

프로젝트: `D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt`
- 디자인 **`e10_net`** = **V1 (균질 k5 권선)**, **`e10bars*`** = **V2 (discrete 구리바)**.

---

## 1. 두 버전 (사용자 요청: 같은 모델·조건, FEM/FVM 솔리드 + 열등가회로, 둘 다 transient, 비교)

| | V1 (균질) | V2 (discrete) |
|---|---|---|
| 권선 | 슬롯밴드(r71.2~91) **− 스테이터** 네이티브 카브, **k5 균질**(cp385/ρ4480, MAPDL 미러) | Maxwell 144 하이핀 **구리바 k387** import + 함침 elan k0.13 |
| 계면 | 카브로 스테이터면 coincident → **컨포멀** | 함침=밴드−스테이터−코일 carve, 하지만 **코일이 imported → 비컨포멀** |
| 냉각 | **대류벽(HTC)** = MAPDL 오일노드온도 ref | 동일 |
| 결과 | **✅ 권선 136.5°C (물리적)** | **❌ 폭주 2376°C (비물리)** |

두 버전이 함께 규명한 것: **권선 유효화는 "네이티브 균질화(컨포멀)"로만 되고, imported discrete 바디는 carve로도 컨포멀이 안 된다** = MAPDL이 병합 컨포멀메시라 문제없는 것과 정확히 대응.

## 2. 냉각 = 동적 오일회로의 Icepak 구현 (Network → 대류벽)
MAPDL 회로는 **SURF152 대류(h·A)로 solid 표면 → 오일 extra-node + COMBIN14 컨덕턴스(G) + MASS71 열용량(C) + OIL 70°C 고정**. 즉 표면은 **Robin(대류)** 결합, 오일노드는 준정상(τ=C/G≈2.5s ≪ 900s).

- **Icepak Network 경계는 전도-only 모델에서 solver input 생성 실패** (`"Failed to generate solver input file 1" → Engine Detected Error`, 메싱은 성공). 데스크탑·VSCode 양쪽 2회 확정 → **폐기**.
- 대신 **`assign_stationary_wall_with_htc(faces, htc, ref_temperature)`** 로 MAPDL 오일노드온도를 ref로 하는 **대류벽**을 각 냉각면에 부여 → `analyze:True`/`is_solved:True`로 **풀리고 냉각됨**. τ_oil≪900s라 준정상 오일온도 고정은 동적회로와 물리적으로 등가.

오일노드 ref/htc (MAPDL 수렴값): JACKET 84.4/1000 · SPRAY 91.9/2000 · GAP_S 122.3/1e4 · GAP_R 87.0/1e4 · SHF 70.3/250 · ROTEND 70/250.

## 3. 결과 (transient@900s, 부품별 max) — `viz/comparison/e10_mapdl_icepak_3way.png`
| 부품 | MAPDL(FEM) | Icepak V1(FVM 균질) | Δ | 판정 |
|---|---|---|---|---|
| **권선** | **152.2** | **136.5** | −15.7 (10%) | ✅ 해결(폭주 2058~3080 → 136.5) |
| 스테이터 | 126.0 | 133.7 | +7.7 | ✅ |
| 샤프트 | 84.9 | 90.0 | +5.1 | ✅ |
| 로터 | 86.9 | 128.7 | +41.8 | ⚠️ magnet↔rotor imported 비컨포멀 |
| 자석 | 86.9 | 105.4 | +18.5 | ⚠️ 〃 |

- 권선 max 차 −16°C: MAPDL은 엔드턴(스택 밖) 국소 hotspot 포함, V1 균질체는 스택길이 annulus라 peak가 완만.
- **로터/자석**은 V1에서 권선만 컨포멀화하고 magnet↔rotor(imported)는 비컨포멀로 남겨 자석열이 갇힘 → 컨포멀 수정의 효과가 대비로 드러남.
- **V2**: 코일 2376 / 스테이터 4726(열원 초과=비물리·non-converged) / 로터 2498 → discrete 비컨포멀 메시가 무효 해. **정량 무의미, "실패" 자체가 결과.**

## 4. pyaedt/Icepak 함정 (재사용 지식, 갱신)
- **Network 경계**: 전도-only서 `AssignNetworkBoundary` → solver input 생성 실패. **대류벽(HTC)로 대체**.
- **대류벽 냉각 조건**: 공기 **Region 제거**(냉각면을 외부면으로) + `assign_stationary_wall_with_htc`. Region 있으면 내부면(양쪽 메시)이라 냉각 안 됨.
- **필드 추출**: field calculator extremum=`Temp`/`Temperature` 둘 다 시도. **코일 리스트 통째 1콜은 None** → 바 샘플링(모든 바 개별쿼리는 매우 느림, ~20바 샘플로 max).
- **Maxwell 디자인 열기**: `Maxwell3d(...)`는 동일명 4-타입 프로젝트서 `TypeError: __init__ should return None, not bool` → **`get_pyaedt_app(project_name, design_name)`** (타입 자동감지) 사용.
- **디자인 삭제 후 동일명 재생성 → `modeler is None`** (조용한 실패). **유니크명**(타임스탬프)으로 생성할 것.
- **discrete 하이핀 메시불가**: 144바 엔드턴이 39264 planar facet → 메싱 40분+ 정체(13GB, 결과 미기록). **엔드턴 z±75 클립**(subtract 박스)하면 active 바만 남아 풀림(그래도 결과는 비컨포멀 폭주).
- **손실**: 총량 정확(coil3350/stator585/rotor65/magnet24 = 4024W).
- **비교 규칙**: transient끼리·steady끼리. (V1 transient@900s는 포화=steady와 동일 136.5.)

## 5. 스크립트/데이터
- 드라이버(scratchpad): `e10_ipk_v1b_htc.py`(V1 대류벽 steady 검증), `e10_ipk_v1c_trans.py`(V1 transient), `e10_ipk_v2_bars.py`(V2 빌드: Maxwell 코일복사+클립+함침+대류벽), `e10_v2_extract.py`(V2 추출).
- 비교 viz: `freeflow/scripts/19_e10_mapdl_icepak_compare.py` → `freeflow/viz/comparison/e10_mapdl_icepak_3way.png`.
- 결과 JSON: `freeflow/data/e10_icepak_v1_homog.json`(V1), `e10_icepak_v2_bars.json`(V2), `ff_mapdl_hybrid_temps.json`(MAPDL).
- 필드 PNG/GIF: `freeflow/viz/icepak/V1/`.

## 6. 권고
- **정량 권선 = Icepak V1 136.5°C ≈ MAPDL 152°C 교차검증 완료** (10% 이내). 슬롯측 Icepak 유효 모델 = **네이티브 균질 권선 + 대류벽 오일회로**.
- discrete 바 해상은 Icepak 전도해석서 실익 없음(비컨포멀·메시비용). 필요시 MAPDL 병합메시.
- (개선여지) 로터/자석까지 맞추려면 magnet도 rotor에서 카브해 컨포멀화. 중력벡터 반경방향 수정(핸드오프 §10-4)은 미적용.
