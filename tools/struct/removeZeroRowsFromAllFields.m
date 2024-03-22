function structModified = removeZeroRowsFromAllFields(inputStruct)
    % 구조체의 모든 필드에서 0인 행을 삭제하는 함수
    % 입력:
    % inputStruct - 처리할 구조체
    % 출력:
    % structModified - 수정된 구조체
    
    % 구조체의 필드 이름 가져오기
    fieldNames = fieldnames(inputStruct);
    
    % 구조체 복사
    structModified = inputStruct;
    
    % 각 필드에 대해 반복
    for i = 1:length(fieldNames)
        % 현재 필드 이름
        currentFieldName = fieldNames{i};
        
        % 현재 필드의 데이터 타입 확인 (수치형 배열인지)
        if isnumeric(inputStruct.(currentFieldName))
            % 현재 필드 데이터 가져오기
            fieldData = inputStruct.(currentFieldName);
            
            % removeZeroRows 함수를 사용하여 0인 행 삭제
            modifiedFieldData = removeZeroRows(fieldData);
            
            % 수정된 데이터를 구조체의 필드에 다시 저장
            structModified.(currentFieldName) = modifiedFieldData;
        end
    end
end
