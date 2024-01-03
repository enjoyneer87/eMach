function [otherSlotAreaTable,RegionDataTable,RegionTablePerType]       =findnReNameOtherSlotArea(RegionDataTable)
% findSimilarValuesWithinTolerance
Name4Object         =   'otherSlotArea';
otherSlotAreaTable  =   table();
InsulationAreaTable =   table();
CoreAreaTable       =   table();
ConductorTable      =   table();
TableIndex4RegionTable =table();   

%% 
    for Index4RegionTable=1:height(RegionDataTable)  
        if strcmp(RegionDataTable.Type{Index4RegionTable},'RegionItem')
            %% StatorCore
            if strcmp(RegionDataTable.Name{Index4RegionTable},'StatorCore')
            CoreAreaTable=[CoreAreaTable;RegionDataTable(Index4RegionTable,:)];
            end
            %% Conductor
            if contains(RegionDataTable.Name{Index4RegionTable},'Conductor')
            ConductorTable=[ConductorTable;RegionDataTable(Index4RegionTable,:)];
            end
            %% Other
            if ~strcmp(RegionDataTable.Name{Index4RegionTable},'StatorCore')&&~contains(RegionDataTable.Name{Index4RegionTable},'Conductor') contains(RegionDataTable.Name{Index4RegionTable},'Housing') 
            TableIndex4RegionTable = [TableIndex4RegionTable; table(Index4RegionTable) ];    
            otherSlotAreaTable=[otherSlotAreaTable;RegionDataTable(Index4RegionTable,:) ];

            end
        end
    end

%% 이름 변경
    numRepeats              =height(otherSlotAreaTable);
    if numRepeats>1
    disp('Slot내 영역은 1개이상이니 확인하세요')
    end
    cellStringArray         = repmat({Name4Object}, numRepeats, 1);
    otherSlotAreaTable.Name =cellStringArray;

    % 가장큰 영역 Insulation으로 지정
    if numRepeats==1
    otherSlotAreaTable(otherSlotAreaTable.Area>ConductorTable.Area(1),:).Name{:}='Insulation'; 
    else
            for indexOtherRegion=1:numRepeats
            otherSlotAreaTable.Name{(1)}='Insulation';      
            otherSlotAreaTable.Name{(indexOtherRegion)}='otherSlotArea';   
            end
    end

% RegionDataTable도 이름 변경
    for i=1:height(TableIndex4RegionTable)
    Index4RegionTable=TableIndex4RegionTable.Index4RegionTable(i);
    RegionDataTable(Index4RegionTable,:)=otherSlotAreaTable(i,:);
    end
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
