function  propertiesTable=getJMagStudyPropertiesTableValue(propertiesTable,StudyPropertiesObj)

AutomationNameColName        =propertiesTable.PropertiesName;
typeofCurrentValueVarData    =propertiesTable.Category;

%% For문
    for rowIndex = 1:length(AutomationNameColName)
        columnName = AutomationNameColName{rowIndex};
        % if isempty(columnName) == 0 || ~isnan(columnName)
        %     [~, valueFromMCAD] = mcad.GetVariable(columnName);
        % end        

    % 가져온 배열 데이터를 str Cell로 변환하여 'CurrentValue' 열 값을 업데이트합니다
        typeofArrayData=typeofCurrentValueVarData{rowIndex};
        switch typeofArrayData
            case 'Flag'
            % propertiesTable.('PropertiesValue'){rowIndex}=StudyPropertiesObj.GetFlagAsString(columnName);
            propertiesTable.('PropertiesValue'){rowIndex} =StudyPropertiesObj.GetValue(columnName);
            case 'Double'
            % variableTable.CurrentValue{rowIndex} = StudyProperties.GetValueWithUnit(columnName);
            propertiesTable.('PropertiesValue'){rowIndex} =StudyPropertiesObj.GetValue(columnName);
            case 'Coordinate System'
            propertiesTable.('PropertiesValue'){rowIndex} = StudyPropertiesObj.GetCoordinateSystemName(columnName);
            % propertiesTable.('PropertiesValue'){rowIndex} = StudyProperties.GetCoordinateSystemIndex(columnName);
            case 'Table'
            propertiesTable.('PropertiesValue'){rowIndex}= StudyPropertiesObj.GetTable(columnName);
            
  
            case 'String'
            propertiesTable.('PropertiesValue'){rowIndex}=StudyPropertiesObj.GetStringValue(columnName);
        end 
    end


%% Value Out
% propertiesTableWithValue=propertiesTable;

end