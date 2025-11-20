# RBF-DNN 통합 모터 손실 모델링 툴킷

이 툴킷은 모터의 Id-Iq 평면에서 손실을 모델링하는 통합 솔루션입니다. RBF(Radial Basis Function) 모델과 DNN(Deep Neural Network)을 결합하여 다양한 geometry 조건에서 robust하고 정확한 손실 예측을 제공합니다.

## 주요 특징

- **Robust RBF 모델링**: NaN, 중복점, 수치적 불안정성을 자동 처리
- **DNN 기반 계수 학습**: RBF 계수를 geometry 파라미터의 함수로 학습
- **자동화된 워크플로우**: 데이터 로드부터 예측까지 완전 자동화
- **실무 지향 설계**: 섹션별 실행 가능, 모듈화된 구조
- **포괄적 시각화**: 3D, contour, performance metrics 등

## 파일 구조

### 메인 스크립트
- `mainTestRBF.m`: 전체 워크플로우 메인 스크립트
- `demoRBF_DNN_Workflow.m`: 가상 데이터를 이용한 전체 과정 데모

### 핵심 함수
- `trainRBFThinplate.m`: Thin Plate Spline RBF 모델 학습
- `evaluateRBFThinplate.m`: RBF 모델 예측
- `trainRBF_DNN.m`: RBF 계수를 DNN으로 학습

### 유틸리티 함수
- `generateLossMapFromGeometry.m`: 새로운 geometry에 대한 손실 맵 생성
- `loadRBFModel.m`: 저장된 RBF 모델 로드
- `evaluateRBFModel.m`: 모델 성능 평가
- `predictAllVariables.m`: 모든 변수 일괄 예측

### 예시 함수
- `createLossModel.m`: 손실 모델 생성 예시
- `visualizeLossModel.m`: 모델 시각화 예시

## 사용 방법

### 1. 기본 RBF 모델링

```matlab
% 데이터 로드 (38100_20231004WorkSpace.mat 등)
load('your_data.mat');

% mainTestRBF.m 실행 (섹션별 실행 권장)
% Ctrl+Enter로 각 섹션 실행:
%   섹션 1-3: 데이터 로드 및 전처리
%   섹션 4-6: RBF 모델 생성 및 성능 평가  
%   섹션 7-8: 시각화
%   섹션 9: 모델 저장
```

### 2. DNN을 이용한 geometry 확장

```matlab
% mainTestRBF.m 계속 실행:
%   섹션 10: 여러 geometry의 RBF 계수 추출
%   섹션 11: DNN 학습
%   섹션 12: 새로운 geometry 예측
%   섹션 13: 종합 사용법
```

### 3. 간단한 데모 실행

```matlab
% 전체 과정을 한 번에 체험
run('demoRBF_DNN_Workflow.m');
```

### 4. 개별 함수 사용

```matlab
% RBF 모델 학습
[weights, centers, bias] = trainRBFThinplate(id_data, iq_data, loss_data);

% 예측
predicted_loss = evaluateRBFThinplate([new_id, new_iq], weights, centers, bias);

% DNN 학습
[dnn_model, train_info] = trainRBF_DNN(geometry_features, current_norm, rbf_coeffs);

% 새로운 geometry 손실 맵 생성
[loss_map, ID, IQ] = generateLossMapFromGeometry(dnn_model, new_geo, current_norm, ...
                                                id_range, iq_range);
```

## 워크플로우 개요

```
FEA 데이터 → RBF 모델링 → 성능 평가 → 시각화 → 모델 저장
     ↓
여러 Geometry → RBF 계수 추출 → DNN 학습 → 새로운 Geometry 예측
     ↓
실무 활용: 설계 최적화, 성능 예측, 효율성 맵 생성
```

### 세부 단계

1. **데이터 전처리**
   - NaN 제거, 중복점 처리
   - 수치형 변수 자동 탐지
   - 데이터 품질 검증

2. **RBF 모델링**
   - Thin Plate Spline 기반
   - 조건수 기반 정규화
   - 특이행렬 처리

3. **성능 평가**
   - R², RMSE, MAE 계산
   - Cross-validation
   - 잔차 분석

4. **DNN 확장**
   - Geometry → RBF계수 매핑 학습
   - 다층 퍼셉트론 또는 RBF 네트워크
   - 하이퍼파라미터 자동 조정

