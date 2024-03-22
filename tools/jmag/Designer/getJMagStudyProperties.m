function propertiesTableWithValue=getJMagStudyProperties(Study)

StudyProperties =Study.GetStudyProperties();
propertiesTable=defJMAG2DStudyPropertiesTable(Study);

AutomationNameColName        =propertiesTable.propertiesName;
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
            propertiesTable.('PropertiesValue(KeyValue)'){rowIndex}=StudyProperties.GetFlagAsString(columnName);
            case 'Double'
            % variableTable.CurrentValue{rowIndex} = StudyProperties.GetValueWithUnit(columnName);
            propertiesTable.('PropertiesValue(KeyValue)'){rowIndex} =StudyProperties.GetValue(columnName);
            case 'Coordinate System'
            propertiesTable.('PropertiesValue(KeyValue)'){rowIndex} = StudyProperties.GetCoordinateSystemName(columnName);
            % propertiesTable.('PropertiesValue(KeyValue)'){rowIndex} = StudyProperties.GetCoordinateSystemIndex(columnName);
            case 'Table'
            propertiesTable.('PropertiesValue(KeyValue)'){rowIndex}= StudyProperties.GetTable(columnName);
            case 'String'
            propertiesTable.('PropertiesValue(KeyValue)'){rowIndex}=StudyProperties.GetStringValue(columnName);
        end 
    end

%% Value Out
propertiesTableWithValue=propertiesTable;

end