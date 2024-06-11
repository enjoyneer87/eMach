function setMcadTableVariable(variableTable, mcad)
    % Motor-CAD 변수 값을 설정하는 함수
    % variableTable: 설정할 변수 정보가 담긴 테이블
    % mcad: Motor-CAD ActiveX 객체

    % 변수의 자동화 이름을 가져옵니다
    AutomationNameColName = variableTable.AutomationName;

    % 각 변수에 대해 설정 작업을 수행합니다
    for rowIndex = 1:length(AutomationNameColName)
        mcadVariableName = AutomationNameColName{rowIndex};

        %% 'CurrentValue' 열의 값을 가져와 배열 데이터로 변환합니다
        if ischar(variableTable.CurrentValue)
         arrayData                          = convertCharTypeData2ArrayData(variableTable.CurrentValue{rowIndex});
        elseif iscell(variableTable.CurrentValue)
         arrayData=variableTable.CurrentValue{rowIndex};
         if contains(mcadVariableName,'name','IgnoreCase',true)
         typeofArrayData= 'cell';
         else
         typeofArrayData=class(arrayData);
         end
         switch typeofArrayData
             % case 'double'
             % arrayData     = arrayData;
             case 'cell'
             arrayData=variableTable.CurrentValue{rowIndex};
             case 'char'
             arrayData     = convertCharTypeData2ArrayData(arrayData);
         end   
         % arrayData = cell2mat(variableTable.CurrentValue(rowIndex));
        elseif isnumeric(variableTable.CurrentValue)
        arrayData =   variableTable.CurrentValue(rowIndex);
        end
        
        %% 실제 입력 
        % 단일 값인 경우
        if length(arrayData) == 1
            % 비어있지 않거나 NaN이 아닌 경우 변수 값을 설정합니다
            if isempty(arrayData) == 0 || ~isnan(arrayData)
                mcad.SetVariable(mcadVariableName, arrayData);
            end
        % 여러 값인 경우
        elseif length(arrayData) > 1    
            % 비어있지 않거나 NaN이 아닌 경우 각 배열 값을 변수에 설정합니다
            if ischar(arrayData) 
                mcad.SetVariable(mcadVariableName, arrayData);              
            elseif isempty(arrayData) == 0 || ~isnan(arrayData)
                for arrayIndex = 1:length(arrayData)
                    mcad.SetArrayVariable(mcadVariableName, arrayIndex-1, arrayData(arrayIndex));
                end
            end
        end      
    end
end
