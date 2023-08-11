function McadVariableTable = updateMcadTableVariable(McadVariableTable, propertiesName, newValue)
    % McadVariableTable의 변수 값을 업데이트하는 함수
    % McadVariableTable: 업데이트할 변수 정보가 담긴 테이블
    % propertiesName: 업데이트할 변수의 이름
    % newValue: 새로운 값

    idx = strcmp(McadVariableTable.AutomationName, propertiesName);

    currentValue = McadVariableTable.CurrentValue(idx);

    % currentValue의 데이터 형식에 따라 newValue를 적절하게 변환하여 업데이트합니다
    if ischar(currentValue)
        newValue = convertArrayData2CharTypeData(newValue);
    elseif iscell(currentValue)
        newValue = cell(newValue);
    elseif isnumeric(currentValue)
        McadVariableTable.CurrentValue(idx) = newValue; % 값이 숫자인 경우 newValue 그대로 사용
    end

    McadVariableTable.CurrentValue(idx) = newValue;
end
