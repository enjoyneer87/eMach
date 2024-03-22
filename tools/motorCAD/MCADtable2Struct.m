function resultStruct = MCADtable2Struct(mcadTable)
    % tableToStruct - mcadTable의 automationName을 필드로 하고 doubleValue를 값으로 하는 구조체로 변경
    %
    % Inputs:
    %   mcadTable - 'automationName'과 'doubleValue' 변수를 포함한 원본 테이블
    %
    % Outputs:
    %   resultStruct - 생성된 구조체

    % 초기 빈 구조체 생성
    resultStruct = struct();
    
    % 테이블의 각 행에 대해 반복
    for i = 1:height(mcadTable)
        % 현재 행의 automationName과 doubleValue 값 가져오기
        fieldName = mcadTable.AutomationName{i};
        fieldValue = mcadTable.doubleValue(i);
        
        % 필드 이름의 유효성 검사 및 필드 이름 조정
        fieldName = matlab.lang.makeValidName(fieldName);
        
        % 구조체에 필드와 값 추가
        resultStruct.(fieldName) = fieldValue;
    end
end
