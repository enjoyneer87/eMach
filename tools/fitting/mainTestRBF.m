%% RBF 모델링 테스트 스크립트
% 각 섹션별로 실행 가능하도록 구성
% Ctrl+Enter로 섹션별 실행, F9로 선택한 줄만 실행 가능

%% 1. 경로 설정 및 초기화
clear; clc; close all;

JMAGParentPath = 'F:\KDH\KDH';
parentPath = 'F:\KDH\Thesis\JEET';

%% 2. 파일 목록 가져오기
[motFileList, ~] = getResultMotMatList(parentPath);
fprintf('발견된 MOT 파일 수: %d\n', length(motFileList));

% 첫 번째 파일 정보 출력
if ~isempty(motFileList)
    fprintf('첫 번째 파일: %s\n', motFileList{1});
end

%% 3. 다중 MOT 파일 데이터 로드 및 전처리
fprintf('\n=== 다중 MOT 파일 처리 ===\n');

% 모든 geometry 데이터를 저장할 구조체 초기화
all_geometry_data = [];
all_target_data = [];
geometry_labels = {};

% 각 MOT 파일에 대해 반복 처리
valid_file_count = 0;
for file_idx = 1:length(motFileList)
    try
        fprintf('[%d/%d] 처리 중: %s\n', file_idx, length(motFileList), motFileList{file_idx});
        
        % 현재 파일 데이터 로드
        filteredTable = getMCADLabDataFromMotFile(motFileList{file_idx});
        
        if isempty(filteredTable) || height(filteredTable) < 5
            fprintf('  건너뛰기: 데이터가 부족합니다 (행 수: %d)\n', height(filteredTable));
            continue;
        end
        
        originLabLinkTable = reNameLabTable2LabLink(filteredTable);
        IdqTable = filterTablewithString(filteredTable, 'Peak');
        currentTable = mergeTables(originLabLinkTable, IdqTable);
        
        fprintf('  테이블 크기: %d x %d\n', size(currentTable));
        
        % Id, Iq 데이터 추출
        idVarIdx = contains(currentTable.Properties.VariableNames, 'Id', 'IgnoreCase', true);
        iqVarIdx = contains(currentTable.Properties.VariableNames, 'Iq', 'IgnoreCase', true);
        
        if ~any(idVarIdx) || ~any(iqVarIdx)
            fprintf('  건너뛰기: Id 또는 Iq 변수를 찾을 수 없습니다.\n');
            continue;
        end
        
        idVarName = currentTable.Properties.VariableNames{find(idVarIdx, 1)};
        iqVarName = currentTable.Properties.VariableNames{find(iqVarIdx, 1)};
        
        current_id = currentTable.(idVarName);
        current_iq = currentTable.(iqVarName);
        
        % 유효한 데이터 확인
        valid_idx = ~isnan(current_id) & ~isnan(current_iq);
        if sum(valid_idx) < 10
            fprintf('  건너뛰기: 유효한 Id, Iq 데이터가 부족합니다 (%d개)\n', sum(valid_idx));
            continue;
        end
        
        % 파일명에서 geometry 정보 추출 (실제 파일명 패턴에 맞게 조정 필요)
        [~, filename, ~] = fileparts(motFileList{file_idx});
        
        % geometry 파라미터 추출 (예시 - 실제 파일명 패턴에 맞게 수정 필요)
        % 파일명에서 숫자 추출하여 geometry 파라미터로 사용
        numbers = regexp(filename, '\d+', 'match');
        if length(numbers) >= 3
            stator_slots = str2double(numbers{1});
            rotor_poles = str2double(numbers{2});
            geometry_id = str2double(numbers{3});
        else
            % 기본값 또는 파일 인덱스 기반
            stator_slots = 24 + mod(file_idx*3, 24); % 24-48 범위
            rotor_poles = 8 + mod(file_idx*2, 16);   % 8-24 범위
            geometry_id = file_idx;
        end
        
        % 추가 geometry 파라미터 (랜덤 또는 파일에서 추출)
        rng(file_idx); % 재현 가능한 랜덤
        air_gap = 0.5 + 1.5*rand(); % 0.5-2.0 mm
        stack_length = 50 + 100*rand(); % 50-150 mm
        magnet_thickness = 2 + 6*rand(); % 2-8 mm
        
        % 현재 geometry의 특성 벡터
        current_geometry = [stator_slots, rotor_poles, air_gap, stack_length, magnet_thickness];
        
        % 전류 크기 (RMS 또는 정격값 추정)
        current_norm = sqrt(mean(current_id.^2 + current_iq.^2));
        
        % target 변수들 추출 (Id, Iq 제외한 모든 수치형 변수)
        target_table = currentTable;
        
        % Id, Iq 변수 제거
        excludeVars = {'Id', 'Iq'};
        for i = 1:length(excludeVars)
            varIdx = contains(target_table.Properties.VariableNames, excludeVars{i}, 'IgnoreCase', true);
            if any(varIdx)
                varsToRemove = target_table.Properties.VariableNames(varIdx);
                target_table = removevars(target_table, varsToRemove);
            end
        end
        
        % 수치형 변수만 선택
        numeric_vars = {};
        for i = 1:width(target_table)
            if isnumeric(target_table{:, i})
                numeric_vars{end+1} = target_table.Properties.VariableNames{i};
            end
        end
        
        if isempty(numeric_vars)
            fprintf('  건너뛰기: 수치형 target 변수가 없습니다.\n');
            continue;
        end
        
        % 각 target 변수에 대한 RBF 계수 추출
        fprintf('  %d개의 target 변수 처리 중...\n', length(numeric_vars));
        
        current_geometry_expanded = [];
        current_targets = [];
        current_coefficients = [];
        
        for var_idx = 1:length(numeric_vars)
            var_name = numeric_vars{var_idx};
            target_data = target_table.(var_name);
            
            % 현재 변수의 유효한 데이터
            var_valid_idx = valid_idx & ~isnan(target_data);
            
            if sum(var_valid_idx) < 10
                continue; % 데이터 부족
            end
            
            try
                % RBF 모델 학습
                [weights, centers, bias] = trainRBFThinplate(...
                    current_id(var_valid_idx), ...
                    current_iq(var_valid_idx), ...
                    target_data(var_valid_idx));
                
                if ~isempty(weights) && ~any(isnan(weights))
                    % 고정 크기로 변환 (패딩 또는 샘플링)
                    max_coeffs = 50; % 최대 계수 개수
                    if length(weights) > max_coeffs
                        weights_fixed = weights(1:max_coeffs);
                    else
                        weights_fixed = [weights; zeros(max_coeffs - length(weights), 1)];
                    end
                    
                    % 데이터 저장
                    current_geometry_expanded = [current_geometry_expanded; ...
                        [current_geometry, current_norm, var_idx]]; % geometry + current_norm + variable_id
                    current_targets = [current_targets; {var_name}];
                    current_coefficients = [current_coefficients; weights_fixed'];
                    
                    fprintf('    %s: RBF 계수 %d개 추출\n', var_name, length(weights));
                end
                
            catch ME
                fprintf('    %s: RBF 학습 실패 - %s\n', var_name, ME.message);
            end
        end
        
        % 현재 파일의 데이터를 전체 데이터에 추가
        if ~isempty(current_coefficients)
            all_geometry_data = [all_geometry_data; current_geometry_expanded];
            all_target_data = [all_target_data; current_coefficients];
            geometry_labels = [geometry_labels; current_targets];
            
            valid_file_count = valid_file_count + 1;
            fprintf('  성공: %d개 변수, %d개 RBF 계수 세트 추출\n', ...
                length(current_targets), size(current_coefficients, 1));
        else
            fprintf('  실패: 유효한 RBF 모델을 생성할 수 없습니다.\n');
        end
        
    catch ME
        fprintf('  파일 처리 오류: %s\n', ME.message);
        continue;
    end
end

fprintf('\n=== 다중 파일 처리 결과 ===\n');
fprintf('처리된 파일 수: %d/%d\n', valid_file_count, length(motFileList));
fprintf('총 geometry-variable 조합: %d개\n', size(all_geometry_data, 1));
fprintf('Geometry 특성 차원: %d개\n', size(all_geometry_data, 2));
fprintf('RBF 계수 차원: %d개\n', size(all_target_data, 2));

if size(all_geometry_data, 1) < 10
    fprintf('경고: DNN 학습을 위한 데이터가 부족합니다 (최소 10개 필요)\n');
end

% 결과를 이전 변수명과 호환되도록 설정
if ~isempty(all_geometry_data)
    % 첫 번째 파일의 데이터를 기존 변수에 할당 (호환성을 위해)
    filteredTable = getMCADLabDataFromMotFile(motFileList{1});
    originLabLinkTable = reNameLabTable2LabLink(filteredTable);
    IdqTable = filterTablewithString(filteredTable,'Peak');
    originLabLinkTable = mergeTables(originLabLinkTable, IdqTable);
    MCADLinkTable = originLabLinkTable;
    
    fprintf('\n첫 번째 파일 기준 MCAD Link 테이블 변수명:\n');
    disp(MCADLinkTable.Properties.VariableNames);
    
    % 다중 파일 데이터를 새로운 변수에 저장
    multi_file_geometry_data = all_geometry_data;
    multi_file_target_data = all_target_data;
    multi_file_labels = geometry_labels;
    
    fprintf('\n다중 파일 데이터가 다음 변수에 저장되었습니다:\n');
    fprintf('  - multi_file_geometry_data: geometry 특성 + current_norm + variable_id\n');
    fprintf('  - multi_file_target_data: RBF 계수들\n');
    fprintf('  - multi_file_labels: target 변수명들\n');
else
    error('모든 파일 처리가 실패했습니다. 파일 경로와 형식을 확인하세요.');
end

%% 4. 기존 bilinear 보간 결과 (선택사항)
% FitResultStr = plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable, 'bilinear');
% fprintf('Bilinear 보간 완료\n');

