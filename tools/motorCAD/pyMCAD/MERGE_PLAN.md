# magnetic.py 병합 계획

> 브랜치: `devVeriACLoss` ← 원격 리팩토링 충돌 해결  
> 작성일: 2026-06-22

---

## 배경

원격에서 단일 파일 `magnetic.py` (~2600줄)를 6개 서브모듈로 분리 리팩토링하는 작업이 있었다.  
로컬 `devVeriACLoss` 브랜치는 그 이전에 **sliding band HDF5 export 기능**을 `magnetic.py`에 직접 추가했기 때문에 충돌이 발생했다.

### 원격 리팩토링 결과 구조

```
magnetic.py          ← 60줄 import hub (get_magnetic_data 등 thin wrapper 포함)
magnetic_model.py    ← 데이터 모델 (MagElement, MagneticRegion, MagneticRegions, ...)
magnetic_parse.py    ← TXT 파일 파서 (_open_mcad_text, _parse_*, ...)
magnetic_export.py   ← MCAD export 호출 (export_magnetic_txt, ...)
magnetic_plot.py     ← 시각화 (export_gif, interactive_plot, ...)
magnetic_h5.py       ← HDF5 export/load (export_*_h5, load_*_h5, ...)
```

---

## 이식 여부 전체 확인 결과

### ✅ 정상 이식된 항목

| 로컬 HEAD 함수/클래스 | 원격 위치 | 비고 |
|----------------------|-----------|------|
| `_open_mcad_text` | `magnetic_parse.py:16` | |
| `export_magnetic_timeseries_gif` | `magnetic_plot.py:18` | |
| `export_magnetic_snapshot_svgs` | `magnetic_plot.py:71` | |
| `MagElement` | `magnetic_model.py:11` | 원격에 `h` property 추가 |
| `MagneticRegion` | `magnetic_model.py:453` | 원격에 `get_hx/hy/h/mur` 추가 |
| `MagneticRegionsTimeSeries` | `magnetic_model.py:850` | 원격에 `interactive_plot`, `export_gif` 추가 |
| `_parse_first_block_magnetic_file` | `magnetic_parse.py:106` | ⚠️ node_a 누락 (아래 참조) |
| `_is_table_header` | `magnetic_parse.py:59` | |
| `_read_until_table_header` | `magnetic_parse.py:64` | |
| `_skip_header_lines` | `magnetic_parse.py:79` | |
| `_read_col_indices` | `magnetic_parse.py:89` | |
| `_parse_magnetic_timeseries_txt` | `magnetic_parse.py:218` | ⚠️ node_a 누락 (아래 참조) |
| `diagnose_magnetic_h5_mesh_motion` | `magnetic_h5.py:533` | |
| `export_magnetic_snapshot_h5` | `magnetic_h5.py:715` | |
| `inspect_magnetic_timeseries_h5` | `magnetic_h5.py:833` | |
| `load_magnetic_timeseries_h5_arrays` | `magnetic_h5.py:871` | |
| `load_magnetic_timeseries_h5_datasets` | `magnetic_h5.py:950` | |
| `load_magnetic_snapshot_h5_arrays` | `magnetic_h5.py:965` | |
| `read_magnetic_h5_format` | `magnetic_h5.py:1020` | |
| `_magnetic_regions_from_snapshot_h5` | `magnetic_h5.py:1071` | |
| `MagneticRegionsTimeSeriesH5` | `magnetic_h5.py:1130` | |
| `export_magnetic_timeseries_h5` | `magnetic_h5.py:15` | ⚠️ slideband 누락 (아래 참조) |
| `get_magnetic_data` | 원격 `magnetic.py` | |
| `get_magnetic_data_from_file` | 원격 `magnetic.py` | |
| `get_magnetic_timeseries_from_file` | 원격 `magnetic.py` | |
| `interactive_magnetic_plot` | `magnetic_plot.py:318` | 원격이 더 강화됨 |
| `interactive_magnetic_quiver` | `magnetic_plot.py:636` | |

### ❌ 누락된 항목 (이식 필요)

**총 3개 파일, 4가지 수정**

---

## 수정 계획 (우선순위 순)

### [수정 1] `magnetic_model.py` — `MagneticRegions`에 `node_a` 추가

**위치:** `MagneticRegions.__init__` + 메서드 추가

