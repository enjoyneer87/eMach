function newStruct = filterWithFieldValueStruct(structArray, FieldName, stringCell)
    % structArray: 검색 대상이 되는 구조체 배열
    % FieldName: 일치 여부를 확인할 필드 이름
    % stringCell: 일치 여부를 확인할 문자열 cell 배열

    % 초기화
    matchedStruct = {};

    % 구조체 배열을 반복하면서 일치하는 행을 찾아서 새 구조체에 추가
    for i = 1:numel(structArray)
        % 현재 구조체의 필드 값을 가져옴
        value2Check = structArray(i).(FieldName);
        
        % value2Check와 stringCell 비교하여 일치하는 값이 있는지 확인
        isMatched = ismember(stringCell, value2Check);

        % 일치하는 경우, 해당 구조체를 matchedStruct에 추가
        if any(isMatched)
            matchedStruct{end + 1} = structArray(i);
        end
    end
    
    for i=1:length(matchedStruct)
     newStruct(i)=matchedStruct{i};
    end
end
