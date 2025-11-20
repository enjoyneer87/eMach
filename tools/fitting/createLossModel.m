function [rbfModel, performance] = createLossModel(data)
% createLossModel - id, iq, 손실 테이블로부터 RBF 손실 모델 생성
%
% 입력:
%   data - 구조체 또는 테이블, 다음 필드를 포함해야 함:
%          .id 또는 .Id - d축 전류 벡터 (A)
%          .iq 또는 .Iq - q축 전류 벡터 (A) 
%          .loss 또는 .Loss - 손실 벡터 (W)
%
% 출력:
%   rbfModel - 훈련된 RBF 모델 구조체:
%              .predict - 예측 함수 handle @(id, iq)
%              .weights - RBF 가중치
%              .coeffs - 선형 계수
%              .centers - RBF 중심점
%   performance - 모델 성능 구조체:
%                 .rmse - Root Mean Square Error
%                 .max_error - 최대 절대 오차
%                 .mean_error - 평균 절대 오차
%
% 사용 예시:
%   % 테이블에서 데이터 로드
%   data = readtable('motor_loss_data.csv');
%   
%   % 또는 구조체로 데이터 준비
%   data.id = [10, 20, 30, ...]';
%   data.iq = [50, 100, 150, ...]';
%   data.loss = [25.5, 45.2, 78.9, ...]';
%   
%   % 모델 생성
%   [model, perf] = createLossModel(data);
%   
%   % 새로운 조건에서 예측
%   predicted_loss = model.predict(25, 125);

    % 입력 데이터 추출
    if istable(data)
        % 테이블인 경우
        if ismember('id', data.Properties.VariableNames)
            id_data = data.id;
        elseif ismember('Id', data.Properties.VariableNames)
            id_data = data.Id;
        else
            error('테이블에 ''id'' 또는 ''Id'' 열이 없습니다.');
        end
        
        if ismember('iq', data.Properties.VariableNames)
            iq_data = data.iq;
        elseif ismember('Iq', data.Properties.VariableNames)
            iq_data = data.Iq;
        else
            error('테이블에 ''iq'' 또는 ''Iq'' 열이 없습니다.');
        end
        
        if ismember('loss', data.Properties.VariableNames)
            loss_data = data.loss;
        elseif ismember('Loss', data.Properties.VariableNames)
            loss_data = data.Loss;
        else
            error('테이블에 ''loss'' 또는 ''Loss'' 열이 없습니다.');
        end
    else
        % 구조체인 경우
        if isfield(data, 'id')
            id_data = data.id;
        elseif isfield(data, 'Id')
            id_data = data.Id;
        else
            error('구조체에 ''id'' 또는 ''Id'' 필드가 없습니다.');
        end
        
        if isfield(data, 'iq')
            iq_data = data.iq;
        elseif isfield(data, 'Iq')
            iq_data = data.Iq;
        else
            error('구조체에 ''iq'' 또는 ''Iq'' 필드가 없습니다.');
        end
        
        if isfield(data, 'loss')
            loss_data = data.loss;
        elseif isfield(data, 'Loss')
            loss_data = data.Loss;
        else
            error('구조체에 ''loss'' 또는 ''Loss'' 필드가 없습니다.');
        end
    end
    
    % 데이터 검증
    if length(id_data) ~= length(iq_data) || length(id_data) ~= length(loss_data)
        error('id, iq, loss 데이터의 길이가 일치하지 않습니다.');
    end
    
    % NaN 값 제거
    valid_idx = ~(isnan(id_data) | isnan(iq_data) | isnan(loss_data));
    id_data = id_data(valid_idx);
    iq_data = iq_data(valid_idx);
    loss_data = loss_data(valid_idx);
    
    fprintf('데이터 포인트 수: %d\n', length(id_data));
    fprintf('Id 범위: [%.2f, %.2f] A\n', min(id_data), max(id_data));
    fprintf('Iq 범위: [%.2f, %.2f] A\n', min(iq_data), max(iq_data));
    fprintf('Loss 범위: [%.2f, %.2f] W\n', min(loss_data), max(loss_data));
    
    % RBF 모델 훈련
    fprintf('\nRBF 모델 훈련 중...\n');
    [rbfFunc, weights, coeffs, centers] = trainRBFThinplate(id_data, iq_data, loss_data);
    
    % 모델 성능 평가
    predicted_loss = rbfFunc(id_data, iq_data);
    rmse = sqrt(mean((loss_data - predicted_loss).^2));
    max_error = max(abs(loss_data - predicted_loss));
    mean_error = mean(abs(loss_data - predicted_loss));
    
    % 결과 구조체 생성
    rbfModel.predict = rbfFunc;
    rbfModel.weights = weights;
    rbfModel.coeffs = coeffs;
    rbfModel.centers = centers;
    
    performance.rmse = rmse;
    performance.max_error = max_error;
    performance.mean_error = mean_error;
    performance.relative_rmse = rmse / mean(loss_data) * 100;  % 상대 RMSE (%)
    
    fprintf('훈련 완료!\n');
    fprintf('RMSE: %.4f W (%.2f%%)\n', rmse, performance.relative_rmse);
    fprintf('최대 오차: %.4f W\n', max_error);
    fprintf('평균 절대 오차: %.4f W\n', mean_error);
end