%% 5. RBF 모델링 준비
% Id, Iq 데이터 추출
idVarIdx = contains(MCADLinkTable.Properties.VariableNames,'Id','IgnoreCase',true);
iqVarIdx = contains(MCADLinkTable.Properties.VariableNames,'Iq','IgnoreCase',true);

if any(idVarIdx)
    idVarName = MCADLinkTable.Properties.VariableNames{idVarIdx};
    id_data = MCADLinkTable.(idVarName);
    fprintf('Id 변수 발견: %s\n', idVarName);
else
    error('Id 변수를 찾을 수 없습니다.');
end

if any(iqVarIdx)
    iqVarName = MCADLinkTable.Properties.VariableNames{iqVarIdx};
    iq_data = MCADLinkTable.(iqVarName);
    fprintf('Iq 변수 발견: %s\n', iqVarName);
else
    error('Iq 변수를 찾을 수 없습니다.');
end

fprintf('Id 범위: [%.2f, %.2f] A\n', min(id_data), max(id_data));
fprintf('Iq 범위: [%.2f, %.2f] A\n', min(iq_data), max(iq_data));
fprintf('데이터 포인트 수: %d\n', length(id_data));

%% 6. 모든 손실 및 물리량 변수에 대한 RBF 모델링
% 모델링할 변수들 필터링 (Id, Iq 제외)
MCADLinkTable_filtered = MCADLinkTable;

% Id, Iq 변수 제거
excludeVars = {'Id', 'Iq'};
for i = 1:length(excludeVars)
    varIdx = contains(MCADLinkTable_filtered.Properties.VariableNames, excludeVars{i}, 'IgnoreCase', true);
    if any(varIdx)
        varsToRemove = MCADLinkTable_filtered.Properties.VariableNames(varIdx);
        MCADLinkTable_filtered = removevars(MCADLinkTable_filtered, varsToRemove);
    end
