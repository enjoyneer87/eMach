# Phase A -- map-based 효율맵 vs Motor-CAD Lab (task A2)

map-based 효율맵(run_efficiency_map.py, 멱지수 AF + SCL-M k_r)을 Lab 효율맵과 대조. Δ = map - Lab.

**철손 주의**: e10_SatuMap의 Iron_Loss는 단일조건 값(속도 스케일링 없음) -> `eta_raw`(자체 철손)는 고속 과대평가. `eta_iso`(철손을 Lab에서 취함)가 동손/AF 충실도의 정직한 지표. Cu_AC parity가 핵심 검증.

## Ref  (유효 276점)

| 채널 | mean Δ | MAE | max|Δ| |
|---|---|---|---|
| η (raw, map 철손) | +1.514 % | 1.845 % | 8.412 % |
| η (iso, Lab 철손) | +0.779 % | 1.286 % | 5.440 % |
| **I_rms (토크당전류)** | -4.469 A | 9.717 A | 75.575 A |
| β 위상각 | -3.733 deg | 3.858 deg | 34.791 deg |
| Cu_DC | -0.556 kW | 1.076 kW | 13.175 kW |
| **Cu_AC (AF 보정)** | -0.625 kW | 0.625 kW | 5.265 kW |
| Iron (gap) | -0.702 kW | 0.702 kW | 4.017 kW |

## SC  (유효 157점)

| 채널 | mean Δ | MAE | max|Δ| |
|---|---|---|---|
| η (raw, map 철손) | +4.799 % | 4.799 % | 26.714 % |
| η (iso, Lab 철손) | +3.856 % | 3.856 % | 21.151 % |
| **I_rms (토크당전류)** | -7.066 A | 17.202 A | 118.673 A |
| β 위상각 | -2.866 deg | 2.993 deg | 18.185 deg |
| Cu_DC | -3.089 kW | 3.089 kW | 22.756 kW |
| **Cu_AC (AF 보정)** | -6.354 kW | 6.354 kW | 58.636 kW |
| Iron (gap) | -1.950 kW | 1.950 kW | 15.316 kW |

## 해석 (Phase B/C 진입점)

### 검증된 부분 (map-based 방법의 유효 영역)
- **온도 정합**: Lab 권선 80°C. R_dc 20→80°C(×1.236) 보정 후 Ref Cu_DC 잔차 -2.24→-0.56 kW, eta_iso +2.14→+0.78%. 잔여분이 운전점/λ 기여.
- **I_rms parity(토크당전류)**: Ref는 대각선 밀착(mean Δ -4.5 A) -> SatuMap λ_d/λ_q + MTPA/FW EEC 솔버가 Lab 운전점을 잘 재현. DC동손·토크는 정합. **정상상태 EEC 솔버 자체는 유효**함을 확인.
- **효율맵(iso)**: 철손을 Lab에서 취하면 Ref 효율맵이 Lab과 시각적으로 일치(MAE 1.29%).

### 구조적 결함 (Phase C가 반드시 해결)
- **AC 동손이 map≈0**: 효율맵의 AC 동손 base는 e10_SatuMap의 Stator_Copper_Loss_AC(단일조건, Ref 기준 ~26W)를 k_a/k_r²로 스케일한 값. AF(TS/Hybrid 비, ~1-3)만 곱하므로 **주파수 스케일링(∝f²)과 SC 후막도체 근접효과의 절대크기가 빠진다**. 결과: Lab AC동손 최대 60 kW(SC) vs map ~0. 논문1은 손실 레벨(h_ac,f_ac 물리값)에서 AF를 검증했지만, 효율맵 파이프라인은 Ref-SatuMap의 작은 값을 base로 써서 크기를 잃음.
  - **처방**: 속도분해 hybrid AC 맵(모델별 물리 hybrid) × AF 로 재구성. AF는 비율, base는 반드시 해당 (속도,모델)의 물리 hybrid.
- **철손도 동일**: 단일조건 Iron_Loss → 속도스케일링 부재. map≈0 vs Lab 최대 16 kW(SC). 에디/히스테리시스 분리 속도맵 또는 Lab 철손 LUT 필요.
- 두 채널 모두 **주파수 의존 손실의 base가 단일조건 SatuMap이라는 한 원인**. Phase C = 속도분해 손실맵 구축 (AC copper + iron).

### Phase 매핑
- Phase B: 가역성 잔차(B1 결과) + I_rms/β 편차 -> 자속맵 가역성 강제·충실화 (효과는 Ref 수준에서 이미 작음 → 우선순위 낮음, 정합성 보증용).
- **Phase C(우선)**: 속도분해 AC동손·철손 맵 + 온도모델. 이게 효율맵 정확도의 지배 요인. 완료 시 SC eta_iso +3.86%의 대부분 해소 예상.
