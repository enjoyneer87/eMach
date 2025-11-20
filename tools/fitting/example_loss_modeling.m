%% RBF Thin Plate Spline을 이용한 손실 모델링 예시
% 이 스크립트는 trainRBFThinplate 함수를 사용하여
% id, iq 조건에 따른 손실(loss)을 모델링하는 방법을 보여줍니다.

clear; clc; close all;

%% 1. 샘플 데이터 생성 (실제로는 측정 또는 시뮬레이션 데이터를 사용)
% id, iq 그리드 생성
id_range = -200:20:200;  % A
iq_range = 0:20:300;     % A

[Id_grid, Iq_grid] = meshgrid(id_range, iq_range);
Id_vec = Id_grid(:);
Iq_vec = Iq_grid(:);

% 예시 손실 함수 (실제로는 측정/시뮬레이션 데이터)
% 동손실 + 철손 + 기타 손실의 조합으로 가정
R_copper = 0.1;  % 구리 저항 (Ohm)
loss_copper = R_copper * (Id_vec.^2 + Iq_vec.^2);  % 동손실

% 철손 (주파수와 자속밀도에 의존하지만 여기서는 간단히 모델링)
loss_iron = 50 + 0.001 * (Id_vec.^2 + Iq_vec.^2);

% 기계적 손실 (일정)
loss_mechanical = 20;

% 총 손실
total_loss = loss_copper + loss_iron + loss_mechanical;

%% 2. RBF 모델 훈련
fprintf('RBF 모델을 훈련 중...\n');
[rbfFunc, weights, coeffs, centers] = trainRBFThinplate(Id_vec, Iq_vec, total_loss);
fprintf('훈련 완료!\n');

%% 3. 모델 검증
% 원본 데이터로 예측
predicted_loss = rbfFunc(Id_vec, Iq_vec);

% 오차 계산
rmse = sqrt(mean((total_loss - predicted_loss).^2));
max_error = max(abs(total_loss - predicted_loss));
mean_error = mean(abs(total_loss - predicted_loss));

fprintf('\n=== 모델 성능 ===\n');
fprintf('RMSE: %.4f W\n', rmse);
fprintf('최대 오차: %.4f W\n', max_error);
fprintf('평균 절대 오차: %.4f W\n', mean_error);

%% 4. 새로운 조건에서 예측
% 새로운 id, iq 조건
new_id = [-150, -100, -50, 0, 50, 100, 150];
new_iq = [50, 100, 150, 200, 250];

[New_Id, New_Iq] = meshgrid(new_id, new_iq);
predicted_new_loss = rbfFunc(New_Id, New_Iq);

fprintf('\n=== 새로운 조건에서의 예측 ===\n');
fprintf('Id = %g A, Iq = %g A에서 예상 손실: %.2f W\n', ...
    [New_Id(:), New_Iq(:), predicted_new_loss(:)]');

%% 5. 시각화
figure('Position', [100, 100, 1200, 400]);

% 원본 데이터
subplot(1,3,1);
scatter3(Id_vec, Iq_vec, total_loss, 20, total_loss, 'filled');
xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('Loss (W)');
title('원본 데이터');
colorbar; grid on;

% 예측 데이터
subplot(1,3,2);
scatter3(Id_vec, Iq_vec, predicted_loss, 20, predicted_loss, 'filled');
xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('Loss (W)');
title('RBF 예측');
colorbar; grid on;

% 오차
subplot(1,3,3);
error = total_loss - predicted_loss;
scatter3(Id_vec, Iq_vec, error, 20, error, 'filled');
xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('Error (W)');
title('예측 오차');
colorbar; grid on;

%% 6. 컨투어 플롯으로 손실 맵 표시
figure('Position', [100, 600, 800, 300]);

% 더 세밀한 그리드로 예측
id_fine = linspace(min(id_range), max(id_range), 50);
iq_fine = linspace(min(iq_range), max(iq_range), 50);
[Id_fine, Iq_fine] = meshgrid(id_fine, iq_fine);

loss_fine = rbfFunc(Id_fine, Iq_fine);

subplot(1,2,1);
contourf(Id_fine, Iq_fine, loss_fine, 20);
hold on;
scatter(Id_vec, Iq_vec, 30, 'k', 'filled', 'MarkerFaceAlpha', 0.7);
xlabel('Id (A)'); ylabel('Iq (A)');
title('손실 맵 (RBF 모델)');
colorbar; 

subplot(1,2,2);
surf(Id_fine, Iq_fine, loss_fine);
shading interp;
xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('Loss (W)');
title('3D 손실 서페이스');
colorbar;

%% 7. 실제 테이블 데이터를 사용하는 경우의 예시
fprintf('\n=== 실제 테이블 데이터 사용 예시 ===\n');
fprintf('테이블 데이터가 있다면 다음과 같이 사용하세요:\n\n');
fprintf('%% 테이블에서 데이터 로드\n');
fprintf('%% data = readtable(''loss_data.csv'');\n');
fprintf('%% id_data = data.Id;\n');
fprintf('%% iq_data = data.Iq;\n');
fprintf('%% loss_data = data.Loss;\n\n');
fprintf('%% RBF 모델 훈련\n');
fprintf('%% [rbfFunc, weights, coeffs, centers] = trainRBFThinplate(id_data, iq_data, loss_data);\n\n');
fprintf('%% 새로운 조건에서 예측\n');
fprintf('%% predicted_loss = rbfFunc(new_id, new_iq);\n');
