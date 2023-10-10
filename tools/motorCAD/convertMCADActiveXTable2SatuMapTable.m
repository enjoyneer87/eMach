function ActiveXSatuMapTable=convertMCADActiveXTable2SatuMapTable(ActiveXTable)
    myStruct=convertMCADActiveXTable2MCADVarStruct(ActiveXTable);
    ActiveXSatuMapTable=struct2table(myStruct);
    ActiveXSatuMapTable.Properties.VariableUnits=cellstr(ActiveXTable.Units);   
end

