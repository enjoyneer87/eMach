function resultCategoricalTable = char2CategoricalPropertiesTable(charVariable)
    % 주어진 char 변수를 categorical 정보로 변환하는 함수

    % 주어진 char 변수를 줄 단위로 분할
    lines = strsplit(charVariable, '\n');

    % 결과를 저장할 cell 배열 초기화
    resultCell = cell(length(lines), 1);

    % conditionPropertiesTable 초기화 (빈 table 선언)
    conditionPropertiesTable = table('Size', [0, 4], 'VariableTypes', {'cell', 'cell', 'cell', 'cell'}, 'VariableNames', {'PropertiesName', 'dataType', 'description', 'PropertiesValue'});

    for lineIndex = 1:length(lines)
        % 각 행의 데이터 추출
        data = strsplit(lines{lineIndex}, ' ', 'CollapseDelimiters', true);

        % convertcharCellArray2PropertiesCell 함수 호출하여 결과를 저장
        resultCell = convertcharCellArray2PropertiesCell(data);

        % 결과 데이터를 conditionPropertiesTable에 추가
        % PropertiesName과 dataType를 그대로 저장
        conditionPropertiesTable.PropertiesName{end+1, 1} = resultCell{1};
        conditionPropertiesTable.dataType{end, 1}      = resultCell{2};

        % description 변수에 PropertiesName에 맞게 할당
        conditionPropertiesTable.description{end, 1} = resultCell{3};

        % PropertiesValue 변수를 추후 테이블 데이터를 입력받을 수 있도록 빈 셀 배열로 초기화
        conditionPropertiesTable.PropertiesValue{end, 1} = {};
    end

    % 결과를 categorical 정보로 변환
    conditionPropertiesTable.PropertiesName = categorical(conditionPropertiesTable.PropertiesName);
    conditionPropertiesTable.dataType = categorical(conditionPropertiesTable.dataType);

    % 최종 결과
    resultCategoricalTable = conditionPropertiesTable;
end