end

% 데이터 유효성 검증 및 NaN 값 처리
valid_idx = true(length(id_data), 1);
valid_idx = valid_idx & ~isnan(id_data) & ~isnan(iq_data);

% 각 타겟 변수의 NaN 값도 확인
for i = 1:width(MCADLinkTable_filtered)
    var_data = MCADLinkTable_filtered{:, i};
    if isnumeric(var_data)
        valid_idx = valid_idx & ~isnan(var_data);
    end
end

if sum(~valid_idx) > 0
    fprintf('경고: %d개의 NaN 값이 발견되어 제거됩니다.\n', sum(~valid_idx));
    id_data = id_data(valid_idx);
    iq_data = iq_data(valid_idx);
    MCADLinkTable_filtered = MCADLinkTable_filtered(valid_idx, :);
    fprintf('유효한 데이터 포인트 수: %d\n', length(id_data));
end

% 모델링할 변수들
target_vars = MCADLinkTable_filtered.Properties.VariableNames(3:end);
fprintf('\n모델링할 변수들 (%d개):\n', length(target_vars));
for i = 1:length(target_vars)
    fprintf('  %d. %s\n', i, target_vars{i});
end

% 각 변수에 대해 RBF 모델링 수행
rbf_models = struct();
performance_results = table();

fprintf('\n=== RBF 모델링 시작 ===\n');
for i = 1:length(target_vars)
    var_name = target_vars{i};
    target_data = MCADLinkTable_filtered.(var_name);
    
    fprintf('\n[%d/%d] %s 모델링 중...\n', i, length(target_vars), var_name);
    
    % 개별 변수의 유효성 검사
    if ~isnumeric(target_data)
        fprintf('  건너뛰기: 수치형 데이터가 아닙니다.\n');
        continue;
    end
    
    % 현재 변수에 대한 유효한 데이터 인덱스
    var_valid_idx = ~isnan(target_data) & ~isnan(id_data) & ~isnan(iq_data);
    
    if sum(var_valid_idx) < 10  % 최소 10개 데이터 포인트 필요
        fprintf('  건너뛰기: 유효한 데이터 포인트가 너무 적습니다 (%d개).\n', sum(var_valid_idx));
        continue;
    end
    
    % 현재 변수에 대한 데이터 준비
    current_id = id_data(var_valid_idx);
    current_iq = iq_data(var_valid_idx);
    current_target = target_data(var_valid_idx);
    
    % 데이터 범위 확인 (너무 작은 변동은 모델링이 어려움)
    if std(current_target) < 1e-10
        fprintf('  건너뛰기: 목표 변수의 변동이 너무 작습니다 (std=%.2e).\n', std(current_target));
        continue;
    end
    
    % 중복 좌표 확인
    unique_coords = unique([current_id, current_iq], 'rows');
    if size(unique_coords, 1) < length(current_id) * 0.8
        fprintf('  경고: 중복된 좌표가 많습니다 (%d개 중 %d개 고유).\n', ...
            length(current_id), size(unique_coords, 1));
    end
    
    try
        % RBF 모델 훈련
        [rbfFunc, weights, coeffs, centers] = trainRBFThinplate(current_id, current_iq, current_target);
        
        % 모델 성능 평가 (NaN 체크 포함)
        predicted_data = rbfFunc(current_id, current_iq);
        
        % NaN 예측값 확인
        if any(isnan(predicted_data))
            fprintf('  경고: 예측값에 %d개의 NaN이 생성되었습니다.\n', sum(isnan(predicted_data)));
            % NaN이 아닌 값들만으로 성능 계산
            valid_pred_idx = ~isnan(predicted_data);
            if sum(valid_pred_idx) < 5
                fprintf('  건너뛰기: 유효한 예측값이 너무 적습니다.\n');
                continue;
            end
            current_target = current_target(valid_pred_idx);
            predicted_data = predicted_data(valid_pred_idx);
        end
        rmse = sqrt(mean((current_target - predicted_data).^2));
        mae = mean(abs(current_target - predicted_data));
        max_error = max(abs(current_target - predicted_data));
        r2 = 1 - sum((current_target - predicted_data).^2) / sum((current_target - mean(current_target)).^2);
        relative_rmse = rmse / mean(abs(current_target)) * 100;
        
        % 결과 저장
        rbf_models.(matlab.lang.makeValidName(var_name)).func = rbfFunc;
        rbf_models.(matlab.lang.makeValidName(var_name)).weights = weights;
        rbf_models.(matlab.lang.makeValidName(var_name)).coeffs = coeffs;
        rbf_models.(matlab.lang.makeValidName(var_name)).centers = centers;
        rbf_models.(matlab.lang.makeValidName(var_name)).original_name = var_name;
        rbf_models.(matlab.lang.makeValidName(var_name)).valid_points = sum(var_valid_idx);
        
        % 성능 결과 테이블에 추가
        new_row = table({var_name}, rmse, mae, max_error, r2, relative_rmse, ...
            min(current_target), max(current_target), mean(current_target), sum(var_valid_idx), ...
            'VariableNames', {'Variable', 'RMSE', 'MAE', 'MaxError', 'R2', 'RelativeRMSE_Percent', 'Min', 'Max', 'Mean', 'ValidPoints'});
        performance_results = [performance_results; new_row];
        
        fprintf('  RMSE: %.4f (%.2f%%), R²: %.4f (데이터: %d개)\n', rmse, relative_rmse, r2, sum(var_valid_idx));
        
    catch ME
        fprintf('  오류 발생: %s\n', ME.message);
        
        % 상세한 디버깅 정보
        if contains(ME.message, 'NaN') || contains(ME.message, 'Inf')
            fprintf('  디버깅 정보:\n');
            fprintf('    - Id 범위: [%.4f, %.4f]\n', min(current_id), max(current_id));
            fprintf('    - Iq 범위: [%.4f, %.4f]\n', min(current_iq), max(current_iq));
            fprintf('    - 타겟 범위: [%.4f, %.4f]\n', min(current_target), max(current_target));
            fprintf('    - 타겟 표준편차: %.4e\n', std(current_target));
            fprintf('    - 데이터 포인트 수: %d\n', length(current_target));
        end
        continue;
    end
