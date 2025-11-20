function [performance, predictions] = evaluateRBFModel(rbfFunc, id_test, iq_test, true_values, options)
% evaluateRBFModel - RBF 모델의 성능을 평가
%
% 입력:
%   rbfFunc - RBF 예측 함수
%   id_test - 테스트 Id 값들
%   iq_test - 테스트 Iq 값들  
%   true_values - 실제 값들
%   options - 옵션 구조체 (선택사항):
%             .plot - 결과 플롯 여부 (기본값: false)
%             .title - 플롯 제목 (기본값: 'RBF Model Evaluation')
%
% 출력:
%   performance - 성능 지표 구조체
%   predictions - 예측값들
%
% 사용 예시:
%   [perf, pred] = evaluateRBFModel(rbf_func, id_test, iq_test, true_test);
%   [perf, pred] = evaluateRBFModel(rbf_func, id_test, iq_test, true_test, ...
%                                   struct('plot', true, 'title', 'Flux Linkage Model'));

    % 기본 옵션 설정
    if nargin < 5
        options = struct();
    end
    if ~isfield(options, 'plot'), options.plot = false; end
    if ~isfield(options, 'title'), options.title = 'RBF Model Evaluation'; end
    
    % 입력 검증
    if length(id_test) ~= length(iq_test) || length(id_test) ~= length(true_values)
        error('모든 입력 벡터의 길이가 일치해야 합니다.');
    end
    
    % NaN 값 제거
    valid_idx = ~(isnan(id_test) | isnan(iq_test) | isnan(true_values));
    if sum(~valid_idx) > 0
        fprintf('경고: %d개의 NaN 값이 제거됩니다.\n', sum(~valid_idx));
        id_test = id_test(valid_idx);
        iq_test = iq_test(valid_idx);
        true_values = true_values(valid_idx);
    end
    
    % 예측 수행
    try
        predictions = rbfFunc(id_test, iq_test);
    catch ME
        error('예측 중 오류 발생: %s', ME.message);
    end
    
    % 성능 지표 계산
    errors = true_values - predictions;
    
    performance.rmse = sqrt(mean(errors.^2));
    performance.mae = mean(abs(errors));
    performance.max_error = max(abs(errors));
    performance.min_error = min(abs(errors));
    performance.std_error = std(errors);
    
    % R² 계산
    ss_res = sum(errors.^2);
    ss_tot = sum((true_values - mean(true_values)).^2);
    performance.r2 = 1 - ss_res/ss_tot;
    
    % 상대 오차 (%)
    performance.relative_rmse = performance.rmse / mean(abs(true_values)) * 100;
    performance.relative_mae = performance.mae / mean(abs(true_values)) * 100;
    
    % 데이터 통계
    performance.n_points = length(true_values);
    performance.true_mean = mean(true_values);
    performance.true_std = std(true_values);
    performance.pred_mean = mean(predictions);
    performance.pred_std = std(predictions);
    
    % 결과 출력
    fprintf('\n=== RBF 모델 성능 평가 ===\n');
    fprintf('데이터 포인트 수: %d\n', performance.n_points);
    fprintf('RMSE: %.4f (%.2f%%)\n', performance.rmse, performance.relative_rmse);
    fprintf('MAE: %.4f (%.2f%%)\n', performance.mae, performance.relative_mae);
    fprintf('최대 오차: %.4f\n', performance.max_error);
    fprintf('R²: %.4f\n', performance.r2);
    fprintf('실제값 범위: [%.4f, %.4f]\n', min(true_values), max(true_values));
    fprintf('예측값 범위: [%.4f, %.4f]\n', min(predictions), max(predictions));
    
    % 시각화
    if options.plot
        figure('Position', [100, 100, 1200, 400]);
        
        % 패리티 플롯
        subplot(1,3,1);
        scatter(true_values, predictions, 30, 'filled', 'MarkerFaceAlpha', 0.7);
        hold on;
        min_val = min([true_values; predictions]);
        max_val = max([true_values; predictions]);
        plot([min_val, max_val], [min_val, max_val], 'r--', 'LineWidth', 2);
        xlabel('실제값'); ylabel('예측값');
        title('패리티 플롯');
        grid on;
        text(0.05, 0.95, sprintf('R² = %.4f', performance.r2), ...
             'Units', 'normalized', 'BackgroundColor', 'white', 'FontSize', 10);
        
        % 오차 분포
        subplot(1,3,2);
        histogram(errors, 20, 'Normalization', 'probability');
        xlabel('예측 오차'); ylabel('확률');
        title('오차 분포');
        grid on;
        xline(0, 'r--', 'LineWidth', 2);
        
        % 오차 vs 예측값
        subplot(1,3,3);
        scatter(predictions, errors, 30, 'filled', 'MarkerFaceAlpha', 0.7);
        xlabel('예측값'); ylabel('예측 오차');
        title('잔차 플롯');
        grid on;
        yline(0, 'r--', 'LineWidth', 2);
        
        sgtitle(options.title);
    end
end
