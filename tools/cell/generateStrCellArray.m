function rowNames = generateStrCellArray(startStr, numStart, numEnd, endStr)
    rowNames = cell(1, numEnd - numStart + 1);
    for i = numStart:numEnd
        rowNames{i - numStart + 1} = [startStr, num2str(i), endStr];
    end
end
