# JEET 논문 결과 재현 안내

논문의 표·그림을 만든 코드와 데이터의 대응표. 모든 산출 코드는
`eMach/tools/jeet_acloss_rbf/` 패키지에 있고, 실행 스크립트는 이 폴더에
있으며, 산출 데이터는 JSON 으로 Google Drive
(`J:\내 드라이브\EveryMotor_JEET_data\results\`) 에 보존한다.

```python
import sys; sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")
from jeet_acloss_rbf import AcLossPipeline, loading_metrics, parse_mes_txt
```

## 논문 산출물 → 코드 대응

| 논문 | 내용 | 실행 스크립트 | 패키지 함수 | 산출 JSON |
|---|---|---|---|---|
| Fig 7 | 스칼라 vs 멱지수 수렴 | `run_manuscript_figs78.py` | `plot_form_convergence` | --- |
| Fig 8 | 전달 플랜 절제 히트맵 | `run_manuscript_figs78.py` | `plot_transfer_ablation` | --- |
| Fig 9 | 모터 단면 기하 | `run_geometry_fig.py` | `plot_motor_geometry_dxf` | `geometry_dims_e10.json` |
| Fig 13 | 보정 검증 parity/box | 노트북 `JEET_AF_Pipeline.ipynb` | `AcLossPipeline.make_validation_figure` | --- |
| Table 2 | 보정 형태 비교 | `run_form_study.py` | `run_form_study` | `form_study.json` |
| Table 3 | 주요 치수 | `run_geometry_fig.py` | `plot_motor_geometry_dxf` (반환값) | `geometry_dims_e10.json` |
| Table 4 | Ref/SC 부하 지표 | `run_loading_metrics.py` | `loading_metrics`, `read_mot`, `winding_losses` | `loading_metrics_6turn.json` |
| Table 4 | $T_{em}$ 검증 | `run_torque_check.py` | `maxwell_torque` + Motor-CAD COM | `torque_check_6turn.json` |
| Table 5 | 비용·정확도 | (실측 시간 + `metrics`) | `AcLossPipeline.metrics` | --- |
| §4.2 | 예산-정확도 파레토 | `run_cost_accuracy.py` | `sweep_cost_accuracy` | `cost_accuracy.json` |

## 원자료 위치

| 자료 | 경로 | 비고 |
|---|---|---|
| AC 손실 데이터셋 | `map_exports/e10/{Ref,HalfSC,SC}/*_Map_Summary.json` | 모델별 120 운전점 |
| 요소 단위 필드 (.mes 텍스트) | `map_exports/e10/fields/Magnetic_*.txt` | Ref·SC 만 (16 kRPM, $\beta$=36°) |
| Motor-CAD 모델 | `D:\KangDH\Thesis\e10\{refModel,SLFEA,SLFEA_Half}\*.mot` | 6턴·1병렬 |
| 2-D 단면 DXF | `D:\KangDH\Thesis\e10\e10_2d.dxf` | Fig 9 원본 |

## 주의사항 (실제로 겪은 함정)

1. **`.mot` 의 파생 출력은 낡을 수 있다.** `RMSCurrentDensity`,
   `Resistance_MotorLAB` 는 Motor-CAD 가 재계산할 때만 갱신된다. 4턴·8턴
   파일은 6턴 값을 그대로 갖고 있으므로 도체 면적으로 교차 확인할 것.
   HalfSC 파일의 저항은 계산값의 정확히 1/4 (2병렬 시절 잔재로 추정).

2. **`Turn_<층>_<슬롯>`** — 첫 인덱스가 반경 방향 층이다. 두 번째로
   묶으면 모든 그룹이 같은 반경대를 갖는 이상한 결과가 나온다.

3. **공극은 여러 층으로 메시된다** (`a1` 은 고정자측, `a2`~ 는 회전자측).
   층 두께는 요소 중심 퍼짐이 아니라 `면적/(각도폭×반경)` 으로 구해야
   한다 --- 중심 퍼짐은 요소 크기만큼 과소평가되어 토크를 부풀린다.

4. **모델은 45°(1극) 섹터**지만 회전자가 돌아간 상태라 요소 전체의
   각도 범위는 45°보다 넓게 보인다. 섹터 배수는 고정자 영역 기준으로
   판정한다 (`maxwell_torque` 가 자동 처리).

5. **LAB 저항 재빌드는 자기 해석과 별개**이며 오래 걸린다.
   `do_magnetic_calculation()` 은 `Resistance_MotorLAB` 을 갱신하지 않는다.

## 검증된 교차 확인

| 항목 | 독립 경로 A | 독립 경로 B | 일치 |
|---|---|---|---|
| Ref $R_{active}$ | `.mot` 78.56−29.08 = 49.48 mΩ | 도체면적·도전율 손계산 49.5 mΩ | ✓ |
| 도체 온도 | `.mot` 80 °C | `.mes` 도전율 → 79 °C | ✓ |
| Ref $T_{em}$ | Motor-CAD `AvTorqueMS` 807.05 Nm | 공극 Maxwell 적분 817.66 Nm | 1.3% |
| SC $T_{em}$ | Motor-CAD 3284.29 Nm | 공극 Maxwell 적분 3267.88 Nm | 0.5% |
| $\vec{B}$ 보존 | Ref 층별 $|B|$ | SC 층별 $|B|$ | 0.1% |

## 미완

- HalfSC 690 A 의 요소 단위 필드(.mes)는 원본 폴더
  (`D:\KDH\simVary\...\690tier`) 가 삭제되어 남아 있지 않다. 손실
  데이터셋에는 690 A 12점이 정상 보존되어 있으므로, $B_g$·$B_{Cu}$ 가
  필요하면 해당 1점을 재실행해 .mes 를 다시 내보내야 한다.
- HalfSC 의 LAB 저항은 모델에서 재빌드가 필요하다 (위 주의사항 1).
