function [otherSlotAreaTable,RegionDataTable]=findnReNameOtherSlotArea(RegionDataTable)
% findSimilarValuesWithinTolerance
Name4Object='otherSlotArea';
otherSlotAreaTable  =table();
CoreAreaTable       =table();
ConductorTable      =table();
TableIndex4RegionTable =table();   
    for Index4RegionTable=1:height(RegionDataTable)  
        if strcmp(RegionDataTable.Type{Index4RegionTable},'RegionItem')
            if strcmp(RegionDataTable.Name{Index4RegionTable},'StatorCore')
            CoreAreaTable=[CoreAreaTable;RegionDataTable(Index4RegionTable,:)];
            end
            if contains(RegionDataTable.Name{Index4RegionTable},'Conductor')
            ConductorTable=[ConductorTable;RegionDataTable(Index4RegionTable,:)];
            end
            if ~strcmp(RegionDataTable.Name{Index4RegionTable},'StatorCore')&&~contains(RegionDataTable.Name{Index4RegionTable},'Conductor') 
            TableIndex4RegionTable = [TableIndex4RegionTable; table(Index4RegionTable) ];    
            otherSlotAreaTable=[otherSlotAreaTable;RegionDataTable(Index4RegionTable,:) ];

            end
        end
    end

% 이름 변경
    numRepeats              =height(otherSlotAreaTable);
    if numRepeats>1
    disp('Slot내 영역은 1개이상이니 확인하세요')
    end
    cellStringArray         = repmat({Name4Object}, numRepeats, 1);
    otherSlotAreaTable.Name =cellStringArray;
    % 가장큰 영역 Insulation으로 지정
    otherSlotAreaTable(otherSlotAreaTable.Area>ConductorTable.Area(1),:).Name{:}='Insulation';   
% RegionDataTable도 이름 변경
    for i=1:height(TableIndex4RegionTable)
    Index4RegionTable=TableIndex4RegionTable.Index4RegionTable(i);
    RegionDataTable(Index4RegionTable,:)=otherSlotAreaTable(i,:);
    end
end
