function newStruct = filterFieldwithStrCellFromStruct(struct, stringCell)
    fieldNames=fieldnames(struct);
    fieldIndex=contains(fieldNames,stringCell);
    focusNameCell=fieldNames(fieldIndex);
    for i = 1:numel(focusNameCell)
        focusName=focusNameCell{i}   ;
        newStruct.(focusName)=struct.(focusName);
    end
end

