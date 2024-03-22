function McadWattsTable=defMCADWattsTable()
    %% mat파일이 존재해야됨
    MCADStruct=defMcadTableStruct();

    %%
    MCADMagTable    =MCADStruct.Magnetics;
    LossInjTable    =MCADStruct.Loss_and_Injected_Power_Values;
    proximityTable  =defMcadTable('Proximity_Loss');
    outputSheetTable=defMcadTable('OutputSheets');

    McadWattsTable=[MCADMagTable;proximityTable;LossInjTable;outputSheetTable];

    McadWattsTable = filterMCADTableWithAnyInfo(McadWattsTable, 'Watts','Units');
    % McadWattsTable = filterMCADTableWithAnyInfo(McadWattsTable, 'o/p','Input_Output');



end
