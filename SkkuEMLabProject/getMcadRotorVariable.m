function variable = getMcadRotorVariable(variable,mcad)
    % mcad = actxserver('MotorCAD.AppAutomation');
    mcad.LoadFromFile(variable.motFile);
    % GetCurrent Data
    variableFieldsName = fieldnames(variable);

    %% fieldIndex 1은 motFile Path
    
    for fieldIndex = 2:length(fieldnames(variable))
        fieldName = variableFieldsName{fieldIndex};
        originalFieldName = fieldName; % Store the original field name
        
        if contains(fieldName, 'Array')
            [success, L1] = mcad.GetArrayVariable(fieldName, 0);
            [success, L2] = mcad.GetArrayVariable(fieldName, 1);
            charTypeData = [double(L1), double(L2)];
        else
            if contains(fieldName, 'Rear')
                fieldName = strrep(fieldName, 'Rear', '[R]');
            elseif contains(fieldName, 'Front')
                fieldName = strrep(fieldName, 'Front', '[F]');
            end
            [success, charTypeData] = mcad.GetVariable(fieldName);
        end       
        % Use the original field name for assignment
        variable.(originalFieldName) = double(charTypeData);
    end
end