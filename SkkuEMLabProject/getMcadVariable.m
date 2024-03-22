function StructData=getMcadVariable(StructData,mcad)    
%%  dependency Check
    % convertCharTypeData2FieldData
    if isstruct(StructData)
    variableFieldsName = fieldnames(StructData);
    elseif ischar(StructData)
    variableFieldsName=StructData;   
    end
    %% fieldIndex 1은 motFile Path
    
    for fieldIndex = 1:length(fieldnames(StructData))
        fieldName = variableFieldsName{fieldIndex};
        originalFieldName = fieldName; % Store the original field name
        
        if contains(fieldName, 'Array')
            [~, L1] = mcad.GetArrayVariable(fieldName, 0);
            [~, L2] = mcad.GetArrayVariable(fieldName, 1);
            fieldData = [double(L1), double(L2)];
        else
            fieldName=replaceMLABvar2MCADvar(fieldName); % 일괄적으로 매틀랩에서 허용하지 않는 변수명을 모터캐드 변수명을 변환
            [~, fieldData] = mcad.GetVariable(fieldName);            
        end       
        % Use the original field name for assignment
        [~, fieldData] = mcad.GetVariable(fieldName);
        if strcmp(fieldName,'CurrentMotFilePath_MotorLAB')
        StructData.(originalFieldName)=fieldData;    
        else
        fieldData = convertCharTypeData2ArrayData(fieldData); % char형을 배열로
        StructData.(originalFieldName) = fieldData;
        end
    end
end