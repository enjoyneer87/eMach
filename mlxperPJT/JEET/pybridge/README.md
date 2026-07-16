# JEET AC-loss pipeline — MATLAB ↔ Python bridge

`jeet_acloss_rbf` 파이썬 패키지의 고수준 파이프라인(`AcLossPipeline`)을
MATLAB 작업공간에서 호출하는 래퍼 모음. 데이터 로드 → 모델 구축 →
AF 예측 → 지표 → 그림 생성을 MATLAB 변수로 확인해 가며 실행할 수 있다.

## 요구사항

- MATLAB R2022b+ (Python 3.10 인터페이스 지원)
- Python: `pyMotorEnv_310` (numpy, scipy, matplotlib)
- 패키지: `D:\KangDH\EveryMotor\eMach\tools\jeet_acloss_rbf`

## 빠른 시작

```matlab
addpath('D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\pybridge');
jeetPySetup();                        % 세션당 1회 (첫 py 호출 전에)

ds  = jeetLoadDataset('SC');          % struct: speed/irms/phase/af/hyb/ts
m   = jeetMetrics('SC');              % mae/wmae + hybrid 기준선
af  = jeetPredictAF('SC', 16000, 920, 0:2:90);   % beta 스윕
T   = jeetSimilarityPairs('SC');      % SCL-M 상사성 39쌍 테이블
G   = jeetTransferAblation('SC');     % (n_base x n_spd8) wMAE 그리드
jeetMakeFigures();                    % 저널 PNG 재생성
```

전체 워크플로는 `demo_jeet_pipeline.m` 참조 (섹션별 실행 권장).

## 함수 목록

| 함수 | 역할 |
|---|---|
| `jeetPySetup(exe?)` | pyenv 설정 + 패키지 경로 + Agg 백엔드 |
| `jeetGetPipeline(reset?)` | 세션 캐시된 `AcLossPipeline` 핸들 |
| `jeetLoadDataset(scale)` | 데이터셋 → struct (제외점 적용됨) |
| `jeetScanOutliers(scale, tol?)` | AF 이웃 일관성 스캔 → table |
| `jeetMetrics(scale)` | 채택 모델 MAE/wMAE + Hybrid 기준선 |
| `jeetPredictAF(scale, rpm, A, deg)` | AF 예측 (스칼라/벡터) |
| `jeetSimilarityPairs(scale)` | 상사 사상 검증쌍 → table |
| `jeetTransferAblation(scale, ...)` | transfer 플랜 wMAE 그리드 |
| `jeetMakeFigures(outDir?)` | Fig 14 스타일 검증 PNG 재생성 |
| `np2mat(x)` | ndarray/py.list → MATLAB double |

## 채택 설정 (paper rev3)

`jeet_acloss_rbf/pipeline.py`의 `DEFAULT_CONFIG`에 내장:

- 기준 커널: **16 kRPM** (전류 집중 최대 발달점, `f_1D(16k)=1` 앵커)
- Ref = donor: 자체 34점 (base 22 + 속도당 4)
- HalfSC/SC = transfer: 자체 25/23점 (base 전량 + 8 kRPM 1점),
  저속 f-값은 Ref 모델 상사 평가 `AF(k_r²ω, I/k_r, β)`
- 데이터 제외: SC (16 kRPM, 690 A, β=90°) — 미수렴 TS-FEA

설정을 바꾸려면 MATLAB에서:

```matlab
pl = jeetGetPipeline(true);           % 새 파이프라인
% 또는 Python 쪽에서 AcLossPipeline(config) 로 커스텀 config 주입
```

## 주의

- `jeetPySetup`은 **첫 Python 호출 전에** 실행해야 함 (pyenv 제약).
  이미 다른 인터프리터가 로드됐으면 MATLAB 재시작 필요.
- Python 쪽 코드를 수정한 뒤에는 `jeetGetPipeline(true)` 로 리로드.
- 무거운 호출: `jeetTransferAblation` ~1분, `jeetMakeFigures` ~30초.
