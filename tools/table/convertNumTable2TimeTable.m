function numericTable=convertNumTable2TimeTable(numericTable)
    varNamesCell=numericTable.Properties.VariableNames;    
    numericTable.Properties.VariableNames=cellfun(@(x) strrep(x,'Fun_',''),varNamesCell,'UniformOutput',false);
    varNamesCell=numericTable.Properties.VariableNames;    
    TimeCell    = varNamesCell{contains(varNamesCell,'time','IgnoreCase',true)};
    numericTable = table2timetable(numericTable,'TimeStep',seconds(numericTable(2,TimeCell).Variables-numericTable(1,TimeCell).Variables));
    numericTable =removevars(numericTable,TimeCell);
end