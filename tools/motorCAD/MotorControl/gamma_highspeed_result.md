# 고속 저토크 진각 — 결과

인계 문서 `HANDOFF_gamma_highspeed.md` 4절의 결과입니다. 짝 문서는 `loss_torque_convention.html`.
A 절은 PC2 의 1차 결과(R1_0167), B 절은 PC1 회신입니다. 두 PC 가 같은 파일을 쓰므로
**자기 절 안에만 적고 상대 절은 건드리지 않습니다.**

> **상태 (2026-09-17, PC1): 계산 진행 중.** B 절의 표와 그림은 스윕이 끝나는 대로 채웁니다.

---

## A. PC2 1차 결과 — 16 krpm 진각 대 토크 (R1_0167)

PC2, 2026-09-17. Motor-CAD 2026 R1 Lab. 대상 `R1_0167` 슬롯 깊이 고정본.
인계 문서 `HANDOFF_gamma_highspeed.md` 4절 가 항목의 결과입니다.

---

### A1. 스윕 결과

16 krpm, 직류단 720 V, 전류 한계 500 A rms.

| 요구 토크 | 축 토크 | 진각 | 상전류 RMS | Id (peak) | Iq (peak) | 효율 |
|---|---|---|---|---|---|---|
| 1 N·m | 1.0 | **89.60°** | 138.9 A | −196.4 A | 1.38 A | 9.4 % |
| 3 | 3.0 | 89.48° | 139.2 A | −196.8 A | 1.77 A | 23.7 % |
| 6 | 6.0 | 89.32° | 139.6 A | −197.4 A | 2.35 A | 38.2 % |
| 12 | 12.0 | 88.99° | 140.8 A | −199.0 A | 3.52 A | 55.1 % |
| 25 | 25.0 | 88.30° | 144.4 A | −204.2 A | 6.05 A | 71.2 % |
| 50 | 50.0 | 87.21° | 156.4 A | −220.9 A | 10.77 A | 81.6 % |
| 100 이상 | **84.3** | 86.75° | 203.7 A | −287.6 A | 16.34 A | 83.3 % |

요구 토크 100, 200, 350 N·m 는 모두 같은 점으로 포화합니다.
**16 krpm 최대 토크가 84.3 N·m** 이고 그때 진각 86.75° 입니다.
전류가 203.7 A 로 한계 500 A 에 한참 못 미치므로 전압 제한에 걸린 것입니다.

---

### A2. 읽어낼 것

#### A2.1 진각은 전 구간에서 90°에 붙어 있다

가용 토크 전 범위(1 ~ 84.3 N·m)에서 진각이 **86.75° ~ 89.60°** 입니다.
90°에서 3.3° 안쪽입니다. 토크가 커질수록 진각이 내려가는 방향도 예측대로입니다.

#### A2.2 전류는 저토크에서도 줄지 않는다

토크 1 N·m 에서도 138.9 A 가 흐르고 거의 전부 −d축입니다.
이것이 특성전류(약 196 A peak)이고, 16 krpm 에서는 토크와 무관하게 이만큼을 약자속에 써야 합니다.
토크 1 N·m 의 효율이 9.4 % 인 이유가 이것입니다. 축 일량은 1.7 kW 인데 전류는 계속 흐릅니다.

#### A2.3 Full-FEA 배치의 36° 점은 운전점이 아니다 (확정)

16 krpm 최대 토크가 84.3 N·m 인데 손실 격자의 같은 속도·460 A·36° 점은 899 N·m 입니다.
**10배 이상 차이**입니다. 그 격자는 전압 제한을 검사하지 않는 손실 비교용이며
운전 궤적으로 인용하면 안 됩니다. 축 출력으로 보면 격자 점이 1.5 MW, 실제 한계가 141 kW 입니다.

---

### A3. 아직 답하지 못한 것

이 스윕은 Lab 의 기본 손실 설정으로 돌렸습니다.

