function [otherSlotAreaTable,RegionDataTable,RegionTablePerType]       =findnReNameOtherSlotArea(RegionDataTable)
% findSimilarValuesWithinTolerance
Name4Object         =   'otherSlotArea';
otherSlotAreaTable  =   table();
InsulationAreaTable =   table();
CoreAreaTable       =   table();
ConductorTable      =   table();

%% 

CoreAreaTable      =RegionDataTable(contains(RegionDataTable.Name,'StatorCore'),:);
ConductorTable     =RegionDataTable(contains(RegionDataTable.Name,'Conductor'),:);    
otherSlotAreaTable =RegionDataTable(~contains(RegionDataTable.Name,'Conductor')&~contains(RegionDataTable.Name,'StatorCore'),:);    

%% 이름 변경
    numRepeats              =height(otherSlotAreaTable);
    if numRepeats>1
    disp('Slot내 영역은 1개이상이니 확인하세요')
    end
    cellStringArray         = repmat({Name4Object}, numRepeats, 1);
    otherSlotAreaTable.Name =cellStringArray;

    % 가장큰 영역 Insulation으로 지정
    if numRepeats==1
        if otherSlotAreaTable.Area>ConductorTable.Area(1)
        otherSlotAreaTable(otherSlotAreaTable.Area>ConductorTable.Area(1),:).Name{:}='Insulation'; 
        end

    else
            for indexOtherRegion=1:numRepeats
            otherSlotAreaTable.Name{(1)}='Insulation';      
            otherSlotAreaTable.Name{(indexOtherRegion)}='otherSlotArea';   
            end
    end
%% RegionDataTable Update
% RegionDataTable = updateTableWithOtherTablewithVar(otherSlotAreaTable, RegionDataTable, 'Id');


%% [TB]면적이 unique한지 아니냐에 따라 분류할것
if ~isempty(otherSlotAreaTable)
InsulationAreaTable = otherSlotAreaTable(1,:);
otherSlotAreaTable(1,:) = [];
end


%% if 
RegionTablePerType= struct();
RegionTablePerType.InsulationAreaTable=InsulationAreaTable;
RegionTablePerType.otherSlotAreaTable =otherSlotAreaTable ;         
RegionTablePerType.CoreAreaTable      =CoreAreaTable      ;
RegionTablePerType.ConductorTable     =ConductorTable     ; 
end