end

% 성능 결과 정렬 (R² 기준 내림차순)
performance_results = sortrows(performance_results, 'R2', 'descend');

fprintf('\n=== 모델 성능 요약 (R² 기준 정렬) ===\n');
fprintf('%-25s %8s %8s %8s %10s %8s\n', '변수명', 'RMSE', 'R²', '상대RMSE%', '최대오차', '데이터수');
fprintf('%s\n', repmat('-', 1, 80));
for i = 1:height(performance_results)
    fprintf('%-25s %8.4f %8.4f %8.2f%% %10.4f %8d\n', ...
        performance_results.Variable{i}, ...
        performance_results.RMSE(i), ...
        performance_results.R2(i), ...
        performance_results.RelativeRMSE_Percent(i), ...
        performance_results.MaxError(i), ...
        performance_results.ValidPoints(i));
end

%% 7. 특정 변수 선택 및 상세 분석
% 성능이 좋은 변수들 선택하여 상세 분석
good_models_idx = performance_results.R2 > 0.95;  % R² > 0.95인 모델들
good_models = performance_results(good_models_idx, :);

if height(good_models) > 0
    fprintf('\n=== 고성능 모델들 (R² > 0.95) ===\n');
    disp(good_models);
    
    % 가장 성능이 좋은 모델 선택
    best_var = good_models.Variable{1};
    best_model_name = matlab.lang.makeValidName(best_var);
    
    fprintf('\n가장 성능이 좋은 변수: %s (R² = %.4f)\n', best_var, good_models.R2(1));
    
    % 예측 함수
    best_rbf_func = rbf_models.(best_model_name).func;
    
    % 새로운 조건에서 예측 예시
    test_id = [-100, -50, 0, 50, 100];
    test_iq = [50, 100, 150, 200];
    [Test_Id, Test_Iq] = meshgrid(test_id, test_iq);
    
    predicted_values = best_rbf_func(Test_Id, Test_Iq);
    
    fprintf('\n%s의 새로운 조건에서 예측:\n', best_var);
    fprintf('Id(A)\tIq(A)\t예측값\n');
    for i = 1:numel(Test_Id)
        fprintf('%.0f\t%.0f\t%.4f\n', Test_Id(i), Test_Iq(i), predicted_values(i));
    end
else
    fprintf('\nR² > 0.95인 모델이 없습니다. 모든 모델 결과를 확인하세요.\n');
end

%% 8. 시각화 및 결과 분석
% 손실 관련 변수들 시각화
loss_related_vars = {};
flux_related_vars = {};

for i = 1:length(target_vars)
    var_name = target_vars{i};
    if contains(var_name, 'Loss', 'IgnoreCase', true)
        loss_related_vars{end+1} = var_name;
    elseif contains(var_name, 'Flux', 'IgnoreCase', true)
        flux_related_vars{end+1} = var_name;
    end
end

fprintf('\n=== 변수 분류 ===\n');
fprintf('손실 관련 변수들 (%d개):\n', length(loss_related_vars));
for i = 1:length(loss_related_vars)
    fprintf('  %s\n', loss_related_vars{i});
end

fprintf('\n자속 관련 변수들 (%d개):\n', length(flux_related_vars));
for i = 1:length(flux_related_vars)
    fprintf('  %s\n', flux_related_vars{i});
end


% 대표적인 손실 변수들 시각화
if ~isempty(loss_related_vars)
    for i = 1:length(loss_related_vars)
        figure(i + 100); % 고유한 figure 번호
        selected_loss_var = loss_related_vars{i};
        loss_model_name = matlab.lang.makeValidName(selected_loss_var);
        
        if isfield(rbf_models, loss_model_name)
            fprintf('\n%s 모델 시각화 중...\n', selected_loss_var);
            
            % 시각화용 그리드 생성
            id_range_viz = linspace(min(id_data), max(id_data), 30);
            iq_range_viz = linspace(min(iq_data), max(iq_data), 30);
            [Id_grid, Iq_grid] = meshgrid(id_range_viz, iq_range_viz);
            
            % RBF 모델로 예측
            loss_rbf_func = rbf_models.(loss_model_name).func;
            Loss_pred = loss_rbf_func(Id_grid, Iq_grid);
            
            % 원본 데이터
            if isfield(MCADLinkTable, selected_loss_var)
                original_loss = MCADLinkTable.(selected_loss_var);
            else
                % MCADLinkTable_filtered에서 찾기
                original_loss = MCADLinkTable_filtered.(selected_loss_var);
            end
            
            % 시각화
            figure('Position', [100 + i*50, 100 + i*50, 1200, 400]);
            
            subplot(1,3,1);
            scatter3(id_data, iq_data, original_loss, 30, original_loss, 'filled');
            xlabel('Id (A)'); ylabel('Iq (A)'); zlabel(selected_loss_var);
            title('원본 데이터');
            colorbar; grid on;
            
            subplot(1,3,2);
            surf(Id_grid, Iq_grid, Loss_pred);
            shading interp;
            xlabel('Id (A)'); ylabel('Iq (A)'); zlabel(selected_loss_var);
            title('RBF 모델 예측');
            colorbar;
            
            subplot(1,3,3);
            contourf(Id_grid, Iq_grid, Loss_pred, 20);
            hold on;
            scatter(id_data, iq_data, 20, 'k', 'filled', 'MarkerFaceAlpha', 0.5);
            xlabel('Id (A)'); ylabel('Iq (A)');
            title('RBF 예측 컨투어');
            colorbar;
            
            sgtitle(sprintf('%s RBF 모델링 결과', selected_loss_var));
        end
    end
end