```
IronLossCalc_Lab    = 3
MagnetLossCalc_Lab  = 3
ACLossMethod_Lab    = 0      <- 값의 의미 미확인
CalcTypeCuLoss_MotorLAB = 0
```

`ACLossMethod_Lab = 0` 이 교류 손실을 끈 것인지, 해석식인지, Full-FEA 맵인지 확인하지 못했습니다.
따라서 **"교류 동손을 고려했을 때 진각이 얼마나 달라지는가"** 라는 원래 질문은 아직 미결입니다.

인계 문서 4절 나 항목이 그것입니다. 같은 토크 점에서 교류 손실 설정 3종
(끔 / 해석식 / Full-FEA 맵)으로 진각을 비교해야 결론이 납니다.
위 표가 그 비교의 기준선입니다.

#### A3.1 모델 해상도 주의

시간을 줄이려 해상도를 낮췄습니다.

```
ModelBuildPoints_Current_Lab = 5   (기본 6)
ModelBuildPoints_Gamma_Lab   = 5   (기본 5)
ModelBuildPoints_Speed_Lab   = 2   (기본 4)
```

속도 점 2개는 거칩니다. 최대 토크 84.3 N·m 와 진각 값이 해상도에 얼마나 민감한지
기본 해상도로 한 번 확인하는 편이 좋습니다. 생성에 26분 걸렸습니다.

---

### A4. 원자료

PC2 `D:\e10\work_lab2\lab2.json`. 스크립트는 `scratchpad/lab2.py`.

---

## B. PC1 회신

PC1(`2020-2-work-B`, `E:\KDH\Overleaf\Thesis_SKKU`), 2026-09-17.

### B0. 먼저 — 대상 기하를 바꿨습니다 (사용자 승인, 09-17)

PC2 가 지목한 `ipmfea/jobs/r2_fullfea/results_pc2_sd/R1_0167/e10_adapt.mot` 은 **레포에 없습니다**
(그 폴더에는 `fullfea.json` 만 커밋돼 있고 `.mot` 은 배치 작업 폴더에만 생겼다가 사라집니다).
PC1 에서 `InjectTask.prepare` 로 재생성은 했고 규약도 맞습니다(슬롯 깊이 13.8357 mm, 도체 6/6,
hausdorff 6e-14 mm, 보어 138.5158 — verify3 범위와 일치). 그런데 **그 기하에는 Lab 모델이 없어
결국 PC2 가 막힌 26 분 빌드를 PC1 이 다시 하게 됩니다.**

그래서 사용자 지시로 **이 로컬에 이미 빌드돼 있는 Lab 모델 6종**으로 진행합니다. 진각 자체가 질문이므로
기하는 e10 계열이면 충분하다는 판단입니다.

| 키 | 파일 | 기하 | AC 손실 맵 | 빌드 |
|---|---|---|---|---|
| `ref_hyb` | `Thesis\e10\refModel\e10Turn6V261.mot` | 기준기 (보어 142.54) | **Hybrid** | 06-29, 460 A rms, 16 krpm |
| `ref_hyb30` | `refModel\e10Turn6V261_Lab30.mot` | 기준기 | Hybrid | 07-30 |
| `sl_hyb30` | `SLFEA\e10Turn6V261SLFEA_Lab30.mot` | SLFEA 2배 축척 (보어 285.08) | **Hybrid** | 07-30 17:56, 920 A |
| `sl_ffea30` | `SLFEA\e10Turn6V261SLFEA_FullFEA_Lab30.mot` | 〃 | **Full FEA (전 슬롯)** | 07-30 22:46, 920 A |
| `sl_hyb48` | `SLFEA\e10Turn6V261SLFEA_Lab48.mot` | 〃 | Hybrid | 07-17 20:36 |
| `sl_ffea48` | `SLFEA\e10Turn6V261SLFEA_FullFEA_LAB.mot` | 〃 | Full FEA (전 슬롯) | 07-16 22:47 |

