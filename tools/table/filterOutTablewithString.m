function filteredTable=filterOutTablewithString(NonZeroTable,string2filter)
    filterOutIndex=contains(NonZeroTable.Properties.VariableNames,string2filter,'IgnoreCase',true);
    filteredTable=NonZeroTable(:,~filterOutIndex);
end