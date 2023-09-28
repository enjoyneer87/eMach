function variableTable = getMcadTableVariable(variableTable, mcad)
    % Motor-CAD 변수 값을 가져오는 함수
    % variableTable: 가져온 변수 값을 업데이트할 테이블
    % mcad: Motor-CAD ActiveX 객체
    % variableTable=ScaledModelParameters_MotorLAB
    % 변수의 자동화 이름을 가져옵니다
    AutomationNameColName = variableTable.AutomationName;

    typeofData=class(variableTable.CurrentValue);
    if ~iscell(variableTable.CurrentValue)
    variableTable.CurrentValue=num2cell(variableTable.CurrentValue);
    end
    % 각 변수에 대해 설정 작업을 수행합니다
    for rowIndex = 1:length(AutomationNameColName)
        columnName = AutomationNameColName{rowIndex};
        % 'CurrentValue' 열의 값을 가져와 배열 데이터로 변환합니다
        switch typeofData
            case 'cell'
            charTypedData = variableTable.CurrentValue{rowIndex};
            arrayData     = convertCharTypeData2ArrayData(charTypedData);
            case 'double'
            arrayData     = variableTable.CurrentValue(rowIndex);
        end

        % 단일 값인 경우
        if length(arrayData) == 1
            % 비어있지 않거나 NaN이 아닌 경우 변수 값을 가져옵니다
            if isempty(arrayData) == 0 || ~isnan(arrayData)
                [~, arrayData] = mcad.GetVariable(columnName);
            end

        % 여러 값인 경우
        elseif length(arrayData) > 1    
            % 비어있지 않거나 NaN이 아닌 경우 각 배열 값을 변수에서 가져옵니다
            if isempty(arrayData) == 0 || ~isnan(arrayData)
                for arrayIndex = 1:length(arrayData)
                     [~, arrayData(arrayIndex)] = mcad.GetArrayVariable(columnName, arrayIndex-1);
                end
            end
        end
        
        % 가져온 배열 데이터를 문자열로 변환하여 'CurrentValue' 열 값을 업데이트합니다
        typeofArrayData=class(arrayData);
    switch typeofArrayData
        case 'logical'
        variableTable.CurrentValue{rowIndex}=(arrayData);
        case 'double'
        variableTable.CurrentValue{rowIndex} = convertArrayData2CharTypeData(arrayData);
        case 'Cell'
         variableTable.CurrentValue{rowIndex}= arrayData;
        case 'char'
         variableTable.CurrentValue{rowIndex}=arrayData;

    end 
    end
end
