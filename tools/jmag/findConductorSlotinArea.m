function [UniqueValueStruct,RegionDataTable]=findConductorSlotinArea(RegionDataTable)
% findSimilarValuesWithinTolerance
Name4Object='Conductor';

UniqueValueStruct = findSimilarValuesWithinTolerance(RegionDataTable.Area);
tolerance=1e-5;
for IndexUqVal=1:length(UniqueValueStruct)
   if UniqueValueStruct(IndexUqVal).Values <tolerance
        UniqueValueStruct(IndexUqVal).Values=[];
        UniqueValueStruct(IndexUqVal).Indices=[];

   end
end
 % 빈 구조체 제거
    emptyStructs = arrayfun(@(x) isempty(x.Values), UniqueValueStruct);
    UniqueValueStruct(emptyStructs) = [];
if length(UniqueValueStruct)==1
    for Index4SameArea=1:length(UniqueValueStruct.Indices)
    RegionDataTable.Name{UniqueValueStruct.Indices(Index4SameArea)}=[Name4Object,'_',num2str(Index4SameArea)];
    end
end

end
