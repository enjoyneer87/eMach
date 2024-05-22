function [maxValue,index]=findMaxValueIndex5Table(StatorAssemRegionTable)
    [maxValue,index]=max(StatorAssemRegionTable.Area(:));
end