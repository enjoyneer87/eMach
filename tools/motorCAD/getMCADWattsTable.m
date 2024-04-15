function McadWattsTable=getMCADWattsTable(mcad)

    %% Watt테이블 정의 (Magnetics와 손실값, OutputSheet들)
    mcad.SetVariable('MessageDisplayState',2);
    McadWattsTable=defMCADWattsTable();
    McadWattsTable=getMcadTableVariable(McadWattsTable,mcad);


    %% 데이터 정리
    McadWattsTable = convertMCADTableCurrentValueToDouble(McadWattsTable);
    McadWattsTable = filterMCADTableZeroValue(McadWattsTable);

end