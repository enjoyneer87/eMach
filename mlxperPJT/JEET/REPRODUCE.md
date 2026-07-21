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
| Fig 2 | 슬롯 내 전류 쏠림(TS-FEA vs Hybrid 참고, TS-FEA 도체 메시 공유) | `run_fig2_slot.py` | `plot_fig2_slot_comparison`, `make_fig2_slot_gif`, `hybrid_je_at_points` | `fig2_slot_je_static_data.json`, GIF·요약은 Drive (`fig2_slot_je_MANIFEST.md` 참조) |
| Fig 2 보조 | 슬롯 내부 **전체 메시** \|B\| (TS-FEA vs MS-FEA, 각자 자기 메시) | `run_fig2_slot.py --only-b` | `plot_fig_b_slot_comparison`, `make_fig_b_slot_gif` | `fig2_slot_b_static_data.json`, GIF·요약은 Drive |
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

6. **`.mes` 는 바이너리다.** 텍스트 표를 얻으려면 COM 세션에서
   `prepare_fea_export_session` + `get_magnetic_data` 를 거쳐야 한다
   (`run_field_export.py`). `pyMCAD` 는 `tools/motorCAD` 아래 있으므로
   그 경로도 `sys.path` 에 넣어야 import 된다.

7. **전 주기 export 는 Solution 블록이 128개 이어 붙는다** (파일 364 MB).
   `parse_mes_txt(path)` (인자 없이) 는 각 표의 **처음** 등장만 취해
   Solution 1 (Rotate Step 0) 을 읽는다 — 마지막을 취하면 다른 회전자
   위치의 값이 조용히 섞여 층별 |B| 가 최대 25% 어긋난다(실제로 겪음).
   특정 스텝이 필요하면 `parse_mes_txt(path, block=k)`, 전체를 훑으려면
   `iter_mes_blocks(path)` 를 쓸 것. 반환 dict 의 `n_solution_blocks` 로
   블록 수를 확인할 수 있고, 단일 스텝만 보관할 때는 첫 블록만 남기면
   2--3 MB 로 줄어 Ref/SC 추출본과 크기가 맞는다.

8. **`Je`(와전류밀도)는 Rotate Step 0(블록 1)에서 항상 0이다.** 아직
   와전류가 발달하지 않은 시작 스냅샷이기 때문 --- 버그가 아니다. 실제
   유도 전류 분포가 필요하면(전류 쏠림 시각화 등) `block>=2` 를 쓸 것.
   전역 최댓값 스텝은 모델·운전점마다 다르므로(이 사례는 128 중
   step 70) 몇 개만 샘플링하지 말고 전체를 스캔해 확인할 것 --- 10점
   샘플링으로 고른 "최댓값"이 실제 전역 최댓값을 놓친 적이 있다.

9. **`run_field_export.py` 의 자동 태그는 모델·속도·위상만으로 만들어져
   전류값과 --step 번호를 반영하지 않으면 서로 다른 진단 실행이 같은
   파일명으로 충돌해 캐노니컬 추출본을 조용히 덮어쓴다**(실제로 두 번
   겪음 --- 처음은 solution 종류 누락, 이번엔 step 번호 누락으로 Table 4
   가 참조하는 `Magnetic_Ref_16k_36deg_OnLoadTorque.txt` 가 덮어써졌다가
   `git checkout --` 으로 복구함). 지금은 전류·step 이 태그에 포함되도록
   고쳤지만, 캐노니컬 파일을 건드릴 가능성이 있는 진단 실행은 항상
   `--tag` 로 명시적인 이름을 줄 것.

10. **Hybrid(MS-FEA) 도체 영역은 아카이브 .mes 와 명명 규칙이 다르다.**
    아카이브: `Turn_<층>_<슬롯>`. 실시간 COM export: `ArmatureSlot<층
    문자><슬롯숫자>`(문자가 층, 숫자가 슬롯 --- 반대로 착각하기 쉽다).
    `slot_conductor_codes()` 가 두 규칙을 모두 인식하므로 대부분은 이
    함수만 쓰면 되지만, 새 명명 변형을 만나면 반경(r) 기준으로 어느
    쪽이 층/슬롯인지 먼저 검증할 것(문자·숫자 각각으로 그룹핑해 반경
    분산이 0에 가까운 쪽이 "층").

11. **Hybrid 참고 재구성은 두 가지 평가 방식이 있다** —
    `hybrid_je_reference(p, ...)` 는 *그 데이터셋 자신의* 도체 요소에서,
    `hybrid_je_at_points(p_source, query_xy, ...)` 는 **임의의 좌표**에서
    평가한다. 물리(층별 1-D 경계값 문제)는 둘이 동일하며 평가 지점만
    다르다. Fig 2 는 후자를 쓴다 --- Hybrid 자신의(더 거칠거나
    이상화된) 메시가 아니라 TS-FEA 의 실제 도체 메시 좌표를 넘겨서,
    두 패널이 같은 형상(도메인) 위에 그려지고 Hybrid 쪽 메시 모양이
    그림에 드러나지 않게 한다.