```python
# __init__ 안에 추가 (set_node_xy 바로 아래)
self.node_a = {}  # NodeIndex -> float (A field at node, from NodesTable)

# set_node_xy 다음에 메서드 추가
def set_node_a(self, node_a):
    """Attach node-level magnetic vector potential A (NodeIndex -> float) from NodesTable."""
    self.node_a = dict(node_a)
```

**왜 필요한가?**  
`node_a`는 NodesTable에서 파싱하는 **노드 단위 자기벡터포텐셜 A** 값이다.  
현재 원격의 `MagneticRegions`에는 이 속성 자체가 없어서,  
파싱 단계에서 읽어도 저장할 곳이 없다.  
H5 export 외에도 향후 노드 기반 A-field 시각화, 플럭스 연산 등에 활용 가능하다.

---

### [수정 2] `magnetic_parse.py` — `_NODE_COL_KEYS`에 `"A"` 추가

**위치:** `magnetic_parse.py:85`

```python
# 현재
_NODE_COL_KEYS = frozenset({"NodeIndex", "X", "Y"})

# 수정 후
_NODE_COL_KEYS = frozenset({"NodeIndex", "X", "Y", "A"})
```

**왜 필요한가?**  
`_read_col_indices()` 함수는 이 frozenset에 있는 컬럼만 인식한다.  
`"A"`가 없으면 `node_ci.get("A")`가 항상 `None`을 반환해서 A 파싱이 불가능하다.

---

### [수정 3] `magnetic_parse.py` — NodesTable 파싱에서 A 컬럼 읽기 (2곳)

#### 3-A. `_parse_first_block_magnetic_file` (line ~181)

```python
# 기존 코드
node_xy = {}
# ... NodesTable 읽기 loop ...
mag_regions.set_node_xy(node_xy)

# 수정 후
node_xy = {}
node_a = {}
# NodesTable 읽기 시작 전:
node_ci = _read_col_indices(in_file, _NODE_COL_KEYS)
ni_i = node_ci.get("NodeIndex", 0)
x_i  = node_ci.get("X", 1)
y_i  = node_ci.get("Y", 2)
a_node_i = node_ci.get("A")          # ← 추가
# loop 안:
    node_xy[node_idx] = (x_mm, y_mm)
    if a_node_i is not None:          # ← 추가
        node_a[node_idx] = float(row[a_node_i])
# loop 끝 후:
mag_regions.set_node_xy(node_xy)
mag_regions.set_node_a(node_a)        # ← 추가
```

#### 3-B. `_parse_magnetic_timeseries_txt` (line ~320) — 동일한 패턴으로 수정

---

### [수정 4] `magnetic_h5.py` — `export_magnetic_timeseries_h5`에 slideband 기능 이식

**위치:** `magnetic_h5.py:15` — 함수 전체

이 수정이 가장 크다. 로컬 HEAD의 `magnetic.py`에서 아래 항목을 이식:

#### 4-A. 함수 파라미터 추가

```python
def export_magnetic_timeseries_h5(
    nts: MagneticRegionsTimeSeries,
    h5_path: str | pathlib.Path,
    *,
    dtype: str = "float32",
    compression: str | None = "gzip",
    compression_opts: int | None = 4,
    chunk_elements: int = 200_000,
    mesh_coords: str = "static",
    moving_region_name_prefixes: Sequence[str] | None = None,
    moving_reg_codes: Sequence[int] | None = None,
    moving_node_motion_tol_mm: float = 1e-4,
    slideband_reg_codes: Sequence[int] | None = None,   # ← 추가
) -> pathlib.Path:
```

#### 4-B. 함수 본문 — CSR 초기화 블록 추가

함수 진입 초기화 부분에:
- `_node_a_by_step` 리스트 수집 (step loop 이전)
- `_sb_*` CSR 리스트들 초기화
- `_detect_slideband_codes()` 내부 함수 정의
- `_sb_codes` 결정 로직

#### 4-C. step loop 안 — slideband element 수집

각 step 처리 후 slideband region code에 해당하는 element를 별도로 수집:
- bx, by, b, a, j, je 값 + CSR offsets

#### 4-D. node loop — sliding band 노드 A 수집

slideband region에 속하는 노드의 `node_a` 값 수집 (CSR 형식)

#### 4-E. HDF5 write — `/slideband/` 그룹 저장

```python
if _has_sb:
    sb_g = f.create_group("slideband")
    sb_g.create_dataset("reg_codes", ...)
    sb_g.create_dataset("offsets", ...)
    sb_g.create_dataset("tri_index", ...)
    # ... node_1, node_2, node_3, reg_code, bx, by, a, j, je
    # ... node_x, node_y, node_a (CSR 형식)
    f.attrs["has_slideband_per_step"] = True
```

