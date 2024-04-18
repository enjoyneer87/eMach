function nameCellofTables=getNameCellofTableFormatInMatFile(filename)
    matobj           =matfile(filename);
    matFileData       =whos(matobj);
    tableRowsStr     = findTableRowsInStruct(matFileData);
    nameCellofTables ={tableRowsStr.name};
end