5. **새로운 조건 예측**
   - DNN으로 RBF 계수 예측
   - 전체 Id-Iq 맵 생성
   - 후처리 및 검증

## 입력 데이터 형식

### MAT 파일 구조
```matlab
data.Id              % Id 전류 (A)
data.Iq              % Iq 전류 (A)  
data.CoreLoss        % 철손 (W)
data.CopperLoss      % 동손 (W)
data.MagnetLoss      % 자석손 (W)
% ... 기타 손실 변수들
```

### Geometry 파라미터
```matlab
geometry.stator_slot_num    % 스테이터 슬롯 수
geometry.rotor_pole_num     % 로터 극 수
geometry.air_gap           % 공극 (mm)
geometry.stack_length      % 적층 길이 (mm)
geometry.magnet_thickness  % 자석 두께 (mm)
```

## 출력 결과

### RBF 모델
- `rbf_models_all_variables.mat`: 모든 변수의 RBF 모델
- 예측 함수, 성능 지표, 원본 데이터 포함

### DNN 모델  
- `dnn_rbf_model.mat`: DNN 모델 및 학습 정보
- Geometry → RBF계수 매핑 함수

### 시각화
- 3D 손실 맵, contour plot
- 성능 비교 차트
- 학습 곡선, 잔차 분석

## 옵션 및 설정

### RBF 옵션
```matlab
% trainRBFThinplate.m에서
options.regularization = 1e-6;    % 정규화 계수
options.condition_threshold = 1e12; % 조건수 임계값
options.min_data_points = 10;     % 최소 데이터 개수
```

### DNN 옵션  
```matlab
options.hidden_layers = [50, 30, 20];  % 은닉층 구조
options.max_epochs = 200;              % 최대 에포크
options.learning_rate = 0.001;         % 학습률
options.train_ratio = 0.7;             % 훈련 데이터 비율
options.use_rbf_basis = false;         % RBF 기저함수 사용 여부
```

## 문제 해결

### 일반적인 문제들

1. **NaN 예측 결과**
   - 원인: 입력 데이터의 NaN, 수치적 불안정성
   - 해결: 데이터 전처리 강화, 정규화 계수 조정

2. **낮은 모델 성능**
   - 원인: 데이터 부족, 부적절한 RBF 센터
   - 해결: 더 많은 데이터, 센터 배치 최적화

3. **DNN 학습 실패**
   - 원인: 데이터 부족, 차원의 저주
   - 해결: 최소 100개 geometry 데이터, 차원 축소

### 성능 최적화

1. **계산 속도 향상**
   - RBF 센터 개수 조정 (50-200개 권장)
   - 병렬 처리 활용
   - 그리드 해상도 조정

2. **메모리 사용량 감소**
   - 대용량 데이터 분할 처리
   - 중간 결과 정리
   - 정밀도 조정 (single vs double)

## 실무 활용 예시

### 1. 모터 설계 최적화
```matlab
% 여러 설계안의 손실 특성 비교
for i = 1:length(design_candidates)
    [loss_map, ~, ~] = generateLossMapFromGeometry(dnn_model, ...
                       design_candidates(i), rated_current, id_range, iq_range);
    efficiency_map = (mechanical_power ./ (mechanical_power + loss_map)) * 100;
    max_efficiency(i) = max(efficiency_map(:));
end
```

### 2. 실시간 손실 추정
```matlab
% 실시간 제어에서 현재 동작점의 손실 추정
current_loss = evaluateRBFThinplate([current_id, current_iq], ...
                                   model.weights, model.centers, model.bias);
```

### 3. 효율성 맵 생성
```matlab
% 전체 동작 영역의 효율성 맵
mechanical_power = id_grid .* vd_grid + iq_grid .* vq_grid;
total_loss = core_loss_map + copper_loss_map + magnet_loss_map;
efficiency_map = mechanical_power ./ (mechanical_power + total_loss) * 100;
```

## 버전 정보
- 버전: 1.0
- 작성자: MATLAB Copilot
- 날짜: 2024
- MATLAB 호환성: R2019b 이상 (Deep Learning Toolbox 필요)

## 라이선스
이 코드는 연구 및 교육 목적으로 자유롭게 사용할 수 있습니다.

## 지원 및 문의
기술적 문의나 개선 사항은 이슈를 통해 제출해 주세요.