%% 9. 모델 저장 및 사용법 안내
% 모든 RBF 모델들을 파일로 저장
save('rbf_models_all_variables.mat', 'rbf_models', 'performance_results', 'id_data', 'iq_data', 'target_vars');
fprintf('\n모든 RBF 모델이 저장되었습니다: rbf_models_all_variables.mat\n');

fprintf('\n=== 모델 사용법 ===\n');
fprintf('1. 저장된 모델 로드:\n');
fprintf('   load(''rbf_models_all_variables.mat'');\n\n');

fprintf('2. 특정 변수 예측 (예: %s):\n', target_vars{1});
model_name = matlab.lang.makeValidName(target_vars{1});
fprintf('   predict_func = rbf_models.%s.func;\n', model_name);
fprintf('   predicted_value = predict_func(new_id, new_iq);\n\n');

fprintf('3. 성능 확인:\n');
fprintf('   disp(performance_results);\n\n');

fprintf('4. 모든 변수 예측 함수:\n');
fprintf('   function results = predictAllVariables(new_id, new_iq)\n');
fprintf('       results = struct();\n');
for i = 1:length(target_vars)
    model_name = matlab.lang.makeValidName(target_vars{i});
    fprintf('       results.%s = rbf_models.%s.func(new_id, new_iq);\n', model_name, model_name);
end
fprintf('   end\n');

%% 10. 실제 다중 파일 데이터를 이용한 DNN 학습
% 섹션 3에서 추출한 실제 다중 geometry 데이터를 사용하여 DNN 학습

fprintf('\n=== 실제 다중 파일 데이터로 DNN 학습 ===\n');

% 다중 파일 데이터 확인
if ~exist('multi_file_geometry_data', 'var') || isempty(multi_file_geometry_data)
    fprintf('다중 파일 데이터가 없습니다. 섹션 3을 먼저 실행하세요.\n');
else
    fprintf('사용 가능한 데이터:\n');
    fprintf('  - Geometry-Target 조합: %d개\n', size(multi_file_geometry_data, 1));
    fprintf('  - Geometry 특성 차원: %d개 (slots, poles, air_gap, stack_length, magnet_thickness, current_norm, variable_id)\n', size(multi_file_geometry_data, 2));
    fprintf('  - RBF 계수 차원: %d개\n', size(multi_file_target_data, 2));
    fprintf('  - 고유한 변수 개수: %d개\n', length(unique(multi_file_labels)));
    
    % 고유한 변수명들 표시
    unique_vars = unique(multi_file_labels);
    fprintf('\n처리된 변수들:\n');
    for i = 1:length(unique_vars)
        var_count = sum(strcmp(multi_file_labels, unique_vars{i}));
        fprintf('  %s: %d개 geometry에서 추출\n', unique_vars{i}, var_count);
    end
    
    % DNN 학습용 데이터 준비
    % geometry 특성만 추출 (variable_id 제외)
    geometry_features = multi_file_geometry_data(:, 1:6); % slots, poles, air_gap, stack_length, magnet_thickness, current_norm
    rbf_coefficients = multi_file_target_data;
    
    % 데이터 품질 확인
    fprintf('\nDNN 학습용 데이터 품질 확인:\n');
    fprintf('  - Geometry 특성 범위:\n');
    fprintf('    Stator slots: [%.0f, %.0f]\n', min(geometry_features(:,1)), max(geometry_features(:,1)));
    fprintf('    Rotor poles: [%.0f, %.0f]\n', min(geometry_features(:,2)), max(geometry_features(:,2)));
    fprintf('    Air gap: [%.2f, %.2f] mm\n', min(geometry_features(:,3)), max(geometry_features(:,3)));
    fprintf('    Stack length: [%.1f, %.1f] mm\n', min(geometry_features(:,4)), max(geometry_features(:,4)));
    fprintf('    Magnet thickness: [%.2f, %.2f] mm\n', min(geometry_features(:,5)), max(geometry_features(:,5)));
    fprintf('    Current norm: [%.1f, %.1f] A\n', min(geometry_features(:,6)), max(geometry_features(:,6)));
    
    % NaN 확인
    nan_geometry = any(isnan(geometry_features), 2);
    nan_coeffs = any(isnan(rbf_coefficients), 2);
    valid_data_idx = ~nan_geometry & ~nan_coeffs;
    
    if sum(~valid_data_idx) > 0
        fprintf('  - 제거된 NaN 데이터: %d개\n', sum(~valid_data_idx));
        geometry_features = geometry_features(valid_data_idx, :);
        rbf_coefficients = rbf_coefficients(valid_data_idx, :);
        multi_file_labels = multi_file_labels(valid_data_idx);
    end
    
    fprintf('  - 최종 유효 데이터: %d개\n', size(geometry_features, 1));
    
    % DNN 학습 수행
    if size(geometry_features, 1) >= 10
        fprintf('\nDNN 학습을 시작합니다...\n');
        
        % 전체 데이터에 대한 DNN 학습 (모든 변수 통합)
        dnn_options = struct();
        dnn_options.hidden_layers = [64, 32, 16]; % 더 큰 네트워크
        dnn_options.max_epochs = 300;
        dnn_options.learning_rate = 0.001;
        dnn_options.train_ratio = 0.7;
        dnn_options.val_ratio = 0.2;
        dnn_options.use_rbf_basis = false;
        dnn_options.verbose = true;
        
        try
            % 현재 형태: geometry_features는 이미 분리되어 있고, 
            % currentNorm은 geometry_features의 6번째 열에 포함됨
            geometry_only = geometry_features(:, 1:5); % geometry만
            current_norms = geometry_features(:, 6);   % current norm
            
            [dnn_model, train_info] = trainRBF_DNN(geometry_only, current_norms, rbf_coefficients, dnn_options);
            
            fprintf('DNN 학습 완료!\n');
            fprintf('최종 훈련 MSE: %.6f\n', train_info.train_mse);
            fprintf('최종 검증 MSE: %.6f\n', train_info.val_mse);
            fprintf('최종 검증 R²: %.4f\n', train_info.val_r2);
            
            % 모델 저장 (추가 정보 포함)
            save('dnn_rbf_model_multifile.mat', 'dnn_model', 'train_info', 'dnn_options', ...
                 'geometry_features', 'rbf_coefficients', 'multi_file_labels', 'unique_vars');
            fprintf('DNN 모델이 저장되었습니다: dnn_rbf_model_multifile.mat\n');
            
            dnn_success = true;
            
            % 학습 결과 시각화
            if isfield(train_info, 'train_mse_history') && length(train_info.train_mse_history) > 1
                figure('Name', '다중 파일 DNN 학습 결과', 'Position', [100, 100, 1000, 400]);
                
                subplot(1,2,1);
                epochs = 1:length(train_info.train_mse_history);
                semilogy(epochs, train_info.train_mse_history, 'b-', 'LineWidth', 2);
                hold on;
                if isfield(train_info, 'val_mse_history')
                    semilogy(epochs, train_info.val_mse_history, 'r--', 'LineWidth', 2);
                    legend('Train MSE', 'Val MSE', 'Location', 'best');
                end
                xlabel('Epoch'); ylabel('MSE (log scale)'); 
                title('DNN 학습 곡선'); grid on;
                
                subplot(1,2,2);
                % Geometry 특성 분포 시각화
                scatter3(geometry_features(:,1), geometry_features(:,2), geometry_features(:,3), ...
                    30, geometry_features(:,6), 'filled', 'Alpha', 0.6);
                xlabel('Stator Slots'); ylabel('Rotor Poles'); zlabel('Air Gap (mm)');
                title('Geometry 특성 분포 (색상: Current Norm)');
                colorbar; grid on;
            end
            
        catch ME
            fprintf('DNN 학습 실패: %s\n', ME.message);
            dnn_success = false;
        end
    else
        fprintf('DNN 학습을 위한 데이터가 부족합니다 (현재 %d개, 최소 10개 필요)\n', size(geometry_features, 1));
        dnn_success = false;
    end
