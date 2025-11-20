function rbfModel = loadRBFModel(modelFile, variableName)
% loadRBFModel - 저장된 RBF 모델에서 특정 변수의 모델을 로드
%
% 입력:
%   modelFile - RBF 모델 파일 경로 (기본값: 'rbf_models_all_variables.mat')
%   variableName - 로드할 변수명 (생략 시 전체 모델 반환)
%
% 출력:
%   rbfModel - RBF 모델 구조체 또는 예측 함수
%
% 사용 예시:
%   % 전체 모델 로드
%   allModels = loadRBFModel();
%   
%   % 특정 변수 모델만 로드
%   fluxModel = loadRBFModel('rbf_models_all_variables.mat', 'Flux Linkage D');
%   prediction = fluxModel(50, 150);  % Id=50A, Iq=150A에서 예측

    % 기본값 설정
    if nargin < 1 || isempty(modelFile)
        modelFile = 'rbf_models_all_variables.mat';
    end
    
    % 파일 존재 확인
    if ~exist(modelFile, 'file')
        error('모델 파일을 찾을 수 없습니다: %s', modelFile);
    end
    
    % 모델 로드
    try
        loaded_data = load(modelFile);
        if ~isfield(loaded_data, 'rbf_models')
            error('파일에 rbf_models 필드가 없습니다.');
        end
        
        rbf_models = loaded_data.rbf_models;
        
    catch ME
        error('모델 파일 로드 중 오류 발생: %s', ME.message);
    end
    
    % 특정 변수 요청 시
    if nargin >= 2 && ~isempty(variableName)
        % 변수명을 MATLAB 유효 이름으로 변환
        validName = matlab.lang.makeValidName(variableName);
        
        % 모델 존재 확인
        if ~isfield(rbf_models, validName)
            % 사용 가능한 변수들 출력
            availableVars = fieldnames(rbf_models);
            fprintf('요청한 변수 "%s"를 찾을 수 없습니다.\n', variableName);
            fprintf('사용 가능한 변수들:\n');
            for i = 1:length(availableVars)
                if isfield(rbf_models.(availableVars{i}), 'original_name')
                    fprintf('  %d. %s (내부명: %s)\n', i, ...
                        rbf_models.(availableVars{i}).original_name, availableVars{i});
                else
                    fprintf('  %d. %s\n', i, availableVars{i});
                end
            end
            error('변수를 찾을 수 없습니다.');
        end
        
        % 예측 함수 반환
        rbfModel = rbf_models.(validName).func;
        
        % 모델 정보 출력
        if isfield(rbf_models.(validName), 'original_name')
            fprintf('로드된 모델: %s\n', rbf_models.(validName).original_name);
        end
        if isfield(rbf_models.(validName), 'valid_points')
            fprintf('훈련 데이터 포인트 수: %d\n', rbf_models.(validName).valid_points);
        end
        
    else
        % 전체 모델 반환
        rbfModel = loaded_data;
        
        % 모델 정보 요약
        modelNames = fieldnames(rbf_models);
        fprintf('로드된 RBF 모델 수: %d\n', length(modelNames));
        fprintf('포함된 변수들:\n');
        for i = 1:length(modelNames)
            if isfield(rbf_models.(modelNames{i}), 'original_name')
                fprintf('  %d. %s\n', i, rbf_models.(modelNames{i}).original_name);
            else
                fprintf('  %d. %s\n', i, modelNames{i});
            end
        end
    end
end
