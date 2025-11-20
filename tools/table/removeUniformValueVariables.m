function T_out = removeUniformValueVariables(T_in, tol)
% 동일한 값을 갖는 변수 제거 (숫자는 tolerance 허용)
% 입력: T_in - 입력 테이블
%        tol  - 허용 오차 (예: 1e-5)
% 출력: T_out - 동일 값 변수 제거된 테이블

    if nargin < 2
        tol = 1e-5;
    end

    T_out = T_in;
    varNames = T_in.Properties.VariableNames;

    for i = numel(varNames):-1:1
        colData = T_in.(varNames{i});

        % 숫자형인 경우 tolerance로 비교
        if isnumeric(colData) || islogical(colData)
            if all(abs(colData - colData(1)) < tol)
                T_out(:, varNames{i}) = [];
            end

        % datetime, string, categorical 등은 isequaln으로 비교
        else
            if all(arrayfun(@(x) isequaln(x, colData(1)), colData))
                T_out(:, varNames{i}) = [];
            end
        end
    end
end
