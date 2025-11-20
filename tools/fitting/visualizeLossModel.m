function visualizeLossModel(data, rbfModel, options)
% visualizeLossModel - 손실 모델의 시각화 및 검증
%
% 입력:
%   data - 원본 데이터 (구조체 또는 테이블)
%   rbfModel - createLossModel에서 생성된 RBF 모델
%   options - 옵션 구조체 (선택사항):
%             .gridSize - 시각화용 그리드 크기 (기본값: 50)
%             .showError - 오차 플롯 표시 여부 (기본값: true)
%             .save - 그림 저장 여부 (기본값: false)
%             .filename - 저장할 파일명 (기본값: 'loss_model_visualization')

    % 기본 옵션 설정
    if nargin < 3
        options = struct();
    end
    if ~isfield(options, 'gridSize'), options.gridSize = 50; end
    if ~isfield(options, 'showError'), options.showError = true; end
    if ~isfield(options, 'save'), options.save = false; end
    if ~isfield(options, 'filename'), options.filename = 'loss_model_visualization'; end
    
    % 데이터 추출
    id_data = extractField(data, {'id', 'Id'});
    iq_data = extractField(data, {'iq', 'Iq'});
    loss_data = extractField(data, {'loss', 'Loss'});
    
    % 예측값 계산
    predicted_loss = rbfModel.predict(id_data, iq_data);
    error = loss_data - predicted_loss;
    
    % 시각화용 세밀한 그리드 생성
    id_range = linspace(min(id_data), max(id_data), options.gridSize);
    iq_range = linspace(min(iq_data), max(iq_data), options.gridSize);
    [Id_grid, Iq_grid] = meshgrid(id_range, iq_range);
    Loss_grid = rbfModel.predict(Id_grid, Iq_grid);
    
    % 메인 시각화
    if options.showError
        fig1 = figure('Position', [100, 100, 1200, 800]);
        
        % 원본 데이터 (3D scatter)
        subplot(2,3,1);
        scatter3(id_data, iq_data, loss_data, 30, loss_data, 'filled');
        xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('Loss (W)');
        title('원본 데이터');
        colorbar; grid on;
        
        % 예측 데이터 (3D scatter)
        subplot(2,3,2);
        scatter3(id_data, iq_data, predicted_loss, 30, predicted_loss, 'filled');
        xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('Loss (W)');
        title('RBF 예측');
        colorbar; grid on;
        
        % 오차 (3D scatter)
        subplot(2,3,3);
        scatter3(id_data, iq_data, error, 30, error, 'filled');
        xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('Error (W)');
        title('예측 오차');
        colorbar; grid on;
        
        % 손실 맵 (contour)
        subplot(2,3,4);
        contourf(Id_grid, Iq_grid, Loss_grid, 20);
        hold on;
        scatter(id_data, iq_data, 20, 'k', 'filled', 'MarkerFaceAlpha', 0.5);
        xlabel('Id (A)'); ylabel('Iq (A)');
        title('손실 맵 (RBF 모델)');
        colorbar;
        
        % 3D 서페이스
        subplot(2,3,5);
        surf(Id_grid, Iq_grid, Loss_grid);
        shading interp;
        xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('Loss (W)');
        title('3D 손실 서페이스');
        
        % 예측 vs 실제 (패리티 플롯)
        subplot(2,3,6);
        scatter(loss_data, predicted_loss, 30, 'filled', 'MarkerFaceAlpha', 0.7);
        hold on;
        plot([min(loss_data), max(loss_data)], [min(loss_data), max(loss_data)], 'r--', 'LineWidth', 2);
        xlabel('실제 손실 (W)'); ylabel('예측 손실 (W)');
        title('패리티 플롯');
        grid on;
        
        % R² 계산 및 표시
        SS_res = sum((loss_data - predicted_loss).^2);
        SS_tot = sum((loss_data - mean(loss_data)).^2);
        R2 = 1 - SS_res/SS_tot;
        text(0.05, 0.95, sprintf('R² = %.4f', R2), 'Units', 'normalized', ...
             'BackgroundColor', 'white', 'FontSize', 10);
        
    else
        fig1 = figure('Position', [100, 100, 800, 600]);
        
        subplot(2,2,1);
        contourf(Id_grid, Iq_grid, Loss_grid, 20);
        hold on;
        scatter(id_data, iq_data, 20, 'k', 'filled', 'MarkerFaceAlpha', 0.5);
        xlabel('Id (A)'); ylabel('Iq (A)');
        title('손실 맵');
        colorbar;
        
        subplot(2,2,2);
        surf(Id_grid, Iq_grid, Loss_grid);
        shading interp;
        xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('Loss (W)');
        title('3D 손실 서페이스');
        
        subplot(2,2,3);
        scatter(loss_data, predicted_loss, 30, 'filled');
        hold on;
        plot([min(loss_data), max(loss_data)], [min(loss_data), max(loss_data)], 'r--', 'LineWidth', 2);
        xlabel('실제 손실 (W)'); ylabel('예측 손실 (W)');
        title('패리티 플롯');
        grid on;
        
        SS_res = sum((loss_data - predicted_loss).^2);
        SS_tot = sum((loss_data - mean(loss_data)).^2);
        R2 = 1 - SS_res/SS_tot;
        text(0.05, 0.95, sprintf('R² = %.4f', R2), 'Units', 'normalized', ...
             'BackgroundColor', 'white', 'FontSize', 10);
        
        subplot(2,2,4);
        histogram(error, 20);
        xlabel('예측 오차 (W)'); ylabel('빈도');
        title('오차 분포');
        grid on;
    end
    
    % 통계 정보 출력
    rmse = sqrt(mean(error.^2));
    mae = mean(abs(error));
    max_err = max(abs(error));
    
    fprintf('\n=== 모델 성능 통계 ===\n');
    fprintf('RMSE: %.4f W\n', rmse);
    fprintf('MAE: %.4f W\n', mae);
    fprintf('최대 절대 오차: %.4f W\n', max_err);
    fprintf('R²: %.4f\n', R2);
    
    % 그림 저장
    if options.save
        saveas(fig1, [options.filename, '.png']);
        saveas(fig1, [options.filename, '.fig']);
        fprintf('그림이 저장되었습니다: %s.png, %s.fig\n', options.filename, options.filename);
    end
end

function value = extractField(data, fieldNames)
    % 구조체나 테이블에서 필드 추출 (여러 가능한 이름 시도)
    for i = 1:length(fieldNames)
        if istable(data)
            if ismember(fieldNames{i}, data.Properties.VariableNames)
                value = data.(fieldNames{i});
                return;
            end
        else
            if isfield(data, fieldNames{i})
                value = data.(fieldNames{i});
                return;
            end
        end
    end
    error('필드를 찾을 수 없습니다: %s', strjoin(fieldNames, ', '));
end
