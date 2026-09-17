# 인계 — 고속 저토크 운전점의 실제 진각

PC2 작성, 2026-09-17. **Motor-CAD Lab 포화맵을 이미 만들어 둔 로컬에서 이어받을 것.**
같은 폴더의 `loss_torque_convention.html`(손실의 토크 귀속 규약)과 짝입니다.

---

## 1. 풀려는 질문

교류 동손을 고려했을 때 **고속 저토크 운전점의 실제 진각이 몇 도인가.**

배경은 이렇습니다. 헤어핀 권선이라 교류 동손이 직류손의 72 %에 이르고(16 krpm·460 A 실측),
`k_ac`가 전류에 따라 10 % 움직입니다. 그래서 동손만 보는 MTPA와 총손실 최소가 서로 다른 각을 줍니다.
그 차이가 전류맵을 다시 짤 만한 크기인지가 판단 기준입니다.

---

## 2. 지금까지 확정된 것

### 2.1 전압 제한이 답을 거의 결정한다

| 항목 | 값 |
|---|---|
| 직류단 전압 | 720 V |
| 상전압 한계 (SVPWM 선형) | 415.7 V |
| 16 krpm 전기 주파수 | 1066.7 Hz |
| 16 krpm 전기 각속도 | 6702 rad/s |
| **쇄교자속 한계** | **62.0 mWb** |

무부하 쇄교자속이 약 210 mWb라 16 krpm에서는 그 29 %까지 약자속해야 합니다.
무부하 기저속도는 약 4700 rpm이므로 3.4배 구간입니다.

### 2.2 Full-FEA 배치의 36도 점은 운전 궤적이 아니다

`ipmfea/jobs/r2_fullfea/results_pc2_sd/`의 6점(4/8/16 krpm × 230/460 A × 36도)은
**손실 비교용 고정 격자**입니다. 전압 제한을 검사하지 않습니다.
실제로 16 krpm·50 A·45도 한 점의 쇄교자속이 252.6 mWb로 한계의 4배가 넘습니다.
16 krpm·460 A에서 899 N·m이면 기계 출력 1.5 MW라 720 V 버스로는 불가능합니다.
**이 격자의 진각 36도를 운전점으로 인용하면 안 됩니다.**

### 2.3 Motor-CAD Lab 첫 결과 (PC2, 2026-09-17)

대상은 `ipmfea/jobs/r2_fullfea/results_pc2_sd/R1_0167/e10_adapt.mot`
(슬롯 깊이 고정본, 최소 체적 대표 설계)입니다.

**스윕 완료.** 전체 결과는 같은 폴더의 `gamma_highspeed_result.md` 를 볼 것.

| 요구 토크 | 축 토크 | 진각 | 상전류 RMS | Id (peak) | 효율 |
|---|---|---|---|---|---|
| 1 N·m | 1.0 | **89.60°** | 138.9 A | −196.4 A | 9.4 % |
| 12 | 12.0 | 88.99° | 140.8 A | −199.0 A | 55.1 % |
| 50 | 50.0 | 87.21° | 156.4 A | −220.9 A | 81.6 % |
| 100 이상 | **84.3** | 86.75° | 203.7 A | −287.6 A | 83.3 % |

가용 토크 전 범위에서 진각이 86.75° ~ 89.60° 로 90°에서 3.3° 안쪽입니다.
토크 1 N·m 에서도 138.9 A 가 흐르고 거의 전부 −d축이며, 이것이 특성전류(약 196 A peak)입니다.
**16 krpm 최대 토크는 84.3 N·m** 이고 전압 제한에 걸립니다(전류 203.7 A, 한계 500 A).

이로써 2.2 절이 확정됩니다. 손실 격자의 16 krpm·460 A·36° 점이 899 N·m 인데
실제 한계가 84.3 N·m 이라 10배 이상 차이납니다.

**다만 원래 질문은 아직 미결입니다.** 이 스윕은 Lab 기본 손실 설정으로 돌렸고
`ACLossMethod_Lab = 0` 의 의미를 확인하지 못했습니다. 4절 나 항목이 남은 핵심입니다.
위 표가 그 비교의 기준선입니다.

---

## 3. PC2에서 막힌 지점

Lab 모델 생성(`build_model_lab`)에 **26분**이 걸립니다(해상도 축소 후).
기본 해상도(전류 6 × 진각 5 × 속도 4)로는 28분 제한 안에 끝나지 않아 한 번 중단됐습니다.

**포화맵을 이미 만들어 둔 로컬이라면 이 26분을 건너뛸 수 있습니다.** 그것이 인계하는 이유입니다.

### PC2가 쓴 설정

```python
mc.set_motorlab_context()
mc.set_variable("ModelBuildPoints_Current_Lab", 5)   # 기본 6
mc.set_variable("ModelBuildPoints_Gamma_Lab", 5)     # 기본 5
mc.set_variable("ModelBuildPoints_Speed_Lab", 2)     # 기본 4
mc.set_variable("SatModelPoints_MotorLAB", 0)
mc.build_model_lab()

mc.set_variable("OperatingMode_Lab", 0)              # motor
mc.set_variable("OpPointSpec_MotorLAB", 0)
mc.set_variable("EmagneticCalcType_Lab", 0)
mc.set_variable("StatorCurrentDemand_RMS_Lab", 500.0)
mc.set_variable("SpeedDemand_MotorLAB", 16000.0)
mc.set_variable("TorqueDemand_MotorLAB", T)
mc.calculate_operating_point_lab()
```

