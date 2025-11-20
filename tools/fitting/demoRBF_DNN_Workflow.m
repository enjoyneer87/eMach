%% RBF-DNN 통합 워크플로우 데모
% RBF 모델링부터 DNN 학습, 새로운 geometry 예측까지 전체 과정 데모

% 작성자: MATLAB Copilot
% 버전: 1.0
% 날짜: 2024

clear; clc;
fprintf('=== RBF-DNN 통합 워크플로우 데모 ===\n\n');

%% 1. 가상 데이터 생성 (실제로는 FEA 데이터 사용)
fprintf('1. 가상 모터 데이터를 생성합니다...\n');

% Id, Iq 그리드
id_range = -200:20:0;
iq_range = 0:20:300;
[ID, IQ] = meshgrid(id_range, iq_range);
id_data = ID(:);
iq_data = IQ(:);

% 가상의 손실 함수들
core_loss = 10 + 0.001*id_data.^2 + 0.002*iq_data.^2 + 0.0001*id_data.*iq_data + 0.5*randn(size(id_data));
copper_loss = 5 + 0.0005*(id_data.^2 + iq_data.^2) + 0.3*randn(size(id_data));
magnet_loss = 2 + 0.0002*id_data.^2 + 0.0003*iq_data.^2 + 0.2*randn(size(id_data));

% 음수 손실 제거
core_loss = max(core_loss, 0.1);
copper_loss = max(copper_loss, 0.1);
magnet_loss = max(magnet_loss, 0.1);

% 데이터 구조체 생성
data.Id = id_data;
data.Iq = iq_data;
data.CoreLoss = core_loss;
data.CopperLoss = copper_loss;
data.MagnetLoss = magnet_loss;

fprintf('  생성된 데이터 점 수: %d\n', length(id_data));
fprintf('  Id 범위: [%.0f, %.0f] A\n', min(id_data), max(id_data));
fprintf('  Iq 범위: [%.0f, %.0f] A\n', min(iq_data), max(iq_data));

%% 2. 기본 RBF 모델 학습
fprintf('\n2. 기본 RBF 모델을 학습합니다...\n');

% CoreLoss에 대한 RBF 모델
[weights, centers, bias] = trainRBFThinplate(id_data, iq_data, core_loss);

if ~isempty(weights)
    fprintf('  RBF 모델 학습 성공!\n');
    fprintf('  센터 개수: %d\n', size(centers, 1));
    fprintf('  계수 범위: [%.2e, %.2e]\n', min(weights), max(weights));
    
    % 간단한 성능 테스트
    pred_core_loss = zeros(size(core_loss));
    for i = 1:length(id_data)
        pred_core_loss(i) = evaluateRBFThinplate([id_data(i), iq_data(i)], weights, centers, bias);
    end
    
    % R² 계산
    ss_res = sum((core_loss - pred_core_loss).^2);
    ss_tot = sum((core_loss - mean(core_loss)).^2);
    r2 = 1 - ss_res/ss_tot;
    
    fprintf('  기본 RBF 모델 R²: %.4f\n', r2);
else
    error('RBF 모델 학습 실패!');
end

%% 3. 여러 geometry에 대한 RBF 계수 데이터 생성
fprintf('\n3. 여러 geometry에 대한 RBF 계수를 생성합니다...\n');

n_geometries = 30;
rng(42); % 재현 가능한 결과

% Geometry 변수들
geometryVars = struct();
geometryVars.stator_slot_num = randi([12, 48], n_geometries, 1);
geometryVars.rotor_pole_num = randi([8, 32], n_geometries, 1);
geometryVars.air_gap = 0.5 + 1.5*rand(n_geometries, 1);
geometryVars.stack_length = 50 + 100*rand(n_geometries, 1);
geometryVars.magnet_thickness = 2 + 6*rand(n_geometries, 1);
currentNorm = 50 + 200*rand(n_geometries, 1);

% 각 geometry에 대해 RBF 계수 추출
rbf_coefficients = [];
geometry_features = [];

