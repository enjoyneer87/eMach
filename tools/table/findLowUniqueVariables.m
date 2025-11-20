function lowUniqueVars = findLowUniqueVariables(T_in, maxUnique)
% 테이블에서 unique한 값이 maxUnique 이하인 변수 이름을 반환
%
% 입력:
%   T_in       - MATLAB 테이블
%   maxUnique  - 허용 가능한 unique 값의 최대 개수 (기본값: 3)
%
% 출력:
%   lowUniqueVars - unique 값 개수가 maxUnique 이하인 변수들의 이름(cell array)

    if nargin < 2
        maxUnique = 3;
    end

    lowUniqueVars = {};
    varNames = T_in.Properties.VariableNames;

    for i = 1:numel(varNames)
        colData = T_in.(varNames{i});
        try
            uniqueVals = unique(colData);
        catch
            % 일부 구조체형 변수는 unique()가 안됨
            continue;
        end

        if numel(uniqueVals) <= maxUnique
            lowUniqueVars{end+1} = varNames{i}; %#ok<AGROW>
        end
    end
end

