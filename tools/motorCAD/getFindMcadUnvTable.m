function McadOCLossWattsTable=getFindMcadUnvTable(mcad,str,McadWattsTable)
mcad.SetVariable('MessageDisplayState',2);
McadOCLossWattsTable=filterMCADTable(McadWattsTable,str);
McadOCLossWattsTable=getMcadTableVariable(McadOCLossWattsTable,mcad);
McadOCLossWattsTable = convertMCADTableCurrentValueToDouble(McadOCLossWattsTable);
McadOCLossWattsTable = filterMCADTableZeroValue(McadOCLossWattsTable);
McadOCLossWattsTable = convertMcadTable2UnvTable(McadOCLossWattsTable);

end