function numericTable=convertNumTable2TFreqTable(numericTable)
    varNamesCell=numericTable.Properties.VariableNames;    
    numericTable.Properties.VariableNames=cellfun(@(x) strrep(x,'Fun_',''),varNamesCell,'UniformOutput',false);
    varNamesCell=numericTable.Properties.VariableNames;    
    FreqCell    = varNamesCell{contains(varNamesCell,'Freq','IgnoreCase',true)};
    % numericTable = table2timetable(numericTable,'TimeStep',seconds(numericTable(2,TimeCell).Variables-numericTable(1,TimeCell).Variables));
    numericTable.Properties.RowNames=cellstr(num2str(numericTable.(FreqCell)));
    numericTable =removevars(numericTable,FreqCell);
end