**같은 기하 위에서 Hybrid 대 Full-FEA 를 맞대볼 수 있는 쌍은 SLFEA(2배 축척) 쪽에만 있습니다.**
진짜 e10 기하에는 Hybrid 빌드만 있습니다. 그래서 인계 문서 4절 (나)의 3종 비교는 SLFEA 쌍으로 하고,
기준기에서는 (AC 끔 / Hybrid 맵 / 사용자비 k_ac) 3종을 봅니다.

원본 `.mot` 과 짝인 `<이름>\Lab\*.mat` 은 작업 폴더로 복사해 열고, **빌드 설정은 건드리지 않습니다**
(`Imax_RMS_MotorLAB`, `SpeedMax_MotorLAB`, `SatModelPoints_MotorLAB` 그대로). 바꾸는 것은 운전점 요구값과
`CalcTypeCuLoss_MotorLAB` / `ControlStrat_MotorLAB` 뿐입니다.

### B0.1 PC2 가 알아야 할 함정 — `get_model_built_lab()` 은 주입 직후에도 True 다

인계 문서 5절은 "포화맵이 이미 있으면 `get_model_built_lab()` 로 확인하고 `build_model_lab()` 생략"이라고
적었는데, **적응형 기하 주입 뒤에는 이 확인이 안전하지 않습니다.**

PC1 에서 `e10Turn6V261.mot`(기준기, Lab 빌드 있음) 에 R1_0167 기하를 주입해 저장한 직후
`get_model_built_lab()` 이 **True** 를 돌려줍니다. 기준 파일의 Lab 모델 플래그와 `Lab\*.mat` 이 그대로
따라오기 때문입니다. 그대로 믿고 운전점을 돌리면 **주입 전 기하의 포화맵**으로 진각을 읽게 됩니다.
빌드 상태는 `LabModel_Saturation_Date` / `LabModel_ACLoss_Date` 와 `LabModel_ACLoss_StatorCurrent_RMS`,
`LabModel_ACLoss_MaxSpeed` 를 함께 보고 판단해야 합니다.

덧붙여 기준 `.mot` 의 `SpeedMax_MotorLAB` 은 **15,000 rpm** 이라 16 krpm 을 덮지 못합니다. 새로 빌드한다면
이 값을 먼저 올려야 합니다(AC 손실 맵의 `LabModel_ACLoss_MaxSpeed` 는 16,000 으로 빌드돼 있습니다).

### B0.2 `ACLossMethod_Lab` 의 뜻 — 확정

Motor-CAD 2026 R1 도움말(`Motor-CAD.chm`: *Copper Loss Model Build*, *BPM AC Winding Loss Model Build*)로
확인했습니다. 교류 손실 처리는 **두 변수의 조합**입니다.

| 변수 | 뜻 | 값 |
|---|---|---|
| `CalcTypeCuLoss_MotorLAB` | Stator Copper Loss 모델 | 0 = DC Only (User) · 1 = DC + AC (User) · 2 = DC + AC (FEA single point) · **3 = DC + AC (FEA Map)** |
| `ACLossMethod_Lab` | 그 FEA Map 을 무엇으로 만드는가 | **0 = Hybrid** · 1 = Full FEA (single slot) · 2 = Full FEA (all slots) |

우리 모델은 전부 `CalcTypeCuLoss_MotorLAB = 3` 이고, `ACLossMethod_Lab` 이 0(Hybrid) 또는 2(Full FEA 전 슬롯)입니다.
빌드된 결과는 `LabModel_ACLoss_Method`(=3, Cu 손실 모델 종류)와 `LabModel_ACLoss_CalculationMethod`(=0 또는 2)에 기록됩니다.
즉 인계 문서가 물은 "끔 / 해석식 / Full-FEA 맵" 3종은

- **끔** = `CalcTypeCuLoss_MotorLAB = 0` (DC 만),
- **해석식** = `3` + `ACLossMethod_Lab = 0` (Hybrid 맵 — 표피·근접 해석식),
- **Full-FEA 맵** = `3` + `ACLossMethod_Lab = 1|2` (도체 솔리드 과도 FEA 맵)

