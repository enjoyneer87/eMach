function PartStructByType = convertJmagPartStructByType(PartStruct)
AirBarrierTable          =table();
StatorTable              =table();
StatorCoreTable          =table();
RotorCoreTable           =table();
MagnetTable              =table();
SlotTable                =table();
ConductorTable           =table();
InsulationTable          =table();
OtherTable               =table();
PartTable = struct2table(PartStruct);
NumberofPart = length(PartStruct);
for partIndex = 1:NumberofPart
    if strcmp(PartTable.Name(partIndex), 'RotorAirBarrier')
        % AirBarrierStruct에 새로운 행을 추가합니다.
        newRow = PartTable(partIndex, :);
        AirBarrierTable = [AirBarrierTable; newRow];
    elseif strcmp(PartTable.Name(partIndex), 'Stator')
        newRow = PartTable(partIndex, :);
        StatorTable = [AirBarrierTable; newRow];   
    elseif contains(PartTable.Name(partIndex), 'StatorCore')
        newRow = PartTable(partIndex, :);
        StatorCoreTable = [StatorCoreTable; newRow];    
    elseif contains(PartTable.Name(partIndex), 'RotorCore')
        newRow = PartTable(partIndex, :);
        RotorCoreTable = [RotorCoreTable; newRow];    
    elseif contains(PartTable.Name(partIndex), 'Magnet')
        newRow = PartTable(partIndex, :);
        MagnetTable = [MagnetTable; newRow];    
    elseif contains(PartTable.Name(partIndex), 'Slot')
        newRow = PartTable(partIndex, :);
        SlotTable = [SlotTable; newRow];   
    elseif contains(PartTable.Name(partIndex), 'Conductor')
        newRow = PartTable(partIndex, :);
        ConductorTable = [ConductorTable; newRow];
    elseif contains(PartTable.Name(partIndex), 'Insulation')
        newRow = PartTable(partIndex, :);
        InsulationTable = [InsulationTable; newRow];
    else
        newRow = PartTable(partIndex, :);
        OtherTable = [OtherTable; newRow];
    end
end


PartStructByType.AirBarrierTable   =AirBarrierTable   ;
PartStructByType.StatorTable       =StatorTable       ;
PartStructByType.StatorCoreTable   =StatorCoreTable   ;
PartStructByType.RotorCoreTable    =RotorCoreTable    ;
PartStructByType.MagnetTable       =MagnetTable       ;
PartStructByType.SlotTable         =SlotTable         ;
PartStructByType.ConductorTable    =ConductorTable    ;
PartStructByType.InsulationTable   =InsulationTable   ;
PartStructByType.OtherTable        =OtherTable   ;

end