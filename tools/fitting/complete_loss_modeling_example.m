%% 종합 예시: id, iq, 손실 테이블을 이용한 RBF 모델링
% 이 스크립트는 실제 테이블 데이터를 사용하여 RBF 손실 모델을 만드는 
% 전체 워크플로우를 보여줍니다.

clear; clc; close all;

%% 방법 1: CSV 파일에서 데이터 로드하는 경우
fprintf('=== 방법 1: CSV 파일에서 데이터 로드 ===\n');
fprintf('CSV 파일 형식 예시:\n');
fprintf('Id,Iq,Loss\n');
fprintf('-100,50,45.2\n');
fprintf('-50,100,52.8\n');
fprintf('0,150,68.5\n');
fprintf('...\n\n');

% 예시 CSV 데이터 생성 (실제로는 기존 파일을 사용)
example_csv_data = table();
example_csv_data.Id = [-150; -100; -50; 0; 50; 100; 150; -100; -50; 0; 50; 100];
example_csv_data.Iq = [100; 100; 100; 100; 100; 100; 100; 200; 200; 200; 200; 200];
example_csv_data.Loss = [85.2; 67.3; 52.8; 45.5; 52.8; 67.3; 85.2; 120.5; 98.6; 85.2; 98.6; 120.5];

% CSV 파일로 저장 (예시)
writetable(example_csv_data, 'example_motor_loss.csv');

% CSV에서 로드
data_from_csv = readtable('example_motor_loss.csv');
fprintf('CSV에서 로드한 데이터: %d개 포인트\n', height(data_from_csv));

% 모델 생성
[model1, perf1] = createLossModel(data_from_csv);

% 시각화
fprintf('\n시각화 중...\n');
visualizeLossModel(data_from_csv, model1, struct('showError', true, 'save', false));

%% 방법 2: MAT 파일에서 데이터 로드하는 경우
fprintf('\n=== 방법 2: MAT 파일에서 데이터 로드 ===\n');

% 예시 MAT 데이터 생성
motor_data.id = (-200:25:200)';
motor_data.iq = (0:20:300)';
[Id_mesh, Iq_mesh] = meshgrid(motor_data.id, motor_data.iq);
motor_data.id = Id_mesh(:);
motor_data.iq = Iq_mesh(:);

% 실제적인 손실 함수 모델링
R_phase = 0.15;  % 상 저항
motor_data.loss = R_phase * (motor_data.id.^2 + motor_data.iq.^2) + ... % 동손실
                  abs(motor_data.id) * 0.1 + abs(motor_data.iq) * 0.05 + ... % 철손
                  20; % 기계 손실

% MAT 파일로 저장
save('example_motor_data.mat', 'motor_data');

% MAT에서 로드
loaded_data = load('example_motor_data.mat');
data_from_mat = loaded_data.motor_data;
fprintf('MAT에서 로드한 데이터: %d개 포인트\n', length(data_from_mat.id));

% 모델 생성
[model2, perf2] = createLossModel(data_from_mat);

%% 방법 3: 직접 데이터 입력하는 경우
fprintf('\n=== 방법 3: 직접 데이터 입력 ===\n');

% 직접 데이터 생성
direct_data = struct();
direct_data.id = [-100, -75, -50, -25, 0, 25, 50, 75, 100, ...
                  -100, -75, -50, -25, 0, 25, 50, 75, 100]';
direct_data.iq = [150, 150, 150, 150, 150, 150, 150, 150, 150, ...
                  250, 250, 250, 250, 250, 250, 250, 250, 250]';
                  
% 측정된 손실값 (예시)
direct_data.loss = [78.5, 65.2, 54.8, 47.2, 43.5, 47.2, 54.8, 65.2, 78.5, ...
                    125.8, 108.6, 94.2, 82.8, 78.5, 82.8, 94.2, 108.6, 125.8]';

fprintf('직접 입력한 데이터: %d개 포인트\n', length(direct_data.id));

% 모델 생성
[model3, perf3] = createLossModel(direct_data);

%% 훈련된 모델 사용 예시
fprintf('\n=== 훈련된 모델 사용 예시 ===\n');

% 새로운 조건에서 예측
test_id = [-80, -40, 0, 40, 80];
test_iq = [120, 180, 220];

[Test_Id, Test_Iq] = meshgrid(test_id, test_iq);
predicted_losses = model3.predict(Test_Id, Test_Iq);

fprintf('새로운 조건에서의 예측 결과:\n');
fprintf('Id(A)\tIq(A)\t예상손실(W)\n');
fprintf('%.0f\t%.0f\t%.2f\n', [Test_Id(:), Test_Iq(:), predicted_losses(:)]');

%% 모델 비교
fprintf('\n=== 모델 성능 비교 ===\n');
fprintf('모델\t\tRMSE(W)\t상대RMSE(%%)\t최대오차(W)\n');
fprintf('CSV 데이터\t%.3f\t%.2f\t\t%.3f\n', perf1.rmse, perf1.relative_rmse, perf1.max_error);
fprintf('MAT 데이터\t%.3f\t%.2f\t\t%.3f\n', perf2.rmse, perf2.relative_rmse, perf2.max_error);
fprintf('직접 입력\t%.3f\t%.2f\t\t%.3f\n', perf3.rmse, perf3.relative_rmse, perf3.max_error);

%% 모델 저장 및 로드
fprintf('\n=== 모델 저장 및 로드 ===\n');

% 모델 저장
loss_model = model3;  % 가장 좋은 모델을 선택
save('trained_loss_model.mat', 'loss_model');
fprintf('모델이 저장되었습니다: trained_loss_model.mat\n');

% 나중에 모델 로드하여 사용하는 방법
% loaded_model = load('trained_loss_model.mat');
% loss_prediction = loaded_model.loss_model.predict(new_id, new_iq);

%% 실무 사용 팁
fprintf('\n=== 실무 사용 팁 ===\n');
fprintf('1. 데이터 품질이 가장 중요합니다.\n');
fprintf('2. id, iq 범위를 고르게 커버하는 데이터를 수집하세요.\n');
fprintf('3. 노이즈가 있는 데이터는 전처리를 통해 제거하세요.\n');
fprintf('4. 모델 검증을 위해 데이터를 훈련/검증 세트로 나누어 사용하세요.\n');
fprintf('5. 외삽(extrapolation)은 가능하면 피하고, 보간(interpolation) 영역에서 사용하세요.\n');

% 임시 파일 정리
delete('example_motor_loss.csv');
delete('example_motor_data.mat');