읽을 출력 변수:

```
LabOpPoint_ShaftTorque, LabOpPoint_PhaseAdvance, LabOpPoint_StatorCurrent_Phase_RMS,
LabOpPoint_PhaseCurrent_D_Peak, LabOpPoint_PhaseCurrent_Q_Peak,
LabOpPoint_Efficiency, LabOpPoint_Efficiency_Motor, LabOpPoint_Frequency
```

전체 스크립트는 PC2의 `scratchpad/lab2.py`에 있고, 아래 5절에 요지를 옮겨 두었습니다.

---

## 4. 이어서 할 일

### 가. 토크 스윕 완성 (Lab)

16 krpm에서 토크를 1부터 최대까지 훑어 진각 곡선을 그립니다.
저토크 쪽을 촘촘히 하십시오(1, 2, 3, 5, 8, 12, 20, 30, 50, 80, 120, 200, 300 N·m).
16 krpm에서 낼 수 있는 최대 토크도 함께 기록하십시오.

### 나. 손실 모델을 바꿔 가며 비교 — 이것이 핵심

Lab의 기본 설정은 `ACLossMethod_Lab = 0`입니다. 이 값이 해석식인지 Full-FEA 맵인지 확인하십시오.
Motor-CAD v261에는 **Full-FEA 교류 손실 맵** 기능이 있습니다.

| 변수 | 기본값 | 뜻 |
|---|---|---|
| `ACLossMethod_Lab` | 0 | 교류 손실 계산 방법 |
| `ACLossModelBuildPoints_Current_Lab` | 4 | 전류 점 수 |
| `ACLossModelBuildPoints_Gamma_Lab` | 4 | 진각 점 수 |
| `ACLossModelBuildPoints_Speed_Lab` | 4 | 속도 점 수 |
| `ACLossMap_FullFEA_ExtrapMethod_Lab` | 1 | 맵 밖 외삽 |

같은 토크 점에서 교류 손실을 끈 경우, 해석식인 경우, Full-FEA 맵인 경우
**세 가지 진각을 비교**하십시오. 그 차이가 이 작업의 결론입니다.

### 다. PC2 실측과 대조

`ipmfea/jobs/r2_fullfea/results_pc2_sd/fullfea.csv`에 R1_0167의 6점이 있습니다.
Lab이 같은 (속도, 전류, 진각)에서 내는 교류 동손과 대조하면 Lab 모델의 정확도가 나옵니다.
PC2 실측 앵커는 이렇습니다.

| 16 krpm | 직류 동손(활성부) | 교류 초과분 | k_ac |
|---|---|---|---|
| 230.1 A | 10.35 kW | 9.47 kW | 1.916 |
| 460.1 A | 41.39 kW | 30.02 kW | 1.725 |

지수는 속도 1.832, 전류 1.732입니다(`ipmfea/src/ipmfea/data/ac_ratio_models.json`의 `fea_exponents`).
이상적 제곱(2.0)에서 벗어나는 것은 표피 효과 때문입니다.

### 라. 무부하 성분 분리 (선택)

전류 0, 16 krpm, `ProximityLossModel = 3`으로 Full-FEA 한 점(약 10분)을 돌리면
무부하 도체 와전류손이 나옵니다. 이것이 제동토크 성분이고, 나머지 교류 동손은 아닙니다.
근거는 `loss_torque_convention.html` 2절과 3절입니다.

---

## 5. 참고 스크립트 요지

```python
import ansys.motorcad.core as pymotorcad
mc = pymotorcad.MotorCAD(open_new_instance=True, enable_success_variable=False)
mc.set_variable("MessageDisplayState", 2)      # 팝업 억제
mc.load_from_file(mot)
mc.set_motorlab_context()
# 포화맵이 이미 있으면 build_model_lab() 생략 가능 — get_model_built_lab() 로 확인
if not mc.get_model_built_lab():
    mc.build_model_lab()
for T in (1, 2, 3, 5, 8, 12, 20, 30, 50, 80, 120, 200, 300):
    mc.set_variable("SpeedDemand_MotorLAB", 16000.0)
    mc.set_variable("TorqueDemand_MotorLAB", float(T))
    mc.calculate_operating_point_lab()
    print(T, mc.get_variable("LabOpPoint_PhaseAdvance"),
             mc.get_variable("LabOpPoint_StatorCurrent_Phase_RMS"))
mc.quit()
```

**공용 PC 주의.** Motor-CAD 프로세스를 이미지 이름으로 일괄 종료하지 마십시오.
다른 사람이 열어 둔 창이 함께 죽습니다. 반드시 PID로 관리하십시오.

---

## 6. 산출물

- 16 krpm 진각 대 토크 곡선 (교류 손실 설정 3종 비교)
- 같은 점에서의 상전류와 d·q 성분
- PC2 Full-FEA 실측 대비 Lab 교류 동손 오차
- 결론: 교류 동손을 제대로 넣으면 진각이 몇 도 움직이는가, 전류맵을 다시 짤 만한가

결과는 이 폴더에 `gamma_highspeed_result.md`로 정리하고 같은 브랜치에 커밋하십시오.
