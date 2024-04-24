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
        originalFieldName = fieldName;               % Store the original field name
        fieldName=replaceMLABvar2MCADvar(fieldName); % 일괄적으로 매틀랩에서 허용하지 않는 변수명을 모터캐드 변수명을 변환
        [~, fieldData] = mcad.GetVariable(fieldName);
            if strcmp(fieldName,'CurrentMotFilePath_MotorLAB')
            StructData.(originalFieldName)=fieldData;    
            else
            fieldData = convertCharTypeData2ArrayData(fieldData); % char형을 배열로
            StructData.(originalFieldName) = fieldData;
            end
    end
end