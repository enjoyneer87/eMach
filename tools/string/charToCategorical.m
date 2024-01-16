function resultCategorical = charToCategorical(charVariable)
    % 주어진 char 변수를 categorical 정보로 변환하는 함수

    % 주어진 char 변수를 줄 단위로 분할
    lines = strsplit(charVariable, '\n');

    % 각 줄에서 변수 이름과 값 추출
    variableNames = {};
    variableValues = {};

    for lineIndex = 1:length(lines)
        % 줄을 공백으로 분할하여 변수 이름과 값 추출
        parts{lineIndex,1} = strsplit(lines{lineIndex}, ' ', 'CollapseDelimiters', true);
        a=parts{lineIndex,1}
        resultCell = convertcharCellArray2PropertiesCell(a);


        % % 비어있는 줄은 건너뜁니다
        % if isempty(parts{1})
        %     continue;
        % end

        % 변수 이름 추출
        % variableName = strjoin(parts(1:end-2), ' ');

        % 변수 값 추출
        % variableValue = parts{end};

        % 변수 이름과 값 저장
        % variableNames{end+1} = variableName;
        % variableValues{end+1} = variableValue;
    end

    % categorical 정보 생성
    resultCategorical = table(categorical(variableValues'), 'VariableNames', variableNames);
end
