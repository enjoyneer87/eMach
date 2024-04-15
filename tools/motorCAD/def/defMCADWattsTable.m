function McadWattsTable=defMCADWattsTable()
    %% ActiveX mat파일로부터 구조체(테이블) 불러오기 존재해야됨
    MCADStruct=defMcadTableStruct();
    
    %% Watt테이블 정의 (Magnetics와 손실값, OutputSheet들)
    MCADMagTable    =MCADStruct.Magnetics;
    LossInjTable    =MCADStruct.Loss_and_Injected_Power_Values;
    proximityTable  =defMcadTable('Proximity_Loss');
    outputSheetTable=defMcadTable('OutputSheets');

    McadWattsTable=[MCADMagTable;proximityTable;LossInjTable;outputSheetTable];

    McadWattsTable = filterMCADTableWithAnyInfo(McadWattsTable, 'Watts','Units');
    % McadWattsTable = filterMCADTableWithAnyInfo(McadWattsTable, 'o/p','Input_Output');



end
