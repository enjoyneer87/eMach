# acloss_ref_methods — Claude Code Context

> 상위 컨텍스트: `../CLAUDE.md` 참조  
> 이 폴더: FEA B 기반 AC 손실 방법 비교 구현

---

## 핵심 스크립트 역할

### `mesh_b_vs_mcad.py`

메인 비교 스크립트. 세 가지 모드:

```bash
python mesh_b_vs_mcad.py halfsc     # HalfSC (MS B, 유효)
python mesh_b_vs_mcad.py sc         # SC (TS B, 참고용만)
python mesh_b_vs_mcad.py sc_hybrid  # SC (MS B, sc_b_data_hybrid/ 필요)
```

비교 컬럼: `P24sol | P24cub6 | G2sol | VlpG2p | KimKDE | MCADpx | TS`

**VlpG2p (Volpe G2 prime)**: Motor-CAD 내부와 동일한 이방성 수정 스킨뎁스 사용.
- `delta_w = delta * sqrt((w+h)/(2h))`
- `delta_h = delta * sqrt((h+w)/(2w))`

### `extract_sc_b_hybrid.py`

SC MS B 추출 — **Windows + Motor-CAD COM 필요** (`pyMotorEnv_310` venv).

```
아카이브: D:\KangDH\Thesis\e10\ACLossCalcExport_SC_no_txt\Hybrid_Speed_*
.mot:      D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot
출력:      sc_b_data_hybrid/Hybrid_Speed_{rpm}RPM_{I}A_{ph}deg.json
```

실행:
```
# pyMotorEnv_310 venv 활성화 후
python extract_sc_b_hybrid.py
```

### `elhajji_2d_acloss.py`

HalfSC 해석. `elhajji_b_data/` (MS B) 소비.
1D/24 결과가 MCAD 대비 2.25~3.11× → 정상 (B 샘플링 방식 차이).

---

## B 소스 규칙

```
elhajji_b_data/   → MS B (HalfSC, Hybrid_Speed_* .mes) ✅ halfsc/sc_hybrid에 사용
sc_b_data/        → TS B (SC, FullFEA_Speed_* .mes)    ⚠️ Hybrid 복제에 부적합
sc_b_data_hybrid/ → MS B (SC, Hybrid_Speed_* .mes)     ⏳ 추출 중
```

**VlpG2p는 반드시 MS B로 계산해야 Hybrid 공식 복제가 성립.**

---

## MAP_E10 경로 (자동 감지)

```python
_MAP_E10_LINUX = HERE.parent / 'map_exports' / 'e10'
_MAP_E10_WIN   = Path(r'D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports\e10')
MAP_E10 = _MAP_E10_LINUX if _MAP_E10_LINUX.exists() else _MAP_E10_WIN
```

Linux/Mac mount에서도 동작함.

---

## 출력 파일

| 파일 | 내용 |
|---|---|
| `mesh_b_vs_mcad_halfsc.json` | HalfSC 결과 (유효) |
| `mesh_b_vs_mcad_sc.json` | SC TS B 결과 (참고용) |
| `mesh_b_vs_mcad_sc_hybrid.json` | SC MS B 결과 (sc_b_data_hybrid/ 완성 후) |
| `elhajji_b_data/elhajji_2d_summary.json` | HalfSC 해석 요약 |

---

## 현재 작업 (2026-07-17)

1. `extract_sc_b_hybrid.py` 실행 → `sc_b_data_hybrid/` 채우기  
   ← `pyMotorEnv_310` venv에서 실행 필요 (일반 venv, conda 아님)
2. 완료 후 `mesh_b_vs_mcad.py sc_hybrid` 실행
3. SC Figure 4 플롯 생성 (`figures/sc_method_comparison_fig4.png`)
