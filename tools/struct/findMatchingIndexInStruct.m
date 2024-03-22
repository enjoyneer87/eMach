function matchingIndicesOfStruct=findMatchingIndexInStruct(PartStruct,FieldName,things2Find)

    if isnumeric(things2Find)
    matchingIndicesOfStruct = findStructsWithValue(PartStruct, FieldName, things2Find);
    elseif ischar(things2Find) || isstring(things2Find)
    matchingIndicesOfStruct=findContainsInStruct(PartStruct,FieldName,desiredName); 
    else
        disp('thing2find 데이터형태가 부적합하네요')
    end

end
