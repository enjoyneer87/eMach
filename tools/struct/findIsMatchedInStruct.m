function isMatched=findIsMatchedInStruct(PartStruct,FieldName,desiredName)
    isMatched = strcmp({PartStruct.(FieldName)}, desiredName); % 'RotorCore'를 가지는 행 인덱스 찾기
end