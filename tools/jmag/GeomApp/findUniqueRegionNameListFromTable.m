function RegionNameStruct=findUniqueRegionNameListFromTable(AssemRegionTable)

%% RegionName List
    RegionNameCell=AssemRegionTable.Name;
    
%% remove Number 4 Check Region Type
    for i=1:length(RegionNameCell)
        result{i}= removeNumbersFromString(RegionNameCell{i});
    end

%% Unique Region Type
    uniqueRegionNameCell=unique(result);

%% List 2 Struct
    RegionNameStruct.RegionNameCell       = RegionNameCell;
    RegionNameStruct.uniqueRegionNameCell = uniqueRegionNameCell;

end