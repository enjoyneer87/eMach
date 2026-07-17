# AC-Loss Reference Method Implementations

문헌의 교류 동손 계산 방법들을 파이썬으로 구현·상호 비교하는 연구 스위트.
(2026-07-17에 `D:\KangDH\Thesis\ACloss_Ref`(문헌 PDF 폴더)에서 코드만 분리 이동)

## 구성

| 파일 | 내용 |
|---|---|
| `morisco_acloss.py` | Morisco 2019/2020 hybrid current-diffusion 방법 |
| `ju_hybrid_acloss.py` | Ju(박사과정) hybrid 구현 |
| `volpe_hybrid_acloss.py` | Volpe 2019 hybrid (eMach `tools/loss/ACLOSS` MATLAB 포팅) |
| `elhajji_2d_acloss.py` / `elhajji_2d_fea_extract.py` | El-Hajji ICEM2020 2-D 방법 + FEA 추출 |
| `cauer_modeling.py` / `cauer_visualization.py` | Cauer ladder 등가회로 모델링 |
| `compare_all_methods.py` → `compare_all_methods_result.csv` | 전 방법 상호 비교 하네스 |
| `acloss_morisco_vs_ju.ipynb`, `cauer_modeling_example.ipynb` | 노트북 |
| `notes/` | 분석 노트 (오차원인, 검증 플랜, 전이 가이드 등) |

## 데이터

`elhajji_b_data/`의 `Hybrid_Speed_*.json`(각 ~4 MB, 요소별 B 데이터)은
용량 문제로 **git에서 제외**되어 있다. 재생성:

```
python elhajji_2d_fea_extract.py   # 입력: D:\KangDH\Thesis\e10\SLFEA_Half\ACLossCalcExport_Map\
```

`elhajji_2d_summary.json`(요약)은 추적된다.
