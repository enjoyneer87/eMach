function variable = getMcadRotorVariable(variable,mcad)
    
%%  dependency Check
    % convertCharTypeData2FieldData

    variableFieldsName = fieldnames(variable);
    %% fieldIndex 1은 motFile Path
    
    for fieldIndex = 1:length(fieldnames(variable))
        fieldName = variableFieldsName{fieldIndex};
        originalFieldName = fieldName; % Store the original field name
        
        if contains(fieldName, 'Array')
            [~, L1] = mcad.GetArrayVariable(fieldName, 0);
            [~, L2] = mcad.GetArrayVariable(fieldName, 1);
            fieldData = [double(L1), double(L2)];
        else
            replaceMLABvar2MCADvar(fieldName); % 일괄적으로 매틀랩에서 허용하지 않는 변수명을 모터캐드 변수명을 변환
            [~, fieldData] = mcad.GetVariable(fieldName);            
        end       
        % Use the original field name for assignment
        [~, fieldData] = mcad.GetVariable(fieldName);
        fieldData = convertCharTypeData2ArrayData(fieldData); % char형을 배열로
        variable.(originalFieldName) = fieldData;
    end
end