**소스:** 로컬 HEAD `magnetic.py` lines 153~826

---

## slideband 기능이 H5 export 외에 필요한가?

### 결론: 모든 slideband/node_a 관련 수정은 H5 export 전용

| 항목 | H5 export에만 사용? | 이유 |
|------|---------------------|------|
| `slideband_reg_codes` 파라미터 | ✅ H5 export 전용 | `export_magnetic_timeseries_h5`에서만 참조됨 |
| `_detect_slideband_codes()` | ✅ H5 export 전용 | 동일 |
| CSR 수집 + `/slideband/` write | ✅ H5 export 전용 | 동일 |
| `node_a` / `set_node_a` | ✅ **실질적으로 H5 slideband 전용** | 아래 참조 |

### node_a / set_node_a 상세

NodesTable에는 두 종류의 A 값이 존재한다:

| A 종류 | 위치 | 원격 파싱 | 활용처 |
|--------|------|-----------|--------|
| **element-level A** | `ElementsTable` 컬럼 `"A"` | ✅ `_ELEM_COL_KEYS`에 포함 → `MagElement.a` | `plot()`, `get_a()` 등 모든 분석 |
| **node-level A** | `NodesTable` 컬럼 `"A"` | ❌ `_NODE_COL_KEYS`에 없음 → 파싱 안 됨 | **현재 H5 slideband 이외 없음** |

H5를 쓰지 않는 한 `node_a`를 직접 읽는 코드가 없으므로, 수정 1~3은 **수정 4의 선행 조건일 뿐** 독립적으로 필요한 수정이 아니다.

**실질적 흐름 (H5 slideband 사용 시에만):**

```
TXT 파싱
  → MagneticRegions.node_a 에 노드 A값 저장   ← 수정 1~3 필요
  → export_magnetic_timeseries_h5(slideband_reg_codes=...) 호출
      sliding band 노드의 node_a 값을 읽어 H5에 기록   ← 수정 4 필요
```

`node_a` 파싱이 누락된 채로 slideband H5 export를 실행하면 `/slideband/node_a` 데이터셋이 모두 0으로 저장된다.

---

## 실행 순서 (작업 체크리스트)

### Step 1 — 충돌 해결 (필수)

```
[ ] 1. magnetic.py 충돌 해결: 원격 버전으로 채택
        git checkout --theirs tools/motorCAD/pyMCAD/magnetic.py
        git add tools/motorCAD/pyMCAD/magnetic.py
        git commit
```

### Step 2 — H5 slideband 이식 (선택: H5 export 사용 시)

수정 2~4는 H5 slideband export를 쓸 경우에만 필요. 의존 순서: 2 → 3 → 4.

```
[ ] 2. magnetic_model.py 수정  (선행 조건)
        - MagneticRegions.__init__에 self.node_a = {} 추가
        - set_node_a() 메서드 추가

[ ] 3. magnetic_parse.py 수정  (선행 조건)
        - _NODE_COL_KEYS에 "A" 추가
        - _parse_first_block_magnetic_file에 node_a 파싱 추가 (a_node_i + set_node_a)
        - _parse_magnetic_timeseries_txt에 node_a 파싱 추가 (동일 패턴)

[ ] 4. magnetic_h5.py 수정  (본체)
        - export_magnetic_timeseries_h5에 slideband_reg_codes 파라미터 추가
        - 로컬 HEAD magnetic.py lines 153~826에서 sliding band 블록 이식

[ ] 5. 동작 확인
        - export_magnetic_timeseries_h5(slideband_reg_codes=None) 기존 동작 회귀 확인
        - export_magnetic_timeseries_h5(slideband_reg_codes=[...]) 실행 후
          h5py로 /slideband/ 그룹 및 node_a 데이터셋 값 확인
```

---

## 참고: 원격이 로컬보다 향상된 항목 (병합 시 유지)

- `MagElement.h` property (H-field 크기)
- `MagneticRegion.get_hx/hy/h/mur()` (투자율 등 추가 물리량)
- `MagneticRegionsTimeSeries.interactive_plot/quiver/export_gif()` (convenience API)
- `magnetic_plot.py`의 `_extract_element_timeseries`, hover/dblclick helpers (더 정교한 interactive plot)
- `_parse_first_block_magnetic_file`에서 `Hx/Hy/Mur` 컬럼 지원 (로컬 HEAD에 없던 것)