12. **B 에서 Je 를 역산할 때 세 가지를 틀리기 쉽다** (Fig 2 에서 실제로
    셋 다 겪었고, 증상은 "Hybrid 패널만 공극이 반대쪽에 있는 것처럼
    보인다"였다):

    - **스택 전체를 한 슬랩으로 풀면 안 된다.** 도체는 서로 절연돼
      있어 와전류가 각 바 안에서 순환한다. 6층 스택(약 11.6 mm =
      5 delta)을 하나로 잡으면 양 끝면에만 부호 반대인 큰 J 가 서고
      가운데가 0 이 되어 위아래가 뒤집힌 그림이 나온다. **층마다** 풀 것.
    - **경계 H 는 `|B|` 가 아니라 부호 있는 접선 성분** `B_theta =
      (-y·Bx + x·By)/r` 로 잡을 것. 슬롯 누설 접선장은 스택을 가로지르며
      부호가 바뀌는데(공극쪽 음 --> 슬롯바닥쪽 양), 크기만 취하면 중간
      층에서 기울기의 부호·크기가 모두 틀어진다.
    - **경계값을 반경 최소/최대 "단일 요소"에서 읽지 말 것.** 슬롯바닥
      층은 배후철심에 접한 요소 하나가 반경 성분 때문에 `|B|` 를
      0.24 --> 0.88 T 로 부풀려 그 층에만 다른 층의 4--9배짜리 가짜
      기울기를 만든다. 각 면에서 두께의 20% 이내 요소 평균을 쓸 것.

    검산 방법: **TS-FEA 의 `Je` 열은 층 평균이 0 이다**(유도 성분만 담고
    전송 전류는 `J` 열에 있음). 재구성값도 층 평균을 빼서 같은 정의로
    맞춰야 비교가 성립한다 --- 빼지 않으면 균일한 전송 성분이 층 전체를
    한 가지 색으로 덮어 쏠림이 보이지 않는다.

13. **B 그림은 도체가 아니라 슬롯 내부 전체 메시로 그린다.** B 는 도체
    밖에도 존재하므로 `_slot_frame(..., domain='slot')` 이 함침
    (`Impreg_LossSlot`)·웨지(`StatorWedge`)·슬롯공기(`StatorAir`) 까지
    포함한다. 철심(`Stator`, |B|~1.6 T)은 반드시 제외할 것 --- 넣으면
    슬롯 내부(0~0.6 T)가 전부 한 색으로 뭉갠다. 또 **MS-FEA 모델에는
    함침 영역이 아예 없다**(도체 + 웨지 + 공기뿐). 그래서 B 그림은 Je
    그림과 달리 각 패널을 자기 메시에 그린다 --- 두 해석 모두 자기
    메시에서 실제로 푼 값이라 그편이 정직하고, MS-FEA 슬롯 모델이
    이상화돼 있다는 점도 함께 드러난다.

## 검증된 교차 확인

| 항목 | 독립 경로 A | 독립 경로 B | 일치 |
|---|---|---|---|
| Ref $R_{active}$ | `.mot` 78.56−29.08 = 49.48 mΩ | 도체면적·도전율 손계산 49.5 mΩ | ✓ |
| 도체 온도 | `.mot` 80 °C | `.mes` 도전율 → 79 °C | ✓ |
| Ref $T_{em}$ | Motor-CAD `AvTorqueMS` 807.05 Nm | 공극 Maxwell 적분 817.66 Nm | 1.3% |
| SC $T_{em}$ | Motor-CAD 3284.29 Nm | 공극 Maxwell 적분 3267.88 Nm | 0.5% |
| $\vec{B}$ 보존 | Ref 층별 $|B|$ | SC 층별 $|B|$ | 0.1% |
| 슬롯 번호 대응(Turn_ vs ArmatureSlot) | TS-FEA 슬롯1 각도 −3.75° | Hybrid 슬롯1 각도 −3.79° | 물리적으로 같은 슬롯 |
| 슬롯1 도체 층평균 \|B\| (step 70) | TS-FEA 0.2769 T | MS-FEA 0.2658 T | 4.0% (층별로는 최대 30%) |

> 위 \|B\| 비교는 **도체 영역에서만** 해야 한다. 슬롯 내부 전체로 평균을
> 내면 MS-FEA 가 26% 높게 나오는데, 이는 물리가 아니라 MS-FEA 모델에
> 함침 영역(저자장)이 없어 평균 대상 요소 집합이 다르기 때문이다
> (주의사항 13). 두 해석의 B 가 도체에서 4% 내로 일치한다는 점이
> MS-FEA 의 B 로부터 Je 를 역산하는 근거가 된다.

## 미완

- HalfSC 690 A 의 요소 단위 필드(.mes)는 원본 폴더
  (`D:\KDH\simVary\...\690tier`) 가 삭제되어 남아 있지 않다. 손실
  데이터셋에는 690 A 12점이 정상 보존되어 있으므로, $B_g$·$B_{Cu}$ 가
  필요하면 해당 1점을 재실행해 .mes 를 다시 내보내야 한다.
- HalfSC 의 LAB 저항은 모델에서 재빌드가 필요하다 (위 주의사항 1).
