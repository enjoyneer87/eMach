# e10 Icepak 온도 추출 — GUI 클릭 가이드 (헤드리스 8종 전부 실패 → GUI 필수)

프로젝트: `D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt`
디자인: `e10_net` / 솔루션: `SolveTrans : Transient` (커플드 오일회로 Network + Transient, 이미 솔브·저장됨)

## 0. 먼저 — 필드 유효성 진단 (중요)
헤드리스 추출이 8종 다 실패한 이유가 (a)API 이슈인지 (b)해가 온도장을 안 만들었는지 판별:
1. `ansysedt.exe` 실행 → File > Open → 위 .aedt.
2. Project Manager(좌) → `e10_net` → **Field Overlays** 우클릭 → **Plot Fields > Temperature > (전체 객체 선택)**.
3. 컬러 온도장이 뜨는가?
   - **YES(권선 뜨겁고~150°C, 외곽 냉각)** → 필드 유효, API 버그였음 → 아래 1번(Field Summary)으로 값 읽기.
   - **NO(전부 균일 70°C or 빈 화면)** → 커플드 해가 온도장 미생성 → 재솔브 조사 필요(analyze는 반환됐으나 미수렴 가능). 그럼 온도 추출 불가, 재솔브가 답.

## 1. 부품별 온도 읽기 — Field Summary
1. 메뉴 **Icepak > Results > Fields Summary** (또는 Field Overlays 우클릭 > Fields Summary).
2. **Add** 클릭 → Entity=**Object**, Geometry=**Volume**, Object=선택, Quantity=**Temperature**.
3. Min/Max/Mean 표시됨 → **Max** 기록. 아래 객체별로 반복(또는 여러개 Add):
   - 권선(coil): `Ph1_P1_C1` (또는 아무 코일 도체) — vs MAPDL **152.2°C**
   - 고정자: `Stator_Lamination_Primitive` — vs **126.0°C**
   - 로터: `Rotor_Lamination_Primitive` — vs **86.9°C**
   - 자석: `L1_1Magnet2S3_1` (또는 자석 객체) — vs **86.9°C**
   - 샤프트: `Shaft` — vs **84.9°C**
   - 또는 **AllObjects** 선택 → 전역 Max(=권선 핫스팟).

## 2. 오일 네트워크 노드 온도 (JACKET/SPRAY) — 자기일관성
- Project Manager → `e10_net` → **Boundaries > OilCircuit**(네트워크) 우클릭 → 노드 결과/온도 보기,
  또는 **Results > Solution Data > 프로파일**에서 네트워크 노드 온도 확인.
- MAPDL 회로값 대조: **JACKET 84.4°C / SPRAY 91.9°C** — 커플드가 맞으면 근사해야 함(자기일관성).

## 3. 값 회신
coil/stator/rotor/magnet/shaft **Max** + JACKET/SPRAY 노드온도를 알려주시면,
제가 **MAPDL vs FreeFlow vs Icepak 3-way 비교표**를 완성해 gdrive에 올리겠습니다.
(현재 3-way는 MAPDL·FreeFlow 2-tool까지 완비, Icepak 열만 대기 중.)
