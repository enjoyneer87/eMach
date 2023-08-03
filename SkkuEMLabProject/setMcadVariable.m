function variable=setMcadVariable(variable,mcad)
    % mcad = actxserver('MotorCAD.AppAutomation');
    % mcad.LoadFromFile(variable.motFile);

    % GetCurrent Data
    variableFieldsName = fieldnames(variable);


    % fieldIndex 1은 motFile Pat
    for fieldIndex = 1:length(fieldnames(variable))
        fieldName = variableFieldsName{fieldIndex};
        originalFieldName = fieldName; % Store the original field name

        % Magnet Layer 2 이상사용할려면 아래 수정할것
        if contains(fieldName, 'Array')
            if length(variable.(fieldName))==1
                mcad.SetArrayVariable(fieldName, 0,variable.(fieldName)(1));
            elseif length(variable.(fieldName))==2
                mcad.SetArrayVariable(fieldName, 0,variable.(fieldName)(1));
                mcad.SetArrayVariable(fieldName, 1,variable.(fieldName)(2));
            elseif length(variable.(fieldName))==3
                mcad.SetArrayVariable(fieldName, 0,variable.(fieldName)(1));
                mcad.SetArrayVariable(fieldName, 1,variable.(fieldName)(2));
                mcad.SetArrayVariable(fieldName, 2,variable.(fieldName)(3));
            end
        else
            if length(variable.(fieldName))==1 
                fieldName=replaceMLABvar2MCADvar(fieldName); % 일괄적으로 매틀랩에서 허용하지 않는 변수명을 모터캐드 변수명을 변환
                if isempty(variable.(originalFieldName))==0 || ~isnan(variable.(originalFieldName)) % 비어있지 않은 Field값만 입력
                   mcad.SetVariable(fieldName,double(variable.(originalFieldName)));
                end
            end
        end       
    end
end