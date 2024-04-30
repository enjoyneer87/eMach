function variableTable = getMcadTableVariable(variableTable, mcad)
    % Motor-CAD 변수 값을 가져오는 함수
    % variableTable: 가져온 변수 값을 업데이트할 테이블
    % mcad: Motor-CAD ActiveX 객체
    % variableTable=ScaledModelParameters_MotorLAB
    % 변수의 자동화 이름을 가져옵니다
    AutomationNameColName = variableTable.AutomationName;

    typeofCurrentValueVarData=class(variableTable.CurrentValue);
    % value값 
    if ~iscell(variableTable.CurrentValue)
    variableTable.CurrentValue=num2cell(variableTable.CurrentValue);
    end

    % 각 변수에 대해 설정 작업을 수행합니다
    for rowIndex = 1:length(AutomationNameColName)
        columnName = AutomationNameColName{rowIndex};
        % 'CurrentValue' 열의 값을 가져와 배열 데이터로 변환합니다
        % 비어있지 않거나 NaN이 아닌 경우 변수 값을 가져옵니다
        if isempty(columnName) == 0 || ~isnan(columnName)
            [~, valueFromMCAD] = mcad.GetVariable(columnName);
        end
        
    % 가져온 배열 데이터를 str Cell로 변환하여 'CurrentValue' 열 값을 업데이트합니다
        typeofArrayData=class(valueFromMCAD);
        switch typeofArrayData
            case 'logical'
            variableTable.CurrentValue{rowIndex}=(valueFromMCAD);
            case 'double'
            variableTable.CurrentValue{rowIndex} = convertArrayData2CharTypeData(valueFromMCAD);
            case 'int32'
            variableTable.CurrentValue{rowIndex} = double(valueFromMCAD);
            case 'Cell'
             variableTable.CurrentValue{rowIndex}= valueFromMCAD;
            case 'char'
             variableTable.CurrentValue{rowIndex}=valueFromMCAD;
        end 
    end

    
end
