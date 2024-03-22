function matchingIndices=findMatchingIndexInStruct(PartStruct,FieldName,desiredName)
    isMatched=findIsMatchedInStruct(PartStruct,FieldName,desiredName);    
    matchingIndices = find(isMatched);
end