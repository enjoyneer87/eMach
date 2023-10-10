function [filteredTable, MatchedcategoryName] = findAutomationNameFromAllCategory(ActiveXParametersStruct, filterCriteria)
    categoryNameList = fieldnames(ActiveXParametersStruct);
    filteredTable = table();
    MatchedcategoryName = {};

    % Find matching indices for the given filterCriteria
    for categoryIndex = 1:length(categoryNameList)
        categoryName = categoryNameList{categoryIndex};
        MCADsomeTable = ActiveXParametersStruct.(categoryName);    
        matchingIndices = findMatchingIndex(MCADsomeTable.AutomationName, filterCriteria);
        
        % Filter the table using the matching indices
        if ~isempty(matchingIndices)
            tempTable = MCADsomeTable(matchingIndices, :);
            tempTable.Category = repmat({categoryName}, size(tempTable, 1), 1);
            filteredTable = [filteredTable; tempTable];
            MatchedcategoryName{end+1} = categoryName;
        end
    end
end
