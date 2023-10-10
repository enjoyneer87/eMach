function scatter3dqTable(filteredTable,value)
    scatter3(filteredTable.Id_Peak,filteredTable.Iq_Peak,filteredTable.(value));
end