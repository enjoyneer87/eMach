function net = trainRBF_DNN(geometryVars, currentNorm, targetVar, options)
% trainRBF_DNN - RBF 계수들을 DNN으로 학습하는 함수
%
% 입력:
%   geometryVars - 기하학적 변수들 [N x M] (예: 자석 두께, 슬롯 폭 등)
%   currentNorm - 정규화된 전류 조건 [N x 2] (Id_norm, Iq_norm)
%   targetVar - 목표 변수 (RBF 계수들) [N x K] (weights 또는 coeffs)
%   options - 옵션 구조체 (선택사항)
%
% 출력:
%   net - 훈련된 신경망 모델
%
% 사용 예시:
%   % 기하학적 변수들 (예시)
%   geometry = [magnet_thickness, slot_width, air_gap];
%   current = [Id_norm, Iq_norm];
%   
%   % RBF weights를 DNN으로 학습
%   net_weights = trainRBF_DNN(geometry, current, rbf_weights);
%   
%   % 새로운 기하학적 조건에서 RBF weights 예측
%   new_weights = predict(net_weights, [new_geometry, new_current]);

    % 기본 옵션 설정
    if nargin < 4
        options = struct();
    end
    if ~isfield(options, 'hiddenLayers'), options.hiddenLayers = [64, 32, 16]; end
    if ~isfield(options, 'trainRatio'), options.trainRatio = 0.7; end
    if ~isfield(options, 'valRatio'), options.valRatio = 0.15; end
    if ~isfield(options, 'testRatio'), options.testRatio = 0.15; end
    if ~isfield(options, 'useRBFBasis'), options.useRBFBasis = true; end
    if ~isfield(options, 'rbfCenters'), options.rbfCenters = 36; end  % 6x6 그리드
    if ~isfield(options, 'rbfSigma'), options.rbfSigma = 0.3; end
    if ~isfield(options, 'verbose'), options.verbose = true; end
    if ~isfield(options, 'plotResults'), options.plotResults = true; end
    
    % 입력 데이터 검증
    if size(geometryVars, 1) ~= size(currentNorm, 1) || size(geometryVars, 1) ~= size(targetVar, 1)
        error('모든 입력 데이터의 행 수가 일치해야 합니다.');
    end
    
    % NaN 값 제거
    valid_idx = ~any(isnan(geometryVars), 2) & ~any(isnan(currentNorm), 2) & ~any(isnan(targetVar), 2);
    geometryVars = geometryVars(valid_idx, :);
    currentNorm = currentNorm(valid_idx, :);
    targetVar = targetVar(valid_idx, :);
    
    if options.verbose
        fprintf('유효한 데이터 포인트: %d개\n', size(geometryVars, 1));
        fprintf('기하학적 변수 수: %d개\n', size(geometryVars, 2));
        fprintf('출력 변수 수: %d개\n', size(targetVar, 2));
    end
    
    % RBF Basis 생성 (선택사항)
    if options.useRBFBasis
        % RBF 중심점 설정 (균등 분포)
        grid_size = round(sqrt(options.rbfCenters));
        [idGrid, iqGrid] = meshgrid(linspace(-1, 1, grid_size), linspace(0, 1, grid_size));
        centers = [idGrid(:), iqGrid(:)];
        
        % RBF Basis 계산 (Gaussian RBF)
        distances = pdist2(currentNorm, centers);
        rbfBasis = exp(-distances.^2 / (2 * options.rbfSigma^2));
        
        % 입력 특성 결합: [기하학적 변수, RBF(current)]
        inputFeatures = [geometryVars, rbfBasis];
        
        if options.verbose
            fprintf('RBF Basis 추가: %d개 중심점\n', size(centers, 1));
        end
    else
        % 입력 특성 결합: [기하학적 변수, 전류]
        inputFeatures = [geometryVars, currentNorm];
    end
    
    if options.verbose
        fprintf('총 입력 특성 수: %d개\n', size(inputFeatures, 2));
    end
    
    % 데이터 분할
    numSamples = size(inputFeatures, 1);
    randIdx = randperm(numSamples);
    
    trainEnd = round(options.trainRatio * numSamples);
    valEnd = trainEnd + round(options.valRatio * numSamples);
    
    trainIdx = randIdx(1:trainEnd);
    valIdx = randIdx(trainEnd+1:valEnd);
    testIdx = randIdx(valEnd+1:end);
    
    % 훈련/검증/테스트 데이터
    X_train = inputFeatures(trainIdx, :)';
    Y_train = targetVar(trainIdx, :)';
    
    if ~isempty(valIdx)
        X_val = inputFeatures(valIdx, :)';
        Y_val = targetVar(valIdx, :)';
    end
    
    if ~isempty(testIdx)
        X_test = inputFeatures(testIdx, :)';
        Y_test = targetVar(testIdx, :)';
    end
    
    if options.verbose
        fprintf('훈련: %d개, 검증: %d개, 테스트: %d개\n', ...
            length(trainIdx), length(valIdx), length(testIdx));
    end
    
    % 신경망 생성 및 설정
    net = fitnet(options.hiddenLayers);
    net.trainParam.showWindow = options.verbose;
    net.trainParam.epochs = 1000;
    net.trainParam.goal = 1e-6;
    net.trainParam.max_fail = 20;
    
    % 데이터 분할 설정
    if ~isempty(valIdx) && ~isempty(testIdx)
        net.divideParam.trainRatio = options.trainRatio;
        net.divideParam.valRatio = options.valRatio;
        net.divideParam.testRatio = options.testRatio;
    end
    
    % 신경망 훈련
    if options.verbose
        fprintf('\n신경망 훈련 시작...\n');
    end
    
    [net, tr] = train(net, X_train, Y_train);
    
    % 테스트 성능 평가
    if ~isempty(testIdx)
        Y_test_pred = net(X_test);
        
        % 성능 지표 계산
        errors = Y_test - Y_test_pred;
        rmse = sqrt(mean(errors.^2, 'all'));
        mae = mean(abs(errors), 'all');
        r2 = 1 - sum(errors.^2, 'all') / sum((Y_test - mean(Y_test, 'all')).^2, 'all');
        
        if options.verbose
            fprintf('\n=== 테스트 성능 ===\n');
            fprintf('RMSE: %.6f\n', rmse);
            fprintf('MAE: %.6f\n', mae);
            fprintf('R²: %.6f\n', r2);
        end
        
        % 결과 시각화
        if options.plotResults
            figure('Position', [100, 100, 1200, 400]);
            
            % 실제값 vs 예측값
            subplot(1,3,1);
            scatter(Y_test(:), Y_test_pred(:), 30, 'filled', 'MarkerFaceAlpha', 0.7);
            hold on;
            min_val = min([Y_test(:); Y_test_pred(:)]);
            max_val = max([Y_test(:); Y_test_pred(:)]);
            plot([min_val, max_val], [min_val, max_val], 'r--', 'LineWidth', 2);
            xlabel('실제값'); ylabel('예측값');
            title('DNN 예측 성능');
            grid on;
            text(0.05, 0.95, sprintf('R² = %.4f', r2), ...
                 'Units', 'normalized', 'BackgroundColor', 'white');
            
            % 오차 분포
            subplot(1,3,2);
            histogram(errors(:), 20, 'Normalization', 'probability');
            xlabel('예측 오차'); ylabel('확률');
            title('오차 분포');
            grid on;
            xline(0, 'r--', 'LineWidth', 2);
            
            % 훈련 곡선
            subplot(1,3,3);
            plot(1:length(tr.perf), tr.perf, 'b-', 'LineWidth', 2);
            hold on;
            if ~isempty(tr.vperf)
                plot(1:length(tr.vperf), tr.vperf, 'r-', 'LineWidth', 2);
                legend('Training', 'Validation', 'Location', 'best');
            end
            xlabel('Epoch'); ylabel('Performance (MSE)');
            title('훈련 곡선');
            grid on;
            set(gca, 'YScale', 'log');
            
            sgtitle('DNN 훈련 결과');
        end
        
        % 성능 정보를 net에 저장
        net.UserData.performance.rmse = rmse;
        net.UserData.performance.mae = mae;
        net.UserData.performance.r2 = r2;
    end
    
    % 추가 정보 저장
    net.UserData.options = options;
    if options.useRBFBasis
        net.UserData.rbf_centers = centers;
        net.UserData.rbf_sigma = options.rbfSigma;
    end
    net.UserData.input_size = [size(geometryVars, 2), 2];  % [geometry_vars, current_vars]
    
    if options.verbose
        fprintf('DNN 훈련 완료!\n');
    end
end