end

%% 11. 특정 변수별 DNN 모델링 (선택사항)
% 각 변수별로 별도의 DNN 모델을 만들어 더 정확한 예측

if exist('dnn_success', 'var') && dnn_success
    fprintf('\n=== 변수별 개별 DNN 모델링 ===\n');
    
    % 충분한 데이터가 있는 변수들만 선택
    variable_counts = containers.Map();
    for i = 1:length(multi_file_labels)
        var_name = multi_file_labels{i};
        if variable_counts.isKey(var_name)
            variable_counts(var_name) = variable_counts(var_name) + 1;
        else
            variable_counts(var_name) = 1;
        end
    end
    
    % 최소 5개 이상의 geometry를 가진 변수들
    min_geometries = 5;
    selected_variables = {};
    var_names = keys(variable_counts);
    for i = 1:length(var_names)
        if variable_counts(var_names{i}) >= min_geometries
            selected_variables{end+1} = var_names{i};
        end
    end
    
    fprintf('개별 모델링할 변수들 (%d개):\n', length(selected_variables));
    for i = 1:length(selected_variables)
        var_count = variable_counts(selected_variables{i});
        fprintf('  %s: %d개 geometry\n', selected_variables{i}, var_count);
    end
    
    % 각 변수별로 DNN 모델 학습
    variable_models = struct();
    
    for var_idx = 1:min(3, length(selected_variables)) % 최대 3개 변수만 (시간 절약)
        var_name = selected_variables{var_idx};
        var_indices = strcmp(multi_file_labels, var_name);
        
        if sum(var_indices) >= min_geometries
            fprintf('\n[%d/%d] %s 개별 모델 학습 중...\n', var_idx, length(selected_variables), var_name);
            
            var_geometry = geometry_features(var_indices, 1:5);
            var_currents = geometry_features(var_indices, 6);
            var_coeffs = rbf_coefficients(var_indices, :);
            
            % 개별 DNN 옵션 (더 작은 네트워크)
            var_dnn_options = struct();
            var_dnn_options.hidden_layers = [32, 16];
            var_dnn_options.max_epochs = 200;
            var_dnn_options.learning_rate = 0.001;
            var_dnn_options.train_ratio = 0.8;
            var_dnn_options.val_ratio = 0.2;
            var_dnn_options.use_rbf_basis = false;
            var_dnn_options.verbose = false;
            
            try
                [var_model, var_train_info] = trainRBF_DNN(var_geometry, var_currents, var_coeffs, var_dnn_options);
                
                variable_models.(matlab.lang.makeValidName(var_name)).model = var_model;
                variable_models.(matlab.lang.makeValidName(var_name)).train_info = var_train_info;
                variable_models.(matlab.lang.makeValidName(var_name)).original_name = var_name;
                variable_models.(matlab.lang.makeValidName(var_name)).data_count = sum(var_indices);
                
                fprintf('  성공: 검증 R² = %.4f (데이터 %d개)\n', var_train_info.val_r2, sum(var_indices));
                
            catch ME
                fprintf('  실패: %s\n', ME.message);
            end
        end
    end
    
    % 개별 모델 성능 요약
    model_names = fieldnames(variable_models);
    if ~isempty(model_names)
        fprintf('\n=== 개별 모델 성능 요약 ===\n');
        fprintf('%-20s %10s %10s %8s\n', '변수명', '검증 R²', '검증 MSE', '데이터수');
        fprintf('%s\n', repmat('-', 1, 50));
        
        for i = 1:length(model_names)
            model_info = variable_models.(model_names{i});
            fprintf('%-20s %10.4f %10.6f %8d\n', ...
                model_info.original_name, ...
                model_info.train_info.val_r2, ...
                model_info.train_info.val_mse, ...
                model_info.data_count);
        end
        
        % 개별 모델들도 저장
        save('variable_specific_dnn_models.mat', 'variable_models', 'selected_variables');
        fprintf('\n개별 변수 모델들이 저장되었습니다: variable_specific_dnn_models.mat\n');
    end
