function NewDOEStruct = getOnlyWeightofDOEStruct(DOE6P54sVCobalt)
    fieldNames = fieldnames(DOE6P54sVCobalt);
    
    % Initialize the NewDOEStruct
    NewDOEStruct = struct();

    % Iterate over field names
    for i = 1:length(fieldNames)
        fieldName = fieldNames{i};
        if isfield(DOE6P54sVCobalt.(fieldName), 'Weight')
            NewDOEStruct.(fieldName).Weight = DOE6P54sVCobalt.(fieldName).Weight;
        end
    end
end
