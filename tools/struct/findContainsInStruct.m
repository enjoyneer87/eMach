function matchingIndices=findContainsInStruct(PartStruct,FieldName,desiredName)

    isMatched       = contains({PartStruct.(FieldName)}, desiredName,"IgnoreCase",true); % 'RotorCore'를 가지는 행 인덱스 찾기
    matchingIndices = find(isMatched);
end