end

%% 12. 새로운 geometry에 대한 실제 예측 및 검증
if exist('dnn_success', 'var') && dnn_success
    fprintf('\n=== 새로운 geometry에 대한 예측 및 검증 ===\n');
    
    % 실제 데이터에서 geometry 범위 확인
    geo_ranges = [min(geometry_features(:,1:5)); max(geometry_features(:,1:5))];
    
    fprintf('기존 geometry 범위:\n');
    fprintf('  Stator slots: [%.0f, %.0f]\n', geo_ranges(1,1), geo_ranges(2,1));
    fprintf('  Rotor poles: [%.0f, %.0f]\n', geo_ranges(1,2), geo_ranges(2,2));
    fprintf('  Air gap: [%.2f, %.2f] mm\n', geo_ranges(1,3), geo_ranges(2,3));
    fprintf('  Stack length: [%.1f, %.1f] mm\n', geo_ranges(1,4), geo_ranges(2,4));
    fprintf('  Magnet thickness: [%.2f, %.2f] mm\n', geo_ranges(1,5), geo_ranges(2,5));
    
    % 새로운 geometry 정의 (기존 범위 내에서)
    new_geometry = struct();
    new_geometry.stator_slot_num = round(mean(geo_ranges(:,1))); % 중간값
    new_geometry.rotor_pole_num = round(mean(geo_ranges(:,2)));
    new_geometry.air_gap = mean(geo_ranges(:,3));
    new_geometry.stack_length = mean(geo_ranges(:,4));
    new_geometry.magnet_thickness = mean(geo_ranges(:,5));
    new_current_norm = mean(geometry_features(:,6));
    
    fprintf('\n새로운 geometry 조건 (기존 데이터 중간값):\n');
    fprintf('  - Stator slots: %d\n', new_geometry.stator_slot_num);
    fprintf('  - Rotor poles: %d\n', new_geometry.rotor_pole_num);
    fprintf('  - Air gap: %.2f mm\n', new_geometry.air_gap);
    fprintf('  - Stack length: %.1f mm\n', new_geometry.stack_length);
    fprintf('  - Magnet thickness: %.2f mm\n', new_geometry.magnet_thickness);
    fprintf('  - Current norm: %.1f A\n', new_current_norm);
    
    % generateLossMapFromGeometry 함수 사용
    try
        % 첫 번째 파일의 Id, Iq 범위 사용
        id_range = [min(id_data), max(id_data)];
        iq_range = [min(iq_data), max(iq_data)];
        
        fprintf('\n손실 맵을 생성합니다...\n');
        [loss_map, ID_pred, IQ_pred] = generateLossMapFromGeometry(...
            dnn_model, new_geometry, new_current_norm, ...
            id_range, iq_range, ...
            'GridSize', [20, 20], ...
            'Verbose', true);
        
        fprintf('손실 맵 생성 완료!\n');
        fprintf('예측된 손실 범위: [%.2e, %.2e]\n', min(loss_map(:)), max(loss_map(:)));
        
        % 기존 데이터와 비교를 위한 시각화
        figure('Name', '실제 데이터 기반 DNN 예측 결과', 'Position', [100, 100, 1400, 600]);
        
        % 예측된 손실 맵 (3D)
        subplot(2,4,1);
        surf(ID_pred, IQ_pred, loss_map);
        title('DNN 예측 손실 맵 (3D)');
        xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('손실');
        
        % 예측된 손실 맵 (Contour)
        subplot(2,4,2);
        contourf(ID_pred, IQ_pred, loss_map, 20);
        title('DNN 예측 손실 맵 (Contour)');
        xlabel('Id (A)'); ylabel('Iq (A)');
        colorbar;
        
        % 원본 데이터 분포 (첫 번째 파일)
        if exist('MCADLinkTable', 'var') && ~isempty(target_vars)
            % 첫 번째 손실 변수 선택
            loss_vars = {};
            for i = 1:length(target_vars)
                if contains(lower(target_vars{i}), 'loss')
                    loss_vars{end+1} = target_vars{i};
                end
            end
            
            if ~isempty(loss_vars)
                first_loss_var = loss_vars{1};
                original_loss = MCADLinkTable.(first_loss_var);
                valid_original = ~isnan(original_loss);
                
                subplot(2,4,3);
                scatter(id_data(valid_original), iq_data(valid_original), 30, original_loss(valid_original), 'filled');
                title(sprintf('원본 데이터: %s', first_loss_var));
                xlabel('Id (A)'); ylabel('Iq (A)');
                colorbar;
            end
        end
        
        % DNN 계수 분포
        subplot(2,4,4);
        new_geo_vector = [new_geometry.stator_slot_num, new_geometry.rotor_pole_num, ...
                         new_geometry.air_gap, new_geometry.stack_length, new_geometry.magnet_thickness];
        predicted_coeffs = predict(dnn_model, [new_geo_vector, new_current_norm]);
        plot(predicted_coeffs, 'o-', 'MarkerSize', 4);
        title('DNN 예측 RBF 계수');
        xlabel('계수 인덱스'); ylabel('계수 값');
        grid on;
        
        % Geometry 특성 비교
        subplot(2,4,5);
        geo_comparison = [mean(geometry_features(:,1:5)); 
                         [new_geometry.stator_slot_num, new_geometry.rotor_pole_num, ...
                          new_geometry.air_gap, new_geometry.stack_length, new_geometry.magnet_thickness]];
        bar(geo_comparison');
        title('Geometry 특성 비교');
        xlabel('특성 (Slots, Poles, Gap, Length, Magnet)');
        ylabel('값');
        legend('기존 평균', '새로운 geometry', 'Location', 'best');
        
        % 예측 불확실성 분석 (여러 geometry 조건에서)
        subplot(2,4,6);
        n_test_geo = 5;
        test_losses = zeros(n_test_geo, 1);
        test_geo_labels = cell(n_test_geo, 1);
        
        for i = 1:n_test_geo
            % 랜덤한 geometry 생성
            test_geo_i = geo_ranges(1,:) + rand(1,5) .* (geo_ranges(2,:) - geo_ranges(1,:));
            test_geo_struct = struct();
            test_geo_struct.stator_slot_num = round(test_geo_i(1));
            test_geo_struct.rotor_pole_num = round(test_geo_i(2));
            test_geo_struct.air_gap = test_geo_i(3);
            test_geo_struct.stack_length = test_geo_i(4);
            test_geo_struct.magnet_thickness = test_geo_i(5);
            
            [test_loss_map, ~, ~] = generateLossMapFromGeometry(...
                dnn_model, test_geo_struct, new_current_norm, ...
                id_range, iq_range, 'GridSize', [10, 10], 'Verbose', false);
            
            test_losses(i) = mean(test_loss_map(:), 'omitnan');
            test_geo_labels{i} = sprintf('Geo%d', i);
        end
        
        bar(test_losses);
        title('다양한 Geometry의 평균 손실');
        xlabel('테스트 Geometry');
        ylabel('평균 손실');
        set(gca, 'XTickLabel', test_geo_labels);
        
        % 실제 vs 예측 비교 (훈련 데이터에서)
        subplot(2,4,7);
        if size(geometry_features, 1) > 0
            % 몇 개 샘플에 대해 실제 계수 vs 예측 계수 비교
            n_samples = min(10, size(geometry_features, 1));
            sample_indices = randperm(size(geometry_features, 1), n_samples);
            
            pred_coeffs_samples = zeros(n_samples, size(rbf_coefficients, 2));
            for i = 1:n_samples
                idx = sample_indices(i);
                geo_input = geometry_features(idx, 1:6);
                pred_coeffs_samples(i, :) = predict(dnn_model, geo_input);
            end
            
            actual_coeffs_samples = rbf_coefficients(sample_indices, :);
            
            % 첫 10개 계수만 비교
            n_coeffs_show = min(10, size(rbf_coefficients, 2));
            scatter(actual_coeffs_samples(:, 1:n_coeffs_show), pred_coeffs_samples(:, 1:n_coeffs_show), 'filled');
            xlabel('실제 RBF 계수'); ylabel('예측 RBF 계수');
            title('실제 vs 예측 계수');
            
            % 이상적인 선 추가
            hold on;
            coeff_range = [min([actual_coeffs_samples(:); pred_coeffs_samples(:)]), ...
                          max([actual_coeffs_samples(:); pred_coeffs_samples(:)])];
            plot(coeff_range, coeff_range, 'r--', 'LineWidth', 2);
            grid on;
        end
        
        % 모델 성능 요약
        subplot(2,4,8);
        text(0.1, 0.8, sprintf('DNN 모델 성능:'), 'FontSize', 12, 'FontWeight', 'bold');
        text(0.1, 0.7, sprintf('검증 R²: %.4f', train_info.val_r2), 'FontSize', 10);
        text(0.1, 0.6, sprintf('검증 MSE: %.6f', train_info.val_mse), 'FontSize', 10);
        text(0.1, 0.5, sprintf('훈련 데이터: %d개', size(geometry_features, 1)), 'FontSize', 10);
        text(0.1, 0.4, sprintf('고유 변수: %d개', length(unique(multi_file_labels))), 'FontSize', 10);
        text(0.1, 0.3, sprintf('처리된 파일: %d개', valid_file_count), 'FontSize', 10);
        
        if exist('variable_models', 'var') && ~isempty(fieldnames(variable_models))
            text(0.1, 0.2, sprintf('개별 모델: %d개', length(fieldnames(variable_models))), 'FontSize', 10);
        end
        
        axis off;
        title('모델 정보');
        
        fprintf('\n새로운 geometry에 대한 예측이 완료되었습니다.\n');
        
    catch ME
        fprintf('새로운 geometry 예측 중 오류 발생: %s\n', ME.message);
    end
else
    fprintf('\nDNN 모델이 없습니다. 섹션 10을 먼저 실행하세요.\n');
end

%% 13. 종합 사용법 안내
fprintf('\n=== 전체 워크플로우 사용법 ===\n');
fprintf('1. 기본 RBF 모델링:\n');
fprintf('   - 섹션 1-9: 데이터 로드, 전처리, RBF 모델 생성, 성능 평가, 시각화\n\n');

fprintf('2. DNN을 이용한 RBF 계수 학습:\n');
fprintf('   - 섹션 10-11: 여러 geometry에 대해 RBF 계수 추출, DNN 학습\n\n');

fprintf('3. 새로운 조건 예측:\n');
fprintf('   - 섹션 12: DNN으로 새로운 geometry의 RBF 계수 예측, 손실 맵 생성\n\n');

fprintf('4. 저장된 모델 활용:\n');
fprintf('   load(''rbf_models_all_variables.mat'');     %% 기본 RBF 모델들\n');
fprintf('   load(''dnn_rbf_model.mat'');                %% DNN 모델\n\n');

fprintf('5. 실제 활용 시나리오:\n');
fprintf('   - FEA 데이터베이스에서 geometry별 손실 데이터 추출\n');
fprintf('   - RBF 모델로 각 geometry의 손실 맵 학습\n');
fprintf('   - DNN으로 geometry → RBF계수 관계 학습\n');
fprintf('   - 새로운 설계에 대해 DNN으로 RBF 계수 예측 → 전체 손실 맵 생성\n\n');

fprintf('스크립트 완료! 각 섹션을 개별적으로 실행할 수 있습니다.\n');
fprintf('사용법:\n');
fprintf('  - Ctrl+Enter: 현재 섹션 실행\n');
fprintf('  - F9: 선택한 줄만 실행\n');
fprintf('  - F5: 전체 스크립트 실행\n');

%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline"}
%---
