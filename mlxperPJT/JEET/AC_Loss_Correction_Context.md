# AC 손실 보정 및 효율맵 반영 방법론 정리

## 1. 문제 정의

### 1.1 AC 손실 성분

```
총 구리 손실 = DC 손실 + AC 손실
                         ├── Skin effect   : 자기 자신의 전류에 의한 표피 효과 (속도/주파수 의존)
                         └── Proximity effect : 인접 도체/회전자 자석에 의한 근접 효과 (속도 + id/iq 의존)
```

### 1.2 Motor-CAD 모델 비교

| 항목 | Hybrid (ProximityLossModel=1) | FullFEA/TS (ProximityLossModel=3) |
|---|---|---|
| FEA 방식 | 정적 자기장 → 해석적 AC 손실 계산 | 과도 FEA (시간 변화 포함) |
| 속도 의존성 | B-field는 속도 무관 → 해석적 스케일링 | 속도마다 별도 FEA 필요 |
| id/iq 반영 | Proximity 부분 불완전 | 완전 반영 |
| 계산 속도 | 빠름 (~10배) | 느림 |
| 정확도 | 과소 추정 경향 | 기준값 (Reference) |

### 1.3 핵심 관찰

동일 전류 크기(460A), 다른 방향:
```
위상=0°  (iq=650A, id=0):   FullFEA / Hybrid = 3.38  ← iq 지배 → proximity 큼
위상=90° (id=650A, iq=0):   FullFEA / Hybrid = 1.22  ← id 지배 → proximity 작음

→ 같은 전류 크기인데 AC 손실이 2.8배 차이
→ Hybrid만으로는 이 차이를 설명 못함
```

---

## 2. Adjustment Factor (AF) 방법론

### 2.1 정의

```
AF(speed, id, iq) = FullFEA_AC_active_only / Hybrid_AC_total
```

- AF > 1 : FullFEA가 Hybrid보다 큼 (대부분의 운전점)
- AF < 1 : 일부 구간 (특정 전류 조합)
- AF ≈ 4.5 (near-zero 전류, 저속) ~ 1.1 (고전류, 고속)

### 2.2 방법 A — 속도만의 2차 다항식 (Motor-CAD Lab 적용용)

```
AF(s) = a·s² + b·s + c    (s: kRPM)

적용 수식 (Motor-CAD Lab Custom Loss):
  Extra_AC_loss = (AF(s) - 1) × Stator_Copper_Loss_AC
```

- **장점**: Motor-CAD Lab 수식에 직접 입력 가능, 구현 단순
- **단점**: id/iq 의존성 미반영 → 고전류 경부하/고부하 구분 불가
- **데이터 요구**: 최대 전류에서 속도별 3~4포인트

### 2.3 방법 B — 3D 다항식 (speed, id, iq)

```
AF(s, id, iq) = c0 + c1·s + c2·id + c3·iq
              + c4·s² + c5·id² + c6·iq²
              + c7·s·id + c8·s·iq + c9·id·iq

특성:
  k = 3 (입력 변수 수)
  d = 2 (다항식 차수)
  계수 수 = C(3+2, 2) = 10개
```

**Motor-CAD Lab Custom Loss로 입력 가능** (Id, Iq 변수 허용됨):
```
((c0 + c1*(Speed/1000) + c2*Id + c3*Iq
  + c4*(Speed/1000)^2 + c5*Id^2 + c6*Iq^2
  + c7*(Speed/1000)*Id + c8*(Speed/1000)*Iq + c9*Id*Iq) - 1)
* Stator_Copper_Loss_AC
```

- **장점**: id/iq 방향 효과 반영, FullFEA 수준 정확도
- **단점**: 캘리브레이션 FEA 필요 (~30-40회)
- **적용 분류**: Internal Custom Loss, Electrical Type

---

## 3. Motor-CAD Lab Custom Loss 적용

### 3.1 Internal vs External 구분

| 항목 | Internal | External |
|---|---|---|
| 손실 위치 | 모터 내부 (권선) | 모터 외부 (인버터 등) |
| 계산 방식 | 1회 순방향 | 반복 수렴 (DC 전류 기반) |
| Voltage Drop 함수 | 불필요 | 필수 |
| Id, Iq 사용 가능 | ✓ | ✓ |
| 제어 전략 반영 | Speed/Id/Iq 기반 시 포함 | 포함 (단 모터만 최적화) |

**AC 손실 보정 → Internal, Electrical Type** (권선 내부 손실, 전기적 에너지 열변환)

### 3.2 제어 전략 반영 조건

Motor-CAD 문서 기준, 아래 변수 기반 Internal Loss는 Control Strategy에 반영:
- Speed, Frequency
- **D/Q axis currents (Id, Iq)** ← 방법 B 가능
- Phase advance
- Stator current

→ 방법 B (Id, Iq 포함 수식)는 MTPA/최대효율 제어점 탐색에도 반영됨

---

## 4. Cauer 회로 방법과의 비교

### 4.1 Cauer 방법 개요 (JSOL 2022)

```
전압 방정식: V = R_i · I + dΦ/dt
R_i를 Cauer 래더 회로로 교체 → 주파수 의존 임피던스
```

파라미터:
```
L_c = (lhN²/w) × μ₀ × (w/w_slot)²   (N² = Σ(i+0.5)² → 층별 위치 가중치)
R_c = (lhN²/w) × (4/σh²) × (w/w_slot)²
W_AC = 3 · R_c · I₂²
```

### 4.2 한계

```
가정: "슬롯 외부에서 들어오는 자속은 슬롯을 가로지르지 않는다"
     → 회전자 자석 자속 침투 무시
     → id/iq 방향성 효과 미반영

W_AC = 3·R_c·I₂² → 전류 크기만, id/iq 방향 없음
```

