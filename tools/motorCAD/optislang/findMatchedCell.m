function matchedWithCSVFileVariable=findMatchedCell(VariableNamesCSV,variableCombinedCell)
matchedWithCSVFileVariable = {};
for i = 1:numel(VariableNamesCSV)
    for j = 1:numel(variableCombinedCell)
        if contains(variableCombinedCell{j}, VariableNamesCSV{i})
            matchedWithCSVFileVariable{end+1} = VariableNamesCSV{i};
        end
    end
end
end