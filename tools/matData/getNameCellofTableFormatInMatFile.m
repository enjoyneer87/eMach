function nameCellofTables=getNameCellofTableFormatInMatFile(filename)
    matobj=matfile(filename);
    scaledData=whos(matobj);
    tableRowsStr = findTableRowsInStruct(scaledData);
    nameCellofTables={tableRowsStr.name};
end