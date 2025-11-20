function structModified = splitFieldArray(inputStruct)
    % 구조체의 모든 필드에서 0인 행을 삭제하는 함수
    % 입력:
    % inputStruct - 처리할 구조체
    % 출력:
    % structModified - 수정된 구조체
    
    % 구조체의 필드 이름 가져오기
    fieldNames = fieldnames(inputStruct);
    
    
    % 각 필드에 대해 반복
    for i = 1:length(fieldNames)
        % 현재 필드 이름
        currentFieldName = fieldNames{i};
        % 현재 필드의 데이터 타입 확인 (수치형 배열인지)
        lengthFieldArray=len(inputStruct.(currentFieldName));
        if lengthFieldArray>1
            % 현재 필드 데이터 가져오기
            fieldData = inputStruct.(currentFieldName);         
            inputStruct=rmfield(inputStruct,currentFieldName);
            for fieldDataIndex=1:lengthFieldArray
                NewFieldName=[currentFieldName,'_',num2str(fieldDataIndex)];
                inputStruct.(NewFieldName)=fieldData(fieldDataIndex);
            end              
        end
    end
        
    structModified = inputStruct;

end