for geo_idx = 1:n_geometries
    % 현재 geometry에 대한 손실 데이터 변형
    scale_factor = 0.5 + rand(); % 0.5 ~ 1.5 스케일
    noise_factor = 0.1 + 0.1*rand(); % 10-20% 노이즈
    
    current_loss = core_loss * scale_factor .* (1 + noise_factor * (rand(size(core_loss)) - 0.5));
    current_loss = max(current_loss, 0.1); % 음수 제거
    
    % RBF 모델 학습
    try
        [weights_i, centers_i, bias_i] = trainRBFThinplate(id_data, iq_data, current_loss);
        
        if ~isempty(weights_i) && ~any(isnan(weights_i))
            % 고정 크기로 변환
            max_centers = 50;
            if length(weights_i) > max_centers
                weights_fixed = weights_i(1:max_centers);
            else
                weights_fixed = [weights_i; zeros(max_centers - length(weights_i), 1)];
            end
            
            rbf_coefficients = [rbf_coefficients; weights_fixed'];
            
            geo_vector = [geometryVars.stator_slot_num(geo_idx), ...
                         geometryVars.rotor_pole_num(geo_idx), ...
                         geometryVars.air_gap(geo_idx), ...
                         geometryVars.stack_length(geo_idx), ...
                         geometryVars.magnet_thickness(geo_idx), ...
                         currentNorm(geo_idx)];
            geometry_features = [geometry_features; geo_vector];
        end
    catch ME
        fprintf('  Geometry %d 실패: %s\n', geo_idx, ME.message);
    end
end

fprintf('  성공적으로 생성된 데이터 세트: %d개\n', size(rbf_coefficients, 1));

%% 4. DNN 학습
if size(rbf_coefficients, 1) >= 10
    fprintf('\n4. DNN으로 RBF 계수를 학습합니다...\n');
    
    % DNN 옵션
    dnn_options = struct();
    dnn_options.hidden_layers = [30, 20];
    dnn_options.max_epochs = 150;
    dnn_options.learning_rate = 0.001;
    dnn_options.train_ratio = 0.7;
    dnn_options.val_ratio = 0.2;
    dnn_options.use_rbf_basis = false;
    dnn_options.verbose = false; % 간소화된 출력
    
    try
        [dnn_model, train_info] = trainRBF_DNN(geometry_features, currentNorm, rbf_coefficients, dnn_options);
        
        fprintf('  DNN 학습 완료!\n');
        fprintf('  최종 검증 MSE: %.6f\n', train_info.val_mse);
        fprintf('  최종 검증 R²: %.4f\n', train_info.val_r2);
        
        dnn_success = true;
        
    catch ME
        fprintf('  DNN 학습 실패: %s\n', ME.message);
        dnn_success = false;
    end
else
    fprintf('\n4. DNN 학습을 위한 데이터 부족 (현재 %d개, 최소 10개 필요)\n', size(rbf_coefficients, 1));
    dnn_success = false;
end

%% 5. 새로운 geometry 예측
if dnn_success
    fprintf('\n5. 새로운 geometry에 대한 손실 맵을 생성합니다...\n');
    
    % 새로운 geometry 정의
    new_geo = struct();
    new_geo.stator_slot_num = 24;
    new_geo.rotor_pole_num = 16;
    new_geo.air_gap = 1.0;
    new_geo.stack_length = 80;
    new_geo.magnet_thickness = 4.0;
    new_current_norm = 120;
    
    fprintf('  새로운 geometry:\n');
    fprintf('    - Stator slots: %d\n', new_geo.stator_slot_num);
    fprintf('    - Rotor poles: %d\n', new_geo.rotor_pole_num);
    fprintf('    - Air gap: %.1f mm\n', new_geo.air_gap);
    fprintf('    - Stack length: %.1f mm\n', new_geo.stack_length);
    fprintf('    - Magnet thickness: %.1f mm\n', new_geo.magnet_thickness);
    fprintf('    - Current norm: %.1f A\n', new_current_norm);
    
    try
        % generateLossMapFromGeometry 함수 사용
        [loss_map, ID_pred, IQ_pred] = generateLossMapFromGeometry(...
            dnn_model, new_geo, new_current_norm, ...
            [-200, 0], [0, 300], ...
            'GridSize', [15, 15], ...
            'Verbose', false);
        
        fprintf('  손실 맵 생성 완료!\n');
        fprintf('  예측된 손실 범위: [%.2e, %.2e]\n', min(loss_map(:)), max(loss_map(:)));
        
        map_success = true;
        
    catch ME
        fprintf('  손실 맵 생성 실패: %s\n', ME.message);
        map_success = false;
    end
else
    map_success = false;
end

%% 6. 결과 시각화
fprintf('\n6. 결과를 시각화합니다...\n');

figure('Name', 'RBF-DNN 워크플로우 데모 결과', 'Position', [100, 100, 1400, 800]);

% 원본 데이터
subplot(2,3,1);
scatter(id_data, iq_data, 30, core_loss, 'filled');
colorbar; title('원본 CoreLoss 데이터');
xlabel('Id (A)'); ylabel('Iq (A)');

% 기본 RBF 모델 예측
subplot(2,3,2);
if exist('pred_core_loss', 'var')
    scatter(id_data, iq_data, 30, pred_core_loss, 'filled');
    colorbar; title(sprintf('기본 RBF 예측 (R²=%.3f)', r2));
    xlabel('Id (A)'); ylabel('Iq (A)');
end

% Geometry 특성 분포
subplot(2,3,3);
if exist('geometry_features', 'var') && ~isempty(geometry_features)
    scatter3(geometry_features(:,1), geometry_features(:,2), geometry_features(:,3), 50, 'filled');
    xlabel('Stator Slots'); ylabel('Rotor Poles'); zlabel('Air Gap (mm)');
    title('Geometry 특성 분포');
    grid on;
end

% DNN 학습 곡선
subplot(2,3,4);
if dnn_success && isfield(train_info, 'train_mse_history')
    epochs = 1:length(train_info.train_mse_history);
    semilogy(epochs, train_info.train_mse_history, 'b-', 'LineWidth', 2);
    hold on;
    if isfield(train_info, 'val_mse_history')
        semilogy(epochs, train_info.val_mse_history, 'r--', 'LineWidth', 2);
        legend('Train MSE', 'Val MSE', 'Location', 'best');
    end
    xlabel('Epoch'); ylabel('MSE'); title('DNN 학습 곡선');
    grid on;
else
    text(0.5, 0.5, 'DNN 학습 없음', 'HorizontalAlignment', 'center');
    title('DNN 학습 결과');
end

% 예측된 손실 맵 (3D)
subplot(2,3,5);
if map_success
    surf(ID_pred, IQ_pred, loss_map);
    xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('CoreLoss');
    title('DNN 예측 손실 맵 (3D)');
    shading interp;
else
    text(0.5, 0.5, '손실 맵 생성 없음', 'HorizontalAlignment', 'center');
    title('예측 손실 맵');
end

% 예측된 손실 맵 (Contour)
subplot(2,3,6);
if map_success
    contourf(ID_pred, IQ_pred, loss_map, 15);
    colorbar; xlabel('Id (A)'); ylabel('Iq (A)');
    title('DNN 예측 손실 맵 (Contour)');
else
    text(0.5, 0.5, '손실 맵 생성 없음', 'HorizontalAlignment', 'center');
    title('예측 손실 맵 (Contour)');
end

%% 7. 요약 및 결론
fprintf('\n=== 데모 요약 ===\n');
fprintf('1. 가상 모터 데이터 생성: 완료 (%d개 점)\n', length(id_data));
fprintf('2. 기본 RBF 모델 학습: ');
if exist('r2', 'var')
    fprintf('완료 (R² = %.4f)\n', r2);
else
    fprintf('실패\n');
end
fprintf('3. 다중 geometry RBF 계수 추출: ');
if exist('rbf_coefficients', 'var')
    fprintf('완료 (%d개 geometry)\n', size(rbf_coefficients, 1));
else
    fprintf('실패\n');
end
fprintf('4. DNN 학습: ');
if dnn_success
    fprintf('완료 (검증 R² = %.4f)\n', train_info.val_r2);
else
    fprintf('실패 또는 건너뜀\n');
end
fprintf('5. 새로운 geometry 예측: ');
if map_success
    fprintf('완료 (손실 범위: %.2e ~ %.2e)\n', min(loss_map(:)), max(loss_map(:)));
else
    fprintf('실패 또는 건너뜀\n');
end

fprintf('\n데모가 완료되었습니다!\n');
fprintf('실제 사용 시에는:\n');
fprintf('  - 실제 FEA 데이터를 사용하세요\n');
fprintf('  - 더 많은 geometry 샘플을 준비하세요 (100개 이상 권장)\n');
fprintf('  - DNN 하이퍼파라미터를 조정하세요\n');
fprintf('  - 검증 데이터로 모델 성능을 확인하세요\n');

%% 8. 모델 저장 (선택적)
if dnn_success
    fprintf('\n모델을 저장하시겠습니까? (y/n): ');
    user_input = input('', 's');
    if strcmpi(user_input, 'y') || strcmpi(user_input, 'yes')
        save('demo_rbf_dnn_model.mat', 'dnn_model', 'train_info', 'dnn_options', ...
             'geometry_features', 'rbf_coefficients', 'new_geo');
        fprintf('모델이 저장되었습니다: demo_rbf_dnn_model.mat\n');
    end
end

fprintf('\n감사합니다!\n');
