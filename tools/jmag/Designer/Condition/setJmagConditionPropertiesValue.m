function setJmagConditionPropertiesValue(ConditionPropertiesTable,ConditionObj)
    
    for ConditionPropertiesIndex=1:height(ConditionPropertiesTable)
        propertiesNameCell=cellstr(ConditionPropertiesTable.PropertiesName(ConditionPropertiesIndex));
        if ~isempty(ConditionPropertiesTable.PropertiesValue{ConditionPropertiesIndex})
            ConditionObj.SetValue(propertiesNameCell{:},ConditionPropertiesTable.PropertiesValue{ConditionPropertiesIndex});
        else
            disp('속성 값이 비어있습니다')
        end
    end

end