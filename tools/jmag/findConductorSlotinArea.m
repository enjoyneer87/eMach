function [UniqueValueStruct,RegionDataTable]=findConductorSlotinArea(RegionDataTable)

    %% findSimilarValuesWithinTolerance
    Name4Object='Conductor';
    % RegionDataTable=StatorAssemRegionTable
    % minRadius=min(RegionDataTable.distanceRFromCenter);
    % RegionDataTable=RegionDataTable(~(difftol(RegionDataTable.distanceRFromCenter,minRadius)),:)
    UniqueValueStruct = findSimilarValuesWithinTolerance(RegionDataTable.Area);
 
    RegionDataTable.Name=RegionDataTable.sketchItemName;

    %% Backup
    % tolerance=1e-5;
    % 
    % for IndexUqVal=1:length(UniqueValueStruct)
    %    if UniqueValueStruct(IndexUqVal).Values <tolerance
    %         UniqueValueStruct(IndexUqVal).Values=[];
    %         UniqueValueStruct(IndexUqVal).Indices=[];
    % 
    %    end
    % end
    % 
    % % 빈 구조체 제거
    %     emptyStructs = arrayfun(@(x) isempty(x.Values), UniqueValueStruct);
    %     UniqueValueStruct(emptyStructs) = [];
    %% 내측부터 번호매기기
    
    
    %% GeomTable이름 변경   

    if isscalar(UniqueValueStruct)
        for Index4SameArea=1:length(UniqueValueStruct.Indices)
        RegionDataTable.Name{UniqueValueStruct.Indices(Index4SameArea)}=[Name4Object,'_',num2str(Index4SameArea)];
        end
    elseif isempty(UniqueValueStruct)     
      RegionDataTable = sortrows(RegionDataTable,'Area','descend');
      RegionDataTable.Name{2}='Conductor'; 
    end

    RegionDataTable.sketchItemName=RegionDataTable.Name;
end