| 항목 | Cauer 방법 | AF 방법 B |
|---|---|---|
| Skin effect | ✓ 해석식 | ✓ FEA 기반 |
| Proximity (슬롯 내 인접) | ✓ N² 항으로 부분 반영 | ✓ 포함 |
| Proximity (회전자 자석) | ✗ 무시 (핵심 한계) | ✓ FullFEA에 포함 |
| id/iq 의존성 | ✗ | ✓ |
| FEA 필요 여부 | 불필요 | 캘리브레이션 ~36회 |
| 방법 A 대비 위치 | 동급 (속도만) | 한 차원 위 |

### 4.3 슬롯 내 도체별 손실 분포 (FullFEA 데이터 확인)

```
w1 (슬롯 입구): 0.686 W  → 85% ← 회전자 자속 직접 노출
w2:             0.095 W  → 12%
w3:             0.019 W  →  2%
w4:             0.005 W
w5:             0.002 W
w6 (슬롯 바닥):  0.001 W  →  0.1%
```
→ JSOL 논문 Fig. 7과 동일 패턴 확인

---

## 5. 필요 FEA 횟수 분석

목표 맵: Ns speeds × Nc currents × Nφ phases

| 방법 | Hybrid FEA | FullFEA | 비고 |
|---|---|---|---|
| 브루트포스 FullFEA | 0 | Ns×Nc×Nφ | 느림 |
| Hybrid 전용 | Ns×Nc×Nφ | 0 | 정확도 부족 |
| **AF 방법 (Hybrid 스케일링 구현)** | **Nc×Nφ** | **~36회** | 권장 |
| AF 방법 (Motor-CAD API) | Ns×Nc×Nφ | ~36회 | 실용적 |

**핵심**: FullFEA 캘리브레이션 횟수는 맵 크기에 무관하게 고정 (~36회)

Hybrid 스케일링 가능 이유:
```
고정 (id, iq) → B-field 분포는 속도 무관
→ 1개 속도에서 FEA → 모든 속도의 Hybrid AC 손실을 해석적으로 계산
```

---

## 6. 현재 개발 데이터 구조

### 6.1 수집 완료 데이터

```
파일: JEET_ACLoss_180Map_Summary_20260620_055628.json
포인트: 180개 (Hybrid 90 + FullFEA 90)
속도: [2000, 4000, 16000] RPM
전류: [0.1, 115.1, 230.1, 345.1, 460.0] A (near-zero 포함)
위상: [0, 18, 36, 54, 72, 90]° × 6
```

### 6.2 8000 RPM 보완 스윕 (진행 중)

```
추가 파일: JEET_ACLoss_4Speed_Map_Summary_*.json
추가 포인트: 32개 (4전류 × 4위상 × 2모델)
전류: [115.1, 230.1, 345.1, 460.0] A (near-zero 제외)
위상: [0, 18, 54, 90]°
완료 후 총: [2000, 4000, 8000, 16000] RPM × 다양한 운전점
```

### 6.3 JSON/MAT 저장 필드

| 필드 | 설명 |
|---|---|
| `hybrid_total_kW` | Hybrid 모델 AC 손실 합계 |
| `ts_per_turn_W` | FullFEA 도체별 손실 (list, 6개) |
| `ts_per_turn_sum_kW` | FullFEA 활성부 전체 손실 합계 |
| `ts_ac_active_only_kW` | FullFEA AC 활성부만 = ts_per_turn_sum - DC_active |
| `ts_dc_active_kW` | DC 활성부 손실 |

---

## 7. 다중공선성 문제 및 해결

### 7.1 문제

(Irms, phase) → (id, iq) 원형 변환으로 인한 설계 행렬 조건수 과대:
```
원인: id² + iq² = 2·Irms² = const (각 전류 원에서)
     → id²와 iq² 열이 준선형종속
     → 조건수 915,135 (기준 1e4 초과)
```

### 7.2 해결: 입력 표준화

```python
s_sc  = (s   - s.mean())   / s.std()
id_sc = (idv - idv.mean()) / idv.std()
iq_sc = (iqv - iqv.mean()) / iqv.std()
# → 조건수 13으로 감소
```

---

## 8. 현재 R² 낮은 원인 및 개선 방향

### 8.1 현재 상태
```
R² = 0.798  (3속도, near-zero 전류 포함)
```

### 8.2 원인

| 원인 | 설명 |
|---|---|
| 0A near-zero 포인트 포함 | AF ≈ 4.5, 위상 무관 (다른 물리 레짐) |
| 속도 3개뿐 | [2k, 4k, 16k] RPM |
| 원형 스윕 구조 | id/iq 독립 변화 불가 |

### 8.3 개선 방향

1. **0A 포인트 분리**: near-zero 전류는 속도만의 함수로 별도 처리
2. **8000 RPM 추가**: 4속도로 속도 방향 해상도 향상
3. **재피팅**: 0A 제외 + 4속도 → R² 0.95+ 목표

---

## 9. 미해결 과제

| 과제 | 우선순위 | 내용 |
|---|---|---|
| 8000 RPM 스윕 완료 | 높음 | 현재 실행 중 |
| 0A 제외 재피팅 | 높음 | R² 개선 확인 |
| Motor-CAD Id/Iq 변수명 확인 | 높음 | Custom Loss 수식 적용 전 필수 |
| near-zero 보간 | 중간 | 8k RPM near-zero → 4k/16k 보간 |
| 도체별 AC 손실 분포 분석 | 낮음 | ts_per_turn_W 데이터 활용 |
| 패키지 함수 구현 | 중간 | Hybrid 스케일링 자체 구현 |