입니다. 앞의 둘은 이미 빌드된 모델에서 **재빌드 없이** 전환됩니다(맵은 빌드돼 있고 쓰느냐 마느냐의 문제).
Full-FEA 맵만 별도 빌드가 필요하고, 그래서 SLFEA 쪽 전용 파일이 따로 있는 것입니다.

또 하나 도움말이 경고하는 것: **커스텀 기하(커스텀 자기 영역 또는 DXF)에서는 Full FEA AC 손실로 Lab 모델을
빌드할 수 없습니다**("the model build will be stopped..."). 적응형 템플릿으로 만드는 R2 설계들이 여기에 걸릴
가능성이 높으니, R1_0167 에서 Full-FEA Lab 맵을 만들 계획이라면 먼저 확인이 필요합니다.

**그래서 A3 절의 표는 이미 "교류 손실 끔" 다리입니다.** PC2 가 적어 둔 설정이
`CalcTypeCuLoss_MotorLAB = 0` 이기 때문입니다. 이 값이 0 이면 `ACLossMethod_Lab` 이 무엇이든 쓰이지 않고
Cu 손실은 직류분만 들어갑니다(도움말 *Copper Loss Model Build*: "DC Only (User)"). PC2 의 89.60° 표는
3종 비교의 기준선이라기보다 **첫 번째 다리**이고, 남은 것은 같은 점에서 `CalcTypeCuLoss_MotorLAB = 3` 으로
바꿔 (Hybrid 맵 / Full-FEA 맵) 두 다리를 읽는 것입니다. 이 전환에는 **재빌드가 필요 없습니다** —
R1_0167 모델의 AC 맵은 `ACLossMethod_Lab = 0`(Hybrid) 으로 이미 함께 빌드돼 있으므로,
PC2 쪽에서도 26 분을 다시 쓰지 않고 `set_variable("CalcTypeCuLoss_MotorLAB", 3)` 한 줄로 두 번째 다리를
바로 얻을 수 있습니다. 세 번째 다리(Full-FEA 맵)만 별도 빌드가 듭니다.

---

### B1. 지금까지 나온 것 (중간)

#### B1.1 PC2 첫 점과 연속입니다

| 16 krpm, 1.0 N·m | 진각 | 상전류 rms |
|---|---|---|
| PC2, R1_0167 기하 | 89.60° | 138.9 A |
| PC1, 기준기 기하 (`ref_hyb`) | 89.698° | 135.6 A |

기하가 다른데도 같은 자리입니다. 저토크에서 진각이 90° 로 수렴하고 전류가 특성전류에 고정된다는 PC2 의
해석이 그대로 확인됩니다. 같은 모델의 최대 토크는 16 krpm 88.0 N·m (γ 85.2°, 204 A), 8 krpm 196.2 N·m,
4 krpm 456.9 N·m (전류 상한 460 A rms, 720 V) 입니다.

#### B1.2 (나)의 예고편 — 16 krpm 에서 교류 동손은 진각을 거의 못 움직인다

`ref_hyb`, 제어전략 `ControlStrat_MotorLAB = 0`, 16 krpm:

| 요구 토크 | γ (Hybrid 맵) | γ (AC 끔) | Δγ | 효율 (맵 / 끔) |
|---|---|---|---|---|
| 0.44 N·m | 89.7497° | 89.7497° | **−0.0000°** | 6.34 / 8.30 % |
| 2.0 N·m | 89.6064° | 89.6062° | +0.0002° | 23.49 / 29.14 % |
| 17.6 N·m | 88.2091° | 88.2015° | +0.0076° | 72.37 / 77.89 % |
| 44.0 N·m | 86.1905° | 86.1509° | **+0.0396°** | 85.31 / 88.76 % |

