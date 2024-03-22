function McadWattsTable=getMCADWattsTable(mcad)
    mcad.SetVariable('MessageDisplayState',2);
    McadWattsTable=defMCADWattsTable();
    McadWattsTable=getMcadTableVariable(McadWattsTable,mcad);
    McadWattsTable = convertMCADTableCurrentValueToDouble(McadWattsTable);
    McadWattsTable = filterMCADTableZeroValue(McadWattsTable);

end