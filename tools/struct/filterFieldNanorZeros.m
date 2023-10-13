function newStruct = filterFieldNanorZeros(targetStruct)
    fieldNames=fieldnames(targetStruct);
    newStruct=targetStruct;
    for i = 1:numel(fieldNames)
        focusName=fieldNames{i}   ;
        checkNZ=isAllZeroOrNan(targetStruct.(focusName));
        if checkNZ==1
        newStruct=rmfield(newStruct,focusName);
        end
        % newStruct.(focusName)=struct.(focusName);
    end
end

