function newStruct = filterFieldwithStrCellFromStruct(matData1, stringCell)
    fieldNames=fieldnames(matData1);
    fieldIndex=contains(fieldNames,stringCell);
    focusNameCell=fieldNames(fieldIndex);
    for i = 1:numel(focusNameCell)
        focusName=focusNameCell{i}   ;
        newStruct.(focusName)=matData1.(focusName);
    end
end

