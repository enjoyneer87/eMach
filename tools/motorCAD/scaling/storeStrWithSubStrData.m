function MachineData = storeStrWithSubStrData(MachineData, category, paramName,filteredTable)
    if ~isempty(filteredTable)
        currentValue = filteredTable.CurrentValue{:};
        TempCurrentValue = convertCharTypeData2ArrayData(currentValue); % char형을 배열로
        % TempCurrentValue = str2double(currentValue);
        if ~isnan(TempCurrentValue)
        currentValue=TempCurrentValue;           
        end
        MachineData.(category).(paramName) = currentValue;
    else
        warning('No matching parameter found for %s');
    end
    return;  % Return the updated BuildingData
end



