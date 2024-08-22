function PartStructByType = convertJmagPartStructByType(PartStruct)
AirBarrierTable          =table();
StatorTable              =table();
StatorCoreTable          =table();
RotorCoreTable           =table();
MagnetTable              =table();
SlotTable                =table();
ConductorTable           =table();
InsulationTable          =table();
CenterAirPostTable       =table();
OtherTable               =table();
if isstruct(PartStruct)
    PartTable = struct2table(PartStruct);
    NumberofPart = length(PartStruct);
elseif istable(PartStruct)
    PartTable = PartStruct;
    NumberofPart = height(PartStruct);
end

for partIndex = 1:NumberofPart
    %% 필수

    if ~contains(PartTable.Name(partIndex), 'Rotor')
        if contains(PartTable.Name(partIndex), 'rotor','IgnoreCase',true)
        PartTable.Name(partIndex) = regexprep(PartTable.Name(partIndex), 'rotor', 'Rotor', 'ignorecase');
        end
    end
    if ~contains(PartTable.Name(partIndex), 'Stator')
        if contains(PartTable.Name(partIndex), 'stator','IgnoreCase',true)
        PartTable.Name(partIndex) = regexprep(PartTable.Name(partIndex), 'stator', 'Stator', 'ignorecase');
        end
    end
    
    if strcmp(PartTable.Name(partIndex), 'Stator')
        newRow = PartTable(partIndex, :);
        StatorTable = [AirBarrierTable; newRow];
    elseif contains(PartTable.Name(partIndex), 'StatorCore')
        newRow = PartTable(partIndex, :);
        StatorCoreTable = [StatorCoreTable; newRow];    
    elseif contains(PartTable.Name(partIndex), 'RotorCore')
        newRow = PartTable(partIndex, :);
        RotorCoreTable = [RotorCoreTable; newRow];
    else
        % 기존 문자열
    end
end


if isempty(StatorCoreTable)
StatorTable=PartTable(contains(PartTable.Name, 'Stator','IgnoreCase',true),:);
StatorAreas=uniquetol(StatorTable.Area,1e-5);
StatorCoreTable= StatorTable(StatorTable.Area==max(StatorAreas),:);
StatorCoreTable.Name{:}='Stator/StatorCore';
elseif isempty(RotorCoreTable)
RotorTable=PartTable(contains(PartTable.Name, 'Rotor','IgnoreCase',true),:);
RotorAreas=uniquetol(StatorTable.Area,1e-5);
RotorCoreTable= RotorTable(RotorTable.Area==max(RotorAreas),:);
RotorCoreTable.Name{:}='Rotor/RotorCore';
end

for partIndex = 1:NumberofPart
    if strcmp(PartTable.Name(partIndex), 'RotorAirBarrier')
        % AirBarrierStruct에 새로운 행을 추가합니다.
        newRow = PartTable(partIndex, :);
        AirBarrierTable = [AirBarrierTable; newRow];
    elseif contains(PartTable.Name(partIndex), 'Magnet')
        newRow = PartTable(partIndex, :);
        MagnetTable = [MagnetTable; newRow];    
    elseif contains(PartTable.Name(partIndex), 'Slot')
        newRow = PartTable(partIndex, :);
        SlotTable = [SlotTable; newRow];   
    elseif contains(PartTable.Name(partIndex), 'Conductor')
        newRow = PartTable(partIndex, :);
        ConductorTable = [ConductorTable; newRow];
    elseif contains(PartTable.Name(partIndex), 'Wire','IgnoreCase',true)
        newRow = PartTable(partIndex, :);
        ConductorTable = [ConductorTable; newRow];
    elseif contains(PartTable.Name(partIndex), 'Insulation')
        newRow = PartTable(partIndex, :);
        InsulationTable = [InsulationTable; newRow];
    elseif contains(PartTable.Name(partIndex), 'CenterAirPost')
        newRow = PartTable(partIndex, :);
        CenterAirPostTable = [CenterAirPostTable; newRow];
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
PartStructByType.CenterAirPostTable        =CenterAirPostTable   ;
PartStructByType.OtherTable        =OtherTable   ;



end