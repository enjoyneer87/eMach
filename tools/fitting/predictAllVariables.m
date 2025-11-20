function results = predictAllVariables(new_id, new_iq, model_file)
% predictAllVariables - 모든 RBF 모델을 사용하여 예측
%
% 입력:
%   new_id - 예측할 Id 값 (스칼라 또는 벡터)
%   new_iq - 예측할 Iq 값 (스칼라 또는 벡터)
%   model_file - RBF 모델 파일 경로 (기본값: 'rbf_models_all_variables.mat')
%
% 출력:
%   results - 모든 변수의 예측 결과를 포함하는 구조체
%
% 사용 예시:
%   % 단일 예측
%   pred = predictAllVariables(50, 150);
%   
%   % 여러 점 예측
%   id_vec = [0, 50, 100];
%   iq_vec = [100, 150, 200];
%   pred = predictAllVariables(id_vec, iq_vec);
%   
%   % 그리드 예측
%   [Id_grid, Iq_grid] = meshgrid(-100:50:100, 50:50:250);
%   pred = predictAllVariables(Id_grid, Iq_grid);

    % 기본 모델 파일 설정
    if nargin < 3
        model_file = 'rbf_models_all_variables.mat';
    end
    
    % 모델 파일 존재 확인
    if ~exist(model_file, 'file')
        error('모델 파일을 찾을 수 없습니다: %s', model_file);
    end
    
    % 모델 로드
    loaded_data = load(model_file);
    rbf_models = loaded_data.rbf_models;
    
    % 입력 크기 확인
    if numel(new_id) ~= numel(new_iq)
        error('new_id와 new_iq의 크기가 일치하지 않습니다.');
    end
    
    % 결과 구조체 초기화
    results = struct();
    results.Id = new_id;
    results.Iq = new_iq;
    
    % 각 변수에 대해 예측
    model_names = fieldnames(rbf_models);
    for i = 1:length(model_names)
        model_name = model_names{i};
        
        try
            % 예측 함수 가져오기
            predict_func = rbf_models.(model_name).func;
            original_name = rbf_models.(model_name).original_name;
            
            % 예측 수행 (NaN 값 처리)
            if any(isnan(new_id(:))) || any(isnan(new_iq(:)))
                warning('입력 데이터에 NaN 값이 있습니다. 해당 위치는 NaN으로 반환됩니다.');
                predicted_values = NaN(size(new_id));
            else
                predicted_values = predict_func(new_id, new_iq);
            end
            
            % 결과 저장 (원본 변수명과 정리된 변수명 모두 저장)
            results.(model_name) = predicted_values;
            
            % 원본 이름도 저장 (공백이나 특수문자가 있는 경우)
            if ~strcmp(model_name, original_name)
                results.OriginalNames.(model_name) = original_name;
            end
            
        catch ME
            warning('변수 %s 예측 중 오류 발생: %s', model_name, ME.message);
            results.(model_name) = NaN(size(new_id));
        end
    end
    
    % 예측 완료 메시지
    fprintf('총 %d개 변수에 대한 예측 완료\n', length(model_names));
    
    % 입력이 스칼라인 경우 결과 요약 출력
    if isscalar(new_id)
        fprintf('\nId = %.2f A, Iq = %.2f A에서의 예측 결과:\n', new_id, new_iq);
        fprintf('%-30s %12s\n', '변수명', '예측값');
        fprintf('%s\n', repmat('-', 1, 45));
        
        for i = 1:length(model_names)
            model_name = model_names{i};
            if isfield(results, model_name) && ~isnan(results.(model_name))
                if isfield(results, 'OriginalNames') && isfield(results.OriginalNames, model_name)
                    display_name = results.OriginalNames.(model_name);
                else
                    display_name = model_name;
                end
                fprintf('%-30s %12.4f\n', display_name, results.(model_name));
            end
        end
    end
end