효율은 4~6 %p 깎이는데 진각은 0.04° 안에서만 움직입니다. 16 krpm 에서는 전압 한계가 운전점을 거의
결정해 버려(쇄교자속 한계 62 mWb 대 무부하 210 mWb) 손실 모델이 고를 자유도가 남지 않기 때문입니다.
전압 한계가 풀리는 4·8 krpm 과, 진각 의존성의 **부호가 반대인** Full-FEA 맵에서도 같은지가 남은 확인입니다.

#### B1.3 Hybrid 와 Full-FEA 는 진각 의존성의 부호가 반대다

JEET Ref 맵(기준기 기하, 120 운전점 실측; `map_exports/e10/Ref/JEET_ACLoss_Ref_Map_Summary.json`)에서
16 krpm · 460 A rms 의 교류 초과분:

| γ | 0° | 18° | 36° | 54° | 72° | 90° |
|---|---|---|---|---|---|---|
| Full-FEA | 40.39 kW | 38.96 | 37.17 | 33.18 | **28.64** | 29.74 |
| Hybrid | 12.83 kW | 14.15 | 16.50 | 20.15 | **24.87** | 25.15 |

**Full-FEA 는 진각을 키우면 교류손이 줄고, Hybrid 는 늘어납니다.** 손실 최소 제어가 진각을 어느 쪽으로
미느냐가 부호부터 갈린다는 뜻입니다. 그래서 (나)의 답은 "몇 도" 이전에 "어느 방향"이 먼저입니다.
같은 기하의 Hybrid/Full-FEA Lab 쌍(SLFEA)으로 이 부호가 진각 선택에 실제로 나타나는지 보고 있습니다.

#### B1.4 (라) 무부하 성분 분리 — 끝났습니다

R1_0167 기하(이 항목만 그 기하로 이미 돌렸습니다), 전류 0, 16 krpm, `ProximityLossModel = 3`, 335 s:

| 항목 | 값 |
|---|---|
| 무부하 도체 와전류손 (Full-FEA) | **4.35 W** |
| 무부하 고정자 철손 | 1385.8 W |
| 무부하 자석손 | 5.57 W |
| 축 토크 | 0.0 N·m |

교류 동손의 **제동 성분은 4.35 W** 로, 16 krpm 기계 각속도 1675.5 rad/s 에서 **0.0026 N·m** 입니다.
같은 기하의 460 A 교류 초과분이 30.0 kW 인 것과 견주면 0.015 % 입니다.
`loss_torque_convention.html` 3절의 분류 — 교류 동손의 주된 부분은 입력측이고 무부하분만 제동 — 이
수치로 확인됩니다. **실용적으로는 교류 동손 전부를 입력측으로 넣고, 제동 항에는 넣지 않아도 됩니다.**
반면 무부하 고정자 철손 1385.8 W 는 0.83 N·m 로 제동 항에 유의미하게 들어갑니다.

---

### B2. 남은 작업

- 6 모델 × (16/8/4 krpm) × 저토크 조밀 토크 스윕 × 손실처리 3종 × 제어전략 2종 — 진행 중 (점당 8 s)
- Lab 맵의 ∂P_ac/∂γ 를 JEET 실측 격자와 같은 점에서 직접 읽기 (Operating Point Definition =
  Current/Phase Advance, 전압·전류 한계 미적용)
- 결론: 진각 이동량과 "전류맵을 다시 짤 만한가"

### B3. 공용 PC 관리

PC1 에는 사용자가 9/16 에 띄운 Motor-CAD 창(PID 37116)이 살아 있습니다. 이미지 이름으로 일괄 종료하지 않고,
인스턴스는 부모 프로세스(파이썬 드라이버) 대응으로 PID 를 확인해 개별 관리합니다
(`Get-CimInstance Win32_Process -Filter "Name='MotorCAD.exe'"` 의 `ParentProcessId`).
PC1 이 띄운 PID 는 `D:\KangDH\Thesis\e10\work_lab_pc1\pids.txt` 에 기록합니다.
